"""Promoter — Darwin 沙箱晋升器

负责将沙箱中验证通过的变更，合并到正式环境（production）。
如果测试失败，则丢弃沙箱。
"""

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PromotionResult:
    """晋升结果"""
    sandbox_id: str
    success: bool
    promoted_files: list[str]
    skipped_files: list[str]
    error: Optional[str] = None
    promoted_at: Optional[str] = None


class Promoter:
    """
    沙箱晋升器

    核心职责：
    1. 将沙箱中验证通过的变更应用到 production
    2. 记录晋升历史
    3. 清理沙箱

    晋升原则：
    - 只晋升测试通过的沙箱
    - 保留变更记录（audit trail）
    - 晋升后自动清理沙箱
    """

    PROMOTION_LOG = "evolution/promotions.jsonl"

    def __init__(self, darwin_root: Path):
        self.darwin_root = darwin_root.resolve()
        self.promotion_log = self.darwin_root / self.PROMOTION_LOG
        self.promotion_log.parent.mkdir(parents=True, exist_ok=True)

    def promote(self, sandbox_id: str, force: bool = False) -> PromotionResult:
        """
        将沙箱晋升到 production

        Args:
            sandbox_id: 沙箱 ID
            force: 是否强制晋升（跳过测试验证）

        Returns:
            PromotionResult: 晋升结果
        """
        from .sandbox_manager import SandboxManager

        sandbox_mgr = SandboxManager(self.darwin_root)
        sandbox_info = sandbox_mgr.get_sandbox(sandbox_id)

        if not sandbox_info:
            return PromotionResult(
                sandbox_id=sandbox_id,
                success=False,
                promoted_files=[],
                skipped_files=[],
                error=f"沙箱不存在: {sandbox_id}",
            )

        sandbox_path = sandbox_info.sandbox_path

        # 安全检查：如果不是 passed 状态，除非 force 否则不允许晋升
        if sandbox_info.status != "passed" and not force:
            return PromotionResult(
                sandbox_id=sandbox_id,
                success=False,
                promoted_files=[],
                skipped_files=[],
                error=f"沙箱状态为 {sandbox_info.status}，需要测试通过才能晋升。强制晋升使用 --force",
            )

        logger.info(f"Promoting sandbox {sandbox_id} to production")

        promoted_files = []
        skipped_files = []

        try:
            # 1. 复制 darwin/ 目录中的变更
            sandbox_darwin = sandbox_path / "darwin"
            if sandbox_darwin.exists():
                prod_darwin = self.darwin_root / "darwin"

                for item in sandbox_darwin.iterdir():
                    if item.name in ("__pycache__", ".git", ".sandbox_marker"):
                        continue

                    dest = prod_darwin / item.name

                    # 备份 production 中的旧版本
                    if dest.exists() and not dest.name.startswith("."):
                        backup_path = self.darwin_root / "evolution" / "backups" / f"{item.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(dest, backup_path)
                        logger.debug(f"Backed up: {item.name} -> {backup_path}")

                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)

                    promoted_files.append(f"darwin/{item.name}")

            # 2. 复制 SOUL.md
            sandbox_soul = sandbox_path / "SOUL.md"
            if sandbox_soul.exists():
                prod_soul = self.darwin_root / "SOUL.md"

                # 备份旧版本
                if prod_soul.exists():
                    backup_path = self.darwin_root / "evolution" / "backups" / f"SOUL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(prod_soul, backup_path)

                shutil.copy2(sandbox_soul, prod_soul)
                promoted_files.append("SOUL.md")

            # 3. 记录晋升日志
            self._log_promotion(sandbox_id, promoted_files)

            # 4. 清理沙箱
            sandbox_mgr.destroy_sandbox(sandbox_id)

            result = PromotionResult(
                sandbox_id=sandbox_id,
                success=True,
                promoted_files=promoted_files,
                skipped_files=skipped_files,
                promoted_at=datetime.now().isoformat(),
            )

            logger.info(f"Sandbox {sandbox_id} promoted successfully: {promoted_files}")

            return result

        except Exception as e:
            logger.error(f"Promotion failed: {e}")
            return PromotionResult(
                sandbox_id=sandbox_id,
                success=False,
                promoted_files=promoted_files,
                skipped_files=skipped_files,
                error=str(e),
            )

    def discard(self, sandbox_id: str) -> bool:
        """
        丢弃沙箱（不晋升）

        Args:
            sandbox_id: 沙箱 ID

        Returns:
            True if discarded successfully
        """
        from .sandbox_manager import SandboxManager

        sandbox_mgr = SandboxManager(self.darwin_root)

        # 记录丢弃日志
        self._log_discard(sandbox_id)

        # 清理沙箱
        return sandbox_mgr.destroy_sandbox(sandbox_id)

    def get_promotion_history(self, limit: int = 50) -> list[dict]:
        """获取晋升历史"""
        if not self.promotion_log.exists():
            return []

        history = []
        with open(self.promotion_log) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    history.append(json.loads(line))
                except Exception:
                    continue

        return history[-limit:]

    def _log_promotion(self, sandbox_id: str, promoted_files: list[str]):
        """记录晋升日志"""
        entry = {
            "type": "promotion",
            "sandbox_id": sandbox_id,
            "promoted_files": promoted_files,
            "promoted_at": datetime.now().isoformat(),
        }

        with open(self.promotion_log, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _log_discard(self, sandbox_id: str):
        """记录丢弃日志"""
        entry = {
            "type": "discard",
            "sandbox_id": sandbox_id,
            "discarded_at": datetime.now().isoformat(),
        }

        with open(self.promotion_log, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")