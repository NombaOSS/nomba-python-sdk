from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v2.airtime import Airtime


def test_buy_airtime_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": "SUCCESS", "id": "a1"}}
        )

    http = fake_http(handler)
    airtime = Airtime(http)
    result = airtime.buy_airtime(
        "ref1", amount=100, phoneNumber="08011112222", network="MTN"
    )
    assert result["status"] == "SUCCESS"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/bill/topup"


def test_buy_airtime_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    airtime = Airtime(http)
    with pytest.raises(UnconfirmedOutcomeError):
        airtime.buy_airtime(
            "ref1", amount=100, phoneNumber="08011112222", network="MTN"
        )


def test_buy_airtime_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    airtime = Airtime(http)
    result = airtime.buy_airtime(
        "ref1",
        amount=100,
        phoneNumber="08011112222",
        network="MTN",
        on_pending=lambda data: "handled",
    )
    assert result == "handled"


def test_buy_airtime_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    airtime = Airtime(http)
    with pytest.raises(NombaError):
        airtime.buy_airtime(
            "ref1", amount=100, phoneNumber="08011112222", network="MTN"
        )


def test_buy_airtime_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    airtime = Airtime(http)
    airtime.buy_airtime_from_sub_account(
        "sub1", "ref1", amount=100, phoneNumber="08011112222", network="MTN"
    )
    req = captured["request"]
    assert req.url.path == "/v2/bill/topup/sub1"
