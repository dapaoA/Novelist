"""Protocols for character persistence and extraction."""

from __future__ import annotations

from typing import Protocol

from src.characters.models import Character, CharacterCandidate


class CharacterStore(Protocol):
    """Persistence contract for canonical character records."""

    def create(self, character: Character) -> Character:
        ...

    def update(self, character: Character) -> Character:
        ...

    def delete(self, character_id: str) -> None:
        ...

    def get_by_id(self, character_id: str) -> Character | None:
        ...

    def get_by_canonical_name(self, canonical_name: str) -> Character | None:
        ...

    def find_by_alias(self, alias: str) -> Character | None:
        ...

    def list_all(self) -> list[Character]:
        ...


class CharacterExtractor(Protocol):
    """Optional contract for text-to-character extraction."""

    def extract(self, text: str) -> list[CharacterCandidate]:
        ...
