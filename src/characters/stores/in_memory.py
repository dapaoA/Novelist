"""In-memory character store for local development and testing."""

from __future__ import annotations

from src.characters.models import Character, normalize_name


class InMemoryCharacterStore:
    """Simple store implementation that keeps records in process memory."""

    def __init__(self) -> None:
        self._characters: dict[str, Character] = {}

    def create(self, character: Character) -> Character:
        if character.id in self._characters:
            raise ValueError(f"Character ID already exists: {character.id}")
        self._characters[character.id] = character
        return character

    def update(self, character: Character) -> Character:
        if character.id not in self._characters:
            raise ValueError(f"Character not found: {character.id}")
        self._characters[character.id] = character
        return character

    def delete(self, character_id: str) -> None:
        self._characters.pop(character_id, None)

    def get_by_id(self, character_id: str) -> Character | None:
        return self._characters.get(character_id)

    def get_by_canonical_name(self, canonical_name: str) -> Character | None:
        normalized = normalize_name(canonical_name).lower()
        for character in self._characters.values():
            if character.canonical_name.lower() == normalized:
                return character
        return None

    def find_by_alias(self, alias: str) -> Character | None:
        normalized = normalize_name(alias).lower()
        for character in self._characters.values():
            aliases = {candidate.lower() for candidate in character.aliases}
            if normalized in aliases:
                return character
        return None

    def list_all(self) -> list[Character]:
        return sorted(self._characters.values(), key=lambda item: item.canonical_name.lower())
