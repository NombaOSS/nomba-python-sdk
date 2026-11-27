from __future__ import annotations

import httpx
import pytest

from nomba.lib.errors import (
    IdempotencyKeyAbsentError,
    NombaError,
    UnconfirmedOutcomeError,
)
from nomba.v1.globals.payouts import (
    Conversion,
    ExchangeRate,
    InstitutionProvider,
    PaymentMethodInfo,
    PayoutAccount,
    Payouts,
    PayoutTransaction,
)
from nomba.v1.globals.payouts.types import (
    AuthorizeExchangeParams,
    AuthorizeTransferParams,
)

# The full set of AuthorizeTransferParams/AuthorizeExchangeParams required fields, for tests
# that only care about outcome classification, not the business fields' actual values.
_TRANSFER_KWARGS: AuthorizeTransferParams = {
    "amount": 100,
    "sourceCurrency": "USD",
    "destinationCurrency": "NGN",
    "receiverName": "Jane Doe",
    "sourceCountryIsoCode": "US",
    "destinationCountryIsoCode": "NG",
    "paymentMethod": "BANK",
    "accountType": "INDIVIDUAL",
}
_EXCHANGE_KWARGS: AuthorizeExchangeParams = {
    "amount": 100,
    "sourceCurrency": "USD",
    "destinationCurrency": "NGN",
    "senderName": "John Doe",
    "receiverName": "Jane Doe",
    "sourceCountryIsoCode": "US",
    "destinationCountryIsoCode": "NG",
}


def test_list_accounts(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": [
                    {
                        "accountId": "acc1",
                        "name": "USD wallet",
                        "currency": "USD",
                        "balance": 100.0,
                        "availableBalance": 100.0,
                        "status": "ACTIVE",
                    }
                ],
            },
        )
    )
    payouts = Payouts(http)
    result = payouts.list_accounts()
    assert result == [
        PayoutAccount(
            accountId="acc1",
            name="USD wallet",
            currency="USD",
            balance=100.0,
            availableBalance=100.0,
            status="ACTIVE",
        )
    ]


def test_get_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"accountId": "acc1", "status": "ACTIVE"}}
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.get_account("acc1")
    assert isinstance(result, PayoutAccount)
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/global-payout/accounts/acc1"


def test_list_sandbox_accounts(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={"code": "00", "data": [{"accountId": "sand1", "status": "ACTIVE"}]},
        )
    )
    payouts = Payouts(http)
    result = payouts.list_sandbox_accounts()
    assert result == [PayoutAccount(accountId="sand1", status="ACTIVE")]


def test_get_sandbox_account(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200, json={"code": "00", "data": {"accountId": "anything"}}
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.get_sandbox_account("anything")
    assert result.accountId == "anything"
    req = captured["request"]
    assert req.url.path == "/v1/sandbox/global-payout/accounts/anything"


def test_exchange_rates(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "rates": [{"exchangeRateId": "r1", "currencyPairName": "USD/NGN"}]
                },
            },
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.exchange_rates(**{"from": "USD", "to": "NGN"})
    assert result == [ExchangeRate(exchangeRateId="r1", currencyPairName="USD/NGN")]
    req = captured["request"]
    assert req.method == "GET"
    assert req.url.path == "/v1/global-payout/exchange-rates"
    assert "from=USD" in str(req.url)


def test_convert(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "fromAmount": 100,
                    "fromCurrency": "USD",
                    "toAmount": 150000,
                    "toCurrency": "NGN",
                    "exchangeRateId": "r1",
                },
            },
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.convert(
        amount=100,
        currency="USD",
        destinationCurrency="NGN",
        transactionType="EXCHANGE",
    )
    assert isinstance(result, Conversion)
    assert result.toCurrency == "NGN"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/global-payout/money/convert"


def test_institution_providers(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": [{"code": "044", "displayName": "Access Bank"}],
            },
        )
    )
    payouts = Payouts(http)
    result = payouts.institution_providers(isMobileMoney=False)
    assert result == [InstitutionProvider(code="044", displayName="Access Bank")]


def test_payment_methods(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": [{"code": "BANK", "displayName": "Bank Transfer"}],
            },
        )
    )
    payouts = Payouts(http)
    result = payouts.payment_methods()
    assert result == [PaymentMethodInfo(code="BANK", displayName="Bank Transfer")]


def test_get_transaction(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"transactionId": "tx1", "status": "COMPLETED"},
            },
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.get_transaction("tx1")
    assert result == PayoutTransaction(transactionId="tx1", status="COMPLETED")
    req = captured["request"]
    assert req.url.path == "/v1/global-payout/transactions/tx1"


# -- authorize_transfer --


def test_authorize_transfer_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"wtTransactionId": "wt1", "status": "COMPLETED"},
            },
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.authorize_transfer("idem1", **_TRANSFER_KWARGS)
    assert result["status"] == "COMPLETED"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/global-payout/transfer/authorize"


def test_authorize_transfer_pending_raises_without_handler(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"wtTransactionId": "wt1", "status": "PROCESSING"},
            },
        )
    )
    payouts = Payouts(http)
    with pytest.raises(UnconfirmedOutcomeError):
        payouts.authorize_transfer("idem1", **_TRANSFER_KWARGS)


def test_authorize_transfer_pending_calls_on_pending(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"wtTransactionId": "wt1", "status": "PENDING"},
            },
        )
    )
    payouts = Payouts(http)
    result = payouts.authorize_transfer(
        "idem1", on_pending=lambda data: "handled", **_TRANSFER_KWARGS
    )
    assert result == "handled"


def test_authorize_transfer_failed_status_maps_to_pending_not_failed(fake_http):
    # FAILED is deliberately classified as pending, not failed, per Node's comment that docs
    # never confirm FAILED is final -- this is the one subtle classification rule here.
    http = fake_http(
        lambda req: httpx.Response(
            200,
            json={"code": "00", "data": {"wtTransactionId": "wt1", "status": "FAILED"}},
        )
    )
    payouts = Payouts(http)
    with pytest.raises(UnconfirmedOutcomeError):
        payouts.authorize_transfer("idem1", **_TRANSFER_KWARGS)
    result = payouts.authorize_transfer(
        "idem1", on_pending=lambda data: "handled", **_TRANSFER_KWARGS
    )
    assert result == "handled"


def test_authorize_transfer_rejected_code(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "Bad request"}
        )
    )
    payouts = Payouts(http)
    with pytest.raises(NombaError):
        payouts.authorize_transfer("idem1", **_TRANSFER_KWARGS)


# -- authorize_exchange --


def test_authorize_exchange_success(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {"wtTransactionId": "wt2", "status": "ANYTHING"},
            },
        )

    http = fake_http(handler)
    payouts = Payouts(http)
    result = payouts.authorize_exchange("idem2", **_EXCHANGE_KWARGS)
    assert result["wtTransactionId"] == "wt2"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/global-payout/exchange/authorize"


def test_authorize_exchange_rejected_code(fake_http):
    http = fake_http(
        lambda req: httpx.Response(
            400, json={"code": "400", "description": "Bad request"}
        )
    )
    payouts = Payouts(http)
    with pytest.raises(NombaError):
        payouts.authorize_exchange("idem2", **_EXCHANGE_KWARGS)


def test_authorize_exchange_requires_idempotency_key(fake_http):
    http = fake_http(lambda req: httpx.Response(200, json={"code": "00", "data": {}}))
    payouts = Payouts(http)
    with pytest.raises(IdempotencyKeyAbsentError):
        payouts.authorize_exchange("", **_EXCHANGE_KWARGS)
