"""Orchestrator Module for SOMS
Central command and control system that coordinates all brain modules
"""

import json
import time
import logging
from datetime import datetime
from .persona import Persona
from .constants import HOW_TO_PATTERNS, WAKE_PREFIXES

logger = logging.getLogger('Orchestrator')
class Orchestrator:
    """Central interface and master controller for all SOMS modules."""

    def __init__(self, config, system_ref=None):
        self.config = config
        self.system = system_ref
        self._running = False
        self.persona = Persona(system_ref)
        self._progress_callback = None

    def start(self):
        """Start the orchestrator service."""
        self._running = True
        logger.info("Orchestrator started and ready to accept commands")

    def stop(self):
        """Stop the orchestrator service."""
        self._running = False
        logger.info("Orchestrator stopped")

    def _get_honorific(self):
        """Get a random honorific for addressing the user."""
        if self.system and hasattr(self.system, 'config'):
            return self.system.config.get_random_honorific()
        return self.config.get_user('current', default='Sir')

    def _strip_soms_prefix(self, text):
        if not text:
            return text
        t = text.lower().strip()
        for prefix in WAKE_PREFIXES:
            if t.startswith(prefix):
                remainder = t[len(prefix):].strip()
                return remainder if remainder else text
        return text

    def process_voice_command(self, audio_data, progress_callback=None):
        """Think about voice command, route it, and respond."""
        if not self._running:
            return {'text': self.persona.system_not_running(), 'confidence': 0.0, 'command_type': 'system', 'timestamp': time.time()}

        if progress_callback:
            progress_callback("Listening...")

        raw_text = self._extract_text_from_audio(audio_data)
        command_text = self._strip_soms_prefix(raw_text)
        user = self._get_honorific()

        command_type = self._detect_command_type(command_text)

        self._progress_callback = progress_callback
        response = self._generate_response(command_text, command_type)
        self._progress_callback = None

        return response

    def _extract_text_from_audio(self, audio_data):
        """Extract text from audio using faster-whisper."""
        if isinstance(audio_data, str):
            return audio_data.lower().strip()
        return ""

    def _detect_command_type(self, text):
        """Detect the type of command in text."""
        if not text:
            return 'unknown'

        text_lower = text.lower()

        if text_lower in ('/.', '/q', '/quit', '/exit', 'exit', 'quit'):
            return 'exit'
        if (text_lower.startswith(('/', '!', 'cmd:')) or
            any(pattern in text_lower for pattern in ['system check', 'info', 'help', 'shutdown', 'update', 'learn', 'soms', 'model', 'restart', 'improve', 'capabilities', 'evolve', 'memory', 'packages', 'pkgs', 'wifite', 'clean', 'plan', 'task', 'grow', 'upgrade-self', 'timesfm'])):
            return 'main_command'
        if any(p in text_lower for p in HOW_TO_PATTERNS):
            return 'hacking_demo'
        elif any(word in text_lower for word in ['weather', 'temperature', 'forecast']):
            return 'weather'
        elif any(word in text_lower for word in ['calculate', 'compute', 'solve']):
            return 'math'
        elif any(word in text_lower for word in ['search', 'find', 'lookup']):
            return 'search'
        elif any(word in text_lower for word in ['open', 'launch', 'start']):
            return 'application'
        elif any(word in text_lower for word in ['fix packages', 'fix deps', 'repair packages', 'repair deps']):
            return 'system_maintenance'
        elif any(word in text_lower for word in ['install', 'uninstall', 'remove', 'package', 'apt-get', 'pacman', 'dnf']):
            return 'system_install'
        elif any(word in text_lower for word in ['upgrade', 'update system']):
            return 'system_maintenance'
        elif any(word in text_lower for word in ['camera', 'snap', 'photo', 'capture', 'see']):
            return 'camera'
        elif any(word in text_lower for word in ['motion', 'detect', 'movement']):
            return 'camera'
        else:
            return 'natural'

    def _live_stats(self):
        """Get live system stats string."""
        if not self.system or not hasattr(self.system, 'resources'):
            return "System monitoring unavailable."
        s = self.system.resources.get_status()
        uptime = self.system.resources.get_uptime()
        return f"CPU: {s.get('cpu_usage', '?')} | RAM: {s.get('memory_usage', '?')} | Disk: {s.get('disk_usage', '?')} | Uptime: {uptime:.1f}h"

    def get_wifite_help(self):
        """Public accessor for the wifite help text."""
        return self._WIFITE_HELP

    def _get_wifite_help(self, command_text):
        """Run wifite with given args or show help."""
        import subprocess
        parts = command_text.strip().split()
        args = parts[1:] if len(parts) > 1 else []
        if args and args[0] == 'sudo':
            args = args[1:]
        if not args or args[0] in ('-h', '--help'):
            return self._WIFITE_HELP
        cmd = ['sudo', '-n', 'wifite'] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return r.stdout or r.stderr or "No output."
        except FileNotFoundError:
            return "wifite is not installed. Install it with: sudo apt install wifite"
        except subprocess.TimeoutExpired:
            return "wifite timed out (120s limit)."
        except Exception as e:
            return f"Error: {e}"

    _WIFITE_HELP = """\
wifite -h
   .               .    
 .´  ·  .     .  ·  `.  wifite2 2.8.1
 :  :  :  (¯)  :  :  :  a wireless auditor by derv82
 `.  ·  ` /¯\\ ´  ·  .´  maintained by kimocoder
   `     /¯¯¯\\     ´    https://github.com/kimocoder/wifite2

options:
  -h, --help                    show this help message and exit

SETTINGS:
  -v, --verbose                 Shows more options (-h -v). Prints commands and outputs. (default: quiet)
  -i [interface]                Wireless interface to use, e.g. wlan0mon (default: ask)
  -c [channel]                  Wireless channel to scan e.g. 1,3-6 (default: all 2Ghz channels)
  -inf, --infinite              Enable infinite attack mode. Modify scanning time with -p (default: off)
  -mac, --random-mac            Randomize wireless card MAC address (default: off)
  -p [scan_time]                Pillage: Attack all targets after scan_time (seconds)
  --kill                        Kill processes that conflict with Airmon/Airodump (default: off)
  -pow, --power [min_power]     Attacks any targets with at least min_power signal strength
  --skip-crack                  Skip cracking captured handshakes/pmkid (default: off)
  -first, --first [attack_max]  Attacks the first attack_max targets
  -ic, --ignore-cracked         Hides previously-cracked targets. (default: off)
  --clients-only                Only show targets that have associated clients (default: off)
  --nodeauths                   Passive mode: Never deauthenticates clients (default: deauth targets)
  --daemon                      Puts device back in managed mode after quitting (default: off)

WEP:
  --wep                         Show only WEP-encrypted networks
  --require-fakeauth            Fails attacks if fake-auth fails (default: off)
  --keep-ivs                    Retain .IVS files and reuse when cracking (default: off)

WPA:
  --wpa                         Show only WPA/WPA2-encrypted networks (may include WPS)
  --wpa3                        Show only WPA3-encrypted networks (SAE/OWE)
  --owe                         Show only OWE-encrypted networks (Enhanced Open)
  --new-hs                      Captures new handshakes, ignores existing handshakes in hs (default: off)
  --dict [file]                 File containing passwords for cracking (default: /usr/share/dict/wordlist-probable.txt)

WPS:
  --wps                         Show only WPS-enabled networks
  --wps-only                    Only use WPS PIN & Pixie-Dust attacks (default: off)
  --bully                       Use bully program for WPS PIN & Pixie-Dust attacks (default: reaver)
  --reaver                      Use reaver program for WPS PIN & Pixie-Dust attacks (default: reaver)
  --ignore-locks                Do not stop WPS PIN attack if AP becomes locked (default: stop)

PMKID:
  --pmkid                       Only use PMKID capture, avoids other WPS & WPA attacks (default: off)
  --no-pmkid                    Don't use PMKID capture (default: off)
  --pmkid-timeout [sec]         Time to wait for PMKID capture (default: 300 seconds)

COMMANDS:
  --cracked                     Print previously-cracked access points
  --ignored                     Print ignored access points
  --check [file]                Check a .cap file (or all hs/*.cap files) for WPA handshakes
  --crack                       Show commands to crack a captured handshake
  --update-db                   Update the local MAC address prefix database from IEEE registries"""

    def _match_cmd(self, text, *variants):
        stripped = text.strip().lower()
        for v in variants:
            vl = v.lower()
            if stripped == vl or stripped == f'/{vl}':
                return True
        return False

    def _generate_response(self, command_text, command_type):
        """Generate appropriate response for command."""

        if command_type == 'exit':
            return {
                'text': self.persona.exit_response(),
                'shutdown': True,
                'command_type': 'exit',
                'timestamp': time.time()
            }

        if command_type == 'main_command':
            if self._match_cmd(command_text, 'info', 'status'):
                stats = self._live_stats()
                return {'text': self.persona.info_response(stats), 'command_type': 'info', 'timestamp': time.time(), 'confidence': 0.95}
            elif self._match_cmd(command_text, 'system check', 'systemcheck', 'health'):
                if self.system and hasattr(self.system, 'diagnostician'):
                    report = self.system.diagnostician.run_diagnostics(self.system)
                    lines = [f"Health Check — status: {report['status'].upper()}"]
                    for c in report['components']:
                        lines.append(f"  • {c['name']}: {c['detail']} [{c['status']}]")
                    if report['alerts']:
                        lines.append("Alerts:")
                        for a in report['alerts']:
                            lines.append(f"  ! {a}")
                    else:
                        lines.append("No alerts.")
                    return {'text': '\n'.join(lines), 'command_type': 'system_check', 'timestamp': time.time(), 'confidence': 0.95}
                health = "unknown"
                modules = "?"
                if self.system:
                    if hasattr(self.system, 'sentinel') and hasattr(self.system.sentinel, 'check_system_health'):
                        h = self.system.sentinel.check_system_health()
                        health = h.get('status', 'unknown')
                    modules = "all 7 brain modules functional"
                    if hasattr(self.system, 'is_running'):
                        modules = "all 7 brain modules online" if self.system.is_running else "system degraded"
                stats = self._live_stats()
                return {'text': self.persona.system_check_response(health, modules, stats), 'command_type': 'system_check', 'timestamp': time.time(), 'confidence': 0.95}
            elif self._match_cmd(command_text, 'update'):
                uptime = self.system.resources.get_uptime() if self.system and hasattr(self.system, 'resources') else 0
                return {'text': self.persona.update_response(uptime), 'command_type': 'update', 'timestamp': time.time(), 'confidence': 0.9}
            elif self._match_cmd(command_text, 'shutdown'):
                return {
                    'text': self.persona.shutdown_response(),
                    'shutdown': True,
                    'command_type': 'exit',
                    'timestamp': time.time()
                }
            elif self._match_cmd(command_text, 'learn'):
                return {'text': self.persona.learn_response(), 'command_type': 'learn', 'timestamp': time.time(), 'confidence': 0.9}
            elif self._match_cmd(command_text, 'restart'):
                return {
                    'text': self.persona.restart_response(),
                    'restart': True,
                    'command_type': 'restart',
                    'timestamp': time.time()
                }
            elif self._match_cmd(command_text, 'model'):
                parts = command_text.strip().split()
                if len(parts) >= 2:
                    identifier = parts[1]
                    ok, msg = self.system.model_manager.set_model(identifier)
                    if ok:
                        return {'text': self.persona.model_set(msg), 'command_type': 'model', 'timestamp': time.time(), 'confidence': 0.95}
                    else:
                        return {'text': self.persona.model_not_found(), 'command_type': 'model', 'timestamp': time.time(), 'confidence': 0.9}
                model_info = self.system.model_manager.format_model_list()
                return {'text': self.persona.model_list(model_info), 'command_type': 'model', 'timestamp': time.time(), 'confidence': 0.9}
            elif self._match_cmd(command_text, 'soms'):
                return {'text': self.persona.soms_info(), 'command_type': 'soms', 'timestamp': time.time(), 'confidence': 0.95}
            elif self._match_cmd(command_text, 'help'):
                manual = '/info - Live system status (CPU, RAM, Disk, Uptime)\n/system check - Full health diagnostics\n/update - System version check\n/model - List and select AI models\n/soms - SOMS system information\n/improve - Self-improvement & capabilities\n/timesfm - TimesFM status; /timesfm demo runs a sample forecast\n/packages - Package manager status\n/install <pkg> - Install a package (GUI sudo prompt)\n/remove <pkg> - Remove a package\n/upgrade - Upgrade installed packages\n/update-system - Update lists then upgrade\n/full-upgrade - Full dist-upgrade + cleanup\n/fix-deps - Repair broken dependencies\n/search <query> - Search package repository\n/voice - Test microphone and voice status\n/wifite - Wireless auditing tool help\n/clean - Self-cleaning (remove old logs, temp files, caches)\n/plan <goal> - Architect: turn a goal into an action plan\n/task <name> - Engineer: run a health/overview task\n/grow <axis> - Upgrade performance/intelligence/efficiency/stability (or "all")\n/restart - Restart SOMS\n/shutdown - Graceful shutdown\n/learn - Enable learning mode\n/help - Show this manual'
                return {'text': self.persona.help_text(manual), 'command_type': 'help', 'timestamp': time.time(), 'confidence': 0.95}
            elif self._match_cmd(command_text, 'improve', 'capabilities'):
                summary = self.system.improver.get_status_summary()
                return {'text': summary, 'command_type': 'improve', 'timestamp': time.time(), 'confidence': 0.95}
            elif self._match_cmd(command_text, 'evolve'):
                if self.system and hasattr(self.system, 'evolver'):
                    analysis = self.system.evolver.analyze_logs(force=True)
                    lines = [f"Evolver Analysis ({time.strftime('%H:%M:%S')}):"]
                    lines.append(f"  Logs scanned: {analysis.get('total_logs', 0)}")
                    lines.append(f"  Issues found: {analysis.get('total_issues', 0)}")
                    cats = analysis.get('categories', {})
                    if cats:
                        lines.append("  Breakdown:")
                        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                            lines.append(f"    {cat}: {count}")
                    recs = analysis.get('recommendations', [])
                    if recs:
                        lines.append("  Recommendations:")
                        for r in recs:
                            lines.append(f"    [{r.get('priority','info')}] {r.get('message','')}")
                    if not cats and not recs:
                        lines.append("  No issues detected.")
                    return {'text': '\n'.join(lines), 'command_type': 'evolve', 'timestamp': time.time(), 'confidence': 0.9}
                return {'text': 'Evolver not available.', 'command_type': 'evolve', 'timestamp': time.time(), 'confidence': 0.5}
            elif self._match_cmd(command_text, 'memory'):
                if self.system and hasattr(self.system, 'memory'):
                    status = self.system.memory.get_status()
                    text = (
                        f"Memory Layer Status:\n"
                        f"  Engine: {status.get('engine', 'N/A')}\n"
                        f"  Collections: {status.get('collections', 0)}\n"
                        f"  Documents stored: {status.get('total_documents', 0)}"
                    )
                    return {'text': text, 'command_type': 'memory', 'timestamp': time.time(), 'confidence': 0.9}
                return {'text': 'MemoryLayer not available.', 'command_type': 'memory', 'timestamp': time.time(), 'confidence': 0.5}
            elif self._match_cmd(command_text, 'packages', 'pkgs'):
                if self.system and hasattr(self.system, 'package_architect'):
                    status = self.system.package_architect.get_status()
                    text = (
                        f"PackageArchitect status:\n"
                        f"  Manager: {status.get('manager', '?')}\n"
                        f"  Distro: {status.get('distro', '?')}\n"
                        f"  Online: {status.get('online', False)}"
                    )
                    return {'text': text, 'command_type': 'packages', 'timestamp': time.time(), 'confidence': 0.9}
                return {'text': 'PackageArchitect not available.', 'command_type': 'packages', 'timestamp': time.time(), 'confidence': 0.5}
            elif self._match_cmd(command_text, 'install', 'remove', 'uninstall', 'upgrade', 'update-system',
                                 'full-upgrade', 'fix-deps', 'repair-deps'):
                return self._route_package_command(command_text)
            elif command_text.strip().lower().startswith('/search'):
                arch = self.system.package_architect if self.system and hasattr(self.system, 'package_architect') else None
                if not arch:
                    return {'text': 'PackageArchitect not available.', 'command_type': 'packages', 'timestamp': time.time(), 'confidence': 0.5}
                q = command_text.replace('/search', '').strip()
                ok, out = arch.search(q) if q else (False, 'Usage: /search <query>')
                return {'text': out if out else 'No results.', 'command_type': 'packages', 'timestamp': time.time(), 'confidence': 0.9}
            elif self._match_cmd(command_text, 'clean', 'self-clean', 'cleanup'):
                if self.system and hasattr(self.system, 'cleaner'):
                    dry_run = 'dry' in command_text.lower() or 'dry-run' in command_text.lower()
                    results = self.system.cleaner.clean(dry_run=dry_run)
                    return {'text': self.system.cleaner.report(results), 'command_type': 'clean', 'timestamp': time.time(), 'confidence': 0.95}
                return {'text': 'Cleaner not available.', 'command_type': 'clean', 'timestamp': time.time(), 'confidence': 0.5}
            elif self._match_cmd(command_text, 'wifite'):
                return {'text': self._get_wifite_help(command_text), 'command_type': 'wifite', 'timestamp': time.time(), 'confidence': 0.95}
            elif self._match_cmd(command_text, 'plan'):
                if self.system and hasattr(self.system, 'architect'):
                    goal = command_text.replace('plan', '', 1).strip()
                    steps = self.system.architect.propose_plan(goal, self.system)
                    lines = [f"Plan{(': ' + goal) if goal else ''}:"]
                    lines += [f"  {i}. {s}" for i, s in enumerate(steps, 1)]
                    return {'text': '\n'.join(lines), 'command_type': 'plan', 'timestamp': time.time(), 'confidence': 0.95}
                return {'text': 'Architect not available.', 'command_type': 'plan', 'timestamp': time.time(), 'confidence': 0.5}
            elif self._match_cmd(command_text, 'task'):
                if self.system and hasattr(self.system, 'engineer'):
                    task = command_text.replace('task', '', 1).strip()
                    ok, out = self.system.engineer.run_task(task, self.system)
                    return {'text': out, 'command_type': 'task', 'timestamp': time.time(), 'confidence': 0.9}
                return {'text': 'Engineer not available.', 'command_type': 'task', 'timestamp': time.time(), 'confidence': 0.5}
            elif self._match_cmd(command_text, 'grow', 'upgrade-self'):
                if self.system and hasattr(self.system, 'grower'):
                    spec = command_text.replace('grow', '', 1).replace('upgrade-self', '', 1).strip().lower()
                    return {'text': self.system.grower.grow(spec or 'all'), 'command_type': 'grow', 'timestamp': time.time(), 'confidence': 0.95}
                return {'text': 'Growth engine not available.', 'command_type': 'grow', 'timestamp': time.time(), 'confidence': 0.5}
            elif command_text.strip().lower().startswith('/timesfm') or self._match_cmd(command_text, 'timesfm'):
                service = getattr(self.system, 'timesfm', None) if self.system else None
                if not service:
                    return {'text': 'TimesFM service is not available.', 'command_type': 'timesfm', 'timestamp': time.time(), 'confidence': 0.5}
                try:
                    if 'demo' in command_text.lower() or 'forecast' in command_text.lower():
                        result = service.demo_forecast()
                        text = (
                            "TimesFM demo forecast complete:\n"
                            f"  point_forecast.shape: {result.point_shape}\n"
                            f"  quantile_forecast.shape: {result.quantile_shape}\n"
                            f"  preview: {result.point_preview}"
                        )
                    else:
                        text = service.status_text()
                except Exception as exc:
                    text = f"TimesFM error: {exc}"
                return {'text': text, 'command_type': 'timesfm', 'timestamp': time.time(), 'confidence': 0.9}
            else:
                improver_result = self.system.improver.route(command_text) if self.system and hasattr(self.system, 'improver') else None
                if improver_result:
                    return improver_result
                return {'text': self.persona.unknown_command(command_text), 'command_type': 'unknown', 'timestamp': time.time(), 'confidence': 0.7}

        elif command_type == 'weather':
            return {'text': self.persona.weather_response(), 'command_type': 'weather', 'timestamp': time.time(), 'confidence': 0.8}

        elif command_type == 'math':
            try:
                import ast, operator
                _OP = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}
                def _eval_node(node):
                    if isinstance(node, ast.Constant): return node.value
                    if isinstance(node, ast.BinOp): return _OP[type(node.op)](_eval_node(node.left), _eval_node(node.right))
                    if isinstance(node, ast.UnaryOp): return _OP[type(node.op)](_eval_node(node.operand))
                    raise ValueError
                expr = command_text.replace('calculate', '').replace('compute', '').replace('solve', '').strip()
                result = _eval_node(ast.parse(expr, mode='eval').body)
                return {'text': self.persona.math_response(expr, result), 'command_type': 'math', 'timestamp': time.time(), 'confidence': 0.95}
            except Exception:
                return {'text': self.persona.math_error(), 'command_type': 'math', 'timestamp': time.time(), 'confidence': 0.7}

        elif command_type == 'search':
            query = command_text.replace('search', '').replace('find', '').replace('lookup', '').strip()
            return {'text': self.persona.search_response(query), 'command_type': 'search', 'timestamp': time.time(), 'confidence': 0.8}

        elif command_type == 'application':
            app_name = self._extract_application_name(command_text)
            return {'text': self.persona.app_launch(app_name), 'command_type': 'application', 'timestamp': time.time(), 'confidence': 0.8}

        elif command_type == 'system_install':
            return self._handle_system_install(command_text)

        elif command_type == 'system_maintenance':
            return self._handle_system_maintenance(command_text)

        elif command_type == 'camera':
            if self.system and hasattr(self.system, 'improver'):
                result = self.system.improver.handle_camera(command_text)
                if result:
                    return {**result, 'command_type': 'camera', 'timestamp': time.time(), 'confidence': 0.9}
            return {'text': 'Camera module not available.', 'command_type': 'camera', 'timestamp': time.time(), 'confidence': 0.5}

        elif command_type == 'hacking_demo':
            if self.system and hasattr(self.system, 'demonstrator'):
                topic = self.system.demonstrator.detect_topic(command_text)
                if topic:
                    guide = self.system.demonstrator.run_demo(topic, progress_callback=self._progress_callback)
                    return {'text': guide, 'command_type': 'hacking_demo', 'timestamp': time.time(), 'confidence': 0.95}
            return {'text': 'Demonstrator module not available.', 'command_type': 'hacking_demo', 'timestamp': time.time(), 'confidence': 0.5}

        else:
            query = command_text.lower()
            if any(w in query for w in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'greetings']):
                return {'text': self.persona.greet(), 'command_type': 'greeting', 'timestamp': time.time(), 'confidence': 0.95}
            elif any(w in query for w in ['who are you', 'what are you', 'your name', 'introduce']):
                return {'text': self.persona.who_are_you(), 'command_type': 'introduction', 'timestamp': time.time(), 'confidence': 0.95}
            elif any(w in query for w in ['capabilities', 'what can you', 'features']):
                return {'text': self.persona.capabilities(), 'command_type': 'capabilities', 'timestamp': time.time(), 'confidence': 0.95}
            elif any(w in query for w in ['time', 'date', 'clock']):
                return {'text': self.persona.time_response(), 'command_type': 'time', 'timestamp': time.time(), 'confidence': 0.95}
            elif any(w in query for w in ['thank', 'thanks', 'appreciate']):
                return {'text': self.persona.thanks_response(), 'command_type': 'thanks', 'timestamp': time.time(), 'confidence': 0.95}
            elif any(w in query for w in ['goodbye', 'bye', 'see you']):
                return {
                    'text': self.persona.farewell(),
                    'shutdown': True,
                    'command_type': 'exit',
                    'timestamp': time.time()
                }
            elif any(w in query for w in ['joke', 'funny', 'humor', 'laugh']):
                return {'text': self.persona.joke_response(), 'command_type': 'joke', 'timestamp': time.time(), 'confidence': 0.9}
            elif any(w in query for w in ['how are you', 'how do you feel', 'status']):
                stats = self._live_stats()
                return {'text': self.persona.status_response(stats), 'command_type': 'status', 'timestamp': time.time(), 'confidence': 0.95}
            elif any(w in query for w in ['song', 'music', 'play', 'songs']):
                return {'text': self.persona.music_response(), 'command_type': 'music', 'timestamp': time.time(), 'confidence': 0.8}
            elif any(w in query for w in ['weather', 'temperature', 'forecast']):
                return {'text': self.persona.weather_response(), 'command_type': 'weather', 'timestamp': time.time(), 'confidence': 0.8}
            else:
                # Try to use the LLM/agent for a real response instead of a canned reply
                if self.system and hasattr(self.system, 'agent'):
                    agent_resp = self.system.agent.process_request(command_text)
                    if agent_resp and agent_resp.get('text'):
                        return {'text': agent_resp['text'], 'command_type': 'natural', 'timestamp': time.time(), 'confidence': 0.85}
                return {'text': self.persona.general_response(command_text), 'command_type': 'natural', 'timestamp': time.time(), 'confidence': 0.7}

    def _route_package_command(self, command_text):
        """Handle explicit /install /remove /upgrade /update-system /fix-deps commands."""
        arch = self.system.package_architect if self.system and hasattr(self.system, 'package_architect') else None
        if not arch:
            return {'text': 'PackageArchitect not available.', 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.5}
        low = command_text.lower()
        parts = command_text.strip().split()
        action = parts[0].lstrip('/').split()[0] if parts else 'install'
        try:
            if action in ('remove', 'uninstall'):
                if len(parts) < 2:
                    return {'text': "Usage: /remove <package>", 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.85}
                ok, msg, out = arch.remove(parts[1].strip())
            elif action == 'install':
                if len(parts) < 2:
                    return {'text': "Usage: /install <package>", 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.85}
                ok, msg, out = arch.install(parts[1].strip())
            elif 'full-upgrade' in low:
                ok, msg, out = arch.full_upgrade()
            elif 'update-system' in low or ('update' in low and 'upgrade' in low):
                ok, msg, out = arch.update_and_upgrade()
            elif 'upgrade' in low:
                ok, msg, out = arch.upgrade()
            elif 'fix-deps' in low or 'repair-deps' in low:
                ok, msg, out = arch.fix_dependencies()
            else:
                ok, msg, out = arch.update_and_upgrade()
        except Exception as e:
            return {'text': f"Package operation error: {e}", 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.7}
        text = msg
        if not ok and isinstance(out, str) and out:
            text += f"\n\n{out[-800:]}"
        return {'text': text, 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.95}

    def _extract_application_name(self, command_text):
        """Extract application name from command."""
        words = command_text.split()
        skip_words = {'open', 'launch', 'start', 'run'}

        for word in words:
            if word not in skip_words:
                return word
        return 'application'

    def _extract_package_name(self, text):
        words = text.strip().split()
        for i, w in enumerate(words):
            if w in ('install', 'uninstall', 'remove', 'package'):
                if i + 1 < len(words):
                    return words[i + 1].strip().lower()
        for w in reversed(words):
            if w not in ('install', 'uninstall', 'remove', 'package', 'the', 'a', 'an', 'please', 'sudo') and not w.startswith('/'):
                return w.lower()
        return ''

    def _handle_system_install(self, command_text):
        if not self.system or not hasattr(self.system, 'package_architect'):
            return {'text': 'PackageArchitect not available.', 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.5}
        pkg = self._extract_package_name(command_text)
        if not pkg:
            return {'text': 'Which package should I install? Example: "install htop"', 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.8}
        auditor = self.system.auditor if hasattr(self.system, 'auditor') else None
        if auditor and hasattr(auditor, 'validate_package_install'):
            validation = auditor.validate_package_install(pkg)
            if not validation['allowed']:
                reasons = '; '.join(validation['violations'])
                return {'text': f"Auditor blocked '{pkg}': {reasons}", 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.95}
        arch = self.system.package_architect
        ok, msg, output = arch.install(pkg)
        if ok:
            return {'text': f"PackageArchitect: {msg}", 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.95}
        return {'text': f"Install failed: {msg}", 'command_type': 'system_install', 'timestamp': time.time(), 'confidence': 0.8}

    def _handle_system_maintenance(self, command_text):
        if not self.system or not hasattr(self.system, 'package_architect'):
            return {'text': 'PackageArchitect not available.', 'command_type': 'system_maintenance', 'timestamp': time.time(), 'confidence': 0.5}
        arch = self.system.package_architect
        text_lower = command_text.lower()
        if 'fix' in text_lower or 'repair' in text_lower:
            ok, msg, output = arch.fix_dependencies()
            return {'text': f"PackageArchitect: {msg}", 'command_type': 'system_maintenance', 'timestamp': time.time(), 'confidence': 0.9}
        if ('upgrade' in text_lower or 'update' in text_lower) and ('and' in text_lower or 'upgrade' in text_lower and 'update' in text_lower):
            ok, msg, output = arch.update_and_upgrade()
            return {'text': f"PackageArchitect: {msg}", 'command_type': 'system_maintenance', 'timestamp': time.time(), 'confidence': 0.9}
        if 'upgrade' in text_lower:
            ok, msg, output = arch.upgrade()
            return {'text': f"PackageArchitect: {msg}", 'command_type': 'system_maintenance', 'timestamp': time.time(), 'confidence': 0.9}
        ok, msg, output = arch.update_repos()
        return {'text': f"PackageArchitect: {msg}", 'command_type': 'system_maintenance', 'timestamp': time.time(), 'confidence': 0.9}

    def is_active(self):
        """Check if orchestrator is running."""
        return self._running
