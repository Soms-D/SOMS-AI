"""Engineer Module for SOMS
System management and execution. Runs safe, validated local tasks
(no shell injection) delegated by the orchestrator/agent. Network-facing
operations are delegated to the Skills toolkit where possible.
"""

import logging
import subprocess
import shlex

logger = logging.getLogger('Engineer')

# Commands the Engineer is allowed to run directly (no free-form shell).
_ALLOWED_COMMANDS = {
    'ping': ['ping', '-c', '4'],
    'uptime': ['uptime'],
    'df': ['df', '-h'],
    'free': ['free', '-h'],
    'uname': ['uname', '-a'],
    'date': ['date'],
    'whoami': ['whoami'],
    'ps': ['ps', 'aux'],
}


class Engineer:
    def __init__(self, config):
        self.config = config
        self.is_running = False

    def start(self):
        self.is_running = True
        logger.info("Engineer started")

    def stop(self):
        self.is_running = False
        logger.info("Engineer stopped")

    def run_shell(self, command, timeout=30):
        """Run a single allowed command safely (no shell, no injection).

        Returns (ok, output). Refuses anything not in the allow-list or that
        looks like shell metacharacters / chaining.
        """
        cmd = command.strip()
        if not cmd:
            return False, "Empty command."
        if any(ch in cmd for ch in ';|&$`><\n'):
            return False, ("Refused: shell metacharacters are not allowed. "
                           "Use a single, simple command.")
        parts = shlex.split(cmd)
        if not parts:
            return False, "Empty command."
        base = parts[0]
        if base in _ALLOWED_COMMANDS:
            argv = _ALLOWED_COMMANDS[base] + parts[1:]
        else:
            # Allow an explicit allow-listed binary only.
            if base not in _ALLOWED_COMMANDS and base not in ('echo',):
                return False, (f"Refused: '{base}' is not in the allow-list. "
                               "Allowed: " + ", ".join(sorted(_ALLOWED_COMMANDS)))
            argv = parts
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            out = (r.stdout or r.stderr or "").strip()
            return (r.returncode == 0), out or "(no output)"
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout}s."
        except Exception as e:
            return False, f"Error: {e}"

    def run_task(self, task, system=None):
        """Execute a named higher-level task, delegating to the right module."""
        task = (task or '').lower()
        if task in ('health', 'diagnostics', 'check'):
            if system is not None and hasattr(system, 'diagnostician'):
                d = system.diagnostician.run_diagnostics(system)
                return True, (f"Status: {d['status']}\n"
                              + "\n".join(f"  - {c['name']}: {c['detail']}"
                                          for c in d['components']))
            return False, "Diagnostician unavailable."
        if task in ('overview', 'status'):
            if system is not None and hasattr(system, 'architect'):
                return True, system.architect.system_overview(system)
            return False, "Architect unavailable."
        return False, f"Unknown task: '{task}'."
