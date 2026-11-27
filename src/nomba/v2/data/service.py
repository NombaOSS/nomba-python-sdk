from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _path_id
from nomba.v2.data.types import DataPurchaseParams

__all__ = ["DATA_OUTCOMES", "Data"]

# Ported from Node's src/services/v2/data/data.service.ts (method list). Both buyData and
# buyDataFromSubAccount route through settle()/OutcomeTable in Node -- this whole file is
# money-moving.
DATA_OUTCOMES = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


class Data:
    """Data bundle purchases (v2)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def buy_data(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[DataPurchaseParams],
    ) -> Any:
        """`POST /v2/bill/data`. Buys a data bundle from the parent account. `merchant_tx_ref`
        is the idempotency key: unique per purchase.

        Without closures: success returns the purchase data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/bill/data",
            DATA_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def buy_data_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[DataPurchaseParams],
    ) -> Any:
        """`POST /v2/bill/data/{subAccountId}`. Buys a data bundle from a sub account.
        `merchant_tx_ref` is the idempotency key.

        Without closures: success returns the purchase data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/bill/data/{_path_id(sub_account_id)}",
            DATA_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
