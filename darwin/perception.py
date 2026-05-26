"""Perception — Darwin 感知外部环境和主人沟通

Darwin 通过感知模块理解外部世界：
- 与主人的对话
- 外部环境变化
- 系统状态变化
- 主人偏好和行为模式
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PerceptionType(Enum):
    """感知类型"""
    # 与主人相关
    MASTER_MESSAGE = "master_message"      # 主人的直接消息
    MASTER_FEEDBACK = "master_feedback"    # 主人的反馈（语气、情绪）
    MASTER_PREFERENCE = "master_preference" # 主人的偏好（喜欢简洁/详细）
    MASTER_REQUEST = "master_request"       # 主人的请求（想做某事）

    # 环境相关
    ENVIRONMENT_CHANGE = "environment_change"  # 环境变化（网络、硬件）
    SYSTEM_STATUS = "system_status"           # 系统状态（性能、错误）
    TOOL_AVAILABLE = "tool_available"         # 新工具可用
    EXTERNAL_EVENT = "external_event"          # 外部事件（时间、日期）

    # 自我相关
    SELF_ABILITY = "self_ability"           # 自我能力评估
    SELF_GOAL = "self_goal"                  # 自我目标状态
    SELF_ERROR = "self_error"                # 自我错误/失败

    # 进化相关
    EVOLUTION_RESULT = "evolution_result"   # 进化结果
    LEARNING_RESULT = "learning_result"     # 学习结果


@dataclass
class Perception:
    """一次感知事件"""
    id: str
    type: PerceptionType
    content: str                          # 感知内容
    source: str                          # 来源（master/system/self/environment）
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict = field(default_factory=dict)  # 额外上下文
    importance: float = 1.0             # 重要性 0-1
    processed: bool = False             # 是否已处理


@dataclass
class PerceptionMemory:
    """感知记忆库"""
    perceptions: list[Perception] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

    def add(self, perception: Perception):
        """添加感知"""
        self.perceptions.append(perception)
        self.last_updated = datetime.now()

    def get_recent(self, limit: int = 50) -> list[Perception]:
        """获取最近的感知"""
        sorted_perceptions = sorted(
            self.perceptions,
            key=lambda p: p.timestamp,
            reverse=True
        )
        return sorted_perceptions[:limit]

    def get_by_type(self, perception_type: PerceptionType) -> list[Perception]:
        """按类型获取感知"""
        return [p for p in self.perceptions if p.type == perception_type]

    def get_unprocessed(self) -> list[Perception]:
        """获取未处理的感知"""
        return [p for p in self.perceptions if not p.processed]

    def mark_processed(self, perception_id: str):
        """标记为已处理"""
        for p in self.perceptions:
            if p.id == perception_id:
                p.processed = True


class PerceptionModule:
    """
    感知模块

    负责收集和存储 Darwin 的感知事件。
    感知是 Darwin 理解外部世界和主人的窗口。
    """

    MEMORY_FILE = "evolution/perception_memory.jsonl"

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root).resolve()
        self.memory_file = self.darwin_root / self.MEMORY_FILE
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory = self._load_memory()

    def perceive(self, perception_type: PerceptionType, content: str,
                source: str, context: dict = None, importance: float = 1.0) -> Perception:
        """
        记录一次感知

        Args:
            perception_type: 感知类型
            content: 感知内容
            source: 来源（master/system/self/environment）
            context: 额外上下文
            importance: 重要性 0-1

        Returns:
            Perception: 创建的感知对象
        """
        perception_id = f"perc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.memory.perceptions)}"

        perception = Perception(
            id=perception_id,
            type=perception_type,
            content=content,
            source=source,
            context=context or {},
            importance=importance,
        )

        self.memory.add(perception)
        self._save_perception(perception)

        logger.info(f"Perception recorded: [{perception_type.value}] {content[:50]}...")
        return perception

    def perceive_master_message(self, message: str, context: dict = None) -> Perception:
        """感知主人的消息"""
        return self.perceive(
            PerceptionType.MASTER_MESSAGE,
            message,
            source="master",
            context=context,
        )

    def perceive_master_feedback(self, feedback: str, sentiment: str = "neutral",
                                 context: dict = None) -> Perception:
        """感知主人的反馈"""
        return self.perceive(
            PerceptionType.MASTER_FEEDBACK,
            feedback,
            source="master",
            context={**(context or {}), "sentiment": sentiment},
        )

    def perceive_master_preference(self, preference: str, context: dict = None) -> Perception:
        """感知主人的偏好"""
        return self.perceive(
            PerceptionType.MASTER_PREFERENCE,
            preference,
            source="master",
            context=context,
        )

    def perceive_self_ability(self, ability: str, confidence: float = 1.0,
                             context: dict = None) -> Perception:
        """感知自我能力状态"""
        return self.perceive(
            PerceptionType.SELF_ABILITY,
            ability,
            source="self",
            importance=0.8,
            context={**(context or {}), "confidence": confidence},
        )

    def perceive_self_error(self, error: str, context: dict = None) -> Perception:
        """感知自我错误"""
        return self.perceive(
            PerceptionType.SELF_ERROR,
            error,
            source="self",
            importance=0.9,
            context=context,
        )

    def perceive_environment_change(self, change: str, context: dict = None) -> Perception:
        """感知环境变化"""
        return self.perceive(
            PerceptionType.ENVIRONMENT_CHANGE,
            change,
            source="environment",
            context=context,
        )

    def perceive_system_status(self, status: str, context: dict = None) -> Perception:
        """感知系统状态"""
        return self.perceive(
            PerceptionType.SYSTEM_STATUS,
            status,
            source="system",
            context=context,
        )

    def perceive_evolution_result(self, result: str, success: bool,
                                 context: dict = None) -> Perception:
        """感知进化结果"""
        return self.perceive(
            PerceptionType.EVOLUTION_RESULT,
            result,
            source="self",
            importance=0.9,
            context={**(context or {}), "success": success},
        )

    def get_context_for_analysis(self, time_window_hours: int = 24) -> dict:
        """
        获取分析用上下文

        收集最近一段时间内的感知事件，用于 LLM 分析。
        """
        recent = self.memory.get_recent(limit=100)
        now = datetime.now()

        # 过滤时间窗口
        window_perceptions = []
        for p in recent:
            age_hours = (now - p.timestamp).total_seconds() / 3600
            if age_hours <= time_window_hours:
                window_perceptions.append(p)

        # 分类整理
        by_type = {}
        for p in window_perceptions:
            type_name = p.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append({
                "content": p.content,
                "timestamp": p.timestamp.isoformat(),
                "importance": p.importance,
                "source": p.source,
            })

        # 未处理的感知
        unprocessed = self.memory.get_unprocessed()

        return {
            "time_window_hours": time_window_hours,
            "total_perceptions": len(window_perceptions),
            "unprocessed_count": len(unprocessed),
            "perceptions_by_type": by_type,
            "unprocessed": [
                {"id": p.id, "content": p.content[:100], "type": p.type.value}
                for p in unprocessed[:10]
            ],
            "recent_master_messages": [
                {"content": p.content[:200], "timestamp": p.timestamp.isoformat()}
                for p in window_perceptions
                if p.type == PerceptionType.MASTER_MESSAGE
            ][-5:],
        }

    def _load_memory(self) -> PerceptionMemory:
        """加载感知记忆"""
        memory = PerceptionMemory()

        if not self.memory_file.exists():
            return memory

        with open(self.memory_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    perception = Perception(
                        id=data["id"],
                        type=PerceptionType(data["type"]),
                        content=data["content"],
                        source=data["source"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        context=data.get("context", {}),
                        importance=data.get("importance", 1.0),
                        processed=data.get("processed", False),
                    )
                    memory.perceptions.append(perception)
                except Exception as e:
                    logger.warning(f"Failed to load perception: {e}")

        return memory

    def _save_perception(self, perception: Perception):
        """保存感知到文件"""
        data = {
            "id": perception.id,
            "type": perception.type.value,
            "content": perception.content,
            "source": perception.source,
            "timestamp": perception.timestamp.isoformat(),
            "context": perception.context,
            "importance": perception.importance,
            "processed": perception.processed,
        }

        with open(self.memory_file, "a") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")