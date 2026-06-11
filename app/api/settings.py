"""Settings REST API endpoints: model configs, tools, guardrails."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.schemas import (
    ApiResponse,
    ModelConfigCreate,
    ModelConfigOut,
    ModelConfigUpdate,
    ToolConfigOut,
    ToolConfigUpdate,
)
from app.models.model_config import ModelConfig
from app.tools.registry import tool_registry

router = APIRouter(prefix="/settings", tags=["settings"])


# ── Model Configs ────────────────────────────────────────────────────


@router.get("/model-configs", response_model=ApiResponse[list[ModelConfigOut]])
async def list_model_configs(
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(ModelConfig).order_by(ModelConfig.purpose)
    )
    configs = result.scalars().all()
    return {"data": [ModelConfigOut.model_validate(c) for c in configs]}


@router.post(
    "/model-configs",
    response_model=ApiResponse[ModelConfigOut],
    status_code=201,
)
async def create_model_config(
    body: ModelConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(timezone.utc)
    config = ModelConfig(
        id=uuid4(),
        provider=body.provider,
        model_name=body.model_name,
        purpose=body.purpose,
        mode=body.mode,
        is_default=body.is_default,
        is_enabled=body.is_enabled,
        config=body.config,
        created_at=now,
        updated_at=now,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return {"data": ModelConfigOut.model_validate(config)}


@router.patch(
    "/model-configs/{config_id}",
    response_model=ApiResponse[ModelConfigOut],
)
async def update_model_config(
    config_id: str,
    body: ModelConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(ModelConfig).where(ModelConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    config.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(config)
    return {"data": ModelConfigOut.model_validate(config)}


# ── Tool Configs ─────────────────────────────────────────────────────


@router.get("/tools", response_model=ApiResponse[list[ToolConfigOut]])
async def list_tools() -> dict:
    from app.guardrails.catalog import TOOL_SENSITIVITY_CATALOG

    tools = []
    for name, entry in tool_registry._tools.items():
        sensitivity = TOOL_SENSITIVITY_CATALOG.get(name, "safe")
        tools.append(
            ToolConfigOut(
                name=name,
                sensitivity=sensitivity,
                description=entry.description if entry.description else "",
                enabled=True,
            )
        )
    return {"data": tools}


@router.patch("/tools/{tool_name}", response_model=ApiResponse[ToolConfigOut])
async def update_tool(tool_name: str, body: ToolConfigUpdate) -> dict:
    from app.guardrails.catalog import TOOL_SENSITIVITY_CATALOG

    if tool_name not in tool_registry._tools:
        raise HTTPException(status_code=404, detail="Tool not found")

    if body.sensitivity:
        TOOL_SENSITIVITY_CATALOG[tool_name] = body.sensitivity

    sensitivity = TOOL_SENSITIVITY_CATALOG.get(tool_name, "safe")
    return {
        "data": ToolConfigOut(
            name=tool_name,
            sensitivity=sensitivity,
            enabled=body.enabled if body.enabled is not None else True,
        )
    }


# ── Guardrail Policies ──────────────────────────────────────────────


@router.get("/guardrail-policies", response_model=ApiResponse[dict])
async def get_guardrail_policies() -> dict:
    from app.guardrails.catalog import (
        APPROVAL_REQUIRED_TOOLS,
        BLOCKED_TOOLS,
        SAFE_TOOLS,
        TOOL_SENSITIVITY_CATALOG,
    )

    return {
        "data": {
            "safe_tools": list(SAFE_TOOLS),
            "approval_required_tools": list(APPROVAL_REQUIRED_TOOLS),
            "blocked_tools": list(BLOCKED_TOOLS),
            "catalog": dict(TOOL_SENSITIVITY_CATALOG),
        }
    }
