from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _build, _path_id, _query
from nomba.v1.globals.payouts.types import (
    AuthorizeExchangeParams,
    AuthorizeTransferParams,
    Conversion,
    ConvertMoneyParams,
    ExchangeRate,
    ExchangeRatesParams,
    InstitutionProvider,
    InstitutionProvidersParams,
    PaymentMethodInfo,
    PaymentMethodsParams,
    PayoutAccount,
    PayoutTransaction,
)

__all__ = ["EXCHANGE_OUTCOMES", "TRANSFER_OUTCOMES", "Payouts"]

# Ported from Node's src/services/v1/globals/payout.service.ts (Global Payout: cross-border
# transfers and currency exchange -- the payouts side of Node's "globals" domain;
# nomba.v1.globals.collections is the collections side, ported separately in Task 15).
#
# Node's #authorize helper raises IdempotencyKeyAbsentError manually before calling settle(),
# but settle() (here and in Node's outcome.ts) already raises the same error when the key is
# missing/blank -- the manual check is redundant. Per the terminals/checkout/transfers
# precedent, no separate manual check is added here; settle()'s own check is relied on alone.

# authorize-transfer documents data.status PROCESSING, PENDING, COMPLETED and FAILED. The docs
# never say FAILED is final or safe to refund, so it stays pending until confirmed; only
# COMPLETED is success.
TRANSFER_OUTCOMES = OutcomeTable(
    codes={"00": "success", **REJECTED},
    statuses={
        "COMPLETED": "success",
        "PROCESSING": "pending",
        "PENDING": "pending",
        "FAILED": "pending",
    },
)

# authorize-exchange documents no status values, so it is classified by code alone.
EXCHANGE_OUTCOMES = OutcomeTable(codes={"00": "success", **REJECTED})


class Payouts:
    """Global Payout (v1): cross-border transfers, currency exchange, and multi-currency
    wallets."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_accounts(self) -> list[PayoutAccount]:
        """`GET /v1/global-payout/accounts`. Every currency wallet, with its balance."""
        data = self._http.request("GET", "/v1/global-payout/accounts")
        return [_build(PayoutAccount, a) for a in data]

    def get_account(self, account_id: str) -> PayoutAccount:
        """`GET /v1/global-payout/accounts/{accountId}`. The wallet's details and balance."""
        return _build(
            PayoutAccount,
            self._http.request(
                "GET", f"/v1/global-payout/accounts/{_path_id(account_id)}"
            ),
        )

    def list_sandbox_accounts(self) -> list[PayoutAccount]:
        """`GET /v1/sandbox/global-payout/accounts`. Canned test wallet data."""
        data = self._http.request("GET", "/v1/sandbox/global-payout/accounts")
        return [_build(PayoutAccount, a) for a in data]

    def get_sandbox_account(self, account_id: str) -> PayoutAccount:
        """`GET /v1/sandbox/global-payout/accounts/{accountId}`. Canned test data; any id is
        echoed back."""
        return _build(
            PayoutAccount,
            self._http.request(
                "GET", f"/v1/sandbox/global-payout/accounts/{_path_id(account_id)}"
            ),
        )

    def exchange_rates(
        self, **params: Unpack[ExchangeRatesParams]
    ) -> list[ExchangeRate]:
        """`GET /v1/global-payout/exchange-rates`. `params["from"]`/`params["to"]` give the
        currency pair to get a rate for."""
        data = self._http.request(
            "GET", f"/v1/global-payout/exchange-rates{_query(params)}"
        )
        return [_build(ExchangeRate, r) for r in data["rates"]]

    def convert(self, **params: Unpack[ConvertMoneyParams]) -> Conversion:
        """`POST /v1/global-payout/money/convert`. A calculation only; no money moves."""
        return _build(
            Conversion,
            self._http.request(
                "POST",
                "/v1/global-payout/money/convert",
                body=params,
            ),
        )

    def institution_providers(
        self, **params: Unpack[InstitutionProvidersParams]
    ) -> list[InstitutionProvider]:
        """`GET /v1/global-payout/bank/providers`. The receiving institutions available for
        payout, optionally filtered e.g. by country or currency."""
        data = self._http.request(
            "GET", f"/v1/global-payout/bank/providers{_query(params)}"
        )
        return [_build(InstitutionProvider, p) for p in data]

    def payment_methods(
        self, **params: Unpack[PaymentMethodsParams]
    ) -> list[PaymentMethodInfo]:
        """`GET /v1/global-payout/payment-methods`. The payment methods available for payout,
        optionally filtered e.g. by country or currency."""
        data = self._http.request(
            "GET", f"/v1/global-payout/payment-methods{_query(params)}"
        )
        return [_build(PaymentMethodInfo, m) for m in data]

    def authorize_transfer(
        self,
        idempotency_key: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[AuthorizeTransferParams],
    ) -> Any:
        """`POST /v1/global-payout/transfer/authorize`. Sends money cross-border.
        `idempotency_key` is sent as `idempotencyKey` -- the SDK never generates one for you,
        to prevent double disbursement.

        Without closures: success returns the payout data; pending/undocumented (including
        FAILED, which the docs never confirm is final) raises `UnconfirmedOutcomeError`; failed
        raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v1/global-payout/transfer/authorize",
            TRANSFER_OUTCOMES,
            field="idempotencyKey",
            key=idempotency_key,
            body={**params, "idempotencyKey": idempotency_key},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def authorize_exchange(
        self,
        idempotency_key: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[AuthorizeExchangeParams],
    ) -> Any:
        """`POST /v1/global-payout/exchange/authorize`. Moves money between your own wallets in
        different currencies. `idempotency_key` is sent as `idempotencyKey` -- the SDK never
        generates one for you, to prevent double disbursement.

        Without closures: success returns the payout data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v1/global-payout/exchange/authorize",
            EXCHANGE_OUTCOMES,
            field="idempotencyKey",
            key=idempotency_key,
            body={**params, "idempotencyKey": idempotency_key},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def get_transaction(self, transaction_id: str) -> PayoutTransaction:
        """`GET /v1/global-payout/transactions/{transactionId}`, with a `wtTransactionId`."""
        return _build(
            PayoutTransaction,
            self._http.request(
                "GET", f"/v1/global-payout/transactions/{_path_id(transaction_id)}"
            ),
        )
