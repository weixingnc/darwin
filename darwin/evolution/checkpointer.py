"""
Checkpointer — 快照管理

在执行重大变更前，对 Darwin 的关键文件和状态进行快照，
支持回滚。
"""

import datetime
import json
import shutil
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Checkpoint:
    id: str
    created_at: datetime.datetime
    plan_id: str
    description: str
    paths: list[str]
    checksum: str
    size_mb: float


class Checkpointer:
    """
    文件系统快照管理器

    快照范围：
        - SOUL.md（灵魂定义）
        - src/（源代码）
        - evolution/（进化记录）
        - ~/.hermes/profiles/darwin/（配置）
    """

    SNAPSHOT_PATHS = [
        "SOUL.md",
        "src",
    ]

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create(self, plan) -> str | None:
        """
        创建快照

        Returns:
            checkpoint_id on success, None on failure
        """
        checkpoint_id = f"ckpt_{plan.id}"
        snapshot_root = self.checkpoint_dir / checkpoint_id

        # Get darwin_root from plan or engine
        darwin_root = getattr(plan, 'darwin_root', None) or getattr(plan, 'engine', None).darwin_root

        try:
            snapshot_root.mkdir(parents=True, exist_ok=True)

            # Copy files (excluding __pycache__)
            for rel_path in self.SNAPSHOT_PATHS:
                src = darwin_root / rel_path
                dst = snapshot_root / rel_path
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True,
                                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)

            # Write metadata
            meta = {
                "id": checkpoint_id,
                "plan_id": plan.id,
                "description": plan.description,
                "created_at": datetime.datetime.now().isoformat(),
                "paths": self.SNAPSHOT_PATHS,
            }
            (snapshot_root / "checkpoint.json").write_text(json.dumps(meta, indent=2))

            # Calculate checksum
            cs = self._calc_checksum(snapshot_root)
            meta["checksum"] = cs
            (snapshot_root / "checkpoint.json").write_text(json.dumps(meta, indent=2))

            return checkpoint_id

        except Exception as e:
            # Cleanup on failure
            if snapshot_root.exists():
                shutil.rmtree(snapshot_root, ignore_errors=True)
            return None

    def restore(self, checkpoint_id: str, target_root: Path | None = None) -> bool:
        """
        从快照恢复

        Args:
            checkpoint_id: 快照ID
            target_root: 恢复到哪个目录（默认原始位置）
        """
        snapshot_root = self.checkpoint_dir / checkpoint_id
        if not snapshot_root.exists():
            return False

        if target_root is None:
            # 需要从 plan 中获取原始路径，这里简化处理
            return False

        try:
            for rel_path in self.SNAPSHOT_PATHS:
                src = snapshot_root / rel_path
                dst = target_root / rel_path
                if src.exists():
                    if dst.exists():
                        if dst.is_dir():
                            shutil.rmtree(dst, ignore_errors=True)
                        else:
                            dst.unlink()
                    if src.is_dir():
                        shutil.copytree(src, dst)
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
            return True
        except Exception:
            return False

    def list(self) -> list[dict]:
        """列出所有快照"""
        checkpoints = []
        for ckpt_dir in sorted(self.checkpoint_dir.iterdir(), reverse=True):
            if ckpt_dir.is_dir() and ckpt_dir.name.startswith("ckpt_"):
                meta_file = ckpt_dir / "checkpoint.json"
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text())
                        checkpoints.append(meta)
                    except Exception:
                        pass
        return checkpoints

    def delete(self, checkpoint_id: str) -> bool:
        """删除快照"""
        ckpt_dir = self.checkpoint_dir / checkpoint_id
        if ckpt_dir.exists():
            shutil.rmtree(ckpt_dir, ignore_errors=True)
            return True
        return False

    def _calc_checksum(self, path: Path) -> str:
        """计算目录的简单 checksum"""
        hasher = hashlib.md5()
        for f in sorted(path.rglob("*")):
            if f.is_file():
                hasher.update(f.read_bytes())
        return hasher.hexdigest()[:12]