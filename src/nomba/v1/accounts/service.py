from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.paginate import paginate
from nomba.lib.util import _build, _path_id, _query
from nomba.v1.accounts.types import AccountBalance, AccountDetails, TerminalListFilters
from nomba.v1.terminals import Terminal

# Ported from Node's src/services/v1/accounts/accounts.service.ts.
# `Terminal` lives in nomba.v1.terminals (its canonical home, mirroring Node's
# cross-import of Terminal from terminals types into the accounts service) and is
# re-imported here for the parent/sub-account-scoped listing methods below.


def _terminal_page(data: dict[str, Any]) -> tuple[list[Terminal], str | None]:
    results = [_build(Terminal, t) for t in data.get("results") or []]
    cursor = data.get("cursor") or None
    return results, cursor


class Accounts:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_parent_account(self) -> AccountDetails:
        """`GET /v1/accounts/parent`."""
        return _build(AccountDetails, self._http.request("GET", "/v1/accounts/parent"))

    def get_parent_balance(self) -> AccountBalance:
        """`GET /v1/accounts/balance`."""
        return _build(AccountBalance, self._http.request("GET", "/v1/accounts/balance"))

    def get_sub_account(
        self, account_id: str | None = None, account_ref: str | None = None
    ) -> AccountDetails:
        """`GET /v1/accounts/sub-account-details`, looked up by account id or account ref."""
        query = _query({"accountId": account_id, "accountRef": account_ref})
        return _build(
            AccountDetails,
            self._http.request("GET", f"/v1/accounts/sub-account-details{query}"),
        )

    def get_sub_account_balance(self, sub_account_id: str) -> AccountBalance:
        """`GET /v1/accounts/{subAccountId}/balance`."""
        return _build(
            AccountBalance,
            self._http.request(
                "GET", f"/v1/accounts/{_path_id(sub_account_id)}/balance"
            ),
        )

    def list_parent_terminals(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        **filters: Unpack[TerminalListFilters],
    ) -> tuple[list[Terminal], str | None]:
        """`GET /v1/accounts/terminals`. Returns one page as `(terminals, next_cursor)`."""
        query = _query({"cursor": cursor, "limit": limit, **filters})
        data = self._http.request("GET", f"/v1/accounts/terminals{query}")
        return _terminal_page(data)

    def list_sub_account_terminals(
        self,
        account_id: str,
        cursor: str | None = None,
        limit: int | None = None,
        **filters: Unpack[TerminalListFilters],
    ) -> tuple[list[Terminal], str | None]:
        """`GET /v1/accounts/{accountId}/terminals`. Returns one page as `(terminals, next_cursor)`."""
        query = _query({"cursor": cursor, "limit": limit, **filters})
        data = self._http.request(
            "GET", f"/v1/accounts/{_path_id(account_id)}/terminals{query}"
        )
        return _terminal_page(data)

    def iterate_parent_terminals(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        **filters: Unpack[TerminalListFilters],
    ) -> Iterator[Terminal]:
        """Every terminal of the parent account, across all pages."""
        return paginate(
            lambda c: self.list_parent_terminals(
                cursor=c or cursor, limit=limit, **filters
            )
        )

    def iterate_sub_account_terminals(
        self,
        account_id: str,
        cursor: str | None = None,
        limit: int | None = None,
        **filters: Unpack[TerminalListFilters],
    ) -> Iterator[Terminal]:
        """Every terminal of a sub account, across all pages."""
        return paginate(
            lambda c: self.list_sub_account_terminals(
                account_id, cursor=c or cursor, limit=limit, **filters
            )
        )
