"""FastAPI routes for the MVP admin control surface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from .admin_auth import authenticate_admin, require_admin_read, require_admin_write, require_owner
from .admin_panel import ADMIN_PANEL_HTML
from .admin_service import (
    change_admin_quiz_item_status,
    change_admin_consumer_status,
    create_admin_consumer,
    get_admin_visual_settings,
    get_admin_quiz_item,
    list_admin_consumers,
    list_admin_quiz_items,
    list_audit_log,
    admin_dashboard,
    update_admin_visual_settings,
)


AdminStatus = Literal[
    "draft",
    "imported",
    "normalized",
    "needs_review",
    "approved",
    "published",
    "monitored",
    "retired",
    "blocked",
]
AdminLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
AdminTheme = Literal[
    "T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09",
    "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18",
]
ConsumerKind = Literal["api_client", "telegram_channel", "telegram_bot", "teacher", "school"]
VisualDeliveryMode = Literal["text_only", "image_standard", "image_branded"]
VisualFallbackPolicy = Literal["text_only", "cache_only", "block_visual_delivery"]


class AdminStatusChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=500)


class AdminConsumerCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consumer_id: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    consumer_kind: ConsumerKind
    daily_quota_limit: int = Field(ge=0, le=10000)
    allowed_cefr_levels: list[AdminLevel] = Field(min_length=1)
    allowed_theme_ids: list[AdminTheme] = Field(min_length=1)
    api_key: str = Field(min_length=8, max_length=200)
    reason: str = Field(min_length=3, max_length=500)


class AdminVisualSettingsPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delivery_mode: VisualDeliveryMode | None = None
    visual_style: str | None = Field(default=None, min_length=1, max_length=120)
    branding_preset: str | None = Field(default=None, min_length=1, max_length=120)
    fallback_policy: VisualFallbackPolicy | None = None
    daily_visual_delivery_limit: int | None = Field(default=None, ge=0, le=10000)
    daily_generation_limit: int | None = Field(default=None, ge=0, le=10000)
    monthly_generation_limit: int | None = Field(default=None, ge=0, le=100000)
    is_active: bool | None = None
    reason: str = Field(min_length=3, max_length=500)


def register_admin_routes(app: FastAPI, database_path: Path) -> None:
    @app.get("/admin", tags=["admin"], response_class=HTMLResponse)
    def admin_panel() -> str:
        return ADMIN_PANEL_HTML

    @app.get("/v1/admin/dashboard", tags=["admin"])
    def dashboard(x_quizbank_admin_key: AdminKeyHeader = None) -> dict[str, object]:
        require_admin_read(authenticate_admin(database_path, x_quizbank_admin_key))
        return admin_dashboard(database_path)

    @app.get("/v1/admin/quiz-items", tags=["admin"])
    def quiz_items(
        x_quizbank_admin_key: AdminKeyHeader = None,
        status: AdminStatus | None = None,
        cefr_level: AdminLevel | None = None,
        theme_id: AdminTheme | None = None,
        source_id: str | None = None,
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, object]:
        require_admin_read(authenticate_admin(database_path, x_quizbank_admin_key))
        return list_admin_quiz_items(
            database_path,
            {
                "status": status,
                "cefr_level": cefr_level,
                "theme_id": theme_id,
                "source_id": source_id,
            },
            limit,
        )

    @app.get("/v1/admin/quiz-items/{item_id}", tags=["admin"])
    def quiz_item(item_id: str, x_quizbank_admin_key: AdminKeyHeader = None) -> dict[str, object]:
        require_admin_read(authenticate_admin(database_path, x_quizbank_admin_key))
        return get_admin_quiz_item(database_path, item_id)

    @app.get("/v1/admin/audit-log", tags=["admin"])
    def audit_log(
        x_quizbank_admin_key: AdminKeyHeader = None,
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, object]:
        require_admin_read(authenticate_admin(database_path, x_quizbank_admin_key))
        return list_audit_log(database_path, limit)

    register_consumer_routes(app, database_path)
    register_status_route(app, database_path, "approve")
    register_status_route(app, database_path, "publish")
    register_status_route(app, database_path, "retire")
    register_status_route(app, database_path, "block")


AdminKeyHeader = Annotated[str | None, Header(alias="X-QuizBank-Admin-Key")]


def register_consumer_routes(app: FastAPI, database_path: Path) -> None:
    @app.get("/v1/admin/consumers", tags=["admin"])
    def consumers(
        x_quizbank_admin_key: AdminKeyHeader = None,
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, object]:
        require_admin_read(authenticate_admin(database_path, x_quizbank_admin_key))
        return list_admin_consumers(database_path, limit)

    @app.post("/v1/admin/consumers", tags=["admin"])
    def create_consumer(
        payload: AdminConsumerCreateRequest,
        x_quizbank_admin_key: AdminKeyHeader = None,
    ) -> dict[str, object]:
        admin = authenticate_admin(database_path, x_quizbank_admin_key)
        require_owner(admin)
        return create_admin_consumer(database_path, payload.model_dump(), admin.actor)

    @app.get("/v1/admin/consumers/{consumer_id}/visual-settings", tags=["admin"])
    def consumer_visual_settings(
        consumer_id: str,
        x_quizbank_admin_key: AdminKeyHeader = None,
    ) -> dict[str, object]:
        admin = authenticate_admin(database_path, x_quizbank_admin_key)
        require_owner(admin)
        return get_admin_visual_settings(database_path, consumer_id)

    @app.patch("/v1/admin/consumers/{consumer_id}/visual-settings", tags=["admin"])
    def patch_consumer_visual_settings(
        consumer_id: str,
        payload: AdminVisualSettingsPatchRequest,
        x_quizbank_admin_key: AdminKeyHeader = None,
    ) -> dict[str, object]:
        admin = authenticate_admin(database_path, x_quizbank_admin_key)
        require_owner(admin)
        return update_admin_visual_settings(
            database_path,
            consumer_id,
            payload.model_dump(exclude_none=True),
            admin.actor,
        )

    register_consumer_status_route(app, database_path, "suspend", "suspended")
    register_consumer_status_route(app, database_path, "activate", "active")
    register_consumer_status_route(app, database_path, "block", "blocked")


def register_status_route(app: FastAPI, database_path: Path, action: str) -> None:
    async def status_change(
        item_id: str,
        payload: AdminStatusChangeRequest,
        x_quizbank_admin_key: AdminKeyHeader = None,
    ) -> dict[str, object]:
        admin = authenticate_admin(database_path, x_quizbank_admin_key)
        require_admin_write(admin)
        return change_admin_quiz_item_status(
            database_path,
            item_id,
            action,
            admin.actor,
            payload.reason,
        )

    app.post(f"/v1/admin/quiz-items/{{item_id}}/{action}", tags=["admin"])(status_change)


def register_consumer_status_route(
    app: FastAPI,
    database_path: Path,
    action: str,
    to_status: str,
) -> None:
    async def consumer_status_change(
        consumer_id: str,
        payload: AdminStatusChangeRequest,
        x_quizbank_admin_key: AdminKeyHeader = None,
    ) -> dict[str, object]:
        admin = authenticate_admin(database_path, x_quizbank_admin_key)
        require_owner(admin)
        return change_admin_consumer_status(
            database_path,
            consumer_id,
            to_status,
            admin.actor,
            payload.reason,
        )

    app.post(f"/v1/admin/consumers/{{consumer_id}}/{action}", tags=["admin"])(consumer_status_change)
