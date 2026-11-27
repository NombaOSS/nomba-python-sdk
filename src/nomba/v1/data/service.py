from __future__ import annotations

from nomba.http import HttpClient
from nomba.lib.util import _build, _path_id
from nomba.v1.data.types import DataPlan

# Ported from Node's src/services/v1/data/data.service.ts (v1: data bundle plan listing --
# lookup only, no purchase endpoint here; see Task 18's data v2 equivalent for purchases).
# No settle()/OutcomeTable call sites exist in that file, so this is plain.


class BillData:
    """Data bundle bill validation (v1): plan listing."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_data_plans(self, telco: str) -> list[DataPlan]:
        """`GET /v1/bill/data-plan/{telco}`. The available data plans for that telco
        network."""
        data = self._http.request("GET", f"/v1/bill/data-plan/{_path_id(telco)}")
        return [_build(DataPlan, p) for p in data]
