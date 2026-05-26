"""SkillBuilder — Darwin 自动构建 Skills

Darwin 发现缺少某个能力时，自动生成新的 skill 文件。
所有新 skill 都需要 creator 审批后才正式生效。
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillSpec:
    """Skill 规格说明"""
    name: str                  # skill 名称（英文，kebab-case）
    description: str            # 一句话描述
    trigger: str                # 触发条件描述
    steps: list[str]            # 实现步骤
    tools_needed: list[str]     # 需要用到的工具
    potential_issues: str       # 潜在问题
    verified: bool = False       # 是否已验证


@dataclass
class SkillProposal:
    """Skill 构建提案"""
    id: str
    spec: SkillSpec
    skill_code: str              # 生成的 SKILL.md 内容
    self_analysis: str          # Darwin 为什么认为需要这个 skill
    proposed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"     # pending / approved / rejected / applied
    creator_decision: Optional[str] = None


class SkillBuilder:
    """
    Skill 构建器

    Darwin 通过 Introspector 发现能力缺口，
    生成 skill 提案 → 等待审批 → 写入 skill 文件
    """

    # Skill 存放目录
    SKILL_DIR = "skills"
    APPROVED_DIR = "skills"          # 审批通过的 skill 目录

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root)
        self.skill_dir = self.darwin_root / self.SKILL_DIR
        self.proposals_dir = self.darwin_root / "evolution" / "proposals" / "skills"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # 提案生成
    # ──────────────────────────────────────────

    def create_proposal(
        self,
        spec: SkillSpec,
        skill_code: str,
        self_analysis: str,
    ) -> SkillProposal:
        """创建 skill 提案"""
        proposal_id = f"skill_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        proposal = SkillProposal(
            id=proposal_id,
            spec=spec,
            skill_code=skill_code,
            self_analysis=self_analysis,
        )

        self._save_proposal(proposal)
        logger.info(f"Skill proposal created: {proposal_id}, skill: {spec.name}")

        return proposal

    def _save_proposal(self, proposal: SkillProposal):
        """保存提案"""
        path = self.proposals_dir / f"{proposal.id}.json"
        data = {
            "id": proposal.id,
            "spec": {
                "name": proposal.spec.name,
                "description": proposal.spec.description,
                "trigger": proposal.spec.trigger,
                "steps": proposal.spec.steps,
                "tools_needed": proposal.spec.tools_needed,
                "potential_issues": proposal.spec.potential_issues,
                "verified": proposal.spec.verified,
            },
            "skill_code": proposal.skill_code,
            "self_analysis": proposal.self_analysis,
            "proposed_at": proposal.proposed_at,
            "status": proposal.status,
            "creator_decision": proposal.creator_decision,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load_proposal(self, proposal_id: str) -> SkillProposal:
        """加载提案"""
        path = self.proposals_dir / f"{proposal_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Proposal not found: {proposal_id}")

        data = json.loads(path.read_text())
        spec = SkillSpec(**data["spec"])
        return SkillProposal(
            id=data["id"],
            spec=spec,
            skill_code=data["skill_code"],
            self_analysis=data["self_analysis"],
            proposed_at=data["proposed_at"],
            status=data["status"],
            creator_decision=data.get("creator_decision"),
        )

    def list_pending_proposals(self) -> list[SkillProposal]:
        """列出待审批的 skill 提案"""
        proposals = []
        if not self.proposals_dir.exists():
            return proposals
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
    # 生成 Skill 代码
    # ──────────────────────────────────────────

    def generate_skill_code(self, spec: SkillSpec) -> str:
        """
        根据规格生成 SKILL.md 内容

        这是 Darwin 自己写的 skill，会给 creator 审批。
        实际生成由 LLM 调用完成，这里提供模板。
        """
        # 简单模板：实际使用时由 LLM 生成完整内容
        template = f"""# {spec.name}

> {spec.description}

## 触发条件

触发条件：`{spec.trigger}`

## 实现步骤

"""
        for i, step in enumerate(spec.steps, 1):
            template += f"{i}. {step}\n"

        template += f"""
## 需要用到的工具

{', '.join(spec.tools_needed)}

## 潜在问题

{spec.potential_issues}

---

*此 skill 由 Darwin 自动生成，审批通过后生效*
"""

        return template

    def _generate_skill_file_path(self, skill_name: str) -> Path:
        """生成 skill 文件路径"""
        safe_name = re.sub(r'[^a-z0-9\-]', '-', skill_name.lower())
        return self.skill_dir / f"{safe_name}" / "SKILL.md"

    # ──────────────────────────────────────────
    # 审批流程
    # ──────────────────────────────────────────

    def approve(self, proposal_id: str, creator_decision: str = "approved") -> bool:
        """Creator 审批 skill 提案"""
        proposal = self.load_proposal(proposal_id)

        if creator_decision != "approved":
            proposal.status = creator_decision
            proposal.creator_decision = creator_decision
            self._save_proposal(proposal)
            logger.info(f"Skill proposal {proposal_id}: {creator_decision}")
            return False

        # 写入 skill 文件
        return self._apply_proposal(proposal)

    def reject(self, proposal_id: str, reason: str = "") -> bool:
        """拒绝提案"""
        proposal = self.load_proposal(proposal_id)
        proposal.status = "rejected"
        proposal.creator_decision = f"rejected: {reason}"
        self._save_proposal(proposal)
        logger.info(f"Skill proposal rejected: {proposal_id}")
        return True

    def _apply_proposal(self, proposal: SkillProposal) -> bool:
        """应用提案：写入 skill 文件"""
        try:
            skill_path = self._generate_skill_file_path(proposal.spec.name)
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(proposal.skill_code)

            proposal.status = "applied"
            proposal.creator_decision = "approved"
            self._save_proposal(proposal)

            # 记录日志
            log_path = self.darwin_root / "evolution" / "logs" / "skill_changes.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a") as f:
                f.write(json.dumps({
                    "proposal_id": proposal.id,
                    "skill_name": proposal.spec.name,
                    "applied_at": datetime.now().isoformat(),
                }, ensure_ascii=False) + "\n")

            logger.info(f"Skill applied: {proposal.spec.name} at {skill_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply skill proposal: {e}")
            return False

    def list_approved_skills(self) -> list[str]:
        """列出已批准的 skills"""
        if not self.skill_dir.exists():
            return []
        skills = []
        for d in self.skill_dir.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                skills.append(d.name)
        return skills