# Contributing

## Baseline Workflow

1. Read `CONSTITUTION.md` and `.agent/AGENTS.md` before changing governed files.
2. Keep changes scoped to the stated task.
3. Do not edit generated files manually.
4. Run relevant local checks before commit.
5. Use Conventional Commits.

## Local Checks

```bash
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank
python3 tools/quizbank_import_sample.py
python3 -m unittest discover -s tests -p "test_*.py"
```

## Generated Artifacts

- Regenerate `QuizBank/README.md` with `python3 tools/quizbank_readme.py`.
- Regenerate manifest/parser artifacts with `python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --write-artifacts`.
- Regenerate schema/taxonomy/API seed artifacts with `python3 tools/quizbank_emit_standards.py`.
- Regenerate the control import evidence with `python3 tools/quizbank_import_sample.py`.

## Protected Content

- Raw CSV files under `QuizBank/` are source assets.
- `QuizBank/README.md` is generated.
- `.agent/core/` contains normative agent rules.
- Real secrets and production wiring are out of scope unless explicitly approved.

## Review Expectations

Production-relevant changes should be reviewed before merge once a remote repository and branch protection are configured. Until then, local commits are only repository snapshots, not production releases.
