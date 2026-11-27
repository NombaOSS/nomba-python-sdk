from __future__ import annotations

from typing import TypedDict

# Ported from Node's src/types/v2/cable/cable.types.ts. No response dataclasses: both
# endpoints route through settle(), which returns the raw response data.

# The guide lists dstv, gotv, startimes and ShowMax, but the API accepts others too.
CableTvType = str


class CableTvSubscriptionParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    cableTvType: CableTvType
    payerName: str
    amount: float
    customerId: str
