"""Diagnostician Module for SOMS
System analysis and diagnostics — actually inspects the host and reports
real findings (resource usage, Ollama/model availability, optional module
health) instead of faking a "healthy" result.
"""

import logging
import shutil
import subprocess
import time

logger = logging.getLogger('Diagnostician')


class Diagnostician:
    def __init__(self, config):
        self.config = config
        self.is_running = False
        self.last_report = None
        self.last_update = 0

    def start(self):
        self.is_running = True
        logger.info("Diagnostician started")

    def stop(self):
        self.is_running = False
        logger.info("Diagnostician stopped")

    def update(self, system=None):
        """Run one maintenance diagnostic pass and cache the latest report."""
        if not self.is_running:
            return None
        self.last_report = self.run_diagnostics(system)
        self.last_update = time.time()
        alert_count = len(self.last_report.get('alerts', []))
        logger.info(
            "Diagnostic update: status=%s alerts=%s",
            self.last_report.get('status', 'unknown'),
            alert_count,
        )
        return self.last_report

    def _read_cpu(self):
        try:
            import psutil
            return psutil.cpu_percent(interval=0.3)
        except Exception:
            return None

    def _read_memory(self):
        try:
            import psutil
            vm = psutil.virtual_memory()
            return vm.percent, vm.available // (1024 * 1024)
        except Exception:
            return None, None

    def _read_disk(self):
        try:
            import psutil
            du = psutil.disk_usage('/')
            return du.percent, du.free // (1024 * 1024 * 1024)
        except Exception:
            return None, None

    def _ollama_status(self):
        try:
            r = subprocess.run(['ollama', 'list'], capture_output=True,
                               text=True, timeout=5)
            if r.returncode == 0:
                models = [l.split()[0] for l in r.stdout.strip().split('\n')[1:]
                          if l.strip()]
                return True, models
        except Exception:
            pass
        return False, []

    def run_diagnostics(self, system=None):
        """Run a real diagnostic pass and return a structured report.

        Returns a dict with top-level 'status' ('healthy'/'warning'/'critical'),
        a list of 'components' (each with name/status/detail), and 'alerts'.
        """
        components = []
        alerts = []

        cpu = self._read_cpu()
        if cpu is not None:
            state = 'healthy'
            if cpu >= 90:
                state = 'critical'
                alerts.append(f"CPU usage critical: {cpu:.0f}%")
            elif cpu >= 75:
                state = 'warning'
                alerts.append(f"CPU usage high: {cpu:.0f}%")
            components.append({'name': 'cpu', 'status': state, 'detail': f"{cpu:.0f}%"})

        mem_pct, mem_free = self._read_memory()
        if mem_pct is not None:
            state = 'healthy'
            if mem_pct >= 90:
                state = 'critical'
                alerts.append(f"Memory usage critical: {mem_pct:.0f}%")
            elif mem_pct >= 80:
                state = 'warning'
                alerts.append(f"Memory usage high: {mem_pct:.0f}%")
            components.append({'name': 'memory', 'status': state,
                               'detail': f"{mem_pct:.0f}% ({mem_free} MB free)"})

        disk_pct, disk_free = self._read_disk()
        if disk_pct is not None:
            state = 'healthy'
            if disk_pct >= 95:
                state = 'critical'
                alerts.append(f"Disk usage critical: {disk_pct:.0f}%")
            elif disk_pct >= 85:
                state = 'warning'
                alerts.append(f"Disk usage high: {disk_pct:.0f}%")
            components.append({'name': 'disk', 'status': state,
                               'detail': f"{disk_pct:.0f}% ({disk_free} GB free)"})

        ollama_up, models = self._ollama_status()
        components.append({
            'name': 'ollama',
            'status': 'healthy' if ollama_up else 'warning',
            'detail': (f"{len(models)} model(s) available" if ollama_up
                       else "not running — chat/vision unavailable"),
        })
        if not ollama_up:
            alerts.append("Ollama is not running; start it with `ollama serve`")

        if system is not None:
            for name in ('sentinel', 'orchestrator', 'agent', 'diagnostician',
                         'architect', 'engineer', 'auditor', 'evolver',
                         'voice', 'memory', 'model_manager', 'improver',
                         'package_architect', 'self_healer', 'cleaner'):
                mod = getattr(system, name, None)
                running = getattr(mod, 'is_running', None)
                if running is True:
                    components.append({'name': name, 'status': 'healthy',
                                       'detail': 'online'})
                elif running is False:
                    components.append({'name': name, 'status': 'warning',
                                       'detail': 'stopped'})
                elif mod is not None:
                    components.append({'name': name, 'status': 'healthy',
                                       'detail': 'loaded'})

        if any(c['status'] == 'critical' for c in components):
            status = 'critical'
        elif any(c['status'] == 'warning' for c in components):
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'status': status,
            'timestamp': time.time(),
            'components': components,
            'alerts': alerts,
        }
