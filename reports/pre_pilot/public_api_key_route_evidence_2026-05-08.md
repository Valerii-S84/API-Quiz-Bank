# Public API Key Route Evidence

Date: 2026-05-08

Status: protected public route enabled for API Quiz Bank; public beta and
production remain not approved.

## Scope

This report records the `api.valerchik.de` Caddy route protected by
`X-API-Key`. It does not approve public beta, production, Telegram real send or
unkeyed public API access.

## Route

| Field | Evidence |
|---|---|
| Public host | `api.valerchik.de` |
| DNS result | `46.225.181.45` |
| Caddy container | `quiz_arena_caddy_prod` |
| Caddy route | `api.valerchik.de` |
| Public auth gate | `X-API-Key` header |
| Key storage | `/root/api-quiz-bank/public-api-key` on VPS, mode `600` |
| Caddy env variable | `API_QUIZ_BANK_PUBLIC_API_KEY` |
| Upstream | `api-quiz-bank-pilot:8000` over Docker network |
| Host bind still present | `127.0.0.1:8010` |

## Runtime Change Evidence

| Component | Result |
|---|---|
| API compose network | `api-quiz-bank-pilot` joined `quiz-arena_default` |
| API container state | `running/healthy` after recreate |
| API public host bind | still `127.0.0.1:8010` |
| Caddy state | `running`, restart count `0` after final recreate |
| Quiz Arena API state | `running/healthy` after compose dependency recreate |

Config backups were created on the VPS before changes:

```text
/opt/api-quiz-bank/docker-compose.api-quiz-bank.yml.bak_20260508T084341Z
/opt/quiz-arena/deploy/Caddyfile.bak_api_quiz_bank_20260508T084341Z
```

## Verification

Unauthorized public health:

```text
curl https://api.valerchik.de/health without X-API-Key
-> 401 Unauthorized
```

Authorized public health:

```text
curl -H "X-API-Key: <redacted>" https://api.valerchik.de/health
-> 200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}
```

Authorized public readiness:

```text
curl -H "X-API-Key: <redacted>" https://api.valerchik.de/ready
-> 200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}
```

Unauthorized delivery endpoint:

```text
POST https://api.valerchik.de/v1/quiz-items/next without X-API-Key
-> 401 Unauthorized
```

Authorized delivery control:

```text
POST https://api.valerchik.de/v1/quiz-items/next with X-API-Key
and consumer_no_entitlement
-> 403 ENTITLEMENT_MISSING_FEATURE
```

## Boundaries

- API key value was not printed or committed.
- API remains directly bound to loopback on the host.
- Public access is key-gated at Caddy.
- Telegram real send was not executed.
- Public beta remains blocked until support, legal/privacy and monitoring
  evidence are recorded.
- Production remains blocked until production deployment, monitored backups,
  restore drill, incident drill, rollback execution and launch approval exist.
