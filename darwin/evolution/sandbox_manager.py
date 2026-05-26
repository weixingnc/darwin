"""SandboxManager — Darwin 沙箱环境管理

负责创建和管理隔离的测试环境。
所有进化变更必须先在沙箱中验证，才能进入正式环境。
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SandboxInfo:
    """沙箱信息"""
    sandbox_id: str
    sandbox_path: Path
    created_at: str
    parent_path: Path              # 原始 production 路径
    status: str = "created"        # created / running / passed / failed / discarded
    change_summary: str = ""
    test_result: Optional[str] = None  # test output or error


class SandboxManager:
    """
    沙箱管理器

    核心职责：
    1. 创建隔离的沙箱副本（只复制必要文件）
    2. 在沙箱中应用变更
    3. 管理沙箱生命周期
    4. 清理沙箱

    沙箱目录结构：
    /path/to/
      darwin_production/     ← 正式环境
      darwin_sandbox/        ← 沙箱环境
        sandbox_20260527_001234/   ← 某个沙箱实例
    """

    SANDBOX_DIR = ".sandbox"
    SANDBOX_PREFIX = "sandbox_"

    def __init__(self, darwin_root: Path):
        self.darwin_root = darwin_root.resolve()
        self.sandbox_base = self.darwin_root / self.SANDBOX_DIR
        self.sandbox_base.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # 生命周期
    # ──────────────────────────────────────────

    def create_sandbox(self, change_summary: str = "") -> SandboxInfo:
        """
        创建沙箱

        复制 Darwin 的核心文件到沙箱目录：
        - darwin/ 目录（核心代码）
        - SOUL.md（灵魂定义）
        - tests/（测试套件）
        - pyproject.toml（依赖）

        排除运行时文件：
        - evolution/checkpoints/
        - evolution/proposals/
        - evolution/metrics/
        - evolution/fixes/
        """
        sandbox_id = f"{self.SANDBOX_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sandbox_path = self.sandbox_base / sandbox_id

        logger.info(f"Creating sandbox: {sandbox_path}")

        # 创建沙箱目录
        sandbox_path.mkdir(parents=True, exist_ok=True)

        # 需要复制的目录/文件
        copy_items = [
            "darwin",
            "SOUL.md",
            "tests",
            "pyproject.toml",
        ]

        # 需要排除的模式
        exclude_patterns = {
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".git",
            "evolution/checkpoints",
            "evolution/proposals",
            "evolution/metrics",
            "evolution/fixes",
        }

        # 复制文件
        for item in copy_items:
            src = self.darwin_root / item
            if src.exists():
                dest = sandbox_path / item

                if src.is_dir():
                    shutil.copytree(
                        src,
                        dest,
                        ignore=shutil.ignore_patterns(*exclude_patterns),
                    )
                else:
                    shutil.copy2(src, dest)

                logger.debug(f"Copied: {item}")

        # 标记文件：这是沙箱，不是 production
        (sandbox_path / ".sandbox_marker").write_text(
            f"sandbox_id={sandbox_id}\ncreated_at={datetime.now().isoformat()}\n"
        )

        info = SandboxInfo(
            sandbox_id=sandbox_id,
            sandbox_path=sandbox_path,
            created_at=datetime.now().isoformat(),
            parent_path=self.darwin_root,
            status="created",
            change_summary=change_summary,
        )

        self._save_sandbox_info(info)

        logger.info(f"Sandbox created: {sandbox_id}")
        return info

    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """
        销毁沙箱

        Args:
            sandbox_id: 沙箱 ID

        Returns:
            True if destroyed, False if not found
        """
        sandbox_path = self.sandbox_base / sandbox_id

        if not sandbox_path.exists():
            logger.warning(f"Sandbox not found: {sandbox_id}")
            return False

        shutil.rmtree(sandbox_path)
        logger.info(f"Sandbox destroyed: {sandbox_id}")

        # 更新 info 文件
        info_file = self.sandbox_base / f"{sandbox_id}.info.json"
        if info_file.exists():
            data = json.loads(info_file.read_text())
            data["status"] = "discarded"
            info_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

        return True

    # ──────────────────────────────────────────
    # 变更应用
    # ──────────────────────────────────────────

    def apply_soul_change(self, sandbox_id: str, new_soul_content: str) -> bool:
        """
        在沙箱中应用 SOUL 变更

        Args:
            sandbox_id: 沙箱 ID
            new_soul_content: 新的 SOUL.md 内容

        Returns:
            True if applied successfully
        """
        sandbox_path = self.sandbox_base / sandbox_id
        soul_file = sandbox_path / "SOUL.md"

        if not soul_file.exists():
            logger.error(f"SOUL.md not found in sandbox: {sandbox_id}")
            return False

        soul_file.write_text(new_soul_content)
        logger.info(f"SOUL change applied in sandbox: {sandbox_id}")

        self._update_sandbox_status(sandbox_id, "soul_modified")

        return True

    def apply_skill(self, sandbox_id: str, skill_name: str, skill_content: str) -> bool:
        """
        在沙箱中应用新 skill

        Args:
            sandbox_id: 沙箱 ID
            skill_name: skill 名称
            skill_content: skill 文件内容

        Returns:
            True if applied successfully
        """
        sandbox_path = self.sandbox_base / sandbox_id
        skill_dir = sandbox_path / "darwin" / "agent" / "skills"

        if not skill_dir.exists():
            skill_dir = sandbox_path / "skills"

        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / f"{skill_name}.md"

        skill_file.write_text(skill_content)
        logger.info(f"Skill '{skill_name}' applied in sandbox: {sandbox_id}")

        self._update_sandbox_status(sandbox_id, "skill_added")

        return True

    def apply_code_change(self, sandbox_id: str, file_path: str, new_content: str) -> bool:
        """
        在沙箱中应用代码变更

        Args:
            sandbox_id: 沙箱 ID
            file_path: 相对于 darwin_root 的文件路径
            new_content: 新的文件内容

        Returns:
            True if applied successfully
        """
        sandbox_path = self.sandbox_base / sandbox_id
        target_file = sandbox_path / file_path

        # 安全检查：不允许修改沙箱标记文件
        if ".sandbox_marker" in str(target_file):
            logger.error("Cannot modify sandbox marker file")
            return False

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(new_content)

        logger.info(f"Code change applied in sandbox: {sandbox_id}/{file_path}")
        self._update_sandbox_status(sandbox_id, "code_modified")

        return True

    # ──────────────────────────────────────────
    # 查询
    # ──────────────────────────────────────────

    def list_sandboxes(self, include_discarded: bool = False) -> list[SandboxInfo]:
        """列出所有沙箱"""
        sandboxes = []

        for info_file in self.sandbox_base.glob("*.info.json"):
            data = json.loads(info_file.read_text())
            if not include_discarded and data.get("status") == "discarded":
                continue
            sandboxes.append(SandboxInfo(**data))

        return sorted(sandboxes, key=lambda s: s.created_at, reverse=True)

    def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """获取沙箱信息"""
        info_file = self.sandbox_base / f"{sandbox_id}.info.json"
        if not info_file.exists():
            return None

        data = json.loads(info_file.read_text())
        return SandboxInfo(
            sandbox_id=data["sandbox_id"],
            sandbox_path=Path(data["sandbox_path"]),
            created_at=data["created_at"],
            parent_path=Path(data["parent_path"]),
            status=data.get("status", "created"),
            change_summary=data.get("change_summary", ""),
            test_result=data.get("test_result"),
        )

    # ──────────────────────────────────────────
    # 内部方法
    # ──────────────────────────────────────────

    def _save_sandbox_info(self, info: SandboxInfo):
        """保存沙箱信息到文件"""
        info_file = self.sandbox_base / f"{info.sandbox_id}.info.json"
        data = {
            "sandbox_id": info.sandbox_id,
            "sandbox_path": str(info.sandbox_path),
            "created_at": info.created_at,
            "parent_path": str(info.parent_path),
            "status": info.status,
            "change_summary": info.change_summary,
            "test_result": info.test_result,
        }
        info_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _update_sandbox_status(self, sandbox_id: str, status: str, test_result: str = None):
        """更新沙箱状态"""
        info = self.get_sandbox(sandbox_id)
        if info:
            info.status = status
            if test_result:
                info.test_result = test_result
            self._save_sandbox_info(info)