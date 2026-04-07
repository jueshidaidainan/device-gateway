from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResolvedTimeRange(BaseModel):
    start: datetime
    end: datetime
    step: str = "60s"


class QueryUnderstandingResult(BaseModel):
    device_id: str | None = None
    topic_id: str | None = None
    analysis_focus: str = "traffic-anomaly"
    notes: list[str] = Field(default_factory=list)


class NormalizedQuery(BaseModel):
    question: str
    time_range_start: datetime
    time_range_end: datetime
    device_id: str | None = None
    topic_id: str | None = None
    analysis_focus: str = "traffic-anomaly"
    metric_query: str
    baseline_metric_query: str | None = None
    total_metric_query: str | None = None
    log_query: str
    gateway_event_limit: int = 20
    notes: list[str] = Field(default_factory=list)


class MetricPoint(BaseModel):
    timestamp: datetime
    value: float


class MetricSeries(BaseModel):
    label: str
    metric: dict[str, str] = Field(default_factory=dict)
    points: list[MetricPoint] = Field(default_factory=list)
    sample_count: int = 0
    average: float | None = None
    latest: float | None = None


class MetricsEvidence(BaseModel):
    query: str
    baseline_query: str | None = None
    total_query: str | None = None
    series: list[MetricSeries] = Field(default_factory=list)
    baseline_series: list[MetricSeries] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    degraded: bool = False
    error: str | None = None


class LogRecord(BaseModel):
    timestamp: datetime | None = None
    line: str
    labels: dict[str, str] = Field(default_factory=dict)


class LogsEvidence(BaseModel):
    query: str
    records: list[LogRecord] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    degraded: bool = False
    error: str | None = None


class GatewayOpsEvidence(BaseModel):
    overview: dict[str, Any] | None = None
    device: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    degraded: bool = False
    error: str | None = None


class EvidenceItem(BaseModel):
    source: str
    title: str
    detail: str


class AnomalyAssessment(BaseModel):
    is_anomalous: bool
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    reasons: list[str] = Field(default_factory=list)
    degraded_reasons: list[str] = Field(default_factory=list)
    stats: dict[str, float | None] = Field(default_factory=dict)


class DiagnosisOutput(BaseModel):
    summary: str
    is_anomalous: bool
    confidence: float = Field(ge=0.0, le=1.0)
    suspected_causes: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
