"""Update-extractor implementations for recurring characters."""

from __future__ import annotations

from src.characters.interfaces import CharacterUpdateExtractor
from src.characters.models import (
    Character,
    CharacterCandidate,
    CharacterUpdateCandidate,
    ProfileDepth,
    normalize_unique_strings,
)


class SimpleCharacterUpdateExtractor(CharacterUpdateExtractor):
    """Create conservative patches from discovery candidates.

    This v1 updater is intentionally deterministic. It reuses the discovery
    candidate that already came from the new text and turns only the durable,
    policy-allowed parts into a sparse patch proposal. A richer LLM-based
    updater can replace this later without changing the orchestration contract.
    """

    def __init__(self, *, enabled_modules: set[str] | None = None) -> None:
        """Initialize the updater with module-level policy switches.

        Args:
            enabled_modules: Profile modules that this updater is allowed to
                carry forward into canonical recurring-character patches.
        """
        self.enabled_modules = set(enabled_modules or {"core"})

    def propose_update(
        self,
        candidate: CharacterCandidate,
        existing_character: Character,
    ) -> CharacterUpdateCandidate | None:
        """Turn a matched discovery candidate into a sparse recurring patch.

        Args:
            candidate: Fresh discovery candidate extracted from new text.
            existing_character: Canonical character already stored in the
                knowledge base.

        Returns:
            A sparse recurring-character patch, or `None` when the candidate
            does not justify any durable canonical change.
        """
        aliases_to_add = self._new_strings(candidate.aliases, existing_character.aliases)
        tendencies_to_add = self._new_strings(
            candidate.stable_tendencies,
            existing_character.stable_tendencies,
        )
        salient_concept = self._choose_salient_concept(candidate, existing_character)
        target_profile_depth = self._promote_profile_depth(candidate, existing_character)

        patch = CharacterUpdateCandidate(
            character_id=existing_character.id,
            canonical_name=existing_character.canonical_name,
            profile_depth=target_profile_depth,
            aliases_to_add=aliases_to_add,
            salient_concept=salient_concept,
            stable_tendencies_to_add=tendencies_to_add,
            capabilities=self._module_value(
                "capabilities",
                candidate.capabilities,
                existing_character=existing_character,
                target_profile_depth=target_profile_depth,
            ),
            conditions=self._module_value(
                "conditions",
                candidate.conditions,
                existing_character=existing_character,
                target_profile_depth=target_profile_depth,
            ),
            social=self._module_value(
                "social",
                candidate.social,
                existing_character=existing_character,
                target_profile_depth=target_profile_depth,
            ),
            appearance=self._module_value(
                "appearance",
                candidate.appearance,
                existing_character=existing_character,
                target_profile_depth=target_profile_depth,
            ),
            system_stats=self._module_value(
                "system_stats",
                candidate.system_stats,
                existing_character=existing_character,
                target_profile_depth=target_profile_depth,
            ),
            metadata_updates={},
        )
        return patch if self._has_patch_data(patch) else None

    def _module_value(
        self,
        module_name: str,
        candidate_value: object | None,
        *,
        existing_character: Character,
        target_profile_depth: ProfileDepth | None,
    ) -> object | None:
        """Return a module update only when policy allows it for this profile.

        Args:
            module_name: Name of the optional module under evaluation.
            candidate_value: Candidate module payload extracted from new text.
            existing_character: Canonical character before the patch is applied.
            target_profile_depth: Optional promoted profile depth that would
                take effect if this patch is applied.

        Returns:
            The candidate module payload when policy allows it, otherwise
            `None`.
        """
        if candidate_value is None:
            return None
        if module_name not in self.enabled_modules:
            return None
        effective_profile_depth = target_profile_depth or existing_character.profile_depth
        if effective_profile_depth is ProfileDepth.CORE:
            return None
        return candidate_value

    def _promote_profile_depth(
        self,
        candidate: CharacterCandidate,
        existing_character: Character,
    ) -> ProfileDepth | None:
        """Promote profile depth only when the candidate is explicitly richer.

        Args:
            candidate: Fresh discovery candidate extracted from new text.
            existing_character: Canonical character already stored in the
                knowledge base.

        Returns:
            A richer profile depth when the new evidence justifies promotion,
            otherwise `None`.
        """
        if candidate.profile_depth is None:
            return None
        order = {
            ProfileDepth.CORE: 0,
            ProfileDepth.STANDARD: 1,
            ProfileDepth.EXPANDED: 2,
        }
        return (
            candidate.profile_depth
            if order[candidate.profile_depth] > order[existing_character.profile_depth]
            else None
        )

    def _choose_salient_concept(
        self,
        candidate: CharacterCandidate,
        existing_character: Character,
    ) -> str | None:
        """Refresh the compressed summary only when policy and evidence allow it.

        Args:
            candidate: Fresh discovery candidate extracted from new text.
            existing_character: Canonical character already stored in the
                knowledge base.

        Returns:
            A replacement summary string when policy allows a refresh,
            otherwise `None`.
        """
        if candidate.salient_concept is None:
            return None
        if existing_character.salient_concept is None:
            return candidate.salient_concept
        if existing_character.profile_depth is ProfileDepth.EXPANDED:
            return candidate.salient_concept
        return None

    def _new_strings(self, new_values: list[str], existing_values: list[str]) -> list[str]:
        """Return only normalized values not already owned by the character.

        Args:
            new_values: Candidate strings extracted from fresh text.
            existing_values: Strings already stored on the canonical record.

        Returns:
            Newly introduced normalized strings that should be appended to the
            canonical record.
        """
        existing_lookup = {value.lower() for value in normalize_unique_strings(existing_values)}
        return [
            value
            for value in normalize_unique_strings(new_values)
            if value.lower() not in existing_lookup
        ]

    def _has_patch_data(self, patch: CharacterUpdateCandidate) -> bool:
        """Return `True` when the patch would change canonical state.

        Args:
            patch: Candidate recurring-character patch to inspect.

        Returns:
            `True` when the patch contains at least one durable change,
            otherwise `False`.
        """
        return any(
            (
                patch.profile_depth is not None,
                bool(patch.aliases_to_add),
                patch.salient_concept is not None,
                bool(patch.stable_tendencies_to_add),
                patch.identity is not None,
                patch.background is not None,
                patch.motivation is not None,
                patch.capabilities is not None,
                patch.conditions is not None,
                patch.social is not None,
                patch.appearance is not None,
                patch.system_stats is not None,
                bool(patch.metadata_updates),
            )
        )
