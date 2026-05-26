"""
Committer — 提交/回滚管理

当评估通过后，正式提交变更到 Darwin 的工作区。
评估失败则回滚。
"""

import datetime
import shutil
from pathlib import Path


class Committer:
    """
    变更提交管理器

    职责：
        - 评估通过后，将变更从临时目录提交到工作区
        - 记录变更日志
        - 提供回滚接口
    """

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root)
        self.change_log = self.darwin_root / "evolution" / "logs" / "change_log.jsonl"

    def commit(self, plan) -> bool:
        """
        正式提交变更

        Returns:
            True on success
        """
        try:
            # Record in change log
            self._log_commit(plan)

            # Update baseline if needed
            self._update_baseline(plan)

            return True
        except Exception as e:
            return False

    def rollback(self, plan) -> bool:
        """
        回滚变更（从快照恢复）

        注意：实际恢复逻辑在 Checkpointer.restore()，这里只做记录
        """
        self._log_rollback(plan)
        return True

    def _log_commit(self, plan):
        """记录提交到日志"""
        from .checkpointer import Checkpointer  # lazy import to avoid circular

        log_entry = {
            "type": "commit",
            "plan_id": plan.id,
            "description": plan.description,
            "changes": plan.changes,
            "checkpoint_id": plan.checkpoint_id,
            "eval_report": plan.eval_report,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self.change_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.change_log, "a") as f:
            f.write(__import__("json").dumps(log_entry) + "\n")

    def _log_rollback(self, plan):
        """记录回滚到日志"""
        log_entry = {
            "type": "rollback",
            "plan_id": plan.id,
            "description": plan.description,
            "checkpoint_id": plan.checkpoint_id,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self.change_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.change_log, "a") as f:
            f.write(__import__("json").dumps(log_entry) + "\n")

    def _update_baseline(self, plan):
        """评估通过后，更新基线"""
        # This will be handled by Evaluator._save_baseline
        pass

    def get_change_history(self, limit: int = 50) -> list[dict]:
        """获取变更历史"""
        if not self.change_log.exists():
            return []

        entries = []
        try:
            with open(self.change_log) as f:
                for line in f:
                    if line.strip():
                        import json as _json
                        entries.append(_json.loads(line))
        except Exception:
            pass

        return entries[-limit:]