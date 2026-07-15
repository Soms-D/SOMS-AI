"""PackageArchitect Module for SOMS
Autonomous system package management — install, update, search, repair
"""

import logging
import os
import re
import shlex
import shutil
import subprocess
import time

from .gui_sudo import prompt_sudo_password

logger = logging.getLogger('PackageArchitect')

BLACKLIST = {
    'docker', 'containerd', 'runc', 'libvirt-daemon', 'qemu',
}

STABLE_PACKAGES = {
    'build-essential', 'python3-dev', 'python3-pip', 'python3-venv',
    'git', 'curl', 'wget', 'htop', 'neofetch', 'tmux', 'vim',
    'ffmpeg', 'portaudio19-dev', 'flac', 'arecord',
}

class SudoPasswordRequired(Exception):
    """Raised when a privileged operation needs a sudo password that the
    GUI/agent must collect from the user (graphical prompt)."""
    pass


class PackageArchitect:
    """Detects distro, manages packages, and reports results safely."""

    def __init__(self, config):
        self.config = config
        self.is_running = False
        self._manager = None
        self._install_cmd = None
        self._search_cmd = None
        self._update_cmd = None
        self._fix_cmd = None
        self._sudo_password = None
        self._detect_package_manager()

    def set_sudo_password(self, password):
        """Cache a sudo password so privileged ops don't need a terminal prompt."""
        self._sudo_password = password or None

    def start(self):
        self.is_running = True
        logger.info(f"PackageArchitect online — manager: {self._manager}")

    def stop(self):
        self.is_running = False
        logger.info("PackageArchitect offline")

    def _detect_package_manager(self):
        for cmd, mgr in [
            ('apt-get --version', 'apt'),
            ('pacman --version', 'pacman'),
            ('dnf --version', 'dnf'),
            ('yum --version', 'yum'),
            ('zypper --version', 'zypper'),
            ('apk --version', 'apk'),
        ]:
            try:
                subprocess.run(shlex.split(cmd), capture_output=True, timeout=5)
                self._manager = mgr
                break
            except Exception:
                continue
        if self._manager is None:
            self._manager = 'apt'
        self._set_commands()

    def _set_commands(self):
        m = self._manager
        if m == 'apt':
            self._install_cmd = ['apt-get', 'install', '-y']
            self._search_cmd = ['apt-cache', 'search']
            self._update_cmd = ['apt-get', 'update']
            self._upgrade_cmd = ['apt-get', 'upgrade', '-y']
            self._fix_cmd = ['apt-get', 'install', '-f', '-y']
            self._show_cmd = ['apt-cache', 'show']
            self._remove_cmd = ['apt-get', 'remove', '-y']
        elif m == 'pacman':
            self._install_cmd = ['pacman', '-S', '--noconfirm']
            self._search_cmd = ['pacman', '-Ss']
            self._update_cmd = ['pacman', '-Sy']
            self._upgrade_cmd = ['pacman', '-Su', '--noconfirm']
            self._fix_cmd = ['pacman', '-Syu', '--noconfirm']
            self._show_cmd = ['pacman', '-Si']
            self._remove_cmd = ['pacman', '-R', '--noconfirm']
        elif m in ('dnf', 'yum'):
            self._install_cmd = [m, 'install', '-y']
            self._search_cmd = [m, 'search']
            self._update_cmd = [m, 'makecache']
            self._upgrade_cmd = [m, 'upgrade', '-y']
            self._fix_cmd = [m, 'distro-sync', '-y']
            self._show_cmd = [m, 'info']
            self._remove_cmd = [m, 'remove', '-y']
        elif m == 'zypper':
            self._install_cmd = ['zypper', 'install', '-y']
            self._search_cmd = ['zypper', 'search']
            self._update_cmd = ['zypper', 'refresh']
            self._upgrade_cmd = ['zypper', 'update', '-y']
            self._fix_cmd = ['zypper', 'verify']
            self._show_cmd = ['zypper', 'info']
            self._remove_cmd = ['zypper', 'remove', '-y']
        elif m == 'apk':
            self._install_cmd = ['apk', 'add']
            self._search_cmd = ['apk', 'search']
            self._update_cmd = ['apk', 'update']
            self._upgrade_cmd = ['apk', 'upgrade']
            self._fix_cmd = ['apk', 'fix']
            self._show_cmd = ['apk', 'info']
            self._remove_cmd = ['apk', 'del']
        else:
            self._install_cmd = ['apt-get', 'install', '-y']
            self._search_cmd = ['apt-cache', 'search']
            self._update_cmd = ['apt-get', 'update']
            self._upgrade_cmd = ['apt-get', 'upgrade', '-y']
            self._fix_cmd = ['apt-get', 'install', '-f', '-y']
            self._show_cmd = ['apt-cache', 'show']
            self._remove_cmd = ['apt-get', 'remove', '-y']

    def _sanitize_input(self, package_name):
        sanitized = re.sub(r'[;&|`$(){}<>!]', '', package_name).strip()
        if not sanitized or not re.match(r'^[a-zA-Z0-9_\-\+\.:]+$', sanitized):
            return None
        return sanitized

    def _execute(self, cmd, timeout=120, use_sudo=False, stream_callback=None):
        try:
            if use_sudo and not self._check_sudo():
                # Sudo requires a password. Prefer a cached (GUI-provided) one;
                # otherwise open a graphical dialog to collect it once.
                if self._sudo_password:
                    return self._run_sudo(cmd, self._sudo_password, timeout, stream_callback)
                if getattr(self, 'use_gui_sudo', True) and not getattr(self, '_gui_auth_attempted', False):
                    self._gui_auth_attempted = True
                    pw = prompt_sudo_password(
                        "SOMS needs your sudo password to manage system packages.")
                    if pw:
                        self._sudo_password = pw
                        if stream_callback:
                            stream_callback("[AUTH] Password received via graphical prompt.")
                        return self._run_sudo(cmd, pw, timeout, stream_callback)
                raise SudoPasswordRequired(
                    "Sudo requires a password. SOMS will open a dialog to collect it.")

            full_cmd = ['sudo'] + cmd if use_sudo else cmd
            if stream_callback:
                process = subprocess.Popen(
                    full_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    stdin=subprocess.DEVNULL,
                )
                output_lines = []
                start = time.time()
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.rstrip()
                    output_lines.append(line)
                    stream_callback(line)
                    if time.time() - start > timeout:
                        process.kill()
                        output_lines.append('[TIMEOUT]')
                        break
                process.wait()
                ok = process.returncode == 0
                output = '\n'.join(output_lines)
                return ok, output
            else:
                result = subprocess.run(full_cmd, capture_output=True, text=True,
                                        timeout=timeout, stdin=subprocess.DEVNULL)
                combined = (result.stdout + result.stderr).strip()
                return result.returncode == 0, combined
        except SudoPasswordRequired:
            raise
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return False, f"Command not found: {cmd[0] if cmd else '?'}"
        except PermissionError:
            return False, "Permission denied"

    def _run_sudo(self, cmd, password, timeout, stream_callback=None):
        """Run a sudo command feeding `password` via stdin (-S)."""
        full_cmd = ['sudo', '-S'] + cmd
        try:
            if stream_callback:
                process = subprocess.Popen(
                    full_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    stdin=subprocess.PIPE,
                )
                try:
                    process.stdin.write(password + '\n')
                    process.stdin.flush()
                    process.stdin.close()
                except Exception:
                    pass
                output_lines = []
                start = time.time()
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.rstrip()
                    if password and password in line:
                        line = line.replace(password, '***')
                    output_lines.append(line)
                    stream_callback(line)
                    if time.time() - start > timeout:
                        process.kill()
                        output_lines.append('[TIMEOUT]')
                        break
                process.wait()
                ok = process.returncode == 0
                output = '\n'.join(output_lines)
                return ok, output
            else:
                result = subprocess.run(
                    full_cmd, input=password + '\n',
                    capture_output=True, text=True, timeout=timeout,
                )
                combined = (result.stdout + result.stderr).strip()
                if password and password in combined:
                    combined = combined.replace(password, '***')
                return result.returncode == 0, combined
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return False, f"Command not found: {cmd[0] if cmd else '?'}"
        except Exception as e:
            return False, str(e)

    def _check_sudo(self):
        try:
            r = subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=5)
            if r.returncode == 0:
                return True
        except Exception:
            pass
        return False

    def _setup_sudoers(self):
        entry = f"{os.environ.get('USER', 'soms')} ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/apt-get, /usr/bin/apt-cache, /usr/bin/dpkg, /usr/bin/python3, /usr/bin/sed, /usr/bin/systemctl, /bin/systemctl, /usr/bin/tee, /bin/tee, /usr/bin/chmod, /bin/chmod, /usr/bin/cat, /bin/cat"
        path = '/etc/sudoers.d/soms-pkg'
        try:
            r = subprocess.run(
                ['sudo', 'sh', '-c', f'echo "{entry}" > {path} && chmod 440 {path}'],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                logger.info("sudoers configured for passwordless package ops")
                return True, "Sudoers configured. Passwordless package ops enabled."
            return False, r.stderr.strip() or "Failed to write sudoers"
        except Exception as e:
            return False, str(e)

    def search(self, query):
        sanitized = self._sanitize_input(query)
        if not sanitized:
            return False, "Invalid package name."
        ok, output = self._execute(self._search_cmd + [sanitized], timeout=30)
        if ok:
            results = [l for l in output.split('\n') if sanitized.lower() in l.lower()]
            return True, '\n'.join(results[:15]) if results else f"No results for '{sanitized}'."
        return False, output if output else "No output from package manager."

    def show(self, package):
        sanitized = self._sanitize_input(package)
        if not sanitized:
            return False, "Invalid package name."
        ok, output = self._execute(self._show_cmd + [sanitized], timeout=15)
        return ok, output if ok else f"Cannot find '{sanitized}'."

    def _is_installed(self, package):
        if shutil.which(package):
            return True
        try:
            r = subprocess.run(['dpkg', '-l', package], capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    def install(self, package, stream_callback=None):
        sanitized = self._sanitize_input(package)
        if not sanitized:
            return False, "Invalid package name.", ''
        if sanitized.lower() in BLACKLIST:
            return False, f"BLOCKED: '{sanitized}' is blacklisted.", ''
        if self._is_installed(sanitized):
            return True, f"'{sanitized}' is already installed.", ''
        
        # Try with sudo (will prompt for password if needed)
        ok, output = self._execute(self._install_cmd + [sanitized], timeout=300, use_sudo=True, stream_callback=stream_callback)
        if ok:
            return True, f"Installed '{sanitized}'.", output
        
        # Get clean error message
        error_lines = [l for l in output.strip().split('\n') if l.strip()]
        reason = error_lines[-1] if error_lines else 'unknown error'
        
        # Suggest alternatives for common removed packages
        alternatives = {
            'neofetch': 'neowofetch or fastfetch',
            'ifconfig': 'net-tools or iproute2',
        }
        alt = alternatives.get(sanitized.lower(), '')
        suggestion = f"\nTry: {alt}" if alt else ""
        return False, f"Failed to install '{sanitized}': {reason}{suggestion}", output

    def remove(self, package, stream_callback=None):
        """Uninstall a package (aggressive CLI: /remove)."""
        sanitized = self._sanitize_input(package)
        if not sanitized:
            return False, "Invalid package name.", ''
        if sanitized.lower() in BLACKLIST:
            return False, f"BLOCKED: '{sanitized}' is blacklisted.", ''
        if not self._is_installed(sanitized):
            return True, f"'{sanitized}' is not installed.", ''
        ok, output = self._execute(self._remove_cmd + [sanitized], timeout=300,
                                   use_sudo=True, stream_callback=stream_callback)
        if ok:
            return True, f"Removed '{sanitized}'.", output
        error_lines = [l for l in output.strip().split('\n') if l.strip()]
        reason = error_lines[-1] if error_lines else 'unknown error'
        return False, f"Failed to remove '{sanitized}': {reason}", output

    def update_repos(self, stream_callback=None):
        if not self._check_sudo():
            return False, "Sudo not available — configure NOPASSWD.", ''
        ok, output = self._execute(self._update_cmd, timeout=120, use_sudo=True, stream_callback=stream_callback)
        if ok:
            return True, "Package lists updated.", output
        return False, "Failed to update package lists.", output

    def upgrade(self, stream_callback=None):
        if not self._check_sudo():
            return False, "Sudo not available — configure NOPASSWD.", ''
        ok, output = self._execute(self._upgrade_cmd, timeout=300, use_sudo=True, stream_callback=stream_callback)
        if ok:
            return True, "System packages upgraded.", output
        return False, "Upgrade failed.", output

    def fix_dependencies(self, stream_callback=None):
        if not self._check_sudo():
            return False, "Sudo not available — configure NOPASSWD.", ''
        ok, output = self._execute(self._fix_cmd, timeout=120, use_sudo=True, stream_callback=stream_callback)
        if ok:
            return True, "Dependencies repaired.", output
        return False, "Dependency repair failed.", output

    def update_and_upgrade(self, stream_callback=None):
        if not self._check_sudo():
            return False, "Sudo not available — configure NOPASSWD.", ''
        ok1, output1 = self._execute(self._update_cmd, timeout=120, use_sudo=True, stream_callback=stream_callback)
        if not ok1:
            return False, "Failed to update package lists.", output1
        ok2, output2 = self._execute(self._upgrade_cmd, timeout=300, use_sudo=True, stream_callback=stream_callback)
        if ok2:
            return True, "Package lists updated and system upgraded.", output1 + "\n" + output2
        return False, "Upgrade failed after update.", output1 + "\n" + output2

    def full_upgrade(self, stream_callback=None):
        """Complete system upgrade: update repos + full-upgrade (dist-upgrade) + fix deps."""
        if not self._check_sudo():
            return False, "Sudo not available — configure NOPASSWD.", ''
        
        outputs = []
        steps = [
            ("Updating package lists...", self._update_cmd, 120),
            ("Running full-upgrade (dist-upgrade)...", self._get_full_upgrade_cmd(), 600),
            ("Fixing dependencies...", self._fix_cmd, 120),
        ]
        
        for desc, cmd, timeout in steps:
            if stream_callback:
                stream_callback(f"[STEP] {desc}")
            ok, output = self._execute(cmd, timeout=timeout, use_sudo=True, stream_callback=stream_callback)
            outputs.append(f"=== {desc} ===\n{output}")
            if not ok:
                return False, f"Failed at: {desc}", "\n".join(outputs)
        
        return True, "Full system upgrade complete.", "\n".join(outputs)

    def dist_upgrade(self, stream_callback=None):
        """Alias for full_upgrade — dist-upgrade with dependency resolution."""
        return self.full_upgrade(stream_callback)

    def _get_full_upgrade_cmd(self):
        """Get the appropriate full-upgrade/dist-upgrade command for the package manager."""
        m = self._manager
        if m == 'apt':
            return ['apt-get', 'full-upgrade', '-y']
        elif m == 'pacman':
            return ['pacman', '-Syu', '--noconfirm']
        elif m in ('dnf', 'yum'):
            return [m, 'distro-sync', '-y']
        elif m == 'zypper':
            return ['zypper', 'dup', '-y']
        elif m == 'apk':
            return ['apk', 'upgrade']
        return ['apt-get', 'full-upgrade', '-y']

    def apt_update_upgrade_dist(self, stream_callback=None):
        """Execute: apt update && apt full-upgrade && apt dist-upgrade (Debian/Ubuntu specific)."""
        if self._manager != 'apt':
            return False, "This command is for apt-based systems only. Use full_upgrade() for cross-distro.", ''
        
        if not self._check_sudo():
            return False, "Sudo not available — configure NOPASSWD.", ''
        
        outputs = []
        commands = [
            ("apt update", ['apt-get', 'update'], 120),
            ("apt full-upgrade", ['apt-get', 'full-upgrade', '-y'], 600),
            ("apt dist-upgrade", ['apt-get', 'dist-upgrade', '-y'], 600),
            ("apt autoremove", ['apt-get', 'autoremove', '-y'], 120),
            ("apt autoclean", ['apt-get', 'autoclean', '-y'], 60),
        ]
        
        for desc, cmd, timeout in commands:
            if stream_callback:
                stream_callback(f"[STEP] {desc}")
            ok, output = self._execute(cmd, timeout=timeout, use_sudo=True, stream_callback=stream_callback)
            outputs.append(f"=== {desc} ===\n{output}")
            if not ok:
                return False, f"Failed at: {desc}", "\n".join(outputs)
        
        return True, "Complete apt update + full-upgrade + dist-upgrade + cleanup done.", "\n".join(outputs)



    def detect_distro(self):
        try:
            with open('/etc/os-release') as f:
                data = f.read()
            name = re.search(r'^ID=(\w+)', data, re.M)
            pretty = re.search(r'^PRETTY_NAME="(.+)"', data, re.M)
            distro = pretty.group(1) if pretty else (name.group(1) if name else 'unknown')
            return distro, self._manager
        except Exception:
            return 'unknown', self._manager

    def get_status(self):
        distro, mgr = self.detect_distro()
        return {
            'online': self.is_running,
            'manager': mgr,
            'distro': distro,
        }
