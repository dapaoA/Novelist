"""In-memory character store for local development and testing."""

from __future__ import annotations

from src.characters.models import Character, normalize_name


class InMemoryCharacterStore:
    """Simple store implementation that keeps records in process memory.

    This implementation is useful for tests, prototypes, and early integration
    work before a persistent database backend is introduced.
    """

    def __init__(self) -> None:
        """Initialize the empty in-memory character index."""
        self._characters: dict[str, Character] = {}

    def create(self, character: Character) -> Character:
        """Insert a new character record into memory.

        Args:
            character: Canonical character to persist.

        Returns:
            The same character after storage.

        Raises:
            ValueError: If the character ID already exists.
        """
        if character.id in self._characters:
            raise ValueError(f"Character ID already exists: {character.id}")
        self._characters[character.id] = character
        return character

    def update(self, character: Character) -> Character:
        """Replace an existing character record in memory.

        Args:
            character: Character object containing the updated field values.

        Returns:
            The updated character record.

        Raises:
            ValueError: If the character ID does not exist.
        """
        if character.id not in self._characters:
            raise ValueError(f"Character not found: {character.id}")
        self._characters[character.id] = character
        return character

    def delete(self, character_id: str) -> None:
        """Remove a character from memory if it exists.

        Args:
            character_id: Identifier of the character to remove.
        """
        self._characters.pop(character_id, None)

    def get_by_id(self, character_id: str) -> Character | None:
        """Look up a character by identifier.

        Args:
            character_id: Canonical character ID.

        Returns:
            The matching character if present, otherwise `None`.
        """
        return self._characters.get(character_id)

    def get_by_canonical_name(self, canonical_name: str) -> Character | None:
        """Look up a character by canonical name.

        Args:
            canonical_name: Name to search for.

        Returns:
            The matching character if present, otherwise `None`.
        """
        normalized = normalize_name(canonical_name).lower()
        for character in self._characters.values():
            if character.canonical_name.lower() == normalized:
                return character
        return None

    def find_by_alias(self, alias: str) -> Character | None:
        """Look up a character by alias.

        Args:
            alias: Alternate name to search for.

        Returns:
            The matching character if present, otherwise `None`.
        """
        normalized = normalize_name(alias).lower()
        for character in self._characters.values():
            aliases = {candidate.lower() for candidate in character.aliases}
            if normalized in aliases:
                return character
        return None

    def list_all(self) -> list[Character]:
        """Return all stored characters in deterministic name order.

        Returns:
            All character records sorted by canonical name.
        """
        return sorted(self._characters.values(), key=lambda item: item.canonical_name.lower())
