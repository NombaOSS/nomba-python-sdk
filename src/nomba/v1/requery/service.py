from __future__ import annotations

from typing import Unpack

from nomba.http import HttpClient
from nomba.lib.util import _build, _path_id, _query
from nomba.v1.requery.types import Transaction, TransactionLookupParams

# Ported from Node's src/services/v1/requery/requery.service.ts (method list).
# Plain read domain -- no settle()/OutcomeTable usage in Node's service.


class Requery:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def fetch_parent_transaction(
        self, **lookup: Unpack[TransactionLookupParams]
    ) -> Transaction:
        """`GET /v1/transactions/accounts/single`. Looks up a transaction on the parent account
        by reference or ID."""
        return _build(
            Transaction,
            self._http.request(
                "GET", f"/v1/transactions/accounts/single{_query(lookup)}"
            ),
        )

    def fetch_sub_account_transaction(
        self, sub_account_id: str, **lookup: Unpack[TransactionLookupParams]
    ) -> Transaction:
        """`GET /v1/transactions/accounts/{subAccountId}/single`. Looks up a transaction on a
        sub account by reference or ID."""
        return _build(
            Transaction,
            self._http.request(
                "GET",
                f"/v1/transactions/accounts/{_path_id(sub_account_id)}/single{_query(lookup)}",
            ),
        )

    def requery_by_session(self, session_id: str) -> Transaction:
        """`GET /v1/transactions/requery/{sessionId}`. Looks up a bank transfer by its session
        ID. Nomba-to-Nomba wallet transfers do not return a sessionId; use
        `fetch_parent_transaction` or `fetch_sub_account_transaction` for those instead."""
        return _build(
            Transaction,
            self._http.request(
                "GET", f"/v1/transactions/requery/{_path_id(session_id)}"
            ),
        )
