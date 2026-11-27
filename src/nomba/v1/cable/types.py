from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

# Ported from Node's src/types/v1/cable/cable.types.ts.


class CablePlansParams(TypedDict):
    cableTvType: str


class CableCustomerLookupParams(TypedDict):
    cableTvType: str
    customerId: str


@dataclass(frozen=True)
class CablePlan:
    subScriptionType: str | None = None
    amount: float | None = None
