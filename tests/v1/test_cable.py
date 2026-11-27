from __future__ import annotations

import httpx

from nomba.v1.cable import BillCable, CablePlan


def test_get_cable_plans(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {"subScriptionType": "Compact", "amount": 6000},
                    {"subScriptionType": "Premium", "amount": 24000},
                ],
            },
        )

    http = fake_http(handler)
    bills = BillCable(http)
    result = bills.get_cable_plans(cableTvType="DSTV")
    assert result == [
        CablePlan(subScriptionType="Compact", amount=6000),
        CablePlan(subScriptionType="Premium", amount=24000),
    ]
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/bill/cableTvProduct"
    assert req.url.params["cableTvType"] == "DSTV"


def test_lookup_customer(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": "Jane Doe"})

    http = fake_http(handler)
    bills = BillCable(http)
    result = bills.lookup_customer(cableTvType="DSTV", customerId="12345")
    assert result == "Jane Doe"
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/bill/cable/lookup"
    assert req.url.params["customerId"] == "12345"
