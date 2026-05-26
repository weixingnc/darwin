"""BugFixer — Darwin 自动修 bug

分析测试失败 / traceback，定位根因，生成修复 patch，
重跑测试验证。所有修复都需要通过测试验证。
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
class BugReport:
    """Bug 报告"""
    source: str           # "test", "log", "user_report"
    error_type: str       # 错误类型（Python exception type）
    error_message: str    # 错误信息
    traceback: str        # 完整 traceback
    file_path: Optional[str] = None   # 疑似问题文件
    line_number: Optional[int] = None  # 疑似问题行


@dataclass
class FixAttempt:
    """修复尝试记录"""
    bug_report: BugReport
    patch_description: str   # 描述如何修复
    patch_content: Optional[str] = None  # patch 文件内容
    verified: bool = False
    attempt_at: str = field(default_factory=lambda: datetime.now().isoformat())
    result: str = "pending"   # pending / verified / failed


class BugFixer:
    """
    自动修 bug 引擎

    Darwin 接收测试失败报告 → 分析 traceback → 定位根因 →
    生成 patch → 重跑验证 → 失败则回滚
    """

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root)
        self.fixes_dir = self.darwin_root / "evolution" / "fixes"
        self.fixes_dir.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # Bug 分析
    # ──────────────────────────────────────────

    def analyze_traceback(self, traceback_str: str) -> BugReport:
        """
        分析 traceback，提取关键信息
        定位最可能的出问题文件和行
        """
        lines = traceback_str.strip().split("\n")

        error_type = ""
        error_message = ""
        file_path = None
        line_number = None

        # 提取错误类型和消息
        for i, line in enumerate(lines):
            if line.startswith("Traceback"):
                continue
            if line.startswith("  File"):
                # 提取文件路径
                match = re.search(r'File "(.+?)", line (\d+)', line)
                if match:
                    file_path = match.group(1)
                    line_number = int(match.group(2))
            elif "Error:" in line or "Exception:" in line or ":" in line:
                parts = line.split(":", 1)
                error_type = parts[0].strip()
                if len(parts) > 1:
                    error_message = parts[1].strip()

        # 确定 source
        source = "test"
        if "pytest" in traceback_str or "test" in traceback_str.lower():
            source = "test"
        elif "log" in traceback_str.lower():
            source = "log"
        else:
            source = "user_report"

        return BugReport(
            source=source,
            error_type=error_type,
            error_message=error_message,
            traceback=traceback_str,
            file_path=file_path,
            line_number=line_number,
        )

    def parse_pytest_output(self, output: str) -> list[BugReport]:
        """解析 pytest 输出，提取所有失败的 bug"""
        reports = []
        # 简单实现：提取 FAILED 行
        for line in output.split("\n"):
            if "FAILED" in line:
                reports.append(BugReport(
                    source="test",
                    error_type="TestFailed",
                    error_message=line.strip(),
                    traceback="",
                ))
        return reports

    # ──────────────────────────────────────────
    # 修复生成（模板，实际由 LLM 生成）
    # ──────────────────────────────────────────

    def generate_fix_description(
        self,
        bug: BugReport,
    ) -> str:
        """
        根据 bug 报告生成修复描述

        这是一个简化版本，实际由 LLM 分析后写出完整 patch。
        这里给出分析框架。
        """
        desc_parts = []

        desc_parts.append(f"## Bug 分析")

        if bug.error_type:
            desc_parts.append(f"**错误类型**: {bug.error_type}")

        if bug.error_message:
            desc_parts.append(f"**错误信息**: {bug.error_message}")

        if bug.file_path:
            desc_parts.append(f"**疑似位置**: {bug.file_path}:{bug.line_number}")

        desc_parts.append(f"\n## Traceback")
        desc_parts.append(f"```\n{bug.traceback}\n```")

        desc_parts.append(f"\n## 修复建议")

        # 根据错误类型给出通用建议
        if bug.error_type == "ImportError":
            desc_parts.append("检查 import 语句，确认模块已安装")
        elif bug.error_type == "TypeError":
            desc_parts.append("检查类型是否匹配，参数顺序是否正确")
        elif bug.error_type == "FileNotFoundError":
            desc_parts.append("检查文件路径是否正确，或需要创建目录")
        elif bug.error_type == "AttributeError":
            desc_parts.append("检查对象是否有该属性，可能需要初始化")
        elif bug.error_type == "AssertionError":
            desc_parts.append("检查断言条件是否符合预期")

        return "\n".join(desc_parts)

    def create_fix_attempt(
        self,
        bug: BugReport,
        patch_description: str,
        patch_content: Optional[str] = None,
    ) -> FixAttempt:
        """创建修复尝试"""
        fix = FixAttempt(
            bug_report=bug,
            patch_description=patch_description,
            patch_content=patch_content,
        )

        self._save_fix_attempt(fix)
        logger.info(f"Fix attempt created for {bug.error_type} in {bug.file_path}")

        return fix

    def _save_fix_attempt(self, fix: FixAttempt):
        """保存修复尝试"""
        fix_id = f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = self.fixes_dir / f"{fix_id}.json"
        data = {
            "bug": fix.bug_report.__dict__,
            "patch_description": fix.patch_description,
            "patch_content": fix.patch_content,
            "verified": fix.verified,
            "attempt_at": fix.attempt_at,
            "result": fix.result,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # ──────────────────────────────────────────
    # 验证
    # ──────────────────────────────────────────

    def run_tests(self, test_path: Optional[str] = None) -> tuple[bool, str]:
        """
        运行测试，返回 (是否全部通过, 输出)
        """
        cmd = ["python3", "-m", "pytest", "-v"]
        if test_path:
            # 只运行特定测试
            cmd.append(test_path)
        else:
            cmd.append(str(self.darwin_root / "tests"))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "测试超时（120秒）"
        except Exception as e:
            return False, str(e)

    def verify_fix(self, fix_id: str) -> tuple[bool, str]:
        """
        验证修复是否有效
        重跑相关测试
        """
        import glob

        fix_files = sorted(self.fixes_dir.glob(f"{fix_id}.json"))
        if not fix_files:
            return False, f"Fix not found: {fix_id}"

        # 简化：运行所有测试
        passed, output = self.run_tests()
        return passed, output

    # ──────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────

    def read_file_for_fix(self, file_path: str, context_lines: int = 5) -> str:
        """读取文件，在疑似 bug 行附近添加注释"""
        path = Path(file_path)
        if not path.exists():
            return f"文件不存在: {file_path}"

        try:
            lines = path.read_text().split("\n")
            start = max(0, (self._find_bug_line(lines) or 0) - context_lines)
            end = min(len(lines), (self._find_bug_line(lines) or 0) + context_lines)
            snippet = "\n".join(f"{i+1:4d}: {l}" for i, l in enumerate(lines[start:end], start + 1))
            return snippet
        except Exception as e:
            return f"读取失败: {e}"

    def _find_bug_line(self, lines: list[str]) -> Optional[int]:
        """找可疑行（简化实现）"""
        for i, line in enumerate(lines):
            if "# BUG:" in line or "# FIXME:" in line:
                return i
        return None