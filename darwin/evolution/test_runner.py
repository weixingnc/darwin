"""TestRunner — Darwin 沙箱测试运行器

在沙箱环境中运行测试套件，收集测试结果。
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果"""
    sandbox_id: str
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    output: str
    duration_seconds: float
    ran_at: str


class TestRunner:
    """
    测试运行器

    在沙箱中运行 Darwin 的测试套件，
    返回结构化的测试结果。
    """

    def __init__(self, darwin_root: Path):
        self.darwin_root = darwin_root

    def run_tests_in_sandbox(
        self,
        sandbox_path: Path,
        test_path: Optional[str] = None,
        timeout: int = 120,
    ) -> TestResult:
        """
        在沙箱中运行测试

        Args:
            sandbox_path: 沙箱目录
            test_path: 可选，指定只跑某个测试文件/目录
            timeout: 超时时间（秒）

        Returns:
            TestResult: 测试结果
        """
        import time
        start = time.time()

        # 确定测试命令
        cmd = [
            "python3", "-m", "pytest",
            "-v",                 # 详细输出
            "--tb=short",         # 简短的 traceback
        ]

        if test_path:
            # 指定测试路径
            cmd.append(str(sandbox_path / test_path))
        else:
            # 运行所有测试
            cmd.append(str(sandbox_path / "tests"))

        logger.info(f"Running tests in sandbox: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(sandbox_path),
            )

            output = result.stdout + "\n" + result.stderr
            passed = result.returncode == 0
            duration = time.time() - start

            # 解析测试结果
            total, passed_count, failed_count = self._parse_pytest_output(output)

            logger.info(
                f"Tests in sandbox: {passed_count}/{total} passed, "
                f"duration: {duration:.1f}s, passed: {passed}"
            )

            return TestResult(
                sandbox_id=sandbox_path.name,
                passed=passed,
                total_tests=total,
                passed_tests=passed_count,
                failed_tests=failed_count,
                output=output,
                duration_seconds=duration,
                ran_at=datetime.now().isoformat(),
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start
            error_output = f"测试超时（{timeout}秒）"

            logger.error(f"Test timeout in sandbox: {sandbox_path.name}")

            return TestResult(
                sandbox_id=sandbox_path.name,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                output=error_output,
                duration_seconds=duration,
                ran_at=datetime.now().isoformat(),
            )

        except Exception as e:
            duration = time.time() - start
            error_output = f"测试执行失败: {str(e)}"

            logger.error(f"Test execution failed: {e}")

            return TestResult(
                sandbox_id=sandbox_path.name,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                output=error_output,
                duration_seconds=duration,
                ran_at=datetime.now().isoformat(),
            )

    def run_specific_tests(
        self,
        sandbox_path: Path,
        test_files: list[str],
    ) -> TestResult:
        """
        运行指定的测试文件列表

        Args:
            sandbox_path: 沙箱目录
            test_files: 测试文件列表（如 ["test_introspector.py", "test_phase2.py"]）

        Returns:
            TestResult: 汇总的测试结果
        """
        if not test_files:
            return TestResult(
                sandbox_id=sandbox_path.name,
                passed=True,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                output="No tests specified",
                duration_seconds=0.0,
                ran_at=datetime.now().isoformat(),
            )

        # 合并所有测试文件的输出
        all_outputs = []
        total = 0
        passed_count = 0
        failed_count = 0
        all_passed = True

        for test_file in test_files:
            test_path = sandbox_path / "tests" / test_file
            if not test_path.exists():
                test_path = sandbox_path / test_file

            result = self.run_tests_in_sandbox(sandbox_path, str(test_path))
            all_outputs.append(f"=== {test_file} ===\n{result.output}\n")

            total += result.total_tests
            passed_count += result.passed_tests
            failed_count += result.failed_tests
            all_passed = all_passed and result.passed

        return TestResult(
            sandbox_id=sandbox_path.name,
            passed=all_passed,
            total_tests=total,
            passed_tests=passed_count,
            failed_tests=failed_count,
            output="\n".join(all_outputs),
            duration_seconds=0.0,
            ran_at=datetime.now().isoformat(),
        )

    def _parse_pytest_output(self, output: str) -> tuple[int, int, int]:
        """
        解析 pytest 输出，提取测试数量

        Returns:
            (total, passed, failed)
        """
        total = 0
        passed = 0
        failed = 0

        for line in output.split("\n"):
            line = line.strip()

            # 统计行
            # 格式: test_file.py::test_name PASSED
            if "PASSED" in line:
                passed += 1
                total += 1
            elif "FAILED" in line:
                failed += 1
                total += 1
            elif "SKIPPED" in line:
                total += 1
            # pytest 总结行: 5 passed, 1 failed in 0.50s
            elif " passed" in line or " failed" in line:
                # e.g. "3 passed, 1 failed in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            passed = int(parts[i - 1])
                            total += passed
                        except (ValueError, IndexError):
                            pass
                    if part == "failed" and i > 0:
                        try:
                            failed = int(parts[i - 1])
                            total += failed
                        except (ValueError, IndexError):
                            pass

        return total, passed, failed

    def verify_soul_consistency(self, sandbox_path: Path) -> tuple[bool, str]:
        """
        验证沙箱中 SOUL.md 的自洽性

        检查：
        - SOUL.md 是否存在
        - 是否有实质内容（不是空文件）
        - identity 部分是否非空（支持多种格式）

        Returns:
            (is_valid, error_message)
        """
        soul_file = sandbox_path / "SOUL.md"

        if not soul_file.exists():
            return False, "SOUL.md 不存在"

        try:
            content = soul_file.read_text()

            # 基本检查：必须有实质身份定义
            # 支持格式：identity: xxx 或者 ## 身份 / ## 核心身份 等
            has_identity_marker = (
                "identity:" in content
                or "## 身份" in content
                or "## 核心身份" in content
                or "## Identity" in content
            )

            if not has_identity_marker:
                return False, "SOUL.md 缺少身份定义字段"

            # 至少要有一些内容（超过 50 字符）
            if len(content.strip()) < 50:
                return False, "SOUL.md 内容过少"

            return True, "SOUL.md 自洽性验证通过"

        except Exception as e:
            return False, f"读取 SOUL.md 失败: {str(e)}"

    def verify_integration(self, sandbox_path: Path) -> TestResult:
        """
        运行集成测试验证

        验证沙箱中的代码是否能正常导入和运行基本功能。
        """
        test_code = """
import sys
sys.path.insert(0, '.')

# 验证核心模块可以导入
from darwin import __version__
from darwin.evolution import EvolutionEngine
from darwin.agent import Introspector

# 验证版本
assert __version__, "版本号为空"

print("集成测试通过")
"""

        # 写入临时测试文件
        test_file = sandbox_path / "tests" / "test_integration_verify.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(test_code)

        result = self.run_tests_in_sandbox(sandbox_path, "tests/test_integration_verify.py")

        # 清理临时测试文件
        if test_file.exists():
            test_file.unlink()

        return result