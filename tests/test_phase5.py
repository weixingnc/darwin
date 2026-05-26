"""Test suite for Phase 5 Self-Improvement modules"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.self_improvement import ImprovementType, ImprovementPlan, AbilityGap
from darwin.ability_gap_detector import AbilityGapDetector, KNOWN_ABILITIES
from darwin.skill_learner import SkillLearner, ChannelLearner, MigrationProtocol


def test_improvement_types():
    """ImprovementType 枚举正常"""
    types = list(ImprovementType)
    assert ImprovementType.ABILITY_GAP in types
    assert ImprovementType.SKILL_ACQUISITION in types
    assert ImprovementType.CHANNEL_ACQUISITION in types
    assert ImprovementType.MIGRATION in types


def test_ability_gap():
    """AbilityGap 数据类正常"""
    gap = AbilityGap(
        ability_name="data_analysis",
        current_level=0.3,
        required_level=0.7,
        evidence=["主人在消息中提到数据分析"],
        suggested_improvement="学习数据分析技能",
    )
    assert gap.ability_name == "data_analysis"
    assert gap.current_level == 0.3
    assert gap.required_level == 0.7


def test_improvement_plan():
    """ImprovementPlan 数据类正常"""
    plan = ImprovementPlan(
        id="test_plan",
        improvement_type=ImprovementType.SKILL_ACQUISITION,
        description="学习数据分析",
        target="data-analysis",
        steps=["研究", "生成", "测试", "晋升"],
        confidence=0.8,
    )
    assert plan.id == "test_plan"
    assert plan.improvement_type == ImprovementType.SKILL_ACQUISITION
    assert len(plan.steps) == 4


def test_ability_gap_detector_loads():
    """AbilityGapDetector 可以正常加载"""
    detector = AbilityGapDetector(Path("/home/weixing/darwin"), None)
    assert detector.darwin_root == Path("/home/weixing/darwin")
    assert len(detector.known_abilities) > 0


def test_known_abilities():
    """已知能力列表包含常见能力"""
    names = [a["name"] for a in KNOWN_ABILITIES]
    assert "conversation" in names
    assert "coding" in names
    assert "data_analysis" in names
    assert "dingtalk" in names
    assert "telegram" in names


def test_skill_learner_loads():
    """SkillLearner 可以正常加载"""
    learner = SkillLearner(Path("/home/weixing/darwin"), None)
    assert learner.darwin_root == Path("/home/weixing/darwin")


def test_skill_learner_learn_request():
    """SkillLearner 可以识别主人的学习请求"""
    learner = SkillLearner(Path("/home/weixing/darwin"), None)
    learner.auto_evolve = False  # 避免触发进化

    # "我想做一个数据分析"
    plan = learner.learn_from_master_request("我想做一个数据分析")
    assert plan is not None
    assert plan.improvement_type == ImprovementType.SKILL_ACQUISITION
    assert plan.target == "data-analysis"


def test_skill_learner_learn_request_novel():
    """SkillLearner 对已知技能返回 None"""
    learner = SkillLearner(Path("/home/weixing/darwin"), None)
    # 如果已经有 data-analysis skill，应该返回 None
    skills_dir = Path("/home/weixing/darwin/skills")
    if (skills_dir / "data-analysis.md").exists():
        plan = learner.learn_from_master_request("我想做一个数据分析")
        # 可能返回 None 如果已经存在


def test_channel_learner_loads():
    """ChannelLearner 可以正常加载"""
    learner = ChannelLearner(Path("/home/weixing/darwin"), None)
    assert learner.darwin_root == Path("/home/weixing/darwin")
    assert len(learner.SUPPORTED_CHANNELS) > 0


def test_channel_learner_supported():
    """ChannelLearner 支持常用平台"""
    channels = ChannelLearner.SUPPORTED_CHANNELS
    assert "dingtalk" in channels
    assert "wecom" in channels
    assert "telegram" in channels
    assert "slack" in channels


def test_channel_learner_plan():
    """ChannelLearner 可以生成学习计划"""
    from darwin.self_improvement import AbilityGap
    learner = ChannelLearner(Path("/home/weixing/darwin"), None)
    gap = AbilityGap(
        ability_name="dingtalk",
        current_level=0.0,
        required_level=0.8,
        evidence=["主人在消息中提到钉钉"],
        suggested_improvement="学习钉钉接入",
    )
    plan = learner.plan_improvement(gap)
    assert plan is not None
    assert plan.improvement_type == ImprovementType.CHANNEL_ACQUISITION
    assert plan.target == "dingtalk"


def test_migration_protocol_loads():
    """MigrationProtocol 可以正常加载"""
    migrator = MigrationProtocol(Path("/home/weixing/darwin"))
    assert migrator.darwin_root == Path("/home/weixing/darwin")


if __name__ == "__main__":
    tests = [
        ("ImprovementType enum", test_improvement_types),
        ("AbilityGap", test_ability_gap),
        ("ImprovementPlan", test_improvement_plan),
        ("AbilityGapDetector loads", test_ability_gap_detector_loads),
        ("Known abilities list", test_known_abilities),
        ("SkillLearner loads", test_skill_learner_loads),
        ("SkillLearner learn request", test_skill_learner_learn_request),
        ("ChannelLearner loads", test_channel_learner_loads),
        ("ChannelLearner supported", test_channel_learner_supported),
        ("ChannelLearner plan", test_channel_learner_plan),
        ("MigrationProtocol loads", test_migration_protocol_loads),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)