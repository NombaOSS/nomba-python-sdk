from __future__ import annotations

import httpx

from nomba.v1.electricity import BillElectricity, ElectricityProvider


def test_get_electricity_providers(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {"id": "disco-1", "name": "Ikeja Electric"},
                    {"id": "disco-2", "name": "Eko Electric"},
                ],
            },
        )

    http = fake_http(handler)
    bills = BillElectricity(http)
    result = bills.get_electricity_providers()
    assert result == [
        ElectricityProvider(id="disco-1", name="Ikeja Electric"),
        ElectricityProvider(id="disco-2", name="Eko Electric"),
    ]
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/bill/electricity/discos"
