"""Analyzer — Darwin 分析感知，生成进化计划

Darwin 分析感知记忆，识别问题和机会，
生成 EvolutionPlan 并触发进化流程。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AnalysisResult(Enum):
    """分析结果类型"""
    NO_ACTION_NEEDED = "no_action_needed"
    OPPORTUNITY_IDENTIFIED = "opportunity_identified"
    PROBLEM_IDENTIFIED = "problem_identified"
    PREFERENCE_LEARNED = "preference_learned"
    ABILITY_GAP = "ability_gap"
    GOAL_SET = "goal_set"


@dataclass
class Analysis:
    """分析结果"""
    id: str
    result: AnalysisResult
    description: str
    perception_ids: list[str] = field(default_factory=list)  # 关联的感知 ID
    suggested_changes: list[str] = field(default_factory=list)  # 建议的变更
    confidence: float = 0.5  # 置信度 0-1
    reasoning: str = ""  # 分析推理过程
    analyzed_at: datetime = field(default_factory=datetime.now)


class AnalyzerModule:
    """
    分析模块

    接收感知上下文，调用 LLM 分析，生成进化建议。
    """

    def __init__(self, darwin_root: Path, llm_provider=None):
        self.darwin_root = Path(darwin_root).resolve()
        self.llm_provider = llm_provider  # 可选：LLM provider

    def analyze(self, context: dict, min_confidence: float = 0.6) -> list[Analysis]:
        """
        分析感知上下文，生成分析结果

        Args:
            context: 感知模块提供的上下文
            min_confidence: 最小置信度阈值

        Returns:
            list[Analysis]: 分析结果列表
        """
        logger.info("Starting analysis of perception context")

        analyses = []

        # 分析 1: 检查未处理的感知
        unprocessed = context.get("unprocessed", [])
        if unprocessed:
            analysis = self._analyze_unprocessed(unprocessed)
            if analysis and analysis.confidence >= min_confidence:
                analyses.append(analysis)

        # 分析 2: 检查主人消息，寻找进化机会
        master_messages = context.get("recent_master_messages", [])
        if master_messages:
            analysis = self._analyze_master_messages(master_messages)
            if analysis and analysis.confidence >= min_confidence:
                analyses.append(analysis)

        # 分析 3: 检查系统状态，寻找问题
        status_perceptions = context.get("perceptions_by_type", {}).get("system_status", [])
        if status_perceptions:
            analysis = self._analyze_system_status(status_perceptions)
            if analysis and analysis.confidence >= min_confidence:
                analyses.append(analysis)

        # 分析 4: 检查自我能力，寻找差距
        ability_perceptions = context.get("perceptions_by_type", {}).get("self_ability", [])
        if ability_perceptions:
            analysis = self._analyze_ability_gaps(ability_perceptions)
            if analysis and analysis.confidence >= min_confidence:
                analyses.append(analysis)

        logger.info(f"Analysis complete: {len(analyses)} items identified")
        return analyses

    def _analyze_unprocessed(self, unprocessed: list[dict]) -> Optional[Analysis]:
        """分析未处理的感知"""
        if not unprocessed:
            return None

        descriptions = [p["content"] for p in unprocessed]
        combined = " | ".join(descriptions[:5])

        return Analysis(
            id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            result=AnalysisResult.OPPORTUNITY_IDENTIFIED,
            description=f"有 {len(unprocessed)} 个未处理的感知需要关注",
            perception_ids=[p["id"] for p in unprocessed],
            suggested_changes=[],
            confidence=0.7,
            reasoning=f"未处理感知: {combined}",
        )

    def _analyze_master_messages(self, messages: list[dict]) -> Optional[Analysis]:
        """分析主人消息，寻找进化机会"""
        if not messages:
            return None

        # 简单的关键词检测
        opportunity_keywords = [
            "我想学", "我想知道", "帮我", "能不能", "会吗",
            "如果", "将来", "以后", "应该", "学习"
        ]
        problem_keywords = [
            "不行", "坏了", "错误", "失败", "不好", "不对",
            "为什么", "问题", "bug", "error"
        ]

        all_content = " ".join([m["content"] for m in messages])

        opportunities = [kw for kw in opportunity_keywords if kw in all_content]
        problems = [kw for kw in problem_keywords if kw in all_content]

        if opportunities:
            return Analysis(
                id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                result=AnalysisResult.OPPORTUNITY_IDENTIFIED,
                description=f"主人表达了学习意愿: {', '.join(opportunities)}",
                suggested_changes=[f"学习新技能以满足主人需求（关键词: {', '.join(opportunities)}）"],
                confidence=0.8,
                reasoning=f"主人消息中检测到学习相关关键词: {opportunities}",
            )

        if problems:
            return Analysis(
                id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                result=AnalysisResult.PROBLEM_IDENTIFIED,
                description=f"主人遇到了问题: {', '.join(problems)}",
                suggested_changes=[f"解决主人遇到的问题（关键词: {', '.join(problems)}）"],
                confidence=0.9,
                reasoning=f"主人消息中检测到问题相关关键词: {problems}",
            )

        return None

    def _analyze_system_status(self, status_perceptions: list[dict]) -> Optional[Analysis]:
        """分析系统状态，寻找问题"""
        if not status_perceptions:
            return None

        error_keywords = ["error", "failed", "failed", "timeout", "slow", "crash"]

        errors = [
            p for p in status_perceptions
            if any(kw in p["content"].lower() for kw in error_keywords)
        ]

        if errors:
            return Analysis(
                id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                result=AnalysisResult.PROBLEM_IDENTIFIED,
                description=f"系统状态异常: {len(errors)} 个错误事件",
                suggested_changes=["检查系统状态，修复错误"],
                confidence=0.95,
                reasoning=f"检测到系统错误: {[e['content'] for e in errors[:3]]}",
            )

        return None

    def _analyze_ability_gaps(self, ability_perceptions: list[dict]) -> Optional[Analysis]:
        """分析自我能力，寻找差距"""
        if not ability_perceptions:
            return None

        # 查找低置信度的能力认知
        low_confidence = [
            p for p in ability_perceptions
            if p.get("context", {}).get("confidence", 1.0) < 0.7
        ]

        if low_confidence:
            return Analysis(
                id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                result=AnalysisResult.ABILITY_GAP,
                description=f"发现 {len(low_confidence)} 项能力置信度较低",
                suggested_changes=["提升低置信度能力的熟练度"],
                confidence=0.6,
                reasoning=f"低置信度能力: {[p['content'] for p in low_confidence[:3]]}",
            )

        return None

    def generate_evolution_plan(self, analysis: Analysis) -> tuple[str, list[str]]:
        """
        从分析结果生成进化计划

        Args:
            analysis: 分析结果

        Returns:
            tuple[str, list[str]]: (description, changes)
        """
        description = analysis.description
        changes = analysis.suggested_changes

        if not changes:
            # 默认变更建议
            if analysis.result == AnalysisResult.PROBLEM_IDENTIFIED:
                changes = [
                    "分析问题根因",
                    "提出解决方案",
                    "在沙箱中验证修复",
                ]
            elif analysis.result == AnalysisResult.OPPORTUNITY_IDENTIFIED:
                changes = [
                    "学习新技能",
                    "扩展能力范围",
                ]
            elif analysis.result == AnalysisResult.ABILITY_GAP:
                changes = [
                    "提升技能熟练度",
                    "增加相关 skill",
                ]

        return description, changes