from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

# Ported from Node's src/types/v1/betting/betting.types.ts.


class BettingCustomerLookupParams(TypedDict):
    bettingProvider: str
    customerId: str


@dataclass(frozen=True)
class BettingProvider:
    id: str | None = None
    name: str | None = None
    biller_id: str | None = None
    lookup_id: str | None = None
    amount: str | None = None
