from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from app.config import Settings
from app.models.domain import (
    AnomalyAssessment,
    GatewayOpsEvidence,
    LogRecord,
    LogsEvidence,
    MetricPoint,
    MetricSeries,
    MetricsEvidence,
)


@dataclass(frozen=True)
class AnomalySignals:
    """规则层使用的中间信号集合。

    这个结构体不直接对外返回，而是承接 metrics / logs / gateway 三路证据
    提炼出来的关键判断信号，方便后续规则命中、异常判定和置信度打分复用。
    """

    current_mean: float | None
    current_latest: float | None
    baseline_mean: float | None
    baseline_latest: float | None
    delta_ratio: float | None
    suspected_offline: bool
    log_match_count: int

    @property
    def has_log_evidence(self) -> bool:
        """把日志数量转成布尔语义，便于规则层直接判断是否存在日志佐证。"""
        return self.log_match_count > 0

    def to_stats(self) -> dict[str, float | None]:
        """将中间信号转换成可落库、可返回的统计字段。"""
        return {
            "current_mean": self.current_mean,
            "current_latest": self.current_latest,
            "baseline_mean": self.baseline_mean,
            "baseline_latest": self.baseline_latest,
            "delta_ratio": self.delta_ratio,
            "log_matches": float(self.log_match_count),
        }


def build_metric_queries(
    *,
    metric_name_flow: str,
    metric_name_total: str,
    device_id: str | None,
    topic_id: str | None,
) -> tuple[str, str | None, str]:
    """根据设备和 topic 条件构造 Prometheus 查询语句。

    返回值依次是：
    1. 当前窗口 flow query
    2. 前一天同窗口 baseline query
    3. total query
    """

    # 查询模板统一收敛在这里，便于后续把 baseline 策略替换成更复杂的版本。
    labels: list[str] = []
    if device_id:
        labels.append(f'device_id="{device_id}"')
    if topic_id:
        labels.append(f'topic_id="{topic_id}"')

    if labels:
        selector = "{" + ",".join(labels) + "}"
        flow_query = f"{metric_name_flow}{selector}"
        total_query = f"{metric_name_total}{selector}"
    else:
        flow_query = f"sum({metric_name_flow})"
        total_query = f"sum({metric_name_total})"

    baseline_query = f"{flow_query} offset 1d"
    return flow_query, baseline_query, total_query


def build_loki_query(settings: Settings, device_id: str | None, topic_id: str | None) -> str:
    """构造 Loki 日志查询语句。

    查询会同时带上设备、topic 和错误关键词过滤，尽量只抓与当前问题相关的日志。
    """

    segments = [settings.loki_log_selector]
    if device_id:
        segments.append(f'|= "{device_id}"')
    if topic_id:
        segments.append(f'|= "{topic_id}"')
    keyword_pattern = "|".join(settings.log_keywords)
    segments.append(f'|~ "(?i){keyword_pattern}"')
    return " ".join(segments)


def parse_prometheus_matrix(payload: dict) -> list[MetricSeries]:
    """把 Prometheus matrix 响应转成项目内部统一的 `MetricSeries` 列表。

    这里顺手计算了 `average` 和 `latest`，避免规则层重复解析原始 payload。
    """

    results = payload.get("data", {}).get("result", [])
    parsed: list[MetricSeries] = []

    for item in results:
        # 在进入规则层之前先把 Prometheus 原始矩阵整理成稳定的数据结构。
        metric = {str(key): str(value) for key, value in item.get("metric", {}).items()}
        label = ",".join(f"{key}={value}" for key, value in metric.items()) or "aggregate"
        points = [
            MetricPoint(
                timestamp=datetime.fromtimestamp(float(ts), tz=timezone.utc),
                value=float(value),
            )
            for ts, value in item.get("values", [])
        ]
        values = [point.value for point in points]
        parsed.append(
            MetricSeries(
                label=label,
                metric=metric,
                points=points,
                sample_count=len(points),
                average=mean(values) if values else None,
                latest=values[-1] if values else None,
            )
        )
    return parsed


def parse_loki_streams(payload: dict, settings: Settings) -> LogsEvidence:
    """把 Loki 查询结果转换成 `LogsEvidence`。

    除了保留日志记录本身，这里还会提取命中的关键词，方便后续展示和解释。
    """

    records: list[LogRecord] = []
    matched_keywords: set[str] = set()
    streams = payload.get("data", {}).get("result", [])

    for stream in streams:
        # 这里顺手提取命中的关键词，后续可以直接作为诊断证据的一部分展示。
        labels = {str(key): str(value) for key, value in stream.get("stream", {}).items()}
        for ts_ns, line in stream.get("values", []):
            lowered = line.lower()
            for keyword in settings.log_keywords:
                if keyword.lower() in lowered:
                    matched_keywords.add(keyword)
            timestamp = datetime.fromtimestamp(int(ts_ns) / 1_000_000_000, tz=timezone.utc)
            records.append(LogRecord(timestamp=timestamp, line=line, labels=labels))

    return LogsEvidence(records=records[: settings.log_line_limit], matched_keywords=sorted(matched_keywords), query="")


def _primary_series(series_list: list[MetricSeries]) -> MetricSeries | None:
    """取规则层当前实际参与计算的主时间序列。

    当前版本默认只使用第一条序列做异常判断，后续如果需要支持多序列聚合，
    可以优先扩展这一层而不是把逻辑散落到各处。
    """

    return series_list[0] if series_list else None


def _collect_degraded_reasons(
    metrics_evidence: MetricsEvidence,
    logs_evidence: LogsEvidence,
    gateway_evidence: GatewayOpsEvidence,
) -> list[str]:
    """汇总证据源降级原因。

    这一步不判断异常本身，只负责记录哪些证据源缺失，供 summary 和 confidence 使用。
    """

    degraded_reasons: list[str] = []
    if metrics_evidence.degraded:
        degraded_reasons.append("metrics_unavailable")
    if logs_evidence.degraded:
        degraded_reasons.append("logs_unavailable")
    if gateway_evidence.degraded:
        degraded_reasons.append("gateway_context_unavailable")
    return degraded_reasons


def _extract_anomaly_signals(
    metrics_evidence: MetricsEvidence,
    logs_evidence: LogsEvidence,
    gateway_evidence: GatewayOpsEvidence,
) -> AnomalySignals:
    """从三路 evidence 中提取规则层真正关心的信号。

    例如当前均值、baseline 均值、偏移比例、设备离线状态、日志命中数等。
    """

    current_series = _primary_series(metrics_evidence.series)
    baseline_series = _primary_series(metrics_evidence.baseline_series)

    current_mean = current_series.average if current_series else None
    current_latest = current_series.latest if current_series else None
    baseline_mean = baseline_series.average if baseline_series else None
    baseline_latest = baseline_series.latest if baseline_series else None

    delta_ratio = None
    if current_mean is not None and baseline_mean not in (None, 0):
        delta_ratio = (current_mean - baseline_mean) / baseline_mean

    device_state = gateway_evidence.device or {}
    suspected_offline = bool(device_state) and not bool(device_state.get("biSocketOnline", True))

    return AnomalySignals(
        current_mean=current_mean,
        current_latest=current_latest,
        baseline_mean=baseline_mean,
        baseline_latest=baseline_latest,
        delta_ratio=delta_ratio,
        suspected_offline=suspected_offline,
        log_match_count=len(logs_evidence.records),
    )


def _build_rule_reasons(signals: AnomalySignals) -> list[str]:
    """根据提取出的信号命中规则，并生成可解释的 reasons 列表。

    `reasons` 既是后续 `is_anomalous` 判定的依据，也是给 LLM / fallback
    生成最终解释文本时的重要输入。
    """

    reasons: list[str] = []

    if signals.delta_ratio is not None and abs(signals.delta_ratio) >= 0.35:
        reasons.append(f"flow deviates from the previous-day baseline by {signals.delta_ratio:.0%}")
    elif signals.current_latest == 0 and signals.baseline_mean not in (None, 0):
        reasons.append("current traffic dropped to zero while the baseline stayed non-zero")

    if signals.has_log_evidence:
        reasons.append("related log evidence was found in the same time window")
    if signals.suspected_offline:
        reasons.append("gateway reports the device as offline")

    return reasons


def _is_anomalous(signals: AnomalySignals, reasons: list[str]) -> bool:
    """根据 reasons 和关键信号决定本次分析是否判为异常。"""

    return bool(reasons) and (
        signals.delta_ratio is None
        or abs(signals.delta_ratio) >= 0.2
        or signals.suspected_offline
        or signals.has_log_evidence
    )


def _score_confidence(signals: AnomalySignals, degraded_reasons: list[str]) -> float:
    """计算工程化的 confidence 分数。

    这里的 confidence 不是模型概率，而是对“当前判断有多站得住脚”的规则打分：
    证据越强、佐证越多，分数越高；证据源降级时分数会下调。
    """

    confidence = 0.35
    if signals.delta_ratio is not None:
        confidence += min(abs(signals.delta_ratio), 1.0) * 0.35
    if signals.has_log_evidence:
        confidence += 0.15
    if signals.suspected_offline:
        confidence += 0.15
    if degraded_reasons:
        confidence -= 0.1
    return max(0.1, min(confidence, 0.98))


def _build_assessment_summary(is_anomalous: bool, degraded_reasons: list[str]) -> str:
    """根据异常判定结果和降级状态生成摘要文案。"""

    if is_anomalous:
        return "Traffic looks abnormal in the requested window."
    if degraded_reasons:
        return "No clear anomaly was confirmed, but some evidence sources were unavailable."
    return "Traffic remains within the expected range for the selected window."


def evaluate_anomaly(
    metrics_evidence: MetricsEvidence,
    logs_evidence: LogsEvidence,
    gateway_evidence: GatewayOpsEvidence,
) -> AnomalyAssessment:
    """规则层主入口。

    这一步负责把多路证据转换成一个结构化的 `AnomalyAssessment`，包括：
    - 是否异常
    - 置信度
    - 摘要
    - 依据列表
    - 可观测统计值
    """

    # 第一版先采用轻量规则，重点是可解释和可验证，而不是追求复杂算法。
    degraded_reasons = _collect_degraded_reasons(metrics_evidence, logs_evidence, gateway_evidence)
    signals = _extract_anomaly_signals(metrics_evidence, logs_evidence, gateway_evidence)
    reasons = _build_rule_reasons(signals)
    is_anomalous = _is_anomalous(signals, reasons)
    confidence = _score_confidence(signals, degraded_reasons)
    summary = _build_assessment_summary(is_anomalous, degraded_reasons)

    return AnomalyAssessment(
        is_anomalous=is_anomalous,
        confidence=confidence,
        summary=summary,
        reasons=reasons,
        degraded_reasons=degraded_reasons,
        stats=signals.to_stats(),
    )


def summarize_metrics(metrics_evidence: MetricsEvidence) -> dict[str, Any]:
    """为 LLM 或 fallback 输出准备一份简化后的指标摘要。"""

    series = _primary_series(metrics_evidence.series)
    baseline = _primary_series(metrics_evidence.baseline_series)
    return {
        "query": metrics_evidence.query,
        "series_label": series.label if series else None,
        "current_average": series.average if series else None,
        "current_latest": series.latest if series else None,
        "baseline_average": baseline.average if baseline else None,
        "baseline_latest": baseline.latest if baseline else None,
        "notes": metrics_evidence.notes,
        "degraded": metrics_evidence.degraded,
        "error": metrics_evidence.error,
    }
