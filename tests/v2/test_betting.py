from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v2.betting import Betting


def test_pay_betting_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": "SUCCESS", "id": "b1"}}
        )

    http = fake_http(handler)
    betting = Betting(http)
    result = betting.pay_betting(
        "ref1",
        bettingProvider="betnaija",
        amount=100,
        customerId="12345",
        payerName="Jane Doe",
        phoneNumber="08011112222",
    )
    assert result["status"] == "SUCCESS"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/bill/betting"


def test_pay_betting_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    betting = Betting(http)
    with pytest.raises(UnconfirmedOutcomeError):
        betting.pay_betting(
            "ref1",
            bettingProvider="betnaija",
            amount=100,
            customerId="12345",
            payerName="Jane Doe",
            phoneNumber="08011112222",
        )


def test_pay_betting_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    betting = Betting(http)
    result = betting.pay_betting(
        "ref1",
        bettingProvider="betnaija",
        amount=100,
        customerId="12345",
        payerName="Jane Doe",
        phoneNumber="08011112222",
        on_pending=lambda d: "handled",
    )
    assert result == "handled"


def test_pay_betting_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    betting = Betting(http)
    with pytest.raises(NombaError):
        betting.pay_betting(
            "ref1",
            bettingProvider="betnaija",
            amount=100,
            customerId="12345",
            payerName="Jane Doe",
            phoneNumber="08011112222",
        )


def test_pay_betting_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    betting = Betting(http)
    betting.pay_betting_from_sub_account(
        "sub1",
        "ref1",
        bettingProvider="betnaija",
        amount=100,
        customerId="12345",
        payerName="Jane Doe",
        phoneNumber="08011112222",
    )
    req = captured["request"]
    assert req.url.path == "/v2/bill/betting/sub1"
