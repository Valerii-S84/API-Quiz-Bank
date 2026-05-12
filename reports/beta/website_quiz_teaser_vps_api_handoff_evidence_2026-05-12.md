# Website Quiz Teaser VPS API Handoff Evidence - 2026-05-12

Status: ready for controlled protected beta handoff.

This is a Controlled Protected Beta. This is not a broad public launch. This is not public signup. This is not a commercial launch. No frontend repository changes were made.

## VPS Preflight

- VPS repo: `/opt/api-quiz-bank`
- Runtime commit: `83fc71e18e9b55fc47bdcebbe12fbcac208476a8`
- Runtime branch: `main`
- Tree changes deployed to VPS per owner instruction:
  - `src/quizbank_mvp/app.py`
  - `src/quizbank_mvp/selection.py`
  - `tools/provision_website_quiz_teaser_consumer.py`
  - `tools/smoke_website_quiz_teaser_consumer.py`
  - `tests/test_website_quiz_teaser_beta.py`
- API container: `api-quiz-bank-pilot`, `running/healthy`, restart count `0`
- PostgreSQL container: `api-quiz-bank-postgres`, `running/healthy`, restart count `0`
- PostgreSQL readiness: `pg_isready` accepted connections
- Backup timer: `api-quiz-bank-postgres-backup.timer` active, last service result `success/0`
- Public health: `GET https://api.valerchik.de/health` with edge key returned `200`
- Public ready: `GET https://api.valerchik.de/ready` with edge key returned `200`
- Protected public route without edge key: `401 Unauthorized`

## Backup

- Pre-change PostgreSQL backup created: `/opt/api-quiz-bank/var/backups/api-quiz-bank/api_quiz_bank_pg_20260512T192335Z.dump`
- Backup size observed: `1570235` bytes
- No backup secrets printed.

## Consumer Readiness

- Consumer created/confirmed: yes
- Consumer ID/name: `website_quiz_teaser`
- Status after smoke: `active`
- Credential status after rotation: `active`
- Credential storage: hashed in DB; report contains no raw credential
- Entitlement: `quiz_delivery`, `active`
- CEFR scope: `A1,A2`
- Runtime theme scope: `T02`
- Controlled teaser theme labels: `Artikel`, `Alltag`, `Verben`, `Präpositionen`
- Quota: `5/day`
- Runtime corpus check for `A1/A2 + T02`: `2021` eligible published/approved items
- No unrestricted corpus access: confirmed by scope denial proofs below.

## VPS API Smoke Proof

Endpoint used: `POST https://api.valerchik.de/v1/quiz-items/next`

Valid protected request returned quiz items and created deliveries:

| # | Status | Delivery ID | Item ID | CEFR | Feedback | Raw answer key |
|---|---:|---|---|---|---|---|
| 1 | 200 | `deliv_57fedcf01dc3407d` | `gmb_everyday_logic_bank_a1_b1_247_el_049` | A2 | present | not exposed |
| 2 | 200 | `deliv_f77549f992b44126` | `gmb_topic_vocabulary_themes_bank_a2_b1_210_tvt_109` | A2 | present | not exposed |
| 3 | 200 | `deliv_a2aa54a5ba814cf3` | `gmb_everyday_logic_bank_a1_b1_247_el_076` | A2 | present | not exposed |
| 4 | 200 | `deliv_b36dfdb271784d3b` | `gmb_preposition_selection_bank_a2_b1_210_ps_183` | A2 | present | not exposed |
| 5 | 200 | `deliv_067940802b3f4854` | `gmb_everyday_logic_bank_a1_b1_247_el_191` | A2 | present | not exposed |

- 5-delivery proof: `5` successful deliveries
- Repeat policy proof: `5` distinct item IDs across `5` deliveries
- Delivery record proof: final DB state had `5` delivery rows and `5` distinct delivered items
- Quota denial proof: 6th request returned `429 QUOTA_EXCEEDED`
- Quota reset for handoff: after proof, daily usage was reset from `5/5` to `0/5` while keeping delivery evidence rows.

## Denial Proofs

- Public route without edge key: `401 Unauthorized`
- Edge key present but missing consumer credentials: `401 AUTH_REQUIRED`
- Wrong consumer credential: `401 AUTH_INVALID_API_KEY`
- Outside CEFR scope, `B1 + T02`: `403 CONSUMER_LEVEL_NOT_ALLOWED`
- Outside theme scope, `A2 + T03`: `403 CONSUMER_THEME_NOT_ALLOWED`
- Entitlement removal probe: `403 ENTITLEMENT_MISSING_FEATURE`
- Suspended consumer probe: `403 CONSUMER_NOT_ACTIVE`
- Credential rotation/revoke path:
  - old key after rotation: `401 AUTH_INVALID_API_KEY`
  - rotated key after rotation: accepted by auth and failed closed at quota gate during proof with `429 QUOTA_EXCEEDED`
- Consumer was restored to `active` and entitlement restored to `active` after denial probes.

## Masked Frontend Env Handoff

Raw values are stored only in secure env files:

- VPS handoff file: `/root/api-quiz-bank/website-quiz-teaser.env`, mode `600`
- Local handoff file: `/home/serputko/.config/api-quiz-bank/website_quiz_teaser_vps.env`, mode `600`
- No raw VPS handoff file is kept in the repository tree.

Masked values:

```dotenv
QUIZ_BANK_API_BASE_URL=https://api.valerchik.de
QUIZ_BANK_EDGE_API_KEY=5849ca...7e54
QUIZ_BANK_CONSUMER_ID=website_quiz_teaser
QUIZ_BANK_CONSUMER_API_KEY=wqt_yk...7f_8
```

No raw secrets are printed in this report.

## API / Frontend Contract

Frontend must call API Bank only from the server-side Next.js proxy route. Browser code must call only the frontend route, not `https://api.valerchik.de` directly.

API Bank endpoint for the proxy:

```http
POST /v1/quiz-items/next
Content-Type: application/json
X-API-Key: ${QUIZ_BANK_EDGE_API_KEY}
X-Consumer-Id: ${QUIZ_BANK_CONSUMER_ID}
X-QuizBank-API-Key: ${QUIZ_BANK_CONSUMER_API_KEY}
```

Request body:

```json
{
  "consumer_id": "website_quiz_teaser",
  "cefr_level": "A2",
  "theme_ids": ["T02"]
}
```

Response fields needed by the widget:

- `delivery_id`
- `delivery.delivery_id`
- `quiz_item.id`
- `quiz_item.question.text`
- `quiz_item.options[].id`
- `quiz_item.options[].text`
- `quiz_item.feedback.correctAnswerId`
- `quiz_item.feedback.explanation`
- `quiz_item.cefr_level`
- `quiz_item.metadata.display.theme_title`

Error behavior:

- Quota exceeded: `429` with `reason_code=QUOTA_EXCEEDED`
- Unauthorized or missing consumer credential: `401` with `AUTH_REQUIRED` or `AUTH_INVALID_API_KEY`
- Missing public edge key: `401 Unauthorized`
- Suspended consumer: `403` with `CONSUMER_NOT_ACTIVE`
- Entitlement removed: `403` with `ENTITLEMENT_MISSING_FEATURE`
- Out of allowed scope: `403` with `CONSUMER_LEVEL_NOT_ALLOWED` or `CONSUMER_THEME_NOT_ALLOWED`
- Unavailable runtime: fail closed on non-2xx/timeout and do not expose secrets to the browser

## Frontend Agent Next Step

- Use the secure env handoff file, not this report, for raw values.
- Wire the values into server-only frontend runtime env.
- Ensure the browser calls only `/api/quiz-teaser/next`.
- Confirm no API Bank secrets appear in HTML, browser bundle, logs, or Git.

## Evidence Hygiene

- No raw API Bank secrets in this report.
- No broad public launch statement.
- No public signup statement.
- No commercial launch statement.
- VPS API Bank runtime was touched; frontend repo was not touched.

## Verification

- VPS deploy: Docker Compose rebuild/recreate completed for `api-quiz-bank-pilot`.
- VPS protected smoke: passed and wrote masked JSON evidence to `/opt/api-quiz-bank/var/reports/website_quiz_teaser_vps_smoke_20260512.json`.
- Local API Bank test suite: `python3 -m unittest discover -s tests -p 'test_*.py'` passed, `140` tests.
- Local secret scan: `python3 tools/no_secrets_scan.py` passed.
- VPS standard secret scan note: `python3 tools/no_secrets_scan.py` detects the operational untracked `.env` runtime file in `/opt/api-quiz-bank`; the file is mode `600` and is not tracked by Git.
- VPS tracked sensitive filename check: passed, no tracked sensitive filenames except allowed `.example` files.
- Final public health: `200`.
- Final public ready: `200`.
- Final VPS handoff file mode: `600`.
