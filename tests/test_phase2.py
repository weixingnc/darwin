"""Test suite for Phase 2: SoulEditor and SkillBuilder"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.evolution.soul_editor import SoulEditor, SoulChange, SoulProposal
from darwin.evolution.skill_builder import SkillBuilder, SkillSpec, SkillProposal


def test_soul_editor_loads():
    """SoulEditor 可以正常加载"""
    editor = SoulEditor(Path("/home/weixing/darwin"))
    assert editor.darwin_root == Path("/home/weixing/darwin")


def test_soul_editor_read_current_soul():
    """可以读取当前 SOUL.md"""
    editor = SoulEditor(Path("/home/weixing/darwin"))
    content = editor.read_current_soul()
    assert "Darwin" in content
    assert len(content) > 100


def test_soul_editor_consistency_check():
    """自洽性检查可以正常运行"""
    editor = SoulEditor(Path("/home/weixing/darwin"))
    current = editor.read_current_soul()

    changes = [
        SoulChange(
            field="caution",
            old_value="True",
            new_value="True",
            reason="测试",
        )
    ]

    report = editor.check_consistency(current, changes)
    assert report.passed is True  # 没有冲突
    assert isinstance(report.conflicts, list)


def test_soul_editor_create_proposal():
    """可以创建 SOUL 提案"""
    editor = SoulEditor(Path("/home/weixing/darwin"))
    changes = [
        SoulChange(
            field="caution",
            old_value="True",
            new_value="False",
            reason="测试：临时关闭谨慎模式",
        )
    ]

    proposal = editor.create_proposal(
        changes=changes,
        self_analysis="测试提案，仅用于验证功能",
    )

    assert proposal.id.startswith("soul_proposal_")
    assert len(proposal.changes) == 1
    assert proposal.status == "pending"


def test_skill_builder_loads():
    """SkillBuilder 可以正常加载"""
    builder = SkillBuilder(Path("/home/weixing/darwin"))
    assert builder.darwin_root == Path("/home/weixing/darwin")


def test_skill_builder_generate_skill_code():
    """可以生成 skill 代码"""
    builder = SkillBuilder(Path("/home/weixing/darwin"))
    spec = SkillSpec(
        name="test-skill",
        description="测试用 skill",
        trigger="用户请求测试",
        steps=["步骤1", "步骤2"],
        tools_needed=["terminal", "file"],
        potential_issues="无",
    )

    code = builder.generate_skill_code(spec)
    assert "test-skill" in code
    assert "测试用 skill" in code
    assert "触发条件" in code


def test_skill_builder_create_proposal():
    """可以创建 Skill 提案"""
    builder = SkillBuilder(Path("/home/weixing/darwin"))
    spec = SkillSpec(
        name="test-skill",
        description="测试用 skill",
        trigger="用户请求测试",
        steps=["步骤1", "步骤2"],
        tools_needed=["terminal", "file"],
        potential_issues="无",
    )

    proposal = builder.create_proposal(
        spec=spec,
        skill_code="# Test Skill\n> Test",
        self_analysis="测试提案",
    )

    assert proposal.id.startswith("skill_proposal_")
    assert proposal.spec.name == "test-skill"
    assert proposal.status == "pending"


def test_skill_builder_list_approved_skills():
    """可以列出已批准的 skills（当前为空）"""
    builder = SkillBuilder(Path("/home/weixing/darwin"))
    skills = builder.list_approved_skills()
    assert isinstance(skills, list)


if __name__ == "__main__":
    tests = [
        ("SoulEditor loads", test_soul_editor_loads),
        ("SoulEditor read current soul", test_soul_editor_read_current_soul),
        ("SoulEditor consistency check", test_soul_editor_consistency_check),
        ("SoulEditor create proposal", test_soul_editor_create_proposal),
        ("SkillBuilder loads", test_skill_builder_loads),
        ("SkillBuilder generate skill code", test_skill_builder_generate_skill_code),
        ("SkillBuilder create proposal", test_skill_builder_create_proposal),
        ("SkillBuilder list approved skills", test_skill_builder_list_approved_skills),
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