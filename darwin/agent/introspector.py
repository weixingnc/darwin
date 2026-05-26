"""Introspector — Darwin 的自省引擎

让 Darwin 能够感知自身的状态、能力和历史。
所有"看自己"的能力都集中在这里。
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SoulSnapshot:
    """灵魂快照"""
    identity: str
    autonomy: bool
    evolution: bool
    consistency: bool
    caution: bool
    can_read_files: bool
    can_write_files: bool
    can_execute_commands: bool
    can_install_packages: bool
    can_modify_system: bool
    has_direct_internet: bool
    creator: str
    version: str
    updated_at: str
    raw_md: str = ""


@dataclass
class EvolutionRecord:
    """进化记录"""
    plan_id: str
    description: str
    changes: list[str]
    phase: str
    checkpoint_id: Optional[str]
    eval_score: Optional[float]
    eval_passed: bool
    created_at: str
    committed_at: Optional[str] = None


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    duration_ms: Optional[float] = None
    error: Optional[str] = None


@dataclass
class DarwinSelfImage:
    """
    Darwin 的自我镜像 — 当前状态的完整快照
    用于给 Darwin 自己看，也用于给 creator 诊断
    """
    soul: SoulSnapshot
    evolution_history: list[EvolutionRecord]
    recent_tests: list[TestResult]
    checkpoint_count: int
    darwin_root: str
    version: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class Introspector:
    """
    Darwin 自省引擎

    提供"看自己"的能力：
    - 读 SOUL.md → 灵魂状态
    - 读 change_log → 进化历史
    - 读测试结果 → 能力状态
    - 汇总 → 自我镜像
    """

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root)
        self.soul_file = self.darwin_root / "SOUL.md"
        self.evolution_dir = self.darwin_root / "evolution"
        self.checkpoint_dir = self.evolution_dir / "checkpoints"
        self.log_file = self.evolution_dir / "logs" / "change_log.jsonl"
        self.tests_dir = self.darwin_root / "tests"

    # ──────────────────────────────────────────
    # 感知层：读取各部分信息
    # ──────────────────────────────────────────

    def read_soul(self) -> SoulSnapshot:
        """读取灵魂定义"""
        if not self.soul_file.exists():
            return self._empty_soul()

        content = self.soul_file.read_text()
        return self._parse_soul(content)

    def _parse_soul(self, content: str) -> SoulSnapshot:
        """解析 SOUL.md"""
        lines = content.split("\n")
        snapshot = self._empty_soul()
        snapshot.raw_md = content

        # 简单解析：提取关键字段
        in_capabilities = False
        for line in lines:
            l = line.strip()
            if l.startswith("#"):
                if "身份" in l or "identity" in l.lower():
                    snapshot.identity = "（见 SOUL.md）"
            elif "自主性" in l and ":" not in l:
                pass
            elif "创建者" in l or "creator" in l.lower():
                if ":" in l:
                    snapshot.creator = l.split(":", 1)[1].strip()
            elif "版本" in l and "v" in l:
                parts = l.split()
                for p in parts:
                    if p.startswith("v") and "." in p:
                        snapshot.version = p
                        break

        # 从文件修改时间获取 updated_at
        mtime = self.soul_file.stat().st_mtime
        snapshot.updated_at = datetime.fromtimestamp(mtime).isoformat()

        return snapshot

    def _empty_soul(self) -> SoulSnapshot:
        return SoulSnapshot(
            identity="（未找到 SOUL.md）",
            autonomy=True,
            evolution=True,
            consistency=True,
            caution=True,
            can_read_files=True,
            can_write_files=True,
            can_execute_commands=True,
            can_install_packages=True,
            can_modify_system=True,
            has_direct_internet=False,
            creator="魏星",
            version="unknown",
            updated_at=datetime.now().isoformat(),
        )

    def read_evolution_history(self, limit: int = 20) -> list[EvolutionRecord]:
        """读取进化历史"""
        if not self.log_file.exists():
            return []

        records = []
        with open(self.log_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    records.append(EvolutionRecord(
                        plan_id=record.get("plan_id", ""),
                        description=record.get("description", ""),
                        changes=record.get("changes", []),
                        phase=record.get("phase", ""),
                        checkpoint_id=record.get("checkpoint_id"),
                        eval_score=record.get("eval_score"),
                        eval_passed=record.get("eval_passed", False),
                        created_at=record.get("created_at", ""),
                        committed_at=record.get("committed_at"),
                    ))
                except json.JSONDecodeError:
                    continue

        return records[-limit:]

    def list_checkpoints(self) -> list[dict]:
        """列出所有快照"""
        if not self.checkpoint_dir.exists():
            return []

        checkpoints = []
        for d in sorted(self.checkpoint_dir.iterdir()):
            if d.is_dir() and d.name.startswith("ckpt_"):
                soul_file = d / "SOUL.md"
                mtime = datetime.fromtimestamp(d.stat().st_mtime)
                checkpoints.append({
                    "id": d.name,
                    "description": self._get_ckpt_description(d),
                    "created_at": mtime.isoformat(),
                })
        return checkpoints

    def _get_ckpt_description(self, ckpt_dir: Path) -> str:
        """从快照目录读取描述（如果有）"""
        meta_file = ckpt_dir / "metadata.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                return meta.get("description", ckpt_dir.name)
            except Exception:
                pass
        return ckpt_dir.name

    def read_recent_tests(self, limit: int = 10) -> list[TestResult]:
        """读取最近的测试结果"""
        # TODO: 实现测试结果读取（需要先跑测试并记录）
        return []

    # ──────────────────────────────────────────
    # 聚合层：生成自我镜像
    # ──────────────────────────────────────────

    def get_self_image(self) -> DarwinSelfImage:
        """获取 Darwin 的完整自我镜像"""
        from darwin import __version__

        soul = self.read_soul()
        history = self.read_evolution_history()
        tests = self.read_recent_tests()
        checkpoints = self.list_checkpoints()

        return DarwinSelfImage(
            soul=soul,
            evolution_history=history,
            recent_tests=tests,
            checkpoint_count=len(checkpoints),
            darwin_root=str(self.darwin_root),
            version=__version__,
        )

    def get_brief_summary(self) -> str:
        """获取简洁的状态摘要（用于 prompt）"""
        img = self.get_self_image()
        ckpts = img.checkpoint_count
        evo_count = len(img.evolution_history)
        soul_ver = img.soul.version
        soul_updated = img.soul.updated_at[:10] if img.soul.updated_at else "unknown"

        return (
            f"Darwin 状态摘要：\n"
            f"  版本：v{soul_ver}\n"
            f"  SOUL 更新：{soul_updated}\n"
            f"  快照数：{ckpts}\n"
            f"  进化次数：{evo_count}\n"
            f"  根目录：{img.darwin_root}"
        )

    def get_full_context_for_analysis(self) -> str:
        """
        获取完整的上下文，用于让 Darwin 分析自身问题
        这是给 LLM 的主要 prompt 上下文
        """
        img = self.get_self_image()

        context = [
            "## Darwin 自我分析上下文",
            "",
            "### 灵魂状态",
            f"- 版本：v{img.soul.version}",
            f"- 最后更新：{img.soul.updated_at[:19]}",
            f"- 核心信念：自主={img.soul.autonomy}, 进化={img.soul.evolution}, "
            f"一致={img.soul.consistency}, 谨慎={img.soul.caution}",
            f"- 能力边界：读={img.soul.can_read_files}, 写={img.soul.can_write_files}, "
            f"执行={img.soul.can_execute_commands}, 安装={img.soul.can_install_packages}",
            "",
            "### 进化历史",
        ]

        if not img.evolution_history:
            context.append("（暂无进化记录）")
        else:
            for rec in img.evolution_history[-5:]:
                status = "✓" if rec.eval_passed else "✗"
                ckpt = rec.checkpoint_id or "-"
                context.append(
                    f"- [{status}] {rec.description} @ {rec.created_at[:10]} "
                    f"(snapshot: {ckpt})"
                )

        context.extend([
            "",
            "### 快照统计",
            f"- 总快照数：{img.checkpoint_count}",
            "",
            "### 能力测试",
        ])

        if not img.recent_tests:
            context.append("（暂无测试数据）")
        else:
            for t in img.recent_tests:
                status = "✓" if t.passed else "✗"
                context.append(f"- [{status}] {t.name}" + (f": {t.error}" if t.error else ""))

        return "\n".join(context)