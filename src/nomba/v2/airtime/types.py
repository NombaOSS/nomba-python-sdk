from __future__ import annotations

from typing import NotRequired, TypedDict

from nomba.http import Network

# Ported from Node's src/types/v2/airtime/airtime.types.ts. No response dataclasses: both
# endpoints route through settle(), which returns the raw response data.


class AirtimePurchaseParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    amount: float
    # 11 to 13 characters.
    phoneNumber: str
    network: Network
    senderName: NotRequired[str]
