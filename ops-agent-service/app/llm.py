from __future__ import annotations

import json
import re

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.models.api import ComponentHealth
from app.models.domain import (
    AnomalyAssessment,
    DiagnosisOutput,
    EvidenceItem,
    GatewayOpsEvidence,
    LogsEvidence,
    MetricsEvidence,
    NormalizedQuery,
    QueryUnderstandingResult,
)
from app.services.anomaly import summarize_metrics


class LlmGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model)
        self._chat_model = None
        if self.enabled:
            # 统一通过 OpenAI-compatible 接口接入，后续替换模型供应商时改动最小。
            self._chat_model = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                temperature=0.1,
            )

    def understand_query(
        self,
        *,
        question: str,
        explicit_device_id: str | None,
        explicit_topic_id: str | None,
    ) -> QueryUnderstandingResult:
        fallback = self._fallback_query_understanding(question, explicit_device_id, explicit_topic_id)
        if not self._chat_model:
            return fallback

        # 这里让模型只做“参数抽取”，而不是让它直接决定诊断结论。
        structured = self._chat_model.with_structured_output(QueryUnderstandingResult)
        try:
            result = structured.invoke(
                [
                    SystemMessage(
                        content=(
                            "Extract the most likely device_id and topic_id from the user request. "
                            "Prefer explicit IDs already supplied by the caller. Keep notes short."
                        )
                    ),
                    HumanMessage(
                        content=json.dumps(
                            {
                                "question": question,
                                "explicit_device_id": explicit_device_id,
                                "explicit_topic_id": explicit_topic_id,
                            },
                            ensure_ascii=False,
                        )
                    ),
                ]
            )
            return QueryUnderstandingResult(
                device_id=explicit_device_id or result.device_id or fallback.device_id,
                topic_id=explicit_topic_id or result.topic_id or fallback.topic_id,
                analysis_focus=result.analysis_focus or fallback.analysis_focus,
                notes=result.notes or fallback.notes,
            )
        except Exception:
            return fallback

    def write_diagnosis(
        self,
        *,
        normalized_query: NormalizedQuery,
        metrics_evidence: MetricsEvidence,
        logs_evidence: LogsEvidence,
        gateway_evidence: GatewayOpsEvidence,
        assessment: AnomalyAssessment,
    ) -> DiagnosisOutput:
        fallback = self._fallback_diagnosis(
            normalized_query=normalized_query,
            metrics_evidence=metrics_evidence,
            logs_evidence=logs_evidence,
            gateway_evidence=gateway_evidence,
            assessment=assessment,
        )
        if not self._chat_model:
            return fallback

        # 输出强制走结构化模型，避免返回风格飘忽不定的自由文本。
        structured = self._chat_model.with_structured_output(DiagnosisOutput)
        try:
            result = structured.invoke(
                [
                    SystemMessage(
                        content=(
                            "You are an observability diagnosis assistant. Summarize the evidence conservatively. "
                            "Do not invent unavailable logs, metrics, or device state."
                        )
                    ),
                    HumanMessage(
                        content=json.dumps(
                            {
                                "normalized_query": normalized_query.model_dump(mode="json"),
                                "metrics_summary": summarize_metrics(metrics_evidence),
                                "log_matches": [
                                    {
                                        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                                        "line": record.line[:240],
                                    }
                                    for record in logs_evidence.records[:5]
                                ],
                                "gateway_device": gateway_evidence.device,
                                "gateway_events": gateway_evidence.events[:5],
                                "assessment": assessment.model_dump(mode="json"),
                            },
                            ensure_ascii=False,
                        )
                    ),
                ]
            )
            if not result.evidence:
                return fallback
            return result
        except Exception:
            return fallback

    def health(self) -> ComponentHealth:
        if not self.enabled:
            return ComponentHealth(name="llm", ok=False, message="LLM is not configured")

        try:
            headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
            with httpx.Client(base_url=self.settings.llm_base_url, timeout=self.settings.request_timeout_seconds) as client:
                response = client.get("/models", headers=headers)
                response.raise_for_status()
            return ComponentHealth(name="llm", ok=True, message="LLM endpoint is reachable")
        except Exception as exc:  # pragma: no cover
            return ComponentHealth(
                name="llm",
                ok=False,
                message="LLM health check failed",
                details={"error": str(exc)},
            )

    def _fallback_query_understanding(
        self,
        question: str,
        explicit_device_id: str | None,
        explicit_topic_id: str | None,
    ) -> QueryUnderstandingResult:
        # 即使模型不可用，也尽量从问题里兜底提取设备和 topic 信息。
        device_id = explicit_device_id or _find_pattern(question, r"(device[-_ ]?\d+)")
        topic_id = explicit_topic_id or _find_pattern(question, r"(topic[-_ ]?\d+|\d+\.\d+\.\d+\.\d+)")
        notes = ["fallback parser used because no LLM response was available"]
        return QueryUnderstandingResult(device_id=device_id, topic_id=topic_id, notes=notes)

    def _fallback_diagnosis(
        self,
        *,
        normalized_query: NormalizedQuery,
        metrics_evidence: MetricsEvidence,
        logs_evidence: LogsEvidence,
        gateway_evidence: GatewayOpsEvidence,
        assessment: AnomalyAssessment,
    ) -> DiagnosisOutput:
        # fallback 结果保持和主流程同一数据结构，方便上层统一消费。
        evidence: list[EvidenceItem] = [
            EvidenceItem(
                source="prometheus",
                title="Metric summary",
                detail=json.dumps(summarize_metrics(metrics_evidence), ensure_ascii=False),
            )
        ]
        if logs_evidence.records:
            evidence.append(
                EvidenceItem(
                    source="loki",
                    title="Relevant logs",
                    detail=logs_evidence.records[0].line[:240],
                )
            )
        if gateway_evidence.device:
            evidence.append(
                EvidenceItem(
                    source="gateway-ops",
                    title="Gateway device state",
                    detail=json.dumps(gateway_evidence.device, ensure_ascii=False),
                )
            )

        next_steps = [
            "Review the referenced Prometheus series in Grafana.",
            "Inspect matching Loki logs for the same time window.",
        ]
        if normalized_query.device_id:
            next_steps.append(f"Check the gateway connection state for {normalized_query.device_id}.")

        return DiagnosisOutput(
            summary=assessment.summary,
            is_anomalous=assessment.is_anomalous,
            confidence=assessment.confidence,
            suspected_causes=assessment.reasons or ["No strong abnormal signal was found."],
            evidence=evidence,
            next_steps=next_steps,
        )


def _find_pattern(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).replace(" ", "") if match else None
