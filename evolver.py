"""Evolver Module for SOMS
Self-evolution engine — reads logs, detects patterns, drives improvements
"""

import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger('Evolver')

LOG_FILE = Path(__file__).parent.parent / 'soms.log'

ERROR_PATTERNS = [
    (re.compile(r'error', re.I), 'error'),
    (re.compile(r'failed?', re.I), 'error'),
    (re.compile(r'traceback', re.I), 'error'),
    (re.compile(r'exception', re.I), 'error'),
    (re.compile(r'timeout', re.I), 'warning'),
    (re.compile(r'warning', re.I), 'warning'),
    (re.compile(r'unavailable', re.I), 'warning'),
    (re.compile(r'not found', re.I), 'warning'),
    (re.compile(r'no module', re.I), 'missing_dep'),
    (re.compile(r'import.*error', re.I), 'missing_dep'),
    (re.compile(r'module.*not found', re.I), 'missing_dep'),
    (re.compile(r'connection refused', re.I), 'network'),
    (re.compile(r'permission denied', re.I), 'permission'),
    (re.compile(r'disk.*full', re.I), 'disk'),
    (re.compile(r'memory.*error', re.I), 'memory'),
]

class Evolver:
    """Analyzes system logs, identifies failure patterns, and recommends evolution steps."""

    def __init__(self, config):
        self.config = config
        self.is_running = False
        self._last_scan = 0
        self._scan_interval = 60
        self._analysis_cache = {}
        self._evolution_log = []
        self._recommendations = []

    def start(self):
        self.is_running = True
        self._last_scan = time.time()
        logger.info("Evolver started — self-evolution engine online")

    def stop(self):
        self.is_running = False
        logger.info("Evolver stopped")

    def _read_logs(self, max_lines=500):
        if not LOG_FILE.exists():
            return []
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
            return lines[-max_lines:]
        except Exception as e:
            logger.debug(f"Evolver read logs: {e}")
            return []

    def analyze_logs(self, force=False):
        now = time.time()
        if not force and (now - self._last_scan) < self._scan_interval:
            return self._analysis_cache
        lines = self._read_logs()
        if not lines:
            self._analysis_cache = {'status': 'no_logs', 'issues': []}
            return self._analysis_cache
        categorized = defaultdict(list)
        agent_errors = defaultdict(int)
        for line in lines:
            for pattern, category in ERROR_PATTERNS:
                if pattern.search(line):
                    categorized[category].append(line.strip())
                    for agent in ['Sentinel', 'Diagnostician', 'Architect', 'Engineer',
                                  'Auditor', 'Evolver', 'Orchestrator', 'Agent',
                                  'VoiceInterface', 'PackageArchitect', 'ImproverAgent',
                                  'MemoryLayer', 'GUI', 'TUI']:
                        if agent in line:
                            agent_errors[agent] += 1
                    break
        total_errors = sum(len(v) for v in categorized.values())
        top_agents = sorted(agent_errors.items(), key=lambda x: -x[1])[:3]
        recommendations = self._generate_recommendations(categorized, total_errors)
        self._analysis_cache = {
            'timestamp': now,
            'total_logs': len(lines),
            'total_issues': total_errors,
            'categories': {k: len(v) for k, v in categorized.items()},
            'samples': {k: v[-3:] for k, v in categorized.items()},
            'top_agents': top_agents,
            'recommendations': recommendations,
        }
        self._last_scan = now
        if recommendations:
            self._recommendations.extend(recommendations)
        if total_errors > 0:
            self._evolution_log.append({
                'timestamp': now,
                'issues_found': total_errors,
                'categories': dict(categorized),
            })
        return self._analysis_cache

    def _generate_recommendations(self, categorized, total_errors):
        recs = []
        if total_errors > 20:
            recs.append({'type': 'maintenance', 'priority': 'high', 'message': 'High error rate detected — run /system check'})
        if categorized.get('missing_dep'):
            pkgs = set()
            for line in categorized['missing_dep']:
                m = re.search(r'(?:module|package|import)\s+[\'"]?(\w+)', line, re.I)
                if m:
                    pkgs.add(m.group(1))
            for pkg in pkgs:
                recs.append({'type': 'install', 'priority': 'medium', 'message': f"Install missing dependency: {pkg}"})
        if categorized.get('disk'):
            recs.append({'type': 'maintenance', 'priority': 'high', 'message': 'Disk space issue detected — investigate storage'})
        if categorized.get('memory'):
            recs.append({'type': 'tuning', 'priority': 'medium', 'message': 'Memory pressure detected — consider reducing model size'})
        if not recs:
            recs.append({'type': 'info', 'priority': 'low', 'message': 'No actionable issues detected — system is stable'})
        return recs

    def evolve(self):
        analysis = self.analyze_logs(force=True)
        if analysis.get('status') == 'no_logs':
            return {
                'timestamp': time.time(),
                'stage': 'skipped',
                'reason': 'no_logs',
                'issues_found': 0,
                'recommendations': [],
            }
        return {
            'timestamp': time.time(),
            'stage': 'completed',
            'issues_found': analysis.get('total_issues', 0),
            'categories': analysis.get('categories', {}),
            'recommendations': analysis.get('recommendations', []),
        }

    def get_evolution_readiness(self):
        now = time.time()
        return (now - self._last_scan) >= self._scan_interval

    def get_recommendations(self):
        return self._recommendations[-10:] if self._recommendations else []

    def get_status(self):
        analysis = self._analysis_cache if self._analysis_cache else self.analyze_logs()
        return {
            'online': self.is_running,
            'last_scan': analysis.get('timestamp', 0),
            'total_logs_scanned': analysis.get('total_logs', 0),
            'total_issues_found': analysis.get('total_issues', 0),
            'categories': analysis.get('categories', {}),
            'recommendations': self.get_recommendations(),
            'evolution_cycles': len(self._evolution_log),
        }
