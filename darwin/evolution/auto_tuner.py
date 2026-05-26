"""AutoTuner — Darwin 自动调参引擎

收集运行时指标，分析趋势，自动调整 LLM 参数。
所有调整都自动执行（低风险），并记录历史。
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RuntimeMetrics:
    """运行时指标快照"""
    timestamp: str
    session_id: str
    llm_latency_ms: Optional[float] = None      # LLM 单次调用延迟
    llm_error_rate: Optional[float] = None       # LLM 错误率
    tool_success_rate: Optional[float] = None     # 工具调用成功率
    tool_avg_latency_ms: Optional[float] = None  # 工具平均延迟
    message_count: int = 0                      # 消息数
    error_count: int = 0                        # 错误数


@dataclass
class ParameterAdjustment:
    """参数调整记录"""
    param: str
    old_value: str
    new_value: str
    reason: str
    metrics_snapshot: dict
    applied_at: str = field(default_factory=lambda: datetime.now().isoformat())


# 可调参数及其安全范围
TUNABLE_PARAMS = {
    "max_tokens": {"min": 256, "max": 8192, "default": 2048},
    "temperature": {"min": 0.0, "max": 2.0, "default": 0.7},
    "top_p": {"min": 0.0, "max": 1.0, "default": 1.0},
    "request_timeout": {"min": 10, "max": 300, "default": 60},
}


class AutoTuner:
    """
    自动调参引擎

    Darwin 收集自己的运行时指标，分析问题，
    在安全范围内自动调整 LLM 参数。
    """

    def __init__(self, darwin_root: Path):
        self.darwin_root = Path(darwin_root)
        self.metrics_dir = self.darwin_root / "evolution" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.metrics_dir / "adjustments.jsonl"
        self.current_params_file = self.metrics_dir / "current_params.json"

    # ──────────────────────────────────────────
    # 指标收集
    # ──────────────────────────────────────────

    def record_metrics(self, metrics: RuntimeMetrics) -> bool:
        """记录一条指标"""
        try:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_dir / "metrics.jsonl", "a") as f:
                f.write(json.dumps(metrics.__dict__, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
            return False

    def load_recent_metrics(self, hours: int = 24) -> list[RuntimeMetrics]:
        """加载最近 N 小时的指标"""
        cutoff = datetime.now() - timedelta(hours=hours)
        metrics = []

        metrics_file = self.metrics_dir / "metrics.jsonl"
        if not metrics_file.exists():
            return metrics

        with open(metrics_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data["timestamp"])
                    if ts >= cutoff:
                        metrics.append(RuntimeMetrics(**data))
                except Exception:
                    continue

        return metrics

    def compute_statistics(self, metrics: list[RuntimeMetrics]) -> dict:
        """计算统计值"""
        if not metrics:
            return {}

        latencies = [m.llm_latency_ms for m in metrics if m.llm_latency_ms]
        error_rates = [m.llm_error_rate for m in metrics if m.llm_error_rate is not None]
        tool_rates = [m.tool_success_rate for m in metrics if m.tool_success_rate is not None]
        tool_lats = [m.tool_avg_latency_ms for m in metrics if m.tool_avg_latency_ms]

        stats = {
            "sample_count": len(metrics),
            "avg_llm_latency_ms": sum(latencies) / len(latencies) if latencies else None,
            "max_llm_latency_ms": max(latencies) if latencies else None,
            "avg_error_rate": sum(error_rates) / len(error_rates) if error_rates else None,
            "avg_tool_success_rate": sum(tool_rates) / len(tool_rates) if tool_rates else None,
            "avg_tool_latency_ms": sum(tool_lats) / len(tool_lats) if tool_lats else None,
        }

        return {k: v for k, v in stats.items() if v is not None}

    # ──────────────────────────────────────────
    # 参数读取/设置
    # ──────────────────────────────────────────

    def get_current_params(self) -> dict:
        """读取当前参数"""
        if self.current_params_file.exists():
            return json.loads(self.current_params_file.read_text())
        return {k: v["default"] for k, v in TUNABLE_PARAMS.items()}

    def set_param(self, param: str, value: float) -> bool:
        """设置参数（在安全范围内）"""
        if param not in TUNABLE_PARAMS:
            logger.warning(f"Unknown param: {param}")
            return False

        info = TUNABLE_PARAMS[param]
        if not (info["min"] <= value <= info["max"]):
            logger.warning(
                f"Value {value} out of range for {param}: "
                f"[{info['min']}, {info['max']}]"
            )
            return False

        params = self.get_current_params()
        old_value = params.get(param, info["default"])
        params[param] = value

        # 记录调整
        self._log_adjustment(ParameterAdjustment(
            param=param,
            old_value=str(old_value),
            new_value=str(value),
            reason=self._infer_reason(param, value, old_value),
            metrics_snapshot=self.compute_statistics(self.load_recent_metrics(24)),
        ))

        self.current_params_file.write_text(json.dumps(params, indent=2))
        logger.info(f"Param adjusted: {param} = {value} (was {old_value})")
        return True

    def _infer_reason(self, param: str, new_value: float, old_value: float) -> str:
        """推断调整原因"""
        stats = self.load_recent_metrics(24)
        if not stats:
            return "手动调整"

        stat_dict = self.compute_statistics(stats)
        reasons = []

        if param == "temperature":
            if new_value < old_value:
                reasons.append("降低温度以减少随机性")
            else:
                reasons.append("提高温度以增加创造性")

        elif param == "max_tokens":
            if stat_dict.get("avg_llm_latency_ms", 0) > 3000:
                reasons.append("LLM 延迟较高，考虑增加超时")

        elif param == "request_timeout":
            if stat_dict.get("avg_llm_latency_ms", 0) > 50000:
                reasons.append("LLM 延迟高，增加超时限制")

        return "; ".join(reasons) if reasons else "指标优化"

    def _log_adjustment(self, adjustment: ParameterAdjustment):
        """记录参数调整历史"""
        with open(self.log_file, "a") as f:
            f.write(json.dumps(adjustment.__dict__, ensure_ascii=False) + "\n")

    def get_adjustment_history(self, limit: int = 20) -> list[ParameterAdjustment]:
        """读取调整历史"""
        if not self.log_file.exists():
            return []

        adjustments = []
        with open(self.log_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    adjustments.append(ParameterAdjustment(**json.loads(line)))
                except Exception:
                    continue

        return adjustments[-limit:]

    # ──────────────────────────────────────────
    # 分析与建议
    # ──────────────────────────────────────────

    def analyze_and_suggest(self) -> list[str]:
        """
        分析指标，给出调整建议
        返回建议列表（供 Darwin 参考）
        """
        suggestions = []
        stats = self.compute_statistics(self.load_recent_metrics(24))

        if not stats:
            return ["暂无足够数据生成建议"]

        # 延迟过高
        if stats.get("avg_llm_latency_ms", 0) > 10000:
            suggestions.append(
                f"LLM 延迟过高（{stats['avg_llm_latency_ms']:.0f}ms），"
                "建议增加 request_timeout 或降低 max_tokens"
            )

        # 错误率高
        if stats.get("avg_error_rate", 0) > 0.1:
            suggestions.append(
                f"LLM 错误率偏高（{stats['avg_error_rate']:.1%}），"
                "建议降低 temperature 减少幻觉"
            )

        # 工具成功率低
        if stats.get("avg_tool_success_rate", 1.0) < 0.8:
            suggestions.append(
                f"工具成功率偏低（{stats['avg_tool_success_rate']:.1%}），"
                "建议检查工具注册和参数"
            )

        # 工具延迟高
        if stats.get("avg_tool_latency_ms", 0) > 5000:
            suggestions.append(
                f"工具延迟偏高（{stats['avg_tool_latency_ms']:.0f}ms），"
                "建议优化工具实现或增加超时"
            )

        if not suggestions:
            suggestions.append("各项指标正常，无需调整")

        return suggestions