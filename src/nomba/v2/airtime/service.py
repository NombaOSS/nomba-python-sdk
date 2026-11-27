from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _path_id
from nomba.v2.airtime.types import AirtimePurchaseParams

__all__ = ["AIRTIME_OUTCOMES", "Airtime"]

# Ported from Node's src/services/v2/airtime/airtime.service.ts (method list). Both
# buyAirtime and buyAirtimeFromSubAccount route through settle()/OutcomeTable in Node --
# this whole file is money-moving.

# Code "00"/"200" done, "201" accepted and still processing; any other status is pending.
AIRTIME_OUTCOMES = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


class Airtime:
    """Airtime top-ups (v2)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def buy_airtime(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[AirtimePurchaseParams],
    ) -> Any:
        """`POST /v2/bill/topup`. Buys airtime from the parent account. `merchant_tx_ref` is
        the idempotency key: unique per purchase.

        Without closures: success returns the purchase data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/bill/topup",
            AIRTIME_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def buy_airtime_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[AirtimePurchaseParams],
    ) -> Any:
        """`POST /v2/bill/topup/{subAccountId}`. Buys airtime from a sub account.
        `merchant_tx_ref` is the idempotency key.

        Without closures: success returns the purchase data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/bill/topup/{_path_id(sub_account_id)}",
            AIRTIME_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
