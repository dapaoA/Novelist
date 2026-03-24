"""Protocols for character persistence and extraction."""

from __future__ import annotations

from typing import Protocol

from src.characters.models import (
    Character,
    CharacterCandidate,
    CharacterResolution,
    CharacterUpdateCandidate,
)


class CharacterStore(Protocol):
    """Persistence contract for canonical character records.

    Implementations hide storage details from the service layer. A store may be
    backed by in-memory state, SQLite, Postgres, or another persistence system.
    """

    def create(self, character: Character) -> Character:
        """Persist a new character record.

        Args:
            character: The validated canonical character to store.

        Returns:
            The stored character record.
        """
        ...

    def update(self, character: Character) -> Character:
        """Persist changes to an existing character.

        Args:
            character: The character record with updated values.

        Returns:
            The updated stored character record.
        """
        ...

    def delete(self, character_id: str) -> None:
        """Delete a character by its canonical identifier.

        Args:
            character_id: The unique identifier of the character to remove.
        """
        ...

    def get_by_id(self, character_id: str) -> Character | None:
        """Look up a character by canonical identifier.

        Args:
            character_id: The unique character identifier.

        Returns:
            The matching character if present, otherwise `None`.
        """
        ...

    def get_by_canonical_name(self, canonical_name: str) -> Character | None:
        """Look up a character by canonical display name.

        Args:
            canonical_name: The normalized display name to search for.

        Returns:
            The matching character if present, otherwise `None`.
        """
        ...

    def find_by_alias(self, alias: str) -> Character | None:
        """Look up a character by one of its known aliases.

        Args:
            alias: An alternate name for a character.

        Returns:
            The matching character if present, otherwise `None`.
        """
        ...

    def list_all(self) -> list[Character]:
        """Return all stored characters.

        Returns:
            A list of canonical character records.
        """
        ...


class CharacterExtractor(Protocol):
    """Contract for discovery-oriented text-to-character extraction.

    Discovery extractors propose candidate records from unstructured input.
    They do not define storage behavior or canonical merge rules.
    """

    def extract(self, text: str) -> list[CharacterCandidate]:
        """Parse text and propose character candidates.

        Args:
            text: Raw unstructured text to analyze.

        Returns:
            A list of extracted candidate records.
        """
        ...


class CharacterUpdateExtractor(Protocol):
    """Contract for recurring-character patch extraction.

    Update extractors operate after resolution has matched a discovery
    candidate to an existing canonical character. They return sparse patch
    proposals instead of rewriting the full record.
    """

    def propose_update(
        self,
        candidate: CharacterCandidate,
        existing_character: Character,
    ) -> CharacterUpdateCandidate | None:
        """Build a patch proposal for a recurring character.

        Args:
            candidate: Fresh discovery candidate extracted from new text.
            existing_character: The canonical character already stored in the
                knowledge base.

        Returns:
            A sparse update proposal or `None` when no durable change should be
            applied.
        """
        ...


class CharacterResolver(Protocol):
    """Contract for matching discovery candidates to existing characters."""

    def resolve(
        self,
        candidate: CharacterCandidate,
        existing_characters: list[Character],
    ) -> CharacterResolution:
        """Resolve a discovery candidate against canonical storage.

        Args:
            candidate: Discovery candidate extracted from new text.
            existing_characters: Canonical characters currently known to the
                project.

        Returns:
            A resolution result describing whether the candidate should create a
            new record, update an existing one, or be treated as ambiguous.
        """
        ...
