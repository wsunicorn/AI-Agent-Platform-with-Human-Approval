from enum import StrEnum

from sqlalchemy import Enum as SQLAlchemyEnum


class TicketStatus(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentMode(StrEnum):
    SUPPORT_AGENT = "support_agent"
    WORKFLOW_AUTOMATION = "workflow_automation"


class InputType(StrEnum):
    TICKET = "ticket"
    EMAIL = "email"
    INSTRUCTION = "instruction"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Sensitivity(StrEnum):
    SAFE = "safe"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


class ToolCallStatus(StrEnum):
    PROPOSED = "proposed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class ApprovalStatus(StrEnum):
    PROPOSED = "proposed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ActorType(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"


class KnowledgeDocumentType(StrEnum):
    POLICY = "policy"
    FAQ = "faq"
    PLAYBOOK = "playbook"
    MACRO = "macro"
    REPORT_TEMPLATE = "report_template"


class ModelProvider(StrEnum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"


class ModelMode(StrEnum):
    HOSTED = "hosted"
    LOCAL = "local"


class ModelPurpose(StrEnum):
    DEFAULT = "default"
    ROUTING = "routing"
    DRAFTING = "drafting"
    EMBEDDING = "embedding"
    FALLBACK = "fallback"
    QUALITY = "quality"


def enum_column(enum_class: type[StrEnum], name: str) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_class,
        name=name,
        values_callable=lambda values: [item.value for item in values],
        validate_strings=True,
    )
