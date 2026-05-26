"""
Evolution Engine — 主协调器

管理 Darwin 的自我进化流程：
    1. 快照（checkpointer）
    2. 评估（evaluator）
    3. 提交（committer）
"""

import datetime
import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .checkpointer import Checkpointer
from .evaluator import Evaluator
from .committer import Committer

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    IDLE = "idle"
    SNAPSHOT = "snapshot"
    EVALUATE = "evaluate"
    COMMIT = "commit"
    ROLLBACK = "rollback"
    DONE = "done"


@dataclass
class EvolutionPlan:
    """一次进化计划"""
    id: str
    description: str
    changes: list[str] = field(default_factory=list)
    phase: EvolutionPhase = EvolutionPhase.IDLE
    checkpoint_id: str | None = None
    eval_report: dict | None = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    engine: "EvolutionEngine" = field(default=None, repr=False)
    darwin_root: Path = field(default=None, repr=False)


@dataclass
class EvolutionResult:
    """进化结果"""
    plan_id: str
    success: bool
    phase_reached: EvolutionPhase
    message: str
    checkpoint_id: str | None = None
    eval_report: dict | None = None


class EvolutionEngine:
    """
    Darwin 进化引擎主类

    使用方式：
        engine = EvolutionEngine(darwin_root=Path("/home/weixing/darwin"))
        plan = engine.create_plan("学习使用 pytorch", ["新增 skill: pytorch-trainer"])
        result = engine.execute(plan)
    """

    def __init__(self, darwin_root: Path, checkpointer: Checkpointer | None = None,
                 evaluator: Evaluator | None = None, committer: Committer | None = None):
        self.darwin_root = Path(darwin_root)
        self.checkpointer = checkpointer or Checkpointer(self.darwin_root / "evolution" / "checkpoints")
        self.evaluator = evaluator or Evaluator(self.darwin_root / "evolution" / "tests")
        self.committer = committer or Committer(self.darwin_root)
        self.current_plan: EvolutionPlan | None = None
        self.history: list[EvolutionPlan] = []

    def create_plan(self, description: str, changes: list[str]) -> EvolutionPlan:
        """创建一个新的进化计划"""
        plan_id = f"evo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan = EvolutionPlan(
            id=plan_id,
            description=description,
            changes=changes,
            engine=self,  # Attach engine reference
            darwin_root=self.darwin_root  # Also store darwin_root directly
        )
        logger.info(f"Created evolution plan: {plan_id} — {description}")
        return plan

    def execute(self, plan: EvolutionPlan) -> EvolutionResult:
        """
        执行一次完整的进化流程

        流程：快照 → 评估 → (通过则提交) | (失败则回滚)
        """
        self.current_plan = plan

        # Phase 1: Snapshot
        logger.info(f"[{plan.id}] Phase 1: Creating snapshot")
        plan.phase = EvolutionPhase.SNAPSHOT
        checkpoint_id = self.checkpointer.create(plan)
        if not checkpoint_id:
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.SNAPSHOT,
                message="快照失败，无法继续"
            )
        plan.checkpoint_id = checkpoint_id

        # Phase 2: Apply changes (simulate execution)
        logger.info(f"[{plan.id}] Phase 2: Applying changes")
        try:
            self._apply_changes(plan.changes)
        except Exception as e:
            logger.error(f"[{plan.id}] Change application failed: {e}")
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.SNAPSHOT,
                message=f"变更失败: {e}",
                checkpoint_id=checkpoint_id
            )

        # Phase 3: Evaluate
        logger.info(f"[{plan.id}] Phase 3: Evaluating")
        plan.phase = EvolutionPhase.EVALUATE
        eval_report = self.evaluator.run(plan)
        plan.eval_report = eval_report

        if not eval_report.get("passed", False):
            logger.warning(f"[{plan.id}] Evaluation failed, rolling back")
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.EVALUATE,
                message=f"评估未通过: {eval_report.get('reason', '未知原因')}",
                checkpoint_id=checkpoint_id,
                eval_report=eval_report
            )

        # Phase 4: Commit
        logger.info(f"[{plan.id}] Phase 4: Committing")
        plan.phase = EvolutionPhase.COMMIT
        commit_ok = self.committer.commit(plan)
        if not commit_ok:
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.COMMIT,
                message="提交失败，已回滚",
                checkpoint_id=checkpoint_id,
                eval_report=eval_report
            )

        plan.phase = EvolutionPhase.DONE
        self.history.append(plan)
        logger.info(f"[{plan.id}] Evolution completed successfully")

        return EvolutionResult(
            plan_id=plan.id,
            success=True,
            phase_reached=EvolutionPhase.DONE,
            message="进化完成",
            checkpoint_id=checkpoint_id,
            eval_report=eval_report
        )

    def _apply_changes(self, changes: list[str]):
        """应用变更（这里只是记录，实际执行需要更复杂的逻辑）"""
        log_file = self.darwin_root / "evolution" / "logs" / f"{self.current_plan.id}_changes.txt"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("\n".join(changes))
        logger.info(f"Changes logged to {log_file}")

    def _rollback(self, plan: EvolutionPlan):
        """回滚到快照"""
        plan.phase = EvolutionPhase.ROLLBACK
        if plan.checkpoint_id:
            self.checkpointer.restore(plan.checkpoint_id)
        plan.phase = EvolutionPhase.DONE

    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "current_plan": {
                "id": self.current_plan.id,
                "phase": self.current_plan.phase.value,
                "description": self.current_plan.description
            } if self.current_plan else None,
            "history_count": len(self.history),
        }

    def list_checkpoints(self) -> list[dict]:
        """列出所有快照"""
        return self.checkpointer.list()

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """恢复到指定快照"""
        return self.checkpointer.restore(checkpoint_id)