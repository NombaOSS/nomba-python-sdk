"""Checks for nomba/http.py: retries, auth envelope, refresh, headers, query.

Mirrors Node's test/http/http-client.service.test.ts.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from nomba.http import SDK_VERSION, HttpClient
from nomba.lib.errors import NombaError, OutcomeUnknownError, TokenError
from nomba.lib.token_store import MemoryTokenStore, TokenData
from nomba.v1.charge import Charge


def _token(tok: str, minutes: int = 60) -> TokenData:
    exp = datetime.now(UTC) + timedelta(minutes=minutes)
    return {
        "businessId": "b",
        "access_token": tok,
        "refresh_token": f"r-{tok}",
        "expiresAt": exp.isoformat().replace("+00:00", "Z"),
    }


def _client(answer, store=None) -> HttpClient:
    return HttpClient(
        "cid",
        "secret",
        "acct",
        "sandbox",
        token_store=store or MemoryTokenStore(),
        retry_delay_s=0,
        transport=httpx.MockTransport(answer),
    )


def test_rejects_path_without_leading_slash(fake_http):
    client = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": {}}))
    with pytest.raises(ValueError):
        client.request("GET", "accounts")  # no leading slash


def test_get_retries_on_timeout_then_succeeds(fake_http):
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.TimeoutException("slow")
        return httpx.Response(200, json={"code": "00", "data": {"ok": True}})

    client = fake_http(answer)
    result = client.request("GET", "/accounts")
    assert result == {"ok": True}
    assert calls["n"] == 2


def test_mutating_call_does_not_retry_on_timeout(fake_http):
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        raise httpx.TimeoutException("slow")

    client = fake_http(answer)
    with pytest.raises(OutcomeUnknownError) as exc_info:
        client.request(
            "POST", "/transfers", body={"merchantTxRef": "x"}, idempotency_key="x"
        )
    assert exc_info.value.idempotency_key == "x"
    assert calls["n"] == 1


def test_mutating_call_defaults_to_not_retrying(fake_http):
    """A mutating call is never auto-retried on a timeout (Node: only 429 is)."""
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        raise httpx.TimeoutException("slow")

    client = fake_http(answer)
    with pytest.raises(OutcomeUnknownError):
        client.request("POST", "/transfers", body={"merchantTxRef": "x"})
    assert calls["n"] == 1


def test_mutating_call_does_not_retry_on_connect_error(fake_http):
    """Non-timeout transport errors (e.g. a connection reset) must also be
    treated as an uncertain outcome, not silently swallowed or retried."""
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        raise httpx.ConnectError("reset")

    client = fake_http(answer)
    with pytest.raises(OutcomeUnknownError):
        client.request("POST", "/transfers", body={"merchantTxRef": "x"})
    assert calls["n"] == 1


def test_get_retries_on_connect_error_then_succeeds(fake_http):
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectError("reset")
        return httpx.Response(200, json={"code": "00", "data": {"ok": True}})

    client = fake_http(answer)
    result = client.request("GET", "/accounts")
    assert result == {"ok": True}
    assert calls["n"] == 2


def test_second_401_raises_token_error(fake_http):
    def answer(req):
        return httpx.Response(401, json={"code": "401", "description": "bad token"})

    client = fake_http(answer)
    with pytest.raises(TokenError):
        client.request("GET", "/accounts")


def test_envelope_unwraps_data(fake_http):
    client = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": {"id": "a1"}})
    )
    assert client.request("GET", "/accounts") == {"id": "a1"}


def test_429_retried_with_backoff(fake_http):
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(429, json={"code": "429", "description": "slow down"})
        return httpx.Response(200, json={"code": "00", "data": {"ok": True}})

    client = fake_http(answer)
    result = client.request("POST", "/transfers", body={"merchantTxRef": "y"})
    assert result == {"ok": True}
    assert calls["n"] == 2


def test_429_honors_retry_after_header(fake_http, monkeypatch):
    sleeps = []
    monkeypatch.setattr("nomba.http.time.sleep", lambda s: sleeps.append(s))
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(
                429,
                headers={"Retry-After": "5"},
                json={"code": "429", "description": "slow down"},
            )
        return httpx.Response(200, json={"code": "00", "data": {"ok": True}})

    client = fake_http(answer)
    result = client.request("POST", "/transfers", body={"merchantTxRef": "z"})
    assert result == {"ok": True}
    assert sleeps == [5.0]


def test_429_retry_after_is_capped_at_60s(fake_http, monkeypatch):
    sleeps = []
    monkeypatch.setattr("nomba.http.time.sleep", lambda s: sleeps.append(s))
    calls = {"n": 0}

    def answer(req):
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(
                429,
                headers={"Retry-After": "120"},
                json={"code": "429", "description": "slow down"},
            )
        return httpx.Response(200, json={"code": "00", "data": {"ok": True}})

    client = fake_http(answer)
    client.request("POST", "/transfers", body={"merchantTxRef": "z2"})
    assert sleeps == [60.0]


def test_issues_token_from_envelope_then_sends_bearer_and_sdk_headers():
    seen = []

    def answer(req):
        seen.append(req)
        if req.url.path == "/v1/auth/token/issue":
            assert json.loads(req.content)["grant_type"] == "client_credentials"
            return httpx.Response(200, json={"code": "00", "data": _token("t1")})
        return httpx.Response(200, json={"code": "00", "data": {"ok": True}})

    assert _client(answer).request("GET", "/v1/accounts/parent") == {"ok": True}
    req = seen[1]
    assert req.headers["Authorization"] == "Bearer t1"
    assert req.headers["accountId"] == "acct"
    assert req.headers["X-Nomba-Sdk-Version"] == SDK_VERSION
    assert req.headers["User-Agent"] == f"nomba_python_sdk:v{SDK_VERSION}"


def test_near_expiry_token_is_refreshed_not_reissued():
    store = MemoryTokenStore()
    store.set(_token("old", minutes=2))
    paths = []

    def answer(req):
        paths.append(req.url.path)
        if req.url.path == "/v1/auth/token/refresh":
            assert req.headers["Authorization"] == "Bearer old"
            assert json.loads(req.content)["refresh_token"] == "r-old"
            return httpx.Response(200, json={"code": "00", "data": _token("new")})
        return httpx.Response(200, json={"code": "00", "data": {}})

    _client(answer, store).request("GET", "/v1/x")
    assert paths == ["/v1/auth/token/refresh", "/v1/x"]
    token = store.get()
    assert token is not None and token["access_token"] == "new"


def test_mutating_call_is_sent_once_on_5xx_with_callers_key():
    calls = []

    def answer(req):
        if req.url.path == "/v1/auth/token/issue":
            return httpx.Response(200, json={"code": "00", "data": _token("t")})
        calls.append(req)
        return httpx.Response(503, json={"code": "503", "description": "down"})

    with pytest.raises(OutcomeUnknownError) as e:
        Charge(_client(answer)).cancel_transaction("txn-1", False)
    assert len(calls) == 1
    assert e.value.idempotency_key == "txn-1"


def test_unreadable_2xx_on_mutating_call_is_unknown_not_rejected():
    def answer(req):
        if req.url.path == "/v1/auth/token/issue":
            return httpx.Response(200, json={"code": "00", "data": _token("t")})
        return httpx.Response(200, content=b'{"code":"00","da')

    with pytest.raises(OutcomeUnknownError):
        _client(answer).request("POST", "/v1/x", body={})


def test_get_retries_in_flight_409_but_not_a_key_conflict():
    replies = iter(
        [
            httpx.Response(409, json={"code": "409", "description": "being processed"}),
            httpx.Response(200, json={"code": "00", "data": 1}),
        ]
    )

    def answer(req):
        if req.url.path == "/v1/auth/token/issue":
            return httpx.Response(200, json={"code": "00", "data": _token("t")})
        return next(replies)

    assert _client(answer).request("GET", "/v1/x") == 1

    def conflict(req):
        if req.url.path == "/v1/auth/token/issue":
            return httpx.Response(200, json={"code": "00", "data": _token("t")})
        return httpx.Response(409, json={"code": "409", "description": "duplicate"})

    with pytest.raises(NombaError):
        _client(conflict).request("GET", "/v1/x")


def test_query_booleans_match_js():
    seen = []

    def answer(req):
        if req.url.path == "/v1/auth/token/issue":
            return httpx.Response(200, json={"code": "00", "data": _token("t")})
        seen.append(req)
        return httpx.Response(200, json={"code": "00", "data": []})

    _client(answer).request(
        "GET", "/v1/x", query={"isMobileMoney": False, "cursor": None, "limit": 10}
    )
    assert seen[0].url.query == b"isMobileMoney=false&limit=10"
