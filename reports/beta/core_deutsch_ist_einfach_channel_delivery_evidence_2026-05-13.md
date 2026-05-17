# Core Deutsch ist einfach! Channel Delivery Evidence

Date: 2026-05-13

Scope: Controlled Protected Beta / controlled channel delivery only.

- Broad public launch: no.
- Public signup: no.
- Commercial launch: no.
- Raw secrets exposed in this report: no.

## Consumer

- channel id: `-1002987612505`
- consumer name: `core_deutsch_ist_einfach_channel`
- status: `active` in local provisioning proof
- credential: active hashed API credential proof; raw value not committed and not printed
- entitlement: `quiz_delivery` / `active`
- CEFR scope: `A2`
- theme scope: `T01`, `T04`
- quota: `2/day`
- delivery target: Telegram channel `-1002987612505`

Local DB proof from `var/beta/core_deutsch_ist_einfach_channel.sqlite3`:

```json
{
  "consumer": {
    "consumer_id": "core_deutsch_ist_einfach_channel",
    "status": "active",
    "allowed_cefr_levels_json": "[\"A2\"]",
    "allowed_theme_ids_json": "[\"T01\", \"T04\"]",
    "daily_quota_limit": 2
  },
  "entitlement": {
    "feature": "quiz_delivery",
    "status": "active",
    "allowed_cefr_levels_json": "[\"A2\"]",
    "allowed_theme_ids_json": "[\"T01\", \"T04\"]"
  },
  "credential": {
    "credential_id": "cred_core_deutsch_ist_einfach_channel",
    "status": "active",
    "hash_len": 64
  }
}
```

## Schedule

- schedule: daily `12:07` `Europe/Berlin`
- format: one scheduled batch with exactly 2 quiz slots
- slot 1: `A2` / `T01` / `core_deutsch_ist_einfach_channel:T01:12_07`
- slot 2: `A2` / `T04` / `core_deutsch_ist_einfach_channel:T04:12_07`
- first live run policy: next scheduled `12:07 Europe/Berlin` after deployment
- backfill missed runs: no

## Dry Run

Command run locally without Telegram Bot API call:

```text
PYTHONPATH=src python3 tools/run_protected_beta_schedule.py --db-path var/beta/core_deutsch_ist_einfach_channel.sqlite3 --mode dry_run --slot-time 12:07 --now 2026-05-13T12:07:00+02:00
```

Result:

- dry-run status: `skipped` with `dry_run_no_bot_api_call`
- Telegram target shown only as redacted `***2505`
- no test/debug text posted to the real channel
- delivery records created and then marked `skipped`

Selection proof:

```json
[
  {
    "slot_id": "core_deutsch_ist_einfach_channel:T01:12_07",
    "delivery_date": "2026-05-13",
    "cefr_level": "A2",
    "theme_id": "T01",
    "status": "skipped",
    "quiz_item_id": "gmb_person_family_natural_usage_bank_a1_c2_2_50_pnu_1458"
  },
  {
    "slot_id": "core_deutsch_ist_einfach_channel:T04:12_07",
    "delivery_date": "2026-05-13",
    "cefr_level": "A2",
    "theme_id": "T04",
    "status": "skipped",
    "quiz_item_id": "gmb_shopping_actions_bank_a2_100_sa_089"
  }
]
```

## Idempotency

Implemented scheduled slot ledger:

- key fields: `consumer_id`, `channel_id`, `delivery_date`, `slot_id`, `theme_id`, `cefr_level`
- duplicate sent retry behavior: existing `sent` slot returns stored delivery and does not call the Telegram adapter again
- partial retry behavior: if one slot is `sent` and another is `failed`, retry sends only the failed slot
- no item behavior: slot is logged as `no_item` with `SELECTION_NO_ELIGIBLE_ITEM`; no empty/broken Telegram payload is sent

Automated proof:

- `tests.test_protected_beta.ProtectedBetaTests.test_core_batch_retry_does_not_duplicate_sent_slot`
- `tests.test_protected_beta.ProtectedBetaTests.test_core_batch_retry_only_resends_failed_slot`
- `tests.test_protected_beta.ProtectedBetaTests.test_core_batch_logs_no_item_without_empty_post`

## Scope Controls

Negative local API checks:

```json
{
  "b1_level_denial": {
    "status": 403,
    "reason_code": "CONSUMER_LEVEL_NOT_ALLOWED"
  },
  "t11_theme_denial": {
    "status": 403,
    "reason_code": "CONSUMER_THEME_NOT_ALLOWED"
  }
}
```

This proves the consumer cannot use other CEFR levels or themes through the governed selection path.

## Telegram Delivery

Local payload/rendering checks:

- Telegram quiz poll payload validation is covered by `tests.test_telegram_shuffle`.
- Correct answer index is recomputed after shuffle before Bot API payload creation.
- Dry-run schedule did not call Telegram Bot API and did not post to the real channel.
- Public target reference in worker output is redacted as `***2505`.

External Telegram permission/posting proof:

- Not performed from this workspace.
- The real channel was not spammed during verification.
- Bot admin/posting permission for `-1002987612505` remains an operational deployment check.

## Suspend / Stop

Local stop proof:

```json
{
  "suspended_denial": {
    "status": 403,
    "reason_code": "CONSUMER_NOT_ACTIVE"
  }
}
```

Owner stop controls available:

- suspend consumer with `transition-consumer-status`;
- disable scheduler entry for this consumer/channel;
- revoke or rotate `CORE_DEUTSCH_IST_EINFACH_CHANNEL_API_KEY`;
- scheduled runner checks active consumer state before selection/send.

## Verification

- provisioning / migration check: `python3 -m py_compile src/quizbank_mvp/protected_beta.py src/quizbank_mvp/telegram_delivery.py tools/run_protected_beta_schedule.py tests/test_protected_beta.py`
- delivery smoke / dry-run: passed locally, no Telegram API call
- scheduler config check: covered by `test_core_channel_seed_and_schedule_are_scoped_to_a2_t01_t04` and `test_core_channel_due_slots_use_berlin_1207_time`
- idempotency tests: passed
- no duplicate protection proof: passed by retry tests above
- no secrets exposed: raw credential values are not included in this report
- targeted test command passed: `python3 -m unittest tests.test_protected_beta tests.test_telegram_shuffle tests.test_style_numeric_limits -v`
- no-secrets scan passed: `python3 tools/no_secrets_scan.py`
- full unittest discovery was run and did not fully pass because `test_generated_readme_is_current` expects the generated `QuizBank/README.md` date to match the current generation date; `QuizBank/README.md` is a protected generated artifact and was not edited for this task.

## What Remains Not Done / Risks

- VPS deployment was not touched from this workspace.
- Real Telegram Bot API permission/posting proof for channel `-1002987612505` was not executed.
- Runtime health/ready check and post-enable logs were not checked because the VPS/live scheduler was not changed here.
- First live run is therefore configured in code, but not proven as deployed/enabled on the VPS.
- Full repository unittest discovery remains blocked by the generated `QuizBank/README.md` current-date invariant outside this task scope.
