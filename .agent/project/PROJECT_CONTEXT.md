# PROJECT_CONTEXT

Заповни цей файл перед початком роботи агента.

Якщо обов'язкові поля лишаються незаповненими, агент має
зупинитися до початку будь-якої задачі.

## 1. Stack

- Project name: `API Quiz Bank` (internal historical names: `QuizBank`, `German QuizBank Platform`)
- Primary languages: `Markdown` documentation, `CSV` corpus/governance data, `Python 3.12+` local tooling/tests, `YAML` OpenAPI/manifest/profile seeds and `JSON Schema`
- Runtime / platform: `Current snapshot is a documentation-and-data repository with committed local validation/generation tooling plus a FastAPI/SQLite MVP runtime under src/quizbank_mvp/; a local Telegram worker MVP path exists under src/quizbank_mvp/telegram_delivery.py and tools/run_telegram_delivery_smoke.py; a VPS Docker deploy is configured and running under /opt/api-quiz-bank with host bind 127.0.0.1:8010 and protected public Caddy route https://api.valerchik.de gated by X-API-Key; deployed Telegram worker real-send evidence for Public MVP / Protected Beta is recorded in reports/beta/closed_external_pilot_smoke_2026-05-08.md; target platform remains an API-first quiz platform with versioned HTTP API, workers and Telegram integration`
- Main frameworks / libraries: `Python standard-library tooling and unittest are committed; MVP runtime uses FastAPI, Pydantic, Uvicorn and SQLite; tests use unittest plus FastAPI TestClient/httpx; target production architecture still documents FastAPI or equivalent ASGI framework, JSON Schema/OpenAPI contracts and PostgreSQL-backed services`
- Data stores: `Current source assets are top-level CSV files under QuizBank/; MVP runtime uses local SQLite via database/migrations/001_create_mvp_runtime.sql; target operational source of truth is PostgreSQL or an equivalent governed DB model after controlled import`
- Default user-facing language: `Ukrainian for documentation and operator-facing text, with canonical technical terms in English; quiz content itself is German`

## 2. Project structure

- Root entrypoints: `README.md`, `CONSTITUTION.md`, `.agent/`, `docs/`, `QuizBank/`, `tools/`, `tests/`, `api/`, `schemas/`, `data/`, `policies/`, `runbooks/`, `reports/`, `.github/`
- Source directories: `QuizBank/` for source corpus assets, `QuizBank/staging/` for staged source work, `tools/` for local validation/generation tooling, `src/quizbank_mvp/` for the FastAPI/SQLite MVP runtime, `database/migrations/` for MVP SQLite schema migration, `api/` for OpenAPI seed, `schemas/` for JSON Schema seed, `docs/` for normative project documents, `policies/` and `runbooks/` for operational policy/workflow baselines, `reports/compliance/` for compliance evidence registers, `data/` for manifests, parser profiles, taxonomy and governance CSV registers, `.agent/` for agent governance`
- Test directories: `tests/` for repository invariant and MVP runtime tests using Python unittest`
- Config / infra directories: `.github/workflows/` for public CI that must not require private QuizBank corpus files; `pyproject.toml` for the local Python package/runtime dependency seed; `Dockerfile` and `docker-compose.api-quiz-bank.yml` for the isolated local-only Docker pilot runtime; `runbooks/server_deploy.md` records the current VPS local-only deployment; docs reserve future runtime paths such as services/ and infra/`
- Read-only or protected paths: `.agent/core/` as normative agent rules, `CONSTITUTION.md` as project source of truth, `QuizBank/README.md` as generated inventory snapshot, raw corpus files in `QuizBank/*.csv` unless the task explicitly targets corpus changes`

## 3. Key commands

| Purpose | Command | Notes |
|---|---|---|
| Test | `python3 -m unittest discover -s tests -p "test_*.py"` | Runs full local repository invariant tests; requires private `QuizBank/` when corpus-dependent tests are included |
| Public CI tests | `python3 -m pip install -e ".[dev]" && python3 -m unittest tests.test_contract_schema_invariants tests.test_import_validation tests.test_mvp_runtime tests.test_pre_pilot_runtime_invariants tests.test_style_numeric_limits` | Installs declared runtime test dependencies, then runs committed public tests that do not require private `QuizBank/` files |
| Public CI corpus fixture validation | `python3 tools/quizbank_constitution_check.py --quizbank-dir tests/fixtures/quizbank_public_smoke` | Validates a committed public fixture bank without requiring private corpus files |
| Public CI corpus fixture inventory | `python3 tools/quizbank_inventory.py --quizbank-dir tests/fixtures/quizbank_public_smoke` | Exercises inventory tooling in GitHub Actions without private corpus files |
| Private corpus validation | `python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank` | Local-only validation of the private corpus baseline and constitutional invariants |
| Private inventory generation | `python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts` | Local-only regeneration of manifest, inventory, checksums and parser profile artifacts |
| Contract seed generation | `python3 tools/quizbank_emit_standards.py` | Regenerates taxonomy, JSON Schema and OpenAPI seed artifacts |
| MVP demo | `PYTHONPATH=src python3 tools/run_mvp_demo.py` | Exercises local SQLite/FastAPI app in-process through TestClient |
| MVP init DB | `PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/quizbank_mvp.sqlite3 init-db` | Creates the local SQLite MVP schema |
| MVP seed demo | `PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/quizbank_mvp.sqlite3 seed-demo` | Seeds approved demo item, consumers, entitlement and quota controls |
| Dev / Run | `QUIZBANK_DB_PATH=var/quizbank_mvp.sqlite3 PYTHONPATH=src uvicorn quizbank_mvp.app:app --host 127.0.0.1 --port 8000` | Runs the local FastAPI MVP service after DB init/seed |
| Lint | `Not defined in current snapshot.` | No committed generic linter or style-check pipeline exists yet |
| Build | `python3 -m pip install -e ".[dev]"` | Installs the local package/runtime for development; no separate deploy build pipeline is committed |

## 4. External dependencies

| System / service | Purpose | Access mode | Notes |
|---|---|---|---|
| `Telegram Bot API` | Planned quiz/poll delivery consumer | Token secret is wired on the VPS as a root-only file and mounted by file path; one controlled direct Bot API send succeeded; local worker supports dry-run and explicitly approved real-send mode; one deployed worker real-send succeeded for Public MVP / Protected Beta | Telegram is an adapter/consumer and must not own selection logic; production Telegram monitoring and incident evidence remain separate |
| `FastAPI / Pydantic / Uvicorn` | Local MVP API runtime and request/response validation | Declared in `pyproject.toml`; installed in the local Python environment when running the API | Do not treat MVP service as production deployment |
| `SQLite` | Local MVP database for runtime proof and tests | Python stdlib sqlite3 with committed SQL migration | Equivalent DB model for MVP proof only; not the target production database |
| `PostgreSQL` | Planned canonical operational data store | Planned runtime dependency; not configured in current snapshot | Raw CSV remains source asset, PostgreSQL is the intended operational truth after import |
| `GitHub / GitHub Actions or equivalent` | Repository governance, public CI and protected-branch workflow | GitHub remote and Actions CI are configured; public CI uses committed fixtures and must not require private `QuizBank/` files | Docs repeatedly require PR/check discipline for production-relevant changes; full private corpus checks remain local-only |
| `VPS Docker runtime` | API Quiz Bank pilot runtime with protected public route | Configured at `/opt/api-quiz-bank` with local SQLite data under service `var/api-quiz-bank/`, backups in `/var/backups/api-quiz-bank`, API bound to `127.0.0.1:8010`, and Caddy route `api.valerchik.de` requiring `X-API-Key` | Public MVP / Protected Beta route and deployed worker real-send are smoke-proven; this is not a production deployment |

## 5. Project constraints

- Protected paths: `.agent/core/`, `CONSTITUTION.md`, generated `QuizBank/README.md`, and raw source corpus under `QuizBank/*.csv` unless the task explicitly requests corpus edits
- Secrets / credentials locations: `No secret files are committed in the current snapshot; future bot tokens, API credentials, database credentials and `.env*` files must be treated as sensitive and never printed or copied into responses`
- Deploy / production boundaries: `VPS Docker deploy is configured and running for the pilot runtime with protected Caddy route api.valerchik.de using X-API-Key; deployed Telegram worker real-send evidence is recorded for Public MVP / Protected Beta; any future weakening of the API-key gate, additional Telegram delivery on external targets, runtime secret wiring beyond this service, production database operation or production claim is outside normal safe edit scope unless explicitly requested`
- Approval-required operations: `Corpus-wide CSV edits, edits to generated inventory outputs, dependency changes, CI/infra changes, destructive file operations, git push/history rewrites, and any real external-service or credential wiring`
- Restricted hosts / environments: `The existing VPS runtime and Caddy route must be changed only through explicit deploy scope; any future production/staging database, Telegram Bot API environment, billing provider, unauthenticated public route, external client environment or unmanaged host outside the local workspace remains restricted`
- Project-specific forbidden actions: `Do not let websites, bots, apps or API clients read raw CSV directly; do not bypass import/validation/status workflow; do not expose draft/blocked items as deliverable content; do not manually edit generated inventory artifacts as if they were source data`

## 6. Git settings

- Default / protected branch: `main` (per Constitution/docs governance target; local Git repository initialized, remote protection not configured yet)
- Branching strategy: `Use short-lived task/feature branches and merge to main only through PR or equivalent approved change path for production-relevant work`
- Merge strategy: `No direct pushes to main; merge only through reviewed PR or equivalent approved change path with the repository host's configured method`
- PR title format: `Conventional Commits style: type(scope): summary`
- PR requirements: `Small scoped PRs only: one logical area per PR, unrelated refactors split out, relevant checks for changed scope, human review for production-relevant changes, no bypass of protected-branch discipline, and changelog or release-note update when API/schema/import/publication behavior changes`
