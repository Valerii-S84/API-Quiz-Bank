# Closed External Pilot Smoke Evidence

Date: 2026-05-08

Scope: Public MVP / Protected Beta section 11 closed external pilot smoke for
`https://api.valerchik.de` plus controlled Telegram worker delivery. This is
not a production launch, broad public beta or unauthenticated access approval.

## Required Scenario

The required section 11 scenario is:

```text
authorized API delivery
  -> delivery log read
  -> Telegram worker real send through runtime path
  -> audit/report
  -> support/monitoring evidence
```

## Execution Result

| Check | Result |
|---|---|
| Public no-key health | `401 Unauthorized` |
| Public no-key delivery request | `401 Unauthorized` |
| SSH access for live VPS checks | `root@valerchik.de` succeeded |
| Runtime host | `ubuntu-8gb-nbg1-1` |
| Runtime branch/head | `main` / `aaad3b7` |
| Container | `api-quiz-bank-pilot` |
| Container state | `running/healthy` |
| Host bind | `127.0.0.1:8010` |
| Authorized health | `200`, body status `ok` |
| Authorized readiness | `200`, body status `ok` |
| Authorized next item | `200`, delivery id present |
| Authorized delivery read | `200`, delivery id matched |
| Repeat guard | `404 SELECTION_NO_ELIGIBLE_ITEM` |
| Quota guard | `429 QUOTA_EXCEEDED` |
| Suspended consumer guard | `403 CONSUMER_NOT_ACTIVE` |
| Runtime Telegram worker real send | `sent` |
| Delivery id | `deliv_b888a8c3b50c4c87` |
| Quiz item id | `approved_traceable_001` |
| Telegram target | `***8132` |
| Telegram message id | `271` |
| Telegram poll id | present, redacted |
| DB delivery status | `sent` |
| DB Telegram result status | `sent` |
| Failure reason | `null` |

## Evidence Boundary

Existing evidence proves these related but insufficient pieces:

- protected public route smoke exists in
  `reports/beta/edge_app_header_split_smoke_2026-05-08.md`;
- direct controlled Telegram Bot API send succeeded in
  `reports/pre_pilot/telegram_controlled_send_2026-05-08.md`;
- local worker path creates a delivery id and records `sent`, `failed` or
  `skipped` in `src/quizbank_mvp/telegram_delivery.py` and
  `tests/test_mvp_runtime.py`;
- owner-reviewed support, monitoring, backup/restore and rollback evidence
  exists for Public MVP / Protected Beta.

The section 11 scenario is now closed for Public MVP / Protected Beta because
the single end-to-end protected external scenario was executed through the
deployed runtime worker and recorded with redacted Telegram evidence.

## Decision

```text
GO for section 11 closed external pilot smoke
```

## Boundary

- secret values were used only inside the VPS execution context and were not
  printed or committed;
- Telegram target id and poll id remain redacted in this public report;
- this is Public MVP / Protected Beta evidence only, not production readiness.
