"""Evolution — Darwin 的自我进化引擎"""

from .engine import EvolutionEngine, EvolutionPlan, EvolutionResult, EvolutionPhase
from .checkpointer import Checkpointer, Checkpoint
from .evaluator import Evaluator
from .committer import Committer
from .soul_editor import SoulEditor, SoulProposal, SoulChange, ConsistencyReport
from .skill_builder import SkillBuilder, SkillProposal, SkillSpec

__all__ = [
    "EvolutionEngine",
    "EvolutionPlan",
    "EvolutionResult",
    "EvolutionPhase",
    "Checkpointer",
    "Checkpoint",
    "Evaluator",
    "Committer",
    "SoulEditor",
    "SoulProposal",
    "SoulChange",
    "ConsistencyReport",
    "SkillBuilder",
    "SkillProposal",
    "SkillSpec",
]