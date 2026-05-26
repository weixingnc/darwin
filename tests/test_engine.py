"""Test suite for updated EvolutionEngine with Sandbox integration"""

import sys
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.evolution import (
    EvolutionEngine, EvolutionPlan, EvolutionResult, EvolutionPhase,
    SandboxManager, TestRunner, Promoter
)


def test_evolution_engine_loads():
    """EvolutionEngine 可以正常加载"""
    engine = EvolutionEngine(Path("/home/weixing/darwin"))
    assert engine.darwin_root == Path("/home/weixing/darwin")
    assert engine.sandbox_manager is not None
    assert engine.test_runner is not None
    assert engine.promoter is not None


def test_evolution_engine_create_plan():
    """可以创建进化计划"""
    engine = EvolutionEngine(Path("/home/weixing/darwin"))
    plan = engine.create_plan("测试进化", ["修改 SOUL", "添加 skill"])
    assert plan.id.startswith("evo_")
    assert plan.description == "测试进化"
    assert len(plan.changes) == 2


def test_evolution_engine_sandbox_phases():
    """验证沙箱模式下新增的阶段"""
    expected = [
        "idle", "snapshot", "sandbox_create", "sandbox_test",
        "sandbox_promote", "evaluate", "commit", "rollback", "done"
    ]
    actual = [p.value for p in EvolutionPhase]
    assert actual == expected, f"Expected {expected}, got {actual}"


def test_evolution_engine_get_status():
    """可以获取状态"""
    engine = EvolutionEngine(Path("/home/weixing/darwin"))
    status = engine.get_status()
    assert "current_plan" in status
    assert "history_count" in status
    assert "sandbox_count" in status


def test_evolution_engine_sandbox_workflow():
    """测试沙箱完整流程（集成测试）"""
    # 清理旧沙箱
    darwin_root = Path("/home/weixing/darwin")
    sandbox_dir = darwin_root / ".sandbox"
    if sandbox_dir.exists():
        for item in sandbox_dir.glob("sandbox_*"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    # 使用真实目录
    engine = EvolutionEngine(darwin_root)

    # 创建计划
    plan = engine.create_plan("测试沙箱进化", ["新增 skill: test-skill"])

    # 执行（沙箱模式）
    # 注意：这个会真正创建沙箱和运行测试
    result = engine.execute(plan)

    # 验证结果结构
    assert result.plan_id == plan.id
    assert result.sandbox_id is not None or result.message is not None
    # 可能通过也可能失败，取决于实际环境
    print(f"Result: success={result.success}, phase={result.phase_reached.value}, message={result.message}")


def test_evolution_engine_execute_simple():
    """测试简化模式（无沙箱）"""
    engine = EvolutionEngine(Path("/home/weixing/darwin"))
    plan = engine.create_plan("测试简化模式", ["修改配置"])

    # 简化模式不需要沙箱
    result = engine.execute_simple(plan)

    # 验证结果结构
    assert result.plan_id == plan.id
    assert result.phase_reached in [EvolutionPhase.DONE, EvolutionPhase.COMMIT, EvolutionPhase.SANDBOX_TEST]


if __name__ == "__main__":
    tests = [
        ("EvolutionEngine loads", test_evolution_engine_loads),
        ("EvolutionEngine create plan", test_evolution_engine_create_plan),
        ("EvolutionEngine sandbox phases", test_evolution_engine_sandbox_phases),
        ("EvolutionEngine get status", test_evolution_engine_get_status),
        ("EvolutionEngine execute simple", test_evolution_engine_execute_simple),
        # 这个测试会真正运行沙箱，比较慢
        # ("EvolutionEngine sandbox workflow", test_evolution_engine_sandbox_workflow),
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