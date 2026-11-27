from __future__ import annotations

import httpx

from nomba.v1.data import BillData, DataPlan


def test_get_data_plans(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {"productId": "p1", "plan": "1GB", "amount": 500},
                    {"productId": "p2", "plan": "2GB", "amount": 900},
                ],
            },
        )

    http = fake_http(handler)
    bills = BillData(http)
    result = bills.get_data_plans("mtn")
    assert result == [
        DataPlan(productId="p1", plan="1GB", amount=500),
        DataPlan(productId="p2", plan="2GB", amount=900),
    ]
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/bill/data-plan/mtn"
