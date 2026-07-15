"""SOMS Core Package with 7BRAIN-CORE architecture"""

__version__ = "1.0.0"
__author__ = "SOMS Team"

from .agent import Agent
from .orchestrator import Orchestrator
from .sentinel import Sentinel
from .diagnostician import Diagnostician
from .architect import Architect
from .engineer import Engineer
from .auditor import Auditor
from .evolver import Evolver
from .voice import VoiceInterface
from .config_manager import ConfigManager
from .model_manager import ModelManager
from .persona import Persona
from .improver import ImproverAgent
from .package_architect import PackageArchitect
from .memory import MemoryLayer
from .cli import SOMSCLI
from .cleaner import Cleaner

__all__ = [
    'Agent', 'Orchestrator', 'Sentinel', 'Diagnostician', 'Architect',
    'Engineer', 'Auditor', 'Evolver', 'VoiceInterface', 'ConfigManager',
    'ModelManager', 'Persona', 'ImproverAgent', 'PackageArchitect', 'MemoryLayer',
    'SOMSCLI', 'Cleaner'
]
