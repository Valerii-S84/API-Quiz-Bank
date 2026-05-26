# API Quiz Bank

API Quiz Bank is a governed documentation-and-data repository for a German quiz corpus and the platform rules around it.

The project is not a raw CSV delivery layer. Raw CSV files under `QuizBank/` are source assets. Product delivery must go through controlled import, canonical data, status gates, selection rules, API contracts, access control and delivery logging.

## Current Snapshot

- Active source bank files: `115`
- Active rows/items: `30,974`
- Active item status in the current corpus: `published`
- Generated corpus report: `QuizBank/README.md`
- Project law: `CONSTITUTION.md`
- Agent rules: `.agent/AGENTS.md`

## Repository Map

- `.agent/` — agent governance rules.
- `docs/` — normative product, data, API, security, QA and operations documents.
- `QuizBank/` — source CSV corpus and generated corpus README.
- `data/manifests/` — generated source inventory, checksums and import manifest.
- `data/config/` — runtime seed configuration, including protected beta channel schedules.
- `data/parser_profiles/` — parser profile seed for current CSV corpus.
- `data/imports/` — canonical sample JSONL output from local dry-run imports.
- `data/registry/` — MVP source registry seed for controlled import evidence.
- `data/taxonomy/` — taxonomy seed files derived from the current corpus.
- `schemas/` — seed JSON Schema artifacts.
- `api/` — seed OpenAPI contract.
- `database/migrations/` — SQLite MVP runtime schema migrations.
- `database/postgresql/` — production-oriented PostgreSQL schema contract and mirror migrations.
- `src/quizbank_mvp/` — FastAPI/SQLite MVP runtime with database, selection and Telegram delivery split into focused modules.
- `reports/imports/` — local dry-run import evidence artifacts.
- `reports/coverage/` — reproducible corpus coverage evidence.
- `reports/delivery/` — local selection/delivery smoke evidence.
- `tools/` — local corpus tooling.
- `tests/` — repository invariant tests.

## Local Checks

```bash
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank
python3 tools/quizbank_import_sample.py
python3 tools/quizbank_gap_map.py --quizbank-dir QuizBank --write-artifacts
python3 tools/quizbank_selection_smoke.py
python3 tools/no_secrets_scan.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m unittest tests.test_import_cycle_guard tests.test_style_numeric_limits tests.test_database_backend_contract
python3 -m coverage run -m unittest tests.test_database_backend_contract tests.test_mvp_admin tests.test_mvp_coverage_branches tests.test_mvp_projections tests.test_mvp_rate_limit tests.test_mvp_runtime tests.test_mvp_selection_contract tests.test_mvp_selection_decisions tests.test_mvp_selection_policy tests.test_mvp_weighted_selection tests.test_pre_pilot_runtime_invariants tests.test_protected_beta tests.test_telegram_shuffle tests.test_telegram_photo_gate_coverage tests.test_visual_access_gate_coverage tests.test_visual_cache tests.test_visual_prompt_builder tests.test_visual_provider tests.test_visual_qa tests.test_visual_runtime_gate_coverage tests.test_visual_settings tests.test_website_quiz_teaser_beta
python3 -m coverage report
```

## MVP Runtime

Install local runtime dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

Create and seed the local SQLite MVP database:

```bash
PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/quizbank_mvp.sqlite3 init-db
PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/quizbank_mvp.sqlite3 seed-demo
```

Run the API locally:

```bash
QUIZBANK_DB_PATH=var/quizbank_mvp.sqlite3 PYTHONPATH=src uvicorn quizbank_mvp.app:app --host 127.0.0.1 --port 8000
```

Exercise the MVP delivery flow:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl -X POST http://127.0.0.1:8000/v1/quiz-items/next \
  -H 'Content-Type: application/json' \
  -H 'X-Consumer-Id: consumer_demo' \
  -H 'X-QuizBank-API-Key: demo_consumer_api_key' \
  -d '{"consumer_id":"consumer_demo","cefr_level":"A2","theme_ids":["T10"]}'
PYTHONPATH=src python3 tools/run_mvp_demo.py
```

## Support and Security Intake

- Use GitHub issues for non-sensitive documentation, corpus, tooling and
  security-boundary changes through the committed issue templates.
- Use the support/abuse issue template for non-sensitive beta support,
  content-quality, abuse and access/quota reports.
- Do not place secrets, tokens, private identifiers or raw request/response
  dumps in public issues.
- Report sensitive security, privacy or abuse issues to the project owner
  through a private channel until a public disclosure contact is approved.

## Rules

- Do not edit `QuizBank/README.md` manually; regenerate it with `python3 tools/quizbank_readme.py`.
- Do not expose raw CSV as public product content.
- Do not treat `draft`, `blocked`, `retired`, `needs_review`, `imported`, `normalized` or `monitored` items as normal-delivery eligible.
- Do not wire real secrets, production hosts, billing providers or Telegram delivery without explicit review and approval.
- The repository is private/all-rights-reserved unless `LICENSE` and `policies/license_policy.md` are explicitly changed through approved review.
