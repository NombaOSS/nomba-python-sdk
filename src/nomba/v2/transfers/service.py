from __future__ import annotations

from collections.abc import Callable
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.outcome import REJECTED, OutcomeTable, settle
from nomba.lib.util import _build, _path_id
from nomba.v2.transfers.types import (
    Bank,
    BankAccountLookupParams,
    BankAccountLookupResult,
    BankTransferParams,
    WalletTransferParams,
)

__all__ = ["TRANSFER_OUTCOMES", "Transfers"]

# Ported from Node's src/services/v2/transfers/transfers.service.ts (method list).
# listBanks and lookupBankAccount stay plain there -- only the four transfer methods
# (bankTransfer, bankTransferFromSubAccount, walletTransfer, walletTransferFromSubAccount)
# route through settle()/OutcomeTable in Node.

# Documented for every transfer endpoint: code "00"/"200" done, "201" accepted and still
# processing; data.status SUCCESS or PENDING_BILLING. The docs say to treat any other status
# as pending, so it is never success or failed -- that includes REFUND and the other requery
# statuses this endpoint does not document.
TRANSFER_OUTCOMES = OutcomeTable(
    codes={"00": "success", "200": "success", "201": "pending", **REJECTED},
    statuses={"SUCCESS": "success", "PENDING_BILLING": "pending"},
)


class Transfers:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_banks(self) -> list[Bank]:
        """`GET /v1/transfers/banks`. Lists the banks usable as a transfer destination."""
        data = self._http.request("GET", "/v1/transfers/banks")
        return [_build(Bank, b) for b in data]

    def lookup_bank_account(
        self, **params: Unpack[BankAccountLookupParams]
    ) -> BankAccountLookupResult:
        """`POST /v1/transfers/bank/lookup`. Resolves a bank account number to its account
        name."""
        return _build(
            BankAccountLookupResult,
            self._http.request("POST", "/v1/transfers/bank/lookup", body=params),
        )

    def bank_transfer(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[BankTransferParams],
    ) -> Any:
        """`POST /v2/transfers/bank`. Sends a bank transfer from the parent account.
        `merchant_tx_ref` is the idempotency key: unique per transfer, and reused (never
        regenerated) when retrying a pending one.

        Without closures: success returns the transfer data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/transfers/bank",
            TRANSFER_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def bank_transfer_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[BankTransferParams],
    ) -> Any:
        """`POST /v2/transfers/bank/{subAccountId}`. Sends a bank transfer from a sub account.
        You must ask Nomba to profile you for sub account transfers. `merchant_tx_ref` is the
        idempotency key.

        Without closures: success returns the transfer data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/transfers/bank/{_path_id(sub_account_id)}",
            TRANSFER_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def wallet_transfer(
        self,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[WalletTransferParams],
    ) -> Any:
        """`POST /v2/transfers/wallet`. Sends a wallet-to-wallet transfer from the parent
        account to another Nomba account. `merchant_tx_ref` is the idempotency key.

        Without closures: success returns the transfer data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            "/v2/transfers/wallet",
            TRANSFER_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )

    def wallet_transfer_from_sub_account(
        self,
        sub_account_id: str,
        merchant_tx_ref: str,
        *,
        on_success: Callable[[Any], Any] | None = None,
        on_pending: Callable[[Any], Any] | None = None,
        on_failed: Callable[[Any], Any] | None = None,
        **params: Unpack[WalletTransferParams],
    ) -> Any:
        """`POST /v2/transfers/wallet/{subAccountId}`. Sends a wallet-to-wallet transfer from a
        sub account. `merchant_tx_ref` is the idempotency key.

        Without closures: success returns the transfer data; pending/undocumented raises
        `UnconfirmedOutcomeError`; failed raises `NombaError`.
        """
        return settle(
            self._http,
            "POST",
            f"/v2/transfers/wallet/{_path_id(sub_account_id)}",
            TRANSFER_OUTCOMES,
            field="merchantTxRef",
            key=merchant_tx_ref,
            body={**params, "merchantTxRef": merchant_tx_ref},
            on_success=on_success,
            on_pending=on_pending,
            on_failed=on_failed,
        )
