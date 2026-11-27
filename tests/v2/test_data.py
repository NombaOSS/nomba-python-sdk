from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v2.data import Data


def test_buy_data_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": "SUCCESS", "id": "d1"}}
        )

    http = fake_http(handler)
    data = Data(http)
    result = data.buy_data(
        "ref1", productId="mtn1", phoneNumber="08011112222", network="MTN"
    )
    assert result["status"] == "SUCCESS"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/bill/data"


def test_buy_data_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    data = Data(http)
    with pytest.raises(UnconfirmedOutcomeError):
        data.buy_data(
            "ref1", productId="mtn1", phoneNumber="08011112222", network="MTN"
        )


def test_buy_data_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    data = Data(http)
    result = data.buy_data(
        "ref1",
        productId="mtn1",
        phoneNumber="08011112222",
        network="MTN",
        on_pending=lambda d: "handled",
    )
    assert result == "handled"


def test_buy_data_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    data = Data(http)
    with pytest.raises(NombaError):
        data.buy_data(
            "ref1", productId="mtn1", phoneNumber="08011112222", network="MTN"
        )


def test_buy_data_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    data = Data(http)
    data.buy_data_from_sub_account(
        "sub1", "ref1", productId="mtn1", phoneNumber="08011112222", network="MTN"
    )
    req = captured["request"]
    assert req.url.path == "/v2/bill/data/sub1"
