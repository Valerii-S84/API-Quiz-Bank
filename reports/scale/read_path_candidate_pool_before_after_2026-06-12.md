# Read Path Candidate Pool Before/After - 2026-06-12

## Scope

Candidate pool and delivery-history metric changes for
`POST /v1/quiz-items/next`.

## Before / After

| Area | Before | After |
|---|---:|---:|
| candidate pool limit | `300` | `150` |
| history metric candidates | all bounded candidates | `24` weighted shortlist |
| item delivery grouped metrics | yes | yes, shortlist only |
| cell delivery grouped metrics | yes | no synchronous hot-path query |
| repeat anti-join | enabled | enabled |
| quota enforcement | enabled | enabled |
| selection decision candidate count | bounded pool count | bounded pool count |

## Local Evidence

`reports/scale/read_path_perf_after_fix_2026-06-12.json` records the after
state on a synthetic 30k-item SQLite runtime:

| Metric | Result |
|---|---:|
| sequential requests | `100` |
| statuses | `{"200": 100}` |
| p95 | `134.965 ms` |
| candidate max | `150` |
| query count per success | `8` |
| exceptions/timeouts | `0/0` |

## Quality Boundary

Hard eligibility, entitlement, repeat and quota rules are unchanged. The
removed cell-level history aggregate was a soft scoring factor only. Item-level
delivery count and freshness remain available for the weighted shortlist, and
target mix, quality and deterministic jitter still participate in scoring.

## Non-Claims

This is not a production or PostgreSQL scale proof. Production deploy and
production load test were explicitly out of scope.
