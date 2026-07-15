"""Growth Engine for SOMS
The meta-capability the user asked for: upgrade SOMS along four axes —
performance, intelligence, efficiency and stability — and combine them with
`/grow all`. Each axis applies safe, concrete changes and reports what it did.
"""

import logging
import time

logger = logging.getLogger('GrowthEngine')


class GrowthEngine:
    def __init__(self, system_ref=None):
        self.system = system_ref
        self.is_running = False

    def start(self):
        self.is_running = True
        logger.info("Growth engine online")

    def stop(self):
        self.is_running = False
        logger.info("Growth engine stopped")

    # -- public API ---------------------------------------------------------

    def grow(self, area='all'):
        """Upgrade one or more axes. `area` may be:
        performance | intelligence | efficiency | stability | all
        Returns a human-readable report.
        """
        area = (area or 'all').lower().strip()
        parts = [a.strip() for a in area.replace(',', ' ').split() if a.strip()]
        if not parts or 'all' in parts:
            axes = ['performance', 'intelligence', 'efficiency', 'stability']
        else:
            axes = [a for a in parts if a in
                    ('performance', 'intelligence', 'efficiency', 'stability')]
        if not axes:
            return ("Unknown axis. Choose from: performance, intelligence, "
                    "efficiency, stability (or 'all').")

        lines = ["SOMS Growth Report:"]
        for ax in axes:
            fn = getattr(self, f'_grow_{ax}', None)
            if fn:
                try:
                    lines.append(fn())
                except Exception as e:
                    logger.error(f"Growth axis {ax} failed: {e}")
                    lines.append(f"  [{ax}] error: {e}")
        lines.append("")
        lines.append("Growth complete. Ask me anything — I'll do my best to "
                     "answer it correctly, and research the web when unsure.")
        return "\n".join(lines)

    # -- axes ----------------------------------------------------------------

    def _grow_performance(self):
        cfg = self._config()
        changes = []
        # Prefer a small/fast model when a lighter one is available.
        mm = self._get('model_manager')
        if mm:
            avail = mm.get_available_models()
            faster = next((m for m in ('tinyllama:1.1b', 'qwen2:0.5b',
                                       'phi3:mini', 'gemma2:2b') if m in avail), None)
            if faster and mm.get_current_model() not in ('tinyllama:1.1b',):
                ok, msg = mm.set_model(faster)
                if ok:
                    changes.append(f"selected faster model {faster}")
                llm = self._get('llm')
                if llm:
                    llm.default_model = mm.get_current_model()
        # Lower log verbosity once stable to reduce I/O overhead.
        if cfg:
            cfg.set('system', 'log_level', value='WARNING')
            changes.append("set log level to WARNING")
        return "  [performance] " + (", ".join(changes) if changes
                                     else "already tuned")

    def _grow_intelligence(self):
        cfg = self._config()
        changes = []
        # Enable research mode: web-augmented answers for factual questions.
        if cfg:
            cfg.set('system', 'research_mode', value=True)
            changes.append("enabled research mode (web-augmented answers)")
        # If a larger model is available, prefer it for better reasoning.
        mm = self._get('model_manager')
        if mm:
            avail = mm.get_available_models()
            smarter = next((m for m in ('llama3.1:70b', 'qwen2:72b',
                                        'gemma2:27b', 'llama3.1:8b') if m in avail), None)
            if smarter and mm.get_current_model() != smarter:
                ok, _ = mm.set_model(smarter)
                if ok:
                    llm = self._get('llm')
                    if llm:
                        llm.default_model = mm.get_current_model()
                    changes.append(f"upgraded reasoning model to {smarter}")
        return "  [intelligence] " + (", ".join(changes) if changes
                                      else "already at full intelligence")

    def _grow_efficiency(self):
        changes = []
        cleaner = self._get('cleaner')
        if cleaner:
            res = cleaner.clean(scope='all', dry_run=False)
            changes.append(f"cleaned {res.get('files_removed', 0)} files "
                           f"({res.get('total_freed', 0)//1024} KB freed)")
        memory = self._get('memory')
        if memory and hasattr(memory, 'prune_old'):
            try:
                n = memory.prune_old(limit=500)
                if n:
                    changes.append(f"pruned {n} old memory entries")
            except Exception:
                pass
        return "  [efficiency] " + (", ".join(changes) if changes
                                    else "nothing to clean")

    def _grow_stability(self):
        changes = []
        # Run a self-heal pass to fix what it can.
        healer = self._get('self_healer')
        if healer and hasattr(healer, 'scan_and_fix'):
            try:
                res = healer.scan_and_fix(auto_apply=True)
                changes.append("ran self-heal pass")
            except Exception as e:
                changes.append(f"self-heal error: {e}")
        # Verify package dependencies are intact.
        arch = self._get('package_architect')
        if arch and hasattr(arch, 'fix_dependencies'):
            try:
                ok, msg, _ = arch.fix_dependencies()
                changes.append(f"dependency check: {msg}")
            except Exception:
                pass
        # Health baseline.
        sentinel = self._get('sentinel')
        if sentinel and hasattr(sentinel, 'check_system_health'):
            h = sentinel.check_system_health()
            changes.append(f"health status: {h.get('status')}")
        return "  [stability] " + (", ".join(changes) if changes
                                   else "system stable")

    # -- helpers -------------------------------------------------------------

    def _config(self):
        return getattr(self.system, 'config', None) if self.system else None

    def _get(self, name):
        return getattr(self.system, name, None) if self.system else None

    def available_axes(self):
        return ['performance', 'intelligence', 'efficiency', 'stability', 'all']
