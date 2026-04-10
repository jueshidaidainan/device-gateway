from __future__ import annotations

from datetime import datetime

import httpx

from app.config import Settings
from app.models.api import ComponentHealth


class LokiClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.loki_base_url
        self.timeout = settings.request_timeout_seconds

    def query_range(self, *, query: str, start: datetime, end: datetime, limit: int) -> dict:
        if not self.base_url:
            raise RuntimeError("Loki base URL is not configured")

        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.get(
                "/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": str(int(start.timestamp() * 1_000_000_000)),
                    "end": str(int(end.timestamp() * 1_000_000_000)),
                    "limit": limit,
                    "direction": "backward",
                },
            )
            response.raise_for_status()
            return response.json()

    async def aquery_range(self, *, query: str, start: datetime, end: datetime, limit: int) -> dict:
        if not self.base_url:
            raise RuntimeError("Loki base URL is not configured")

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(
                "/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": str(int(start.timestamp() * 1_000_000_000)),
                    "end": str(int(end.timestamp() * 1_000_000_000)),
                    "limit": limit,
                    "direction": "backward",
                },
            )
            response.raise_for_status()
            return response.json()

    def health(self) -> ComponentHealth:
        if not self.base_url:
            return ComponentHealth(name="loki", ok=False, message="Loki URL is not configured")

        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.get("/ready")
                response.raise_for_status()
            return ComponentHealth(name="loki", ok=True, message="Loki is reachable")
        except Exception as exc:  # pragma: no cover
            return ComponentHealth(
                name="loki",
                ok=False,
                message="Loki health check failed",
                details={"error": str(exc)},
            )

    async def ahealth(self) -> ComponentHealth:
        if not self.base_url:
            return ComponentHealth(name="loki", ok=False, message="Loki URL is not configured")

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.get("/ready")
                response.raise_for_status()
            return ComponentHealth(name="loki", ok=True, message="Loki is reachable")
        except Exception as exc:  # pragma: no cover
            return ComponentHealth(
                name="loki",
                ok=False,
                message="Loki health check failed",
                details={"error": str(exc)},
            )
