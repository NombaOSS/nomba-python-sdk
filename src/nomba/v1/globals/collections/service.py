from __future__ import annotations

from typing import Unpack

from nomba.http import HttpClient
from nomba.lib.errors import IdempotencyKeyAbsentError
from nomba.lib.util import _build, _path_id
from nomba.v1.globals.collections.types import (
    CollectionTransaction,
    InflowProvider,
    InflowResult,
    InitiateInflowParams,
)

# Ported from Node's src/services/v1/globals/collections.service.ts (Global Collections:
# DRC mobile money inflows -- the collections side of Node's "globals" domain;
# src/services/v1/globals/payout.service.ts is the payouts side, ported separately).
#
# Per Task 13's lesson: none of collections.service.ts's methods call settle()/OutcomeTable
# in Node, even initiateInflow, which moves money (it only prompts an approval and always
# comes back pending/PENDING -- confirmed no settle() call site exists in that file). So
# none of these route through Python's settle() either. initiateInflow does, however,
# require idempotencyKey and raises IdempotencyKeyAbsentError (via a manual check, not
# settle()) when it is missing/blank -- ported as-is.


class Collections:
    """Global Collections (v1): DRC mobile money inflows."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def inflow_providers(self) -> list[InflowProvider]:
        """`GET /v1/global-collection/drc/inflow/providers`. The mobile money providers
        available for DRC inflows."""
        data = self._http.request("GET", "/v1/global-collection/drc/inflow/providers")
        return [_build(InflowProvider, p) for p in data]

    def initiate_inflow(self, **params: Unpack[InitiateInflowParams]) -> InflowResult:
        """`POST /v1/global-collection/inflow/initiate`. Prompts the customer to approve the
        charge on their phone. `params["idempotencyKey"]` is required -- the SDK never
        generates one for you, to prevent double collection."""
        idempotency_key = params.get("idempotencyKey")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise IdempotencyKeyAbsentError(
                "idempotencyKey", "/v1/global-collection/inflow/initiate"
            )
        return _build(
            InflowResult,
            self._http.request(
                "POST",
                "/v1/global-collection/inflow/initiate",
                body=params,
                idempotency_key=idempotency_key,
            ),
        )

    def get_transaction(self, transaction_id: str) -> CollectionTransaction:
        """`GET /v1/global-collection/transactions/{transactionId}`, with the
        `transactionReference` from `initiate_inflow`."""
        return _build(
            CollectionTransaction,
            self._http.request(
                "GET",
                f"/v1/global-collection/transactions/{_path_id(transaction_id)}",
            ),
        )
