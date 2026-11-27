from __future__ import annotations

import httpx

from nomba.v1.direct_debits import (
    CreatedMandate,
    DirectDebits,
    MandateDebitResult,
    MandatePage,
    MandateStatus,
    UpdatedMandateStatus,
)


def test_create_mandate_uses_non_default_code_description_fields(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "responseCode": "00",
                "responseMessage": "Success",
                "data": {
                    "mandateId": "m1",
                    "merchantReference": "ref1",
                    "phoneNumber": "08012345678",
                    "description": "Approve via USSD",
                },
            },
        )

    http = fake_http(handler)
    dd = DirectDebits(http)
    result = dd.create_mandate(
        merchantReference="ref1",
        customerAccountNumber="1234567890",
        bankCode="044",
        customerName="Jane Doe",
        customerAccountName="Jane Doe",
        amount=100,
        frequency="MONTHLY",
        startDate="2026-01-01",
        endDate="2027-01-01",
        customerEmail="jane@example.com",
    )
    assert result == CreatedMandate(
        mandateId="m1",
        merchantReference="ref1",
        phoneNumber="08012345678",
        description="Approve via USSD",
    )
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/direct-debits"


def test_create_mandate_errors_use_response_code_field(fake_http):
    # The envelope's own error indicator is responseCode/responseMessage, not code/description;
    # if the override weren't passed, a non-"00" responseCode would be ignored and this request
    # would wrongly look successful.
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "responseCode": "99",
                "responseMessage": "Invalid bank code",
                "data": {},
            },
        )
    )
    dd = DirectDebits(http)
    import pytest

    from nomba.lib.errors import NombaError

    with pytest.raises(NombaError) as exc_info:
        dd.create_mandate(
            merchantReference="ref1",
            customerAccountNumber="1234567890",
            bankCode="044",
            customerName="Jane Doe",
            customerAccountName="Jane Doe",
            amount=100,
            frequency="MONTHLY",
            startDate="2026-01-01",
            endDate="2027-01-01",
            customerEmail="jane@example.com",
        )
    assert exc_info.value.description == "Invalid bank code"


def test_get_mandate_status(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "customerAccountName": "Jane Doe",
                    "mandateId": "m1",
                    "customerAccountNumber": "1234567890",
                    "mandateStatus": "ACTIVE",
                },
            },
        )

    http = fake_http(handler)
    dd = DirectDebits(http)
    result = dd.get_mandate_status("m1")
    assert result == MandateStatus(
        customerAccountName="Jane Doe",
        mandateId="m1",
        customerAccountNumber="1234567890",
        mandateStatus="ACTIVE",
    )
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/direct-debits/status"
    assert req.url.params["mandateId"] == "m1"


def test_debit_mandate(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"mandateId": "m1", "status": "SUCCESS", "amount": "110.00"},
            },
        )

    http = fake_http(handler)
    dd = DirectDebits(http)
    result = dd.debit_mandate(mandateId="m1", amount="110.00")
    assert result == MandateDebitResult(
        mandateId="m1", status="SUCCESS", amount="110.00"
    )
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/direct-debits/debit-mandate"


def test_list_mandates(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"items": [], "page": 1, "pageSize": 10, "totalItems": 0},
            },
        )

    http = fake_http(handler)
    dd = DirectDebits(http)
    result = dd.list_mandates(page=1, pageSize=10)
    assert result == MandatePage(items=[], page=1, pageSize=10, totalItems=0)
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/direct-debits/mandates"


def test_update_mandate_status(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"mandateId": "m1", "mandateStatus": "SUSPENDED"},
            },
        )

    http = fake_http(handler)
    dd = DirectDebits(http)
    result = dd.update_mandate_status(mandateId="m1", status="SUSPEND")
    assert result == UpdatedMandateStatus(mandateId="m1", mandateStatus="SUSPENDED")
    req = captured["request"]
    assert req.method == "PUT"
    assert req.url.path == "/v1/direct-debits/update-status"
