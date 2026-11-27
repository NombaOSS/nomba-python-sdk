from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v2.cable import Cable


def test_subscribe_cable_tv_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": "SUCCESS", "id": "c1"}}
        )

    http = fake_http(handler)
    cable = Cable(http)
    result = cable.subscribe_cable_tv(
        "ref1", cableTvType="dstv", amount=100, customerId="12345", payerName="Jane Doe"
    )
    assert result["status"] == "SUCCESS"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/bill/cabletv"


def test_subscribe_cable_tv_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    cable = Cable(http)
    with pytest.raises(UnconfirmedOutcomeError):
        cable.subscribe_cable_tv(
            "ref1",
            cableTvType="dstv",
            amount=100,
            customerId="12345",
            payerName="Jane Doe",
        )


def test_subscribe_cable_tv_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    cable = Cable(http)
    result = cable.subscribe_cable_tv(
        "ref1",
        cableTvType="dstv",
        amount=100,
        customerId="12345",
        payerName="Jane Doe",
        on_pending=lambda d: "handled",
    )
    assert result == "handled"


def test_subscribe_cable_tv_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    cable = Cable(http)
    with pytest.raises(NombaError):
        cable.subscribe_cable_tv(
            "ref1",
            cableTvType="dstv",
            amount=100,
            customerId="12345",
            payerName="Jane Doe",
        )


def test_subscribe_cable_tv_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    cable = Cable(http)
    cable.subscribe_cable_tv_from_sub_account(
        "sub1",
        "ref1",
        cableTvType="dstv",
        amount=100,
        customerId="12345",
        payerName="Jane Doe",
    )
    req = captured["request"]
    assert req.url.path == "/v2/bill/cabletv/sub1"
