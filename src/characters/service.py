"""Business logic for creating, updating, resolving, and merging characters."""

from __future__ import annotations

from typing import Any
from datetime import UTC, datetime
from uuid import uuid4

from src.characters.interfaces import CharacterStore
from src.characters.models import Character, normalize_name, normalize_unique_strings

_MISSING = object()


class CharacterService:
    """Coordinates validation and persistence for the character domain."""

    def __init__(self, store: CharacterStore):
        self.store = store

    def create_character(
        self,
        canonical_name: str,
        aliases: list[str] | None = None,
        summary: str | None = None,
        traits: list[str] | None = None,
        role: str | None = None,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Character:
        normalized_name = self._require_name(canonical_name)
        normalized_aliases = normalize_unique_strings(aliases or [])
        self._ensure_name_is_available(normalized_name)
        self._ensure_aliases_are_available(normalized_aliases)

        now = datetime.now(UTC)
        character = Character(
            id=uuid4().hex,
            canonical_name=normalized_name,
            aliases=self._remove_conflicting_alias(normalized_aliases, normalized_name),
            summary=self._normalize_optional_text(summary),
            traits=normalize_unique_strings(traits or []),
            role=self._normalize_optional_text(role),
            status=self._normalize_optional_text(status),
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )
        return self.store.create(character)

    def get_character_by_id(self, character_id: str) -> Character | None:
        return self.store.get_by_id(character_id)

    def find_character(self, name_or_alias: str) -> Character | None:
        normalized = self._require_name(name_or_alias)
        exact_match = self.store.get_by_canonical_name(normalized)
        if exact_match is not None:
            return exact_match
        return self.store.find_by_alias(normalized)

    def list_characters(self) -> list[Character]:
        return self.store.list_all()

    def update_character(
        self,
        character_id: str,
        *,
        canonical_name: str | None | object = _MISSING,
        aliases: list[str] | object = _MISSING,
        summary: str | None | object = _MISSING,
        traits: list[str] | object = _MISSING,
        role: str | None | object = _MISSING,
        status: str | None | object = _MISSING,
        metadata: dict[str, Any] | None | object = _MISSING,
    ) -> Character:
        character = self._require_character(character_id)

        next_name = (
            self._require_name(canonical_name)
            if canonical_name is not _MISSING
            else character.canonical_name
        )
        next_aliases = (
            normalize_unique_strings(aliases)
            if aliases is not _MISSING
            else list(character.aliases)
        )

        self._ensure_name_is_available(next_name, ignore_character_id=character.id)
        self._ensure_aliases_are_available(next_aliases, ignore_character_id=character.id)

        character.canonical_name = next_name
        character.aliases = self._remove_conflicting_alias(next_aliases, next_name)

        if summary is not _MISSING:
            character.summary = self._normalize_optional_text(summary)
        if traits is not _MISSING:
            character.traits = normalize_unique_strings(traits)
        if role is not _MISSING:
            character.role = self._normalize_optional_text(role)
        if status is not _MISSING:
            character.status = self._normalize_optional_text(status)
        if metadata is not _MISSING:
            character.metadata = dict(metadata or {})

        character.updated_at = datetime.now(UTC)
        return self.store.update(character)

    def merge_characters(self, primary_character_id: str, duplicate_character_id: str) -> Character:
        if primary_character_id == duplicate_character_id:
            raise ValueError("Cannot merge a character into itself.")

        primary = self._require_character(primary_character_id)
        duplicate = self._require_character(duplicate_character_id)

        merged_aliases = normalize_unique_strings(
            [*primary.aliases, duplicate.canonical_name, *duplicate.aliases]
        )
        merged_traits = normalize_unique_strings([*primary.traits, *duplicate.traits])
        merged_metadata = {**duplicate.metadata, **primary.metadata}

        primary.aliases = self._remove_conflicting_alias(merged_aliases, primary.canonical_name)
        primary.traits = merged_traits
        primary.summary = primary.summary or duplicate.summary
        primary.role = primary.role or duplicate.role
        primary.status = primary.status or duplicate.status
        primary.metadata = merged_metadata
        primary.updated_at = datetime.now(UTC)

        self._ensure_aliases_are_available(
            primary.aliases,
            ignore_character_ids={primary.id, duplicate.id},
        )
        updated_primary = self.store.update(primary)
        self.store.delete(duplicate.id)
        return updated_primary

    def _ensure_name_is_available(
        self,
        canonical_name: str,
        *,
        ignore_character_id: str | None = None,
    ) -> None:
        existing = self.find_character(canonical_name)
        if existing is not None and existing.id != ignore_character_id:
            raise ValueError(f"Character name already exists: {canonical_name}")

    def _ensure_aliases_are_available(
        self,
        aliases: list[str],
        *,
        ignore_character_id: str | None = None,
        ignore_character_ids: set[str] | None = None,
    ) -> None:
        ignored_ids = set(ignore_character_ids or set())
        if ignore_character_id is not None:
            ignored_ids.add(ignore_character_id)
        for alias in aliases:
            existing = self.find_character(alias)
            if existing is not None and existing.id not in ignored_ids:
                raise ValueError(f"Alias already exists: {alias}")

    def _require_character(self, character_id: str) -> Character:
        character = self.store.get_by_id(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        return character

    def _require_name(self, value: str) -> str:
        normalized = normalize_name(value)
        if not normalized:
            raise ValueError("Character name cannot be empty.")
        return normalized

    def _normalize_optional_text(self, value: str | None | object) -> str | None:
        if value is None:
            return None
        if value is _MISSING:
            raise ValueError("Internal error: missing sentinel passed for normalization.")
        normalized = normalize_name(value)
        return normalized or None

    def _remove_conflicting_alias(self, aliases: list[str], canonical_name: str) -> list[str]:
        canonical_lookup = canonical_name.lower()
        return [alias for alias in aliases if alias.lower() != canonical_lookup]
