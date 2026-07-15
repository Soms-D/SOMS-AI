"""Architect Module for SOMS
Strategic planning and decision-making. Turns a high-level goal into an
ordered, actionable plan, and can produce a system overview from live
diagnostics. Operates fully offline (no network/LLM required).
"""

import logging

logger = logging.getLogger('Architect')


class Architect:
    def __init__(self, config):
        self.config = config
        self.is_running = False
        # Built-in playbooks mapping goal keywords -> ordered steps.
        self._playbooks = {
            'health': [
                "Run a diagnostic pass (Diagnostician.run_diagnostics)",
                "Review alerts and rank by severity",
                "Apply safe fixes via Self-Healer / Cleaner",
                "Re-run diagnostics to confirm recovery",
            ],
            'cleanup': [
                "Inventory logs, temp files, caches and state files",
                "Run Cleaner in dry-run mode for review",
                "Remove only files older than the retention window",
                "Report space freed",
            ],
            'install': [
                "Validate the package name with the Auditor",
                "Update package indexes",
                "Install via PackageArchitect with sudo",
                "Verify the binary is present and runnable",
            ],
            'secure': [
                "Audit open services and listening ports",
                "Check for broken package dependencies",
                "Review recent log anomalies via Evolver",
                "Apply hardening suggestions",
            ],
            'learn': [
                "Enable learning mode",
                "Capture the current interaction pattern",
                "Summarize new capabilities discovered",
            ],
        }

    def start(self):
        self.is_running = True
        logger.info("Architect started")

    def stop(self):
        self.is_running = False
        logger.info("Architect stopped")

    def propose_plan(self, goal, system=None):
        """Return an ordered plan (list of steps) for a natural-language goal.

        Falls back to a generic plan when no playbook matches.
        """
        if not goal:
            return ["Specify a goal for SOMS to plan.",
                    "Examples: 'plan a health check', 'plan cleanup', 'plan to install a package'."]

        g = goal.lower()
        chosen = None
        for key in self._playbooks:
            if key in g:
                chosen = key
                break

        if chosen:
            steps = list(self._playbooks[chosen])
        else:
            steps = [
                f"Analyze goal: '{goal}'",
                "Decompose into subtasks",
                "Delegate each subtask to the appropriate brain module",
                "Monitor execution and report results",
            ]

        if system is not None and hasattr(system, 'diagnostician'):
            try:
                diag = system.diagnostician.run_diagnostics(system)
                if diag.get('alerts'):
                    steps.insert(0, "Pre-check found alerts: "
                                 + "; ".join(diag['alerts']))
            except Exception:
                pass

        return steps

    def system_overview(self, system=None):
        """Summarize the current system state for planning purposes."""
        lines = ["SOMS System Overview:"]
        if system is not None and hasattr(system, 'resources'):
            try:
                s = system.resources.get_status()
                lines.append(f"  Uptime: {s.get('uptime_hours', '?')} h")
                lines.append(f"  CPU: {s.get('cpu_usage', '?')}  "
                             f"RAM: {s.get('memory_usage', '?')}  "
                             f"Disk: {s.get('disk_usage', '?')}")
            except Exception:
                pass
        lines.append("  Modules: 7BRAIN-CORE (Sentinel, Diagnostician, "
                     "Architect, Engineer, Auditor, Evolver, Orchestrator)")
        return "\n".join(lines)
