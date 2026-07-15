"""Small sudo password dialog helper used by package management commands."""

from __future__ import annotations

import getpass
import os


def prompt_sudo_password(message: str = "SOMS needs your sudo password.") -> str | None:
    """Collect a sudo password from GUI-capable environments or the terminal.

    Tkinter is part of the Python standard library on many desktop installs. If
    it is unavailable or there is no display, fall back to a terminal prompt.
    """

    if os.environ.get("DISPLAY"):
        try:
            import tkinter as tk
            from tkinter import simpledialog

            root = tk.Tk()
            root.withdraw()
            try:
                return simpledialog.askstring("SOMS authentication", message, show="*")
            finally:
                root.destroy()
        except Exception:
            pass

    try:
        return getpass.getpass(f"{message}\nSudo password: ")
    except Exception:
        return None

