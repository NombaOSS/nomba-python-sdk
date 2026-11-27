from __future__ import annotations

from nomba.http import HttpClient
from nomba.lib.util import _build
from nomba.v1.electricity.types import ElectricityProvider

# Ported from Node's src/services/v1/electricity/electricity.service.ts (v1: disco listing
# only -- meter lookup/purchase moved to v2, see Task 18's electricity v2 equivalent). No
# settle()/OutcomeTable call sites exist in that file, so this is plain.


class BillElectricity:
    """Electricity bill validation (v1): disco listing."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_electricity_providers(self) -> list[ElectricityProvider]:
        """`GET /v1/bill/electricity/discos`. The electricity distribution companies
        (discos) available for meter lookup."""
        data = self._http.request("GET", "/v1/bill/electricity/discos")
        return [_build(ElectricityProvider, p) for p in data]
