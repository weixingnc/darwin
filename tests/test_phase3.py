"""Test suite for Phase 3: AutoTuner and BugFixer"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from darwin.evolution.auto_tuner import AutoTuner, RuntimeMetrics, TUNABLE_PARAMS
from darwin.evolution.bug_fixer import BugFixer, BugReport


def test_auto_tuner_loads():
    """AutoTuner 可以正常加载"""
    tuner = AutoTuner(Path("/home/weixing/darwin"))
    assert tuner.darwin_root == Path("/home/weixing/darwin")


def test_auto_tuner_get_current_params():
    """可以读取当前参数"""
    tuner = AutoTuner(Path("/home/weixing/darwin"))
    params = tuner.get_current_params()
    assert isinstance(params, dict)
    assert "temperature" in params
    assert "max_tokens" in params


def test_auto_tuner_record_metrics():
    """可以记录指标"""
    tuner = AutoTuner(Path("/home/weixing/darwin"))
    metrics = RuntimeMetrics(
        timestamp="2026-05-27T00:00:00",
        session_id="test-session",
        llm_latency_ms=500.0,
        llm_error_rate=0.0,
        tool_success_rate=1.0,
        tool_avg_latency_ms=100.0,
        message_count=10,
        error_count=0,
    )
    result = tuner.record_metrics(metrics)
    assert result is True


def test_auto_tuner_analyze_and_suggest():
    """可以生成分析建议"""
    tuner = AutoTuner(Path("/home/weixing/darwin"))
    suggestions = tuner.analyze_and_suggest()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_auto_tuner_param_safety_range():
    """参数在安全范围内"""
    for param, info in TUNABLE_PARAMS.items():
        assert info["min"] <= info["default"] <= info["max"]
        assert info["min"] < info["max"]


def test_bug_fixer_loads():
    """BugFixer 可以正常加载"""
    fixer = BugFixer(Path("/home/weixing/darwin"))
    assert fixer.darwin_root == Path("/home/weixing/darwin")


def test_bug_fixer_analyze_traceback():
    """可以分析 traceback"""
    fixer = BugFixer(Path("/home/weixing/darwin"))

    sample_traceback = """
Traceback (most recent call last):
  File "/test/file.py", line 10, in test_function
    raise ValueError("test error")
ValueError: test error
"""

    report = fixer.analyze_traceback(sample_traceback)
    assert report.error_type == "ValueError"
    assert report.error_message == "test error"
    assert report.file_path == "/test/file.py"
    assert report.line_number == 10


def test_bug_fixer_parse_pytest_output():
    """可以解析 pytest 输出"""
    fixer = BugFixer(Path("/home/weixing/darwin"))

    output = """
test_file.py::test_one PASSED
test_file.py::test_two FAILED
test_file.py::test_three PASSED
"""
    reports = fixer.parse_pytest_output(output)
    assert len(reports) == 1
    assert reports[0].source == "test"
    assert reports[0].error_type == "TestFailed"


def test_bug_fixer_generate_fix_description():
    """可以生成修复描述"""
    fixer = BugFixer(Path("/home/weixing/darwin"))

    bug = BugReport(
        source="test",
        error_type="TypeError",
        error_message="unsupported operand type(s)",
        traceback="TypeError: unsupported operand type(s)\n",
        file_path="/test/file.py",
        line_number=5,
    )

    desc = fixer.generate_fix_description(bug)
    assert "Bug 分析" in desc
    assert "TypeError" in desc
    assert "unsupported operand" in desc


def test_bug_fixer_create_fix_attempt():
    """可以创建修复尝试"""
    fixer = BugFixer(Path("/home/weixing/darwin"))

    bug = BugReport(
        source="test",
        error_type="ImportError",
        error_message="No module named 'xyz'",
        traceback="",
    )

    fix = fixer.create_fix_attempt(
        bug=bug,
        patch_description="安装缺失的模块",
        patch_content=None,
    )

    assert fix.result == "pending"
    assert fix.bug_report.error_type == "ImportError"


if __name__ == "__main__":
    tests = [
        ("AutoTuner loads", test_auto_tuner_loads),
        ("AutoTuner get current params", test_auto_tuner_get_current_params),
        ("AutoTuner record metrics", test_auto_tuner_record_metrics),
        ("AutoTuner analyze and suggest", test_auto_tuner_analyze_and_suggest),
        ("AutoTuner param safety range", test_auto_tuner_param_safety_range),
        ("BugFixer loads", test_bug_fixer_loads),
        ("BugFixer analyze traceback", test_bug_fixer_analyze_traceback),
        ("BugFixer parse pytest output", test_bug_fixer_parse_pytest_output),
        ("BugFixer generate fix description", test_bug_fixer_generate_fix_description),
        ("BugFixer create fix attempt", test_bug_fixer_create_fix_attempt),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)