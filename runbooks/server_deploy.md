# API Quiz Bank Server Deploy Runbook

Status: VPS local-only pilot runtime record.

## Scope

This runbook records the current VPS deployment for API Quiz Bank.
It defines the protected `api.valerchik.de` Caddy route and does not define bot
integration, public beta or production launch.

## Current VPS Runtime

| Field | Value |
|---|---|
| Mode | local-only pilot runtime |
| Repository path | `/opt/api-quiz-bank` |
| Data path | `/var/lib/api-quiz-bank` |
| Backup path | `/var/backups/api-quiz-bank` |
| API bind | `127.0.0.1:8010` |
| Public access | disabled |
| Caddy | `api.valerchik.de` connected with `X-API-Key` gate |
| Container | `api-quiz-bank-pilot` |
| Current checkout HEAD | `a86d625` |
| Runtime image state | recreated during public-route network update on 2026-05-08 |

## Boundaries

- Do not expose the API on a public interface without the `X-API-Key` gate.
- Do not remove or weaken the Caddy `X-API-Key` gate without a separate approved
  security slice.
- Do not reuse `.env` files from other projects.
- Do not modify `/opt/quiz-arena`.
- Do not modify `/opt/it-quiz-bot`.
- Do not move private `QuizBank/` corpus files through GitHub.

## Deploy / Update Command

Run only inside `/opt/api-quiz-bank`:

```bash
git fetch origin main
git checkout main
git pull --ff-only origin main
docker compose -f docker-compose.api-quiz-bank.yml up --build -d
```

## Checkout-Only Sync Evidence

Date: 2026-05-08.

Scope: align `/opt/api-quiz-bank` checkout with GitHub `main` without
restarting `api-quiz-bank-pilot`.

Commands executed inside `/opt/api-quiz-bank`:

```bash
git fetch origin main
git checkout main
git pull --ff-only origin main
```

Evidence:

| Check | Result |
|---|---|
| HEAD before sync | `61e32d7362203d9b765d5fe89a09930f585f3758` |
| HEAD after sync | `a86d6251148adbb574067ca68d429a531c0f8380` |
| `origin/main` after sync | `a86d6251148adbb574067ca68d429a531c0f8380` |
| Container started at before/after | `2026-05-08T07:46:48.873758412Z` |
| Container restart count before/after/final | `0` |
| Container state before/after/final | `running/healthy` |
| Port bind before/after/final | `127.0.0.1:8010` |

Full evidence is recorded in
`reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md`.

## Protected Public Route Evidence

Date: 2026-05-08.

Scope: expose API Quiz Bank through Caddy at `api.valerchik.de` with mandatory
`X-API-Key`.

Evidence:

| Check | Result |
|---|---|
| Public host | `api.valerchik.de` |
| Public no-key health | `401 Unauthorized` |
| Public authorized health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Public authorized ready | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |
| Public no-key delivery request | `401 Unauthorized` |
| Public authorized entitlement control | `403 ENTITLEMENT_MISSING_FEATURE` |
| API key storage | `/root/api-quiz-bank/public-api-key` on VPS, mode `600` |
| App credential storage | `/root/api-quiz-bank/app-consumer-api-key` on VPS, mode `600` |
| API host bind | `127.0.0.1:8010` remains present |

Full evidence is recorded in
`reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md`.

## App-Level Credential Header

The protected public route keeps the edge Caddy gate on `X-API-Key`.
The application-level consumer credential uses `X-QuizBank-API-Key`.
This prevents the edge key and consumer credential from sharing the same header
before broader beta traffic.

## Telegram Token Secret Wiring

One controlled direct Bot API send has succeeded as separate evidence, but that
was not the runtime worker path. Deployed worker real-send remains disabled
until an explicit controlled-send execution through the worker. The server-side
token is stored outside Git and exposed to the container only as a file path:

| Field | Value |
|---|---|
| VPS secret path | `/root/api-quiz-bank/telegram-bot-token` |
| Container secret path | `/run/secrets/api_quiz_bank_telegram_bot_token` |
| Env references | `QUIZBANK_TELEGRAM_BOT_TOKEN_FILE`, `TELEGRAM_BOT_TOKEN_FILE` |
| Compose override | `/opt/api-quiz-bank/docker-compose.api-quiz-bank.secrets.yml` |
| Git policy | secret file and server override are not committed |
| Current send status | token wired; direct controlled send succeeded; deployed worker real-send succeeded for Public MVP / Protected Beta |

Expected permission check:

```bash
stat -c '%a %U:%G %n' /root/api-quiz-bank/telegram-bot-token
```

Expected mode:

```text
600 root:root /root/api-quiz-bank/telegram-bot-token
```

Secret wiring evidence is recorded in
`reports/pre_pilot/telegram_secret_wiring_2026-05-08.md`.

## Public MVP / Protected Beta Telegram Worker Evidence

Date: 2026-05-08.

Scope: one controlled deployed worker real-send through the runtime path.
Secret values and Telegram target id were not printed or committed.

Evidence:

| Check | Result |
|---|---|
| Worker mode | `real` |
| Selection path | `src/quizbank_mvp/telegram_delivery.py` -> core selection |
| Delivery id | `deliv_b888a8c3b50c4c87` |
| Quiz item id | `approved_traceable_001` |
| Telegram target | `***8132` |
| Telegram message id | `271` |
| Telegram poll id | present, redacted |
| Delivery status | `sent` |
| Telegram result status | `sent` |

Full evidence is recorded in
`reports/beta/closed_external_pilot_smoke_2026-05-08.md`.

## Protected Beta Systemd Runtime Templates

The protected beta Telegram service, timer and runtime-user drop-in are tracked
under `deploy/systemd/`:

- `deploy/systemd/api-quiz-bank-protected-beta-telegram.service`
- `deploy/systemd/api-quiz-bank-protected-beta-telegram.timer`
- `deploy/systemd/api-quiz-bank-protected-beta-telegram.service.d/10-runtime-user-and-assets.conf`

The drop-in creates `/var/lib/api-quiz-bank/app-var/visual-assets` with owner
`65532:65532` and mode `0750`, then runs the scheduler inside the container as
UID/GID `65532:65532`. Do not replace this with `chmod 777`.

Install or refresh the unit files from `/opt/api-quiz-bank`:

```bash
install -m 0644 deploy/systemd/api-quiz-bank-protected-beta-telegram.service \
  /etc/systemd/system/api-quiz-bank-protected-beta-telegram.service
install -m 0644 deploy/systemd/api-quiz-bank-protected-beta-telegram.timer \
  /etc/systemd/system/api-quiz-bank-protected-beta-telegram.timer
install -d -m 0755 \
  /etc/systemd/system/api-quiz-bank-protected-beta-telegram.service.d
install -m 0644 \
  deploy/systemd/api-quiz-bank-protected-beta-telegram.service.d/10-runtime-user-and-assets.conf \
  /etc/systemd/system/api-quiz-bank-protected-beta-telegram.service.d/10-runtime-user-and-assets.conf
systemctl daemon-reload
systemctl enable --now api-quiz-bank-protected-beta-telegram.timer
```

Recovery dry-runs must use `tools/recover_protected_beta_schedule.py` with
`--mode dry_run --dry-run --no-duplicate-send`; this path is safe for checking
that already-sent T01/T04 slots return `already_sent_noop` without a new
Telegram send.

## Health Checks

```bash
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/ready
./scripts/api_quiz_bank_smoke.sh
./scripts/api_quiz_bank_backup.sh
./scripts/api_quiz_bank_restore_drill.sh
docker inspect -f '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' api-quiz-bank-pilot
docker port api-quiz-bank-pilot 8000/tcp
```

Expected port output:

```text
127.0.0.1:8010
```

## CI Boundary

GitHub Actions must not require private `QuizBank/` files. Public CI uses the
small fixture bank in `tests/fixtures/quizbank_public_smoke/`.

Public CI tests are limited to committed public fixtures and runtime checks that
do not need the private corpus:

```bash
python3 -m pip install -e ".[dev]"
python3 -m unittest \
  tests.test_contract_schema_invariants \
  tests.test_import_validation \
  tests.test_mvp_runtime \
  tests.test_pre_pilot_runtime_invariants \
  tests.test_style_numeric_limits
```

Full corpus checks remain local-only:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank
```
