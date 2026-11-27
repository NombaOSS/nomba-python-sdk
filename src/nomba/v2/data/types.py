from __future__ import annotations

from typing import NotRequired, TypedDict

from nomba.http import Network

# Ported from Node's src/types/v2/data/data.types.ts. No response dataclasses: both
# endpoints route through settle(), which returns the raw response data.


class DataPurchaseParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    # From `data_plans`. Buying by amount is deprecated and not supported here.
    productId: str
    # 11 to 13 characters.
    phoneNumber: str
    network: Network
    senderName: NotRequired[str]
