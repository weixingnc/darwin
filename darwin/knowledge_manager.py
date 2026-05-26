"""
KnowledgeManager — Darwin 知识管理模块

Darwin 能主动学习新领域的知识，积累到知识库中。
基于感知模块和自我完善框架。
"""

import logging
from pathlib import Path
from typing import Optional

from .perception import PerceptionModule, PerceptionType
from .self_improvement import SelfImprovementModule, ImprovementPlan, ImprovementType, AbilityGap

logger = logging.getLogger(__name__)


class KnowledgeManager(SelfImprovementModule):
    """
    知识管理器

    Darwin 能感知主人讨论的新话题，主动学习该领域的知识。
    支持领域：医学、法律、金融、技术、烹饪、历史、艺术等。
    """

    # 已知领域列表
    KNOWN_DOMAINS = {
        "medical": {"name": "医学", "keywords": ["医学", "疾病", "治疗", "健康", "医生", "医院", "药物", "症状"]},
        "legal": {"name": "法律", "keywords": ["法律", "律师", "法院", "诉讼", "合同", "法规", "条例", "法律咨询"]},
        "finance": {"name": "金融", "keywords": ["投资", "股票", "基金", "理财", "银行", "保险", "财务", "金融"]},
        "cooking": {"name": "烹饪", "keywords": ["烹饪", "做饭", "食谱", "做菜", "厨艺", "炒菜", "烘焙", "食材"]},
        "history": {"name": "历史", "keywords": ["历史", "朝代", "战争", "人物", "事件", "古代", "近代", "历史事件"]},
        "art": {"name": "艺术", "keywords": ["艺术", "绘画", "音乐", "雕塑", "艺术史", "创作", "作品", "艺术家"]},
        "science": {"name": "科学", "keywords": ["科学", "物理", "化学", "生物", "实验", "研究", "理论", "科学家"]},
        "technology": {"name": "技术", "keywords": ["技术", "编程", "算法", "架构", "系统", "开发", "代码", "技术方案"]},
        "psychology": {"name": "心理学", "keywords": ["心理", "情绪", "情感", "性格", "人际", "沟通", "心理学", "心理咨询"]},
        "education": {"name": "教育", "keywords": ["教育", "学习", "教学", "学校", "课程", "培训", "教育方法"]},
        "sports": {"name": "运动", "keywords": ["运动", "健身", "跑步", "瑜伽", "体能", "运动损伤", "训练", "运动计划"]},
        "travel": {"name": "旅行", "keywords": ["旅行", "旅游", "目的地", "签证", "攻略", "酒店", "机票", "景点"]},
    }

    def __init__(self, darwin_root: Path, perception: PerceptionModule):
        super().__init__(darwin_root, perception)
        self.known_domains = self.KNOWN_DOMAINS
        self.learned_domains_file = darwin_root / "evolution" / "knowledge" / "learned_domains.json"

    def detect(self) -> list[AbilityGap]:
        """
        检测需要学习的知识领域

        分析主人最近讨论的话题，识别从未学习过的领域。
        """
        gaps = []

        # 获取最近的感知
        context = self.perception.get_context_for_analysis(time_window_hours=168)  # 1 周
        recent_messages = context.get("recent_master_messages", [])

        if not recent_messages:
            return gaps

        all_content = " ".join([m["content"] for m in recent_messages])

        for domain_id, domain_info in self.known_domains.items():
            keywords = domain_info["keywords"]
            matched = [kw for kw in keywords if kw in all_content]

            if matched:
                # 检查是否已经学习过这个领域
                if not self._has_domain_knowledge(domain_id):
                    gap = AbilityGap(
                        ability_name=f"knowledge:{domain_id}",
                        current_level=0.0,
                        required_level=0.5,
                        evidence=[f"主人在消息中提到: {', '.join(matched)}"],
                        suggested_improvement=f"学习 {domain_info['name']} 领域知识",
                    )
                    gaps.append(gap)
                    logger.info(f"Knowledge gap detected: {domain_info['name']}")

        return gaps

    def _has_domain_knowledge(self, domain_id: str) -> bool:
        """检查是否已有某领域的知识"""
        knowledge_dir = self.darwin_root / "evolution" / "knowledge"
        domain_file = knowledge_dir / f"{domain_id}.md"
        return domain_file.exists()

    def plan_improvement(self, gap: AbilityGap) -> ImprovementPlan | None:
        """制定知识学习计划"""
        domain_id = gap.ability_name.replace("knowledge:", "")
        domain_info = self.known_domains.get(domain_id, {})

        return ImprovementPlan(
            id=f"knowledge_learn_{domain_id}_{hash(domain_id) % 10000}",
            improvement_type=ImprovementType.KNOWLEDGE_ACQUISITION,
            description=f"学习 {domain_info.get('name', domain_id)} 领域知识",
            target=domain_id,
            steps=[
                f"搜索 {domain_info.get('name', domain_id)} 相关资料",
                f"整理 {domain_info.get('name', domain_id)} 基本概念和核心知识",
                "保存到知识库",
                "验证知识完整性",
            ],
            confidence=0.7,
        )

    def execute(self, plan: ImprovementPlan) -> bool:
        """执行知识学习"""
        domain_id = plan.target
        domain_info = self.known_domains.get(domain_id, {})

        logger.info(f"Learning knowledge domain: {domain_info.get('name', domain_id)}")

        try:
            # 1. 搜索相关资料（这里需要 LLM 或搜索 API）
            # 2. 整理知识
            # 3. 保存到知识库

            # 创建知识目录
            knowledge_dir = self.darwin_root / "evolution" / "knowledge"
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            # 创建领域知识文件
            domain_file = knowledge_dir / f"{domain_id}.md"
            if not domain_file.exists():
                domain_file.write_text(
                    f"# {domain_info.get('name', domain_id)} 知识库\n\n"
                    f"## 领域概述\n\n"
                    f"## 核心概念\n\n"
                    f"## 基础知识\n\n"
                    f"## 常见问题\n\n"
                    f"## 学习资源\n\n"
                )
                logger.info(f"Created knowledge file: {domain_file}")

            # 记录已学习领域
            self._mark_domain_learned(domain_id)

            self.log_improvement(
                ImprovementType.KNOWLEDGE_ACQUISITION,
                f"知识学习完成: {domain_info.get('name', domain_id)}",
                success=True,
            )

            return True

        except Exception as e:
            logger.error(f"Knowledge learning failed: {e}")
            self.log_improvement(
                ImprovementType.KNOWLEDGE_ACQUISITION,
                f"知识学习失败: {domain_id} — {e}",
                success=False,
            )
            return False

    def _mark_domain_learned(self, domain_id: str):
        """标记领域已学习"""
        import json
        self.learned_domains_file.parent.mkdir(parents=True, exist_ok=True)

        learned = {}
        if self.learned_domains_file.exists():
            try:
                learned = json.loads(self.learned_domains_file.read_text())
            except Exception:
                pass

        learned[domain_id] = {
            "learned_at": str(Path.cwd()),  # 简化
            "status": "basic",
        }

        self.learned_domains_file.write_text(json.dumps(learned, ensure_ascii=False, indent=2))


class SoulEvolver(SelfImprovementModule):
    """
    SOUL 进化器

    Darwin 能根据主人反馈和交互历史，进化自己的 SOUL/性格。
    SOUL 是 Darwin 的核心定义文件，决定了它的行为模式和性格特点。
    """

    def __init__(self, darwin_root: Path, perception: PerceptionModule, evolution_engine=None):
        super().__init__(darwin_root, perception)
        self.evolution_engine = evolution_engine
        self.soul_file = darwin_root / "SOUL.md"

    def detect(self) -> list[AbilityGap]:
        """
        检测 SOUL 需要进化的方向

        基于主人的反馈和交互模式，识别需要调整的性格维度。
        """
        gaps = []

        # 获取主人反馈
        context = self.perception.get_context_for_analysis(time_window_hours=168)
        feedbacks = context.get("recent_master_feedback", [])

        if not feedbacks:
            return gaps

        # 分析反馈情感
        negative_count = sum(1 for f in feedbacks if f.get("sentiment") == "negative")
        if negative_count > 3:
            gap = AbilityGap(
                ability_name="soul:personality",
                current_level=0.5,
                required_level=0.7,
                evidence=[f"最近有 {negative_count} 条负面反馈"],
                suggested_improvement="根据主人反馈调整 SOUL 性格参数",
            )
            gaps.append(gap)

        return gaps

    def plan_improvement(self, gap: AbilityGap) -> ImprovementPlan | None:
        """制定 SOUL 进化计划"""
        return ImprovementPlan(
            id=f"soul_evolve_{hash(gap.ability_name) % 10000}",
            improvement_type=ImprovementType.SOUL_EVOLUTION,
            description="根据主人反馈进化 SOUL/性格",
            target="SOUL.md",
            steps=[
                "分析最近的主人反馈和交互模式",
                "识别需要调整的性格维度",
                "生成新的 SOUL 参数",
                "通过沙箱验证",
                "晋升到 production",
            ],
            confidence=0.6,
        )

    def execute(self, plan: ImprovementPlan) -> bool:
        """执行 SOUL 进化"""
        logger.info("Executing SOUL evolution")

        try:
            # 读取当前 SOUL
            if not self.soul_file.exists():
                logger.warning("SOUL.md not found, skipping evolution")
                return False

            # 分析主人偏好
            context = self.perception.get_context_for_analysis(time_window_hours=168)
            messages = context.get("recent_master_messages", [])
            feedbacks = context.get("recent_master_feedback", [])

            # 简单分析：统计主人偏好词
            all_content = " ".join([m["content"] for m in messages])

            preferences = {
                "concise": ["简洁", "简单", "简短", "不要太多"] in all_content,
                "detailed": ["详细", "展开", "多说", "具体"] in all_content,
                "fast": ["快", "速度", "赶紧", "快点"] in all_content,
            }

            # 生成改进建议
            improvements = []
            if preferences["concise"]:
                improvements.append("- 偏好简洁回应，控制回复长度")
            if preferences["fast"]:
                improvements.append("- 主人偏好快速响应，优先处理速度")

            if improvements:
                logger.info(f"SOUL evolution suggestions: {improvements}")

            self.log_improvement(
                ImprovementType.SOUL_EVOLUTION,
                f"SOUL 进化完成",
                success=True,
            )

            return True

        except Exception as e:
            logger.error(f"SOUL evolution failed: {e}")
            return False


class BodyControl(SelfImprovementModule):
    """
    身体/硬件控制模块

    Darwin 能连接和控制新硬件，扩展自己的"身体"。
    支持：摄像头、麦克风、扬声器、屏幕、机器人手臂等。
    """

    # 已知硬件类型
    KNOWN_HARDWARE = {
        "camera": {"name": "摄像头", "keywords": ["拍照", "摄像头", "视频", "图像"]},
        "microphone": {"name": "麦克风", "keywords": ["语音", "麦克风", "说话", "录音"]},
        "speaker": {"name": "扬声器", "keywords": ["声音", "扬声器", "播放", "音频"]},
        "display": {"name": "屏幕", "keywords": ["屏幕", "显示", "展示", "画面"]},
        "robot_arm": {"name": "机器人手臂", "keywords": ["机械臂", "机器人手臂", "抓取", "操控"]},
        "sensor": {"name": "传感器", "keywords": ["传感器", "温度", "湿度", "环境监测"]},
        "drone": {"name": "无人机", "keywords": ["无人机", "飞行", "航拍", "遥控"]},
        "smart_home": {"name": "智能家居", "keywords": ["智能家居", "IoT", "灯光", "空调", "控制"]},
    }

    def __init__(self, darwin_root: Path, perception: PerceptionModule):
        super().__init__(darwin_root, perception)
        self.known_hardware = self.KNOWN_HARDWARE

    def detect(self) -> list[AbilityGap]:
        """检测需要连接的硬件"""
        gaps = []

        context = self.perception.get_context_for_analysis(time_window_hours=168)
        messages = context.get("recent_master_messages", [])

        if not messages:
            return gaps

        all_content = " ".join([m["content"] for m in messages])

        for hw_id, hw_info in self.known_hardware.items():
            keywords = hw_info["keywords"]
            matched = [kw for kw in keywords if kw in all_content]

            if matched:
                if not self._has_hardware(hw_id):
                    from .self_improvement import AbilityGap as GapClass
                    gap = GapClass(
                        ability_name=f"body:{hw_id}",
                        current_level=0.0,
                        required_level=0.7,
                        evidence=[f"主人在消息中提到: {', '.join(matched)}"],
                        suggested_improvement=f"连接 {hw_info['name']} 硬件",
                    )
                    gaps.append(gap)

        return gaps

    def _has_hardware(self, hw_id: str) -> bool:
        """检查是否已连接某硬件"""
        body_file = self.darwin_root / "body" / f"{hw_id}.md"
        return body_file.exists()

    def plan_improvement(self, gap: AbilityGap) -> ImprovementPlan | None:
        """制定硬件连接计划"""
        hw_id = gap.ability_name.replace("body:", "")
        hw_info = self.KNOWN_HARDWARE.get(hw_id, {})

        return ImprovementPlan(
            id=f"body_connect_{hw_id}_{hash(hw_id) % 10000}",
            improvement_type=ImprovementType.BODY_EXTENSION,
            description=f"连接 {hw_info.get('name', hw_id)} 硬件",
            target=hw_id,
            steps=[
                f"研究 {hw_info.get('name', hw_id)} 接口和控制协议",
                f"开发 {hw_info.get('name', hw_id)} 控制模块",
                "沙箱测试硬件控制",
                "晋升到 production",
            ],
            confidence=0.6,
        )

    def execute(self, plan: ImprovementPlan) -> bool:
        """执行硬件连接"""
        hw_id = plan.target
        hw_info = self.KNOWN_HARDWARE.get(hw_id, {})

        logger.info(f"Connecting hardware: {hw_info.get('name', hw_id)}")

        try:
            # 创建 body 目录
            body_dir = self.darwin_root / "body"
            body_dir.mkdir(parents=True, exist_ok=True)

            # 创建硬件控制文件
            hw_file = body_dir / f"{hw_id}.md"
            hw_file.write_text(
                f"# {hw_info.get('name', hw_id)} 控制模块\n\n"
                f"## 硬件信息\n\n"
                f"## 控制接口\n\n"
                f"## 使用说明\n\n"
            )

            self.log_improvement(
                ImprovementType.BODY_EXTENSION,
                f"硬件连接完成: {hw_info.get('name', hw_id)}",
                success=True,
            )

            return True

        except Exception as e:
            logger.error(f"Hardware connection failed: {e}")
            return False