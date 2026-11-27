from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from nomba.http import HttpClient
from nomba.lib.paginate import paginate
from nomba.lib.util import _build, _path_id, _query
from nomba.v1.transactions.types import (
    BankTransaction,
    FilterTransactionsParams,
    Transaction,
    VirtualAccountTransaction,
)

# Ported from Node's src/services/v1/transactions/transactions.service.ts (method list).


def _page(cls: type[Any], data: dict[str, Any]) -> tuple[list[Any], str | None]:
    results: list[Any] = [_build(cls, r) for r in data.get("results") or []]
    cursor = data.get("cursor") or None
    return results, cursor


class Transactions:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_bank_transactions(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[BankTransaction], str | None]:
        """`GET /v1/transactions/bank`. Lists credit/debit transactions on the parent account."""
        query = _query(
            {"cursor": cursor, "limit": limit, "dateFrom": date_from, "dateTo": date_to}
        )
        data = self._http.request("GET", f"/v1/transactions/bank{query}")
        return _page(BankTransaction, data)

    def iterate_bank_transactions(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Iterator[BankTransaction]:
        """Every credit/debit transaction on the parent account, across all pages."""
        return paginate(
            lambda c: self.list_bank_transactions(
                cursor=c or cursor, limit=limit, date_from=date_from, date_to=date_to
            )
        )

    def list_virtual_account_transactions(
        self,
        account_number: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[VirtualAccountTransaction], str | None]:
        """`GET /v1/transactions/virtual`. Lists transactions on a virtual account.

        The response carries a cursor, but the API docs do not name a paging
        parameter, so only the first page is returned.
        """
        query = _query(
            {
                "virtual_account": account_number,
                "dateFrom": date_from,
                "dateTo": date_to,
            }
        )
        data = self._http.request("GET", f"/v1/transactions/virtual{query}")
        return _page(VirtualAccountTransaction, data)

    def list_parent_transactions(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Transaction], str | None]:
        """`GET /v1/transactions/accounts`. Lists transactions on the parent account."""
        query = _query(
            {"cursor": cursor, "limit": limit, "dateFrom": date_from, "dateTo": date_to}
        )
        data = self._http.request("GET", f"/v1/transactions/accounts{query}")
        return _page(Transaction, data)

    def iterate_parent_transactions(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Iterator[Transaction]:
        """Every transaction on the parent account, across all pages."""
        return paginate(
            lambda c: self.list_parent_transactions(
                cursor=c or cursor, limit=limit, date_from=date_from, date_to=date_to
            )
        )

    def list_sub_account_transactions(
        self,
        sub_account_id: str,
        cursor: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[Transaction], str | None]:
        """`GET /v1/transactions/accounts/{subAccountId}`. Lists transactions on a sub account."""
        query = _query(
            {"cursor": cursor, "limit": limit, "dateFrom": date_from, "dateTo": date_to}
        )
        data = self._http.request(
            "GET", f"/v1/transactions/accounts/{_path_id(sub_account_id)}{query}"
        )
        return _page(Transaction, data)

    def iterate_sub_account_transactions(
        self,
        sub_account_id: str,
        cursor: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Iterator[Transaction]:
        """Every transaction on a sub account, across all pages."""
        return paginate(
            lambda c: self.list_sub_account_transactions(
                sub_account_id,
                cursor=c or cursor,
                limit=limit,
                date_from=date_from,
                date_to=date_to,
            )
        )

    def filter_parent_transactions(
        self,
        filter: FilterTransactionsParams | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> tuple[list[Transaction], str | None]:
        """`POST /v1/transactions/accounts`. Filters transactions on the parent account."""
        query = _query({"cursor": cursor, "limit": limit})
        data = self._http.request(
            "POST", f"/v1/transactions/accounts{query}", body=filter or {}
        )
        return _page(Transaction, data)

    def iterate_filtered_parent_transactions(
        self,
        filter: FilterTransactionsParams | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Iterator[Transaction]:
        """Every parent account transaction matching the filter, across all pages."""
        return paginate(
            lambda c: self.filter_parent_transactions(
                filter, cursor=c or cursor, limit=limit
            )
        )

    def filter_sub_account_transactions(
        self,
        sub_account_id: str,
        filter: FilterTransactionsParams | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> tuple[list[Transaction], str | None]:
        """`POST /v1/transactions/accounts/{subAccountId}`. Filters transactions on a sub account."""
        query = _query({"cursor": cursor, "limit": limit})
        data = self._http.request(
            "POST",
            f"/v1/transactions/accounts/{_path_id(sub_account_id)}{query}",
            body=filter or {},
        )
        return _page(Transaction, data)

    def iterate_filtered_sub_account_transactions(
        self,
        sub_account_id: str,
        filter: FilterTransactionsParams | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Iterator[Transaction]:
        """Every sub account transaction matching the filter, across all pages."""
        return paginate(
            lambda c: self.filter_sub_account_transactions(
                sub_account_id, filter, cursor=c or cursor, limit=limit
            )
        )
