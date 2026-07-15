"""LLM Client Module for SOMS

Provides a real conversational backend for SOMS. Defaults to a LOCAL Ollama
instance (http://localhost:11434) so conversations and secrets never leave the
device. A remote host (e.g. ollama.com) can be configured via the `llm` config
section, optionally with an API key.

This is what turns SOMS from a command-echo into a reliable, private companion
that can remember past conversations and act as a life/moral adviser.
"""

import logging

logger = logging.getLogger('LLMClient')

DEFAULT_HOST = 'http://localhost:11434'
FALLBACK_MODEL = 'llama3.1:8b'


class LLMClient:
    """Thin wrapper around the Ollama chat API (local or remote)."""

    def __init__(self, config):
        self.config = config
        self.host = config.get('llm', 'host', default=DEFAULT_HOST)
        self.api_key = config.get('llm', 'api_key', default=None)
        self.default_model = config.get('llm', 'default_model', default=None)
        # Code/math tasks use a coding model; general chat uses a conversational
        # one. Both fall back to a locally-present model at resolution time.
        self.code_model = config.get('llm', 'code_model', default=None) or self.default_model
        self.chat_model = config.get('llm', 'chat_model', default=None)
        self._client = None
        self._available = None
        self._models_cache = None
        self._init()

    def _init(self):
        try:
            from ollama import Client
            headers = None
            if self.api_key:
                headers = {'Authorization': f'Bearer {self.api_key}'}
            # Timeout prevents an indefinite hang when a model has to be pulled.
            self._client = Client(host=self.host, headers=headers, timeout=30)
            # Verify connectivity
            self._client.list()
            self._available = True
            logger.info(f"LLMClient connected to {self.host}")
        except Exception as e:
            logger.warning(f"LLMClient unavailable at {self.host}: {e}")
            self._available = False
            self._client = None

    def available(self):
        return bool(self._available and self._client)

    def _raw_models(self):
        """Return full model entries from Ollama."""
        if not self.available():
            return []
        try:
            return self._client.list().get('models', []) or []
        except Exception:
            return []

    def list_models(self):
        if not self.available():
            return []
        if self._models_cache is not None:
            return self._models_cache
        try:
            models = [m.get('name') or m.get('model')
                      for m in self._raw_models()]
            self._models_cache = [m for m in models if m]
        except Exception:
            self._models_cache = []
        return self._models_cache

    @staticmethod
    def _is_remote_stub(entry):
        """True for models that are just pointers to a remote host (not pulled)."""
        details = entry.get('details') or {}
        if entry.get('remote_host') or details.get('remote_host'):
            return True
        size = entry.get('size') or 0
        # A real model is many MB; a stub is a few hundred bytes.
        return size > 0 and size < 1024 * 1024

    def _local_models(self):
        return [m.get('name') or m.get('model')
                for m in self._raw_models()
                if m.get('name') or m.get('model')
                and not self._is_remote_stub(m)]

    def _resolve_model(self, model=None):
        model = model or self.default_model
        available = self.list_models()
        local = self._local_models()
        # Prefer a locally-present model so we never hang pulling a remote stub.
        if local:
            if model in local:
                return model
            return local[0]
        if model and model in available:
            return model
        if available:
            return available[0]
        return self.default_model or FALLBACK_MODEL

    _CODE_HINTS = (
        'code', 'python', 'javascript', 'function', 'class ', 'def ', 'bug',
        'error', 'regex', 'script', 'compile', 'algorithm', '```', 'import ',
        'syntax', 'variable', 'loop', 'sql', 'html', 'css', 'api', 'debug',
        'stack trace', 'exception', 'json', 'shell', 'bash', 'terminal',
    )

    @staticmethod
    def _looks_code(text):
        low = (text or '').lower()
        if '```' in text:
            return True
        # Strong signal: an assignment or call pattern on its own line.
        for line in low.splitlines():
            line = line.strip()
            if line.startswith(('def ', 'class ', 'import ', 'function ', '#!')):
                return True
        return any(h in low for h in LLMClient._CODE_HINTS)

    def _conversational_model(self):
        """Pick the best locally-present model for natural conversation."""
        if self.chat_model:
            return self._resolve_model(self.chat_model)
        local = self._local_models()
        # Exclude coder/specialist models and very small (<~3B) models so we
        # don't answer conversation with a 1B model.
        tiny = ('1b', '1.1b', '2b', '2.7b', '0.5b')
        cands = [m for m in local
                 if 'coder' not in m.lower()
                 and not any(t in m.lower() for t in tiny)]
        if not cands:
            cands = [m for m in local if 'coder' not in m.lower()]
        if not cands:
            cands = local
        if not cands:
            return self.default_model or FALLBACK_MODEL
        # Prefer well-known conversational families, best-first.
        for fam in ('llama2-uncensored', 'llama3', 'llama2', 'gemma',
                    'mistral', 'qwen', 'phi', 'vicuna', 'command-r'):
            for m in cands:
                if fam in m.lower():
                    return m
        return cands[0]

    def select_model(self, text):
        """Choose the right model for a query: coding model for code/math,
        conversational model otherwise."""
        if self._looks_code(text):
            return self._resolve_model(self.code_model)
        return self._conversational_model()

    def chat(self, messages, model=None, images=None):
        """Send a full message list and return the assistant's text reply.

        `images` is an optional list of base64-encoded image strings; when given,
        they are attached to the last user message for multimodal (vision) chat.
        """
        if not self.available():
            raise RuntimeError("LLM not available")
        model = self._resolve_model(model)
        # Attach images to the final user turn for vision requests.
        if images:
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get('role') == 'user':
                    messages[i]['images'] = images
                    break
            else:
                messages.append({'role': 'user', 'content': '', 'images': images})
        try:
            resp = self._client.chat(model=model, messages=messages)
            return (resp.get('message', {}).get('content') or '').strip()
        except Exception as e:
            # A different (preferably local) model is worth one retry; retrying
            # the exact same broken model just wastes another long timeout.
            logger.debug(f"chat failed with model {model}: {e}")
            alt = self._resolve_model(None)
            if alt and alt != model:
                try:
                    resp = self._client.chat(model=alt, messages=messages)
                    return (resp.get('message', {}).get('content') or '').strip()
                except Exception as e2:
                    raise RuntimeError(f"LLM chat failed: {e2}")
            raise RuntimeError(f"LLM chat failed: {e}")

    def vision_model(self):
        """Return a vision-capable model name, or None if none available."""
        configured = self.config.get('llm', 'vision_model', default=None)
        if configured and (not self.list_models() or configured in self.list_models()):
            return configured
        for m in self.list_models():
            low = m.lower()
            if any(k in low for k in ['vision', 'llava', 'moondream', 'bakllava', 'nanollava']):
                return m
        return None

    def reconnect(self):
        """Re-initialize connection to Ollama. Returns True if successful."""
        self._init()
        return self.available()
