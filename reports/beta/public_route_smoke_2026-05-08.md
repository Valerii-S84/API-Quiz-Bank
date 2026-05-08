# Public Route Smoke Evidence

Date: 2026-05-08

Scope: protected public route smoke for `https://api.valerchik.de`.
No secret value was printed or committed.

## Result

| Check | Result |
|---|---|
| Endpoint | `https://api.valerchik.de` |
| No-key health | `401` |
| Authorized health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Authorized readiness | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| No-key delivery request | `401` |
| Authorized entitlement control | `403 ENTITLEMENT_MISSING_FEATURE` |

## Boundary

This smoke used the existing server-side public route key from the VPS secret
store. It did not deploy the app-level API credential branch and did not prove
new consumer-bound credentials on the public endpoint.
