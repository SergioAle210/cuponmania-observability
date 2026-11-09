"""Destino real (API de preproducción): solo HTTPS al host permitido, tasa baja y peticiones que no crean datos."""

import asyncio
from itertools import islice
import re
import uuid

import httpx
import pytest

from traffic.main import (
    REAL_DEFAULT_URL,
    REAL_ENDPOINTS,
    USER_AGENT,
    Config,
    parse_args,
    real_base_url,
    real_requests_for,
    run,
)


@pytest.mark.parametrize("url", [
    "http://api-preprod.cuponmania.com.gt",  # sin TLS
    "https://api.cuponmania.com.gt",  # producción nunca
    "https://cuponmania.com.gt",
    "https://api-preprod.cuponmania.com.gt.evil.test",
    "https://user:secret@api-preprod.cuponmania.com.gt",
    "https://api-preprod.cuponmania.com.gt:8443",
    "https://api-preprod.cuponmania.com.gt/api",
    "https://api-preprod.cuponmania.com.gt?x=1",
    "https://api-preprod.cuponmania.com.gt#f",
    "https://127.0.0.1",
    "",
])
def test_real_rejects_any_other_destination(url):
    with pytest.raises(ValueError):
        real_base_url(url)


@pytest.mark.parametrize("url", [REAL_DEFAULT_URL, REAL_DEFAULT_URL + "/"])
def test_real_accepts_the_preprod_host(url):
    assert real_base_url(url) == REAL_DEFAULT_URL


@pytest.mark.parametrize("kwargs", [
    {"rate": 2.5}, {"concurrency": 3}, {"scenario": "qr-degraded"}, {"base_url": "http://127.0.0.1:8000"},
])
def test_real_limits(kwargs):
    with pytest.raises(ValueError):
        Config(**{"target": "real", "base_url": REAL_DEFAULT_URL, **kwargs})


def test_local_target_is_unchanged_default():
    config = parse_args([])
    assert config.target == "local"
    assert config.base_url == "http://127.0.0.1:8000"
    with pytest.raises(ValueError):
        Config(target="local", base_url=REAL_DEFAULT_URL)


def test_real_cli_defaults_to_preprod():
    config = parse_args(["--target", "real", "--rate", "1", "--concurrency", "1"])
    assert (config.target, config.base_url, config.rate) == ("real", REAL_DEFAULT_URL, 1.0)


def test_real_cycles_cover_every_route_with_fictitious_ids_and_reproduce_with_a_seed():
    config = Config(target="real", base_url=REAL_DEFAULT_URL, seed=7)
    calls = list(islice(real_requests_for(config), len(REAL_ENDPOINTS) * 3))
    assert calls == list(islice(real_requests_for(config), len(REAL_ENDPOINTS) * 3))
    size = len(REAL_ENDPOINTS)
    for start in range(0, len(calls), size):
        assert {(m, t) for m, t, _p, _b in calls[start:start + size]} == {(m, t) for m, t, _b in REAL_ENDPOINTS}
    for _method, template, path, _body in calls:
        assert "{" not in path
        if "{id}" in template:
            uuid.UUID(re.search(r"[0-9a-f-]{36}", path).group(0))
        if "{code}" in template:
            assert re.search(r"/DEMO-\d{6}(/|$)", path)


def test_real_routes_never_create_data():
    # Every write goes to a route the API refuses without a session (401) or with an empty body (400).
    writes = {(m, t) for m, t, _b in REAL_ENDPOINTS if m != "GET"}
    assert writes == {
        ("POST", "/api/v1/me/checkout"),
        ("POST", "/api/v1/me/sales/{id}/confirm-payment"),
        ("POST", "/api/v1/redemptions/{code}/redeem"),
        ("POST", "/api/v1/businesses"),
        ("PATCH", "/api/v1/coupons/{id}"),
        ("POST", "/api/v1/account-recovery/request"),
        ("POST", "/api/v1/refunds"),
    }
    assert all(body in ({}, None) for _m, _t, body in REAL_ENDPOINTS)


def test_real_run_sends_no_credentials_and_a_uuid_request_id():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(401 if request.method != "GET" else 200)

    config = Config(target="real", base_url=REAL_DEFAULT_URL, count=len(REAL_ENDPOINTS), rate=2, concurrency=2, seed=3, mode="sequential")
    summary = asyncio.run(run(config, transport=httpx.MockTransport(handler)))
    assert summary["attempted"] == len(REAL_ENDPOINTS)
    assert summary["target"] == "real"
    assert set(summary["endpoint_counts"]) == {t for _m, t, _b in REAL_ENDPOINTS}
    for request in seen:
        assert request.url.scheme == "https" and request.url.host == "api-preprod.cuponmania.com.gt"
        assert "authorization" not in request.headers and "cookie" not in request.headers
        assert "x-simulation-scenario" not in request.headers
        assert request.headers["user-agent"] == USER_AGENT
        uuid.UUID(request.headers["x-request-id"])
    assert len({r.headers["x-request-id"] for r in seen}) == len(seen)
