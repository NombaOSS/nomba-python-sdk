from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

# Ported from Node's src/types/v1/virtual-accounts/virtual-accounts.types.ts.


class CreateVirtualAccountParams(TypedDict):
    # Your unique reference for the account. 16 to 64 characters.
    accountRef: str
    # 8 to 64 characters.
    accountName: str
    currency: NotRequired[Literal["NGN"]]
    # Defaults to the parent account's BVN.
    bvn: NotRequired[str]
    nin: NotRequired[str]
    # e.g. "2026-01-30 12:15:00". Omit for a permanent (static) account.
    expiryDate: NotRequired[str]
    # The account then accepts only this exact amount.
    expectedAmount: NotRequired[float]
    callbackUrl: NotRequired[str]
    restrictInflowToAccountName: NotRequired[bool]


class UpdateVirtualAccountParams(TypedDict):
    newAccountRef: NotRequired[str]
    accountName: NotRequired[str]
    # Decimal string, e.g. "100.0".
    expectedAmount: NotRequired[str]


class FilterVirtualAccountsParams(TypedDict):
    accountName: NotRequired[str]
    accountRef: NotRequired[str]
    bvn: NotRequired[str]
    bankAccountNumber: NotRequired[str]
    dateCreatedFrom: NotRequired[str]
    dateCreatedTo: NotRequired[str]
    expired: NotRequired[bool]
    resourceAcquired: NotRequired[bool]


@dataclass(frozen=True)
class VirtualAccount:
    createdAt: str
    accountHolderId: str
    accountRef: str
    bvn: str
    accountName: str
    bankName: str
    bankAccountName: str
    bankAccountNumber: str
    currency: str
    callbackUrl: str | None = None
    expired: bool | None = None
    restrictInflowToAccountName: bool | None = None


@dataclass(frozen=True)
class CreatedVirtualAccount:
    createdAt: str
    accountHolderId: str
    accountRef: str
    bvn: str
    accountName: str
    bankName: str
    bankAccountName: str
    bankAccountNumber: str
    currency: str
    callbackUrl: str | None = None
    identifierType: str | None = None
    expiryDate: str | None = None
    expired: bool | None = None
    restrictInflowToAccountName: bool | None = None
