from __future__ import annotations

import json as jsonlib

import httpx

from nomba.v1.webhooks import EventLog, Webhooks, WebhookSubscription


def test_event_logs_returns_logs_and_page_token(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "list": [{"hookRequestId": "h1", "eventType": "payment_success"}],
                    "pageToken": "next",
                },
            },
        )

    http = fake_http(handler)
    webhooks = Webhooks(http)
    logs, page_token = webhooks.event_logs(eventType="payment_success")
    assert logs == [EventLog(hookRequestId="h1", eventType="payment_success")]
    assert page_token == "next"
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/webhooks/event-logs"
    assert jsonlib.loads(req.content) == {"eventType": "payment_success"}


def test_event_logs_empty_list_returns_no_page_token(fake_http):
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "00", "data": {"list": []}})
    )
    webhooks = Webhooks(http)
    logs, page_token = webhooks.event_logs()
    assert logs == []
    assert page_token is None


def test_event_logs_accepts_code_200(fake_http):
    # Node's docs examples for this call answer with code "200", not "00".
    http = fake_http(
        lambda req: httpx.Response(200, json={"code": "200", "data": {"list": []}})
    )
    webhooks = Webhooks(http)
    logs, page_token = webhooks.event_logs()
    assert logs == []
    assert page_token is None


def test_events_returns_subscriptions(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        return httpx.Response(
            200,
            json={
                "code": "00",
                "data": {
                    "list": [{"webHookId": 1, "eventURL": "https://x", "enabled": True}]
                },
            },
        )

    http = fake_http(handler)
    webhooks = Webhooks(http)
    subs, page_token = webhooks.events(coreUserId="u1")
    assert subs == [
        WebhookSubscription(webHookId=1, eventURL="https://x", enabled=True)
    ]
    assert page_token is None
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/webhooks/events"
    assert jsonlib.loads(req.content) == {"coreUserId": "u1"}


def test_repush_posts_hook_request_id(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        # Node: repush answers with no `data` key at all, so the client resolves to
        # undefined -- Python must not raise on a missing `data` field here.
        return httpx.Response(200, json={"code": "00"})

    http = fake_http(handler)
    webhooks = Webhooks(http)
    webhooks.repush("hook1")
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/webhooks/re-push"
    assert jsonlib.loads(req.content) == {"hooksRequestId": "hook1"}


def test_repush_accepts_code_200(fake_http):
    http = fake_http(lambda req: httpx.Response(200, json={"code": "200"}))
    webhooks = Webhooks(http)
    webhooks.repush("hook1")


def test_bulk_repush_posts_hook_request_ids(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        # Node: bulkRepush also answers with no `data` key.
        return httpx.Response(200, json={"code": "00"})

    http = fake_http(handler)
    webhooks = Webhooks(http)
    webhooks.bulk_repush(["hook1", "hook2"])
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/webhooks/bulk-re-push"
    assert jsonlib.loads(req.content) == {"hooksRequestIds": ["hook1", "hook2"]}


def test_replay_posts_time_window_and_filter(fake_http):
    captured = {}

    def handler(req):
        captured["request"] = req
        # Node: replay also answers with no `data` key.
        return httpx.Response(200, json={"code": "00"})

    http = fake_http(handler)
    webhooks = Webhooks(http)
    webhooks.replay(
        startDate="2026-01-27T00:00:00Z",
        endDate="2026-01-28T00:00:00Z",
        filter={"statuses": ["FAILED"]},
    )
    req = captured["request"]
    assert req.method == "POST"
    assert req.url.path == "/v1/webhooks/replay"
    assert jsonlib.loads(req.content) == {
        "startDate": "2026-01-27T00:00:00Z",
        "endDate": "2026-01-28T00:00:00Z",
        "filter": {"statuses": ["FAILED"]},
    }
