"""Resolver implementations for matching discovery candidates to canon."""

from __future__ import annotations

from src.characters.interfaces import CharacterResolver
from src.characters.models import (
    Character,
    CharacterCandidate,
    CharacterResolution,
    ResolutionDecision,
    normalize_name,
)


class SimpleCharacterResolver(CharacterResolver):
    """Resolve candidates with deterministic name and alias matching.

    This resolver is intentionally strict. It only auto-matches when a single
    canonical record clearly owns the candidate's name or alias surface. The
    conservative behavior keeps v1 auto-updates from merging distinct people
    before the project has a richer review workflow.
    """

    def resolve(
        self,
        candidate: CharacterCandidate,
        existing_characters: list[Character],
    ) -> CharacterResolution:
        """Resolve a discovery candidate against the current knowledge base."""
        candidate_names = self._candidate_lookup_names(candidate)
        matches = [
            character
            for character in existing_characters
            if self._character_matches_any_name(character, candidate_names)
        ]

        if not matches:
            return CharacterResolution(
                decision=ResolutionDecision.CREATE,
                candidate=candidate,
                reason="No canonical name or alias match found in the imported knowledge base.",
            )

        if len(matches) == 1:
            match = matches[0]
            return CharacterResolution(
                decision=ResolutionDecision.UPDATE,
                candidate=candidate,
                matched_character_id=match.id,
                matched_character_name=match.canonical_name,
                reason="Matched a single existing character by canonical name or alias.",
            )

        return CharacterResolution(
            decision=ResolutionDecision.AMBIGUOUS,
            candidate=candidate,
            reason="Multiple canonical characters match the same name or alias surface.",
        )

    def _candidate_lookup_names(self, candidate: CharacterCandidate) -> set[str]:
        """Build a normalized lookup surface for the discovery candidate."""
        return {
            normalize_name(value).lower()
            for value in [candidate.canonical_name, *candidate.aliases]
            if normalize_name(value)
        }

    def _character_matches_any_name(
        self,
        character: Character,
        candidate_names: set[str],
    ) -> bool:
        """Return `True` when a canonical record owns any candidate name."""
        character_names = {
            normalize_name(value).lower()
            for value in [character.canonical_name, *character.aliases]
            if normalize_name(value)
        }
        return bool(character_names & candidate_names)
