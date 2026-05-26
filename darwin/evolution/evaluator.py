"""
Evaluator — 能力评估器

在进化后运行测试，验证 Darwin 的能力是否提升或至少保持不降。
"""

import datetime
import json
import subprocess
from pathlib import Path


class Evaluator:
    """
    Darwin 能力评估器

    评估方式：
        1. 测试集运行（evolution/tests/ 下的测试脚本）
        2. 基准对比（与快照时的表现对比）
        3. 自我测试（Darwin 回答标准化问题）

    输出：
        {
            "passed": bool,
            "score": float,          # 0-100
            "baseline_score": float, # 快照时的分数
            "delta": float,          # 分数变化
            "tests_run": int,
            "tests_passed": int,
            "reason": str,           # 失败原因（如果有）
        }
    """

    def __init__(self, tests_dir: Path, baseline_file: Path | None = None):
        self.tests_dir = Path(tests_dir)
        self.baseline_file = baseline_file or tests_dir.parent / "baseline.json"
        self.tests_dir.mkdir(parents=True, exist_ok=True)

    def run(self, plan) -> dict:
        """
        执行评估

        Returns:
            评估报告字典
        """
        baseline = self._load_baseline()

        # Run tests
        test_results = self._run_tests()

        # Calculate score
        score = test_results["score"]
        baseline_score = baseline.get("score", 0)

        passed = score >= baseline_score * 0.9  # 允许10%波动

        report = {
            "passed": passed,
            "score": score,
            "baseline_score": baseline_score,
            "delta": score - baseline_score,
            "tests_run": test_results["run"],
            "tests_passed": test_results["passed"],
            "test_details": test_results["details"],
            "reason": "" if passed else f"分数下降 {baseline_score} → {score}",
            "evaluated_at": datetime.datetime.now().isoformat(),
        }

        # Save baseline if better
        if score > baseline_score:
            self._save_baseline(score, report)

        return report

    def _run_tests(self) -> dict:
        """运行测试目录下的所有测试"""
        tests = list(self.tests_dir.glob("test_*.py"))
        passed = 0
        details = []

        for test_file in tests:
            try:
                result = subprocess.run(
                    ["python3", str(test_file)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=test_file.parent
                )
                ok = result.returncode == 0
                if ok:
                    passed += 1
                details.append({
                    "name": test_file.stem,
                    "passed": ok,
                    "output": result.stdout[:200] if ok else result.stderr[:200],
                })
            except Exception as e:
                details.append({
                    "name": test_file.stem,
                    "passed": False,
                    "output": str(e),
                })

        total = len(tests) or 1
        return {
            "run": len(tests),
            "passed": passed,
            "score": round(passed / total * 100, 1),
            "details": details,
        }

    def _load_baseline(self) -> dict:
        """加载基准分数"""
        if self.baseline_file.exists():
            try:
                return json.loads(self.baseline_file.read_text())
            except Exception:
                pass
        return {"score": 0}

    def _save_baseline(self, score: float, report: dict):
        """保存新的基准分数"""
        self.baseline_file.write_text(json.dumps({
            "score": score,
            "report": report,
            "updated_at": datetime.datetime.now().isoformat(),
        }, indent=2))