from __future__ import annotations

from typing import Unpack

from nomba.http import HttpClient
from nomba.lib.util import _build, _query
from nomba.v1.cable.types import (
    CableCustomerLookupParams,
    CablePlan,
    CablePlansParams,
)

# Ported from Node's src/services/v1/cable/cable.service.ts (v1: plan listing and customer
# lookup -- payments moved to v2, see Task 18's cable v2 equivalent). No settle()/
# OutcomeTable call sites exist in that file, so this is plain.


class BillCable:
    """Cable TV bill validation (v1): plan listing and customer lookup."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_cable_plans(self, **params: Unpack[CablePlansParams]) -> list[CablePlan]:
        """`GET /v1/bill/cableTvProduct`. `cableTvType` (in `params`) selects the provider."""
        data = self._http.request("GET", "/v1/bill/cableTvProduct" + _query(params))
        return [_build(CablePlan, p) for p in data]

    def lookup_customer(self, **params: Unpack[CableCustomerLookupParams]) -> str:
        """`GET /v1/bill/cable/lookup`. Validates a smartcard number and returns the
        customer's account name. `cableTvType`/`customerId` (in `params`)."""
        name: str = self._http.request("GET", "/v1/bill/cable/lookup" + _query(params))
        return name
