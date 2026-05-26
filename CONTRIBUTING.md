# Contributing

## Baseline Workflow

1. Read `CONSTITUTION.md` and `.agent/AGENTS.md` before changing governed files.
2. Keep changes scoped to the stated task.
3. Do not edit generated files manually.
4. Run relevant local checks before commit.
5. Use Conventional Commits.

## Small PR Discipline

- Keep each PR limited to one logical area, such as docs/governance, database boundary, selection, Telegram delivery, protected beta config, tests, or tooling.
- Do not combine unrelated refactors, behavior changes, schema changes, dependency changes, CI changes, or production wiring in one PR.
- Split changes when reviewers would need to reason about unrelated runtime paths to approve the work.
- If a change must cross module boundaries, explain the coupling and run checks that cover every touched boundary.
- List intentionally changed files and commands run in the PR description.

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

## Generated Artifacts

- Regenerate `QuizBank/README.md` with `python3 tools/quizbank_readme.py`.
- Regenerate manifest/parser artifacts with `python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts`.
- Regenerate schema/taxonomy/API seed artifacts with `python3 tools/quizbank_emit_standards.py`.
- Regenerate the control import evidence and canonical JSONL sample with `python3 tools/quizbank_import_sample.py`.
- Regenerate the corpus coverage report with `python3 tools/quizbank_gap_map.py --quizbank-dir QuizBank --write-artifacts`.
- Regenerate the selection smoke evidence with `python3 tools/quizbank_selection_smoke.py`.
- Regenerate the approved-item delivery evidence with `python3 tools/quizbank_selection_smoke.py --canonical-input tests/fixtures/selection/approved_traceable_items.jsonl --report-out reports/delivery/control_approved_selection_report.json`.
- Regenerate the repeat-policy evidence with `python3 tools/quizbank_selection_smoke.py --canonical-input tests/fixtures/selection/approved_traceable_items.jsonl --delivery-history reports/delivery/control_approved_selection_report.json --report-out reports/delivery/control_repeat_policy_report.json`.

## Protected Content

- Raw CSV files under `QuizBank/` are source assets.
- `QuizBank/README.md` is generated.
- `.agent/core/` contains normative agent rules.
- Real secrets and production wiring are out of scope unless explicitly approved.

## Review Expectations

Production-relevant changes should be reviewed before merge once a remote repository and branch protection are configured. Until then, local commits are only repository snapshots, not production releases.
