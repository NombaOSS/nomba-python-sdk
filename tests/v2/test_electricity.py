from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v2.electricity import Electricity, MeterLookupResult


def test_lookup_meter(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"name": "Jane Doe", "address": "unknown"}}
        )

    http = fake_http(handler)
    electricity = Electricity(http)
    result = electricity.lookup_meter(disco="enugu", customerId="12345")
    assert result == MeterLookupResult(name="Jane Doe", address="unknown")
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v2/bill/electricity/lookup"


def test_pay_electricity_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": "SUCCESS", "id": "e1"}}
        )

    http = fake_http(handler)
    electricity = Electricity(http)
    result = electricity.pay_electricity(
        "ref1",
        disco="enugu",
        amount=100,
        customerId="12345",
        meterType="PREPAID",
        payerName="Jane Doe",
    )
    assert result["status"] == "SUCCESS"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/bill/electricity"


def test_pay_electricity_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    electricity = Electricity(http)
    with pytest.raises(UnconfirmedOutcomeError):
        electricity.pay_electricity(
            "ref1",
            disco="enugu",
            amount=100,
            customerId="12345",
            meterType="PREPAID",
            payerName="Jane Doe",
        )


def test_pay_electricity_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    electricity = Electricity(http)
    result = electricity.pay_electricity(
        "ref1",
        disco="enugu",
        amount=100,
        customerId="12345",
        meterType="PREPAID",
        payerName="Jane Doe",
        on_pending=lambda d: "handled",
    )
    assert result == "handled"


def test_pay_electricity_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    electricity = Electricity(http)
    with pytest.raises(NombaError):
        electricity.pay_electricity(
            "ref1",
            disco="enugu",
            amount=100,
            customerId="12345",
            meterType="PREPAID",
            payerName="Jane Doe",
        )


def test_pay_electricity_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    electricity = Electricity(http)
    electricity.pay_electricity_from_sub_account(
        "sub1",
        "ref1",
        disco="enugu",
        amount=100,
        customerId="12345",
        meterType="PREPAID",
        payerName="Jane Doe",
    )
    req = captured["request"]
    assert req.url.path == "/v2/bill/electricity/sub1"
