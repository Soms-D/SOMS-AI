"""Improver Agent Module for SOMS
Self-improvement agent that detects capabilities, installs tools,
and expands command handlers dynamically.
"""

import logging
import os
import re
import shutil
import subprocess
import time
import getpass
from datetime import datetime

logger = logging.getLogger('Improver')

# Cached sudo password to avoid repeated prompts
_sudo_password = None

def set_sudo_password(password):
    """Set the cached sudo password (e.g. from the GUI)."""
    global _sudo_password
    _sudo_password = password if password else None


def _run_sudo(cmd, timeout=60):
    """Run a command with sudo, using a cached/GUI-provided password if needed."""
    global _sudo_password

    # Check if sudo needs password
    check = subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=5)
    if check.returncode == 0:
        # No password needed
        return subprocess.run(['sudo', '-n'] + cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)

    # Need password - use cached/GUI password, else try prompting (fails in GUI)
    if _sudo_password is None:
        try:
            _sudo_password = getpass.getpass("[SOMS] Enter sudo password: ")
        except Exception:
            # No TTY (e.g. running under the GUI) and no password provided.
            class _R:
                returncode = 1
                stdout = ''
                stderr = 'sudo password required (enter it in the SOMS GUI)'
            return _R()

    r = subprocess.run(
        ['sudo', '-S'] + cmd,
        input=_sudo_password + '\n',
        capture_output=True, text=True, timeout=timeout
    )

    # Check if password was wrong
    if 'sorry, try again' in (r.stderr or '').lower():
        _sudo_password = None  # Reset cached password
        return r

    # Hide password from output
    r.stdout = (r.stdout or '').replace(_sudo_password, '***')
    r.stderr = (r.stderr or '').replace(_sudo_password, '***')
    return r

CAPABILITY_DEFS = {
    'volume': {
        'label': 'Volume Control',
        'check': ['amixer'],
        'install': ['alsa-utils'],
        'handlers': ['volume', 'vol'],
    },
    'packages': {
        'label': 'Package Management',
        'check': ['apt', 'dpkg'],
        'install': [],
        'handlers': ['install', 'remove', 'pkg', 'package'],
    },
    'network': {
        'label': 'Network Analysis',
        'check': ['nmcli', 'iwconfig', 'ip'],
        'install': ['network-manager', 'wireless-tools'],
        'handlers': ['network', 'wifi', 'net'],
    },
    'system': {
        'label': 'System Control',
        'check': ['systemctl', 'ps', 'kill'],
        'install': [],
        'handlers': ['system', 'service', 'process'],
    },
    'files': {
        'label': 'File Operations',
        'check': ['cp', 'mv', 'rm', 'find'],
        'install': [],
        'handlers': ['file', 'edit', 'find'],
    },
    'media': {
        'label': 'Media Processing',
        'check': ['ffmpeg', 'convert', 'sox'],
        'install': ['ffmpeg', 'imagemagick', 'sox'],
        'handlers': ['media', 'photo', 'video', 'audio'],
    },
    'hack': {
        'label': 'Security & Analysis',
        'check': ['nmap', 'netstat', 'ss'],
        'install': ['nmap', 'net-tools'],
        'handlers': ['scan', 'hack', 'security'],
    },
    'devices': {
        'label': 'Device Management',
        'check': ['lsusb', 'lspci', 'lsblk'],
        'install': ['usbutils', 'pciutils'],
        'handlers': ['device', 'usb', 'hardware'],
    },
    'develop': {
        'label': 'Development Tools',
        'check': ['python3', 'pip3', 'git', 'gcc'],
        'install': ['python3-pip', 'git', 'build-essential'],
        'handlers': ['code', 'build', 'compile'],
    },
    'ai': {
        'label': 'AI & Gemini Features',
        'check': ['python3'],
        'install': ['python3-requests'],
        'handlers': ['ai', 'gemini', 'model', 'infer'],
    },
    'camera': {
        'label': 'Camera Capture',
        'check': ['ffmpeg'],
        'install': ['ffmpeg'],
        'handlers': ['camera', 'snap', 'photo', 'capture', 'see'],
    },
    'motion': {
        'label': 'Motion Detection',
        'check': ['motion'],
        'install': ['motion'],
        'handlers': ['motion', 'detect', 'movement'],
    },
    'notify': {
        'label': 'Notifications',
        'check': ['python3'],
        'install': [],
        'handlers': ['notify', 'email', 'notification', 'alert'],
    },
}

class ImproverAgent:
    """Self-improvement agent that detects, installs, and manages capabilities."""

    def __init__(self, config, system_ref=None):
        self.config = config
        self.system = system_ref
        self.is_running = False
        self.capabilities = {}
        self.improvement_log = []
        self.last_scan = 0
        self._dynamic_handlers = {}

    def start(self):
        self.is_running = True
        logger.info("Improver agent started")
        self.scan_capabilities()

    def stop(self):
        self.is_running = False
        logger.info("Improver agent stopped")

    def scan_capabilities(self):
        """Scan the system for available tools and capabilities."""
        self.capabilities = {}
        for key, cdef in CAPABILITY_DEFS.items():
            available = []
            missing = []
            for tool in cdef['check']:
                if shutil.which(tool):
                    available.append(tool)
                else:
                    missing.append(tool)
            status = 'ready' if available else 'missing' if missing else 'unknown'
            self.capabilities[key] = {
                'label': cdef['label'],
                'status': status,
                'available': available,
                'missing': missing,
                'install_cmd': cdef['install'],
                'handlers': cdef['handlers'],
            }
        self.last_scan = time.time()
        count = sum(1 for c in self.capabilities.values() if c['status'] == 'ready')
        logger.info(f"Scan complete: {count}/{len(self.capabilities)} capabilities ready")
        return self.capabilities

    def get_capability(self, name):
        return self.capabilities.get(name)

    def get_status_summary(self):
        lines = []
        ready = []
        missing_flags = []
        for key, cap in self.capabilities.items():
            icon = '✓' if cap['status'] == 'ready' else '✗'
            label = cap['label']
            tools = ', '.join(cap['available']) if cap['available'] else 'none'
            if cap['status'] == 'ready':
                ready.append(key)
                lines.append(f"  {icon} {label} [{tools}]")
            else:
                missing_flags.append(key)
                install = ', '.join(cap['install_cmd']) if cap['install_cmd'] else 'manual'
                lines.append(f"  {icon} {label} (install: {install})")
        summary = f"Capabilities: {len(ready)}/{len(self.capabilities)} ready"
        return summary + '\n' + '\n'.join(lines)

    def install_capability(self, cap_name):
        cap = self.capabilities.get(cap_name)
        if not cap:
            return False, f"No capability '{cap_name}'"
        if cap['status'] == 'ready':
            return True, f"{cap['label']} already ready"
        pkgs = cap.get('install_cmd', [])
        if not pkgs:
            return False, f"No packages defined for {cap['label']}"
        try:
            for pkg in pkgs:
                logger.info(f"Installing {pkg}...")
                r = subprocess.run(
                    ['sudo', 'apt', 'install', '-y', pkg],
                    capture_output=True, text=True, timeout=120
                )
                if r.returncode != 0:
                    return False, f"Failed to install {pkg}: {r.stderr.strip()}"
            self.scan_capabilities()
            return True, f"Installed packages for {cap['label']}"
        except Exception as e:
            return False, f"Install error: {e}"

    def learn_command(self, trigger, handler_fn, description=''):
        self._dynamic_handlers[trigger.lower()] = {
            'fn': handler_fn,
            'desc': description,
        }
        self.improvement_log.append(f"Learned command: {trigger}")
        return True

    def dispatch(self, command_text, command_type):
        text_lower = command_text.lower().strip()
        for trigger, h in self._dynamic_handlers.items():
            if text_lower.startswith(trigger) or trigger in text_lower:
                try:
                    return h['fn'](command_text)
                except Exception as e:
                    return {'text': f"Handler error: {e}", 'type': 'improver_error'}
        return None

    def handle_volume(self, cmd_text):
        text = cmd_text.lower()
        try:
            if any(w in text for w in ['up', 'inc', 'high', '+']):
                subprocess.run(['amixer', 'sset', 'Master', '5%+'], capture_output=True, timeout=5)
                return {'text': 'Turning it up! Volume increased.', 'type': 'improver_volume'}
            elif any(w in text for w in ['down', 'dec', 'low', '-']):
                subprocess.run(['amixer', 'sset', 'Master', '5%-'], capture_output=True, timeout=5)
                return {'text': 'Coming down. Volume decreased.', 'type': 'improver_volume'}
            elif 'mute' in text:
                subprocess.run(['amixer', 'sset', 'Master', 'mute'], capture_output=True, timeout=5)
                return {'text': 'Shhh... Audio muted.', 'type': 'improver_volume'}
            elif any(w in text for w in ['unmute', 'on']):
                subprocess.run(['amixer', 'sset', 'Master', 'unmute'], capture_output=True, timeout=5)
                return {'text': 'Audio back on. Unmuted.', 'type': 'improver_volume'}
            r = subprocess.run(['amixer', 'get', 'Master'], capture_output=True, text=True, timeout=5)
            m = re.search(r'\[(\d+)%\]', r.stdout)
            pct = m.group(1) if m else '?'
            return {'text': f"Volume is at {pct}% right now. Want me to turn it up or down?", 'type': 'improver_volume'}
        except Exception as e:
            return {'text': f"Volume control failed: {e}", 'type': 'improver_error'}

    def handle_package(self, cmd_text):
        text = cmd_text.lower()
        def _is_installed(pkg):
            if shutil.which(pkg):
                return True
            try:
                r = subprocess.run(['dpkg', '-l', pkg], capture_output=True, timeout=5)
                return r.returncode == 0
            except Exception:
                return False
        def _install(pkg):
            r = _run_sudo(['apt-get', 'install', '-y', pkg], timeout=120)
            if r.returncode != 0:
                # Suggest alternatives for common removed packages
                alternatives = {
                    'neofetch': 'neowofetch or fastfetch',
                    'ifconfig': 'net-tools or iproute2',
                }
                alt = alternatives.get(pkg.lower(), '')
                if alt:
                    return r.returncode == 0, (r.stdout + r.stderr) + f"\nTry: {alt}"
            return r.returncode == 0, r.stdout + r.stderr
        try:
            if any(w in text for w in ['install', 'get']):
                parts = cmd_text.split()
                for p in parts:
                    if p in ('install', 'get', 'package', 'pkg', 'sudo', 'apt', 'apt-get'):
                        continue
                    if _is_installed(p):
                        return {'text': f"'{p}' is already installed.", 'type': 'improver_package'}
                    ok, out = _install(p)
                    if ok:
                        return {'text': f"Installed '{p}'. All set.", 'type': 'improver_package'}
                    if 'password' in out.lower() or 'terminal is required' in out.lower():
                        return {'text': f"Need sudo NOPASSWD to install '{p}'. Run:\n  echo 'soms ALL=(ALL) NOPASSWD: /usr/bin/apt-get' | sudo tee /etc/sudoers.d/soms-pkg", 'type': 'improver_error'}
                    return {'text': f"Couldn't install {p}: {out.strip()[:200]}", 'type': 'improver_error'}
            elif any(w in text for w in ['remove', 'delete', 'uninstall']):
                parts = cmd_text.split()
                for p in parts:
                    if p in ('remove', 'delete', 'uninstall', 'package', 'pkg', 'sudo', 'apt'):
                        continue
                    r = _run_sudo(['apt-get', 'remove', '-y', p], timeout=60)
                    if r.returncode == 0:
                        return {'text': f"{p} has been removed.", 'type': 'improver_package'}
                    return {'text': f"Couldn't remove {p}: {r.stderr.strip()[:200]}", 'type': 'improver_error'}
            elif any(w in text for w in ['update', 'upgrade']):
                r = _run_sudo(['apt-get', 'update'], timeout=120)
                return {'text': 'Package list refreshed.', 'type': 'improver_package'}
            return {'text': 'Try "install <package>" or "remove <package>".', 'type': 'improver_package'}
        except Exception as e:
            return {'text': f"Package operation failed: {e}", 'type': 'improver_error'}

    def handle_network(self, cmd_text):
        text = cmd_text.lower()
        try:
            if any(w in text for w in ['scan', 'list', 'available']):
                r = subprocess.run(['nmcli', 'dev', 'wifi', 'list'], capture_output=True, text=True, timeout=15)
                lines = r.stdout.strip().split('\n')[:10] if r.stdout else ['No networks found']
                return {'text': 'Here are the networks I can see:\n' + '\n'.join(lines), 'type': 'improver_network'}
            elif any(w in text for w in ['status', 'info', 'ip']):
                r = subprocess.run(['ip', '-br', 'addr'], capture_output=True, text=True, timeout=5)
                return {'text': r.stdout.strip()[:500] or 'No network info', 'type': 'improver_network'}
            return {'text': 'You can say "scan networks", "network status", or "wifi list".', 'type': 'improver_network'}
        except Exception as e:
            return {'text': f"Network check failed: {e}", 'type': 'improver_error'}

    def handle_system(self, cmd_text):
        text = cmd_text.lower()
        try:
            if any(w in text for w in ['service', 'daemon']):
                parts = cmd_text.split()
                action = 'status'
                svc = ''
                for p in parts:
                    if p in ('start', 'stop', 'restart', 'status', 'enable', 'disable'):
                        action = p
                    elif p not in ('service', 'system', 'sudo'):
                        svc = p
                if svc:
                    r = subprocess.run(['systemctl', action, svc], capture_output=True, text=True, timeout=15)
                    return {'text': r.stdout.strip()[:300] or r.stderr.strip()[:300], 'type': 'improver_system'}
                return {'text': 'Tell me which service — like "restart ssh" or "stop apache2".', 'type': 'improver_system'}
            elif any(w in text for w in ['process', 'ps', 'running']):
                r = subprocess.run(['ps', 'aux', '--sort=-%mem'], capture_output=True, text=True, timeout=5)
                lines = r.stdout.strip().split('\n')[:8]
                return {'text': 'Top running processes:\n' + '\n'.join(lines), 'type': 'improver_system'}
            return {'text': 'Try "restart <service>" or say "what\'s running?".', 'type': 'improver_system'}
        except Exception as e:
            return {'text': f"System control failed: {e}", 'type': 'improver_error'}

    def handle_file(self, cmd_text):
        text = cmd_text.lower()
        try:
            if any(w in text for w in ['find', 'search', 'locate']):
                parts = cmd_text.split()
                name = ''
                for p in parts:
                    if p not in ('find', 'search', 'locate', 'file'):
                        name = p
                if name:
                    r = subprocess.run(['find', '/home', '-maxdepth', '4', '-iname', f'*{name}*', '-type', 'f'], capture_output=True, text=True, timeout=10)
                    results = r.stdout.strip().split('\n') if r.stdout.strip() else []
                    if not results:
                        return {'text': f"Couldn't find anything named '{name}'. Want to try a different name?", 'type': 'improver_file'}
                    return {'text': f"Found {len(results)} file{'s' if len(results) != 1 else ''}:\n" + '\n'.join(results[:10]), 'type': 'improver_file'}
                return {'text': 'Say "find <filename>" and I\'ll search for it.', 'type': 'improver_file'}
            elif any(w in text for w in ['edit', 'open', 'read']):
                parts = cmd_text.split()
                fpath = ''
                for p in parts:
                    if p not in ('edit', 'open', 'read', 'file'):
                        fpath = p
                if fpath and os.path.isfile(fpath):
                    with open(fpath) as f:
                        content = f.read()
                    return {'text': f"Here's what's in {fpath}:\n{content[:500]}", 'type': 'improver_file'}
                return {'text': 'Tell me which file to read — I need the full path.', 'type': 'improver_file'}
            elif any(w in text for w in ['write', 'create', 'save']):
                parts = cmd_text.split()
                fpath = ''
                for p in parts:
                    if p not in ('write', 'create', 'save', 'file'):
                        fpath = p
                if fpath:
                    with open(fpath, 'w') as f:
                        f.write('')
                    return {'text': f"Created {fpath}. Ready to go.", 'type': 'improver_file'}
                return {'text': 'Tell me the file path you want to create.', 'type': 'improver_file'}
            return {'text': 'You can say "find <name>", "read <path>", or "create <path>".', 'type': 'improver_file'}
        except Exception as e:
            return {'text': f"File operation failed: {e}", 'type': 'improver_error'}

    def handle_media(self, cmd_text):
        text = cmd_text.lower()
        try:
            if shutil.which('ffmpeg'):
                if any(w in text for w in ['convert', 'transcode']):
                    parts = cmd_text.split()
                    src, fmt = '', 'mp3'
                    for p in parts:
                        if p.endswith(('.mp4', '.avi', '.mkv', '.wav', '.flac', '.mp3', '.jpg', '.png')):
                            src = p
                        elif p in ('mp3', 'mp4', 'wav', 'flac', 'jpg', 'png', 'gif'):
                            fmt = p
                    if src and os.path.isfile(src):
                        out = os.path.splitext(src)[0] + '.' + fmt
                        subprocess.run(['ffmpeg', '-i', src, out], capture_output=True, timeout=60)
                        return {'text': f"Converted {src} to {out}. Done!", 'type': 'improver_media'}
                    return {'text': 'Try "convert <file> <format>" like "convert video.mp4 mp3".', 'type': 'improver_media'}
            if shutil.which('convert'):
                if any(w in text for w in ['resize', 'image', 'photo']):
                    parts = cmd_text.split()
                    src, sz = '', '50%'
                    for p in parts:
                        if p.endswith(('.jpg', '.png', '.gif', '.webp')):
                            src = p
                        elif '%' in p or 'x' in p:
                            sz = p
                    if src and os.path.isfile(src):
                        out = os.path.splitext(src)[0] + '_resized' + os.path.splitext(src)[1]
                        subprocess.run(['convert', src, '-resize', sz, out], capture_output=True, timeout=30)
                        return {'text': f"Resized {src} saved as {out}. All good!", 'type': 'improver_media'}
                    return {'text': 'Say "resize <image> 50%" or "convert <file> <format>". I\'ll handle it.', 'type': 'improver_media'}
            return {'text': 'Media tools aren\'t fully available. Try "install ffmpeg" and I\'ll set them up.', 'type': 'improver_media'}
        except Exception as e:
            return {'text': f"Media operation failed: {e}", 'type': 'improver_error'}

    def handle_security(self, cmd_text):
        text = cmd_text.lower()
        try:
            if shutil.which('nmap'):
                if any(w in text for w in ['scan', 'port']):
                    target = 'localhost'
                    parts = cmd_text.split()
                    for p in parts:
                        if p not in ('scan', 'port', 'nmap', 'security', 'hack') and not p.startswith('-'):
                            target = p
                    r = subprocess.run(['nmap', '-sn', target], capture_output=True, text=True, timeout=30)
                    return {'text': f"Scanned {target}. Here's what I found:\n{r.stdout.strip()[:500]}", 'type': 'improver_security'}
            if any(w in text for w in ['port', 'listen', 'open']):
                r = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=5)
                return {'text': 'Ports currently listening:\n' + r.stdout.strip()[:500], 'type': 'improver_security'}
            if any(w in text for w in ['wifi', 'deauth', 'monitor']):
                r = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
                return {'text': 'Wireless info I picked up:\n' + r.stdout.strip()[:500], 'type': 'improver_security'}
            return {'text': 'Try "scan <target>", "list ports", or "wifi info".', 'type': 'improver_security'}
        except Exception as e:
            return {'text': f"Security operation failed: {e}", 'type': 'improver_error'}

    def handle_device(self, cmd_text):
        text = cmd_text.lower()
        try:
            if any(w in text for w in ['usb', 'device', 'hardware']):
                results = []
                if shutil.which('lsusb'):
                    r = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
                    results.append('USB Devices:\n' + r.stdout.strip()[:300])
                if shutil.which('lspci'):
                    r = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                    results.append('PCI Devices:\n' + r.stdout.strip()[:300])
                if shutil.which('lsblk'):
                    r = subprocess.run(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'], capture_output=True, text=True, timeout=5)
                    results.append('Block Devices:\n' + r.stdout.strip()[:300])
                return {'text': 'Here\'s what I found:\n' + '\n\n'.join(results) or 'No device info available.', 'type': 'improver_device'}
            return {'text': 'Try "list usb", "list pci", or "list devices".', 'type': 'improver_device'}
        except Exception as e:
            return {'text': f"Device check failed: {e}", 'type': 'improver_error'}

    def handle_code(self, cmd_text):
        text = cmd_text.lower()
        try:
            if any(w in text for w in ['run', 'exec', 'execute']):
                parts = cmd_text.split(maxsplit=1)
                if len(parts) > 1:
                    code = parts[1]
                    for pfx in ('run', 'exec', 'execute', 'code', 'python'):
                        if code.startswith(pfx):
                            code = code[len(pfx):].strip()
                    try:
                        import ast
                        tree = ast.parse(code, mode='exec')
                        last = tree.body[-1] if tree.body else None
                        if isinstance(last, ast.Expr):
                            tree.body[-1] = ast.Assign(
                                targets=[ast.Name(id='_result', ctx=ast.Store())],
                                value=last.value
                            )
                        local_ns = {}
                        exec(compile(tree, '<cmd>', 'exec'), local_ns)
                        out = local_ns.get('_result', 'Done')
                        return {'text': f"That evaluates to: {out}", 'type': 'improver_code'}
                    except Exception as e:
                        return {'text': f"Hit a snag: {e}", 'type': 'improver_error'}
                return {'text': 'Try "run print(\'hello\')" — I\'ll execute Python on the fly.', 'type': 'improver_code'}
            return {'text': 'Say "run <python_code>" and I\'ll run it for you.', 'type': 'improver_code'}
        except Exception as e:
            return {'text': f"Code execution failed: {e}", 'type': 'improver_error'}

    def route(self, command_text):
        """Route a command to the appropriate capability handler."""
        text = command_text.lower().strip()
        if text.startswith('/'):
            return None
        routes = [
            ('volume', 'volume'),
            ('package', 'install'),
            ('package', 'remove'),
            ('package', 'uninstall'),
            ('network', 'wifi'),
            ('network', 'network'),
            ('system', 'service'),
            ('system', 'process'),
            ('file', 'find'),
            ('file', 'read'),
            ('file', 'create'),
            ('media', 'convert'),
            ('media', 'resize'),
            ('security', 'scan'),
            ('security', 'port'),
            ('device', 'usb'),
            ('device', 'hardware'),
            ('code', 'run'),
            ('ai', 'ask'),
            ('ai', 'query'),
            ('camera', 'camera'),
            ('camera', 'snap'),
            ('camera', 'photo'),
            ('camera', 'capture'),
            ('camera', 'see'),
            ('motion', 'motion'),
            ('motion', 'detect'),
            ('motion', 'movement'),
            ('notify', 'notify'),
            ('notify', 'email'),
            ('notify', 'notification'),
            ('notify', 'alert'),
        ]
        handler_map = {
            'volume': self.handle_volume,
            'package': self.handle_package,
            'network': self.handle_network,
            'system': self.handle_system,
            'file': self.handle_file,
            'media': self.handle_media,
            'security': self.handle_security,
            'device': self.handle_device,
            'code': self.handle_code,
            'ai': self.handle_ai,
            'camera': self.handle_camera,
            'motion': self.handle_motion,
            'notify': self.handle_notify,
        }
        for handler_key, trigger in routes:
            if trigger in text:
                fn = handler_map.get(handler_key)
                if fn:
                    return fn(command_text)
        return None

    def handle_ai(self, cmd_text):
        text = cmd_text.lower()
        try:
            import requests
            current = self.system.model_manager.get_current_model() if self.system and hasattr(self.system, 'model_manager') else 'unknown'
            if any(w in text for w in ['ask', 'query', 'prompt', 'gemini']):
                parts = cmd_text.split(maxsplit=1)
                if len(parts) > 1:
                    prompt = parts[1]
                    for pfx in ('ask', 'query', 'prompt', 'gemini', 'ai'):
                        if prompt.startswith(pfx):
                            prompt = prompt[len(pfx):].strip()
                    try:
                        r = requests.post(
                            'http://localhost:11434/api/generate',
                            json={'model': current, 'prompt': prompt, 'stream': False},
                            timeout=60
                        )
                        if r.status_code == 200:
                            resp = r.json().get('response', 'No response')
                            return {'text': resp[:500], 'type': 'improver_ai'}
                        return {'text': f"Ollama said: {r.status_code}. Might be an issue.", 'type': 'improver_error'}
                    except requests.ConnectionError:
                        return {'text': f"Can't reach Ollama. Make sure it's running with 'ollama serve' and a model is pulled.", 'type': 'improver_error'}
                return {'text': f'Ask me anything — say "ask <your question>" and I\'ll query {current}.', 'type': 'improver_ai'}
            return {'text': f'I\'m running {current} right now. Say "ask <question>" to use it.', 'type': 'improver_ai'}
        except ImportError:
            return {'text': 'Install requests library for AI features: "install python3-requests".', 'type': 'improver_error'}

    def handle_camera(self, cmd_text):
        """Capture from camera and describe what it sees."""
        import os, tempfile, subprocess, time
        from datetime import datetime
        try:
            from PIL import Image
            has_pillow = True
        except ImportError:
            has_pillow = False

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_dir = os.path.expanduser('~/Pictures/SOMS')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'capture_{ts}.jpg')

        devices = []
        for d in os.listdir('/dev'):
            if d.startswith('video'):
                devices.append(f'/dev/{d}')
        if not devices:
            devices = ['/dev/video0']

        device = devices[0]
        cmd = ['ffmpeg', '-f', 'video4linux2', '-i', device,
               '-vframes', '1', '-y', out_path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            return {'text': '[Camera] ffmpeg not installed. Install with: sudo apt install ffmpeg', 'type': 'improver_error'}
        except subprocess.TimeoutExpired:
            return {'text': '[Camera] Capture timed out.', 'type': 'improver_error'}

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            return {'text': f'[Camera] No camera detected at {device}.', 'type': 'improver_error'}

        size = os.path.getsize(out_path)
        details = f'Captured at {ts} | Device: {device} | File: {out_path} | Size: {size/1024:.1f} KB'

        if has_pillow:
            try:
                img = Image.open(out_path)
                w, h = img.size
                mode = img.mode
                fmt = img.format
                details += f' | Resolution: {w}x{h} | Mode: {mode} | Format: {fmt}'
            except Exception:
                pass

        text = cmd_text.lower()
        if 'describe' in text or 'see' in text or 'what' in text:
            try:
                import requests
                model = self.system.model_manager.get_current_model() if self.system and hasattr(self.system, 'model_manager') else 'llava'
                import base64
                with open(out_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                r = requests.post(
                    'http://localhost:11434/api/generate',
                    json={'model': model, 'prompt': 'Describe this image in detail.',
                          'images': [b64], 'stream': False},
                    timeout=60
                )
                if r.status_code == 200:
                    desc = r.json().get('response', '')
                    return {'text': f'[Camera] {details}\n\nWhat I see:\n{desc}', 'type': 'improver_camera'}
            except Exception:
                pass
            return {'text': f'[Camera] {details}\n\nVision model not available. Install llava: ollama pull llava', 'type': 'improver_camera'}

        return {'text': f'[Camera] {details}', 'type': 'improver_camera'}

    def handle_motion(self, cmd_text):
        """Control motion detection service."""
        import subprocess
        text = cmd_text.lower()
        if 'status' in text or 'running' in text or 'check' in text:
            r = subprocess.run(['systemctl', 'is-active', 'motion'], capture_output=True, text=True, timeout=5)
            status = r.stdout.strip()
            if status == 'active':
                conf = '/etc/motion/motion.conf'
                device = '/dev/video0'
                try:
                    with open(conf) as f:
                        for line in f:
                            if line.startswith('video_device'):
                                parts = line.split()
                                if len(parts) > 1:
                                    device = parts[1]
                                    break
                except Exception:
                    pass
                return {'text': f'[Motion] Active | Camera: {device} | Stream: http://localhost:8081 | Web: http://localhost:8080 | Output: /var/lib/motion', 'type': 'improver_motion'}
            return {'text': f'[Motion] Status: {status}', 'type': 'improver_motion'}
        if 'stop' in text or 'off' in text:
            r = _run_sudo(['systemctl', 'stop', 'motion'], timeout=10)
            if r.returncode == 0:
                return {'text': '[Motion] Stopped.', 'type': 'improver_motion'}
            return {'text': f'[Motion] Failed to stop: {r.stderr}', 'type': 'improver_error'}
        if 'start' in text or 'on' in text:
            r = _run_sudo(['systemctl', 'start', 'motion'], timeout=10)
            if r.returncode == 0:
                return {'text': '[Motion] Started.', 'type': 'improver_motion'}
            return {'text': f'[Motion] Failed to start: {r.stderr}', 'type': 'improver_error'}
        if 'restart' in text:
            r = _run_sudo(['systemctl', 'restart', 'motion'], timeout=10)
            if r.returncode == 0:
                return {'text': '[Motion] Restarted.', 'type': 'improver_motion'}
            return {'text': f'[Motion] Failed: {r.stderr}', 'type': 'improver_error'}
        r = subprocess.run(['systemctl', 'is-active', 'motion'], capture_output=True, text=True, timeout=5)
        return {'text': f'[Motion] Status: {r.stdout.strip()} | Say "motion status/start/stop/restart"', 'type': 'improver_motion'}

    def handle_notify(self, cmd_text):
        """Configure notifications for motion detection."""
        import subprocess, json
        text = cmd_text.lower()
        cfg_path = os.path.expanduser("~/.config/soms/notify.json")
        script_path = os.path.expanduser("~/.config/soms/motion_notify.py")
        motion_conf = "/etc/motion/motion.conf"
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
        except Exception:
            cfg = {"email": {"enabled": False, "server": "", "port": 587, "user": "", "password": "", "to": "", "from": ""}}

        if 'setup' in text or 'configure' in text or 'config' in text:
            return {'text': f'[Notify] To configure email, edit:\n  {cfg_path}\nSet email.enabled=true, server, port, user, password, to, from.\nThen say "notify enable" to activate.', 'type': 'improver_notify'}

        if 'enable' in text or 'on' in text:
            cfg["email"]["enabled"] = True
            with open(cfg_path, "w") as f:
                json.dump(cfg, f, indent=2)
            _run_sudo(['sed', '-i', f'|^on_event_end|s|^;*||', motion_conf], timeout=5)
            _run_sudo(['sed', '-i', f'|^on_movie_end|s|^;*||', motion_conf], timeout=5)
            _run_sudo(['sed', '-i', f'|^on_event_end|s|.*|on_event_end {script_path} %f|', motion_conf], timeout=5)
            _run_sudo(['systemctl', 'restart', 'motion'], timeout=10)
            return {'text': '[Notify] Email notifications enabled and motion restarted.', 'type': 'improver_notify'}

        if 'disable' in text or 'off' in text:
            cfg["email"]["enabled"] = False
            with open(cfg_path, "w") as f:
                json.dump(cfg, f, indent=2)
            _run_sudo(['sed', '-i', 's|^on_event_end|;on_event_end|', motion_conf], timeout=5)
            _run_sudo(['systemctl', 'restart', 'motion'], timeout=10)
            return {'text': '[Notify] Email notifications disabled.', 'type': 'improver_notify'}

        if 'status' in text or 'check' in text:
            e = cfg.get("email", {})
            status = "ENABLED" if e.get("enabled") else "DISABLED"
            to = e.get("to", "not set")
            return {'text': f'[Notify] Email: {status} | To: {to}\nSay "notify setup" to configure, "notify enable" to activate.', 'type': 'improver_notify'}

        return {'text': f'[Notify] Say "notify status", "notify setup", "notify enable", or "notify disable".', 'type': 'improver_notify'}
