# Website Quiz Teaser Consumer Evidence

Date: 2026-05-12

Scope: Controlled Protected Beta only; not public launch, signup or commercial launch.

- consumer created: yes
- entitlement: `quiz_delivery` / `active`
- quota: `5/scope/day`
- quota scope: `per-session/IP/user key via X-QuizBank-Quota-Key`
- CEFR scope: `A1, A2`
- themes: `Artikel, Alltag, Verben, Präpositionen`
- next item: `200`
- 5-question flow: `[200, 200, 200, 200, 200]`, unique `5`
- quota denial: `429 QUOTA_EXCEEDED`
- wrong credential: `401 AUTH_INVALID_API_KEY`
- missing quota scope: `400 QUOTA_SCOPE_REQUIRED`
- suspended: `403 CONSUMER_NOT_ACTIVE`
- revoked credential: `403 AUTH_CREDENTIAL_INACTIVE`

## Masked Frontend Env Handoff

```text
QUIZ_BANK_API_BASE_URL=http://127.0.0.1:8000
QUIZ_BANK_EDGE_API_KEY=qb_D7E...edge
QUIZ_BANK_CONSUMER_ID=website_quiz_teaser
QUIZ_BANK_CONSUMER_API_KEY=qb_3ct...ated
```

- raw secrets exposed: no
- unrestricted corpus access: no
