"""Model Manager Module for SOMS
Manages available AI models and selection
"""

import logging
import subprocess
import json

logger = logging.getLogger('ModelManager')

CURATED_MODELS = [
    "llama3.1:8b",
    "llama3.1:70b",
    "llama3.1:405b",
    "mistral:7b",
    "mixtral:8x7b",
    "phi3:mini",
    "phi3:medium",
    "gemma2:2b",
    "gemma2:9b",
    "gemma2:27b",
    "qwen2:0.5b",
    "qwen2:1.5b",
    "qwen2:7b",
    "qwen2:72b",
    "codestral:22b",
    "deepseek-coder:6.7b",
    "neural-chat:7b",
    "starling-lm:7b",
    "solar:10.7b",
    "command-r:35b",
    "dolphin-mixtral:8x7b",
    "nous-hermes2:10.7b",
    "orca-mini:3b",
    "tinyllama:1.1b",
]

class ModelManager:
    def __init__(self, config):
        self.config = config
        self._available = None
        self._current = None
        self._load_state()

    def _load_state(self):
        self._current = self.config.get('model', 'selected', default=CURATED_MODELS[0])

    def _save_state(self):
        self.config.set('model', 'selected', value=self._current)

    def _detect_ollama_models(self):
        """Return list of installed ollama models, [] if ollama runs with none, or None if ollama is unavailable."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                models = []
                for line in result.stdout.strip().split('\n')[1:]:
                    if line.strip():
                        name = line.split()[0]
                        models.append(name)
                return models
        except Exception as e:
            logger.debug(f"Ollama detection: {e}")
        return None

    def get_available_models(self):
        if self._available is None:
            ollama = self._detect_ollama_models()
            if ollama is not None:
                self._available = ollama if ollama else CURATED_MODELS[:]
            else:
                self._available = CURATED_MODELS[:]
        return self._available

    def get_current_model(self):
        return self._current

    def set_model(self, identifier):
        models = self.get_available_models()
        try:
            idx = int(identifier) - 1
            if 0 <= idx < len(models):
                self._current = models[idx]
                self._save_state()
                return True, f"Model set to {self._current}"
        except ValueError:
            pass
        if identifier in models:
            self._current = identifier
            self._save_state()
            return True, f"Model set to {self._current}"
        return False, f"Model '{identifier}' not found. Use /model to see available models."

    def format_model_list(self):
        models = self.get_available_models()
        lines = [f"Available Models ({len(models)}):"]
        for i, m in enumerate(models, 1):
            marker = ">" if m == self._current else " "
            lines.append(f"  {marker} [{i}] {m}")
        lines.append(f"\nCurrent: {self._current}")
        lines.append("Select: /model <number> or /model <name>")
        return '\n'.join(lines)

    def refresh(self):
        self._available = None
        self.get_available_models()
