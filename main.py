#!/usr/bin/env python3
"""
SOMS (Self-Organizing Master System)

An elite 7BRAIN-CORE autonomous voice assistant for system control and task execution.
Features 100% offline, private, local operation with advanced capabilities including
voice interaction, system control, hacking, teaching, coding, problem-solving, and more.

Author: Your Engineer
"""

import json
import logging
import os
import subprocess
import sys
import time
import threading
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('soms.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SOMS')

# Import core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from soms.agent import Agent
from soms.orchestrator import Orchestrator
from soms.sentinel import Sentinel
from soms.diagnostician import Diagnostician
from soms.architect import Architect
from soms.engineer import Engineer
from soms.auditor import Auditor
from soms.evolver import Evolver
from soms.voice import VoiceInterface
from soms.gui import GUI
from soms.tui import TUI
from soms.cli import run_cli
from soms.config_manager import ConfigManager
from soms.model_manager import ModelManager
from soms.improver import ImproverAgent
from soms.package_architect import PackageArchitect
from soms.memory import MemoryLayer
from soms.demonstrator import Demonstrator
from soms.llm_client import LLMClient
from soms.self_heal import SelfHealer
from soms.cleaner import Cleaner
from soms.growth import GrowthEngine
from soms.forecasting import TimesFMService

class SystemResources:
    """Track and manage system resources."""

    def __init__(self):
        self.boot_time = time.time()
        self.system_stats = {}

    def update(self):
        """Update system resource statistics."""
        try:
            import psutil
            self.system_stats = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'boot_time': self.boot_time
            }
        except ImportError:
            self.system_stats = {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'disk_percent': 0.0,
                'boot_time': self.boot_time
            }

    def get_uptime(self):
        """Get system uptime in hours."""
        return (time.time() - self.boot_time) / 3600

    def get_status(self):
        """Get formatted system status."""
        return {
            'uptime_hours': f"{self.get_uptime():.1f}",
            'cpu_usage': f"{self.system_stats.get('cpu_percent', 0):.1f}%",
            'memory_usage': f"{self.system_stats.get('memory_percent', 0):.1f}%",
            'disk_usage': f"{self.system_stats.get('disk_percent', 0):.1f}%"
        }

class SOMSSystem:
    """Main SOMS autonomous system controller with 7BRAIN-CORE architecture."""

    def __init__(self, use_tui=False):
        self.config = ConfigManager()
        self.resources = SystemResources()
        self.modules_initialized = False
        self.user_greeting_delivered = False
        self.welcome_text = ""
        self.mic_enabled = False
        self.is_running = False
        self.use_tui = use_tui

        # Initialize core brain modules
        self._initialize_brain_modules()

        # System state
        self.system_start_time = time.time()
        self.current_time = datetime.now()

    def _initialize_brain_modules(self):
        """Initialize all 7 brain modules."""
        self.sentinel = Sentinel(self.config)
        self.diagnostician = Diagnostician(self.config)
        self.architect = Architect(self.config)
        self.engineer = Engineer(self.config)
        self.auditor = Auditor(self.config)
        self.evolver = Evolver(self.config)
        self.orchestrator = Orchestrator(self.config, system_ref=self)
        self.agent = Agent(self)
        self.voice = VoiceInterface(self.config)
        self.model_manager = ModelManager(self.config)
        self.llm = LLMClient(self.config)
        self.improver = ImproverAgent(self.config, system_ref=self)
        self.package_architect = PackageArchitect(self.config)
        self.memory = MemoryLayer(self.config)
        self.demonstrator = Demonstrator(self)
        self.self_healer = SelfHealer(self)
        self.cleaner = Cleaner(self)
        self.grower = GrowthEngine(self)
        self.timesfm = TimesFMService()
        if self.use_tui:
            self.gui = TUI(self.config, self)
        else:
            self.gui = GUI(self.config, self)

    def initialize_system(self):
        """Initialize the complete SOMS system."""
        logger.info("Starting SOMS System Initialization")

        self._setup_system_environment()
        self._setup_audio_system()

        self.sentinel.start()
        self.diagnostician.start()
        self.architect.start()
        self.engineer.start()
        self.auditor.start()
        self.evolver.start()
        self.orchestrator.start()
        self.agent.start()
        self.voice.start()
        self.improver.start()
        self.package_architect.start()
        self.memory.start()
        self.self_healer.start()
        self.cleaner.start()
        self.grower.start()

        self.modules_initialized = True
        self.is_running = True

        logger.info("SOMS system initialization complete - Ready for voice interaction")
        self._deliver_welcome_message()

    def initialize_cli(self):
        """Headless initialization for CLI use — boots all brain modules but
        does NOT start voice capture or the GUI, so it runs on servers / over
        SSH without a display or microphone."""
        logger.info("Starting SOMS (headless CLI mode)")

        self._setup_system_environment()

        self.sentinel.start()
        self.diagnostician.start()
        self.architect.start()
        self.engineer.start()
        self.auditor.start()
        self.evolver.start()
        self.orchestrator.start()
        self.agent.start()
        self.improver.start()
        self.package_architect.start()
        self.memory.start()
        self.self_healer.start()
        self.cleaner.start()
        self.grower.start()

        self.modules_initialized = True
        self.is_running = True
        logger.info("SOMS headless initialization complete - CLI ready")

    def _setup_system_environment(self):
        """Setup system environment and configuration."""
        logger.info(f"System: {os.name}")
        logger.info(f"Python: {sys.version.split()[0]}")

        self.config.set('system', 'boot_time', value=self.system_start_time)
        self.config.set('system', 'initialized', value=True)

    def _setup_audio_system(self):
        """Setup audio system for voice input/output."""
        try:
            subprocess.run(['amixer', 'sset', 'Master', '100%'], check=False)
            self.mic_enabled = True
            logger.info("Audio volume set to 100%")
        except Exception:
            self.mic_enabled = False
            logger.warning("Audio setup failed")

    def _get_greeting_text(self):
        user = self.config.get_random_honorific()
        now = datetime.now()
        hour = now.hour
        if hour < 12:
            tod = "GOOD MORNING"
        elif hour < 17:
            tod = "GOOD AFTERNOON"
        else:
            tod = "GOOD EVENING"
        return f"SYSTEM ONLINE! {tod} {user}, SOMS AT YOUR SERVICE."

    def _deliver_welcome_message(self):
        """Deliver personalized welcome message with time-of-day greeting."""
        greeting = self._get_greeting_text()
        self.welcome_text = greeting
        self.voice.speak(greeting, mark_welcome=True)
        self.user_greeting_delivered = True

    def run(self):
        """Run the main SOMS system with GUI or TUI."""
        self.initialize_system()

        # Start system logic in background thread
        system_thread = threading.Thread(target=self._system_loop, daemon=True)
        system_thread.start()

        # Auto-start voice listening
        if hasattr(self, 'voice') and self.voice:
            logger.info("Setting up voice callback...")
            self.voice.set_command_callback(self._on_voice_command)
            logger.info("Starting voice listening...")
            self.voice.start_listening()
            logger.info(f"Voice listening status: {self.voice.is_listening}")
        else:
            logger.warning("Voice module not available!")

        mode = "TUI" if self.use_tui else "GUI"
        try:
            logger.info(f"SOMS system running - starting {mode}")
            self.gui.start()

        except KeyboardInterrupt:
            logger.info("SOMS shutdown requested by user")
            self.shutdown()

        except Exception as e:
            logger.error(f"SOMS system error: {e}")
            self.shutdown()

    def _system_loop(self):
        """System maintenance loop running in background."""
        while self.is_running:
            try:
                self.resources.update()
                self._periodic_maintenance()

                if self.evolver.get_evolution_readiness():
                    logger.info("Starting system evolution cycle")
                    self.evolver.evolve()

                # Ensure reasoning engine stays online
                if hasattr(self, 'llm') and self.llm and not self.llm.available():
                    logger.warning("LLM client unavailable — attempting reconnect")
                    self.llm.reconnect()

                time.sleep(30)
            except Exception as e:
                logger.error(f"System loop error: {e}")
                time.sleep(5)

    def _periodic_maintenance(self):
        """Run periodic system maintenance tasks."""
        if self.diagnostician.is_running:
            self.diagnostician.update(self)

    def _on_voice_command(self, text):
        """Process a voice command and speak the response."""
        if not text:
            return
        logger.info(f"Voice command: {text}")
        try:
            response = self.execute_command(text)
            if response and 'orchestrator' in response:
                if response['orchestrator'].get('restart'):
                    self.voice.speak("Restarting SOMS.")
                    self.restart()
                    return
                if response['orchestrator'].get('shutdown'):
                    self.voice.speak("Shutting down SOMS. Goodbye!")
                    self.shutdown()
                    return
                reply = response['orchestrator'].get('text', 'Command processed')
            else:
                reply = 'Command processed'
            self.voice.speak(reply)
        except Exception as e:
            logger.error(f"Voice command error: {e}")
            self.voice.speak("I encountered an error processing your request.")

    def process_voice_input(self, audio_data):
        """Process voice input and generate responses."""
        if not self.modules_initialized:
            return self._get_startup_response()

        try:
            response = self.orchestrator.process_voice_command(audio_data)

            if response and 'text' in response:
                self.voice.speak(response['text'])

            return response

        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            self.voice.speak("I encountered an error processing your request.")
            return None

    def _get_startup_response(self):
        """Get startup response if system not fully initialized."""
        if not self.user_greeting_delivered:
            self._deliver_welcome_message()

        return {
            'text': 'SOMS system ready. How can I help you today?',
            'type': 'system_status',
            'timestamp': time.time()
        }

    def shutdown(self):
        """Gracefully shutdown the SOMS system."""
        logger.info("Initiating SOMS system shutdown")

        if hasattr(self, 'voice'):
            self.voice.speak("SOMS system shutting down. Goodbye!")

        self._stop_modules()
        self.is_running = False
        self._save_system_state()

        logger.info("SOMS system shutdown complete")
        os._exit(0)

    def restart(self):
        """Restart the SOMS system."""
        logger.info("Initiating SOMS system restart")

        self._stop_modules()
        self._save_system_state()

        logger.info("SOMS system restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _stop_modules(self):
        """Stop all brain modules - includes all 7 core + support modules."""
        modules = [
            self.sentinel, self.diagnostician, self.architect, self.engineer,
            self.auditor, self.evolver, self.orchestrator, self.agent, self.voice,
            self.improver, self.package_architect, self.memory, self.demonstrator,
            self.self_healer, self.cleaner, self.grower
        ]
        for module in modules:
            try:
                if module and hasattr(module, 'stop'):
                    module.stop()
            except Exception as e:
                logger.warning(f"Error stopping module {module.__class__.__name__ if module else 'unknown'}: {e}")

    def _save_system_state(self):
        """Save current system state to persistent storage."""
        state = {
            'timestamp': time.time(),
            'system_start_time': self.system_start_time,
            'current_time': self.current_time.isoformat(),
            'modules_initialized': self.modules_initialized,
            'user_greeting_delivered': self.user_greeting_delivered,
            'mic_enabled': self.mic_enabled,
            'is_running': self.is_running
        }

        try:
            with open('soms_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            logger.info("SOMS system state saved")
        except Exception as e:
            logger.error(f"Failed to save system state: {e}")

    def get_system_status(self):
        """Get comprehensive system status for diagnostics."""
        health = self.sentinel.check_system_health() if hasattr(self.sentinel, 'check_system_health') else {'status': 'unknown'}

        return {
            'timestamp': time.time(),
            'system_info': self._get_system_info(),
            'resources': self.resources.get_status(),
            'brain_modules': {
                'sentinel': self.sentinel.is_running if hasattr(self.sentinel, 'is_running') else 'unknown',
                'orchestrator': self.orchestrator.is_active() if hasattr(self.orchestrator, 'is_active') else 'unknown',
                'agent': self.agent.is_running if hasattr(self.agent, 'is_running') else 'unknown',
                'diagnostician': self.diagnostician.is_running if hasattr(self.diagnostician, 'is_running') else 'unknown'
            },
            'voice_interface': {
                'enabled': self.voice.is_voice_enabled() if hasattr(self.voice, 'is_voice_enabled') else False,
                'listening': getattr(self.voice, 'is_listening', False)
            },
            'system_health': {
                'system_healthy': health.get('status') == 'healthy',
                'diagnostic_status': 'healthy'
            },
            'user_honorific': self.config.get_user('current'),
            'evolution_ready': self.evolver.get_evolution_readiness() if hasattr(self.evolver, 'get_evolution_readiness') else False
        }

    def _get_system_info(self):
        """Get basic system information."""
        return {
            'platform': 'Linux',
            'release': 'unknown',
            'machine': 'unknown',
            'python_version': sys.version.split()[0],
            'boot_time': datetime.fromtimestamp(self.resources.boot_time).isoformat(),
            'soms_version': '1.0.0',
            'brain_modules': 7
        }

    def execute_command(self, command, progress_callback=None):
        """Execute a direct command (used by GUI, CLI and testing).

        Both the orchestrator and the agent see the command. The orchestrator
        handles canonical slash-commands; the agent is the broader router
        (skills, LLM chat, argument-bearing commands like `/plan <goal>`).
        When the orchestrator has no useful answer we surface the agent's.
        """
        if progress_callback:
            progress_callback("Thinking...")
        response = self.orchestrator.process_voice_command(command, progress_callback=progress_callback)

        if progress_callback:
            progress_callback("Reflecting...")
        agent_response = self.agent.process_request(command)

        if progress_callback:
            progress_callback("Done.")

        orch_text = (response or {}).get('text') or ''
        agent_text = (agent_response or {}).get('text') or ''
        # If the orchestrator didn't recognize the command but the agent did,
        # promote the agent's answer so it isn't shadowed by "unknown command".
        if (not orch_text or 'not a recognized command' in orch_text.lower()) and agent_text:
            response = dict(response or {})
            response['text'] = agent_text

        return {
            'orchestrator': response,
            'agent': agent_response
        }

def main():
    """Main entry point for SOMS system."""
    use_tui = '--tui' in sys.argv
    use_cli = '--cli' in sys.argv
    no_wake = '--no-wake' in sys.argv
    force_gui = '--gui' in sys.argv
    if force_gui:
        use_tui = False
        use_cli = False

    # Anything that isn't a known flag becomes a one-shot CLI query.
    flags = {'--tui', '--cli', '--no-wake', '--gui'}
    query = ' '.join(a for a in sys.argv[1:] if a not in flags)

    print("Starting SOMS: Self-Organizing Master System")
    print("Version 1.0.0 - 7BRAIN-CORE Architecture")
    print("=" * 60)
    print("\nSystem Features:")
    print("  ✓ 100% private, local, and offline operation")
    print("  ✓ Voice interaction (STT/TTS)")
    print("  ✓ 7 specialized brain modules:")
    print("    - Sentinel: System monitoring and telemetry")
    print("    - Diagnostician: System analysis and diagnostics")
    print("    - Architect: Strategic planning")
    print("    - Engineer: System execution and control")
    print("    - Auditor: Validation and security")
    print("    - Evolver: Learning and evolution")
    print("    - Orchestrator: Command processing")
    print("    - Agent: User interaction")
    print("\nAdvanced Capabilities:")
    print("  ✓ Hacking and security analysis")
    print("  ✓ Teaching and coding assistance")
    print("  ✓ Problem-solving and mathematics")
    print("  ✓ Weather checks and forecasts")
    print("  ✓ YouTube control and media management")
    print("  ✓ Camera operations and photo capture")
    print("\nSystem is initialized and ready for voice commands.\n")
    print("Available commands (start with /):")
    print("  /info - System status and diagnostics")
    print("  /system check - Full health check")
    print("  /update - System improvement")
    print("  /model - List and select AI models")
    print("  /soms - SOMS system information")
    print("  /improve - Self-improvement & capabilities")
    print("  /wifite - Wireless auditing tool help")
    print("  /restart - Restart SOMS")
    print("  /shutdown - Graceful shutdown")
    print("  /learn - Acquire new skills")
    print("  /help - Show this help message")
    print("  --tui    - Launch terminal UI instead of desktop GUI")
    print("  --cli    - Launch Gemini-style CLI interface")
    print("  --no-wake - Disable wake word detection (always listening)")
    print("\nSOMS system ready. How can I help you today?")

    try:
        system = SOMSSystem(use_tui=use_tui)
        if no_wake and hasattr(system, 'voice') and system.voice:
            system.voice.wake_word_enabled = False

        if use_cli:
            system.initialize_cli()
            run_cli(system, query=query if query else None)
        else:
            system.run()
    except Exception as e:
        logger.error(f"SOMS startup failed: {e}")
        print(f"SOMS startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
