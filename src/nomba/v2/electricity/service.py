from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _build, _path_id, _query
from nomba.v2.electricity.types import (
    ElectricityPaymentParams,
    MeterLookupResult,
    MeterLookupV2Params,
)

__all__ = ["ELECTRICITY_OUTCOMES", "Electricity"]

# Ported from Node's src/services/v2/electricity/electricity.service.ts (method list).
# payElectricity and payElectricityFromSubAccount route through settle()/OutcomeTable in
# Node; lookupMeter stays a plain GET -- it never calls settle(), so it is not
# money-moving (verified, not assumed).
ELECTRICITY_OUTCOMES = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


class Electricity:
    """Electricity meter lookup and bill payments (v2)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def lookup_meter(self, **params: Unpack[MeterLookupV2Params]) -> MeterLookupResult:
        """`GET /v2/bill/electricity/lookup`. Resolves a disco + meter/customer id to the
        customer's name and address. Not money-moving."""
        return _build(
            MeterLookupResult,
            self._http.request("GET", f"/v2/bill/electricity/lookup{_query(params)}"),
        )

    def pay_electricity(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[ElectricityPaymentParams],
    ) -> Any:
        """`POST /v2/bill/electricity`. Pays an electricity bill from the parent account.
        Prepaid meters get the token in `meta.phcnToken`. `merchant_tx_ref` is the idempotency
        key: unique per payment.

        Without closures: success returns the payment data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/bill/electricity",
            ELECTRICITY_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def pay_electricity_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[ElectricityPaymentParams],
    ) -> Any:
        """`POST /v2/bill/electricity/{subAccountId}`. Pays from a sub account.
        `merchant_tx_ref` is the idempotency key.

        Without closures: success returns the payment data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/bill/electricity/{_path_id(sub_account_id)}",
            ELECTRICITY_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
