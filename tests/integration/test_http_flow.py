"""Integración TCP real entre Uvicorn, clientes HTTP y CLI; sin Docker."""

from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from itertools import islice
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import UUID

import httpx
import pytest

from traffic.main import Config, requests_for


ROOT = Path(__file__).resolve().parents[2]
CATALOG = {
    "/api/v1/purchases": ("INC-01", "Compras y pagos", 201),
    "/api/v1/coupons/issue": ("INC-02", "QR y canje", 201),
    "/api/v1/coupons/redeem": ("INC-03", "QR y canje", 200),
    "/api/v1/platform/status": ("INC-04", "Plataforma", 200),
    "/api/v1/merchants": ("SR-01", "Comercios", 201),
    "/api/v1/promotions": ("SR-02", "Promociones", 201),
    "/api/v1/accounts/recovery": ("SR-03", "Cuentas y accesos", 200),
    "/api/v1/refunds": ("SR-04", "Reembolsos", 200),
}
HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def available_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


class LiveAPI:
    def __init__(self, directory, **overrides):
        self.port = available_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.log_path = directory / "api.log"
        self.stderr_path = directory / "uvicorn.txt"
        self.process = None
        self.output = None
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(("API_", "QR_"))}
        self.env.update({
            "API_LOG_PATH": str(self.log_path), "API_SEED": "17", "API_SCENARIO": "normal",
            "API_SUCCESS_RATE": "1", "API_CLIENT_ERROR_RATE": "0", "API_SERVER_ERROR_RATE": "0",
            "API_LATENCY_MIN_MS": "2", "API_LATENCY_MAX_MS": "15",
            "QR_SUCCESS_RATE": "0", "QR_CLIENT_ERROR_RATE": "0", "QR_SERVER_ERROR_RATE": "1",
            "QR_LATENCY_MIN_MS": "20", "QR_LATENCY_MAX_MS": "30",
            **overrides,
        })

    def start(self):
        self.output = self.stderr_path.open("a", encoding="utf-8")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1",
             "--port", str(self.port), "--workers", "1", "--no-access-log", "--log-level", "warning"],
            cwd=ROOT, env=self.env, stdout=self.output, stderr=subprocess.STDOUT, creationflags=HIDDEN,
        )
        deadline = time.monotonic() + 10
        with httpx.Client(trust_env=False, timeout=.25) as client:
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise AssertionError(self.stderr_path.read_text(encoding="utf-8"))
                try:
                    if client.get(self.url + "/healthz").status_code == 200:
                        return
                except httpx.RequestError:
                    pass
                time.sleep(.03)
        raise AssertionError("La API local no inició en 10 segundos")

    def stop(self):
        if self.process is not None:
            stop_process(self.process)
        if self.output is not None:
            self.output.close()

    def records(self, expected_business=None):
        deadline = time.monotonic() + 3
        while True:
            try:
                rows = [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]
                if expected_business is None or sum(row["catalog_item"] is not None for row in rows) >= expected_business:
                    return rows
            except (FileNotFoundError, json.JSONDecodeError):
                pass  # The writer may still be completing the final line.
            if time.monotonic() > deadline:
                raise AssertionError("No llegaron los logs HTTP esperados")
            time.sleep(.01)


@contextmanager
def live_api(tmp_path, **overrides):
    api = LiveAPI(tmp_path, **overrides)
    try:
        api.start()
        yield api
    finally:
        api.stop()


def cli_command(base_url, *args):
    return [sys.executable, "-m", "traffic.main", "--base-url", base_url, *map(str, args)]


def run_cli(base_url, *args):
    result = subprocess.run(cli_command(base_url, *args), cwd=ROOT, capture_output=True,
                            text=True, timeout=20, creationflags=HIDDEN)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return json.loads(result.stdout)


def validate_record(record):
    assert datetime.fromisoformat(record["@timestamp"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0
    assert record["http.request.method"] in {"GET", "POST"}
    assert type(record["http.response.status_code"]) is int
    assert type(record["event.duration"]) is int and record["event.duration"] > 0
    assert record["service.name"] == "cuponmania-api"
    status = record["http.response.status_code"]
    assert record["log.level"] == ("ERROR" if status >= 500 else "WARN" if status >= 400 else "INFO")
    assert record["cuponmania.synthetic"] is True
    UUID(record["event.id"])
    UUID(record["request_id"])
    if record["catalog_item"] is not None:
        catalog, component, _ = CATALOG[record["url.path"]]
        assert (record["catalog_item"], record["component"]) == (catalog, component)


@pytest.mark.parametrize("rates,forced_status", [(("1", "0", "0"), None),
                                                  (("0", "1", "0"), 400),
                                                  (("0", "0", "1"), 503)])
def test_eight_routes_codes_and_exact_response_log_correlation(tmp_path, rates, forced_status):
    overrides = dict(zip(("API_SUCCESS_RATE", "API_CLIENT_ERROR_RATE", "API_SERVER_ERROR_RATE"), rates))
    with live_api(tmp_path, **overrides) as api:
        sent = {}
        with httpx.Client(base_url=api.url, trust_env=False, timeout=2) as client:
            for method, path, body in islice(requests_for(Config(mode="sequential", seed=1)), 8):
                before = time.perf_counter_ns()
                response = client.request(method, path, **({"json": body} if body else {}))
                elapsed = time.perf_counter_ns() - before
                assert response.status_code == (forced_status or CATALOG[path][2])
                payload = response.json()
                request_id = response.headers["x-request-id"]
                assert payload["request_id"] == request_id and payload["synthetic"] is True
                sent[request_id] = (method, path, response.status_code, elapsed)
            assert client.get("/healthz", headers={"X-Simulation-Scenario": "invalid"}).json() == {"status": "ok", "synthetic": True}
        rows = api.records(expected_business=8)
    business = [row for row in rows if row["catalog_item"] is not None]
    assert len(business) == 8
    assert len({row["event.id"] for row in rows}) == len(rows)
    assert len({row["request_id"] for row in rows}) == len(rows)
    for row in rows:
        validate_record(row)
        if row["catalog_item"] is not None:
            method, path, status, elapsed = sent[row["request_id"]]
            assert (row["http.request.method"], row["url.path"], row["http.response.status_code"]) == (method, path, status)
            assert 2_000_000 <= row["event.duration"] <= elapsed


def test_cli_64_http_requests_cover_catalog_and_match_logged_counts(tmp_path):
    with live_api(tmp_path, API_SUCCESS_RATE="0.5", API_CLIENT_ERROR_RATE="0.25", API_SERVER_ERROR_RATE="0.25") as api:
        summary = run_cli(api.url, "--count", 64, "--rate", 20, "--concurrency", 4,
                          "--mode", "random", "--seed", 11)
        rows = api.records(expected_business=64)
    business = [row for row in rows if row["catalog_item"] is not None]
    assert summary["attempted"] == summary["completed"] == len(business) == 64
    assert summary["transport_errors"] == summary["cancelled"] == 0
    assert summary["stop_reason"] == "count"
    assert summary["status_counts"] == dict(Counter(str(row["http.response.status_code"]) for row in business))
    assert summary["endpoint_counts"] == dict(Counter(row["url.path"] for row in business))
    assert set(summary["endpoint_counts"].values()) == {8}
    assert {200, 400, 500} == {row["http.response.status_code"] // 100 * 100 for row in business}
    assert len({row["request_id"] for row in business}) == len(business)
    assert len({row["event.duration"] for row in business}) > 1
    assert sum(row["event.duration"] for row in business) > 64 * 2_000_000
    for row in rows:
        validate_record(row)


def test_qr_profile_and_duration_cli_over_tcp(tmp_path):
    with live_api(tmp_path) as api:
        summary = run_cli(api.url, "--duration", 1, "--rate", 20, "--concurrency", 2,
                          "--mode", "sequential", "--scenario", "qr-degraded")
        rows = api.records(expected_business=summary["completed"])
    business = [row for row in rows if row["catalog_item"] is not None]
    assert summary["stop_reason"] == "duration"
    assert summary["attempted"] == summary["completed"] >= 8
    assert summary["transport_errors"] == 0
    assert summary["duration_seconds"] >= 1
    assert len(business) == summary["completed"]
    for row in business:
        is_qr = row["catalog_item"] in {"INC-02", "INC-03"}
        assert row["scenario"] == "qr-degraded"
        assert row["http.response.status_code"] == (503 if is_qr else CATALOG[row["url.path"]][2])
        assert row["event.duration"] >= (20_000_000 if is_qr else 2_000_000)


def test_real_validation_errors_are_logged_without_input_secrets(tmp_path):
    with live_api(tmp_path) as api:
        with httpx.Client(base_url=api.url, trust_env=False, timeout=2) as client:
            replies = [client.post("/api/v1/purchases?token=SECRET_QUERY",
                                   json={"coupon_id": "demo-id", "quantity": 1, "password": "SECRET_BODY"},
                                   headers={"Authorization": "Bearer SECRET_HEADER"}),
                       client.get("/api/v1/platform/status", headers={"X-Simulation-Scenario": "SECRET_SCENARIO"}),
                       client.get("/not-found"), client.get("/api/v1/purchases")]
        assert [reply.status_code for reply in replies] == [422, 422, 404, 405]
        assert all("SECRET" not in reply.text for reply in replies)
        rows = api.records(expected_business=3)
    assert "SECRET" not in api.log_path.read_text(encoding="utf-8")
    sent_ids = {reply.headers["x-request-id"] for reply in replies}
    logged = [row for row in rows if row["request_id"] in sent_ids]
    assert len(logged) == 4
    assert Counter(row["http.response.status_code"] for row in logged) == Counter([422, 422, 404, 405])


def test_generator_survives_actual_api_stop_and_restart(tmp_path):
    with live_api(tmp_path) as api:
        process = subprocess.Popen(cli_command(api.url, "--duration", 4, "--rate", 10,
                                              "--concurrency", 2, "--timeout", .2),
                                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, creationflags=HIDDEN)
        try:
            api.records(expected_business=2)
            api.stop()
            time.sleep(.7)
            api.start()
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, stderr
            summary = json.loads(stdout)
            rows = api.records()
        finally:
            stop_process(process)
    assert summary["completed"] > 2 and summary["transport_errors"] > 0
    assert summary["attempted"] == summary["completed"] + summary["transport_errors"]
    assert summary["stop_reason"] == "duration"
    # Restart preserves the same file; health marks the two successful startups.
    health_indices = [i for i, row in enumerate(rows) if row["url.path"] == "/healthz"]
    assert len(health_indices) >= 2
    assert any(row["catalog_item"] is not None for row in rows[health_indices[-1] + 1:])
    assert len({row["event.id"] for row in rows}) == len(rows)


def test_continuous_cli_signal_stops_after_real_tcp_traffic(tmp_path):
    # raise_signal executes a real Python signal inside a child process on both
    # Windows and POSIX; parent PTY test separately checks keyboard Ctrl+C.
    with live_api(tmp_path) as api:
        code = (
            "import signal, threading; from traffic.main import main; "
            "timer=threading.Timer(1.0, lambda: signal.raise_signal(signal.SIGINT)); "
            "timer.start(); "
            f"raise SystemExit(main(['--base-url',{api.url!r},'--rate','10','--timeout','0.5']))"
        )
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                                text=True, timeout=10, creationflags=HIDDEN)
        assert result.returncode == 0, result.stderr
        summary = json.loads(result.stdout)
        rows = api.records(expected_business=summary["completed"])
    assert summary["stop_reason"] == "stopped"
    assert summary["attempted"] == summary["completed"] > 0
    assert summary["transport_errors"] == summary["cancelled"] == 0
    assert summary["duration_seconds"] < 4
    assert sum(row["catalog_item"] is not None for row in rows) == summary["completed"]
