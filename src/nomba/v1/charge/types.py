from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

# Ported from Node's src/types/v1/charge/charge.types.ts.


class CardDetails(TypedDict):
    """The shape shown in the docs' example for the stringified ``cardDetails``."""

    cardCVV: NotRequired[int | str]
    cardExpiryMonth: NotRequired[int | str]
    cardExpiryYear: NotRequired[int | str]
    cardNumber: NotRequired[str]
    cardPin: NotRequired[int | str]


class DeviceInformation(TypedDict):
    """Browser information for the device making the call, used for 3D Secure."""

    httpBrowserLanguage: NotRequired[str]
    httpBrowserJavaEnabled: NotRequired[bool]
    httpBrowserJavaScriptEnabled: NotRequired[bool]
    httpBrowserColorDepth: NotRequired[str]
    httpBrowserScreenHeight: NotRequired[str]
    httpBrowserScreenWidth: NotRequired[str]
    httpBrowserTimeDifference: NotRequired[str]
    userAgentBrowserValue: NotRequired[str]
    deviceChannel: NotRequired[str]


class SubmitCardDetailsParams(TypedDict):
    cardDetails: NotRequired[str | CardDetails]
    # The encryption key if data encryption is in use, else an empty string.
    key: NotRequired[str]
    orderReference: NotRequired[str]
    saveCard: NotRequired[bool]
    deviceInformation: NotRequired[DeviceInformation]


@dataclass(frozen=True)
class ChargeOrderDetails:
    orderId: str | None = None
    orderReference: str | None = None
    customerId: str | None = None
    accountId: str | None = None
    callbackUrl: str | None = None
    customerEmail: str | None = None
    amount: float | None = None
    currency: str | None = None
    businessName: str | None = None
    businessEmail: str | None = None
    businessLogo: str | None = None


@dataclass(frozen=True)
class ChargeOrder:
    order: dict[str, Any] | None = None
    hasSavedCards: bool | None = None
    base64EncodedRsaPublicKey: str | None = None


@dataclass(frozen=True)
class SubmitCardDetailsResult:
    status: bool | None = None
    message: str | None = None
    # "00" completed, "T0" an OTP was sent and must be submitted next, "SO" 3D Secure is
    # required (see secureAuthenticationData).
    responseCode: str | None = None
    transactionId: str | None = None
    secureAuthenticationData: dict[str, Any] | None = None


@dataclass(frozen=True)
class SubmitCardOtpResult:
    status: bool | None = None
    message: str | None = None


@dataclass(frozen=True)
class ChargeTransactionDetails:
    status: bool | None = None
    message: str | None = None
    order: dict[str, Any] | None = None


@dataclass(frozen=True)
class FlashAccount:
    accountNumber: str | None = None
    accountName: str | None = None
    bankName: str | None = None
