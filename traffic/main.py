"""Tráfico HTTP real, acotado y exclusivamente local. No escribe logs de API."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
import ipaddress
import json
import math
import os
import random
import signal
import time
from typing import Iterator
from urllib.parse import urlsplit, urlunsplit

import httpx


ENDPOINTS = (
    ("POST", "/api/v1/purchases"),
    ("POST", "/api/v1/coupons/issue"),
    ("POST", "/api/v1/coupons/redeem"),
    ("GET", "/api/v1/platform/status"),
    ("POST", "/api/v1/merchants"),
    ("POST", "/api/v1/promotions"),
    ("POST", "/api/v1/accounts/recovery"),
    ("POST", "/api/v1/refunds"),
)


def local_base_url(value: str) -> str:
    """Reject accidental third-party traffic, credentials and URL suffixes."""
    try:
        if not value or any(char.isspace() or ord(char) < 32 for char in value):
            raise ValueError
        parts = urlsplit(value)
        host = parts.hostname
        if (
            parts.scheme != "http"
            or not host
            or parts.username is not None
            or parts.password is not None
            or parts.path not in ("", "/")
            or "?" in value
            or "#" in value
            or "\\" in value
        ):
            raise ValueError
        port = parts.port  # Also validates malformed/non-numeric ports.
        if port is not None and not 1 <= port <= 65535:
            raise ValueError
        if host not in ("localhost", "api"):
            if not ipaddress.ip_address(host).is_loopback:
                raise ValueError
        return urlunsplit(("http", parts.netloc.lower(), "", "", ""))
    except ValueError:
        raise ValueError(
            "base-url debe ser HTTP a localhost, una IP loopback o api, "
            "sin credenciales, ruta, query ni fragmento"
        ) from None


@dataclass(frozen=True)
class Config:
    base_url: str = "http://127.0.0.1:8000"
    rate: float = 2.0
    concurrency: int = 2
    timeout: float = 5.0
    duration: float | None = None
    count: int | None = None
    seed: int | None = None
    mode: str = "random"
    scenario: str = "normal"

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", local_base_url(self.base_url))
        for name, value, limit in (("rate", self.rate, 20), ("timeout", self.timeout, 60)):
            if isinstance(value, bool) or not math.isfinite(value) or not 0 < value <= limit:
                raise ValueError(f"{name} debe ser finito, mayor que 0 y menor o igual a {limit}")
        if type(self.concurrency) is not int or not 1 <= self.concurrency <= 16:
            raise ValueError("concurrency debe ser un entero de 1 a 16")
        if self.duration is not None and (
            isinstance(self.duration, bool) or not math.isfinite(self.duration) or self.duration <= 0
        ):
            raise ValueError("duration debe ser finita y mayor que 0")
        if self.count is not None and (type(self.count) is not int or self.count <= 0):
            raise ValueError("count debe ser un entero positivo")
        if self.duration is not None and self.count is not None:
            raise ValueError("duration y count son mutuamente excluyentes")
        if self.seed is not None and type(self.seed) is not int:
            raise ValueError("seed debe ser un entero")
        if self.mode not in ("random", "sequential"):
            raise ValueError("mode debe ser random o sequential")
        if self.scenario not in ("normal", "qr-degraded"):
            raise ValueError("scenario debe ser normal o qr-degraded")


def requests_for(config: Config) -> Iterator[tuple[str, str, dict | None]]:
    """Every eight requests cover the catalog; seeds reproduce request inputs."""
    rng = random.Random(config.seed)
    while True:
        order = list(range(len(ENDPOINTS)))
        if config.mode == "random":
            rng.shuffle(order)
        for index in order:
            suffix = f"{rng.randrange(1_000_000):06d}"
            bodies = (
                {"coupon_id": f"demo-coupon-{suffix}", "quantity": rng.randint(1, 10)},
                {"purchase_id": f"demo-purchase-{suffix}"},
                {"qr_code": f"demo-qr-{suffix}", "merchant_id": f"demo-merchant-{suffix}"},
                None,
                {"merchant_id": f"demo-merchant-{suffix}", "action": rng.choice(("create", "update"))},
                {
                    "promotion_id": f"demo-promotion-{suffix}",
                    "merchant_id": f"demo-merchant-{suffix}",
                    "action": rng.choice(("publish", "update")),
                },
                {"account_id": f"demo-account-{suffix}", "action": rng.choice(("unlock", "reset"))},
                {"purchase_id": f"demo-purchase-{suffix}", "action": rng.choice(("refund", "cancel"))},
            )
            method, path = ENDPOINTS[index]
            yield method, path, bodies[index]


async def run(
    config: Config,
    stop_event: asyncio.Event | None = None,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict:
    """Run until count, duration or stop; injectable transport is for tests only."""
    stop = stop_event if stop_event is not None else asyncio.Event()
    loop = asyncio.get_running_loop()
    started_ns = time.perf_counter_ns()
    started = loop.time()
    deadline = None if config.duration is None else started + config.duration
    next_start = started
    stream = requests_for(config)
    pending: set[asyncio.Task] = set()
    status_counts: Counter[str] = Counter()
    endpoint_counts = {path: 0 for _, path in ENDPOINTS}
    error_counts: Counter[str] = Counter()
    attempted = completed = cancelled = 0
    reason = "stopped"
    stop_wait = asyncio.create_task(stop.wait())

    async with httpx.AsyncClient(
        base_url=config.base_url,
        timeout=httpx.Timeout(config.timeout),
        limits=httpx.Limits(max_connections=config.concurrency, max_keepalive_connections=config.concurrency),
        trust_env=False,
        follow_redirects=False,
        transport=transport,
        headers={"X-Simulation-Scenario": config.scenario},
    ) as client:

        async def send(method: str, path: str, body: dict | None) -> None:
            nonlocal completed, cancelled
            try:
                # HTTPX timeouts apply per I/O phase; this additionally bounds total time.
                async with asyncio.timeout(config.timeout):
                    kwargs = {} if body is None else {"json": body}
                    async with client.stream(method, path, **kwargs) as response:
                        async for _chunk in response.aiter_bytes():
                            pass  # Do not retain bodies in memory or log response contents.
                        status_counts[str(response.status_code)] += 1
                        completed += 1
            except (TimeoutError, httpx.TimeoutException):
                error_counts["timeout"] += 1
            except httpx.RequestError:
                error_counts["transport"] += 1
            except asyncio.CancelledError:
                cancelled += 1
                raise

        try:
            while True:
                finished = {task for task in pending if task.done()}
                pending.difference_update(finished)
                for task in finished:
                    task.result()
                if stop.is_set():
                    reason = "stopped"
                    break
                if config.count is not None and attempted >= config.count:
                    reason = "count"
                    break
                now = loop.time()
                if deadline is not None and now >= deadline:
                    reason = "duration"
                    break
                remaining = None if deadline is None else max(0.0, deadline - now)
                if len(pending) >= config.concurrency:
                    await asyncio.wait(pending | {stop_wait}, timeout=remaining, return_when=asyncio.FIRST_COMPLETED)
                    continue
                delay = next_start - now
                if delay > 0:
                    await asyncio.wait(
                        {stop_wait},
                        timeout=delay if remaining is None else min(delay, remaining),
                    )
                    continue
                method, path, body = next(stream)
                attempted += 1
                endpoint_counts[path] += 1
                pending.add(asyncio.create_task(send(method, path, body)))
                # Never catch up using a burst after a slow response or full concurrency.
                next_start = loop.time() + 1.0 / config.rate
            if pending:
                await asyncio.gather(*pending)
        finally:
            stop_wait.cancel()
            for task in pending:
                if not task.done():
                    task.cancel()
            await asyncio.gather(stop_wait, *pending, return_exceptions=True)

    duration_ns = max(1, time.perf_counter_ns() - started_ns)
    return {
        "attempted": attempted,
        "completed": completed,
        "transport_errors": sum(error_counts.values()),
        "cancelled": cancelled,
        "status_counts": dict(sorted(status_counts.items())),
        "endpoint_counts": endpoint_counts,
        "transport_error_counts": dict(sorted(error_counts.items())),
        "duration_ns": duration_ns,
        "duration_seconds": duration_ns / 1_000_000_000,
        "configured_rate": config.rate,
        "scenario": config.scenario,
        "stop_reason": reason,
    }


def parse_args(argv: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(description="Tráfico HTTP ficticio hacia la API local de CupónManía")
    parser.add_argument("--base-url", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--rate", type=float, default=2.0, help="peticiones por segundo: >0 y <=20 (2)")
    parser.add_argument("--concurrency", type=int, default=2, help="peticiones simultáneas: 1..16 (2)")
    parser.add_argument("--timeout", type=float, default=5.0, help="límite total por petición en segundos: >0 y <=60 (5)")
    limit = parser.add_mutually_exclusive_group()
    limit.add_argument("--duration", type=float, help="segundos de admisión de tráfico")
    limit.add_argument("--count", type=int, help="número de intentos HTTP")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--mode", choices=("random", "sequential"), default="random")
    parser.add_argument("--scenario", choices=("normal", "qr-degraded"), default="normal")
    values = vars(parser.parse_args(argv))
    try:
        return Config(**values)
    except ValueError as exc:
        parser.error(str(exc))


async def run_cli(config: Config) -> dict:
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    previous_handlers = {}

    def request_stop(_signum, _frame) -> None:
        loop.call_soon_threadsafe(stop.set)

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, request_stop)
        return await run(config, stop)
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    summary = asyncio.run(run_cli(config))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
