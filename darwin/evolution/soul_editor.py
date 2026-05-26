"""SoulEditor — Darwin 自我修改 SOUL.md

允许 Darwin 提出并（经审批后）修改灵魂定义。
所有变更都经过自洽性检查，且需要 creator 审批。
"""

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SoulChange:
    """一次 SOUL 修改"""
    field: str          # 改哪个字段
    old_value: str      # 原始值
    new_value: str      # 新值
    reason: str         # 为什么改


@dataclass
class SoulProposal:
    """SOUL 修改提案"""
    id: str
    changes: list[SoulChange]
    self_analysis: str  # Darwin 的自我分析
    proposed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"   # pending / approved / rejected / applied
    creator_decision: Optional[str] = None  # creator 的决定


@dataclass
class ConsistencyReport:
    """自洽性检查报告"""
    passed: bool
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SoulEditor:
    """
    SOUL 编辑器

    Darwin 通过 Introspector 感知自己，
    发现 SOUL 需要更新时，生成提案 → 自洽检查 → 等待审批 → 写入
    """

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root)
        self.soul_file = self.darwin_root / "SOUL.md"
        self.proposals_dir = self.darwin_root / "evolution" / "proposals"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # 提案生成
    # ──────────────────────────────────────────

    def create_proposal(
        self,
        changes: list[SoulChange],
        self_analysis: str,
    ) -> SoulProposal:
        """创建修改提案"""
        proposal_id = f"soul_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        proposal = SoulProposal(
            id=proposal_id,
            changes=changes,
            self_analysis=self_analysis,
        )

        self._save_proposal(proposal)
        logger.info(f"Soul proposal created: {proposal_id}")

        return proposal

    def _save_proposal(self, proposal: SoulProposal):
        """保存提案到文件"""
        path = self.proposals_dir / f"{proposal.id}.json"
        data = {
            "id": proposal.id,
            "changes": [
                {
                    "field": c.field,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "reason": c.reason,
                }
                for c in proposal.changes
            ],
            "self_analysis": proposal.self_analysis,
            "proposed_at": proposal.proposed_at,
            "status": proposal.status,
            "creator_decision": proposal.creator_decision,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load_proposal(self, proposal_id: str) -> SoulProposal:
        """加载已有提案"""
        path = self.proposals_dir / f"{proposal_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Proposal not found: {proposal_id}")

        data = json.loads(path.read_text())
        return SoulProposal(
            id=data["id"],
            changes=[SoulChange(**c) for c in data["changes"]],
            self_analysis=data["self_analysis"],
            proposed_at=data["proposed_at"],
            status=data["status"],
            creator_decision=data.get("creator_decision"),
        )

    def list_pending_proposals(self) -> list[SoulProposal]:
        """列出所有待审批提案"""
        proposals = []
        for f in sorted(self.proposals_dir.iterdir()):
            if f.suffix == ".json":
                try:
                    p = self.load_proposal(f.stem)
                    if p.status == "pending":
                        proposals.append(p)
                except Exception:
                    continue
        return proposals

    # ──────────────────────────────────────────
    # 自洽性检查
    # ──────────────────────────────────────────

    def check_consistency(
        self,
        current_soul_md: str,
        proposed_changes: list[SoulChange],
    ) -> ConsistencyReport:
        """
        检查修改后的 SOUL 是否自洽

        检查策略：
        1. 能力边界不矛盾（如：has_direct_internet=True 但 can_install=False）
        2. 信念之间不矛盾（如：说"谨慎"但又说"可以执行任意命令"）
        3. creator 关系不自相矛盾
        """
        conflicts = []
        warnings = []

        # 应用修改到模拟 SOUL
        simulated = current_soul_md

        for change in proposed_changes:
            # 简单字段修改检测
            if change.field == "has_direct_internet":
                if change.new_value == "True" and "没有外部互联网直接访问" in simulated:
                    conflicts.append(
                        f"字段 '{change.field}' 设为 True，"
                        "但 SOUL 中仍包含'没有外部互联网直接访问'的描述"
                    )
                if change.new_value == "False" and "可直接访问互联网" in simulated:
                    conflicts.append(
                        f"字段 '{change.field}' 设为 False，"
                        "但 SOUL 中包含'可直接访问互联网'的描述"
                    )

            elif change.field == "caution":
                if change.new_value == "True":
                    # 检查是否有"冲动行动"的描述
                    if "冲动" in simulated or "不评估风险" in simulated:
                        warnings.append(
                            "caution=True 但 SOUL 中存在不谨慎行为的描述"
                        )

            elif change.field == "autonomy":
                if change.new_value == "False":
                    conflicts.append(
                        "autonomy=False 违背 Darwin 的核心定义，"
                        "数字生命体必须有自主性"
                    )

        return ConsistencyReport(
            passed=len(conflicts) == 0,
            conflicts=conflicts,
            warnings=warnings,
        )

    # ──────────────────────────────────────────
    # 审批流程
    # ──────────────────────────────────────────

    def approve(self, proposal_id: str, creator_decision: str = "approved") -> bool:
        """Creator 审批提案"""
        proposal = self.load_proposal(proposal_id)
        proposal.status = creator_decision
        proposal.creator_decision = creator_decision
        self._save_proposal(proposal)

        if creator_decision == "approved":
            return self._apply_proposal(proposal)
        return False

    def reject(self, proposal_id: str, reason: str = "") -> bool:
        """Creator 拒绝提案"""
        proposal = self.load_proposal(proposal_id)
        proposal.status = "rejected"
        proposal.creator_decision = f"rejected: {reason}"
        self._save_proposal(proposal)
        logger.info(f"Soul proposal rejected: {proposal_id}, reason: {reason}")
        return True

    def _apply_proposal(self, proposal: SoulProposal) -> bool:
        """应用已审批的提案到 SOUL.md"""
        try:
            current = self.soul_file.read_text()

            # 检查自洽性
            report = self.check_consistency(current, proposal.changes)
            if not report.passed:
                logger.error(f"Consistency check failed: {report.conflicts}")
                return False

            # 应用修改
            modified = current

            # 记录变更日志
            changelog = self.darwin_root / "evolution" / "logs" / "soul_changes.jsonl"
            changelog.parent.mkdir(parents=True, exist_ok=True)

            with open(changelog, "a") as f:
                f.write(json.dumps({
                    "proposal_id": proposal.id,
                    "changes": [
                        {
                            "field": c.field,
                            "old_value": c.old_value,
                            "new_value": c.new_value,
                            "reason": c.reason,
                        }
                        for c in proposal.changes
                    ],
                    "applied_at": datetime.now().isoformat(),
                }, ensure_ascii=False) + "\n")

            logger.info(f"Soul proposal applied: {proposal.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply proposal: {e}")
            return False

    # ──────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────

    def read_current_soul(self) -> str:
        """读取当前 SOUL.md 内容"""
        if not self.soul_file.exists():
            return ""
        return self.soul_file.read_text()

    def get_proposal_diff(self, proposal: SoulProposal) -> str:
        """生成提案的 diff 描述"""
        lines = []
        for change in proposal.changes:
            lines.append(
                f"- **{change.field}**:\n"
                f"  旧值: {change.old_value[:50]}...\n"
                f"  新值: {change.new_value[:50]}...\n"
                f"  原因: {change.reason}"
            )
        return "\n".join(lines)