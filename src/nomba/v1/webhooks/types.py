from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

# Ported from Node's src/types/v1/webhooks/webhooks.types.ts.


class EventLogsParams(TypedDict):
    coreUserId: NotRequired[str]
    limit: NotRequired[int]
    # e.g. payment_success.
    eventType: NotRequired[str]
    # e.g. 2025-03-03.
    startDateTime: NotRequired[str]
    endDateTime: NotRequired[str]


class EventsParams(TypedDict):
    coreUserId: NotRequired[str]
    limit: NotRequired[int]


ReplayStatus = Literal["INITIATED", "FAILED", "INCONCLUSIVE", "PUSHED"]
ReplayEventType = Literal[
    "PAYMENT_SUCCESS",
    "PAYMENT_FAILED",
    "PAYOUT_SUCCESS",
    "PAYOUT_FAILED",
    "ORDER_SUCCESS",
    "PAYMENT_REVERSAL",
    "PAYOUT_REFUND",
]


class ReplayFilter(TypedDict):
    statuses: NotRequired[list[ReplayStatus]]
    eventTypes: NotRequired[list[ReplayEventType]]


class ReplayParams(TypedDict):
    # RFC 3339, e.g. 2026-01-27T00:00:00Z.
    startDate: str
    endDate: str
    filter: NotRequired[ReplayFilter]


@dataclass(frozen=True)
class EventLog:
    webhookUrl: str | None = None
    eventId: int | None = None
    eventType: str | None = None
    hookRequestId: str | None = None
    responsePayload: str | None = None
    responseHttpStatus: int | None = None


@dataclass(frozen=True)
class WebhookSubscription:
    webHookId: int | None = None
    eventURL: str | None = None
    description: str | None = None
    eventType: str | None = None
    enabled: bool | None = None
