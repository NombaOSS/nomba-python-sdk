from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import NombaError, UnconfirmedOutcomeError
from nomba.v2.transfers import Bank, BankAccountLookupResult, Transfers


def test_list_banks(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {"code": "044", "name": "Access Bank", "nipCode": "044", "logo": ""}
                ],
            },
        )
    )
    transfers = Transfers(http)
    result = transfers.list_banks()
    assert result == [Bank(code="044", name="Access Bank", nipCode="044", logo="")]


def test_lookup_bank_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"accountNumber": "1234567890", "accountName": "Jane Doe"},
            },
        )

    http = fake_http(handler)
    transfers = Transfers(http)
    result = transfers.lookup_bank_account(accountNumber="1234567890", bankCode="044")
    assert isinstance(result, BankAccountLookupResult)
    assert result.accountName == "Jane Doe"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/transfers/bank/lookup"


def test_bank_transfer_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"status": "SUCCESS", "id": "t1"}}
        )

    http = fake_http(handler)
    transfers = Transfers(http)
    result = transfers.bank_transfer(
        "ref1",
        amount=100,
        accountNumber="1234567890",
        accountName="Jane Doe",
        bankCode="044",
    )
    assert result["status"] == "SUCCESS"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/transfers/bank"


def test_bank_transfer_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    transfers = Transfers(http)
    with pytest.raises(UnconfirmedOutcomeError):
        transfers.bank_transfer(
            "ref1",
            amount=100,
            accountNumber="0123456789",
            bankCode="044",
            accountName="Jane",
        )


def test_bank_transfer_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    transfers = Transfers(http)
    result = transfers.bank_transfer(
        "ref1",
        amount=100,
        accountNumber="0123456789",
        bankCode="044",
        accountName="Jane",
        on_pending=lambda data: "handled",
    )
    assert result == "handled"


def test_bank_transfer_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    transfers = Transfers(http)
    with pytest.raises(NombaError):
        transfers.bank_transfer(
            "ref1",
            amount=100,
            accountNumber="0123456789",
            bankCode="044",
            accountName="Jane",
        )


def test_bank_transfer_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    transfers = Transfers(http)
    transfers.bank_transfer_from_sub_account(
        "sub1",
        "ref1",
        amount=100,
        accountNumber="0123456789",
        bankCode="044",
        accountName="Jane",
    )
    req = captured["request"]
    assert req.url.path == "/v2/transfers/bank/sub1"


def test_wallet_transfer_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    transfers = Transfers(http)
    transfers.wallet_transfer(
        "ref1", amount=100, receiverAccountId="acc1", senderName="Jane"
    )
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v2/transfers/wallet"


def test_wallet_transfer_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200, json={"code": "00", "data": {"status": "PENDING_BILLING"}}
        )
    )
    transfers = Transfers(http)
    with pytest.raises(UnconfirmedOutcomeError):
        transfers.wallet_transfer(
            "ref1", amount=100, receiverAccountId="acc1", senderName="Jane"
        )


def test_wallet_transfer_rejected_code_raises_nomba_error(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "bad request"}
        )
    )
    transfers = Transfers(http)
    with pytest.raises(NombaError):
        transfers.wallet_transfer(
            "ref1", amount=100, receiverAccountId="acc1", senderName="Jane"
        )


def test_wallet_transfer_from_sub_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(200, json={"code": "00", "data": {"status": "SUCCESS"}})

    http = fake_http(handler)
    transfers = Transfers(http)
    transfers.wallet_transfer_from_sub_account(
        "sub1", "ref1", amount=100, receiverAccountId="acc1", senderName="Jane"
    )
    req = captured["request"]
    assert req.url.path == "/v2/transfers/wallet/sub1"
