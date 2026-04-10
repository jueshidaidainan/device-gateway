from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.clients.gateway_ops import GatewayOpsClient
from app.clients.loki import LokiClient
from app.clients.prometheus import PrometheusClient
from app.config import Settings, get_settings
from app.dashboard import build_dashboard_html
from app.graph.workflow import DiagnosticDependencies, build_diagnostic_graph
from app.llm import LlmGateway
from app.models.api import AnalyzeRequest, AnalyzeResponse, ExplainAlertRequest, HealthResponse
from app.models.domain import AnomalyAssessment, DiagnosisOutput, NormalizedQuery
from app.services.persistence import RunRepository
from app.tools.observability import build_observability_tools


@dataclass
# @dataclass 是 Python 提供的一个装饰器，用来快速定义“只负责存数据的类”。
class Runtime:
    # 将外部依赖集中收口，避免在路由层四处分散初始化逻辑。
    settings: Settings
    llm: LlmGateway
    repository: RunRepository
    workflow: object
    prometheus: PrometheusClient
    loki: LokiClient
    gateway_ops: GatewayOpsClient


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="LangGraph-based diagnostic agent for metrics, logs, and gateway connection state.",
        version="0.1.0",
        docs_url="/api/docs",
    )

    runtime = build_runtime(settings)
    app.state.runtime = runtime

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard() -> str:
        return build_dashboard_html(app_name=settings.app_name)

    @app.get("/agent/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        # 健康检查直接反映 LLM、指标、日志和网关上下文接口的可用性。
        components = await asyncio.gather(
            runtime.llm.ahealth(),
            runtime.prometheus.ahealth(),
            runtime.loki.ahealth(),
            runtime.gateway_ops.ahealth(),
        )
        return HealthResponse(ok=all(component.ok for component in components), components=components)

    @app.post("/agent/analyze", response_model=AnalyzeResponse)
    async def analyze(payload: AnalyzeRequest, request: Request) -> AnalyzeResponse:
        return await run_analysis(
            runtime=request.app.state.runtime,
            request_type="analyze",
            request_payload=payload.model_dump(mode="json"),
            question=payload.question,
            time_range=payload.time_range.resolve(
                runtime.settings.default_lookback_minutes,
                runtime.settings.default_query_step,
            ),
            device_id=payload.device_id,
            topic_id=payload.topic_id,
            thread_id=payload.thread_id,
        )

    @app.post("/agent/explain-alert", response_model=AnalyzeResponse)
    async def explain_alert(payload: ExplainAlertRequest, request: Request) -> AnalyzeResponse:
        # 告警解释复用同一条诊断链路，只是在入口侧先把告警转成自然语言问题。
        alert_name = payload.labels.get("alertname", "unknown-alert")
        device_id = payload.labels.get("device_id") or payload.labels.get("device")
        topic_id = payload.labels.get("topic_id")
        summary = payload.annotations.get("summary") or payload.annotations.get("description") or "No annotation provided."
        question = f"Explain alert {alert_name}. {summary}"
        return await run_analysis(
            runtime=request.app.state.runtime,
            request_type="explain-alert",
            request_payload=payload.model_dump(mode="json"),
            question=question,
            time_range=payload.time_range.resolve(
                runtime.settings.default_lookback_minutes,
                runtime.settings.default_query_step,
            ),
            device_id=device_id,
            topic_id=topic_id,
            thread_id=payload.thread_id,
        )

    return app


def build_runtime(settings: Settings) -> Runtime:
    # 在应用启动时一次性构建好客户端、工具层和 LangGraph 工作流。
    llm = LlmGateway(settings)
    repository = RunRepository(settings.sqlite_path)
    prometheus = PrometheusClient(settings)
    loki = LokiClient(settings)
    gateway_ops = GatewayOpsClient(settings)
    tools = build_observability_tools(prometheus, loki, gateway_ops)
    workflow = build_diagnostic_graph(DiagnosticDependencies(settings=settings, llm=llm, tools=tools))
    return Runtime(
        settings=settings,
        llm=llm,
        repository=repository,
        workflow=workflow,
        prometheus=prometheus,
        loki=loki,
        gateway_ops=gateway_ops,
    )


async def run_analysis(
    *,
    runtime: Runtime,
    request_type: str,
    request_payload: dict,
    question: str,
    time_range,
    device_id: str | None,
    topic_id: str | None,
    thread_id: str,
) -> AnalyzeResponse:
    run_id = str(uuid4())
    started_at = datetime.now(timezone.utc)
    started = perf_counter()

    # LangGraph 状态保持最小必要字段，避免把 HTTP 层细节泄漏到图内部。
    initial_state = {
        "question": question,
        "thread_id": thread_id,
        "time_range": time_range.model_dump(mode="json"),
        "device_id": device_id,
        "topic_id": topic_id,
    }

    try:
        state = await runtime.workflow.ainvoke(initial_state, config={"configurable": {"thread_id": thread_id}})
        normalized = NormalizedQuery.model_validate(state["normalized_query"])
        assessment = AnomalyAssessment.model_validate(state["anomaly_assessment"])
        final_answer = DiagnosisOutput.model_validate(state["final_answer"])
        response = AnalyzeResponse(
            run_id=run_id,
            thread_id=thread_id,
            normalized_query=normalized,
            assessment=assessment,
            **final_answer.model_dump(mode="json"),
        )
        finished_at = datetime.now(timezone.utc)
        # 无论是面试演示还是后续排障，落库存档都能帮助回放每次分析过程。
        await asyncio.to_thread(
            runtime.repository.save_run,
            run_id=run_id,
            thread_id=thread_id,
            request_type=request_type,
            request_payload=request_payload,
            normalized_query=state["normalized_query"],
            metrics_evidence=state.get("metrics_evidence"),
            log_evidence=state.get("log_evidence"),
            gateway_evidence=state.get("gateway_evidence"),
            anomaly_assessment=state.get("anomaly_assessment"),
            final_answer=state.get("final_answer"),
            status="completed",
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_ms=int((perf_counter() - started) * 1000),
            error_message=None,
        )
        return response
    except Exception as exc:
        finished_at = datetime.now(timezone.utc)
        await asyncio.to_thread(
            runtime.repository.save_run,
            run_id=run_id,
            thread_id=thread_id,
            request_type=request_type,
            request_payload=request_payload,
            normalized_query=None,
            metrics_evidence=None,
            log_evidence=None,
            gateway_evidence=None,
            anomaly_assessment=None,
            final_answer=None,
            status="failed",
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_ms=int((perf_counter() - started) * 1000),
            error_message=str(exc),
        )
        raise HTTPException(status_code=502, detail=f"Agent workflow failed: {exc}") from exc


app = create_app()
