from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _path_id
from nomba.v2.cable.types import CableTvSubscriptionParams

__all__ = ["CABLE_OUTCOMES", "Cable"]

# Ported from Node's src/services/v2/cable/cable.service.ts (method list). Both
# subscribeCableTv and subscribeCableTvFromSubAccount route through settle()/OutcomeTable
# in Node (v2 has purchase endpoints only, no lookup) -- this whole file is money-moving.
CABLE_OUTCOMES = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


class Cable:
    """Cable TV subscription payments (v2)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def subscribe_cable_tv(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[CableTvSubscriptionParams],
    ) -> Any:
        """`POST /v2/bill/cabletv`. Pays a cable TV subscription from the parent account.
        `merchant_tx_ref` is the idempotency key: unique per payment.

        Without closures: success returns the payment data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/bill/cabletv",
            CABLE_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def subscribe_cable_tv_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[CableTvSubscriptionParams],
    ) -> Any:
        """`POST /v2/bill/cabletv/{subAccountId}`. Pays from a sub account. `merchant_tx_ref`
        is the idempotency key.

        Without closures: success returns the payment data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/bill/cabletv/{_path_id(sub_account_id)}",
            CABLE_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
