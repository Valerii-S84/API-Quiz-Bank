# Core Deutsch ist einfach! VPS Delivery Evidence

Date: 2026-05-13

Scope: Controlled Protected Beta / controlled channel delivery only.

- Broad public launch: no.
- Public signup: no.
- Commercial launch: no.
- Raw secrets exposed in this report: no.

## Deploy

- deployed commit: `502be57`
- deployed branch on VPS: `deploy/core-deutsch-channel-final`
- predecessor delivery commit: `bcf708f`
- timezone deploy fix: `fb0240a`
- VPS path: `/opt/api-quiz-bank`
- container: `api-quiz-bank-pilot`

Pre-deploy backup:

- result: `postgres-backup-ok`
- backup path: `/var/backups/api-quiz-bank/api_quiz_bank_pg_20260513T164929Z.dump`

Pre/post deploy health:

- API `/health`: `200`, `{"status":"ok","service":"api-quiz-bank","version":"0.1.0"}`
- API `/ready`: `200`, database check `ok`
- API container: `running/healthy`, restart count `0`
- PostgreSQL container: `running/healthy`, restart count `0`
- PostgreSQL backup timer: `active`
- production monitor: `production-monitor-snapshot-ok /var/log/api-quiz-bank/monitoring/production_monitor_20260513T165937Z.md`

## Migration

- migration file: `database/postgresql/006_add_scheduled_delivery_slots.sql`
- result: `scheduled_delivery_slots` exists in PostgreSQL
- current core scheduled slot rows before first scheduled run: `0`

## Consumer Config

- consumer: `core_deutsch_ist_einfach_channel`
- channel id: `-1002987612505`
- status: `active`
- entitlement: `quiz_delivery` / `active`
- active hashed credential count: `1`
- CEFR scope: `["A2"]`
- theme scope: `["T01", "T04"]`
- quota: `2/day`

Post-deploy DB proof:

```text
core_deutsch_ist_einfach_channel|active|["A2"]|["T01", "T04"]|2|quiz_delivery|active|1
```

## Schedule

- systemd timer: `api-quiz-bank-core-deutsch-channel.timer`
- status: `active`
- service: `api-quiz-bank-core-deutsch-channel.service`
- command: `tools/run_protected_beta_schedule.py --mode real --approve-real-send --token-file /run/secrets/api_quiz_bank_telegram_bot_token --slot-time 12:07`
- schedule: daily `12:07 Europe/Berlin`
- no backfill: `Persistent=false`
- next trigger: `Thu 2026-05-14 10:07:00 UTC` = `2026-05-14 12:07 Europe/Berlin`
- slot 1: `core_deutsch_ist_einfach_channel:T01:12_07`, `A2`, `T01`
- slot 2: `core_deutsch_ist_einfach_channel:T04:12_07`, `A2`, `T04`

## Telegram Permission

No-send Telegram API permission proof:

```json
{
  "bot_id_present": true,
  "can_post_messages": true,
  "chat_id": "-1002987612505",
  "member_status": "administrator",
  "permission_ok": true
}
```

No debug/test garbage was sent to the main channel.

## Live Delivery

Live delivery proof is pending until the first permitted scheduled run:

- first permitted real run: `2026-05-14 12:07 Europe/Berlin`
- forced real-send on 2026-05-13: not performed
- reason: forcing a real send after deployment would violate the requirement that the first real run be the next scheduled `12:07 Europe/Berlin`

Current scheduled ledger proof:

```text
scheduled_delivery_slots rows for core_deutsch_ist_einfach_channel: 0
```

## T01 / T04 Proof

Configured live batch contains exactly two slots:

- first slot: `A2` / `T01`
- second slot: `A2` / `T04`

Live post-level proof remains pending until `2026-05-14 12:07 Europe/Berlin`.

## Duplicate Protection

Implemented ledger key:

- `consumer_id`
- `channel_id`
- `delivery_date`
- `slot_id`
- `theme_id`
- `cefr_level`

Local automated proof passed:

- sent slot retry does not call Telegram again
- if one slot fails, retry sends only failed slot
- `no_item` records state without sending an empty/broken Telegram payload

Relevant tests passed:

```text
python3 -m unittest tests.test_protected_beta tests.test_telegram_shuffle tests.test_style_numeric_limits -v
python3 -m unittest tests.test_mvp_coverage_branches tests.test_protected_beta tests.test_style_numeric_limits -v
```

## Quota Proof

- configured quota: `2/day`
- DB consumer quota: `2`
- scheduled quota for first real run: pending
- operational side effect: one ordinary API selection proof attempt created a non-Telegram delivery record on `2026-05-13`, before the corrected suspend proof command was rerun
- affected row: `deliv_93a912380d6a454a|created|A2|T01`
- scheduled slot ledger rows remain `0`; no Telegram send occurred
- quota row after side effect: `quiz_delivery|2026-05-13|1|2`
- this does not backfill or post to Telegram; it should not affect the next scheduled run on `2026-05-14`

## Suspend / Stop

Suspend proof:

```json
{
  "delivery_count_after": 1,
  "delivery_count_before": 1,
  "reason_code": "CONSUMER_NOT_ACTIVE",
  "suspended_request_status": 403
}
```

Stop controls:

- `systemctl disable --now api-quiz-bank-core-deutsch-channel.timer`
- transition consumer to `suspended`
- revoke/rotate `/root/api-quiz-bank/core-deutsch-ist-einfach-channel-api-key`

Consumer was reactivated after the suspend proof:

```text
active|1
```

## Logs

Post-deploy API logs show startup and health/ready requests only; no delivery errors were present in the checked window.

Core channel delivery log:

- not created yet, because the timer has not fired

## Full Test Issue

The earlier full test failure was investigated:

- original issue: `QuizBank/README.md` generated snapshot date invariant
- direct check now passes: `python3 -m unittest tests.test_generated_artifacts_invariants.GeneratedArtifactsInvariantTests.test_generated_readme_is_current -v`
- a later full discovery run exposed a separate regression caused by mandatory credential env in `seed-protected-beta`; fixed in commit `502be57`
- final full discovery passed: `python3 -m unittest discover -s tests -p "test_*.py"` ran 147 tests in 104.467s, `OK`
- no-secrets scan passed: `python3 tools/no_secrets_scan.py`

## What Remains Not Done

- Live scheduled Telegram delivery has not happened yet.
- Post-run proof for exactly 2 sent quizzes, T01/T04 sent status, slot ledger `sent`, live quota consumption, and delivery log status remains pending until after `2026-05-14 12:07 Europe/Berlin`.
