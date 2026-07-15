"""Shared chat history with JSON persistence and common pattern data."""

import json
from datetime import datetime
from pathlib import Path

CHAT_HISTORY_FILE = Path(__file__).parent.parent / '.soms_chat_history.json'

class ChatHistory:
    def __init__(self):
        self.entries = []
        self.max_entries = 1000
        self._load_history()

    def _load_history(self):
        try:
            if CHAT_HISTORY_FILE.exists():
                with open(CHAT_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.entries = data.get('entries', [])
        except Exception:
            self.entries = []

    def _save_history(self):
        try:
            with open(CHAT_HISTORY_FILE, 'w') as f:
                json.dump({'entries': self.entries[-self.max_entries:]}, f, indent=2)
        except Exception:
            pass

    def add_entry(self, user_input, response_text, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        entry = {'timestamp': timestamp, 'user': user_input, 'response': response_text}
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        self._save_history()

    def get_entries(self, limit=None):
        if limit:
            return self.entries[-limit:]
        return self.entries

    def clear(self):
        self.entries = []
        self._save_history()

    def search(self, query):
        results = []
        query_lower = query.lower()
        for entry in self.entries:
            if query_lower in entry.get('user', '').lower() or query_lower in entry.get('response', '').lower():
                results.append(entry)
        return results
