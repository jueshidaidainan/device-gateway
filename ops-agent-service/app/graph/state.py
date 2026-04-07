from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    thread_id: str
    time_range: dict
    device_id: str | None
    topic_id: str | None
    normalized_query: dict
    metrics_evidence: dict
    log_evidence: dict
    gateway_evidence: dict
    anomaly_assessment: dict
    final_answer: dict
