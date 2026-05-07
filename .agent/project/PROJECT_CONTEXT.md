# PROJECT_CONTEXT

Заповни цей файл перед початком роботи агента.

Якщо обов'язкові поля лишаються незаповненими, агент має
зупинитися до початку будь-якої задачі.

## 1. Stack

- Project name: `API Quiz Bank` (internal historical names: `QuizBank`, `German QuizBank Platform`)
- Primary languages: `Markdown` documentation and `CSV` corpus data in the current snapshot; target implementation stack is documented around `Python 3.12+`, `OpenAPI` and `PostgreSQL`
- Runtime / platform: `Current snapshot is a documentation-and-data repository without committed runnable services; target platform is an API-first quiz platform with versioned HTTP API, workers and Telegram integration`
- Main frameworks / libraries: `No committed runtime framework in the current snapshot; target architecture documents FastAPI or equivalent ASGI framework, JSON Schema/OpenAPI contracts and PostgreSQL-backed services`
- Data stores: `Current source assets are top-level CSV files under QuizBank/; target operational source of truth is PostgreSQL after controlled import`
- Default user-facing language: `Ukrainian for documentation and operator-facing text, with canonical technical terms in English; quiz content itself is German`

## 2. Project structure

- Root entrypoints: `CONSTITUTION.md`, `.agent/`, `docs/`, `QuizBank/`, `policies/`, `runbooks/`, `reports/`, `data/`
- Source directories: `QuizBank/` for source corpus assets, `QuizBank/staging/` for staged source work, `docs/` for normative project documents, `policies/` and `runbooks/` for operational policy/workflow baselines, `reports/compliance/` for compliance evidence registers, `data/governance/` for governance CSV registers, `.agent/` for agent governance`
- Test directories: `No committed tests/ directory in the current snapshot; target repository shape in the docs reserves tests/ for unit, integration, contract, data-quality and security checks`
- Config / infra directories: `No committed runtime config/infra directories in the current snapshot; data/governance/ exists for governance registers, while docs reserve future runtime paths such as api/, services/, infra/, tools/ and tests/`
- Read-only or protected paths: `.agent/core/` as normative agent rules, `CONSTITUTION.md` as project source of truth, `QuizBank/README.md` as generated inventory snapshot, raw corpus files in `QuizBank/*.csv` unless the task explicitly targets corpus changes`

## 3. Key commands

| Purpose | Command | Notes |
|---|---|---|
| Test | `python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank` | Documented corpus validation command from `QuizBank/README.md`; referenced tooling is not committed in this snapshot |
| Lint | `Not defined in current snapshot.` | No committed generic linter or style-check pipeline exists yet |
| Build | `Not defined in current snapshot.` | No buildable API/service implementation is committed yet |
| Dev / Run | `Not defined in current snapshot.` | Target runtime is documented, but runnable services are not present in the repository snapshot |

## 4. External dependencies

| System / service | Purpose | Access mode | Notes |
|---|---|---|---|
| `Telegram Bot API` | Planned quiz/poll delivery consumer | Planned external integration; not configured in current snapshot | Telegram is an adapter/consumer and must not own selection logic |
| `PostgreSQL` | Planned canonical operational data store | Planned runtime dependency; not configured in current snapshot | Raw CSV remains source asset, PostgreSQL is the intended operational truth after import |
| `GitHub / GitHub Actions or equivalent` | Planned repository governance, CI and protected-branch workflow | Planned hosting/integration; current workspace is not initialized as a git repository | Docs repeatedly require PR/check discipline for production-relevant changes |

## 5. Project constraints

- Protected paths: `.agent/core/`, `CONSTITUTION.md`, generated `QuizBank/README.md`, and raw source corpus under `QuizBank/*.csv` unless the task explicitly requests corpus edits
- Secrets / credentials locations: `No secret files are committed in the current snapshot; future bot tokens, API credentials, database credentials and `.env*` files must be treated as sensitive and never printed or copied into responses`
- Deploy / production boundaries: `No production environment is configured in this repository snapshot; any future deploy, infra, CI/CD, runtime secret wiring, Telegram delivery or production database operation is outside normal safe edit scope unless explicitly requested`
- Approval-required operations: `Corpus-wide CSV edits, edits to generated inventory outputs, dependency changes, CI/infra changes, destructive file operations, git push/history rewrites, and any real external-service or credential wiring`
- Restricted hosts / environments: `Any future production/staging database, Telegram Bot API environment, billing provider, external client environment or unmanaged host outside the local workspace`
- Project-specific forbidden actions: `Do not let websites, bots, apps or API clients read raw CSV directly; do not bypass import/validation/status workflow; do not expose draft/blocked items as deliverable content; do not manually edit generated inventory artifacts as if they were source data`

## 6. Git settings

- Default / protected branch: `main` (per Constitution/docs governance target; current workspace is not initialized as a git repository)`
- Branching strategy: `Use short-lived task/feature branches and merge to main only through PR or equivalent approved change path for production-relevant work`
- Merge strategy: `No direct pushes to main; merge only through reviewed PR or equivalent approved change path with the repository host's configured method`
- PR title format: `Conventional Commits style: type(scope): summary`
- PR requirements: `Relevant checks for changed scope, human review for production-relevant changes, no bypass of protected-branch discipline, and changelog or release-note update when API/schema/import/publication behavior changes`
