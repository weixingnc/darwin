"""Test suite for Sandbox system"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.evolution.sandbox_manager import SandboxManager, SandboxInfo
from darwin.evolution.test_runner import TestRunner
from darwin.evolution.promoter import Promoter


def test_sandbox_manager_create():
    """可以创建沙箱"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SandboxManager(Path(tmpdir))
        info = mgr.create_sandbox("测试变更")
        assert info.sandbox_id.startswith("sandbox_")
        assert info.status == "created"
        assert (Path(tmpdir) / ".sandbox" / info.sandbox_id).exists()


def test_sandbox_manager_list():
    """可以列出沙箱"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SandboxManager(Path(tmpdir))
        mgr.create_sandbox("test 1")
        mgr.create_sandbox("test 2")
        sandboxes = mgr.list_sandboxes()
        # 每个沙箱应该在自己的临时目录中
        assert len(sandboxes) >= 1


def test_sandbox_manager_destroy():
    """可以销毁沙箱"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = SandboxManager(Path(tmpdir))
        info = mgr.create_sandbox("测试")
        result = mgr.destroy_sandbox(info.sandbox_id)
        assert result is True
        assert not (Path(tmpdir) / ".sandbox" / info.sandbox_id).exists()


def test_sandbox_manager_apply_soul_change():
    """可以在沙箱中应用 SOUL 变更"""
    # 使用真实的 darwin 目录（有 SOUL.md）
    darwin_root = Path("/home/weixing/darwin")
    mgr = SandboxManager(darwin_root)
    info = mgr.create_sandbox("测试 SOUL 变更")

    new_soul = "# SOUL 测试\nidentity: 测试用 Darwin\n"
    result = mgr.apply_soul_change(info.sandbox_id, new_soul)

    assert result is True
    soul_file = darwin_root / ".sandbox" / info.sandbox_id / "SOUL.md"
    assert soul_file.read_text() == new_soul


def test_sandbox_manager_apply_skill():
    """可以在沙箱中应用 skill"""
    import shutil
    sandbox_dir = Path("/home/weixing/darwin/.sandbox")
    if sandbox_dir.exists():
        for item in sandbox_dir.glob("sandbox_*"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    darwin_root = Path("/home/weixing/darwin")
    mgr = SandboxManager(darwin_root)
    info = mgr.create_sandbox("测试 Skill 添加")

    skill_content = "# 测试 Skill\n测试内容"
    result = mgr.apply_skill(info.sandbox_id, "test-skill", skill_content)

    assert result is True


def test_test_runner_loads():
    """TestRunner 可以正常加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = TestRunner(Path(tmpdir))
        assert runner.darwin_root == Path(tmpdir)


def test_test_runner_verify_soul_consistency():
    """可以验证 SOUL 自洽性"""
    import shutil
    sandbox_dir = Path("/home/weixing/darwin/.sandbox")
    if sandbox_dir.exists():
        for item in sandbox_dir.glob("sandbox_*"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    darwin_root = Path("/home/weixing/darwin")
    runner = TestRunner(darwin_root)

    mgr = SandboxManager(darwin_root)
    info = mgr.create_sandbox("测试 SOUL 验证")

    valid, msg = runner.verify_soul_consistency(info.sandbox_path)
    assert valid is True, f"SOUL consistency check failed: {msg}"


def test_promoter_loads():
    """Promoter 可以正常加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        promoter = Promoter(Path(tmpdir))
        assert promoter.darwin_root == Path(tmpdir)


def test_promoter_get_history():
    """可以获取晋升历史"""
    with tempfile.TemporaryDirectory() as tmpdir:
        promoter = Promoter(Path(tmpdir))
        history = promoter.get_promotion_history()
        assert isinstance(history, list)


if __name__ == "__main__":
    tests = [
        ("SandboxManager create", test_sandbox_manager_create),
        ("SandboxManager list", test_sandbox_manager_list),
        ("SandboxManager destroy", test_sandbox_manager_destroy),
        ("SandboxManager apply soul change", test_sandbox_manager_apply_soul_change),
        ("SandboxManager apply skill", test_sandbox_manager_apply_skill),
        ("TestRunner loads", test_test_runner_loads),
        ("TestRunner verify soul", test_test_runner_verify_soul_consistency),
        ("Promoter loads", test_promoter_loads),
        ("Promoter get history", test_promoter_get_history),
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