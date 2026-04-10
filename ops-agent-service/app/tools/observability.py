from __future__ import annotations

from dataclasses import dataclass

from langchain_core.tools import BaseTool, tool

from app.clients.gateway_ops import GatewayOpsClient
from app.clients.loki import LokiClient
from app.clients.prometheus import PrometheusClient


@dataclass
class ObservabilityTools:
    query_prometheus: BaseTool
    query_loki: BaseTool
    query_gateway_ops_api: BaseTool


def build_observability_tools(
    prometheus_client: PrometheusClient,
    loki_client: LokiClient,
    gateway_ops_client: GatewayOpsClient,
) -> ObservabilityTools:
    @tool
    async def query_prometheus(query: str, start: str, end: str, step: str) -> dict:
        """Execute a Prometheus range query against the configured server."""

        from datetime import datetime

        return await prometheus_client.aquery_range(
            query=query,
            start=datetime.fromisoformat(start),
            end=datetime.fromisoformat(end),
            step=step,
        )

    @tool
    async def query_loki(query: str, start: str, end: str, limit: int) -> dict:
        """Execute a Loki range query against the configured server."""

        from datetime import datetime

        return await loki_client.aquery_range(
            query=query,
            start=datetime.fromisoformat(start),
            end=datetime.fromisoformat(end),
            limit=limit,
        )

    @tool
    async def query_gateway_ops_api(resource: str, device_id: str | None = None, limit: int = 20) -> dict:
        """Query the gateway ops API for devices, one device, or recent events."""

        if resource == "devices":
            return await gateway_ops_client.aget_devices()
        if resource == "device_status":
            if not device_id:
                raise ValueError("device_id is required when resource=device_status")
            return await gateway_ops_client.aget_device_status(device_id)
        if resource == "events":
            return await gateway_ops_client.aget_events(limit)
        raise ValueError(f"Unsupported resource: {resource}")

    return ObservabilityTools(
        query_prometheus=query_prometheus,
        query_loki=query_loki,
        query_gateway_ops_api=query_gateway_ops_api,
    )
