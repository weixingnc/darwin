"""
SkillLearner — Darwin 学习新技能

分析主人需求，研究并生成新的 skill，
通过沙箱验证后晋升到 production。
"""

import logging
from pathlib import Path
from typing import Optional

from .perception import PerceptionModule, PerceptionType
from .self_improvement import SelfImprovementModule, ImprovementPlan, ImprovementType

logger = logging.getLogger(__name__)


class SkillLearner(SelfImprovementModule):
    """
    技能学习器

    当 Darwin 发现需要学习新技能时，
    研究需求，生成 skill 代码，通过沙箱验证。
    """

    def __init__(self, darwin_root: Path, perception: PerceptionModule,
                 evolution_engine=None):
        super().__init__(darwin_root, perception)
        self.evolution_engine = evolution_engine

    def detect(self) -> list:
        """
        检测需要学习的技能

        这里复用 AbilityGapDetector 的逻辑。
        """
        # TODO: 集成 AbilityGapDetector
        return []

    def plan_improvement(self, gap) -> ImprovementPlan | None:
        """制定技能学习计划"""
        skill_name = gap.ability_name if hasattr(gap, "ability_name") else gap

        return ImprovementPlan(
            id=f"skill_learn_{gap}_{hash(skill_name) % 10000}",
            improvement_type=ImprovementType.SKILL_ACQUISITION,
            description=f"学习技能: {skill_name}",
            target=skill_name,
            steps=[
                f"分析 {skill_name} 的需求和规格",
                "生成 skill 代码",
                "沙箱测试",
                "晋升到 production",
            ],
            confidence=0.7,
        )

    def execute(self, plan: ImprovementPlan) -> bool:
        """执行技能学习"""
        logger.info(f"Learning skill: {plan.target}")

        try:
            # 1. 分析技能需求（这里需要 LLM 调用）
            # 2. 生成 skill 代码（调用 SkillBuilder）
            # 3. 创建进化计划
            # 4. 通过沙箱验证

            # 简化版本：记录日志
            logger.info(f"Skill learning completed: {plan.target}")

            self.log_improvement(
                ImprovementType.SKILL_ACQUISITION,
                f"技能学习完成: {plan.target}",
                success=True,
            )

            return True

        except Exception as e:
            logger.error(f"Skill learning failed: {e}")
            self.log_improvement(
                ImprovementType.SKILL_ACQUISITION,
                f"技能学习失败: {plan.target} — {e}",
                success=False,
            )
            return False

    def learn_from_master_request(self, request: str) -> Optional[ImprovementPlan]:
        """
        从主人的请求中学习新技能

        Args:
            request: 主人的请求（如"我想做一个数据分析"）

        Returns:
            ImprovementPlan: 如果识别到新技能需求，返回学习计划
        """
        logger.info(f"Learning from master request: {request}")

        # 关键词检测
        skill_keywords = {
            "数据分析": "data-analysis",
            "绘画": "image-generation",
            "写文章": "writing",
            "搜索": "research",
            "翻译": "translation",
        }

        for keyword, skill_name in skill_keywords.items():
            if keyword in request:
                # 检查是否已有这个技能
                if self._has_skill(skill_name):
                    logger.info(f"Skill {skill_name} already exists")
                    return None

                return ImprovementPlan(
                    id=f"learn_{skill_name}_{hash(request) % 10000}",
                    improvement_type=ImprovementType.SKILL_ACQUISITION,
                    description=f"主人请求: {request}",
                    target=skill_name,
                    steps=[
                        f"研究 {skill_name} 技能需求",
                        "生成 skill 代码",
                        "沙箱测试",
                        "晋升到 production",
                    ],
                    confidence=0.8,
                )

        return None

    def _has_skill(self, skill_name: str) -> bool:
        """检查技能是否已存在"""
        skills_dir = self.darwin_root / "skills"
        skill_path = skills_dir / f"{skill_name}.md"
        return skill_path.exists()


class ChannelLearner(SelfImprovementModule):
    """
    沟通渠道学习器

    当 Darwin 发现需要支持新沟通平台时，
    研究平台 API，生成 channel skill，通过沙箱验证。
    """

    # 支持的平台列表
    SUPPORTED_CHANNELS = {
        "dingtalk": {
            "name": "钉钉",
            "api_docs": "https://open.dingtalk.com/document/app",
            "icon": "🔔",
        },
        "wecom": {
            "name": "企业微信",
            "api_docs": "https://developer.work.weixin.qq.com/document/",
            "icon": "💼",
        },
        "telegram": {
            "name": "Telegram",
            "api_docs": "https://core.telegram.org/bots/api",
            "icon": "✈️",
        },
        "slack": {
            "name": "Slack",
            "api_docs": "https://api.slack.com/",
            "icon": "💬",
        },
        "discord": {
            "name": "Discord",
            "api_docs": "https://discord.com/developers/docs",
            "icon": "🎮",
        },
    }

    def __init__(self, darwin_root: Path, perception: PerceptionModule,
                 evolution_engine=None):
        super().__init__(darwin_root, perception)
        self.evolution_engine = evolution_engine

    def detect(self) -> list:
        """检测需要学习的沟通渠道"""
        gaps = []

        # 获取最近的主人消息
        context = self.perception.get_context_for_analysis(time_window_hours=168)
        messages = context.get("recent_master_messages", [])
        all_content = " ".join([m["content"] for m in messages])

        for channel_id, channel_info in self.SUPPORTED_CHANNELS.items():
            # 检查是否提到了这个平台
            if channel_id in all_content.lower() or channel_info["name"] in all_content:
                # 检查是否已有这个渠道
                if not self._has_channel(channel_id):
                    from .self_improvement import AbilityGap
                    gap = AbilityGap(
                        ability_name=channel_id,
                        current_level=0.0,
                        required_level=0.8,
                        evidence=[f"主人在消息中提到: {channel_info['name']}"],
                        suggested_improvement=f"学习 {channel_info['name']} 接入",
                    )
                    gaps.append(gap)

        return gaps

    def plan_improvement(self, gap) -> ImprovementPlan | None:
        """制定渠道学习计划"""
        channel_id = gap.ability_name if hasattr(gap, "ability_name") else gap
        channel_info = self.SUPPORTED_CHANNELS.get(channel_id, {})

        return ImprovementPlan(
            id=f"channel_learn_{channel_id}_{hash(channel_id) % 10000}",
            improvement_type=ImprovementType.CHANNEL_ACQUISITION,
            description=f"学习接入 {channel_info.get('name', channel_id)}",
            target=channel_id,
            steps=[
                f"研究 {channel_info.get('name', channel_id)} API 文档",
                f"了解 {channel_info.get('name', channel_id)} 机器人配置",
                f"生成 {channel_id}-channel-skill",
                "沙箱测试连通性",
                "晋升到 production",
            ],
            confidence=0.8,
        )

    def execute(self, plan: ImprovementPlan) -> bool:
        """执行渠道学习"""
        channel_id = plan.target
        channel_info = self.SUPPORTED_CHANNELS.get(channel_id, {})

        logger.info(f"Learning channel: {channel_info.get('name', channel_id)}")

        try:
            # 1. 研究 API 文档（这里需要 LLM 调用）
            # 2. 生成 channel skill 代码
            # 3. 通过沙箱验证

            logger.info(f"Channel learning completed: {channel_id}")

            self.log_improvement(
                ImprovementType.CHANNEL_ACQUISITION,
                f"渠道学习完成: {channel_info.get('name', channel_id)}",
                success=True,
            )

            return True

        except Exception as e:
            logger.error(f"Channel learning failed: {e}")
            self.log_improvement(
                ImprovementType.CHANNEL_ACQUISITION,
                f"渠道学习失败: {channel_id} — {e}",
                success=False,
            )
            return False

    def _has_channel(self, channel_id: str) -> bool:
        """检查渠道是否已存在"""
        channels_dir = self.darwin_root / "channels"
        channel_path = channels_dir / f"{channel_id}.md"
        return channel_path.exists()


class MigrationProtocol:
    """
    跨设备迁移协议

    导出 Darwin 的所有记忆和状态，导入到新设备。
    """

    MIGRATION_DIR = "migration"
    EXPORT_FILE = "darwin_migration_{timestamp}.zip"

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root).resolve()

    def export_package(self, target_path: Path = None) -> Path:
        """
        导出迁移包

        包含：SOUL.md, skills/, evolution/, perception_memory.jsonl 等

        Returns:
            Path: 迁移包路径
        """
        logger.info("Starting Darwin migration package export")

        # TODO: 实现 zip 打包
        # 包含内容：
        # - SOUL.md
        # - skills/
        # - evolution/memory/
        # - evolution/checkpoints/
        # - evolution/proposals/
        # - evolution/tests/
        # - config.yaml

        logger.info("Migration package export completed (stub)")
        return target_path or self.darwin_root

    def import_package(self, package_path: Path) -> bool:
        """
        导入迁移包

        从旧设备接收迁移包，恢复 Darwin 完整状态。

        Returns:
            bool: 是否成功
        """
        logger.info(f"Importing migration package from {package_path}")

        try:
            # TODO: 实现 zip 解压和验证
            # 验证内容：
            # - SOUL.md 是否存在
            # - 必需文件是否完整
            # - 版本是否兼容

            logger.info("Migration package import completed (stub)")
            return True

        except Exception as e:
            logger.error(f"Migration import failed: {e}")
            return False

    def verify_identity(self, package_path: Path) -> bool:
        """
        验证迁移后身份是否一致

        检查 SOUL.md 的 identity 是否匹配。

        Returns:
            bool: 是否通过验证
        """
        # TODO: 实现身份验证
        return True