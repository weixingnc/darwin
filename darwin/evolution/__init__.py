"""Evolution — Darwin 的自我进化引擎"""

from .engine import EvolutionEngine, EvolutionPlan, EvolutionResult, EvolutionPhase
from .checkpointer import Checkpointer, Checkpoint
from .evaluator import Evaluator
from .committer import Committer
from .soul_editor import SoulEditor, SoulProposal, SoulChange, ConsistencyReport
from .skill_builder import SkillBuilder, SkillProposal, SkillSpec
from .auto_tuner import AutoTuner, RuntimeMetrics, ParameterAdjustment, TUNABLE_PARAMS
from .bug_fixer import BugFixer, BugReport, FixAttempt
from .sandbox_manager import SandboxManager, SandboxInfo
from .test_runner import TestRunner, TestResult
from .promoter import Promoter, PromotionResult

__all__ = [
    # Core
    "EvolutionEngine",
    "EvolutionPlan",
    "EvolutionResult",
    "EvolutionPhase",
    "Checkpointer",
    "Checkpoint",
    "Evaluator",
    "Committer",
    # Soul editing
    "SoulEditor",
    "SoulProposal",
    "SoulChange",
    "ConsistencyReport",
    # Skill building
    "SkillBuilder",
    "SkillProposal",
    "SkillSpec",
    # Auto tuning
    "AutoTuner",
    "RuntimeMetrics",
    "ParameterAdjustment",
    "TUNABLE_PARAMS",
    # Bug fixing
    "BugFixer",
    "BugReport",
    "FixAttempt",
    # Sandbox
    "SandboxManager",
    "SandboxInfo",
    "TestRunner",
    "TestResult",
    "Promoter",
    "PromotionResult",
]