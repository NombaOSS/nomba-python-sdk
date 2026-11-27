from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _path_id
from nomba.v2.betting.types import BettingPaymentParams

__all__ = ["BETTING_OUTCOMES", "Betting"]

# Ported from Node's src/services/v2/betting/betting.service.ts (method list). Both
# payBetting and payBettingFromSubAccount route through settle()/OutcomeTable in Node (v2
# has purchase endpoints only, no lookup) -- this whole file is money-moving.
BETTING_OUTCOMES = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


class Betting:
    """Betting wallet funding (v2)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def pay_betting(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[BettingPaymentParams],
    ) -> Any:
        """`POST /v2/bill/betting`. Funds a betting wallet from the parent account.
        `merchant_tx_ref` is the idempotency key: unique per payment.

        Without closures: success returns the payment data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/bill/betting",
            BETTING_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def pay_betting_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[BettingPaymentParams],
    ) -> Any:
        """`POST /v2/bill/betting/{subAccountId}`. Pays from a sub account. `merchant_tx_ref`
        is the idempotency key.

        Without closures: success returns the payment data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/bill/betting/{_path_id(sub_account_id)}",
            BETTING_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
