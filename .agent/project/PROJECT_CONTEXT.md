# PROJECT_CONTEXT

Заповни цей файл перед початком роботи агента.

Якщо обов'язкові поля лишаються незаповненими, агент має
зупинитися до початку будь-якої задачі.

## 1. Stack

- Project name: `API Quiz Bank` (internal historical names: `QuizBank`, `German QuizBank Platform`)
- Primary languages: `Markdown` documentation, `CSV` corpus/governance data, `Python 3.12+` local tooling/tests, `YAML` OpenAPI/manifest/profile seeds and `JSON Schema`
- Runtime / platform: `Current snapshot is a documentation-and-data repository with committed local validation/generation tooling plus a modular FastAPI runtime under src/quizbank_mvp/; database, selection, Telegram delivery and protected channel configuration are split into focused modules with compatibility orchestration/facade entrypoints; the owner-operated VPS runtime for this repository is under /opt/api-quiz-bank only, uses containers api-quiz-bank-pilot and api-quiz-bank-postgres, binds API to 127.0.0.1:8010 and exposes the protected public route https://api.valerchik.de behind the mandatory X-API-Key edge gate; runtime corpus delivery is PostgreSQL-backed in the protected API environment; this does not approve broad public launch, unauthenticated API access, school deployment, paid launch or legal/privacy expansion; target platform remains an API-first quiz platform with versioned HTTP API, workers and Telegram integration`
- Main frameworks / libraries: `Python standard-library tooling and unittest are committed; MVP runtime uses FastAPI, Pydantic, Uvicorn and SQLite; tests use unittest plus FastAPI TestClient/httpx; target production architecture still documents FastAPI or equivalent ASGI framework, JSON Schema/OpenAPI contracts and PostgreSQL-backed services`
- Data stores: `Current source assets are top-level CSV files under QuizBank/; MVP runtime uses local SQLite via database/migrations/001_create_mvp_runtime.sql; database/postgresql/ holds the production-oriented PostgreSQL schema contract and mirror migrations; target operational source of truth is PostgreSQL or an equivalent governed DB model after controlled import`
- Default user-facing language: `Ukrainian for documentation and operator-facing text, with canonical technical terms in English; quiz content itself is German`

## 2. Project structure

- Root entrypoints: `README.md`, `CONSTITUTION.md`, `.agent/`, `docs/`, `QuizBank/`, `tools/`, `tests/`, `api/`, `schemas/`, `data/`, `policies/`, `runbooks/`, `reports/`, `.github/`
- Source directories: `QuizBank/` for source corpus assets, `QuizBank/staging/` for staged source work, `tools/` for local validation/generation tooling, `src/quizbank_mvp/` for the FastAPI/SQLite MVP runtime, `database/migrations/` for MVP SQLite schema migrations, `database/postgresql/` for the PostgreSQL runtime contract, `api/` for OpenAPI seed, `schemas/` for JSON Schema seed, `docs/` for normative project documents, `policies/` and `runbooks/` for operational policy/workflow baselines, `reports/compliance/` for compliance evidence registers, `data/` for manifests, parser profiles, taxonomy, governance CSV registers and runtime seed config, `.agent/` for agent governance`
- Test directories: `tests/` for repository invariant and MVP runtime tests using Python unittest`
- Config / infra directories: `.github/workflows/` for public CI that must not require private QuizBank corpus files; `pyproject.toml` for the local Python package/runtime dependency seed; `Dockerfile` and `docker-compose.api-quiz-bank.yml` for the isolated local-only Docker pilot runtime; `runbooks/server_deploy.md` records the current VPS local-only deployment; docs reserve future runtime paths such as services/ and infra/`
- Read-only or protected paths: `.agent/core/` as normative agent rules, `CONSTITUTION.md` as project source of truth, `QuizBank/README.md` as generated inventory snapshot, raw corpus files in `QuizBank/*.csv` unless the task explicitly targets corpus changes`

## 3. Key commands

| Purpose | Command | Notes |
|---|---|---|
| Test | `python3 -m unittest discover -s tests -p "test_*.py"` | Runs full local repository invariant tests; requires private `QuizBank/` when corpus-dependent tests are included |
| No-secrets scan | `python3 tools/no_secrets_scan.py` | Mirrors the committed CI secret-pattern gate |
| Public CI tests | `python3 -m pip install -e ".[dev]" && python3 -m unittest tests.test_contract_schema_invariants tests.test_import_cycle_guard tests.test_import_validation tests.test_mvp_runtime tests.test_mvp_rate_limit tests.test_pre_pilot_runtime_invariants tests.test_database_operations_backup tests.test_legal_privacy_gate tests.test_production_monitor_snapshot tests.test_production_security_hardening tests.test_release_governance_gate tests.test_scale_load_gate tests.test_style_numeric_limits` | Installs declared runtime test dependencies, then runs committed public tests that do not require private `QuizBank/` files |
| Public CI corpus fixture validation | `python3 tools/quizbank_constitution_check.py --quizbank-dir tests/fixtures/quizbank_public_smoke` | Validates a committed public fixture bank without requiring private corpus files |
| Public CI corpus fixture inventory | `python3 tools/quizbank_inventory.py --quizbank-dir tests/fixtures/quizbank_public_smoke` | Exercises inventory tooling in GitHub Actions without private corpus files |
| Private corpus validation | `python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank` | Local-only validation of the private corpus baseline and constitutional invariants |
| Private inventory generation | `python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts` | Local-only regeneration of manifest, inventory, checksums and parser profile artifacts |
| Contract seed generation | `python3 tools/quizbank_emit_standards.py` | Regenerates taxonomy, JSON Schema and OpenAPI seed artifacts |
| MVP demo | `PYTHONPATH=src python3 tools/run_mvp_demo.py` | Exercises local SQLite/FastAPI app in-process through TestClient |
| MVP init DB | `PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/quizbank_mvp.sqlite3 init-db` | Creates the local SQLite MVP schema |
| MVP seed demo | `PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/quizbank_mvp.sqlite3 seed-demo` | Seeds approved demo item, consumers, entitlement and quota controls |
| Dev / Run | `QUIZBANK_DB_PATH=var/quizbank_mvp.sqlite3 PYTHONPATH=src uvicorn quizbank_mvp.app:app --host 127.0.0.1 --port 8000` | Runs the local FastAPI MVP service after DB init/seed |
| Lint / import boundaries | `python3 -m unittest tests.test_import_cycle_guard tests.test_style_numeric_limits tests.test_database_backend_contract` | Committed dependency-free gates catch MVP runtime import cycles, numeric limit regressions, basic Python whitespace style issues and PostgreSQL boundary drift |
| Runtime coverage gate | `python3 -m coverage run -m unittest tests.test_database_backend_contract tests.test_mvp_admin tests.test_mvp_coverage_branches tests.test_mvp_projections tests.test_mvp_rate_limit tests.test_mvp_runtime tests.test_mvp_selection_contract tests.test_mvp_selection_decisions tests.test_mvp_selection_policy tests.test_mvp_weighted_selection tests.test_pre_pilot_runtime_invariants tests.test_protected_beta tests.test_telegram_shuffle tests.test_telegram_photo_gate_coverage tests.test_visual_access_gate_coverage tests.test_visual_cache tests.test_visual_prompt_builder tests.test_visual_provider tests.test_visual_qa tests.test_visual_runtime_gate_coverage tests.test_visual_settings tests.test_website_quiz_teaser_beta && python3 -m coverage report` | Mirrors the CI coverage gate; `pyproject.toml` currently requires at least 93% runtime coverage |
| Build | `python3 -m pip install -e ".[dev]"` | Installs the local package/runtime for development; no separate deploy build pipeline is committed |

## 4. External dependencies

| System / service | Purpose | Access mode | Notes |
|---|---|---|---|
| `Telegram Bot API` | Planned quiz/poll delivery consumer | Token secret is wired on the VPS as a root-only file and mounted by file path; one controlled direct Bot API send succeeded; local worker supports dry-run and explicitly approved real-send mode; one deployed worker real-send succeeded for Public MVP / Protected Beta | Telegram is an adapter/consumer and must not own selection logic; production Telegram monitoring and incident evidence remain separate |
| `FastAPI / Pydantic / Uvicorn` | Local MVP API runtime and request/response validation | Declared in `pyproject.toml`; installed in the local Python environment when running the API | Do not treat MVP service as production deployment |
| `SQLite` | Local MVP database for runtime proof and tests | Python stdlib sqlite3 with committed SQL migration | Equivalent DB model for MVP proof only; not the target production database |
| `PostgreSQL` | Planned canonical operational data store | `psycopg` is declared and a runtime adapter/schema contract are committed; no external PostgreSQL instance is configured in the current snapshot | Raw CSV remains source asset, PostgreSQL is the intended operational truth after import |
| `GitHub / GitHub Actions or equivalent` | Repository governance, public CI and protected-branch workflow | GitHub remote and Actions CI are configured; public CI uses committed fixtures and must not require private `QuizBank/` files | Docs repeatedly require PR/check discipline for production-relevant changes; full private corpus checks remain local-only |
| `VPS Docker runtime` | API Quiz Bank protected runtime with protected public route | Configured only at `/opt/api-quiz-bank`; API container is `api-quiz-bank-pilot`, PostgreSQL container is `api-quiz-bank-postgres`, backups are under `/var/backups/api-quiz-bank`, API binds to `127.0.0.1:8010`, and Caddy route `api.valerchik.de` requires `X-API-Key` | Protected API runtime is owner-operated and must remain closed behind the edge key; it is not broad public launch, unauthenticated API access, school deployment or paid launch |

## 5. Project constraints

- Protected paths: `.agent/core/`, `CONSTITUTION.md`, generated `QuizBank/README.md`, and raw source corpus under `QuizBank/*.csv` unless the task explicitly requests corpus edits
- Secrets / credentials locations: `No secret files are committed in the current snapshot; future bot tokens, API credentials, database credentials and `.env*` files must be treated as sensitive and never printed or copied into responses`
- Deploy / production boundaries: `The only approved VPS scope for this repository is /opt/api-quiz-bank and the named units/containers that belong to it: api-quiz-bank-pilot, api-quiz-bank-postgres, api-quiz-bank-protected-beta-telegram.*, api-quiz-bank-core-deutsch-channel.*, api-quiz-bank-production-monitor.*, api-quiz-bank-backup.*, api-quiz-bank-postgres-backup.*. Do not inspect, modify, restart, deploy or report on other /opt projects. Do not touch /opt/quiz-arena, /opt/it-quiz-bot or any unrelated service even read-only unless the user explicitly names that project in a separate task. Keep api.valerchik.de protected by X-API-Key; any weakening of the edge gate, secret wiring, database operation, Telegram real-send/backfill, scheduler change, consumer access change or production claim requires explicit task scope.`
- Approval-required operations: `Corpus-wide CSV edits, edits to generated inventory outputs, dependency changes, CI/infra changes, destructive file operations, git push/history rewrites, server deploy/recreate/restart, systemd timer or service changes, database writes, consumer/entitlement/quota/credential changes, real Telegram sends, backfills, secret wiring and any real external-service operation`
- Restricted hosts / environments: `The existing VPS runtime and Caddy route may be inspected only inside /opt/api-quiz-bank and only for this repository's named containers/units. Any other production/staging database, Telegram Bot API environment, billing provider, unauthenticated public route, external client environment, unmanaged host or unrelated VPS project remains restricted.`
- Project-specific forbidden actions: `Do not let websites, bots, apps or API clients read raw CSV directly; do not bypass import/validation/status workflow; do not expose draft/blocked items as deliverable content; do not manually edit generated inventory artifacts as if they were source data; do not create screenshots, visual assets, smoke reports, generated reports, extra evidence files or documentation extras unless directly requested; do not backfill missed Telegram schedule slots unless the user explicitly requests backfill.`

## 6. Git settings

- Default / protected branch: `main` (per Constitution/docs governance target; local Git repository initialized, remote protection not configured yet)
- Branching strategy: `Use short-lived task/feature branches and merge to main only through PR or equivalent approved change path for production-relevant work`
- Merge strategy: `No direct pushes to main; merge only through reviewed PR or equivalent approved change path with the repository host's configured method`
- PR title format: `Conventional Commits style: type(scope): summary`
- PR requirements: `Small scoped PRs only: one logical area per PR, unrelated refactors split out, relevant checks for changed scope, human review for production-relevant changes, no bypass of protected-branch discipline, and changelog or release-note update when API/schema/import/publication behavior changes`
