from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

# Ported from Node's src/types/v2/transfers/transfers.types.ts.

TransferType = Literal[
    "withdrawal",
    "purchase",
    "transfer",
    "p2p",
    "online_checkout",
    "qrt_credit",
    "qrt_debit",
]


class BankAccountLookupParams(TypedDict):
    # 10 digits.
    accountNumber: str
    # From `list_banks`.
    bankCode: str


class BankTransferParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    amount: float
    # 10 digits.
    accountNumber: str
    accountName: str
    bankCode: str
    senderName: NotRequired[str]
    narration: NotRequired[str]


class WalletTransferParams(TypedDict):
    """``merchantTxRef`` is supplied separately, as the method's own required positional
    argument -- not part of these kwargs."""

    amount: float
    receiverAccountId: str
    # Required per API documentation.
    senderName: str
    narration: NotRequired[str]


@dataclass(frozen=True)
class Bank:
    code: str | None = None
    name: str | None = None
    nipCode: str | None = None
    logo: str | None = None


@dataclass(frozen=True)
class BankAccountLookupResult:
    accountNumber: str | None = None
    accountName: str | None = None
