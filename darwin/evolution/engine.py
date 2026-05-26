"""
Evolution Engine — 主协调器

管理 Darwin 的自我进化流程：
    1. 快照（checkpointer）
    2. 沙箱验证（sandbox_manager + test_runner + promoter）
    3. 提交（committer）

所有进化都必须经过沙箱验证，确保安全后晋升到 production。
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
from .sandbox_manager import SandboxManager
from .test_runner import TestRunner
from .promoter import Promoter

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    IDLE = "idle"
    SNAPSHOT = "snapshot"
    SANDBOX_CREATE = "sandbox_create"
    SANDBOX_TEST = "sandbox_test"
    SANDBOX_PROMOTE = "sandbox_promote"
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
    sandbox_id: str | None = None
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
    sandbox_id: str | None = None
    eval_report: dict | None = None


class EvolutionEngine:
    """
    Darwin 进化引擎主类

    使用方式：
        engine = EvolutionEngine(darwin_root=Path("/home/weixing/darwin"))
        plan = engine.create_plan("学习使用 pytorch", ["新增 skill: pytorch-trainer"])
        result = engine.execute(plan)

    进化流程（沙箱验证模式）：
        1. 创建快照
        2. 创建沙箱
        3. 在沙箱中应用变更
        4. 在沙箱中运行测试
        5. 测试通过 → 晋升到 production
        6. 测试失败 → 丢弃沙箱，回滚到快照
    """

    def __init__(self, darwin_root: Path, checkpointer: Checkpointer | None = None,
                 evaluator: Evaluator | None = None, committer: Committer | None = None,
                 sandbox_manager: SandboxManager | None = None,
                 test_runner: TestRunner | None = None,
                 promoter: Promoter | None = None):
        self.darwin_root = Path(darwin_root)
        self.checkpointer = checkpointer or Checkpointer(self.darwin_root / "evolution" / "checkpoints")
        self.evaluator = evaluator or Evaluator(self.darwin_root / "evolution" / "tests")
        self.committer = committer or Committer(self.darwin_root)
        # Sandbox 模块
        self.sandbox_manager = sandbox_manager or SandboxManager(self.darwin_root)
        self.test_runner = test_runner or TestRunner(self.darwin_root)
        self.promoter = promoter or Promoter(self.darwin_root)
        self.current_plan: EvolutionPlan | None = None
        self.history: list[EvolutionPlan] = []

    def create_plan(self, description: str, changes: list[str]) -> EvolutionPlan:
        """创建一个新的进化计划"""
        plan_id = f"evo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan = EvolutionPlan(
            id=plan_id,
            description=description,
            changes=changes,
            engine=self,
            darwin_root=self.darwin_root
        )
        logger.info(f"Created evolution plan: {plan_id} — {description}")
        return plan

    def execute(self, plan: EvolutionPlan) -> EvolutionResult:
        """
        执行一次完整的进化流程（沙箱验证模式）

        流程：快照 → 创建沙箱 → 沙箱测试 → 晋升/丢弃 → 评估 → 提交
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

        # Phase 2: Create sandbox
        logger.info(f"[{plan.id}] Phase 2: Creating sandbox")
        plan.phase = EvolutionPhase.SANDBOX_CREATE
        sandbox_info = self.sandbox_manager.create_sandbox(
            plan.description,
            plan.changes,
        )
        if not sandbox_info:
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.SANDBOX_CREATE,
                message="沙箱创建失败，无法继续",
                checkpoint_id=checkpoint_id
            )
        plan.sandbox_id = sandbox_info.sandbox_id
        sandbox_path = sandbox_info.sandbox_path

        # Phase 3: Apply changes in sandbox
        logger.info(f"[{plan.id}] Phase 3: Applying changes in sandbox")
        try:
            self._apply_changes_in_sandbox(plan.changes, sandbox_path)
        except Exception as e:
            logger.error(f"[{plan.id}] Change application in sandbox failed: {e}")
            self.sandbox_manager.destroy_sandbox(sandbox_info.sandbox_id)
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.SANDBOX_TEST,
                message=f"变更失败: {e}",
                checkpoint_id=checkpoint_id,
                sandbox_id=sandbox_info.sandbox_id
            )

        # Phase 4: Run tests in sandbox
        logger.info(f"[{plan.id}] Phase 4: Running tests in sandbox")
        plan.phase = EvolutionPhase.SANDBOX_TEST
        test_result = self.test_runner.run_tests_in_sandbox(sandbox_path)

        if not test_result.passed:
            logger.warning(f"[{plan.id}] Tests failed in sandbox, discarding sandbox")
            self.sandbox_manager.destroy_sandbox(sandbox_info.sandbox_id)
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.SANDBOX_TEST,
                message=f"沙箱测试未通过: {test_result.failed_tests} 个测试失败",
                checkpoint_id=checkpoint_id,
                sandbox_id=sandbox_info.sandbox_id,
                eval_report={"test_result": test_result.__dict__}
            )

        # Phase 5: Promote to production (sandbox passed)
        logger.info(f"[{plan.id}] Phase 5: Promoting sandbox to production")
        plan.phase = EvolutionPhase.SANDBOX_PROMOTE
        promotion_result = self.promoter.promote(sandbox_info.sandbox_id)

        if not promotion_result.success:
            logger.error(f"[{plan.id}] Promotion failed: {promotion_result.error}")
            self._rollback(plan)
            return EvolutionResult(
                plan_id=plan.id,
                success=False,
                phase_reached=EvolutionPhase.SANDBOX_PROMOTE,
                message=f"晋升失败: {promotion_result.error}",
                checkpoint_id=checkpoint_id,
                sandbox_id=sandbox_info.sandbox_id
            )

        logger.info(
            f"[{plan.id}] Sandbox promoted successfully: "
            f"{promotion_result.promoted_files}"
        )

        # Phase 6: Evaluate (final check)
        logger.info(f"[{plan.id}] Phase 6: Final evaluation")
        plan.phase = EvolutionPhase.EVALUATE
        eval_report = self.evaluator.run(plan)
        plan.eval_report = eval_report

        if not eval_report.get("passed", False):
            # 注意：这里不应该回滚，因为已经晋升到 production 了
            # 只是记录警告
            logger.warning(
                f"[{plan.id}] Evaluation warning: {eval_report.get('reason', '未知原因')}"
            )

        # Phase 7: Commit
        logger.info(f"[{plan.id}] Phase 7: Committing")
        plan.phase = EvolutionPhase.COMMIT
        commit_ok = self.committer.commit(plan)
        if not commit_ok:
            # 晋升已经完成，提交失败不应该回滚 promotion
            # 只是记录错误
            logger.error(f"[{plan.id}] Commit failed but promotion succeeded")

        plan.phase = EvolutionPhase.DONE
        self.history.append(plan)
        logger.info(f"[{plan.id}] Evolution completed successfully")

        return EvolutionResult(
            plan_id=plan.id,
            success=True,
            phase_reached=EvolutionPhase.DONE,
            message="进化完成（沙箱验证通过）",
            checkpoint_id=checkpoint_id,
            sandbox_id=sandbox_info.sandbox_id,
            eval_report=eval_report
        )

    def execute_simple(self, plan: EvolutionPlan) -> EvolutionResult:
        """
        执行进化（简化模式，跳过沙箱，直接应用变更）

        适用于紧急修复或 creator 明确授权的场景。
        使用前请确保理解风险。
        """
        self.current_plan = plan

        # Phase 1: Snapshot
        logger.info(f"[{plan.id}] Simple mode: Creating snapshot")
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

        # Phase 2: Apply changes directly
        logger.info(f"[{plan.id}] Simple mode: Applying changes directly")
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
        logger.info(f"[{plan.id}] Simple mode: Evaluating")
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
        logger.info(f"[{plan.id}] Simple mode: Committing")
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
        logger.info(f"[{plan.id}] Simple evolution completed successfully")

        return EvolutionResult(
            plan_id=plan.id,
            success=True,
            phase_reached=EvolutionPhase.DONE,
            message="进化完成（简化模式）",
            checkpoint_id=checkpoint_id,
            eval_report=eval_report
        )

    def _apply_changes_in_sandbox(self, changes: list[str], sandbox_path: Path):
        """在沙箱中应用变更"""
        # 将变更记录到沙箱的 evolution/logs 目录
        log_dir = sandbox_path / "evolution" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{self.current_plan.id}_changes.txt"
        log_file.write_text("\n".join(changes))
        logger.info(f"Changes logged to sandbox: {log_file}")

    def _apply_changes(self, changes: list[str]):
        """应用变更（直接模式）"""
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
            "sandbox_count": len(self.sandbox_manager.list_sandboxes()),
        }

    def list_checkpoints(self) -> list[dict]:
        """列出所有快照"""
        return self.checkpointer.list()

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """恢复到指定快照"""
        return self.checkpointer.restore(checkpoint_id)