from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

# Ported from Node's src/types/v1/terminals/terminals.types.ts.


class AssignTerminalParams(TypedDict):
    serialNumber: str
    terminalLabel: NotRequired[str]


@dataclass(frozen=True)
class Terminal:
    terminalId: str
    serialNumber: str
    accountId: str
    parentAccountId: str
    merchantName: str
    terminalLabel: str
    createdAt: str
    updatedAt: str


@dataclass(frozen=True)
class TerminalPayment:
    paymentId: str
    status: str
    amount: float
    currency: str
    createdAt: str
