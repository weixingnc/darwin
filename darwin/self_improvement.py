"""
SelfImprovement — Darwin 自我完善的接口和基础设施

定义自我完善的统一接口，以及能力差距检测、技能学习、
沟通渠道学习、跨设备迁移等模块。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from .perception import PerceptionModule, PerceptionType

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    """改进类型"""
    ABILITY_GAP = "ability_gap"      # 能力差距
    SKILL_ACQUISITION = "skill_acquisition"  # 技能习得
    CHANNEL_ACQUISITION = "channel_acquisition"  # 渠道扩展
    KNOWLEDGE_GAP = "knowledge_gap"  # 知识差距
    MIGRATION = "migration"          # 设备迁移


@dataclass
class ImprovementPlan:
    """自我完善计划"""
    id: str
    improvement_type: ImprovementType
    description: str
    target: str                    # 目标（skill名/渠道名/设备信息）
    steps: list[str] = field(default_factory=list)
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"         # pending/in_progress/completed/failed


@dataclass
class AbilityGap:
    """能力差距"""
    ability_name: str              # 能力名称
    current_level: float            # 当前水平 0-1
    required_level: float           # 需要的水平 0-1
    evidence: list[str] = field(default_factory=list)  # 证据
    suggested_improvement: str = ""


class SelfImprovementModule(ABC):
    """
    自我完善模块基类

    所有自我完善能力都继承这个接口。
    """

    def __init__(self, darwin_root: Path, perception: PerceptionModule):
        self.darwin_root = Path(darwin_root).resolve()
        self.perception = perception

    @abstractmethod
    def detect(self) -> list[AbilityGap]:
        """检测改进机会"""
        pass

    @abstractmethod
    def plan_improvement(self, gap: AbilityGap) -> ImprovementPlan | None:
        """制定改进计划"""
        pass

    @abstractmethod
    def execute(self, plan: ImprovementPlan) -> bool:
        """执行改进计划"""
        pass

    def log_improvement(self, improvement_type: ImprovementType,
                       description: str, success: bool):
        """记录改进结果到感知"""
        self.perception.perceive(
            PerceptionType.LEARNING_RESULT,
            f"{improvement_type.value}: {description}",
            source="self",
            context={"success": success, "type": improvement_type.value},
            importance=0.9,
        )