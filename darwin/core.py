"""Core — Darwin 核心循环

整合感知 → 分析 → 进化 的完整流程。
这是 Darwin 的主循环，持续运行，感知环境，分析机会，执行进化。
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from .perception import PerceptionModule, PerceptionType
from .analyzer import AnalyzerModule, AnalysisResult
from .evolution import EvolutionEngine
from .self_improvement import ImprovementType
from .ability_gap_detector import AbilityGapDetector, detect_ability_gaps
from .skill_learner import SkillLearner, ChannelLearner, MigrationProtocol
from .knowledge_manager import KnowledgeManager, SoulEvolver, BodyControl

logger = logging.getLogger(__name__)


class DarwinState(Enum):
    """Darwin 状态"""
    IDLE = "idle"           # 空闲，等待
    PERCEIVING = "perceiving"  # 感知中
    ANALYZING = "analyzing"   # 分析中
    EVOLVING = "evolving"     # 进化中
    WAITING = "waiting"       # 等待主人
    ERROR = "error"           # 错误


@dataclass
class DarwinCore:
    """
    Darwin 核心循环

    整合所有模块，协调感知、分析、进化流程。
    可以作为后台线程运行，也可以手动调用。
    """

    def __init__(self, darwin_root: Path, config: dict = None):
        self.darwin_root = Path(darwin_root).resolve()
        self.config = config or {}

        # 初始化模块
        self.perception = PerceptionModule(self.darwin_root)
        self.analyzer = AnalyzerModule(self.darwin_root)
        self.evolution = EvolutionEngine(self.darwin_root)
        # 自我完善模块
        self.ability_detector = AbilityGapDetector(self.darwin_root, self.perception)
        self.skill_learner = SkillLearner(self.darwin_root, self.perception, self.evolution)
        self.channel_learner = ChannelLearner(self.darwin_root, self.perception, self.evolution)
        self.knowledge_manager = KnowledgeManager(self.darwin_root, self.perception)
        self.soul_evolver = SoulEvolver(self.darwin_root, self.perception, self.evolution)
        self.body_control = BodyControl(self.darwin_root, self.perception)

        # 状态
        self.state = DarwinState.IDLE
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # 配置
        self.analyze_interval = self.config.get("analyze_interval", 300)  # 分析间隔（秒）
        self.auto_evolve = self.config.get("auto_evolve", True)  # 自动进化

    # ──────────────────────────────────────────
    # 感知接口（供外部调用）
    # ──────────────────────────────────────────

    def on_master_message(self, message: str):
        """当主人发来消息时调用"""
        self.perception.perceive_master_message(message)

        # 如果启用了自动分析，立即分析
        if self.auto_evolve:
            self.analyze_and_evolve()

    def on_master_request(self, request: str):
        """当主人提出明确需求时调用（如"我想学数据分析"）"""
        self.perception.perceive(
            PerceptionType.MASTER_REQUEST,
            request,
            source="master",
            context={},
            importance=0.9,
        )

        # 尝试学习新技能
        if self.auto_evolve:
            plan = self.skill_learner.learn_from_master_request(request)
            if plan:
                logger.info(f"Master request detected: {request}, creating improvement plan")
                # 执行改进计划
                self.skill_learner.execute(plan)

    def on_master_feedback(self, feedback: str, sentiment: str = "neutral"):
        """当主人给出反馈时调用"""
        self.perception.perceive_master_feedback(feedback, sentiment)

        # 如果负面反馈，优先处理
        if sentiment in ("negative", "frustrated"):
            logger.warning(f"Negative feedback from master: {feedback}")
            if self.auto_evolve:
                self.analyze_and_evolve(priority="high")

    def on_self_error(self, error: str, context: dict = None):
        """当 Darwin 遇到错误时调用"""
        self.perception.perceive_self_error(error, context)

        if self.auto_evolve:
            self.analyze_and_evolve(priority="high")

    def on_system_status(self, status: str, context: dict = None):
        """当系统状态变化时调用"""
        self.perception.perceive_system_status(status, context)

    def on_evolution_complete(self, success: bool, result_message: str):
        """当进化完成时调用"""
        self.perception.perceive_evolution_result(result_message, success)

    # ──────────────────────────────────────────
    # 分析和进化
    # ──────────────────────────────────────────

    def analyze_and_evolve(self, priority: str = "normal") -> dict:
        """
        分析感知并执行进化

        Args:
            priority: 优先级（normal/high）

        Returns:
            dict: 执行结果
        """
        logger.info(f"Starting analyze_and_evolve (priority={priority})")
        self.state = DarwinState.ANALYZING

        try:
            # 1. 获取感知上下文
            context = self.perception.get_context_for_analysis(
                time_window_hours=24 if priority == "normal" else 168  # 24h 或 1 周
            )

            if context["total_perceptions"] == 0:
                logger.info("No perceptions to analyze")
                self.state = DarwinState.IDLE
                return {"success": True, "action": "no_perceptions"}

            # 2. 分析
            analyses = self.analyzer.analyze(context)

            if not analyses:
                logger.info("No actionable analyses found")
                self.state = DarwinState.IDLE
                return {"success": True, "action": "no_analysis"}

            # 3. 按优先级排序，选择最高优先级的分析
            analyses.sort(key=lambda a: (
                {"high": 1, "normal": 0}[priority],
                -a.confidence
            ), reverse=True)

            selected = analyses[0]
            logger.info(f"Selected analysis: {selected.result.value} — {selected.description}")

            # 4. 生成进化计划
            description, changes = self.analyzer.generate_evolution_plan(selected)

            if not changes:
                logger.info("No changes suggested, skipping evolution")
                self.state = DarwinState.IDLE
                return {"success": True, "action": "no_changes"}

            # 5. 创建并执行进化计划
            plan = self.evolution.create_plan(description, changes)
            self.state = DarwinState.EVOLVING

            result = self.evolution.execute(plan)

            # 6. 记录进化结果
            self.on_evolution_complete(result.success, result.message)

            final_state = DarwinState.IDLE if result.success else DarwinState.ERROR
            self.state = final_state

            return {
                "success": result.success,
                "plan_id": result.plan_id,
                "message": result.message,
                "phase_reached": result.phase_reached.value,
                "analysis": {
                    "result": selected.result.value,
                    "description": selected.description,
                    "confidence": selected.confidence,
                }
            }

        except Exception as e:
            logger.error(f"Error in analyze_and_evolve: {e}")
            self.state = DarwinState.ERROR
            return {
                "success": False,
                "error": str(e)
            }

    def run_analysis_cycle(self) -> dict:
        """
        运行一次分析周期（无进化）

        适用于定期检查，不需要立即进化。
        """
        logger.info("Running analysis cycle")
        self.state = DarwinState.ANALYZING

        try:
            context = self.perception.get_context_for_analysis(time_window_hours=24)
            analyses = self.analyzer.analyze(context)

            self.state = DarwinState.IDLE

            return {
                "success": True,
                "total_perceptions": context["total_perceptions"],
                "analyses_count": len(analyses),
                "analyses": [
                    {
                        "result": a.result.value,
                        "description": a.description,
                        "confidence": a.confidence,
                        "changes": a.suggested_changes,
                    }
                    for a in analyses
                ]
            }

        except Exception as e:
            logger.error(f"Error in run_analysis_cycle: {e}")
            self.state = DarwinState.ERROR
            return {"success": False, "error": str(e)}

    # ──────────────────────────────────────────
    # 后台运行
    # ──────────────────────────────────────────

    def start(self):
        """启动 Darwin 核心循环（后台线程）"""
        if self.running:
            logger.warning("Darwin core already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Darwin core started in background")

    def stop(self):
        """停止 Darwin 核心循环"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.state = DarwinState.IDLE
        logger.info("Darwin core stopped")

    def _run_loop(self):
        """后台运行循环"""
        logger.info("Darwin core loop started")

        while self.running:
            try:
                if self.auto_evolve:
                    # 定期分析并可能进化
                    result = self.run_analysis_cycle()

                    if result.get("analyses_count", 0) > 0:
                        analyses = result.get("analyses", [])
                        if analyses:
                            logger.info(
                                f"Analysis cycle found {len(analyses)} items, "
                                f"top priority: {analyses[0]['description']}"
                            )
                else:
                    # 非自动模式，只是等待
                    time.sleep(self.analyze_interval)

                # 睡眠间隔
                time.sleep(self.analyze_interval)

            except Exception as e:
                logger.error(f"Error in Darwin core loop: {e}")
                time.sleep(60)  # 出错时等待 1 分钟再试

        logger.info("Darwin core loop ended")

    # ──────────────────────────────────────────
    # 状态和诊断
    # ──────────────────────────────────────────

    def get_status(self) -> dict:
        """获取 Darwin 状态"""
        return {
            "state": self.state.value,
            "running": self.running,
            "auto_evolve": self.auto_evolve,
            "analyze_interval": self.analyze_interval,
            "perception_count": len(self.perception.memory.perceptions),
            "unprocessed_perceptions": len(self.perception.memory.get_unprocessed()),
        }

    def get_full_context(self) -> dict:
        """获取完整上下文（用于分析）"""
        return {
            "status": self.get_status(),
            "perception_context": self.perception.get_context_for_analysis(),
            "evolution_status": self.evolution.get_status(),
            "checkpoints": self.evolution.list_checkpoints()[:5],
        }