from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import IdempotencyKeyAbsentError
from nomba.v1.globals.collections import (
    Collections,
    CollectionTransaction,
    InflowProvider,
    InflowResult,
)


def test_inflow_providers(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {"code": "MPESA", "displayName": "M-Pesa"},
                    {"code": "AIRTEL", "displayName": "Airtel Money"},
                ],
            },
        )

    http = fake_http(handler)
    collections = Collections(http)
    result = collections.inflow_providers()
    assert result == [
        InflowProvider(code="MPESA", displayName="M-Pesa"),
        InflowProvider(code="AIRTEL", displayName="Airtel Money"),
    ]
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/global-collection/drc/inflow/providers"


def test_initiate_inflow(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "transactionReference": "txn-1",
                    "status": "PENDING",
                    "idempotencyKey": "idem-1",
                },
            },
        )

    http = fake_http(handler)
    collections = Collections(http)
    result = collections.initiate_inflow(
        phoneNumber="0800000000",
        callbackUrl="https://example.com/cb",
        amount=100,
        currency="CDF",
        topupVendor="MPESA",
        idempotencyKey="idem-1",
    )
    assert result == InflowResult(
        transactionReference="txn-1", status="PENDING", idempotencyKey="idem-1"
    )
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/global-collection/inflow/initiate"


def test_initiate_inflow_requires_idempotency_key(fake_http):
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": {}}))
    collections = Collections(http)
    with pytest.raises(IdempotencyKeyAbsentError):
        # Deliberately omits idempotencyKey to test the runtime guard for it.
        collections.initiate_inflow(  # type: ignore[call-arg]
            phoneNumber="0800000000",
            callbackUrl="https://example.com/cb",
            amount=100,
            currency="CDF",
            topupVendor="MPESA",
        )


def test_initiate_inflow_rejects_blank_idempotency_key(fake_http):
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": {}}))
    collections = Collections(http)
    with pytest.raises(IdempotencyKeyAbsentError):
        # Deliberately omits the other required fields to test the blank-key guard alone.
        collections.initiate_inflow(idempotencyKey="   ")  # type: ignore[call-arg]


def test_get_transaction(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "transactionId": "txn-1",
                    "status": "SUCCESS",
                    "amount": 100,
                    "currency": "CDF",
                },
            },
        )

    http = fake_http(handler)
    collections = Collections(http)
    result = collections.get_transaction("txn-1")
    assert result == CollectionTransaction(
        transactionId="txn-1", status="SUCCESS", amount=100, currency="CDF"
    )
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/global-collection/transactions/txn-1"
