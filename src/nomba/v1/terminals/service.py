from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _build, _path_id
from nomba.v1.terminals.types import AssignTerminalParams, Terminal

__all__ = ["PAYMENT_REQUEST_OUTCOMES", "Terminals"]

# Ported from Node's src/services/v1/terminals/terminals.service.ts (method list).
# Documented: code "00"; data.status pending, completed or failed. As with Node's service,
# the docs never say "failed" is final, so only "completed" is success.
PAYMENT_REQUEST_OUTCOMES = OutcomeTable(
    codes={"00": "success", **REJECTED},
    statuses={"completed": "success", "pending": "pending", "failed": "pending"},
)


class Terminals:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def assign_to_parent(self, **params: Unpack[AssignTerminalParams]) -> Terminal:
        """`POST /v1/terminals/assign`. Assigns a terminal to the parent account."""
        return _build(
            Terminal, self._http.request("POST", "/v1/terminals/assign", body=params)
        )

    def assign_to_sub_account(
        self, sub_account_id: str, **params: Unpack[AssignTerminalParams]
    ) -> Terminal:
        """`POST /v1/terminals/assign/{subAccountId}`. Assigns a terminal to a sub account."""
        return _build(
            Terminal,
            self._http.request(
                "POST", f"/v1/terminals/assign/{_path_id(sub_account_id)}", body=params
            ),
        )

    def unassign_from_parent(self, **params: Unpack[AssignTerminalParams]) -> Terminal:
        """`POST /v1/terminals/unassign`. Unassigns a terminal from the parent account."""
        return _build(
            Terminal, self._http.request("POST", "/v1/terminals/unassign", body=params)
        )

    def unassign_from_sub_account(
        self, sub_account_id: str, **params: Unpack[AssignTerminalParams]
    ) -> Terminal:
        """`POST /v1/terminals/unassign/{subAccountId}`. Unassigns a terminal from a sub
        account."""
        return _build(
            Terminal,
            self._http.request(
                "POST",
                f"/v1/terminals/unassign/{_path_id(sub_account_id)}",
                body=params,
            ),
        )

    def push_payment_request(
        self,
        terminal_id: str,
        merchant_tx_ref: str,
        amount: float,
        currency: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
    ) -> Any:
        """`POST /v1/terminals/payment-request/{terminalId}`. Triggers a payment prompt on the
        physical terminal; the customer taps or swipes their card, and the outcome is reported
        via webhook or requery.

        `merchant_tx_ref` is used as the idempotency key. Without closures: success returns the
        payment data; pending/undocumented raises `UnconfirmedOutcomeError`; failed raises
        `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v1/terminals/payment-request/{_path_id(terminal_id)}",
            PAYMENT_REQUEST_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={
                "merchantTxRef": merchant_tx_ref,
                "amount": amount,
                "currency": currency,
            },
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
