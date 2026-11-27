from __future__ import annotations

import httpx

from nomba.v1.requery import Requery, Transaction


def _tx() -> dict:
    return {
        "id": "tx1",
        "status": "SUCCESS",
        "amount": 1000,
        "source": "api",
        "type": "transfer",
        "gatewayMessage": "Approved",
        "timeCreated": "2024-01-01T00:00:00Z",
        "merchantTxRef": "ref1",
    }


def test_fetch_parent_transaction_returns_transaction(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _tx()})

    http = fake_http(handler)
    requery = Requery(http)
    result = requery.fetch_parent_transaction(merchantTxRef="ref1")
    assert isinstance(result, Transaction)
    assert result.id == "tx1"
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/transactions/accounts/single"
    assert req.url.params["merchantTxRef"] == "ref1"


def test_fetch_sub_account_transaction_returns_transaction(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _tx()})

    http = fake_http(handler)
    requery = Requery(http)
    result = requery.fetch_sub_account_transaction("sub1", transactionRef="tref1")
    assert isinstance(result, Transaction)
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/transactions/accounts/sub1/single"
    assert req.url.params["transactionRef"] == "tref1"


def test_requery_by_session_returns_transaction(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": _tx()})

    http = fake_http(handler)
    requery = Requery(http)
    result = requery.requery_by_session("sess1")
    assert isinstance(result, Transaction)
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/transactions/requery/sess1"
