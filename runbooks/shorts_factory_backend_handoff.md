# Shorts Factory Backend Handoff

Scope: trusted backend-to-backend quiz delivery for German quiz short videos.

Base URLs:

- Local MVP: `http://127.0.0.1:8000`
- Protected beta route: `https://api.valerchik.de`

Provisioning:

```bash
PYTHONPATH=src python3 tools/provision_shorts_factory_backend_consumer.py \
  --db-path var/quizbank_mvp.sqlite3 \
  --secret-env-out var/deployment_env/shorts_factory_backend.env
```

The provisioner creates active consumer `shorts_factory_backend`, a hashed active API credential and active `quiz_delivery` entitlement for approved/published delivery. The raw API key is written only to the gitignored env file and must be handed over through a private channel, not GitHub.

Smoke: next approved/published item with answer-enabled projection:

```bash
curl -sS "${QUIZ_BANK_API_BASE_URL}/v1/quiz-items/next" \
  -H "Content-Type: application/json" \
  -H "X-Consumer-Id: shorts_factory_backend" \
  -H "X-QuizBank-API-Key: ${QUIZ_BANK_CONSUMER_API_KEY}" \
  --data '{"consumer_id":"shorts_factory_backend","cefr_level":"A2","theme_ids":["T10"]}'
```

Smoke: trusted manual `item_id` lookup:

```bash
curl -sS "${QUIZ_BANK_API_BASE_URL}/v1/quiz-items/${QUIZ_BANK_ITEM_ID}" \
  -H "X-Consumer-Id: shorts_factory_backend" \
  -H "X-QuizBank-API-Key: ${QUIZ_BANK_CONSUMER_API_KEY}"
```

Smoke: delivery outcome:

```bash
curl -sS -X POST "${QUIZ_BANK_API_BASE_URL}/v1/deliveries/${QUIZ_BANK_DELIVERY_ID}/outcome" \
  -H "Content-Type: application/json" \
  -H "X-Consumer-Id: shorts_factory_backend" \
  -H "X-QuizBank-API-Key: ${QUIZ_BANK_CONSUMER_API_KEY}" \
  --data '{"status":"sent"}'
```

Expected trusted quiz projection includes `quiz_item.feedback.correctAnswerId` and `quiz_item.feedback.explanation`. Regular consumers do not receive `quiz_item.feedback`.
