from __future__ import annotations

from typing import TypedDict

# Ported from Node's src/types/v2/betting/betting.types.ts. No response dataclasses: both
# endpoints route through settle(), which returns the raw response data.


class BettingPaymentParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    # From `betting_providers`.
    bettingProvider: str
    phoneNumber: str
    payerName: str
    amount: float
    # Same as verified with `lookup_customer`.
    customerId: str
