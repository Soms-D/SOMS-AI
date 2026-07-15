"""SOMS CLI Module - Gemini-style terminal interface
Provides interactive command-line interface with rich output and history
"""

import sys
import os
import time
import threading
import signal
import json
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.live import Live
    from rich.style import Style
    from rich.columns import Columns
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory, InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# readline fallback for history navigation + auto-completion
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

# History file path
HISTORY_FILE = Path(__file__).parent.parent / '.soms_history'

from .constants import CANONICAL_COMMANDS as COMMANDS

# Command completer
if HAS_PROMPT_TOOLKIT:
    COMMAND_COMPLETER = WordCompleter(COMMANDS, ignore_case=True)
else:
    COMMAND_COMPLETER = None


def _readline_completer(text, state):
    """readline completer: complete command names from COMMANDS."""
    matches = [c for c in COMMANDS if c.startswith(text)]
    return matches[state] if state < len(matches) else None


def setup_readline_history():
    """Enable ↑/↓ history navigation and Tab auto-completion via readline."""
    if not HAS_READLINE:
        return
    try:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(_readline_completer)
        readline.set_completer_delims(" ")
        if HISTORY_FILE.exists():
            readline.read_history_file(str(HISTORY_FILE))
        import atexit
        atexit.register(readline.write_history_file, str(HISTORY_FILE))
    except Exception:
        pass

from .chat_history import ChatHistory

class SOMSCLI:
    """Gemini-style CLI interface for SOMS with history navigation."""

    BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗ ██████╗ ██████╗ ████████╗██╗ ██████╗ ███╗   ███╗  ║
║   ██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗ ████║  ║
║   ███████╗██║   ██║██████╔╝   ██║   ██║██║   ██║██╔████╔██║  ║
║   ╚════██║██║   ██║██╔══██╗   ██║   ██║██║   ██║██║╚██╔╝██║  ║
║   ███████║╚██████╔╝██║  ██║   ██║   ██║╚██████╔╝██║ ╚═╝ ██║  ║
║   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝     ╚═╝  ║
║                                                               ║
║   Self-Organizing Master System v1.0                         ║
║   7BRAIN-CORE Architecture | 100% Offline & Private          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

    def __init__(self, system):
        self.system = system
        self.console = Console() if HAS_RICH else None
        self.running = True
        self.history = []
        self.history_index = -1
        self.chat_history = ChatHistory()
        self._session = None

        # Initialize prompt_toolkit session if available
        if HAS_PROMPT_TOOLKIT:
            history = FileHistory(str(HISTORY_FILE))
            self._session = PromptSession(
                history=history,
                auto_suggest=AutoSuggestFromHistory(),
                completer=COMMAND_COMPLETER,
                complete_while_typing=True,
            )

    def print(self, *args, **kwargs):
        """Print with rich formatting or fallback to basic print."""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args)

    def print_banner(self):
        """Display the SOMS banner."""
        if self.console:
            self.console.print(Panel(
                self.BANNER,
                style="bold blue",
                border_style="bright_blue"
            ))
            self.console.print()
        else:
            print(self.BANNER)

    def print_help(self):
        """Display help information."""
        if self.console:
            table = Table(title="SOMS Commands", show_header=True, header_style="bold cyan")
            table.add_column("Command", style="green")
            table.add_column("Description")
            table.add_row("/info", "System status and diagnostics")
            table.add_row("/system check", "Full health check")
            table.add_row("/update", "System improvement")
            table.add_row("/model", "List and select AI models")
            table.add_row("/soms", "SOMS system information")
            table.add_row("/improve", "Self-improvement & capabilities")
            table.add_row("/memory", "Memory layer status")
            table.add_row("/packages", "Package manager status")
            table.add_row("/install <pkg>", "Install a package (GUI sudo prompt)")
            table.add_row("/remove <pkg>", "Remove a package")
            table.add_row("/upgrade", "Upgrade installed packages")
            table.add_row("/update-system", "Update lists then upgrade")
            table.add_row("/full-upgrade", "Full dist-upgrade + cleanup")
            table.add_row("/fix-deps", "Repair broken dependencies")
            table.add_row("/search <query>", "Search package repository")
            table.add_row("/plan <goal>", "Architect: turn a goal into an action plan")
            table.add_row("/task <name>", "Engineer: run health/overview task")
            table.add_row("/grow <axis>", "Upgrade performance/intelligence/efficiency/stability (or 'all')")
            table.add_row("/learn", "Enable learning mode")
            table.add_row("/evolve", "Run evolution analysis")
            table.add_row("/history", "View chat history (↑/↓ to scroll)")
            table.add_row("/clear", "Clear chat history")
            table.add_row("/help", "Show this help message")
            table.add_row("/exit", "Exit SOMS CLI")
            table.add_row("", "")
            table.add_row("[dim]↑/↓[/dim]", "Navigate command history")
            table.add_row("[dim]Tab[/dim]", "Auto-complete commands")
            table.add_row("[dim]Ctrl+C[/dim]", "Cancel current input")
            self.console.print(table)
        else:
            print("\nSOMS Commands:")
            print("  /info - System status")
            print("  /system check - Health check")
            print("  /update - System update")
            print("  /model - AI models")
            print("  /soms - SOMS info")
            print("  /improve - Capabilities")
            print("  /memory - Memory status")
            print("  /history - View chat history")
            print("  /clear - Clear history")
            print("  /help - Show help")
            print("  /exit - Exit")
            print("\nNavigation:")
            print("  ↑/↓ - Navigate command history")
            print("  Tab - Auto-complete commands")
        print()

    def display_history(self, limit=20):
        """Display chat history with scrolling."""
        entries = self.chat_history.get_entries(limit)
        
        if not entries:
            self.print("[yellow]No chat history yet.[/yellow]")
            return

        if self.console:
            table = Table(title=f"Chat History (last {len(entries)} messages)", 
                         show_header=True, header_style="bold cyan")
            table.add_column("Time", style="dim", width=12)
            table.add_column("You", style="blue", max_width=40)
            table.add_column("SOMS", style="green", max_width=60)
            
            for entry in entries:
                try:
                    ts = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                except Exception:
                    ts = "??:??:??"
                user_msg = entry.get('user', '')[:40]
                response = entry.get('response', '')[:60]
                table.add_row(ts, user_msg, response)
            
            self.console.print(table)
        else:
            print("\nChat History:")
            print("-" * 60)
            for entry in entries:
                try:
                    ts = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                except Exception:
                    ts = "??:??:??"
                print(f"[{ts}] You: {entry.get('user', '')}")
                print(f"         SOMS: {entry.get('response', '')[:80]}")
                print()
        print()

    def process_input(self, user_input):
        """Process user input and return response."""
        if not user_input.strip():
            return None

        self.history.append(user_input)
        self.history_index = len(self.history)

        cmd = user_input.strip().lower()

        if cmd in ('exit', 'quit', '/exit', '/quit', 'q'):
            self.running = False
            return {"text": "Goodbye!", "shutdown": True}

        if cmd in ('help', '/help', '?'):
            self.print_help()
            return None

        if cmd in ('history', '/history'):
            self.display_history()
            return None

        if cmd in ('clear', '/clear'):
            self.chat_history.clear()
            self.print("[green]Chat history cleared.[/green]")
            return None

        def step(msg):
            if self.console:
                self.console.print(f"[dim]▸ {msg}[/dim]")
            else:
                print(f"  {msg}")
        response = self.system.execute_command(user_input, progress_callback=step)
        return response

    def display_response(self, response):
        """Display response with formatting."""
        if not response:
            return

        response_text = ""

        if isinstance(response, dict):
            if response.get('shutdown'):
                if self.console:
                    self.console.print(Panel(
                        "[bold red]Shutting down SOMS...[/bold red]",
                        border_style="red"
                    ))
                else:
                    print("Shutting down SOMS...")
                return

            if response.get('restart'):
                if self.console:
                    self.console.print(Panel(
                        "[bold yellow]Restarting SOMS...[/bold yellow]",
                        border_style="yellow"
                    ))
                else:
                    print("Restarting SOMS...")
                return

            text = response.get('orchestrator', {}).get('text', '')
            if not text:
                text = response.get('agent', {}).get('text', '')
            
            response_text = text

            if text:
                if self.console:
                    self.console.print(Panel(
                        text,
                        title="[bold green]SOMS[/bold green]",
                        border_style="green",
                        padding=(1, 2)
                    ))
                else:
                    print(f"SOMS: {text}")
        else:
            response_text = str(response)
            if self.console:
                self.console.print(f"[green]SOMS:[/green] {response}")
            else:
                print(f"SOMS: {response}")

        # Save to chat history
        if self.history and response_text:
            last_user_input = self.history[-1] if self.history else ""
            self.chat_history.add_entry(last_user_input, response_text)

    def _get_input(self):
        """Get user input with history navigation."""
        if self._session:
            try:
                return self._session.prompt("You: ")
            except KeyboardInterrupt:
                return ""
            except EOFError:
                return "/exit"
        else:
            try:
                return input("You: ")
            except KeyboardInterrupt:
                return ""
            except EOFError:
                return "/exit"

    def run(self):
        """Run the interactive CLI."""

        # Piped input (e.g. `echo "weather" | main.py --cli`): process each line
        # non-interactively, then exit.
        if not sys.stdin.isatty():
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                resp = self.process_input(line)
                if resp:
                    self.display_response(resp)
                if isinstance(resp, dict) and resp.get('shutdown'):
                    break
            return

        self.print_banner()

        # Enable ↑/↓ history navigation + Tab auto-completion in the fallback path
        setup_readline_history()

        if self.console:
            self.console.print("[bold green]SOMS CLI Ready[/bold green]")
            self.console.print("[dim]Type /help for commands | ↑/↓ for history | Tab for auto-complete[/dim]")
        else:
            print("SOMS CLI Ready — Type /help for commands")
            print("Use ↑/↓ arrows to navigate command history | Tab to auto-complete")
        print()

        while self.running:
            try:
                user_input = self._get_input()

                if not user_input.strip():
                    continue

                response = self.process_input(user_input)
                if response:
                    self.display_response(response)

                if isinstance(response, dict) and response.get('shutdown'):
                    break

            except KeyboardInterrupt:
                self.print("\n")
                if self.console:
                    self.console.print("[yellow]Use /exit to quit[/yellow]")
                else:
                    print("Use /exit to quit")
            except EOFError:
                break
            except Exception as e:
                if self.console:
                    self.console.print(f"[red]Error: {e}[/red]")
                else:
                    print(f"Error: {e}")

        if self.console:
            self.console.print("[dim]SOMS CLI session ended.[/dim]")
        else:
            print("SOMS CLI session ended.")

def run_cli(system, query=None):
    """Run the SOMS CLI.

    If `query` is provided, run it as a single one-shot command (great for
    scripting/automation) and exit. Otherwise start the interactive session.
    """
    cli = SOMSCLI(system)
    if query:
        resp = cli.process_input(query)
        if resp:
            cli.display_response(resp)
        return
    cli.run()
