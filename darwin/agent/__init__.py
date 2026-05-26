"""Agent — Darwin 的运行时，基于 Hermes Agent Engine

Darwin 的 Agent 模块封装了 Hermes AIAgent，
提供 Darwin 特有的对话管理和工具集。
"""

from .runtime import DarwinRuntime
from .introspector import Introspector, DarwinSelfImage, SoulSnapshot, EvolutionRecord

__all__ = ["DarwinRuntime", "Introspector", "DarwinSelfImage", "SoulSnapshot", "EvolutionRecord"]