"""Evolution CLI — 进化相关的命令行扩展"""

import click
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@click.group()
def evolution():
    """进化引擎相关命令"""
    pass


# ──────────────────────────────────────────
# SOUL Editor commands
# ──────────────────────────────────────────

@evolution.command("list-soul-proposals")
def list_soul_proposals():
    """列出待审批的 SOUL 修改提案"""
    from darwin.evolution.soul_editor import SoulEditor

    editor = SoulEditor(Path(__file__).parent.parent.parent)
    pending = editor.list_pending_proposals()

    if not pending:
        click.echo("暂无待审批的 SOUL 提案")
        return

    for p in pending:
        click.echo(f"\n提案: {p.id}")
        click.echo(f"时间: {p.proposed_at[:19]}")
        for change in p.changes:
            click.echo(f"  - {change.field}: {change.old_value[:30]} → {change.new_value[:30]}")
            click.echo(f"    原因: {change.reason}")


@evolution.command("approve-soul")
@click.argument("proposal_id")
def approve_soul(proposal_id: str):
    """审批 SOUL 提案（需要 creator 密码确认）"""
    from darwin.evolution.soul_editor import SoulEditor

    editor = SoulEditor(Path(__file__).parent.parent.parent)

    # 简单确认：显示提案内容后要求输入 y
    try:
        proposal = editor.load_proposal(proposal_id)
    except FileNotFoundError:
        click.echo(f"提案不存在: {proposal_id}")
        return

    click.echo(f"\n提案: {proposal.id}")
    for change in proposal.changes:
        click.echo(f"  - {change.field}: {change.old_value[:50]} → {change.new_value[:50]}")
    click.echo(f"\n自我分析:\n{proposal.self_analysis}")

    confirm = click.prompt("确认批准? (y/n)", default="n")
    if confirm.lower() != "y":
        click.echo("已取消")
        return

    success = editor.approve(proposal_id)
    if success:
        click.echo("✓ SOUL 提案已批准并应用")
    else:
        click.echo("✗ 应用失败")


@evolution.command("reject-soul")
@click.argument("proposal_id")
@click.option("--reason", default="", help="拒绝原因")
def reject_soul(proposal_id: str, reason: str):
    """拒绝 SOUL 提案"""
    from darwin.evolution.soul_editor import SoulEditor

    editor = SoulEditor(Path(__file__).parent.parent.parent)
    editor.reject(proposal_id, reason)
    click.echo("✓ SOUL 提案已拒绝")


# ──────────────────────────────────────────
# Skill Builder commands
# ──────────────────────────────────────────

@evolution.command("list-skill-proposals")
def list_skill_proposals():
    """列出待审批的 Skill 提案"""
    from darwin.evolution.skill_builder import SkillBuilder

    builder = SkillBuilder(Path(__file__).parent.parent.parent)
    pending = builder.list_pending_proposals()

    if not pending:
        click.echo("暂无待审批的 Skill 提案")
        return

    for p in pending:
        click.echo(f"\nSkill: {p.spec.name}")
        click.echo(f"描述: {p.spec.description}")
        click.echo(f"提案ID: {p.id}")
        click.echo(f"时间: {p.proposed_at[:19]}")


@evolution.command("approve-skill")
@click.argument("proposal_id")
def approve_skill(proposal_id: str):
    """审批 Skill 提案"""
    from darwin.evolution.skill_builder import SkillBuilder

    builder = SkillBuilder(Path(__file__).parent.parent.parent)

    try:
        proposal = builder.load_proposal(proposal_id)
    except FileNotFoundError:
        click.echo(f"提案不存在: {proposal_id}")
        return

    click.echo(f"\nSkill: {proposal.spec.name}")
    click.echo(f"描述: {proposal.spec.description}")
    click.echo(f"触发条件: {proposal.spec.trigger}")
    click.echo(f"\n自我分析:\n{proposal.self_analysis}")

    confirm = click.prompt("确认批准? (y/n)", default="n")
    if confirm.lower() != "y":
        click.echo("已取消")
        return

    success = builder.approve(proposal_id)
    if success:
        click.echo("✓ Skill 提案已批准并写入")
    else:
        click.echo("✗ 应用失败")


@evolution.command("reject-skill")
@click.argument("proposal_id")
@click.option("--reason", default="", help="拒绝原因")
def reject_skill(proposal_id: str, reason: str):
    """拒绝 Skill 提案"""
    from darwin.evolution.skill_builder import SkillBuilder

    builder = SkillBuilder(Path(__file__).parent.parent.parent)
    builder.reject(proposal_id, reason)
    click.echo("✓ Skill 提案已拒绝")


# ──────────────────────────────────────────
# Integration with main CLI
# ──────────────────────────────────────────

def register_commands(cli_group):
    """注册到主 CLI"""
    cli_group.add_command(evolution)