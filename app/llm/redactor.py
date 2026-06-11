"""PII redaction before sending data to hosted LLM providers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RedactionResult:
    """Result of redacting PII from text."""

    redacted_text: str
    redaction_count: int = 0
    redaction_map: dict[str, str] = field(default_factory=dict)


# Compiled patterns for performance.
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
_PHONE_PATTERN = re.compile(
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
_SSN_PATTERN = re.compile(
    r"\b\d{3}-\d{2}-\d{4}\b"
)
_CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
)
_IP_PATTERN = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
)

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_EMAIL_PATTERN, "[EMAIL_REDACTED]"),
    (_SSN_PATTERN, "[SSN_REDACTED]"),
    (_CREDIT_CARD_PATTERN, "[CC_REDACTED]"),
    (_PHONE_PATTERN, "[PHONE_REDACTED]"),
    (_IP_PATTERN, "[IP_REDACTED]"),
]


class PIIRedactor:
    """Redacts PII from text before sending to hosted LLM providers."""

    def __init__(
        self,
        redact_emails: bool = True,
        redact_phones: bool = True,
        redact_ssns: bool = True,
        redact_credit_cards: bool = True,
        redact_ips: bool = False,
    ) -> None:
        self._active_patterns: list[tuple[re.Pattern[str], str]] = []
        if redact_emails:
            self._active_patterns.append((_EMAIL_PATTERN, "[EMAIL_REDACTED]"))
        if redact_ssns:
            self._active_patterns.append((_SSN_PATTERN, "[SSN_REDACTED]"))
        if redact_credit_cards:
            self._active_patterns.append((_CREDIT_CARD_PATTERN, "[CC_REDACTED]"))
        if redact_phones:
            self._active_patterns.append((_PHONE_PATTERN, "[PHONE_REDACTED]"))
        if redact_ips:
            self._active_patterns.append((_IP_PATTERN, "[IP_REDACTED]"))

    def redact(self, text: str) -> RedactionResult:
        """Redact PII from text, returning the redacted text and a map."""
        redacted = text
        count = 0
        redaction_map: dict[str, str] = {}

        for pattern, replacement in self._active_patterns:
            matches = pattern.findall(redacted)
            for match in matches:
                placeholder = f"{replacement.rstrip(']')}_{count}]"
                redaction_map[placeholder] = match
                redacted = redacted.replace(match, placeholder, 1)
                count += 1

        return RedactionResult(
            redacted_text=redacted,
            redaction_count=count,
            redaction_map=redaction_map,
        )

    def unredact(self, text: str, redaction_map: dict[str, str]) -> str:
        """Restore redacted PII using the redaction map."""
        result = text
        for placeholder, original in redaction_map.items():
            result = result.replace(placeholder, original)
        return result


# Singleton instance with default settings.
_default_redactor = PIIRedactor()


def redact_pii(text: str) -> RedactionResult:
    """Convenience function for PII redaction with default settings."""
    return _default_redactor.redact(text)


def unredact_pii(text: str, redaction_map: dict[str, str]) -> str:
    """Convenience function for PII un-redaction."""
    return _default_redactor.unredact(text, redaction_map)
