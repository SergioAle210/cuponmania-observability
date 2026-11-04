"""Ocho operaciones simuladas e instrumentación HTTP automática."""

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import threading
from time import perf_counter_ns
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.catalog import CATALOG
from api.config import Settings


Identifier = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Purchase(StrictBody):
    coupon_id: Identifier
    quantity: Annotated[int, Field(ge=1, le=10)]


class Issue(StrictBody):
    purchase_id: Identifier


class Redeem(StrictBody):
    qr_code: Identifier
    merchant_id: Identifier


class Merchant(StrictBody):
    merchant_id: Identifier
    action: Literal["create", "update"]


class Promotion(StrictBody):
    promotion_id: Identifier
    merchant_id: Identifier
    action: Literal["publish", "update"]


class Recovery(StrictBody):
    account_id: Identifier
    action: Literal["unlock", "reset"]


class Refund(StrictBody):
    purchase_id: Identifier
    action: Literal["refund", "cancel"]


class EventWriter:
    """Un proceso por archivo; apertura append y flush por evento, sin rotación."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Validar permisos antes de aceptar tráfico, también cuando se usa factory.
        with path.open("a", encoding="utf-8"):
            pass

    def write(self, event: dict) -> None:
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        with self.lock, self.path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(line + "\n")
            output.flush()


class RequestLogMiddleware:
    """Mide hasta el envío del último cuerpo y registra exactamente una vez."""

    def __init__(self, app: ASGIApp, writer: EventWriter, settings: Settings):
        self.app, self.writer, self.settings = app, writer, settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = perf_counter_ns()
        request_id = str(uuid4())
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        item = CATALOG.get(scope["path"])
        scenario = self.settings.scenario if item else ("health" if scope["path"] == "/healthz" else "unmatched")
        if item:
            for key, value in scope.get("headers", []):
                if key.lower() == b"x-simulation-scenario":
                    selected = value.decode("latin-1")
                    if selected in ("normal", "qr-degraded"):
                        scenario = selected
        state["scenario"] = scenario
        started = False
        complete = False
        status = 500

        async def instrumented_send(message: Message) -> None:
            nonlocal started, complete, status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = list(message.get("headers", [])) + [(b"x-request-id", request_id.encode("ascii"))]
                started = True
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False) and not complete:
                complete = True
                duration = max(1, perf_counter_ns() - start)
                self.writer.write({
                    "@timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                    "http.request.method": scope["method"],
                    "http.response.status_code": status,
                    "event.duration": duration,
                    "url.path": scope["path"],
                    "service.name": "cuponmania-api",
                    "log.level": "ERROR" if status >= 500 else "WARN" if status >= 400 else "INFO",
                    "event.id": str(uuid4()),
                    "request_id": request_id,
                    "catalog_item": item.catalog_item if item else None,
                    "component": item.component if item else None,
                    "scenario": state["scenario"],
                    "cuponmania.synthetic": True,
                })

        try:
            await self.app(scope, receive, instrumented_send)
        except Exception:
            # Una respuesta iniciada no puede cambiar a 500. Fallas de escritura
            # se propagan para que el servidor no oculte la pérdida de evidencia.
            if started:
                raise
            response = JSONResponse({"synthetic": True, "request_id": request_id,
                                     "error": {"code": "internal_error", "message": "Error interno de simulación"}},
                                    status_code=500)
            await response(scope, receive, instrumented_send)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    writer = EventWriter(settings.log_path)
    rng = random.Random(settings.seed)
    app = FastAPI(title="CupónManía API simulada", version="1.0.0", docs_url=None, redoc_url=None,
                  redirect_slashes=False)
    app.state.settings = settings
    app.state.rng = rng
    app.add_middleware(RequestLogMiddleware, writer=writer, settings=settings)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # No devolver exc.errors(): incluye valores de entrada, posiblemente secretos.
        return JSONResponse({"synthetic": True, "request_id": request.state.request_id,
                             "error": {"code": "validation_error", "message": "Solicitud inválida"}}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse({"synthetic": True, "request_id": request.state.request_id,
                             "error": {"code": "http_error", "message": "Ruta o método no disponible"}},
                            status_code=exc.status_code, headers=exc.headers)

    async def simulate(request: Request) -> JSONResponse:
        if request.headers.get("X-Simulation-Scenario", settings.scenario) not in ("normal", "qr-degraded"):
            return JSONResponse({"synthetic": True, "request_id": request.state.request_id,
                                 "error": {"code": "invalid_scenario", "message": "Escenario inválido"}}, status_code=422)
        item = CATALOG[request.url.path]
        scenario = request.state.scenario
        profile = settings.qr if scenario == "qr-degraded" and item.catalog_item in ("INC-02", "INC-03") else settings.normal
        outcome, delay = profile.sample(rng)
        await asyncio.sleep(delay)
        envelope = {"synthetic": True, "request_id": request.state.request_id,
                    "catalog_item": item.catalog_item, "component": item.component,
                    "scenario": scenario, "outcome": outcome}
        if outcome == "success":
            return JSONResponse({**envelope, "data": item.data}, status_code=item.status_code)
        status = 400 if outcome == "client_error" else 503
        return JSONResponse({**envelope, "error": {"code": f"simulated_{outcome}",
                                                  "message": "Error simulado de cliente" if status == 400 else "Servicio simulado no disponible"}},
                            status_code=status)

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok", "synthetic": True}

    @app.post("/api/v1/purchases", status_code=201)
    async def purchases(body: Purchase, request: Request):
        return await simulate(request)

    @app.post("/api/v1/coupons/issue", status_code=201)
    async def issue(body: Issue, request: Request):
        return await simulate(request)

    @app.post("/api/v1/coupons/redeem")
    async def redeem(body: Redeem, request: Request):
        return await simulate(request)

    @app.get("/api/v1/platform/status")
    async def platform_status(request: Request):
        return await simulate(request)

    @app.post("/api/v1/merchants", status_code=201)
    async def merchants(body: Merchant, request: Request):
        return await simulate(request)

    @app.post("/api/v1/promotions", status_code=201)
    async def promotions(body: Promotion, request: Request):
        return await simulate(request)

    @app.post("/api/v1/accounts/recovery")
    async def recovery(body: Recovery, request: Request):
        return await simulate(request)

    @app.post("/api/v1/refunds")
    async def refunds(body: Refund, request: Request):
        return await simulate(request)

    return app


app = create_app()
