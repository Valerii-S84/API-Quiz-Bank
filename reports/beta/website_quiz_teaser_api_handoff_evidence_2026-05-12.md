# Website Quiz Teaser API Handoff Evidence

Date: 2026-05-12

Scope: API Bank local runtime only. VPS deploy was not touched. This is a Controlled Protected Beta handoff, not a broad public launch, not public signup and not a commercial launch.

## Consumer Readiness

- consumer exists: `yes`
- consumer id: `website_quiz_teaser`
- credential active and hashed: `yes`
- entitlement: `quiz_delivery` / `active`
- CEFR scope: `A1, A2`
- allowed themes: `Artikel, Alltag, Verben, Präpositionen`
- runtime theme scope: `T02`
- quota: `5/day`

## API Proof

- next item: `200`
- delivery records created: `5`
- repeat policy: `5` unique items in 5 requests
- quota denial: `429 QUOTA_EXCEEDED`
- unauthenticated denial: `401 AUTH_REQUIRED`
- wrong credential denial: `401 AUTH_INVALID_API_KEY`
- entitlement removal denial: `403 ENTITLEMENT_MISSING_FEATURE`
- suspended consumer denial: `403 CONSUMER_NOT_ACTIVE`
- revoked credential denial: `403 AUTH_CREDENTIAL_INACTIVE`

## Masked Frontend Env Handoff

```text
QUIZ_BANK_API_BASE_URL=http://127.0.0.1:8000
QUIZ_BANK_EDGE_API_KEY=qb_pjg...edge
QUIZ_BANK_CONSUMER_ID=website_quiz_teaser
QUIZ_BANK_CONSUMER_API_KEY=qb_myi...ated
```

## API / Frontend Contract

- API Bank endpoint: `POST /v1/quiz-items/next`
- Required headers: `X-API-Key`, `X-Consumer-Id`, `X-QuizBank-API-Key`
- Expected body: `{ "consumer_id": "website_quiz_teaser", "cefr_level": "A2", "theme_ids": ["T02"] }`
- Question id: `quiz_item.id`
- Question text: `quiz_item.question.text`
- Answer options: `quiz_item.options[].id` and `quiz_item.options[].text`
- Validation data: `quiz_item.feedback.correctAnswerId` for this protected beta consumer
- Explanation: `quiz_item.feedback.explanation` when available
- Delivery id: top-level `delivery_id` and `delivery.delivery_id`
- Quota exceeded: `429 QUOTA_EXCEEDED`
- Unauthorized or wrong credential: `401 AUTH_REQUIRED` or `401 AUTH_INVALID_API_KEY`
- Suspended consumer: `403 CONSUMER_NOT_ACTIVE`
- Frontend proxy should fail closed and show unavailable UI for non-2xx API Bank responses.

## Security Boundary

- raw secrets in report: no
- raw secrets in Git: no
- raw env values stored only in local git-ignored secure env file
- unrestricted corpus access: no
- broad public launch: no
