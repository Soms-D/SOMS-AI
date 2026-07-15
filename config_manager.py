"""
Config Manager Module for SOMS
Manages configuration settings and user preferences
"""

import json
import os
import logging
from pathlib import Path

logger = logging.getLogger('ConfigManager')
class ConfigManager:
    """Centralized configuration management for SOMS system."""

    def __init__(self):
        self.config_file = Path('soms_config.json')
        self.user_config_file = Path('soms_user_config.json')

        self.settings = self._load_settings()
        self.user_settings = self._load_user_settings()

    def _deep_merge(self, base, override):
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _load_settings(self):
        """Load system settings from file or create defaults."""
        default_settings = {
            'system': {
                'name': 'SOMS',
                'version': '1.0.0',
                'auto_start': True,
                'log_level': 'INFO',
                'max_memory_usage': 80,
                'enable_gui': False,
                'voice_enabled': True,
                'camera_enabled': False,
                'weather_enabled': True,
                'research_mode': False,
                'auto_grow': False
            },
            'voice': {
                'stt_engine': 'faster-whisper',
                'tts_engine': 'piper',
                'language': 'en',
                'sample_rate': 16000,
                'channels': 1,
                'local_files_only': True,
                'whisper_model': 'base.en',
                'whisper_cpp_model': '',
                'piper_model': '',
                'voice_id': 'en-us-1',
                'speed': 1.0,
                'volume': 1.0
            },
            'email': {
                'user': '',
                'server': '',
                'password': ''
            }
        }

        loaded_ok = False
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    self._deep_merge(default_settings, loaded)
                    loaded_ok = True
            except Exception as e:
                logger.warning(f"Could not load settings: {e}")

        self.settings = default_settings
        if loaded_ok:
            self._save_settings()
        return default_settings

    def _save_settings(self):
        """Save settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, *keys, default=None):
        """Get a value from nested dictionary structure."""
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value=None):
        """Set a value in nested dictionary structure."""
        current = self.settings
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        self._save_settings()

    def get_random_honorific(self):
        """Return a random honorific (different from the last one used)."""
        import random
        honorifics = self.get_user('user', 'honorifics', default=['Sir'])
        if not isinstance(honorifics, list) or not honorifics:
            honorifics = ['Sir']
        current = self.get_user('user', 'current', default=None)
        if len(honorifics) > 1:
            candidates = [h for h in honorifics if h != current]
            chosen = random.choice(candidates)
        else:
            chosen = honorifics[0]
        self.set_user('user', 'current', value=chosen)
        return chosen

    def get_user(self, *keys, default=None):
        """Get user-specific value from nested dictionary structure."""
        value = self.user_settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set_user(self, *keys, value=None):
        """Set user-specific value in nested dictionary structure."""
        current = self.user_settings
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        self._save_user_settings()

    def _load_user_settings(self):
        """Load user-specific settings from file or create defaults."""
        default_user_settings = {
            'user': {
                'honorifics': ['Sir', 'BKEEPER', 'DADDY', 'BATISTA', 'BOSS', 'COMMANDER', 'CHIEF', 'CAPTAIN', 'MY LORD', 'SIR KNIGHT', 'ADMIRAL', 'GOVERNOR'],
                'current': 'Sir',
                'preferences': {
                    'voice_pitch': 'normal',
                    'response_style': 'professional',
                    'learning_enabled': True
                }
            }
        }

        loaded_ok = False
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r') as f:
                    loaded = json.load(f)
                    self._deep_merge(default_user_settings, loaded)
                    loaded_ok = True
            except Exception as e:
                logger.warning(f"Could not load user settings: {e}")

        self.user_settings = default_user_settings
        if loaded_ok:
            self._save_user_settings()
        return default_user_settings

    def _save_user_settings(self):
        """Save user settings to file."""
        try:
            with open(self.user_config_file, 'w') as f:
                json.dump(self.user_settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user settings: {e}")
