# Telegram Secret Wiring Evidence

Date: 2026-05-08

Status: current bot token stored on VPS as a secret file; no Telegram real send.

## Scope

This report records secret placement and container wiring for the Telegram bot
token. It does not record the token value, call Telegram Bot API or approve a
real Telegram send.

## Secret Storage

| Field | Evidence |
|---|---|
| VPS secret path | `/root/api-quiz-bank/telegram-bot-token` |
| File mode | `600` |
| Owner | `root:root` |
| Container secret path | `/run/secrets/api_quiz_bank_telegram_bot_token` |
| Env references | `QUIZBANK_TELEGRAM_BOT_TOKEN_FILE`, `TELEGRAM_BOT_TOKEN_FILE` |
| Server-only compose override | `/opt/api-quiz-bank/docker-compose.api-quiz-bank.secrets.yml` |

## Verification

The verification checks must not print the token value.

```text
secret file exists -> yes
secret file permissions -> 600 root:root
container env references -> present with secret file path only
container secret file readable -> yes
container secret format check -> ok
public no-key health after restart -> 401
public authorized health after restart -> 200
```

## Boundaries

- Token value is not committed to Git.
- Token value is not written to reports.
- Token value is not printed in logs or final responses.
- Telegram real send remains `not approved/not done`.
- Current operator decision: use this token for now, then rotate it later before
  production hardening is closed.
- Because the token was shared in chat, production use should rotate it before
  production launch if there is any chance the chat transcript is not treated as
  a secure secret channel.
