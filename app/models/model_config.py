from sqlalchemy import Boolean, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ModelMode, ModelProvider, ModelPurpose, enum_column
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ModelConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_configs"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "model_name",
            "purpose",
            name="uq_model_configs_provider_model_purpose",
        ),
        Index("ix_model_configs_provider_purpose_default", "provider", "purpose", "is_default"),
    )

    provider: Mapped[ModelProvider] = mapped_column(
        enum_column(ModelProvider, "model_provider"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint_url: Mapped[str | None] = mapped_column(String(500))
    mode: Mapped[ModelMode] = mapped_column(enum_column(ModelMode, "model_mode"), nullable=False)
    purpose: Mapped[ModelPurpose] = mapped_column(
        enum_column(ModelPurpose, "model_purpose"),
        nullable=False,
    )
    temperature: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.2, server_default="0.2"
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2048, server_default="2048"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
