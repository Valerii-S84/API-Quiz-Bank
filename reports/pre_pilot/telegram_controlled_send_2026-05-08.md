# Telegram Controlled Send Attempt

Date: 2026-05-08

Scope: one controlled Telegram `sendPoll` attempt using the server-side bot
token file and the user-approved target channel. Token and target identifier are
redacted in this report.

## Preconditions Checked

| Check | Result |
|---|---|
| Bot token source | available on VPS outside Git |
| Target boundary | user-approved target provided in chat |
| Payload source | approved local fixture item `approved_traceable_001` |
| Payload type | Telegram quiz poll |
| Question length | 70 |
| Option count | 4 |
| Correct option id | redacted adapter-only index |
| Protected content | true |

## Result

```json
{
  "event": "telegram_controlled_send",
  "ok": false,
  "target": "<redacted_approved_channel>",
  "error_code": 400,
  "description": "Bad Request: chat not found"
}
```

## Decision

No Telegram message was created. The controlled send gate remains blocked until
the bot is added to the target channel, the channel id is confirmed for this
bot, or a different approved test target is provided.

## Boundary

This was a direct Bot API send attempt from the VPS. It did not create a runtime
delivery id because the deployed Telegram worker path is not implemented.
