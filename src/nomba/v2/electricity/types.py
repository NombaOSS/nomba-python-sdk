from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

# Ported from Node's src/types/v2/electricity/electricity.types.ts.


class MeterLookupV2Params(TypedDict):
    # From `electricity_providers`.
    disco: str
    customerId: str


class ElectricityPaymentParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    # From `electricity_providers`.
    disco: str
    payerName: str
    amount: float
    customerId: str
    # Usually PREPAID or POSTPAID.
    meterType: str


@dataclass(frozen=True)
class MeterLookupResult:
    name: str | None = None
    address: str | None = None
