import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set):
        return [to_jsonable(item) for item in value]

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, uuid.UUID):
        return str(value)

    if isinstance(value, datetime | date):
        return value.isoformat()

    return value
