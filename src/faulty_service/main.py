from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


APPLICATION_NAME = os.getenv("APPLICATION_NAME", "platform-observability-faulty")
FAILURE_DELAY_SECONDS = float(os.getenv("FAILURE_DELAY_SECONDS", "1.25"))
logger = logging.getLogger("faulty_service")

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests handled by the demo application.",
    ["application", "method", "route", "status"],
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration for the demo application.",
    ["application", "method", "route"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2.5, 5),
)


class MetricsMiddleware:
    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or scope.get("path") == "/metrics":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status_code = 500

        async def observe(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, observe)
        finally:
            route = getattr(scope.get("route"), "path", None) or "unmatched"
            labels = {
                "application": APPLICATION_NAME,
                "method": scope.get("method", "UNKNOWN"),
                "route": route,
            }
            HTTP_REQUESTS.labels(status=str(status_code), **labels).inc()
            HTTP_DURATION.labels(**labels).observe(time.perf_counter() - started)


app = FastAPI(title="Faulty Observability Demo")
app.add_middleware(MetricsMiddleware)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"service": APPLICATION_NAME, "status": "ok"}


@app.get("/api/orders/{order_id}")
async def order(order_id: int) -> JSONResponse:
    await asyncio.sleep(FAILURE_DELAY_SECONDS)
    logger.error("simulated dependency timeout order_id=%s", order_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": "DEPENDENCY_TIMEOUT",
            "message": "The downstream inventory service did not respond in time.",
            "orderId": order_id,
        },
    )


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
