"""Cleaner Module for SOMS
Self-cleaning function that removes temporary files, old logs, and caches.
"""

import os
import shutil
import time
import logging
import glob as glob_mod

logger = logging.getLogger('Cleaner')

class Cleaner:
    def __init__(self, system_ref=None):
        self.system = system_ref

    def clean(self, scope='all', dry_run=False):
        """Run self-cleaning across specified scopes.
        
        Args:
            scope: 'logs', 'temp', 'cache', 'state', or 'all'
            dry_run: If True, report what would be deleted without deleting.
        
        Returns:
            dict with keys: total_freed, files_removed, details
        """
        results = {
            'total_freed': 0,
            'files_removed': 0,
            'details': [],
        }

        if scope in ('logs', 'all'):
            self._clean_logs(results, dry_run)
        if scope in ('temp', 'all'):
            self._clean_temp(results, dry_run)
        if scope in ('cache', 'all'):
            self._clean_cache(results, dry_run)
        if scope in ('state', 'all'):
            self._clean_state(results, dry_run)

        return results

    def _clean_logs(self, results, dry_run):
        """Remove old log files (>1 day) in the project directory."""
        pattern = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '*.log')
        count = 0
        freed = 0
        cutoff = time.time() - 86400
        for f in glob_mod.glob(pattern):
            try:
                stat = os.stat(f)
                if stat.st_mtime < cutoff:
                    freed += stat.st_size
                    count += 1
                    if not dry_run:
                        os.remove(f)
                        logger.info(f"Removed old log: {f}")
                    results['details'].append(f"Removed old log: {f}")
            except OSError:
                pass
        results['files_removed'] += count
        results['total_freed'] += freed
        if count:
            logger.info(f"Cleaned {count} old log files ({freed/1024:.1f} KB)")

    def _clean_temp(self, results, dry_run):
        """Remove temporary files from /tmp created by SOMS."""
        count = 0
        freed = 0
        for root, dirs, files in os.walk('/tmp'):
            for f in files:
                if (f.startswith('soms_') or f.startswith('tmp')) and f.endswith(('.wav', '.mp3', '.txt', '.py')):
                    path = os.path.join(root, f)
                    try:
                        stat = os.stat(path)
                        freed += stat.st_size
                        count += 1
                        if not dry_run:
                            os.remove(path)
                            logger.info(f"Removed temp: {path}")
                        results['details'].append(f"Removed temp: {path}")
                    except OSError:
                        pass
        results['files_removed'] += count
        results['total_freed'] += freed
        if count:
            logger.info(f"Cleaned {count} temp files ({freed/1024:.1f} KB)")

    def _clean_cache(self, results, dry_run):
        """Remove __pycache__ directories in the project."""
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        count = 0
        freed = 0
        for root, dirs, files in os.walk(project_dir):
            if '__pycache__' in dirs:
                path = os.path.join(root, '__pycache__')
                try:
                    size = 0
                    for dirpath, _, filenames in os.walk(path):
                        for fn in filenames:
                            try:
                                size += os.path.getsize(os.path.join(dirpath, fn))
                            except OSError:
                                pass
                    freed += size
                    count += 1
                    if not dry_run:
                        shutil.rmtree(path)
                        logger.info(f"Removed cache: {path}")
                    results['details'].append(f"Removed cache: {path}")
                except OSError:
                    pass
        results['files_removed'] += count
        results['total_freed'] += freed
        if count:
            logger.info(f"Cleaned {count} __pycache__ dirs ({freed/1024:.1f} KB)")

    def _clean_state(self, results, dry_run):
        """Remove persisted system state files."""
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_files = ['soms_state.json']
        count = 0
        freed = 0
        for sf in state_files:
            path = os.path.join(project_dir, sf)
            if os.path.exists(path):
                try:
                    size = os.path.getsize(path)
                    freed += size
                    count += 1
                    if not dry_run:
                        os.remove(path)
                        logger.info(f"Removed state: {path}")
                    results['details'].append(f"Removed state: {path}")
                except OSError:
                    pass
        results['files_removed'] += count
        results['total_freed'] += freed
        if count:
            logger.info(f"Cleaned {count} state files ({freed/1024:.1f} KB)")

    def report(self, results):
        """Generate a human-readable report from cleaning results."""
        lines = [
            f"Self-Cleaning Complete:",
            f"  Files removed: {results['files_removed']}",
            f"  Space freed: {results['total_freed']/1024:.1f} KB",
        ]
        if results['details']:
            for d in results['details'][:10]:
                lines.append(f"  • {d}")
            if len(results['details']) > 10:
                lines.append(f"  ... and {len(results['details']) - 10} more")
        else:
            lines.append("  Nothing to clean — system is tidy.")
        return '\n'.join(lines)

    def start(self):
        logger.info("Cleaner ready")

    def stop(self):
        logger.info("Cleaner stopped")
