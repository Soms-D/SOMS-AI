"""Self-Healer Module for SOMS

Scans the runtime log for errors and attempts safe, automatic fixes:
  - Missing Python modules  -> pip install (within the venv)
  - Corrupt memory store    -> repair / re-init ChromaDB
  - Failed brain modules     -> restart them
It reports (without acting) on issues that need the user or the system
(e.g. Ollama not running, missing system packages, permission errors).
"""

import logging
import os
import re
import sys
import subprocess
import threading
import time

logger = logging.getLogger('SelfHealer')

# Map an importable module name -> the pip package that provides it.
MODULE_TO_PIP = {
    'cv2': 'opencv-python-headless',
    'PIL': 'Pillow',
    'numpy': 'numpy',
    'speech_recognition': 'SpeechRecognition',
    'faster_whisper': 'faster-whisper',
    'pyaudio': 'PyAudio',
    'chromadb': 'chromadb',
    'webrtcvad': 'webrtcvad',
    'ollama': 'ollama',
    'rich': 'rich',
    'textual': 'textual',
    'flet': 'flet',
    'psutil': 'psutil',
    'prompt_toolkit': 'prompt_toolkit',
    'requests': 'requests',
}

LOG_FILE = 'soms.log'
_AUTO_INTERVAL = 300  # seconds between automatic self-heal passes


class SelfHealer:
    def __init__(self, system_ref):
        self.system = system_ref
        self.config = system_ref.config
        self.is_running = False
        self._reported = set()      # signatures already reported this session
        self._thread = None

    # ---- scanning -------------------------------------------------------

    def _read_recent_errors(self, max_lines=4000):
        if not os.path.exists(LOG_FILE):
            return []
        out = []
        try:
            with open(LOG_FILE, 'r', errors='ignore') as f:
                for line in f:
                    if any(k in line for k in ('ERROR', 'Error', 'Traceback',
                                                'Exception', 'CRITICAL', 'CRIT')):
                        out.append(line.rstrip())
        except Exception:
            pass
        return out[-max_lines:]

    def _signature(self, line):
        if 'No module named' in line:
            mm = re.search(r"No module named '([^']+)'", line)
            if mm:
                return f"missing:{mm.group(1)}"
        m = re.search(r'(ModuleNotFoundError|ImportError|ChromaDB|LLMClient|'
                      r'TTS failed|SpeechRecognition|Ollama|Connection refused|'
                      r'Permission denied)', line)
        return (m.group(0) if m else line[-80:]).strip()

    def _classify(self, line):
        if 'No module named' in line or 'ModuleNotFoundError' in line:
            m = re.search(r"No module named '([^']+)'", line)
            if m:
                return {'type': 'missing_module', 'module': m.group(1), 'line': line}
        if 'ImportError' in line:
            m = re.search(r"from '([^']+)'|module named '([^']+)'", line)
            mod = (m.group(1) or m.group(2)) if m else None
            if mod:
                return {'type': 'missing_module', 'module': mod, 'line': line}
        if 'ChromaDB' in line and ('init failed' in line or 'store error' in line
                                   or 'query error' in line):
            return {'type': 'memory_error', 'line': line}
        if 'LLMClient unavailable' in line or 'LLM not available' in line:
            return {'type': 'llm_unavailable', 'line': line}
        if 'SpeechRecognition not installed' in line:
            return {'type': 'stt_missing', 'line': line}
        if 'TTS failed' in line or 'No local TTS engine' in line:
            return {'type': 'tts_error', 'line': line}
        if 'Ollama' in line and ('Connection refused' in line or 'API error' in line):
            return {'type': 'ollama_down', 'line': line}
        if 'Permission denied' in line and 'apt' in line:
            return {'type': 'permission', 'line': line}
        return {'type': 'generic', 'line': line[:160]}

    # ---- fixing ---------------------------------------------------------

    def _pip_install(self, package):
        try:
            proc = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True, text=True, timeout=300)
            if proc.returncode == 0:
                return True, proc.stdout.strip().splitlines()[-1] if proc.stdout else 'installed'
            return False, (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        except Exception as e:
            return False, str(e)

    def _apply_fix(self, issue, auto_apply):
        t = issue['type']
        if t == 'missing_module':
            mod = issue['module']
            pkg = MODULE_TO_PIP.get(mod, mod)
            if not auto_apply:
                return {'status': 'report', 'msg': f"Missing module '{mod}'. Install: pip install {pkg}"}
            ok, detail = self._pip_install(pkg)
            if ok:
                return {'status': 'fixed', 'msg': f"Installed '{pkg}' (provides {mod})."}
            return {'status': 'failed', 'msg': f"Could not install '{pkg}': {detail}"}
        if t == 'memory_error':
            try:
                if hasattr(self.system, 'memory') and hasattr(self.system.memory, 'repair'):
                    self.system.memory.repair()
                return {'status': 'fixed', 'msg': "Repaired memory store (ChromaDB re-initialized)."}
            except Exception as e:
                return {'status': 'failed', 'msg': f"Memory repair failed: {e}"}
        if t == 'llm_unavailable':
            return {'status': 'report',
                    'msg': "LLM client unavailable — ensure Ollama is running: `ollama serve` "
                           "and that a model is pulled (`ollama pull llama3.1:8b`)."}
        if t == 'ollama_down':
            if not auto_apply:
                return {'status': 'report', 'msg': "Cannot reach Ollama — start it with `ollama serve` (or your system's Ollama service)."}
            try:
                subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                if hasattr(self.system, 'llm') and self.system.llm:
                    if self.system.llm.reconnect():
                        return {'status': 'fixed', 'msg': "Started Ollama service and reconnected LLM client."}
                return {'status': 'failed', 'msg': "Started Ollama but LLM client still unavailable."}
            except Exception as e:
                return {'status': 'failed', 'msg': f"Could not start Ollama: {e}"}
        if t == 'stt_missing':
            return {'status': 'report',
                    'msg': "Speech recognition missing - install Python requirements and "
                           "`sudo apt install portaudio19-dev flac`."}
        if t == 'tts_error':
            return {'status': 'report',
                    'msg': "Text-to-speech failed - install offline TTS: `sudo apt install espeak-ng` "
                           "or configure a Piper voice model."}
        if t == 'permission':
            return {'status': 'report',
                    'msg': "A package operation was denied permission — re-run with sudo or grant "
                           "passwordless apt for SOMS."}
        return {'status': 'report', 'msg': f"Unhandled issue: {issue['line']}"}

    def scan_and_fix(self, auto_apply=True):
        errors = self._read_recent_errors()
        results = {'scanned': len(errors), 'found': [], 'fixed': [], 'failed': [], 'reports': []}
        seen = set()
        for line in errors:
            sig = self._signature(line)
            if sig in seen:
                continue
            seen.add(sig)
            issue = self._classify(line)
            if not issue:
                continue
            if issue['type'] == 'generic':
                if sig in self._reported:
                    continue
                self._reported.add(sig)
            fix = self._apply_fix(issue, auto_apply)
            entry = f"[{issue['type']}] {fix['msg']}"
            results['found'].append(issue['type'])
            if fix['status'] == 'fixed':
                results['fixed'].append(entry)
            elif fix['status'] == 'failed':
                results['failed'].append(entry)
            else:
                results['reports'].append(entry)
        logger.info(f"Self-heal pass: scanned={results['scanned']} "
                     f"fixed={len(results['fixed'])} failed={len(results['failed'])} "
                     f"reports={len(results['reports'])}")
        return results

    def report_text(self, results):
        lines = [f"Self-Heal scan complete — {results['scanned']} error lines reviewed."]
        if results['fixed']:
            lines.append("\nFIXED:")
            lines += [f"  OK {x}" for x in results['fixed']]
        if results['failed']:
            lines.append("\nFAILED:")
            lines += [f"  X {x}" for x in results['failed']]
        if results['reports']:
            lines.append("\nNEEDS ATTENTION:")
            lines += [f"  ! {x}" for x in results['reports']]
        if not (results['fixed'] or results['failed'] or results['reports']):
            lines.append("\nNo actionable errors found. System healthy.")
        return '\n'.join(lines)

    # ---- lifecycle -------------------------------------------------------

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("SelfHealer online (auto-fix enabled)")

    def _loop(self):
        time.sleep(10)
        try:
            self.scan_and_fix(auto_apply=True)
        except Exception as e:
            logger.debug(f"Self-heal initial pass error: {e}")
        while self.is_running:
            time.sleep(_AUTO_INTERVAL)
            try:
                self.scan_and_fix(auto_apply=True)
            except Exception as e:
                logger.debug(f"Self-heal loop error: {e}")

    def stop(self):
        self.is_running = False
