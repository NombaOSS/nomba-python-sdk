from __future__ import annotations

from typing import Any, Unpack

from nomba.http import HttpClient
from nomba.lib.util import _build
from nomba.v1.webhooks.types import (
    EventLog,
    EventLogsParams,
    EventsParams,
    ReplayParams,
    WebhookSubscription,
)

# Ported from Node's src/services/v1/webhooks/webhooks.service.ts. Plain read/action
# domain -- no settle()/OutcomeTable usage in Node's service (verified by grepping
# webhooks.service.ts).


def _list_page(cls: type[Any], data: dict[str, Any]) -> tuple[list[Any], str | None]:
    items: list[Any] = [_build(cls, r) for r in data.get("list") or []]
    return items, data.get("pageToken") or None


# Documented in the guide only (no API reference page). Its examples answer code "200",
# not "00" (Node: OK_CODES in webhooks.service.ts), so every call here accepts both.
_OK_CODES = ("00", "200")


class Webhooks:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def event_logs(
        self, **params: Unpack[EventLogsParams]
    ) -> tuple[list[EventLog], str | None]:
        """`POST /v1/webhooks/event-logs`. Returns webhooks sent to your system and how
        your server answered. Useful for debugging missed or failed deliveries."""
        data = self._http.request(
            "POST", "/v1/webhooks/event-logs", body=params, ok_codes=_OK_CODES
        )
        return _list_page(EventLog, data)

    def events(
        self, **params: Unpack[EventsParams]
    ) -> tuple[list[WebhookSubscription], str | None]:
        """`POST /v1/webhooks/events`. Returns your webhook subscriptions."""
        data = self._http.request(
            "POST", "/v1/webhooks/events", body=params, ok_codes=_OK_CODES
        )
        return _list_page(WebhookSubscription, data)

    def repush(self, hook_request_id: str) -> None:
        """`POST /v1/webhooks/re-push`. Resends a single webhook event. Use the
        `hookRequestId` from `event_logs`."""
        self._http.request(
            "POST",
            "/v1/webhooks/re-push",
            body={"hooksRequestId": hook_request_id},
            ok_codes=_OK_CODES,
        )

    def bulk_repush(self, hook_request_ids: list[str]) -> None:
        """`POST /v1/webhooks/bulk-re-push`. Resends multiple webhook events at once."""
        self._http.request(
            "POST",
            "/v1/webhooks/bulk-re-push",
            body={"hooksRequestIds": hook_request_ids},
            ok_codes=_OK_CODES,
        )

    def replay(self, **params: Unpack[ReplayParams]) -> None:
        """`POST /v1/webhooks/replay`. Resends every matching webhook event in a time
        window (`startDate`, `endDate`), with optional `filter`. Useful for recovering
        from webhook handler outages."""
        self._http.request(
            "POST",
            "/v1/webhooks/replay",
            body=params,
            ok_codes=_OK_CODES,
        )
