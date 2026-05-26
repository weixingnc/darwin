"""Test suite for Perception, Analyzer, and DarwinCore modules"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.perception import PerceptionModule, PerceptionType, Perception
from darwin.analyzer import AnalyzerModule, AnalysisResult, Analysis
from darwin.core import DarwinCore, DarwinState


def test_perception_module_loads():
    """PerceptionModule 可以正常加载"""
    pm = PerceptionModule(Path("/home/weixing/darwin"))
    assert pm.darwin_root == Path("/home/weixing/darwin")
    assert pm.memory is not None


def test_perception_record():
    """可以记录感知"""
    pm = PerceptionModule(Path("/home/weixing/darwin"))
    p = pm.perceive(
        PerceptionType.MASTER_MESSAGE,
        "测试消息",
        source="master",
        context={"chat_id": "test"},
        importance=0.8,
    )
    assert p.id.startswith("perc_")
    assert p.type == PerceptionType.MASTER_MESSAGE
    assert p.content == "测试消息"
    assert p.source == "master"


def test_perception_types():
    """所有感知类型都可用"""
    types = list(PerceptionType)
    assert PerceptionType.MASTER_MESSAGE in types
    assert PerceptionType.SELF_ERROR in types
    assert PerceptionType.ENVIRONMENT_CHANGE in types


def test_analyzer_module_loads():
    """AnalyzerModule 可以正常加载"""
    am = AnalyzerModule(Path("/home/weixing/darwin"))
    assert am.darwin_root == Path("/home/weixing/darwin")


def test_analyzer_analyze_empty():
    """分析空上下文"""
    am = AnalyzerModule(Path("/home/weixing/darwin"))
    context = {
        "unprocessed": [],
        "recent_master_messages": [],
        "perceptions_by_type": {},
    }
    analyses = am.analyze(context)
    assert isinstance(analyses, list)


def test_analyzer_analyze_messages():
    """分析主人消息"""
    am = AnalyzerModule(Path("/home/weixing/darwin"))
    context = {
        "unprocessed": [],
        "recent_master_messages": [
            {"content": "我想学习数据分析", "timestamp": "2026-05-27T10:00:00"},
        ],
        "perceptions_by_type": {},
    }
    analyses = am.analyze(context, min_confidence=0.0)
    assert len(analyses) > 0
    assert analyses[0].result == AnalysisResult.OPPORTUNITY_IDENTIFIED


def test_analyzer_analyze_problems():
    """分析问题"""
    am = AnalyzerModule(Path("/home/weixing/darwin"))
    context = {
        "unprocessed": [],
        "recent_master_messages": [
            {"content": "这个功能不行，错误很多", "timestamp": "2026-05-27T10:00:00"},
        ],
        "perceptions_by_type": {},
    }
    analyses = am.analyze(context, min_confidence=0.0)
    assert len(analyses) > 0
    assert analyses[0].result == AnalysisResult.PROBLEM_IDENTIFIED


def test_analyzer_generate_plan():
    """生成进化计划"""
    am = AnalyzerModule(Path("/home/weixing/darwin"))
    analysis = Analysis(
        id="test_analysis",
        result=AnalysisResult.OPPORTUNITY_IDENTIFIED,
        description="测试分析",
        suggested_changes=["学习新技能", "提升能力"],
        confidence=0.8,
        reasoning="测试",
    )
    desc, changes = am.generate_evolution_plan(analysis)
    assert desc == "测试分析"
    assert len(changes) == 2


def test_darwin_core_loads():
    """DarwinCore 可以正常加载"""
    core = DarwinCore(Path("/home/weixing/darwin"))
    assert core.darwin_root == Path("/home/weixing/darwin")
    assert core.perception is not None
    assert core.analyzer is not None
    assert core.evolution is not None


def test_darwin_core_state():
    """状态管理正常"""
    core = DarwinCore(Path("/home/weixing/darwin"))
    assert core.state == DarwinState.IDLE
    core.state = DarwinState.ANALYZING
    assert core.state == DarwinState.ANALYZING


def test_darwin_core_on_message():
    """接收主人消息"""
    core = DarwinCore(Path("/home/weixing/darwin"))
    core.auto_evolve = False  # 关闭自动进化避免意外执行
    core.on_master_message("测试消息")
    # 检查感知是否被记录
    recent = core.perception.memory.get_recent(limit=1)
    assert len(recent) >= 1
    assert recent[0].content == "测试消息"


def test_darwin_core_get_status():
    """获取状态"""
    core = DarwinCore(Path("/home/weixing/darwin"))
    status = core.get_status()
    assert "state" in status
    assert "running" in status
    assert "perception_count" in status


if __name__ == "__main__":
    tests = [
        ("PerceptionModule loads", test_perception_module_loads),
        ("Perception record", test_perception_record),
        ("Perception types", test_perception_types),
        ("AnalyzerModule loads", test_analyzer_module_loads),
        ("Analyzer analyze empty", test_analyzer_analyze_empty),
        ("Analyzer analyze messages", test_analyzer_analyze_messages),
        ("Analyzer analyze problems", test_analyzer_analyze_problems),
        ("Analyzer generate plan", test_analyzer_generate_plan),
        ("DarwinCore loads", test_darwin_core_loads),
        ("DarwinCore state", test_darwin_core_state),
        ("DarwinCore on message", test_darwin_core_on_message),
        ("DarwinCore get status", test_darwin_core_get_status),
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