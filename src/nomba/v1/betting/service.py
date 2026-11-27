from __future__ import annotations

from typing import Unpack

from nomba.http import HttpClient
from nomba.lib.util import _build, _query
from nomba.v1.betting.types import BettingCustomerLookupParams, BettingProvider

# Ported from Node's src/services/v1/betting/betting.service.ts (v1: provider listing and
# customer lookup -- payments moved to v2, see Task 18's betting v2 equivalent). No
# settle()/OutcomeTable call sites exist in that file, so this is plain.


class BillBetting:
    """Betting bill validation (v1): provider listing and customer lookup."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_betting_providers(self) -> list[BettingProvider]:
        """`GET /v1/bill/betting/providers`. The supported betting providers."""
        data = self._http.request("GET", "/v1/bill/betting/providers")
        return [_build(BettingProvider, p) for p in data]

    def lookup_customer(self, **params: Unpack[BettingCustomerLookupParams]) -> str:
        """`GET /v1/bill/betting/lookup`. Validates a customer ID and returns the
        customer's account name. `bettingProvider`/`customerId` (in `params`)."""
        name: str = self._http.request(
            "GET", "/v1/bill/betting/lookup" + _query(params)
        )
        return name
