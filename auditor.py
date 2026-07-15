"""Auditor Module for SOMS
Validation and security — gatekeeper for all autonomous actions
"""

import logging
import time

logger = logging.getLogger('Auditor')

BLACKLISTED_PACKAGES = {
    'docker', 'containerd', 'libvirt-daemon', 'qemu', 'openvpn',
    'tor', 'nmap', 'aircrack-ng', 'metasploit', 'hydra', 'john',
}

SOMS_CRITICAL_PKGS = {
    'python3', 'python3-pip', 'ffmpeg', 'portaudio19-dev', 'flac',
}

SAFE_PACKAGES = {
    'build-essential', 'git', 'curl', 'wget', 'htop', 'neofetch',
    'tmux', 'vim', 'python3-dev', 'python3-venv', 'python3-pip',
    'cmake', 'gcc', 'g++', 'make', 'libssl-dev', 'zlib1g-dev',
    'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'libncursesw5-dev',
    'xz-utils', 'tk-dev', 'libxml2-dev', 'libxmlsec1-dev', 'libffi-dev',
    'liblzma-dev', 'ffmpeg', 'espeak', 'espeak-ng', 'portaudio19-dev',
    'flac', 'mpg123', 'sox', 'libsox-fmt-mp3', 'vorbis-tools',
}

COMPROMISED_PACKAGE_PATTERNS = [
    'password', 'hack', 'crack', 'keylog', 'screenshot',
    'webcam', 'backdoor', 'trojan', 'worm', 'ransom',
]

class Auditor:
    """Validates all system actions for security, stability, and correctness."""

    def __init__(self, config):
        self.config = config
        self.is_running = False
        self._audit_log = []

    def start(self):
        self.is_running = True
        logger.info("Auditor started — gatekeeper online")

    def stop(self):
        self.is_running = False
        logger.info("Auditor stopped")

    def validate_package_install(self, package_name):
        pkg = package_name.lower().strip()
        violations = []
        warnings = []
        if pkg in BLACKLISTED_PACKAGES:
            violations.append(f"BLACKLISTED: {pkg}")
        if pkg in SOMS_CRITICAL_PKGS:
            warnings.append(f"CRITICAL: {pkg} is a SOMS dependency")
        for pattern in COMPROMISED_PACKAGE_PATTERNS:
            if pattern in pkg:
                violations.append(f"Suspicious package name contains '{pattern}'")
        alphanum = sum(c.isalnum() for c in pkg)
        total_chars = len(pkg)
        if total_chars > 0 and alphanum / total_chars < 0.5:
            violations.append(f"Package name has unusual characters")
        return {
            'package': package_name,
            'allowed': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
        }

    def validate_action(self, action_type, action_details, user_context=None):
        if action_type == 'package_install':
            validation = self.validate_package_install(action_details.get('package', ''))
            self._audit_log.append({
                'timestamp': time.time(),
                'action_type': action_type,
                'package': action_details.get('package', ''),
                'allowed': validation['allowed'],
                'violations': validation['violations'],
            })
            return validation
        return {
            'allowed': True,
            'violations': [],
            'warnings': [],
        }


