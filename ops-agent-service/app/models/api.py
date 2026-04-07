from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.domain import AnomalyAssessment, DiagnosisOutput, NormalizedQuery, ResolvedTimeRange


class TimeRangeInput(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
    lookback_minutes: int | None = Field(default=None, ge=1, le=24 * 60)

    def resolve(self, default_lookback_minutes: int, step: str) -> ResolvedTimeRange:
        end = self.end.astimezone(timezone.utc) if self.end else datetime.now(timezone.utc)
        if self.start:
            start = self.start.astimezone(timezone.utc)
        else:
            lookback = self.lookback_minutes or default_lookback_minutes
            start = end - timedelta(minutes=lookback)
        return ResolvedTimeRange(start=start, end=end, step=step)


class AnalyzeRequest(BaseModel):
    question: str = Field(
        ...,
        examples=["帮我看看 device-001 最近 1 小时 topic-10 的流量波动是否正常"],
    )
    time_range: TimeRangeInput = Field(
        default_factory=TimeRangeInput,
        json_schema_extra={"example": {"lookback_minutes": 60}},
    )
    device_id: str | None = Field(default=None, examples=["device-001"])
    topic_id: str | None = Field(default=None, examples=["10.10.10.8"])
    thread_id: str = Field(default_factory=lambda: str(uuid4()))


class ExplainAlertRequest(BaseModel):
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    starts_at: datetime | None = None
    time_range: TimeRangeInput = Field(default_factory=TimeRangeInput)
    thread_id: str = Field(default_factory=lambda: str(uuid4()))


class AnalyzeResponse(DiagnosisOutput):
    run_id: str
    thread_id: str
    normalized_query: NormalizedQuery
    assessment: AnomalyAssessment


class ComponentHealth(BaseModel):
    name: str
    ok: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    ok: bool
    components: list[ComponentHealth]
