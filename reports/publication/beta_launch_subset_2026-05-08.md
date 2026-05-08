# Beta Launch Subset Publication Gate

Date: 2026-05-08

Scope: controlled local subset only.

## Selected Subset

| Source | Status | Delivery eligibility |
|---|---|---|
| `tests/fixtures/selection/approved_traceable_items.jsonl` | approved/published in tests | eligible |
| `data/imports/control_sample_items.jsonl` | draft in negative test | not eligible |
| Full private `QuizBank/` corpus | not imported for beta delivery | not eligible |

## Gate

Normal delivery must select only `approved` or `published` items. Draft,
blocked and retired status paths are covered by runtime tests and return
`SELECTION_NO_ELIGIBLE_ITEM`.

## Limitation

The full private corpus was not changed or republished. This record defines the
controlled local launch subset; it is not an external content launch approval.
