"""Darwin — 数字生命体"""

__version__ = "0.1.0"
__author__ = "魏星"

from .soul import Soul

# 默认实例
SOUL = Soul()
from .evolution.engine import EvolutionEngine

__all__ = ["SOUL", "EvolutionEngine", "__version__"]