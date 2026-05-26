"""Test suite for Phase 5 knowledge/soul/body modules"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.self_improvement import ImprovementType, ImprovementPlan, AbilityGap
from darwin.knowledge_manager import KnowledgeManager, SoulEvolver, BodyControl


def test_improvement_types_complete():
    """ImprovementType 枚举包含所有类型"""
    types = list(ImprovementType)
    expected = [
        "ABILITY_GAP", "SKILL_ACQUISITION", "CHANNEL_ACQUISITION",
        "KNOWLEDGE_ACQUISITION", "SOUL_EVOLUTION", "BODY_EXTENSION", "MIGRATION"
    ]
    actual = [t.name for t in types]
    for e in expected:
        assert e in actual, f"Missing: {e}"


def test_knowledge_manager_loads():
    """KnowledgeManager 可以正常加载"""
    km = KnowledgeManager(Path("/home/weixing/darwin"), None)
    assert km.darwin_root == Path("/home/weixing/darwin")
    assert len(km.known_domains) > 0


def test_knowledge_manager_domains():
    """KnowledgeManager 包含常用领域"""
    km = KnowledgeManager(Path("/home/weixing/darwin"), None)
    domains = list(km.known_domains.keys())
    assert "medical" in domains
    assert "legal" in domains
    assert "finance" in domains
    assert "technology" in domains


def test_knowledge_manager_plan():
    """KnowledgeManager 可以生成学习计划"""
    km = KnowledgeManager(Path("/home/weixing/darwin"), None)
    gap = AbilityGap(
        ability_name="knowledge:medical",
        current_level=0.0,
        required_level=0.5,
        evidence=["主人在消息中提到医学"],
        suggested_improvement="学习医学领域知识",
    )
    plan = km.plan_improvement(gap)
    assert plan is not None
    assert plan.improvement_type == ImprovementType.KNOWLEDGE_ACQUISITION
    assert plan.target == "medical"


def test_soul_evolver_loads():
    """SoulEvolver 可以正常加载"""
    se = SoulEvolver(Path("/home/weixing/darwin"), None)
    assert se.darwin_root == Path("/home/weixing/darwin")


def test_soul_evolver_plan():
    """SoulEvolver 可以生成进化计划"""
    se = SoulEvolver(Path("/home/weixing/darwin"), None)
    gap = AbilityGap(
        ability_name="soul:personality",
        current_level=0.5,
        required_level=0.7,
        evidence=["有3条负面反馈"],
        suggested_improvement="调整SOUL性格参数",
    )
    plan = se.plan_improvement(gap)
    assert plan is not None
    assert plan.improvement_type == ImprovementType.SOUL_EVOLUTION


def test_body_control_loads():
    """BodyControl 可以正常加载"""
    bc = BodyControl(Path("/home/weixing/darwin"), None)
    assert bc.darwin_root == Path("/home/weixing/darwin")
    assert len(bc.known_hardware) > 0


def test_body_control_hardware():
    """BodyControl 支持常见硬件"""
    bc = BodyControl(Path("/home/weixing/darwin"), None)
    hw = list(bc.known_hardware.keys())
    assert "camera" in hw
    assert "microphone" in hw
    assert "speaker" in hw
    assert "smart_home" in hw


def test_body_control_plan():
    """BodyControl 可以生成硬件连接计划"""
    bc = BodyControl(Path("/home/weixing/darwin"), None)
    gap = AbilityGap(
        ability_name="body:camera",
        current_level=0.0,
        required_level=0.7,
        evidence=["主人在消息中提到拍照"],
        suggested_improvement="连接摄像头硬件",
    )
    plan = bc.plan_improvement(gap)
    assert plan is not None
    assert plan.improvement_type == ImprovementType.BODY_EXTENSION
    assert plan.target == "camera"


def test_darwin_core_has_all_modules():
    """DarwinCore 包含所有自我完善模块"""
    from darwin.core import DarwinCore
    core = DarwinCore(Path("/home/weixing/darwin"))
    assert hasattr(core, 'knowledge_manager')
    assert hasattr(core, 'soul_evolver')
    assert hasattr(core, 'body_control')
    assert hasattr(core, 'ability_detector')
    assert hasattr(core, 'skill_learner')
    assert hasattr(core, 'channel_learner')


if __name__ == "__main__":
    tests = [
        ("ImprovementType complete", test_improvement_types_complete),
        ("KnowledgeManager loads", test_knowledge_manager_loads),
        ("KnowledgeManager domains", test_knowledge_manager_domains),
        ("KnowledgeManager plan", test_knowledge_manager_plan),
        ("SoulEvolver loads", test_soul_evolver_loads),
        ("SoulEvolver plan", test_soul_evolver_plan),
        ("BodyControl loads", test_body_control_loads),
        ("BodyControl hardware", test_body_control_hardware),
        ("BodyControl plan", test_body_control_plan),
        ("DarwinCore has all modules", test_darwin_core_has_all_modules),
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