import asyncio
from itertools import islice
import json
import math
import time

import httpx
import pytest

from traffic.main import Config, ENDPOINTS, local_base_url, parse_args, requests_for, run, run_cli


@pytest.mark.parametrize("url", [
    "https://127.0.0.1:8000", "http://example.com", "http://localhost.evil.test", "http://192.168.1.2",
    "http://user:secret@localhost", "http://localhost/api", "http://localhost?token=secret",
    "http://localhost#frag", "http://localhost?", "http://localhost#", "http://localhost:0",
    "http://localhost:65536", "http://localhost:abc", "http://local\nhost", "http://api\\evil",
    "http://", "", "http://127.1", "http://2130706433",
])
def test_reject_nonlocal_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        local_base_url(url)


@pytest.mark.parametrize("url", ["http://localhost:8000", "http://api:8000/", "http://127.0.0.1:8123", "http://[::1]:8000"])
def test_accept_local_urls(url):
    assert local_base_url(url) == url.rstrip("/")


@pytest.mark.parametrize("kwargs", [
    {"rate": 0}, {"rate": 21}, {"rate": math.inf}, {"rate": math.nan}, {"rate": True},
    {"concurrency": 0}, {"concurrency": 17}, {"concurrency": 1.5}, {"concurrency": True},
    {"timeout": 0}, {"timeout": 61}, {"timeout": math.inf},
    {"duration": 0}, {"duration": math.nan}, {"count": -1}, {"count": True},
    {"count": 1, "duration": 1}, {"mode": "unknown"}, {"scenario": "bad"}, {"seed": 1.2},
])
def test_config_rejects_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


def test_seed_reproducibility_and_every_cycle_covers_catalog():
    config = Config(seed=25)
    first = list(islice(requests_for(config), 24))
    assert first == list(islice(requests_for(config), 24))
    for start in range(0, 24, 8):
        assert {(method, path) for method, path, _ in first[start:start + 8]} == set(ENDPOINTS)
    assert first != list(islice(requests_for(Config(seed=26)), 24))
    for _method, _path, body in first:
        if body:
            for name, value in body.items():
                if name.endswith("_id") or name == "qr_code":
                    assert value.startswith("demo-")


def test_sequential_order():
    calls = list(islice(requests_for(Config(mode="sequential", seed=1)), 16))
    assert [(method, path) for method, path, _ in calls] == list(ENDPOINTS) * 2
    assert calls[:8] != calls[8:]


def test_cli_environment_and_mutually_exclusive_limits(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://api:8000")
    assert parse_args(["--count", "8"]).base_url == "http://api:8000"
    assert parse_args(["--base-url", "http://localhost:9000"]).base_url == "http://localhost:9000"
    with pytest.raises(SystemExit) as exc:
        parse_args(["--count", "8", "--duration", "1"])
    assert exc.value.code == 2


def test_all_endpoints_real_request_format_and_http_error_counts():
    received = []
    codes = [201, 400, 503, 200, 201, 201, 200, 200]

    async def handle(request):
        received.append(request)
        return httpx.Response(codes[len(received) - 1], json={"synthetic": True})

    result = asyncio.run(run(Config(count=8, rate=20, mode="sequential", scenario="qr-degraded"), transport=httpx.MockTransport(handle)))
    assert result["attempted"] == result["completed"] == 8
    assert result["transport_errors"] == 0
    assert result["status_counts"] == {"200": 3, "201": 3, "400": 1, "503": 1}
    assert all(count == 1 for count in result["endpoint_counts"].values())
    assert [(req.method, req.url.path) for req in received] == list(ENDPOINTS)
    assert all(req.headers["X-Simulation-Scenario"] == "qr-degraded" for req in received)
    assert received[3].content == b""
    assert json.loads(received[0].content)["quantity"] in range(1, 11)


def test_transport_failure_timeout_and_recovery_do_not_stop():
    calls = 0

    async def handle(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("unreachable", request=request)
        if calls == 2:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200)

    result = asyncio.run(run(Config(count=4, rate=20), transport=httpx.MockTransport(handle)))
    assert result["attempted"] == 4
    assert result["completed"] == result["transport_errors"] == 2
    assert result["transport_error_counts"] == {"timeout": 1, "transport": 1}


def test_total_timeout_and_concurrency_limit():
    active = peak = 0

    async def handle(_request):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(1)
            return httpx.Response(200)
        finally:
            active -= 1

    result = asyncio.run(run(Config(count=5, rate=20, concurrency=2, timeout=0.15), transport=httpx.MockTransport(handle)))
    assert peak == 2
    assert active == 0
    assert result["completed"] == 0
    assert result["transport_errors"] == 5
    assert result["duration_seconds"] < 1.5


def test_global_rate_has_no_initial_burst():
    starts = []

    async def handle(_request):
        starts.append(time.perf_counter())
        return httpx.Response(200)

    asyncio.run(run(Config(count=5, rate=10, concurrency=8), transport=httpx.MockTransport(handle)))
    assert all(b - a >= 0.085 for a, b in zip(starts, starts[1:]))
    assert starts[-1] - starts[0] >= 0.38


def test_duration_stops_admission_and_drains_inflight():
    async def handle(_request):
        await asyncio.sleep(0.2)
        return httpx.Response(200)

    result = asyncio.run(run(Config(duration=0.13, rate=20, concurrency=2), transport=httpx.MockTransport(handle)))
    assert result["stop_reason"] == "duration"
    assert result["attempted"] == result["completed"] == 2
    assert result["duration_seconds"] >= 0.2


def test_stop_event_interrupts_low_rate_wait_and_drains():
    async def exercise():
        stop = asyncio.Event()

        async def handle(_request):
            stop.set()
            await asyncio.sleep(0.04)
            return httpx.Response(200)

        return await run(Config(rate=0.01), stop, transport=httpx.MockTransport(handle))

    result = asyncio.run(exercise())
    assert result["attempted"] == result["completed"] == 1
    assert result["stop_reason"] == "stopped"
    assert result["duration_seconds"] < 1


def test_redirect_is_not_followed():
    received = []

    async def handle(request):
        received.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://example.com/"})

    result = asyncio.run(run(Config(count=1), transport=httpx.MockTransport(handle)))
    assert len(received) == 1
    assert result["status_counts"] == {"302": 1}


def test_cli_sigint_stops_cleanly_and_restores_handlers(monkeypatch):
    import signal
    import traffic.main as module

    original = signal.getsignal(signal.SIGINT)
    observed = []

    async def fake_run(config, stop):
        handler = signal.getsignal(signal.SIGINT)
        observed.append(callable(handler))
        handler(signal.SIGINT, None)
        await asyncio.wait_for(stop.wait(), timeout=1)
        return {"attempted": 0, "completed": 0}

    monkeypatch.setattr(module, "run", fake_run)
    assert asyncio.run(run_cli(Config())) == {"attempted": 0, "completed": 0}
    assert observed == [True]
    assert signal.getsignal(signal.SIGINT) == original
