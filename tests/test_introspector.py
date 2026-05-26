"""Test suite for Darwin introspector"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.agent.introspector import Introspector, SoulSnapshot, EvolutionRecord


def test_introspector_loads():
    """Introspector 可以正常加载"""
    intro = Introspector(Path("/home/weixing/darwin"))
    assert intro.darwin_root == Path("/home/weixing/darwin")


def test_read_soul():
    """可以读取 SOUL.md"""
    intro = Introspector(Path("/home/weixing/darwin"))
    soul = intro.read_soul()
    assert isinstance(soul, SoulSnapshot)
    assert soul.creator == "魏星"
    assert len(soul.identity) > 0


def test_list_checkpoints():
    """可以列出快照"""
    intro = Introspector(Path("/home/weixing/darwin"))
    checkpoints = intro.list_checkpoints()
    assert isinstance(checkpoints, list)


def test_read_evolution_history():
    """可以读取进化历史"""
    intro = Introspector(Path("/home/weixing/darwin"))
    history = intro.read_evolution_history()
    assert isinstance(history, list)


def test_get_self_image():
    """可以生成完整自我镜像"""
    intro = Introspector(Path("/home/weixing/darwin"))
    img = intro.get_self_image()
    assert img.soul is not None
    assert img.version is not None
    assert img.darwin_root is not None


def test_get_brief_summary():
    """可以生成简洁摘要"""
    intro = Introspector(Path("/home/weixing/darwin"))
    summary = intro.get_brief_summary()
    assert "Darwin 状态摘要" in summary
    assert "版本" in summary
    assert "快照数" in summary


def test_get_full_context_for_analysis():
    """可以生成分析用完整上下文"""
    intro = Introspector(Path("/home/weixing/darwin"))
    context = intro.get_full_context_for_analysis()
    assert "## Darwin 自我分析上下文" in context
    assert "灵魂状态" in context
    assert "进化历史" in context


if __name__ == "__main__":
    tests = [
        ("Introspector loads", test_introspector_loads),
        ("Read SOUL", test_read_soul),
        ("List checkpoints", test_list_checkpoints),
        ("Read evolution history", test_read_evolution_history),
        ("Get self image", test_get_self_image),
        ("Get brief summary", test_get_brief_summary),
        ("Get full analysis context", test_get_full_context_for_analysis),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")

    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)