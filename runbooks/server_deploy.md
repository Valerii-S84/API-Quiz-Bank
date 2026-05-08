# API Quiz Bank Server Deploy Runbook

Status: VPS local-only pilot runtime record.

## Scope

This runbook records the current isolated VPS deployment for API Quiz Bank.
It does not define public exposure, Caddy routing, bot integration or production launch.

## Current VPS Runtime

| Field | Value |
|---|---|
| Mode | local-only pilot runtime |
| Repository path | `/opt/api-quiz-bank` |
| Data path | `/var/lib/api-quiz-bank` |
| Backup path | `/var/backups/api-quiz-bank` |
| API bind | `127.0.0.1:8010` |
| Public access | disabled |
| Caddy | not connected |
| Container | `api-quiz-bank-pilot` |
| Current deployed HEAD | `61e32d7` |

## Boundaries

- Do not expose the API on a public interface.
- Do not connect this service to Caddy until a separate public-access slice is approved.
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
