"""Business logic for creating, updating, resolving, and merging characters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.characters.interfaces import CharacterStore
from src.characters.models import (
    AppearanceProfile,
    BackgroundProfile,
    CapabilityProfile,
    Character,
    CharacterCandidate,
    CharacterCore,
    CharacterUpdateCandidate,
    ConditionProfile,
    IdentityProfile,
    MotivationProfile,
    ProfileDepth,
    SocialProfile,
    SystemStatsProfile,
    normalize_name,
    normalize_unique_strings,
)

# Sentinel used to distinguish "field not provided" from "explicitly clear field".
_MISSING = object()


class CharacterService:
    """Coordinates validation and persistence for the character domain.

    The service owns business rules such as normalization, duplicate detection,
    alias collision checks, and merge behavior. Storage details stay behind the
    `CharacterStore` protocol.
    """

    def __init__(self, store: CharacterStore):
        """Initialize the service with a store implementation.

        Args:
            store: Persistence backend that satisfies the `CharacterStore`
                protocol.
        """
        self.store = store

    def create_character(
        self,
        canonical_name: str,
        aliases: list[str] | None = None,
        *,
        profile_depth: ProfileDepth | str | None = None,
        salient_concept: str | None = None,
        stable_tendencies: list[str] | None = None,
        identity: IdentityProfile | None = None,
        background: BackgroundProfile | None = None,
        motivation: MotivationProfile | None = None,
        capabilities: CapabilityProfile | None = None,
        conditions: ConditionProfile | None = None,
        social: SocialProfile | None = None,
        appearance: AppearanceProfile | None = None,
        system_stats: SystemStatsProfile | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Character:
        """Create and persist a new canonical character record.

        Args:
            canonical_name: Primary display name for the character.
            aliases: Alternate names that should resolve to the same character.
            profile_depth: Intended richness of the maintained profile. When
                omitted, the service infers a cheap default from the amount of
                supplied module data instead of hardcoding a schema-level value.
            salient_concept: Prompt-cheap memory hook for the character.
            stable_tendencies: Small set of durable behavioral anchors.
            identity: Optional identity module.
            background: Optional background module.
            motivation: Optional motivation module.
            capabilities: Optional capabilities module.
            conditions: Optional persistent conditions module.
            social: Optional social placement module.
            appearance: Optional appearance module.
            system_stats: Optional LitRPG/systemized stats module.
            metadata: Optional structured extension data owned by callers.

        Returns:
            The created canonical character.

        Raises:
            ValueError: If the name is empty or if the name/aliases collide with
                an existing character.
        """
        normalized_name = self._require_name(canonical_name)
        normalized_aliases = normalize_unique_strings(aliases or [])
        self._ensure_name_is_available(normalized_name)
        self._ensure_aliases_are_available(normalized_aliases)

        now = datetime.now(UTC)
        character = Character(
            id=uuid4().hex,
            core=CharacterCore(
                canonical_name=normalized_name,
                aliases=self._remove_conflicting_alias(normalized_aliases, normalized_name),
                salient_concept=self._normalize_optional_text(salient_concept),
                stable_tendencies=normalize_unique_strings(stable_tendencies or []),
            ),
            profile_depth=self._resolve_profile_depth_for_create(
                profile_depth,
                identity=identity,
                background=background,
                motivation=motivation,
                capabilities=capabilities,
                conditions=conditions,
                social=social,
                appearance=appearance,
                system_stats=system_stats,
            ),
            identity=identity,
            background=background,
            motivation=motivation,
            capabilities=capabilities,
            conditions=conditions,
            social=social,
            appearance=appearance,
            system_stats=system_stats,
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )
        return self.store.create(character)

    def create_character_from_candidate(
        self,
        candidate: CharacterCandidate,
        *,
        profile_depth: ProfileDepth | str | None = None,
    ) -> Character:
        """Materialize a discovery candidate into canonical storage.

        Args:
            candidate: Sparse discovery result produced by an extractor.
            profile_depth: Optional workflow override for the candidate's target
                profile depth.

        Returns:
            The created canonical character record.

        The workflow layer uses this method so candidate-to-character mapping
        stays centralized in the service instead of being repeated by each
        orchestrator or importer.
        """
        resolved_profile_depth = (
            profile_depth
            if profile_depth is not None
            else candidate.profile_depth
        )
        return self.create_character(
            canonical_name=candidate.canonical_name,
            aliases=candidate.aliases,
            profile_depth=resolved_profile_depth,
            salient_concept=candidate.salient_concept,
            stable_tendencies=candidate.stable_tendencies,
            identity=candidate.identity,
            background=candidate.background,
            motivation=candidate.motivation,
            capabilities=candidate.capabilities,
            conditions=candidate.conditions,
            social=candidate.social,
            appearance=candidate.appearance,
            system_stats=candidate.system_stats,
            metadata=candidate.metadata,
        )

    def import_character(self, character: Character) -> Character:
        """Validate and import a prebuilt canonical character.

        Args:
            character: Canonical character loaded from an external knowledge
                snapshot and not yet trusted by the runtime store.

        Returns:
            The stored canonical character after normalization and validation.

        Raises:
            ValueError: If the imported character has an invalid name, alias
                collision, duplicate canonical name, or duplicate identifier.
        """
        normalized_name = self._require_name(character.canonical_name)
        normalized_aliases = normalize_unique_strings(character.aliases)
        self._ensure_name_is_available(normalized_name)
        self._ensure_aliases_are_available(normalized_aliases)

        character.canonical_name = normalized_name
        character.aliases = self._remove_conflicting_alias(normalized_aliases, normalized_name)
        character.salient_concept = self._normalize_optional_text(character.salient_concept)
        character.stable_tendencies = normalize_unique_strings(character.stable_tendencies)
        if character.profile_depth is None:
            raise ValueError(f"Imported character is missing profile depth: {character.id}")
        return self.store.create(character)

    def get_character_by_id(self, character_id: str) -> Character | None:
        """Fetch a character by its canonical identifier.

        Args:
            character_id: Unique identifier assigned to the character.

        Returns:
            The matching character if present, otherwise `None`.
        """
        return self.store.get_by_id(character_id)

    def find_character(self, name_or_alias: str) -> Character | None:
        """Resolve a character by canonical name first, then alias.

        Args:
            name_or_alias: User-facing name or alternate name to resolve.

        Returns:
            The matching character if present, otherwise `None`.

        Raises:
            ValueError: If the provided lookup string is empty after
                normalization.
        """
        normalized = self._require_name(name_or_alias)
        exact_match = self.store.get_by_canonical_name(normalized)
        if exact_match is not None:
            return exact_match
        return self.store.find_by_alias(normalized)

    def list_characters(self) -> list[Character]:
        """Return all known characters from the backing store.

        Returns:
            A list of canonical character records.
        """
        return self.store.list_all()

    def apply_update_candidate(self, update_candidate: CharacterUpdateCandidate) -> Character:
        """Apply a sparse recurring-character patch to canonical storage.

        Args:
            update_candidate: Conservative patch proposal for a recurring
                character that already exists in canonical storage.

        Returns:
            The updated canonical character after the patch is applied.

        Update candidates use additive fields such as `aliases_to_add` so the
        auto-update path can stay conservative until the future IDE exposes a
        richer review workflow.
        """
        character = self._require_character(update_candidate.character_id)
        next_aliases = self._filter_available_aliases(
            normalize_unique_strings([*character.aliases, *update_candidate.aliases_to_add]),
            owner_character_id=character.id,
        )
        next_tendencies = normalize_unique_strings(
            [*character.stable_tendencies, *update_candidate.stable_tendencies_to_add]
        )
        next_metadata = {**character.metadata, **update_candidate.metadata_updates}
        return self.update_character(
            character.id,
            aliases=next_aliases,
            profile_depth=update_candidate.profile_depth
            if update_candidate.profile_depth is not None
            else _MISSING,
            salient_concept=(
                update_candidate.salient_concept
                if update_candidate.salient_concept is not None
                else _MISSING
            ),
            stable_tendencies=next_tendencies,
            identity=update_candidate.identity if update_candidate.identity is not None else _MISSING,
            background=update_candidate.background if update_candidate.background is not None else _MISSING,
            motivation=update_candidate.motivation if update_candidate.motivation is not None else _MISSING,
            capabilities=update_candidate.capabilities if update_candidate.capabilities is not None else _MISSING,
            conditions=update_candidate.conditions if update_candidate.conditions is not None else _MISSING,
            social=update_candidate.social if update_candidate.social is not None else _MISSING,
            appearance=update_candidate.appearance if update_candidate.appearance is not None else _MISSING,
            system_stats=update_candidate.system_stats if update_candidate.system_stats is not None else _MISSING,
            metadata=next_metadata,
        )

    def update_character(
        self,
        character_id: str,
        *,
        canonical_name: str | None | object = _MISSING,
        aliases: list[str] | object = _MISSING,
        profile_depth: ProfileDepth | str | object = _MISSING,
        salient_concept: str | None | object = _MISSING,
        stable_tendencies: list[str] | object = _MISSING,
        identity: IdentityProfile | None | object = _MISSING,
        background: BackgroundProfile | None | object = _MISSING,
        motivation: MotivationProfile | None | object = _MISSING,
        capabilities: CapabilityProfile | None | object = _MISSING,
        conditions: ConditionProfile | None | object = _MISSING,
        social: SocialProfile | None | object = _MISSING,
        appearance: AppearanceProfile | None | object = _MISSING,
        system_stats: SystemStatsProfile | None | object = _MISSING,
        metadata: dict[str, Any] | None | object = _MISSING,
    ) -> Character:
        """Update selected fields on an existing character.

        Args:
            character_id: Identifier of the character to update.
            canonical_name: New canonical name. Omit to keep the current value.
            aliases: Replacement alias list. Omit to keep the current value.
            profile_depth: New modeling depth. Omit to keep the current value.
            salient_concept: New memory hook. Pass `None` to clear it.
            stable_tendencies: Replacement tendency list. Omit to keep the
                current value.
            identity: Replacement identity module. Pass `None` to clear it.
            background: Replacement background module. Pass `None` to clear it.
            motivation: Replacement motivation module. Pass `None` to clear it.
            capabilities: Replacement capabilities module. Pass `None` to clear it.
            conditions: Replacement conditions module. Pass `None` to clear it.
            social: Replacement social module. Pass `None` to clear it.
            appearance: Replacement appearance module. Pass `None` to clear it.
            system_stats: Replacement system-stats module. Pass `None` to clear it.
            metadata: Replacement metadata object. Pass `None` to clear it.

        Returns:
            The updated canonical character.

        Raises:
            ValueError: If the character does not exist, if the name is invalid,
                or if the update would cause a name or alias collision.
        """
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

        if profile_depth is not _MISSING:
            character.profile_depth = self._normalize_profile_depth(profile_depth)

        if salient_concept is not _MISSING:
            character.salient_concept = self._normalize_optional_text(salient_concept)

        if stable_tendencies is not _MISSING:
            character.stable_tendencies = normalize_unique_strings(stable_tendencies or [])

        if identity is not _MISSING:
            character.identity = identity
        if background is not _MISSING:
            character.background = background
        if motivation is not _MISSING:
            character.motivation = motivation
        if capabilities is not _MISSING:
            character.capabilities = capabilities
        if conditions is not _MISSING:
            character.conditions = conditions
        if social is not _MISSING:
            character.social = social
        if appearance is not _MISSING:
            character.appearance = appearance
        if system_stats is not _MISSING:
            character.system_stats = system_stats
        if metadata is not _MISSING:
            character.metadata = dict(metadata or {})

        character.updated_at = datetime.now(UTC)
        return self.store.update(character)

    def merge_characters(self, primary_character_id: str, duplicate_character_id: str) -> Character:
        """Merge a duplicate character into a primary canonical record.

        The merge strategy is intentionally shallow for the new optional modules.
        Until extraction and editing workflows understand those modules well,
        primary-module values win and missing primary modules are backfilled from
        the duplicate record.

        Args:
            primary_character_id: Identifier of the record to keep.
            duplicate_character_id: Identifier of the record to remove.

        Returns:
            The updated primary character after aliases and missing fields are
            merged in.

        Raises:
            ValueError: If either character does not exist, if both IDs are the
                same, or if the merged aliases would conflict with another
                character.
        """
        if primary_character_id == duplicate_character_id:
            raise ValueError("Cannot merge a character into itself.")

        primary = self._require_character(primary_character_id)
        duplicate = self._require_character(duplicate_character_id)

        merged_aliases = normalize_unique_strings(
            [*primary.aliases, duplicate.canonical_name, *duplicate.aliases]
        )
        merged_tendencies = normalize_unique_strings(
            [*primary.stable_tendencies, *duplicate.stable_tendencies]
        )
        merged_metadata = {**duplicate.metadata, **primary.metadata}

        primary.aliases = self._remove_conflicting_alias(merged_aliases, primary.canonical_name)
        primary.salient_concept = primary.salient_concept or duplicate.salient_concept
        primary.stable_tendencies = merged_tendencies
        primary.profile_depth = self._merge_profile_depth(primary.profile_depth, duplicate.profile_depth)
        primary.identity = primary.identity or duplicate.identity
        primary.background = primary.background or duplicate.background
        primary.motivation = primary.motivation or duplicate.motivation
        primary.capabilities = primary.capabilities or duplicate.capabilities
        primary.conditions = primary.conditions or duplicate.conditions
        primary.social = primary.social or duplicate.social
        primary.appearance = primary.appearance or duplicate.appearance
        primary.system_stats = primary.system_stats or duplicate.system_stats
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
        """Raise if a canonical name already resolves to another character.

        Args:
            canonical_name: Proposed canonical name to validate.
            ignore_character_id: Optional character ID allowed to own this name.

        Raises:
            ValueError: If another character already uses the same name or alias.
        """
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
        """Raise if any alias resolves to another character.

        Args:
            aliases: Proposed aliases to validate.
            ignore_character_id: Optional single character ID allowed to own the
                aliases.
            ignore_character_ids: Optional set of character IDs ignored during
                validation, useful during merges.

        Raises:
            ValueError: If any alias is already claimed by another character.
        """
        ignored_ids = set(ignore_character_ids or set())
        if ignore_character_id is not None:
            ignored_ids.add(ignore_character_id)
        for alias in aliases:
            existing = self.find_character(alias)
            if existing is not None and existing.id not in ignored_ids:
                raise ValueError(f"Alias already exists: {alias}")

    def _require_character(self, character_id: str) -> Character:
        """Return an existing character or raise if it is missing.

        Args:
            character_id: Identifier of the character to fetch.

        Returns:
            The matching character record.

        Raises:
            ValueError: If the character cannot be found.
        """
        character = self.store.get_by_id(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        return character

    def _require_name(self, value: str) -> str:
        """Normalize a name-like value and ensure it is not empty.

        Args:
            value: Raw name input.

        Returns:
            The normalized non-empty name.

        Raises:
            ValueError: If the normalized name is empty.
        """
        normalized = normalize_name(value)
        if not normalized:
            raise ValueError("Character name cannot be empty.")
        return normalized

    def _normalize_optional_text(self, value: str | None | object) -> str | None:
        """Normalize optional free-text fields.

        Args:
            value: Raw optional text, `None` to clear a field, or the internal
                `_MISSING` sentinel when a caller did not provide the field.

        Returns:
            A normalized string or `None`.

        Raises:
            ValueError: If the internal `_MISSING` sentinel is passed by mistake.
        """
        if value is None:
            return None
        if value is _MISSING:
            raise ValueError("Internal error: missing sentinel passed for normalization.")
        normalized = normalize_name(value)
        return normalized or None

    def _remove_conflicting_alias(self, aliases: list[str], canonical_name: str) -> list[str]:
        """Drop aliases that duplicate the canonical name.

        Args:
            aliases: Proposed alias list.
            canonical_name: Canonical display name for the same character.

        Returns:
            A filtered alias list that does not repeat the canonical name.
        """
        canonical_lookup = canonical_name.lower()
        return [alias for alias in aliases if alias.lower() != canonical_lookup]

    def _filter_available_aliases(
        self,
        aliases: list[str],
        *,
        owner_character_id: str,
    ) -> list[str]:
        """Keep only aliases that are unclaimed or already owned by the target.

        Args:
            aliases: Candidate alias list assembled for an update operation.
            owner_character_id: Character that will receive the aliases.

        Returns:
            A filtered alias list that drops aliases already claimed by another
            canonical character.

        The recurring-character update path is intentionally conservative. When
        a discovery candidate mixes in another character's surface form, the
        service prefers dropping the conflicting alias over aborting the entire
        patch.
        """
        filtered_aliases: list[str] = []
        for alias in aliases:
            existing = self.find_character(alias)
            if existing is None or existing.id == owner_character_id:
                filtered_aliases.append(alias)
        return filtered_aliases

    def _normalize_profile_depth(self, value: ProfileDepth | str | object) -> ProfileDepth:
        """Validate and normalize a profile-depth input.

        Args:
            value: Candidate profile depth from a workflow, candidate, or API.

        Returns:
            A normalized `ProfileDepth` enum value.

        Raises:
            ValueError: If the value is missing internally or does not map to a
                supported profile depth.
        """
        if value is _MISSING:
            raise ValueError("Internal error: missing sentinel passed for profile depth.")
        if isinstance(value, ProfileDepth):
            return value
        normalized = normalize_name(str(value)).lower()
        try:
            return ProfileDepth(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported profile depth: {value}") from exc

    def _resolve_profile_depth_for_create(
        self,
        value: ProfileDepth | str | None,
        *,
        identity: IdentityProfile | None,
        background: BackgroundProfile | None,
        motivation: MotivationProfile | None,
        capabilities: CapabilityProfile | None,
        conditions: ConditionProfile | None,
        social: SocialProfile | None,
        appearance: AppearanceProfile | None,
        system_stats: SystemStatsProfile | None,
    ) -> ProfileDepth:
        """Infer a profile depth only when the caller leaves it unspecified.

        Args:
            value: Explicit profile depth supplied by the caller, if any.
            identity: Optional identity module.
            background: Optional background module.
            motivation: Optional motivation module.
            capabilities: Optional capabilities module.
            conditions: Optional conditions module.
            social: Optional social module.
            appearance: Optional appearance module.
            system_stats: Optional LitRPG-style system module.

        Returns:
            A profile depth chosen from explicit caller policy or the presence
            of richer optional modules.

        The schema no longer hardcodes a universal default. Discovery-oriented
        workflows can explicitly pass `core`, while richer imports may omit the
        value and let the service promote records that already carry optional
        modules.
        """
        if value is not None:
            return self._normalize_profile_depth(value)
        has_optional_modules = any(
            module is not None
            for module in (
                identity,
                background,
                motivation,
                capabilities,
                conditions,
                social,
                appearance,
                system_stats,
            )
        )
        return ProfileDepth.STANDARD if has_optional_modules else ProfileDepth.CORE

    def _merge_profile_depth(self, left: ProfileDepth, right: ProfileDepth) -> ProfileDepth:
        """Return the richer of two profile depths.

        Args:
            left: First profile depth to compare.
            right: Second profile depth to compare.

        Returns:
            The richer of the two supplied profile depths.
        """
        order = {
            ProfileDepth.CORE: 0,
            ProfileDepth.STANDARD: 1,
            ProfileDepth.EXPANDED: 2,
        }
        return left if order[left] >= order[right] else right
