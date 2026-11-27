from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

# Ported from Node's src/types/v1/checkout/checkout.types.ts.


class SplitListEntry(TypedDict):
    accountId: NotRequired[str]
    value: NotRequired[float]


class SplitRequest(TypedDict):
    splitType: NotRequired[Literal["PERCENTAGE", "AMOUNT"]]
    splitList: NotRequired[list[SplitListEntry]]


class CheckoutOrder(TypedDict):
    # Your reference for the order.
    orderReference: NotRequired[str]
    customerId: NotRequired[str]
    # Where the customer is redirected after payment.
    callbackUrl: str
    customerEmail: str
    amount: float
    currency: Literal["NGN", "CDF", "USD", "EUR", "GBP"]
    # Account to deposit the funds into. Must be one of your outlet accounts.
    accountId: NotRequired[str]
    allowedPaymentMethods: NotRequired[
        list[
            Literal[
                "Card",
                "Transfer",
                "Nomba QR",
                "USSD",
                "Buy Now Pay Later",
                "MOMO",
                "Intl Card",
                "Apple Pay",
                "Intl Transfer",
            ]
        ]
    ]
    splitRequest: NotRequired[SplitRequest]
    # String keys and values, returned in webhook payloads.
    orderMetaData: NotRequired[dict[str, str]]


class CreateCheckoutOrderParams(TypedDict):
    # Tokenize the card used, only if you will charge it again later.
    tokenizeCard: NotRequired[bool]


class FetchCheckoutTransactionParams(TypedDict):
    idType: NotRequired[Literal["ORDER_ID", "ORDER_REFERENCE"]]
    id: NotRequired[str]


class RefundCheckoutTransactionParams(TypedDict):
    # For a partial refund.
    amount: NotRequired[float]
    # Refund by bank transfer: 10 digit account number and bank code.
    accountNumber: NotRequired[str]
    bankCode: NotRequired[str]


class ListTokenizedCardsParams(TypedDict):
    customerEmail: NotRequired[str]
    startDate: NotRequired[str]
    endDate: NotRequired[str]
    # Page number to start from. Omit or 0 for the first page.
    page: NotRequired[int | str]


@dataclass(frozen=True)
class CheckoutOrderCreated:
    checkoutLink: str
    orderReference: str


@dataclass(frozen=True)
class CheckoutTransaction:
    success: bool | None = None
    message: str | None = None
    order: dict[str, Any] | None = None
    transactionDetails: dict[str, Any] | None = None
    transferDetails: dict[str, Any] | None = None
    cardDetails: dict[str, Any] | None = None


@dataclass(frozen=True)
class CheckoutResult:
    success: bool
    message: str


@dataclass(frozen=True)
class ChargeTokenizedCardResult:
    status: bool | None = None
    message: str | None = None
    orderId: str | None = None
    orderReference: str | None = None
    otpRequired: bool | None = None
    transactionId: str | None = None


@dataclass(frozen=True)
class TokenizedCardData:
    tokenKey: str | None = None
    customerEmail: str | None = None
    cardType: str | None = None
    cardPan: str | None = None
    tokenExpirationDate: str | None = None


@dataclass(frozen=True)
class TokenizedCardResult:
    status: bool | None = None
    message: str | None = None


@dataclass(frozen=True)
class UpdatedTokenizedCard:
    status: bool | None = None
    message: str | None = None
    tokenizedCardData: list[dict[str, Any]] | None = None
