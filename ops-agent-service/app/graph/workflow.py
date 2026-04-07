from __future__ import annotations

from dataclasses import dataclass

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.config import Settings
from app.graph.state import AgentState
from app.llm import LlmGateway
from app.models.domain import GatewayOpsEvidence, LogsEvidence, MetricsEvidence, NormalizedQuery
from app.services.anomaly import (
    build_loki_query,
    build_metric_queries,
    evaluate_anomaly,
    parse_loki_streams,
    parse_prometheus_matrix,
)
from app.tools.observability import ObservabilityTools


@dataclass
class DiagnosticDependencies:
    # 将图依赖显式注入，便于测试替换和后续扩展更多工具。
    settings: Settings
    llm: LlmGateway
    tools: ObservabilityTools


def build_diagnostic_graph(deps: DiagnosticDependencies):
    settings = deps.settings

    def query_understanding(state: AgentState) -> dict:
        # 先把自然语言问题规范成结构化查询条件，后续节点都围绕这个结果工作。
        understanding = deps.llm.understand_query(
            question=state["question"],
            explicit_device_id=state.get("device_id"),
            explicit_topic_id=state.get("topic_id"),
        )
        time_range = state["time_range"]
        metric_query, baseline_query, total_query = build_metric_queries(
            metric_name_flow=settings.metrics_name_flow,
            metric_name_total=settings.metrics_name_total,
            device_id=understanding.device_id,
            topic_id=understanding.topic_id,
        )
        log_query = build_loki_query(settings, understanding.device_id, understanding.topic_id)
        normalized = NormalizedQuery(
            question=state["question"],
            time_range_start=time_range["start"],
            time_range_end=time_range["end"],
            device_id=understanding.device_id,
            topic_id=understanding.topic_id,
            analysis_focus=understanding.analysis_focus,
            metric_query=metric_query,
            baseline_metric_query=baseline_query,
            total_metric_query=total_query,
            log_query=log_query,
            gateway_event_limit=settings.gateway_event_limit,
            notes=understanding.notes,
        )
        return {
            "normalized_query": normalized.model_dump(mode="json"),
            "device_id": normalized.device_id,
            "topic_id": normalized.topic_id,
        }

    def fetch_metrics(state: AgentState) -> dict:
        normalized = NormalizedQuery.model_validate(state["normalized_query"])
        try:
            # 同时查询当前窗口和前一天基线，给规则层一个最直接的对照组。
            current_payload = deps.tools.query_prometheus.invoke(
                {
                    "query": normalized.metric_query,
                    "start": normalized.time_range_start.isoformat(),
                    "end": normalized.time_range_end.isoformat(),
                    "step": settings.default_query_step,
                }
            )
            baseline_payload = deps.tools.query_prometheus.invoke(
                {
                    "query": normalized.baseline_metric_query,
                    "start": normalized.time_range_start.isoformat(),
                    "end": normalized.time_range_end.isoformat(),
                    "step": settings.default_query_step,
                }
            )
            metrics_evidence = MetricsEvidence(
                query=normalized.metric_query,
                baseline_query=normalized.baseline_metric_query,
                total_query=normalized.total_metric_query,
                series=parse_prometheus_matrix(current_payload),
                baseline_series=parse_prometheus_matrix(baseline_payload),
                notes=["queried Prometheus current and previous-day baseline windows"],
            )
        except Exception as exc:
            metrics_evidence = MetricsEvidence(
                query=normalized.metric_query,
                baseline_query=normalized.baseline_metric_query,
                total_query=normalized.total_metric_query,
                degraded=True,
                error=str(exc),
                notes=["Prometheus evidence unavailable"],
            )
        return {"metrics_evidence": metrics_evidence.model_dump(mode="json")}

    def fetch_logs(state: AgentState) -> dict:
        normalized = NormalizedQuery.model_validate(state["normalized_query"])
        try:
            # 日志只取和当前问题相关的窗口与关键词，避免把无关噪音带进总结节点。
            payload = deps.tools.query_loki.invoke(
                {
                    "query": normalized.log_query,
                    "start": normalized.time_range_start.isoformat(),
                    "end": normalized.time_range_end.isoformat(),
                    "limit": settings.log_line_limit,
                }
            )
            logs_evidence = parse_loki_streams(payload, settings)
            logs_evidence.query = normalized.log_query
        except Exception as exc:
            logs_evidence = LogsEvidence(
                query=normalized.log_query,
                degraded=True,
                error=str(exc),
            )
        return {"log_evidence": logs_evidence.model_dump(mode="json")}

    def fetch_gateway_context(state: AgentState) -> dict:
        normalized = NormalizedQuery.model_validate(state["normalized_query"])
        try:
            # 这一步补的是领域上下文，解决通用 observability 平台不了解设备在线态的问题。
            devices_payload = deps.tools.query_gateway_ops_api.invoke({"resource": "devices"})
            events_payload = deps.tools.query_gateway_ops_api.invoke(
                {"resource": "events", "limit": normalized.gateway_event_limit}
            )
            device_payload = None
            if normalized.device_id:
                device_payload = deps.tools.query_gateway_ops_api.invoke(
                    {"resource": "device_status", "device_id": normalized.device_id}
                )
            gateway_evidence = GatewayOpsEvidence(
                overview=devices_payload.get("overview"),
                device=device_payload.get("device") if device_payload else None,
                events=events_payload.get("events", []),
            )
        except Exception as exc:
            gateway_evidence = GatewayOpsEvidence(degraded=True, error=str(exc))
        return {"gateway_evidence": gateway_evidence.model_dump(mode="json")}

    def anomaly_evaluator(state: AgentState) -> dict:
        # 规则层先做事实判断，避免让 LLM 直接决定“是否异常”。
        metrics_evidence = MetricsEvidence.model_validate(state["metrics_evidence"])
        logs_evidence = LogsEvidence.model_validate(state["log_evidence"])
        gateway_evidence = GatewayOpsEvidence.model_validate(state["gateway_evidence"])
        assessment = evaluate_anomaly(metrics_evidence, logs_evidence, gateway_evidence)
        return {"anomaly_assessment": assessment.model_dump(mode="json")}

    def diagnosis_writer(state: AgentState) -> dict:
        # 只有在证据已经齐备后才让模型做总结，保证输出有明确证据来源。
        normalized = NormalizedQuery.model_validate(state["normalized_query"])
        metrics_evidence = MetricsEvidence.model_validate(state["metrics_evidence"])
        logs_evidence = LogsEvidence.model_validate(state["log_evidence"])
        gateway_evidence = GatewayOpsEvidence.model_validate(state["gateway_evidence"])
        assessment = evaluate_anomaly(metrics_evidence, logs_evidence, gateway_evidence)
        diagnosis = deps.llm.write_diagnosis(
            normalized_query=normalized,
            metrics_evidence=metrics_evidence,
            logs_evidence=logs_evidence,
            gateway_evidence=gateway_evidence,
            assessment=assessment,
        )
        return {"final_answer": diagnosis.model_dump(mode="json")}

    workflow = StateGraph(AgentState)
    workflow.add_node("query_understanding", query_understanding)
    workflow.add_node("fetch_metrics", fetch_metrics)
    workflow.add_node("fetch_logs", fetch_logs)
    workflow.add_node("fetch_gateway_context", fetch_gateway_context)
    workflow.add_node("anomaly_evaluator", anomaly_evaluator)
    workflow.add_node("diagnosis_writer", diagnosis_writer)

    # 这里保持单图多节点设计，第一版不引入更重的多 agent 协作复杂度。
    workflow.add_edge(START, "query_understanding")
    workflow.add_edge("query_understanding", "fetch_metrics")
    workflow.add_edge("query_understanding", "fetch_logs")
    workflow.add_edge("query_understanding", "fetch_gateway_context")
    workflow.add_edge(["fetch_metrics", "fetch_logs", "fetch_gateway_context"], "anomaly_evaluator")
    workflow.add_edge("anomaly_evaluator", "diagnosis_writer")
    workflow.add_edge("diagnosis_writer", END)

    return workflow.compile(checkpointer=MemorySaver())
