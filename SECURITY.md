# Security policy

## Reporting a vulnerability

Please don't open a public issue for a security problem. Report it privately in either of these ways:

- **Private vulnerability report:** open this repository's **Security** tab and choose **Report a vulnerability**.
- **Email:** security@nomba.com.

Include the affected version, a description and, if possible, steps to reproduce. We aim to acknowledge reports within three working days.

## Supported versions

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |
| Older   | No        |

The SDK is pre-1.0 (`0.x`); only the latest published version receives fixes.

## How the SDK protects you

- GET calls are retried automatically; a mutating call is sent once with one idempotency key and is never auto-retried except the one 401-renew-and-retry, which reuses the same key. If its outcome is unknown, the SDK raises `OutcomeUnknownError` rather than guessing.
- Redirects are never followed, so the bearer token can't be sent to another host, and request paths must start with `/`.
- Webhook signatures are compared with `hmac.compare_digest`.
- Path ids are validated and reject `""`, `.` and `..`.
