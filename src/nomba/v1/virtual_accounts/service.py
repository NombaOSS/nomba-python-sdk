from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.paginate import paginate
from nomba.lib.util import _build, _path_id, _query
from nomba.v1.virtual_accounts.types import (
    CreatedVirtualAccount,
    CreateVirtualAccountParams,
    FilterVirtualAccountsParams,
    UpdateVirtualAccountParams,
    VirtualAccount,
)

# Ported from Node's src/services/v1/virtual-accounts/virtual-accounts.service.ts (method
# list). No settle()/OutcomeTable usage in Node's service -- this domain stays plain.


def _va_page(data: dict[str, Any]) -> tuple[list[VirtualAccount], str | None]:
    results = [_build(VirtualAccount, v) for v in data.get("results") or []]
    cursor = data.get("cursor") or None
    return results, cursor


class VirtualAccounts:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self, **params: Unpack[CreateVirtualAccountParams]
    ) -> CreatedVirtualAccount:
        """`POST /v1/accounts/virtual`. Creates a virtual account for the parent account."""
        return _build(
            CreatedVirtualAccount,
            self._http.request("POST", "/v1/accounts/virtual", body=params),
        )

    def create_for_sub_account(
        self, sub_account_id: str, **params: Unpack[CreateVirtualAccountParams]
    ) -> CreatedVirtualAccount:
        """`POST /v1/accounts/virtual/{subAccountId}`. Creates a virtual account that collects
        funds into a specific sub account."""
        return _build(
            CreatedVirtualAccount,
            self._http.request(
                "POST", f"/v1/accounts/virtual/{_path_id(sub_account_id)}", body=params
            ),
        )

    def get(self, identifier: str) -> VirtualAccount:
        """`GET /v1/accounts/virtual/{identifier}`. Looks up a virtual account by reference or
        account number."""
        return _build(
            VirtualAccount,
            self._http.request("GET", f"/v1/accounts/virtual/{_path_id(identifier)}"),
        )

    def update(
        self, identifier: str, **params: Unpack[UpdateVirtualAccountParams]
    ) -> dict[str, Any]:
        """`PUT /v1/accounts/virtual/{identifier}`. Updates a virtual account's mutable fields."""
        data: dict[str, Any] = self._http.request(
            "PUT", f"/v1/accounts/virtual/{_path_id(identifier)}", body=params
        )
        return data

    def expire(self, identifier: str) -> dict[str, Any]:
        """`DELETE /v1/accounts/virtual/{identifier}`. Expires a virtual account so it no longer
        accepts payments. This action cannot be undone."""
        data: dict[str, Any] = self._http.request(
            "DELETE", f"/v1/accounts/virtual/{_path_id(identifier)}"
        )
        return data

    def list(
        self,
        filter: FilterVirtualAccountsParams | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> tuple[list[VirtualAccount], str | None]:
        """`POST /v1/accounts/virtual/list`. Lists virtual accounts matching the given filters."""
        query = _query({"cursor": cursor, "limit": limit})
        data = self._http.request(
            "POST", f"/v1/accounts/virtual/list{query}", body=filter or {}
        )
        return _va_page(data)

    def iterate(
        self,
        filter: FilterVirtualAccountsParams | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Iterator[VirtualAccount]:
        """Every matching virtual account, across all pages."""
        return paginate(lambda c: self.list(filter, cursor=c or cursor, limit=limit))
