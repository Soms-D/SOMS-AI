"""
Agent Module for SOMS
Core cognitive agent that thinks about user requests and learns from interactions
"""

import time
import logging
import random
from .persona import Persona
from . import skills
from .constants import HOW_TO_PATTERNS, WAKE_PREFIXES

logger = logging.getLogger('Agent')
class Agent:
    """Core cognitive agent for SOMS system."""

    def __init__(self, system_ref):
        self.system = system_ref
        self.config = system_ref.config
        self.memory = []
        self.knowledge_base = {}
        self.personality = "professional"
        self.experience_count = 0
        self.last_interaction = 0
        self.persona = Persona(system_ref)
        # In-session conversation turns (role/content) for context within a session.
        self.session_history = []
        # Keyword triggers for storing a private, long-term note about the user.
        self._secret_triggers = [
            'my secret', 'remember that', "don't tell", 'do not tell', 'keep this',
            'keep it secret', 'always remember', 'note that', 'remember this',
            'between us', 'confide', 'i trust you',
        ]

    def _strip_soms_prefix(self, text):
        if not text:
            return text
        t = text.lower().strip()
        for prefix in WAKE_PREFIXES:
            if t.startswith(prefix):
                remainder = t[len(prefix):].strip()
                return remainder if remainder else ''
        return text

    def process_request(self, request, context=None):
        """Think about user request and figure out the best response."""
        self.experience_count += 1
        self.last_interaction = time.time()

        try:
            request = self._strip_soms_prefix(request)
            stripped = request.strip().lower()
            if stripped == '':
                return self._handle_soms_request()
            if stripped in ('exit', 'quit', '/shutdown', 'reboot', 'goodbye', 'bye'):
                return self._handle_shutdown_request()
            if request.startswith('/info'):
                return self._handle_info_request(request)
            elif request.startswith('/system check'):
                return self._handle_system_check()
            elif request.startswith('/update'):
                return self._handle_update_request()
            elif request.startswith('/shutdown'):
                return self._handle_shutdown_request()
            elif request.startswith('/learn'):
                return self._handle_learning_request(request)
            elif request.startswith('/restart'):
                return self._handle_restart_request()
            elif request.startswith('/model'):
                return self._handle_model_request(request)
            elif request.startswith('/soms'):
                return self._handle_soms_request()
            elif request.startswith('/help'):
                return self._handle_help_request()
            elif request.startswith('/improve') or request.startswith('/capabilities'):
                return self._handle_improve_request()
            elif request.startswith('/plan'):
                return self._handle_plan_request(request)
            elif request.startswith('/task'):
                return self._handle_task_request(request)
            elif request.startswith('/grow') or request.startswith('/upgrade-self'):
                return self._handle_grow_request(request)
            elif request.startswith('/timesfm'):
                return self._handle_timesfm_request(request)
            elif request.startswith('/evolve'):
                return self._handle_evolve_request()
            elif request.startswith('/memory'):
                return self._handle_memory_request()
            elif request.startswith('/forget'):
                return self._handle_forget_request(request)
            elif request.startswith('/email'):
                return self._handle_email_request(request)
            elif request.startswith('/clean') or request.startswith('/self-clean') or request.startswith('/cleanup'):
                return self._handle_clean_request(request)
            elif request.startswith('/self-heal') or request.startswith('/diagnose'):
                return self._handle_self_heal_request(request)
            elif request.startswith('/packages') or request.startswith('/pkgs'):
                return self._handle_packages_request()
            elif request.startswith('/install') or request.startswith('/remove') or request.startswith('/uninstall'):
                return self._handle_pkg_install_request(request)
            elif request.startswith('/upgrade') or request.startswith('/update-system') or request.startswith('/full-upgrade'):
                return self._handle_pkg_maintenance_request(request)
            elif request.startswith('/fix-deps') or request.startswith('/repair-deps'):
                return self._handle_pkg_maintenance_request(request)
            elif request.startswith('/search'):
                return self._handle_pkg_search_request(request)
            elif request.startswith('/wifite'):
                return self._handle_wifite_request(request)
            elif request.startswith('/voice') or request.startswith('/mic') or request.startswith('/test mic'):
                return self._handle_voice_test()
            elif request.startswith('@'):
                return self._handle_context_injection(request)
            else:
                if any(p in stripped for p in HOW_TO_PATTERNS):
                    return self._handle_demonstration_request(request)
                skill = self._detect_skill(request)
                if skill:
                    name, q = skill
                    result = self._run_skill(name, q)
                    return {
                        'text': self._companion_reply(request, action_result=result),
                        'type': 'agent_response', 'timestamp': time.time(),
                    }
                improver_result = self.system.improver.route(request) if self.system and hasattr(self.system, 'improver') else None
                if improver_result:
                    return improver_result
                return self._handle_general_request(request)
        except Exception as e:
            logger.error(f"Error thinking about request: {e}")
            return {'text': self.persona.error_response(), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_info_request(self, request):
        """Handle system information requests."""
        start_time = getattr(self.system, 'system_start_time', time.time()) if self.system else time.time()
        info = {
            'system_uptime': time.time() - start_time,
            'cpu_usage': 0,
            'memory_usage': 0,
            'active_modules': [],
            'persona': self.personality,
            'experience_count': self.experience_count,
            'last_interaction': self.last_interaction
        }
        return info

    def _handle_system_check(self):
        """Handle system health check requests with real diagnostics."""
        diag = getattr(self.system, 'diagnostician', None)
        if diag:
            report = diag.run_diagnostics(self.system)
            lines = [f"System Check — status: {report['status'].upper()}"]
            for c in report['components']:
                lines.append(f"  • {c['name']}: {c['detail']} [{c['status']}]")
            if report['alerts']:
                lines.append("Alerts:")
                for a in report['alerts']:
                    lines.append(f"  ! {a}")
            else:
                lines.append("No alerts.")
            return {'text': '\n'.join(lines), 'type': 'agent_response', 'timestamp': time.time()}
        return {'text': self.persona.system_check_response('healthy', 'all systems operational', ''), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_update_request(self):
        """Handle system update requests."""
        uptime = self.system.resources.get_uptime() if self.system and hasattr(self.system, 'resources') else 0
        return {'text': self.persona.update_response(uptime), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_shutdown_request(self):
        """Handle system shutdown requests."""
        return {'response': {'text': self.persona.shutdown_response(), 'type': 'agent_response', 'timestamp': time.time()}, 'shutdown': True}

    def _handle_learning_request(self, request):
        """Handle learning requests."""
        return {'text': self.persona.learn_response(), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_restart_request(self):
        """Handle restart requests."""
        return {'response': {'text': self.persona.restart_response(), 'type': 'agent_response', 'timestamp': time.time()}, 'restart': True}

    def _handle_model_request(self, request):
        """Handle model selection requests."""
        parts = request.strip().split()
        if not hasattr(self.system, 'model_manager'):
            return {'text': 'ModelManager not available.', 'type': 'agent_response', 'timestamp': time.time()}
        if len(parts) >= 2:
            identifier = parts[1]
            ok, msg = self.system.model_manager.set_model(identifier)
            if ok:
                current = self.system.model_manager.get_current_model()
                if hasattr(self.system, 'llm') and self.system.llm:
                    self.system.llm.default_model = current
                try:
                    self.system.config.set('llm', 'default_model', value=current)
                except Exception:
                    pass
                text = self.persona.model_set(msg)
            else:
                text = self.persona.model_not_found()
            return {'text': text, 'type': 'agent_response', 'timestamp': time.time()}
        model_info = self.system.model_manager.format_model_list()
        return {'text': self.persona.model_list(model_info), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_soms_request(self):
        """Handle SOMS info requests."""
        return {'text': self.persona.soms_info(), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_improve_request(self):
        """Handle improvement/capabilities requests."""
        if not hasattr(self.system, 'improver'):
            return {'text': 'Improver not available.', 'type': 'agent_response', 'timestamp': time.time()}
        summary = self.system.improver.get_status_summary()
        return {'text': summary, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_plan_request(self, request):
        """Turn a goal into an ordered, actionable plan via the Architect."""
        architect = getattr(self.system, 'architect', None)
        if not architect:
            return {'text': 'Architect not available.', 'type': 'agent_response', 'timestamp': time.time()}
        goal = request.replace('/plan', '', 1).strip()
        steps = architect.propose_plan(goal, self.system)
        lines = [f"Plan{(': ' + goal) if goal else ''}:"]
        for i, step in enumerate(steps, 1):
            lines.append(f"  {i}. {step}")
        return {'text': '\n'.join(lines), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_task_request(self, request):
        """Run a named task via the Engineer."""
        engineer = getattr(self.system, 'engineer', None)
        if not engineer:
            return {'text': 'Engineer not available.', 'type': 'agent_response', 'timestamp': time.time()}
        task = request.replace('/task', '', 1).strip()
        ok, out = engineer.run_task(task, self.system)
        return {'text': out, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_grow_request(self, request):
        """Upgrade SOMS along one or more axes: performance, intelligence,
        efficiency, stability (or 'all'). Returns a report of what changed."""
        grower = getattr(self.system, 'grower', None)
        if not grower:
            return {'text': 'Growth engine not available.', 'type': 'agent_response', 'timestamp': time.time()}
        spec = request.replace('/grow', '', 1).strip().lower()
        report = grower.grow(spec or 'all')
        return {'text': report, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_help_request(self):
        """Handle help requests."""
        manual = '/info - System status\n/system check - Health check\n/update - System improvement\n/model - List/select AI models\n/soms - SOMS information\n/improve - Self-improvement & capabilities\n/memory - Memory layer status\n/timesfm - TimesFM status; /timesfm demo runs a sample forecast\n/packages - Package manager status\n/install <pkg> - Install a package (asks for sudo via GUI dialog)\n/remove <pkg> - Remove a package\n/upgrade - Upgrade installed packages\n/update-system - Update lists then upgrade\n/full-upgrade - Full dist-upgrade + autoremove + autoclean\n/fix-deps - Repair broken dependencies\n/search <query> - Search the package repository\n/forget - Erase what SOMS remembers (add "secrets" or "chat" to scope it)\n/email - Check email (or: /email set <user> <server> [password])\n/camera - Look through the camera and describe what it sees\n/camera stop (or "stop all cameras") - Disable camera access (privacy mode)\n/camera start (or "enable camera") - Re-enable camera access\n/self-heal (or /diagnose) - Scan logs for errors and auto-fix what it can\n/clean (or /self-clean) - Remove old logs, temp files, and caches\n/plan <goal> - Architect: turn a goal into an action plan\n/task <name> - Engineer: run a health/overview task\n/grow <axis> - Upgrade performance/intelligence/efficiency/stability (or "all")\n/wifite - Wireless auditing tool help\n/restart - Restart SOMS\n/shutdown - Graceful shutdown\n/exit or /quit - Immediate exit'
        return {'text': self.persona.help_text(manual), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_timesfm_request(self, request):
        service = getattr(self.system, 'timesfm', None)
        if not service:
            return {'text': 'TimesFM service is not available.', 'type': 'agent_response', 'timestamp': time.time()}
        try:
            if 'demo' in request.lower() or 'forecast' in request.lower():
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
        return {'text': text, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_context_injection(self, request):
        """Handle context injection for deep task analysis."""
        return {'text': self.persona.general_response(request.replace('@', '').strip()), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_general_request(self, request):
        """Handle general user requests as a real, private conversation."""
        return {'text': self._companion_reply(request), 'type': 'agent_response', 'timestamp': time.time()}

    # -- Real-world skills (files, music, youtube, movies, weather, email) --

    def _detect_skill(self, request):
        """Detect an actionable real-world intent and return (skill, query)."""
        low = request.lower().strip()
        if any(k in low for k in ['play music', 'some music', 'put on music', 'music please', 'play some songs']):
            q = low.split('play', 1)[-1].replace('music', '').replace('some', '') \
                     .replace('please', '').strip(' .')
            return ('music', q)
        if 'youtube' in low:
            q = low.split('youtube', 1)[-1].replace('search', '').replace('play', '') \
                 .replace('on', '').strip(' .')
            return ('youtube', q)
        if any(k in low for k in ['play a movie', 'watch a movie', 'watch movie', 'play movie', 'movie']):
            q = low.split('movie', 1)[-1].strip(' .')
            return ('movie', q)
        if any(k in low for k in ['weather', 'forecast', 'temperature']):
            q = ''
            for prep in [' in ', ' for ', ' at ', ' near ', ' of ']:
                if prep in low:
                    q = low.split(prep, 1)[1].strip(' .?!')
                    break
            return ('weather', q)
        if any(k in low for k in ['check email', 'check my mail', 'my email', 'my mail',
                                  'read email', 'read mail', 'emails', 'open email', 'open my mail']):
            return ('email', None)
        if any(k in low for k in ['open file', 'show my files', 'open my files', 'open folder',
                                  'my files', 'find file', 'open my file']):
            q = low.replace('open', '').replace('file', '').replace('folder', '').replace('my', '') \
                  .replace('show', '').replace('me', '').replace('find', '').strip(' .')
            return ('file', q)
        if any(k in low for k in ['search for', 'search the web', 'google']):
            q = low.replace('search for', '').replace('search the web', '').replace('google', '').strip(' .')
            return ('web', q)
        # Camera control (checked before describe): stop/start all cameras
        if any(k in low for k in ['stop all cameras', 'stop camera', 'turn off camera',
                                  'disable camera', 'camera off', 'cameras off']):
            return ('camerastop', None)
        if any(k in low for k in ['start camera', 'enable camera', 'turn on camera',
                                  'camera on', 'cameras on']):
            return ('camerastart', None)
        # Camera / vision: "what do you see", "check the camera", "what's happening on camera"
        if any(k in low for k in ['camera', 'webcam', 'what do you see', 'what can you see',
                                  'whats on the camera', "what's on the camera",
                                  'what is on the camera', 'whats happening', 'what is happening']):
            q = low
            for token in ['what do you see', 'what can you see', 'on the camera',
                          'the camera', 'camera', 'webcam', 'whats happening',
                          'what is happening', 'happening', 'check', 'show me',
                          'look', 'see', 'whats', "what's", 'what is', 'on', 'the', 'a', 'is']:
                q = q.replace(token, ' ')
            q = q.strip(' ?.')
            if not q or q in ('me',):
                q = None
            return ('camera', q)
        return None

    def _run_skill(self, name, query):
        cfg = self.config
        if name == 'music':
            return skills.play_music(query)
        if name == 'youtube':
            return skills.youtube(query)
        if name == 'movie':
            return skills.play_movie(query)
        if name == 'weather':
            return skills.check_weather(query, cfg)
        if name == 'email':
            return skills.check_email(cfg)
        if name == 'file':
            return skills.open_file(query)
        if name == 'web':
            return skills.search_web(query)
        if name == 'camera':
            return skills.describe_camera(query, llm=self.system.llm if hasattr(self.system, 'llm') else None)
        if name == 'camerastop':
            return skills.stop_cameras()
        if name == 'camerastart':
            return skills.start_cameras()
        return None

    def _companion_reply(self, user_text, action_result=None):
        """Generate a confidential, memory-aware conversational reply.

        Uses the LLM when available; otherwise falls back to an empathetic message.
        All exchanges are stored locally so SOMS remembers past conversations and
        keeps the user's secrets private.
        """
        llm = getattr(self.system, 'llm', None)
        memory = getattr(self.system, 'memory', None)
        honorific = self.persona._honorific() if hasattr(self.persona, '_honorific') else ''

        messages = [{'role': 'system', 'content': self.persona.advisor_system_prompt()}]

        # Recall private long-term notes about the user (secrets, things to remember).
        if memory:
            try:
                for note in memory.recall_recent('profile', 40):
                    doc = note.get('document', '')
                    if doc:
                        messages.append({
                            'role': 'system',
                            'content': f"[Private memory about the user — keep strictly confidential] {doc}",
                        })
            except Exception:
                pass

        # Recall past conversations so SOMS remembers earlier sessions. Only when the
        # current session has no turns yet, to avoid duplicating in-session context.
        if memory and not self.session_history:
            try:
                for past in memory.recall_recent('conversations', 14):
                    meta = past.get('metadata', {}) or {}
                    role = meta.get('role', 'user')
                    doc = past.get('document', '')
                    if doc:
                        messages.append({'role': role, 'content': doc})
            except Exception:
                pass

        # Recent turns from the current session.
        for turn in self.session_history[-10:]:
            messages.append(turn)

        # If we just performed a real-world action, let the model acknowledge it
        # naturally (so it feels like talking to a person, not a script).
        if action_result:
            messages.append({
                'role': 'system',
                'content': f"[You just performed this action for the user — acknowledge it naturally in your reply] {action_result}",
            })

        messages.append({'role': 'user', 'content': user_text})

        # Research mode: when enabled, fetch web context so factual answers are
        # accurate even when the local model is unsure. Best-effort; ignored if
        # offline or scraping fails.
        research_on = False
        try:
            research_on = bool(self.config.get('system', 'research_mode', default=False))
        except Exception:
            pass
        if research_on and llm:
            try:
                from . import skills as _skills
                web_ctx = _skills.web_answer(user_text)
                if web_ctx:
                    messages.append({
                        'role': 'system',
                        'content': ("[Web research context — use this to answer "
                                    "accurately and cite facts] " + web_ctx),
                    })
            except Exception:
                pass

        used_llm = False
        if llm and llm.available():
            try:
                model = llm.select_model(user_text)
                reply = llm.chat(messages, model=model)
                used_llm = True
            except Exception as e:
                logger.warning(f"LLM chat failed: {e}")
                reply = self.persona.companion_fallback(user_text)
        else:
            reply = self.persona.companion_fallback(user_text)

        # If the LLM couldn't acknowledge the action, report it directly so the
        # user still gets confirmation of what SOMS did.
        if action_result and not used_llm:
            reply = f"{action_result}\n\n{reply}"

        # If the language model was unavailable/unreachable, still try to give a
        # correct, sourced answer for factual questions via web research.
        if not used_llm:
            try:
                from . import skills as _skills
                web_ctx = _skills.web_answer(user_text)
                if web_ctx:
                    reply = ("I couldn't reach my local language model, so I "
                             "researched this for you instead:\n" + web_ctx)
            except Exception:
                pass

        # Persist the exchange locally.
        if memory:
            try:
                memory.store('conversations', user_text, {'role': 'user'})
                memory.store('conversations', reply, {'role': 'assistant'})
                self._maybe_store_profile(user_text, memory)
            except Exception as e:
                logger.debug(f"Memory store failed: {e}")

        self.session_history.append({'role': 'user', 'content': user_text})
        self.session_history.append({'role': 'assistant', 'content': reply})
        return reply

    def _maybe_store_profile(self, user_text, memory):
        """Store a private long-term note when the user explicitly shares/asks to remember."""
        low = (user_text or '').lower()
        if any(t in low for t in self._secret_triggers):
            try:
                memory.store('profile', user_text, {'kind': 'user_note'})
                logger.info("Stored private user note to profile memory")
            except Exception:
                pass

    def _handle_evolve_request(self):
        analysis = self.system.evolver.analyze_logs(force=True) if hasattr(self.system, 'evolver') else {}
        if not analysis:
            return {'text': 'Evolver not available.', 'type': 'agent_response', 'timestamp': time.time()}
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
            lines.append("  No issues detected — system is healthy.")
        return {'text': '\n'.join(lines), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_memory_request(self):
        if not hasattr(self.system, 'memory'):
            return {'text': 'MemoryLayer not available.', 'type': 'agent_response', 'timestamp': time.time()}
        status = self.system.memory.get_status()
        lines = [
            f"Memory Layer Status:",
            f"  Engine: {status.get('engine', 'N/A')}",
            f"  Collections: {status.get('collections', 0)}",
            f"  Documents stored: {status.get('total_documents', 0)}",
        ]
        if hasattr(self.system, 'interactions_collection'):
            try:
                interactions = self.system.memory.recall_recent('interactions', 3)
                if interactions:
                    lines.append("  Recent interactions:")
                    for i in interactions:
                        doc = i.get('document', '')[:80]
                        lines.append(f"    - {doc}")
            except Exception:
                pass
        return {'text': '\n'.join(lines), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_forget_request(self, request):
        """Erase SOMS's private memory of the user (local only)."""
        memory = getattr(self.system, 'memory', None)
        low = request.lower()
        if 'secret' in low:
            targets = ['profile']
        elif 'chat' in low or 'conversation' in low:
            targets = ['conversations']
        else:
            targets = ['conversations', 'profile']

        if memory:
            for t in targets:
                memory.clear_collection(t)
        self.session_history = []

        if targets == ['profile']:
            msg = "Done. I've forgotten the private notes and secrets you asked me to remember. Our chat history stays intact."
        elif targets == ['conversations']:
            msg = "Done. I've cleared our conversation memory. Your private notes are still safe with me."
        else:
            msg = "Done. I've wiped everything I remembered about you — conversations and private notes. Clean slate."
        return {'text': msg, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_clean_request(self, request):
        """Handle self-cleaning requests."""
        cleaner = getattr(self.system, 'cleaner', None)
        if not cleaner:
            return {'text': 'Cleaner not available.', 'type': 'agent_response', 'timestamp': time.time()}
        dry_run = 'dry' in request.lower() or 'dry-run' in request.lower()
        scope = 'all'
        for s in ('logs', 'temp', 'cache', 'state'):
            if s in request.lower():
                scope = s
                break
        results = cleaner.clean(scope=scope, dry_run=dry_run)
        return {'text': cleaner.report(results), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_self_heal_request(self, request):
        """Scan logs for errors and automatically apply safe fixes where possible."""
        healer = getattr(self.system, 'self_heal', None)
        if not healer:
            return {'text': 'Self-Healer not available.', 'type': 'agent_response', 'timestamp': time.time()}
        results = healer.scan_and_fix(auto_apply=True)
        return {'text': healer.report_text(results), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_email_request(self, request):
        """Check email, or configure IMAP credentials: /email set <user> <server> [password]."""
        parts = request.strip().split()
        if len(parts) >= 3 and parts[1] == 'set':
            args = parts[2:]
            if len(args) >= 2:
                user, server = args[0], args[1]
                pw = args[2] if len(args) >= 3 else ''
                self.config.set('email', 'user', value=user)
                self.config.set('email', 'server', value=server)
                if pw:
                    self.config.set('email', 'password', value=pw)
                return {'text': f"Saved email settings for {user} on {server}. "
                                 f"Say 'check my email' and I'll report unread messages.",
                        'type': 'agent_response', 'timestamp': time.time()}
            return {'text': "Usage: /email set <user@domain.com> <imap.server.com> [password]",
                    'type': 'agent_response', 'timestamp': time.time()}
        result = skills.check_email(self.config)
        return {'text': result, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_packages_request(self):
        if not hasattr(self.system, 'package_architect'):
            return {'text': 'PackageArchitect not available.', 'type': 'agent_response', 'timestamp': time.time()}
        status = self.system.package_architect.get_status()
        return {'text': f"PackageArchitect status:\n  Manager: {status.get('manager', '?')}\n  Distro: {status.get('distro', '?')}\n  Online: {status.get('online', False)}", 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_pkg_install_request(self, request):
        arch = getattr(self.system, 'package_architect', None)
        if not arch:
            return {'text': 'PackageArchitect not available.', 'type': 'agent_response', 'timestamp': time.time()}
        parts = request.strip().split()
        action = parts[0].lstrip('/').split()[0] if parts else 'install'
        if len(parts) < 2:
            return {'text': f"Usage: /{action} <package>  (e.g. /{action} htop)", 'type': 'agent_response', 'timestamp': time.time()}
        pkg = parts[1].strip()
        remove = action in ('remove', 'uninstall')
        try:
            if remove:
                ok, msg, out = arch.remove(pkg)
            else:
                ok, msg, out = arch.install(pkg)
        except Exception as e:
            return {'text': f"Package operation error: {e}", 'type': 'agent_response', 'timestamp': time.time()}
        text = msg
        if not ok and out:
            text += f"\n\n{out[-800:]}" if isinstance(out, str) else ""
        return {'text': text, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_pkg_maintenance_request(self, request):
        arch = getattr(self.system, 'package_architect', None)
        if not arch:
            return {'text': 'PackageArchitect not available.', 'type': 'agent_response', 'timestamp': time.time()}
        low = request.lower()
        try:
            if 'full-upgrade' in low:
                ok, msg, out = arch.full_upgrade()
            elif 'update-system' in low or ('update' in low and 'upgrade' in low):
                ok, msg, out = arch.update_and_upgrade()
            elif 'upgrade' in low:
                ok, msg, out = arch.upgrade()
            elif 'fix-deps' in low or 'repair-deps' in low:
                ok, msg, out = arch.fix_dependencies()
            elif 'update' in low:
                ok, msg, out = arch.update_repos()
            else:
                ok, msg, out = arch.update_and_upgrade()
        except Exception as e:
            return {'text': f"Maintenance error: {e}", 'type': 'agent_response', 'timestamp': time.time()}
        text = msg
        if not ok and isinstance(out, str) and out:
            text += f"\n\n{out[-800:]}"
        return {'text': text, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_pkg_search_request(self, request):
        arch = getattr(self.system, 'package_architect', None)
        if not arch:
            return {'text': 'PackageArchitect not available.', 'type': 'agent_response', 'timestamp': time.time()}
        q = request.replace('/search', '').replace('pkg', '').replace('package', '').replace('apt', '').strip()
        if not q:
            return {'text': "Usage: /search <query>  (e.g. /search editor)", 'type': 'agent_response', 'timestamp': time.time()}
        ok, out = arch.search(q)
        return {'text': out if out else "No results.", 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_wifite_request(self, request):
        import subprocess
        parts = request.strip().split()
        args = parts[1:] if len(parts) > 1 else []
        if args and args[0] == 'sudo':
            args = args[1:]
        if not args or args[0] in ('-h', '--help'):
            orchestrator = getattr(self.system, 'orchestrator', None)
            help_text = orchestrator.get_wifite_help() if orchestrator else ''
            return {'text': help_text, 'type': 'agent_response', 'timestamp': time.time()}
        cmd = ['sudo', 'wifite'] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            text = r.stdout or r.stderr or "No output."
        except FileNotFoundError:
            text = "wifite is not installed. Install it with: sudo apt install wifite"
        except subprocess.TimeoutExpired:
            text = "wifite timed out (120s limit)."
        except Exception as e:
            text = f"Error: {e}"
        return {'text': text, 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_demonstration_request(self, request):
        """Handle step-by-step demonstration requests."""
        if not hasattr(self.system, 'demonstrator'):
            return {'text': 'Demonstrator module not available.', 'type': 'agent_response', 'timestamp': time.time()}
        topic = self.system.demonstrator.detect_topic(request)
        if topic:
            guide = self.system.demonstrator.run_demo(topic)
            return {'text': guide, 'type': 'agent_response', 'timestamp': time.time()}
        return {'text': self.persona.general_response(request), 'type': 'agent_response', 'timestamp': time.time()}

    def _handle_voice_test(self):
        """Handle voice/microphone test requests."""
        if not hasattr(self.system, 'voice'):
            return {'text': 'Voice module not available.', 'type': 'agent_response', 'timestamp': time.time()}
        
        voice = self.system.voice
        status = voice.get_status()
        
        # Build status report
        lines = ["Voice Interface Status:"]
        lines.append(f"  STT Available: {'Yes' if status.get('stt_available') else 'No'}")
        lines.append(f"  TTS Available: {'Yes' if status.get('tts_available') else 'No'}")
        lines.append(f"  Microphone Available: {'Yes' if status.get('mic_available') else 'No'}")
        lines.append(f"  Using arecord: {'Yes' if status.get('using_arecord') else 'No'}")
        lines.append(f"  Listening: {'Yes' if status.get('listening') else 'No'}")
        lines.append(f"  Wake Word Enabled: {'Yes' if status.get('wake_word_enabled') else 'No'}")
        
        # Test microphone if available
        if status.get('stt_available'):
            lines.append("\nTesting microphone...")
            working, msg = voice.test_microphone()
            lines.append(f"  Result: {msg}")
        
        return {'text': '\n'.join(lines), 'type': 'agent_response', 'timestamp': time.time()}

    def start(self):
        """Start the agent."""
        logger.info("Agent online and ready to think")

    def stop(self):
        """Stop the agent."""
        logger.info("Agent stopped")
