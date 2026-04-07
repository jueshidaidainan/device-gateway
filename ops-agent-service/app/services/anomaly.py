from __future__ import annotations

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


def build_metric_queries(
    *,
    metric_name_flow: str,
    metric_name_total: str,
    device_id: str | None,
    topic_id: str | None,
) -> tuple[str, str | None, str]:
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
    segments = [settings.loki_log_selector]
    if device_id:
        segments.append(f'|= "{device_id}"')
    if topic_id:
        segments.append(f'|= "{topic_id}"')
    keyword_pattern = "|".join(settings.log_keywords)
    segments.append(f'|~ "(?i){keyword_pattern}"')
    return " ".join(segments)


def parse_prometheus_matrix(payload: dict) -> list[MetricSeries]:
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


def evaluate_anomaly(
    metrics_evidence: MetricsEvidence,
    logs_evidence: LogsEvidence,
    gateway_evidence: GatewayOpsEvidence,
) -> AnomalyAssessment:
    # 第一版先采用轻量规则，重点是可解释和可验证，而不是追求复杂算法。
    degraded_reasons: list[str] = []
    if metrics_evidence.degraded:
        degraded_reasons.append("metrics_unavailable")
    if logs_evidence.degraded:
        degraded_reasons.append("logs_unavailable")
    if gateway_evidence.degraded:
        degraded_reasons.append("gateway_context_unavailable")

    current_series = metrics_evidence.series[0] if metrics_evidence.series else None
    baseline_series = metrics_evidence.baseline_series[0] if metrics_evidence.baseline_series else None

    current_mean = current_series.average if current_series else None
    current_latest = current_series.latest if current_series else None
    baseline_mean = baseline_series.average if baseline_series else None
    baseline_latest = baseline_series.latest if baseline_series else None

    delta_ratio = None
    if current_mean is not None and baseline_mean not in (None, 0):
        delta_ratio = (current_mean - baseline_mean) / baseline_mean

    reasons: list[str] = []
    suspected_offline = False
    device_state = gateway_evidence.device or {}
    if device_state:
        suspected_offline = not bool(device_state.get("biSocketOnline", True))

    if delta_ratio is not None and abs(delta_ratio) >= 0.35:
        reasons.append(f"flow deviates from the previous-day baseline by {delta_ratio:.0%}")
    elif current_latest == 0 and baseline_mean not in (None, 0):
        reasons.append("current traffic dropped to zero while the baseline stayed non-zero")

    if logs_evidence.records:
        reasons.append("related log evidence was found in the same time window")
    if suspected_offline:
        reasons.append("gateway reports the device as offline")

    is_anomalous = bool(reasons) and (
        delta_ratio is None or abs(delta_ratio) >= 0.2 or suspected_offline or bool(logs_evidence.records)
    )

    confidence = 0.35
    if delta_ratio is not None:
        confidence += min(abs(delta_ratio), 1.0) * 0.35
    if logs_evidence.records:
        confidence += 0.15
    if suspected_offline:
        confidence += 0.15
    if degraded_reasons:
        confidence -= 0.1
    confidence = max(0.1, min(confidence, 0.98))

    if is_anomalous:
        summary = "Traffic looks abnormal in the requested window."
    elif degraded_reasons:
        summary = "No clear anomaly was confirmed, but some evidence sources were unavailable."
    else:
        summary = "Traffic remains within the expected range for the selected window."

    return AnomalyAssessment(
        is_anomalous=is_anomalous,
        confidence=confidence,
        summary=summary,
        reasons=reasons,
        degraded_reasons=degraded_reasons,
        stats={
            "current_mean": current_mean,
            "current_latest": current_latest,
            "baseline_mean": baseline_mean,
            "baseline_latest": baseline_latest,
            "delta_ratio": delta_ratio,
            "log_matches": float(len(logs_evidence.records)),
        },
    )


def summarize_metrics(metrics_evidence: MetricsEvidence) -> dict[str, Any]:
    series = metrics_evidence.series[0] if metrics_evidence.series else None
    baseline = metrics_evidence.baseline_series[0] if metrics_evidence.baseline_series else None
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
