"""Telegram Bot API HTTP adapter primitives."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramDeliveryError(Exception):
    """Raised when a Telegram payload cannot be delivered or validated."""


@dataclass(frozen=True)
class TelegramSendResult:
    message_id: str
    poll_id: str | None = None


@dataclass(frozen=True)
class TelegramImageSendResult:
    message_id: str


class TelegramBotApiAdapter:
    def __init__(self, bot_token: str, api_base: str = TELEGRAM_API_BASE) -> None:
        if not bot_token.strip():
            raise ValueError("Telegram bot token must not be empty")
        self.bot_token = bot_token.strip()
        self.api_base = api_base.rstrip("/")

    def send_quiz_poll(self, payload: dict[str, Any]) -> TelegramSendResult:
        request = self.json_request("sendPoll", telegram_api_payload(payload))
        body = execute_telegram_request(request)
        result = body.get("result", {})
        return TelegramSendResult(
            message_id=str(result.get("message_id", "")),
            poll_id=poll_id_from_result(result),
        )

    def send_photo(self, payload: dict[str, Any]) -> TelegramImageSendResult:
        content_type, body_bytes = telegram_photo_multipart_payload(payload)
        request = urllib.request.Request(
            self.method_url("sendPhoto"),
            data=body_bytes,
            headers={"Content-Type": content_type},
            method="POST",
        )
        body = execute_telegram_request(request)
        result = body.get("result", {})
        return TelegramImageSendResult(message_id=str(result.get("message_id", "")))

    def json_request(self, method_name: str, payload: dict[str, Any]) -> urllib.request.Request:
        return urllib.request.Request(
            self.method_url(method_name),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    def method_url(self, method_name: str) -> str:
        return f"{self.api_base}/bot{self.bot_token}/{method_name}"


def execute_telegram_request(request: urllib.request.Request) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise TelegramDeliveryError(read_http_error_description(error)) from error
    except urllib.error.URLError as error:
        raise TelegramDeliveryError(f"telegram_request_failed:{error.reason}") from error
    if not body.get("ok"):
        description = str(body.get("description", "telegram_send_rejected"))
        raise TelegramDeliveryError(description[:180])
    return body


def telegram_api_payload(payload: dict[str, Any]) -> dict[str, Any]:
    correct_option_ids = payload["correct_option_ids"]
    if not isinstance(correct_option_ids, list) or len(correct_option_ids) != 1:
        raise TelegramDeliveryError("telegram_bot_api_requires_single_correct_option")
    return {
        "chat_id": payload["chat_id"],
        "question": payload["question"],
        "options": payload["options"],
        "type": payload["type"],
        "correct_option_id": correct_option_ids[0],
        "explanation": payload["explanation"],
        "is_anonymous": payload["is_anonymous"],
    }


def telegram_photo_multipart_payload(payload: dict[str, Any]) -> tuple[str, bytes]:
    photo_path = Path(str(payload.get("photo_path", "")))
    if not photo_path.is_file():
        raise TelegramDeliveryError("telegram_photo_file_not_found")
    return multipart_form_data(
        {"chat_id": str(payload["chat_id"])},
        {"photo": (photo_path.name, photo_path.read_bytes(), "application/octet-stream")},
    )


def multipart_form_data(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[str, bytes]:
    boundary = f"quizbank-{uuid.uuid4().hex}"
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")
    for name, (filename, file_bytes, content_type) in files.items():
        append_file_part(body, boundary, name, filename, content_type, file_bytes)
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return f"multipart/form-data; boundary={boundary}", bytes(body)


def append_file_part(
    body: bytearray,
    boundary: str,
    name: str,
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> None:
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(file_bytes)
    body.extend(b"\r\n")


def poll_id_from_result(result: dict[str, Any]) -> str | None:
    poll = result.get("poll")
    if not isinstance(poll, dict):
        return None
    poll_id = poll.get("id")
    return None if poll_id is None else str(poll_id)


def read_http_error_description(error: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(error.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return f"telegram_http_error:{error.code}"
    description = str(body.get("description", f"telegram_http_error:{error.code}"))
    return description[:180]
