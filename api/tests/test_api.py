"""Pruebas locales; las respuestas usan ASGI real, sin Docker ni ELK."""

from collections import Counter
from datetime import datetime
import json
import random
from time import perf_counter_ns
from uuid import UUID

from fastapi.testclient import TestClient
import pytest

from api.catalog import CATALOG
from api.config import Profile, Settings
from api.main import create_app


REQUESTS = [
    ("POST", "/api/v1/purchases", {"coupon_id": "demo-coupon-001", "quantity": 1}, "INC-01", "Compras y pagos", 201),
    ("POST", "/api/v1/coupons/issue", {"purchase_id": "demo-purchase-001"}, "INC-02", "QR y canje", 201),
    ("POST", "/api/v1/coupons/redeem", {"qr_code": "demo-qr-001", "merchant_id": "demo-merchant-001"}, "INC-03", "QR y canje", 200),
    ("GET", "/api/v1/platform/status", None, "INC-04", "Plataforma", 200),
    ("POST", "/api/v1/merchants", {"merchant_id": "demo-merchant-001", "action": "create"}, "SR-01", "Comercios", 201),
    ("POST", "/api/v1/promotions", {"promotion_id": "demo-promotion-001", "merchant_id": "demo-merchant-001", "action": "publish"}, "SR-02", "Promociones", 201),
    ("POST", "/api/v1/accounts/recovery", {"account_id": "demo-account-001", "action": "unlock"}, "SR-03", "Cuentas y accesos", 200),
    ("POST", "/api/v1/refunds", {"purchase_id": "demo-purchase-001", "action": "refund"}, "SR-04", "Reembolsos", 200),
]


def configured(tmp_path, **overrides):
    env = {"API_LOG_PATH": str(tmp_path / "events.log"), "API_SEED": "12",
           "API_SUCCESS_RATE": "1", "API_CLIENT_ERROR_RATE": "0", "API_SERVER_ERROR_RATE": "0",
           "API_LATENCY_MIN_MS": "0", "API_LATENCY_MAX_MS": "0",
           "QR_LATENCY_MIN_MS": "0", "QR_LATENCY_MAX_MS": "0"}
    env.update(overrides)
    settings = Settings.from_env(env)
    return create_app(settings), settings.log_path


def events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("method,path,body,catalog,component,success", REQUESTS)
@pytest.mark.parametrize("kind,status,rates", [
    ("success", None, (1, 0, 0)), ("client_error", 400, (0, 1, 0)), ("server_error", 503, (0, 0, 1)),
])
def test_catalog_responses_match_log(tmp_path, method, path, body, catalog, component, success, kind, status, rates):
    app, log_path = configured(tmp_path, **dict(zip(
        ("API_SUCCESS_RATE", "API_CLIENT_ERROR_RATE", "API_SERVER_ERROR_RATE"), map(str, rates))))
    with TestClient(app) as client:
        before = perf_counter_ns()
        response = client.request(method, path, json=body) if body else client.request(method, path)
        elapsed = perf_counter_ns() - before
    assert response.status_code == (status or success)
    result = response.json()
    assert result["synthetic"] is True
    assert result["catalog_item"] == catalog and result["component"] == component
    assert result["outcome"] == kind and result["scenario"] == "normal"
    assert ("data" if kind == "success" else "error") in result
    records = events(log_path)
    assert len(records) == 1
    log = records[0]
    assert log["http.request.method"] == method
    assert log["http.response.status_code"] == response.status_code
    assert log["url.path"] == path
    assert log["service.name"] == "cuponmania-api"
    assert log["log.level"] == {"success": "INFO", "client_error": "WARN", "server_error": "ERROR"}[kind]
    assert log["catalog_item"] == catalog and log["component"] == component
    assert log["scenario"] == "normal" and log["cuponmania.synthetic"] is True
    assert log["request_id"] == result["request_id"] == response.headers["X-Request-ID"]
    UUID(log["request_id"])
    UUID(log["event.id"])
    assert datetime.fromisoformat(log["@timestamp"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0
    assert type(log["event.duration"]) is int and 0 < log["event.duration"] <= elapsed


@pytest.mark.parametrize("env", [
    {"API_SUCCESS_RATE": "nan"}, {"API_CLIENT_ERROR_RATE": "inf"},
    {"API_SUCCESS_RATE": "-0.1"}, {"API_SUCCESS_RATE": "1.1"},
    {"API_SUCCESS_RATE": "0.5"}, {"API_LATENCY_MIN_MS": "-1"},
    {"API_LATENCY_MIN_MS": "351"}, {"API_LATENCY_MAX_MS": "10001"},
    {"API_LATENCY_MAX_MS": "inf"}, {"API_LATENCY_MIN_MS": "nan"},
    {"QR_SUCCESS_RATE": "nan"}, {"QR_LATENCY_MAX_MS": "bad"},
    {"API_SCENARIO": "unknown"}, {"API_SEED": "1.5"}, {"API_LOG_PATH": ""},
])
def test_invalid_configuration_rejected(env):
    with pytest.raises(ValueError):
        Settings.from_env(env)


def test_seeded_probability_distribution_and_latency_range():
    profile = Settings.from_env({}).normal
    first, second = random.Random(19), random.Random(19)
    draws = [profile.sample(first) for _ in range(20000)]
    assert draws == [profile.sample(second) for _ in range(20000)]
    counts = Counter(outcome for outcome, delay in draws)
    assert 0.89 < counts["success"] / len(draws) < 0.91
    assert 0.04 < counts["client_error"] / len(draws) < 0.06
    assert 0.04 < counts["server_error"] / len(draws) < 0.06
    assert all(.080 <= delay <= .350 for outcome, delay in draws)
    assert len({delay for outcome, delay in draws}) > 100


def test_actual_duration_is_nanoseconds_and_varies(tmp_path):
    app, log_path = configured(tmp_path, API_LATENCY_MIN_MS="5", API_LATENCY_MAX_MS="30")
    with TestClient(app) as client:
        before = perf_counter_ns()
        for _ in range(12):
            assert client.get("/api/v1/platform/status").status_code == 200
        elapsed = perf_counter_ns() - before
    durations = [row["event.duration"] for row in events(log_path)]
    assert min(durations) >= 5_000_000
    assert sum(durations) <= elapsed
    assert max(durations) - min(durations) > 1_000_000


def test_health_is_stable_and_scenario_independent(tmp_path):
    app, log_path = configured(tmp_path, API_SUCCESS_RATE="0", API_SERVER_ERROR_RATE="1",
                               API_LATENCY_MIN_MS="10000", API_LATENCY_MAX_MS="10000")
    with TestClient(app) as client:
        for _ in range(5):
            response = client.get("/healthz", headers={"X-Simulation-Scenario": "invalid-secret"})
            assert response.status_code == 200
            assert response.json() == {"status": "ok", "synthetic": True}
    assert all(row["scenario"] == "health" and row["catalog_item"] is None for row in events(log_path))


def test_qr_degradation_affects_only_qr(tmp_path):
    app, log_path = configured(tmp_path, QR_SUCCESS_RATE="0", QR_CLIENT_ERROR_RATE="0", QR_SERVER_ERROR_RATE="1")
    with TestClient(app) as client:
        for method, path, body, catalog, component, success in REQUESTS:
            response = client.request(method, path, json=body, headers={"X-Simulation-Scenario": "qr-degraded"})
            assert response.status_code == (503 if catalog in ("INC-02", "INC-03") else success)
        assert client.post("/api/v1/coupons/issue", json={"purchase_id": "demo-id"},
                           headers={"X-Simulation-Scenario": "normal"}).status_code == 201
    assert all(row["scenario"] == "qr-degraded" for row in events(log_path)[:-1])


@pytest.mark.parametrize("body", [None, {}, {"coupon_id": "demo-id", "quantity": "1"},
    {"coupon_id": "demo-id", "quantity": True}, {"coupon_id": "demo-id", "quantity": 0},
    {"coupon_id": "demo-id", "quantity": 11}, {"coupon_id": "secret@example.com", "quantity": 1},
    {"coupon_id": "x" * 65, "quantity": 1}, {"coupon_id": "demo-id", "quantity": 1, "password": "SECRET_TOKEN"},
])
def test_validation_does_not_echo_input(tmp_path, body):
    app, log_path = configured(tmp_path)
    with TestClient(app) as client:
        response = client.post("/api/v1/purchases?token=SECRET_QUERY", json=body,
                               headers={"Authorization": "Bearer SECRET_HEADER", "X-Request-ID": "SECRET_ID"})
    assert response.status_code == 422
    assert "SECRET" not in response.text and "secret@example.com" not in response.text
    log_text = log_path.read_text(encoding="utf-8")
    assert "SECRET" not in log_text and "secret@example.com" not in log_text
    assert len(events(log_path)) == 1 and events(log_path)[0]["url.path"] == "/api/v1/purchases"


def test_invalid_json_invalid_scenario_and_routing_logged_once(tmp_path):
    app, log_path = configured(tmp_path)
    with TestClient(app) as client:
        responses = [
            client.post("/api/v1/purchases", content='{"SECRET_BROKEN":', headers={"Content-Type": "application/json"}),
            client.get("/api/v1/platform/status", headers={"X-Simulation-Scenario": "SECRET_SCENARIO"}),
            client.get("/not-found"), client.get("/api/v1/purchases"),
        ]
        assert [r.status_code for r in responses] == [422, 422, 404, 405]
        assert all("SECRET" not in r.text for r in responses)
    assert [row["http.response.status_code"] for row in events(log_path)] == [422, 422, 404, 405]
    assert "SECRET" not in log_path.read_text(encoding="utf-8")


def test_unexpected_exception_is_500_without_secret_or_duplicate(tmp_path):
    app, log_path = configured(tmp_path)

    @app.get("/test-crash")
    async def crash():
        raise RuntimeError("SECRET_EXCEPTION")

    with TestClient(app) as client:
        response = client.get("/test-crash")
    assert response.status_code == 500 and "SECRET" not in response.text
    rows = events(log_path)
    assert len(rows) == 1 and rows[0]["http.response.status_code"] == 500
    assert rows[0]["log.level"] == "ERROR"
    assert "SECRET" not in log_path.read_text(encoding="utf-8")


def test_openapi_has_eight_business_routes_without_ui(tmp_path):
    app, log_path = configured(tmp_path)
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
        for method, path, *_ in REQUESTS:
            assert method.lower() in schema["paths"][path]
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404


def test_logs_append_across_app_instances(tmp_path):
    ids = []
    for _ in range(2):
        app, log_path = configured(tmp_path)
        with TestClient(app) as client:
            ids.append(client.get("/healthz").headers["X-Request-ID"])
    assert len(events(log_path)) == 2
    assert len(set(ids)) == 2


def test_log_path_failure_prevents_startup(tmp_path):
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("test", encoding="utf-8")
    with pytest.raises(OSError):
        configured(tmp_path, API_LOG_PATH=str(blocking_file / "events.log"))
