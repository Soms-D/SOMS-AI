"""Sentinel Module for SOMS
System monitoring and telemetry module
"""

import time
import logging
import subprocess

logger = logging.getLogger('Sentinel')
class Sentinel:
    """Continuous, low-overhead monitoring of system telemetry and hardware states."""

    def __init__(self, config):
        self.config = config
        self.is_running = False

    def start(self):
        """Start system monitoring."""
        self.is_running = True
        logger.info("Sentinel monitoring started")

    def stop(self):
        """Stop monitoring."""
        self.is_running = False
        logger.info("Sentinel monitoring stopped")

    def check_system_health(self):
        """Perform a real, lightweight system health check.

        Returns a dict with 'status' ('healthy'/'warning'/'critical'),
        'timestamp', a 'components' map and an 'alerts' list.
        """
        components = {}
        alerts = []

        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.2)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
        except Exception:
            cpu = mem = disk = None

        if cpu is not None:
            components['cpu'] = f"{cpu:.0f}%"
            if cpu >= 90:
                alerts.append(f"CPU critical: {cpu:.0f}%")
            elif cpu >= 75:
                alerts.append(f"CPU high: {cpu:.0f}%")
        if mem is not None:
            components['memory'] = f"{mem:.0f}%"
            if mem >= 90:
                alerts.append(f"Memory critical: {mem:.0f}%")
        if disk is not None:
            components['disk'] = f"{disk:.0f}%"
            if disk >= 95:
                alerts.append(f"Disk critical: {disk:.0f}%")

        try:
            r = subprocess.run(['ollama', 'list'], capture_output=True,
                               text=True, timeout=5)
            components['ollama'] = 'online' if r.returncode == 0 else 'offline'
        except Exception:
            components['ollama'] = 'offline'

        if any(a and ('critical' in a.lower()) for a in alerts):
            status = 'critical'
        elif alerts:
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'status': status,
            'timestamp': time.time(),
            'components': components,
            'alerts': alerts,
        }
