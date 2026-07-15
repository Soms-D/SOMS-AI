"""Flet desktop GUI for SOMS."""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger("GUI")

try:
    import flet as ft

    HAS_FLET = True
except Exception:
    ft = None
    HAS_FLET = False


class GUI:
    """Desktop GUI wrapper used by ``main.py``.

    The UI keeps the first screen functional: chat transcript, command input,
    quick commands, and live status.  Command execution runs in a worker thread
    so the window stays responsive while SOMS talks to the LLM or system tools.
    """

    def __init__(self, config, system_ref):
        self.config = config
        self.system = system_ref
        self.is_running = False
        self.page = None
        self.chat = None
        self.command_input = None
        self.status_text = None
        self.mic_button = None
        self.mic_status_text = None
        self.voice_status_text = None
        self._last_mic_state = None
        self._last_voice_state = None
        self._mic_sync_started = False

    def start(self):
        self.is_running = True
        if not HAS_FLET:
            raise RuntimeError("Flet is not installed. Run: ./venv/bin/pip install -r requirements.txt")
        logger.info("GUI starting")
        ft.app(target=self._build)

    def stop(self):
        self.is_running = False
        logger.info("GUI stopped")
        if self.page:
            try:
                self.page.window.close()
            except Exception:
                pass

    def _build(self, page):
        self.page = page
        page.title = "SOMS AI"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.window.min_width = 920
        page.window.min_height = 620

        self.status_text = ft.Text("Online", color=ft.Colors.GREEN_400, size=13)
        self.mic_status_text = ft.Text("Checking mic...", color=ft.Colors.BLUE_GREY_200, size=13)
        self.voice_status_text = ft.Text("Voice idle", color=ft.Colors.BLUE_GREY_200, size=12)
        self.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True, padding=16)
        self.command_input = ft.TextField(
            hint_text="Type a command or message...",
            expand=True,
            autofocus=True,
            border_radius=6,
            on_submit=lambda _: self._submit(),
        )

        send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            tooltip="Send",
            on_click=lambda _: self._submit(),
        )
        self.mic_button = ft.IconButton(
            icon=ft.Icons.MIC_ROUNDED,
            tooltip="Toggle microphone",
            on_click=lambda _: self._toggle_mic(),
        )

        quick_commands = ft.Row(
            [
                self._quick_button("/info", ft.Icons.MONITOR_HEART_ROUNDED),
                self._quick_button("/memory", ft.Icons.PSYCHOLOGY_ROUNDED),
                self._quick_button("/model", ft.Icons.HUB_ROUNDED),
                self._quick_button("/self-heal", ft.Icons.HEALING_ROUNDED),
                self._quick_button("/help", ft.Icons.HELP_OUTLINE_ROUNDED),
            ],
            wrap=True,
            spacing=8,
        )

        sidebar = ft.Container(
            width=250,
            padding=16,
            bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Column(
                [
                    ft.Text("SOMS AI", size=26, weight=ft.FontWeight.BOLD),
                    ft.Text("Self-Organizing Master System", size=12, color=ft.Colors.BLUE_GREY_200),
                    ft.Divider(),
                    ft.Row([ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN_400, size=12), self.status_text]),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.MIC_ROUNDED, color=ft.Colors.BLUE_GREY_200, size=14),
                            self.mic_status_text,
                        ],
                        spacing=8,
                    ),
                    self.voice_status_text,
                    ft.Text("7BRAIN-CORE", size=12, color=ft.Colors.BLUE_GREY_200),
                    ft.Divider(),
                    quick_commands,
                ],
                spacing=12,
            ),
        )

        input_bar = ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Row([self.command_input, self.mic_button, send_button], spacing=8),
        )

        page.add(
            ft.Row(
                [
                    sidebar,
                    ft.Column([self.chat, input_bar], expand=True, spacing=0),
                ],
                expand=True,
                spacing=0,
            )
        )
        self._sync_mic_state(force=True)
        self._start_mic_sync()
        self._write("SOMS", getattr(self.system, "welcome_text", "") or "System online. Type /help for commands.")

    def _quick_button(self, command, icon):
        return ft.IconButton(
            icon=icon,
            tooltip=command,
            on_click=lambda _, value=command: self._execute(value),
        )

    def _submit(self):
        text = (self.command_input.value or "").strip()
        if not text:
            return
        self.command_input.value = ""
        self.page.update()
        self._execute(text)

    def _execute(self, text):
        self._write("You", text)
        self._set_status("Thinking", ft.Colors.AMBER_300)

        def worker():
            try:
                response = self.system.execute_command(text)
                orchestrator = response.get("orchestrator") or {}
                if orchestrator.get("restart"):
                    reply = "Restarting SOMS."
                elif orchestrator.get("shutdown"):
                    reply = "Shutting down SOMS."
                else:
                    reply = orchestrator.get("text") or response.get("agent", {}).get("text") or "Done."
                self._write("SOMS", reply)
                if orchestrator.get("restart"):
                    self.system.restart()
                elif orchestrator.get("shutdown"):
                    self.system.shutdown()
            except Exception as exc:
                logger.exception("GUI command failed")
                self._write("Error", str(exc))
            finally:
                self._set_status("Online", ft.Colors.GREEN_400)

        threading.Thread(target=worker, daemon=True).start()

    def _toggle_mic(self):
        try:
            voice = getattr(self.system, "voice", None)
            if not voice:
                self._write("SOMS", "Voice module is not available.")
                return
            if getattr(voice, "is_listening", False):
                voice.stop_listening()
                self._sync_mic_state(force=True)
                self._write("SOMS", "Microphone disabled.")
            else:
                voice.set_command_callback(self.system._on_voice_command)
                voice.start_listening()
                self._sync_mic_state(force=True)
                self._write("SOMS", "Microphone enabled.")
        except Exception as exc:
            self._write("Error", str(exc))

    def _write(self, speaker, message):
        if not self.chat or not self.page:
            return
        color = ft.Colors.BLUE_200 if speaker == "You" else ft.Colors.GREEN_200
        if speaker == "Error":
            color = ft.Colors.RED_200
        timestamp = datetime.now().strftime("%H:%M")
        self.chat.controls.append(
            ft.Container(
                border_radius=6,
                padding=12,
                bgcolor=ft.Colors.BLUE_GREY_800,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(speaker, weight=ft.FontWeight.BOLD, color=color),
                                ft.Text(timestamp, size=11, color=ft.Colors.BLUE_GREY_300),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(str(message), selectable=True),
                    ],
                    spacing=6,
                ),
            )
        )
        self.page.update()

    def _set_status(self, text, color):
        if self.status_text and self.page:
            self.status_text.value = text
            self.status_text.color = color
            self.page.update()

    def _start_mic_sync(self):
        if self._mic_sync_started:
            return
        self._mic_sync_started = True

        def worker():
            while self.is_running and self.page:
                self._sync_mic_state()
                time.sleep(1)

        threading.Thread(target=worker, daemon=True).start()

    def _sync_mic_state(self, force=False):
        if not self.page or not self.mic_button or not self.mic_status_text or not self.voice_status_text:
            return
        voice = getattr(self.system, "voice", None)
        listening = bool(getattr(voice, "is_listening", False)) if voice else False
        status_text, status_color = self._voice_status(voice, listening)
        state = (listening, status_text, status_color)
        if not force and listening == self._last_mic_state and state == self._last_voice_state:
            return

        self._last_mic_state = listening
        self._last_voice_state = state
        if listening:
            self.mic_button.icon = ft.Icons.MIC_ROUNDED
            self.mic_button.icon_color = ft.Colors.GREEN_400
            self.mic_button.tooltip = "Microphone listening"
            self.mic_status_text.value = "Mic listening"
            self.mic_status_text.color = ft.Colors.GREEN_400
        else:
            self.mic_button.icon = ft.Icons.MIC_OFF_ROUNDED
            self.mic_button.icon_color = ft.Colors.RED_300
            self.mic_button.tooltip = "Microphone off"
            self.mic_status_text.value = "Mic off"
            self.mic_status_text.color = ft.Colors.RED_300
        self.voice_status_text.value = status_text
        self.voice_status_text.color = status_color
        self.page.update()

    def _voice_status(self, voice, listening):
        if not voice:
            return "Voice module unavailable", ft.Colors.RED_300
        error = getattr(voice, "last_stt_error", "") or ""
        transcript = getattr(voice, "last_transcript", "") or ""
        last_audio = getattr(voice, "last_audio_time", None)

        if error:
            if "cached snapshot" in error or "No working local STT" in error:
                return "Hearing audio, STT model missing", ft.Colors.AMBER_300
            return f"Voice error: {error[:46]}", ft.Colors.AMBER_300
        if transcript:
            return f"Heard: {transcript[:52]}", ft.Colors.GREEN_200
        if last_audio and time.time() - last_audio < 8:
            return "Audio detected, no words yet", ft.Colors.AMBER_300
        if listening:
            return "Say: soms ...", ft.Colors.BLUE_GREY_200
        return "Voice idle", ft.Colors.BLUE_GREY_200
