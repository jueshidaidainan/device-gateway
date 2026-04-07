from __future__ import annotations

import httpx

from app.config import Settings
from app.models.api import ComponentHealth


class GatewayOpsClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.gateway_ops_base_url
        self.timeout = settings.request_timeout_seconds

    def get_devices(self) -> dict:
        return self._get("/ops/devices")

    def get_device_status(self, device_id: str) -> dict:
        return self._get(f"/ops/devices/{device_id}/status")

    def get_events(self, limit: int) -> dict:
        return self._get("/ops/events", params={"limit": limit})

    def _get(self, path: str, params: dict | None = None) -> dict:
        if not self.base_url:
            raise RuntimeError("Gateway ops URL is not configured")

        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    def health(self) -> ComponentHealth:
        if not self.base_url:
            return ComponentHealth(name="gateway-ops", ok=False, message="Gateway ops URL is not configured")

        try:
            self.get_devices()
            return ComponentHealth(name="gateway-ops", ok=True, message="Gateway ops API is reachable")
        except Exception as exc:  # pragma: no cover
            return ComponentHealth(
                name="gateway-ops",
                ok=False,
                message="Gateway ops API health check failed",
                details={"error": str(exc)},
            )
