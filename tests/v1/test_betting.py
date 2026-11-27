from __future__ import annotations

import httpx

from nomba.v1.betting import BettingProvider, BillBetting


def test_get_betting_providers(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {
                        "id": "1",
                        "name": "Bet9ja",
                        "biller_id": "b1",
                        "lookup_id": "l1",
                        "amount": "100",
                    },
                ],
            },
        )

    http = fake_http(handler)
    bills = BillBetting(http)
    result = bills.get_betting_providers()
    assert result == [
        BettingProvider(
            id="1", name="Bet9ja", biller_id="b1", lookup_id="l1", amount="100"
        )
    ]
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/bill/betting/providers"


def test_lookup_customer(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": "John Smith"})

    http = fake_http(handler)
    bills = BillBetting(http)
    result = bills.lookup_customer(bettingProvider="bet9ja", customerId="99999")
    assert result == "John Smith"
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/bill/betting/lookup"
    assert req.url.params["customerId"] == "99999"
