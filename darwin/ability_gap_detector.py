"""
AbilityGapDetector — Darwin 能力差距检测

自动发现 Darwin 当前能力与主人需求之间的差距，
生成改进计划并触发学习流程。
"""

import logging
from pathlib import Path
from typing import Optional

from .perception import PerceptionModule, PerceptionType
from .self_improvement import SelfImprovementModule, AbilityGap, ImprovementPlan, ImprovementType

logger = logging.getLogger(__name__)


# 已知能力列表（未来可以从 SkillBuilder 动态获取）
KNOWN_ABILITIES = [
    {"name": "conversation", "description": "对话交流", "keywords": ["聊天", "对话", "说话", "聊聊"]},
    {"name": "coding", "description": "编程", "keywords": ["代码", "编程", "程序", "写代码", "python", "java"]},
    {"name": "data_analysis", "description": "数据分析", "keywords": ["分析", "数据", "统计", "图表"]},
    {"name": "writing", "description": "写作", "keywords": ["写", "文章", "文案", "内容创作"]},
    {"name": "research", "description": "研究搜索", "keywords": ["搜索", "研究", "查找", "查询"]},
    {"name": "image_generation", "description": "图像生成", "keywords": ["画", "图", "生成图片", "图像"]},
    {"name": "video_generation", "description": "视频生成", "keywords": ["视频", "生成视频"]},
    {"name": "music_generation", "description": "音乐生成", "keywords": ["音乐", "歌曲", "作曲"]},
    {"name": "ocr", "description": "文字识别", "keywords": ["识别", "OCR", "文字识别", "扫描"]},
    {"name": "translation", "description": "翻译", "keywords": ["翻译", "译"]},
    {"name": "knowledge_management", "description": "知识管理", "keywords": ["笔记", "知识", "整理", "记忆"]},
    {"name": "scheduling", "description": "日程管理", "keywords": ["日程", "日历", "安排", "提醒"]},
    {"name": "email", "description": "邮件处理", "keywords": ["邮件", "email", "发邮件"]},
    {"name": "feishu", "description": "飞书通信", "keywords": ["飞书", "lark"]},
    {"name": "dingtalk", "description": "钉钉通信", "keywords": ["钉钉", "dingtalk"]},
    {"name": "telegram", "description": "Telegram通信", "keywords": ["telegram", "TG"]},
]


class AbilityGapDetector(SelfImprovementModule):
    """
    能力差距检测器

    分析主人消息和反馈，检测当前能力是否满足需求，
    识别能力差距并生成改进计划。
    """

    def __init__(self, darwin_root: Path, perception: PerceptionModule):
        super().__init__(darwin_root, perception)
        self.known_abilities = KNOWN_ABILITIES
        # 动态加载技能列表
        self._load_skills()

    def _load_skills(self):
        """从 skills 目录加载已有技能"""
        skills_dir = self.darwin_root / "skills"
        if skills_dir.exists():
            skill_names = []
            for item in skills_dir.iterdir():
                if item.is_dir() or item.suffix == ".md":
                    skill_names.append(item.stem)
            logger.info(f"Loaded {len(skill_names)} existing skills: {skill_names}")

    def detect(self) -> list[AbilityGap]:
        """
        检测能力差距

        分析最近的主人消息和反馈，识别未满足的需求。
        """
        gaps = []

        # 获取最近的感知
        context = self.perception.get_context_for_analysis(time_window_hours=168)  # 1 周
        recent_messages = context.get("recent_master_messages", [])

        if not recent_messages:
            logger.info("No recent messages to analyze for ability gaps")
            return gaps

        # 分析每个消息
        all_content = " ".join([m["content"] for m in recent_messages])

        for ability in self.known_abilities:
            # 检查是否有相关关键词
            keywords = ability["keywords"]
            matched = [kw for kw in keywords if kw.lower() in all_content.lower()]

            if matched:
                # 检查 Darwin 是否已有这个能力
                if not self._has_ability(ability["name"]):
                    # 能力缺失
                    gap = AbilityGap(
                        ability_name=ability["name"],
                        current_level=0.0,
                        required_level=0.7,
                        evidence=[f"主人在消息中提到: {', '.join(matched)}"],
                        suggested_improvement=f"学习 {ability['description']} 相关技能",
                    )
                    gaps.append(gap)
                    logger.info(f"Ability gap detected: {ability['name']}")

                elif self._confidence_low(ability["name"], recent_messages):
                    # 能力置信度低
                    gap = AbilityGap(
                        ability_name=ability["name"],
                        current_level=0.4,
                        required_level=0.7,
                        evidence=[f"主人重复提到相关话题: {', '.join(matched)}"],
                        suggested_improvement=f"提升 {ability['description']} 熟练度",
                    )
                    gaps.append(gap)

        return gaps

    def _has_ability(self, ability_name: str) -> bool:
        """检查是否有某能力（通过检查 skill 是否存在）"""
        # 检查对应 skill 是否存在
        skills_dir = self.darwin_root / "skills"
        skill_file = skills_dir / f"{ability_name}.md"

        # 简化：认为只要有对应 skill 文件就算有能力
        return skill_file.exists()

    def _confidence_low(self, ability_name: str, messages: list[dict]) -> bool:
        """
        检查能力置信度是否低

        如果主人在短时间内多次提到相关话题，说明置信度低。
        """
        # 简化：如果消息中重复出现同一个能力相关关键词超过 2 次
        for ability in self.known_abilities:
            if ability["name"] == ability_name:
                keywords = ability["keywords"]
                count = sum(
                    1 for msg in messages
                    if any(kw.lower() in msg["content"].lower() for kw in keywords)
                )
                return count >= 3  # 超过 3 次认为置信度低

        return False

    def plan_improvement(self, gap: AbilityGap) -> ImprovementPlan | None:
        """制定改进计划"""
        if gap.ability_name == "dingtalk":
            # 钉钉学习计划
            return ImprovementPlan(
                id=f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                improvement_type=ImprovementType.CHANNEL_ACQUISITION,
                description=f"学习 {gap.ability_name} 能力",
                target=gap.ability_name,
                steps=[
                    "研究钉钉开放平台 API 文档",
                    "了解钉钉机器人配置流程",
                    "生成 DingTalk Channel Skill",
                    "沙箱测试连通性",
                    "晋升到 production",
                ],
                confidence=0.8,
            )

        elif gap.ability_name == "telegram":
            return ImprovementPlan(
                id=f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                improvement_type=ImprovementType.CHANNEL_ACQUISITION,
                description=f"学习 {gap.ability_name} 能力",
                target=gap.ability_name,
                steps=[
                    "研究 Telegram Bot API 文档",
                    "了解 Telegram Bot 配置流程",
                    "生成 Telegram Channel Skill",
                    "沙箱测试连通性",
                    "晋升到 production",
                ],
                confidence=0.8,
            )

        elif gap.ability_name == "data_analysis":
            return ImprovementPlan(
                id=f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                improvement_type=ImprovementType.SKILL_ACQUISITION,
                description=f"学习数据分析能力",
                target="data-analysis-skill",
                steps=[
                    "学习数据分析基本概念",
                    "生成 data-analysis-skill",
                    "沙箱测试",
                    "晋升到 production",
                ],
                confidence=0.7,
            )

        else:
            # 默认技能学习计划
            return ImprovementPlan(
                id=f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                improvement_type=ImprovementType.SKILL_ACQUISITION,
                description=f"学习 {gap.ability_name} 能力",
                target=f"{gap.ability_name}-skill",
                steps=[
                    f"研究 {gap.ability_name} 相关技能",
                    f"生成 {gap.ability_name}-skill",
                    "沙箱测试",
                    "晋升到 production",
                ],
                confidence=0.6,
            )

    def execute(self, plan: ImprovementPlan) -> bool:
        """执行改进计划"""
        logger.info(f"Executing improvement plan: {plan.id} — {plan.description}")

        # 这里调用 SkillBuilder 或 ChannelLearner 来执行
        # 简化版本：只记录日志

        success = True  # 实际执行需要更复杂的逻辑

        self.log_improvement(
            plan.improvement_type,
            plan.description,
            success,
        )

        return success


# 全局函数，方便调用
def detect_ability_gaps(darwin_root: Path, perception: PerceptionModule) -> list[AbilityGap]:
    """检测能力差距的快捷函数"""
    detector = AbilityGapDetector(darwin_root, perception)
    return detector.detect()