from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

# Ported from Node's src/types/v1/accounts/accounts.types.ts.


class TerminalListFilters(TypedDict):
    """The non-pagination fields of Node's ``TerminalListParams`` (``cursor``/``limit`` are
    already explicit named parameters on the listing methods)."""

    terminalId: NotRequired[str]
    serialNumber: NotRequired[str]
    terminalLabel: NotRequired[str]
    merchantName: NotRequired[str]


@dataclass(frozen=True)
class AccountBalance:
    amount: str  # decimal string, e.g. "281946.0"
    currency: str
    timeCreated: str


@dataclass(frozen=True)
class AccountDetails:
    createdAt: str
    accountId: str
    accountHolderId: str
    accountRef: str
    bvn: str
    status: str
    type: str
    accountName: str
    currency: str
    banks: list[dict[str, Any]]
