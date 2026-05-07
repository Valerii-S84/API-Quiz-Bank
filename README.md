# API Quiz Bank

API Quiz Bank is a governed documentation-and-data repository for a German quiz corpus and the platform rules around it.

The project is not a raw CSV delivery layer. Raw CSV files under `QuizBank/` are source assets. Product delivery must go through controlled import, canonical data, status gates, selection rules, API contracts, access control and delivery logging.

## Current Snapshot

- Active source bank files: `115`
- Active rows/items: `30,974`
- Active item status in the current corpus: `draft`
- Generated corpus report: `QuizBank/README.md`
- Project law: `CONSTITUTION.md`
- Agent rules: `.agent/AGENTS.md`

## Repository Map

- `.agent/` — agent governance rules.
- `docs/` — normative product, data, API, security, QA and operations documents.
- `QuizBank/` — source CSV corpus and generated corpus README.
- `data/manifests/` — generated source inventory, checksums and import manifest.
- `data/parser_profiles/` — parser profile seed for current CSV corpus.
- `data/imports/` — canonical sample JSONL output from local dry-run imports.
- `data/registry/` — MVP source registry seed for controlled import evidence.
- `data/taxonomy/` — taxonomy seed files derived from the current corpus.
- `schemas/` — seed JSON Schema artifacts.
- `api/` — seed OpenAPI contract.
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
python3 -m unittest discover -s tests -p "test_*.py"
```

## Rules

- Do not edit `QuizBank/README.md` manually; regenerate it with `python3 tools/quizbank_readme.py`.
- Do not expose raw CSV as public product content.
- Do not treat `draft`, `blocked`, `retired`, `needs_review`, `imported`, `normalized` or `monitored` items as normal-delivery eligible.
- Do not wire real secrets, production hosts, billing providers or Telegram delivery without explicit review and approval.
- The repository is private/all-rights-reserved unless `LICENSE` and `policies/license_policy.md` are explicitly changed through approved review.
