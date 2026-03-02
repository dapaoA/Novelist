"""Data models and normalization helpers for the character domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def normalize_name(value: str) -> str:
    """Collapse whitespace so character names have a stable canonical form."""
    return " ".join(value.strip().split())


def normalize_unique_strings(values: list[str]) -> list[str]:
    """Normalize, deduplicate, and preserve insertion order."""
    seen: set[str] = set()
    normalized_values: list[str] = []

    for value in values:
        normalized = normalize_name(value)
        lookup = normalized.lower()
        if normalized and lookup not in seen:
            seen.add(lookup)
            normalized_values.append(normalized)

    return normalized_values


@dataclass(slots=True)
class Character:
    """Canonical character record used by the rest of the project."""

    id: str
    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    summary: str | None = None
    traits: list[str] = field(default_factory=list)
    role: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class CharacterCandidate:
    """Proposed character data from an extractor or parser."""

    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    summary: str | None = None
    traits: list[str] = field(default_factory=list)
    role: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
