# Telegram Dry-Run Readiness Artifact

Date: 2026-05-08

Status: VPS dry-run executed; no Telegram real send.

## Scope

This artifact defines and records the local-only VPS Telegram dry-run protocol
for the closed pilot. It does not load a bot token, call Telegram Bot API,
integrate with existing bots, open public access or approve a controlled real
send.

## Endpoint Path

The Telegram worker or dry-run harness must request governed selection through
the API. It must not read raw CSV files.

```http
POST http://127.0.0.1:8010/v1/quiz-items/next
X-Consumer-Id: <telegram_consumer_id>
Content-Type: application/json

{
  "consumer_id": "<telegram_consumer_id>",
  "cefr_level": "<pilot_cefr_level>",
  "theme_ids": ["<pilot_theme_id>"]
}
```

Optional verification after selection:

```http
GET http://127.0.0.1:8010/v1/deliveries/<delivery_id>
X-Consumer-Id: <telegram_consumer_id>
```

## Adapter Payload Shape

Dry-run builds this payload shape and records it without sending:

```json
{
  "method": "sendPoll",
  "chat_id": "<redacted_approved_closed_pilot_target>",
  "question": "<quiz_item.prompt>",
  "options": ["<option_1>", "<option_2>", "..."],
  "type": "quiz",
  "correct_option_id": "<adapter_only_index>",
  "is_anonymous": false,
  "allows_multiple_answers": false,
  "protect_content": true
}
```

`correct_option_id` may exist only inside the authorized adapter-to-Telegram
payload. It must be redacted from public reports and normal learner-facing API
responses.

## Dry-Run Log Contract

Dry-run success log fields:

```json
{
  "event": "telegram_dry_run",
  "environment": "local-only-vps",
  "consumer_id": "<telegram_consumer_id>",
  "delivery_id": "<delivery_id>",
  "quiz_item_id": "<quiz_item_id>",
  "item_status": "approved_or_published",
  "compatibility_status": "ok",
  "decision": "would_send",
  "telegram_message_id": null
}
```

Dry-run failure or skip log fields:

```json
{
  "event": "telegram_dry_run",
  "environment": "local-only-vps",
  "consumer_id": "<telegram_consumer_id>",
  "delivery_id": null,
  "quiz_item_id": null,
  "compatibility_status": "failed_or_not_applicable",
  "decision": "blocked_or_would_skip",
  "reason_code": "<api_or_adapter_reason_code>",
  "telegram_message_id": null
}
```

## Compatibility Checks

- question text fits Telegram poll limits;
- option count and option text fit Telegram poll limits;
- exactly one correct option is available to the adapter;
- no draft, blocked or retired item is sent;
- consumer is active and entitled;
- repeat and quota controls pass;
- no bot token, chat id or correct answer is printed in logs.

## Stop Conditions

- API is not bound to `127.0.0.1:8010`.
- `/health` or `/ready` fails.
- Consumer is suspended, blocked, not entitled or over quota.
- Selected item status is not approved/published for the pilot scope.
- Payload compatibility fails.
- Target chat/channel is missing or not approved.
- Logging would expose token, chat id or correct answer.
- Operator cannot disable the consumer/channel.

## Current Decision

Real Telegram send remains `not approved/not done`.

## VPS Dry-Run Evidence

Executed on the local-only VPS through `http://127.0.0.1:8010`; no Telegram Bot
API request was made.

```text
seeded quiz items: 1
seeded consumer: consumer_vps_telegram_dry_run_20260508T082436Z
```

Result:

```json
{
  "event": "telegram_dry_run",
  "environment": "local-only-vps",
  "consumer_id": "consumer_vps_telegram_dry_run_20260508T082436Z",
  "delivery_id": "deliv_f84040c93e124d73",
  "quiz_item_id": "approved_traceable_001",
  "item_status": "approved",
  "compatibility_status": "ok",
  "decision": "would_send",
  "adapter_payload_summary": {
    "method": "sendPoll",
    "chat_id": "<redacted_approved_closed_pilot_target>",
    "question_length": 38,
    "option_count": 4,
    "correct_option_id": "<redacted_adapter_only_index>",
    "protect_content": true
  },
  "checks": {
    "question_non_empty": true,
    "question_length_ok": true,
    "option_count_ok": true,
    "option_lengths_ok": true,
    "delivery_id_present": true,
    "item_status_ok": true,
    "telegram_message_id": null
  }
}
```

Current conclusion: Telegram dry-run is complete for local-only/internal pilot;
controlled real send remains not approved and not done.
