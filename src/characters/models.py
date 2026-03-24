"""Data models and normalization helpers for the character domain.

The character system is intentionally split into a tiny always-present core and
optional profile modules. Most characters in a novel do not deserve a full
biography-shaped schema, while a small subset of recurring characters benefit
from richer modeling over a long project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


def normalize_name(value: str) -> str:
    """Return a whitespace-normalized string.

    Args:
        value: Raw text that may contain leading, trailing, or repeated spaces.

    Returns:
        The same text with surrounding whitespace removed and internal whitespace
        collapsed to single spaces.
    """
    return " ".join(value.strip().split())


def normalize_unique_strings(values: list[str]) -> list[str]:
    """Return normalized unique strings while preserving input order.

    Args:
        values: Raw string values that may contain duplicates or inconsistent
            spacing/casing.

    Returns:
        A list of normalized strings with empty values removed and duplicates
        collapsed case-insensitively.
    """
    seen: set[str] = set()
    normalized_values: list[str] = []

    for value in values:
        normalized = normalize_name(value)
        lookup = normalized.lower()
        if normalized and lookup not in seen:
            seen.add(lookup)
            normalized_values.append(normalized)

    return normalized_values


class ProfileDepth(str, Enum):
    """Operational modeling budget for a character profile.

    This is intentionally not a narrative-importance field. It tells the system
    how much canonical profile detail should be maintained and fed back into
    downstream prompting.
    """

    CORE = "core"
    STANDARD = "standard"
    EXPANDED = "expanded"


@dataclass(slots=True)
class CharacterCore:
    """The minimum canonical record that every character should carry."""

    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    salient_concept: str | None = None
    stable_tendencies: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IdentityProfile:
    """Identity facts that are durable but not required for every character."""

    age_band: str | None = None
    gender: str | None = None
    origin: str | None = None
    culture: str | None = None
    species: str | None = None


@dataclass(slots=True)
class BackgroundProfile:
    """Background context that explains how the character was formed."""

    family_context: str | None = None
    upbringing: str | None = None
    training: list[str] = field(default_factory=list)
    formative_events: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MotivationProfile:
    """Long-lived internal push/pull structure for behavior generation."""

    drives: list[str] = field(default_factory=list)
    reward_profile: list[str] = field(default_factory=list)
    stress_profile: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CapabilityProfile:
    """Qualitative strengths and limits rather than game-like point values."""

    cognitive: list[str] = field(default_factory=list)
    social: list[str] = field(default_factory=list)
    physical: list[str] = field(default_factory=list)
    practical: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConditionProfile:
    """Persistent burdens, fragilities, or limitations worth carrying forward."""

    persistent_conditions: list[str] = field(default_factory=list)
    vulnerabilities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SocialProfile:
    """Durable placement in the setting's social and institutional structures."""

    class_status: str | None = None
    rank: str | None = None
    faction: str | None = None
    occupation: str | None = None
    obligations: list[str] = field(default_factory=list)
    reputation: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppearanceProfile:
    """Visible presentation that matters to continuity or social reaction."""

    summary: str | None = None
    distinguishing_features: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SystemStatsProfile:
    """Optional LitRPG/game-system module kept out of baseline fiction models."""

    attributes: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    skills: dict[str, Any] = field(default_factory=dict)
    progression: dict[str, Any] = field(default_factory=dict)
    rules_context: str | None = None


@dataclass(slots=True, init=False)
class Character:
    """Canonical aggregate root for one fictional person.

    The core fields are always present because they are cheap to store and cheap
    to prompt with. Optional modules are progressively attached only when the
    project actually needs them. For deep profiles, the modules are the source
    of truth and the core acts as a compressed retrieval surface.
    """

    id: str
    core: CharacterCore
    profile_depth: ProfileDepth
    identity: IdentityProfile | None = None
    background: BackgroundProfile | None = None
    motivation: MotivationProfile | None = None
    capabilities: CapabilityProfile | None = None
    conditions: ConditionProfile | None = None
    social: SocialProfile | None = None
    appearance: AppearanceProfile | None = None
    system_stats: SystemStatsProfile | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __init__(
        self,
        id: str,
        core: CharacterCore | None = None,
        *,
        canonical_name: str | None = None,
        aliases: list[str] | None = None,
        salient_concept: str | None = None,
        stable_tendencies: list[str] | None = None,
        profile_depth: ProfileDepth,
        identity: IdentityProfile | None = None,
        background: BackgroundProfile | None = None,
        motivation: MotivationProfile | None = None,
        capabilities: CapabilityProfile | None = None,
        conditions: ConditionProfile | None = None,
        social: SocialProfile | None = None,
        appearance: AppearanceProfile | None = None,
        system_stats: SystemStatsProfile | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        """Initialize a character from the new aggregate form or shorthand core fields.

        Args:
            id: Stable canonical identifier for the character.
            core: Preferred prebuilt core record.
            canonical_name: Shorthand canonical name used when `core` is omitted.
            aliases: Shorthand aliases used when `core` is omitted.
            salient_concept: Shorthand prompt-cheap memory hook used when
                `core` is omitted.
            stable_tendencies: Shorthand durable tendency shortlist used when
                `core` is omitted.
            profile_depth: Explicit modeling budget for the character record.
            identity: Optional identity module.
            background: Optional background module.
            motivation: Optional motivation module.
            capabilities: Optional capability module.
            conditions: Optional persistent-conditions module.
            social: Optional durable social-placement module.
            appearance: Optional appearance module.
            system_stats: Optional LitRPG-style system module.
            metadata: Optional extension data owned by callers.
            created_at: Optional preexisting creation timestamp.
            updated_at: Optional preexisting update timestamp.

        Raises:
            ValueError: If neither `core` nor `canonical_name` is provided, or
                if both the aggregate and shorthand paths are provided at once.
        """
        if core is None:
            if canonical_name is None:
                raise ValueError("Character requires either `core` or `canonical_name`.")
            core = CharacterCore(
                canonical_name=canonical_name,
                aliases=list(aliases or []),
                salient_concept=salient_concept,
                stable_tendencies=list(stable_tendencies or []),
            )
        elif canonical_name is not None:
            raise ValueError("Pass either `core` or shorthand core fields, not both.")

        now = datetime.now(UTC)
        self.id = id
        self.core = core
        self.profile_depth = profile_depth
        self.identity = identity
        self.background = background
        self.motivation = motivation
        self.capabilities = capabilities
        self.conditions = conditions
        self.social = social
        self.appearance = appearance
        self.system_stats = system_stats
        self.metadata = dict(metadata or {})
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @property
    def canonical_name(self) -> str:
        """Compatibility view over the canonical name stored in `core`."""
        return self.core.canonical_name

    @canonical_name.setter
    def canonical_name(self, value: str) -> None:
        self.core.canonical_name = value

    @property
    def aliases(self) -> list[str]:
        """Compatibility view over aliases stored in `core`."""
        return self.core.aliases

    @aliases.setter
    def aliases(self, value: list[str]) -> None:
        self.core.aliases = value

    @property
    def salient_concept(self) -> str | None:
        """Return the short memory hook used for prompt-cheap retrieval."""
        return self.core.salient_concept

    @salient_concept.setter
    def salient_concept(self, value: str | None) -> None:
        self.core.salient_concept = value

    @property
    def stable_tendencies(self) -> list[str]:
        """Return the durable behavioral anchors stored in `core`."""
        return self.core.stable_tendencies

    @stable_tendencies.setter
    def stable_tendencies(self, value: list[str]) -> None:
        self.core.stable_tendencies = value


@dataclass(slots=True)
class CharacterCandidate:
    """Proposed character data from a discovery extractor.

    Candidates stay sparse on purpose. The extractor should summarize what the
    text supports directly, not attempt to build a full encyclopedia entry for
    every mentioned person.
    """

    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    profile_depth: ProfileDepth | None = None
    salient_concept: str | None = None
    stable_tendencies: list[str] = field(default_factory=list)
    identity: IdentityProfile | None = None
    background: BackgroundProfile | None = None
    motivation: MotivationProfile | None = None
    capabilities: CapabilityProfile | None = None
    conditions: ConditionProfile | None = None
    social: SocialProfile | None = None
    appearance: AppearanceProfile | None = None
    system_stats: SystemStatsProfile | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CharacterUpdateCandidate:
    """Patch proposal for a recurring character already in the knowledge base.

    Update candidates are intentionally additive and conservative. This keeps
    automatic later-volume updates from rewriting the canonical record too
    aggressively before the project has a human review UI.
    """

    character_id: str
    canonical_name: str
    profile_depth: ProfileDepth | None = None
    aliases_to_add: list[str] = field(default_factory=list)
    salient_concept: str | None = None
    stable_tendencies_to_add: list[str] = field(default_factory=list)
    identity: IdentityProfile | None = None
    background: BackgroundProfile | None = None
    motivation: MotivationProfile | None = None
    capabilities: CapabilityProfile | None = None
    conditions: ConditionProfile | None = None
    social: SocialProfile | None = None
    appearance: AppearanceProfile | None = None
    system_stats: SystemStatsProfile | None = None
    metadata_updates: dict[str, Any] = field(default_factory=dict)


class ResolutionDecision(str, Enum):
    """Decision produced by the resolver after matching a candidate."""

    CREATE = "create"
    UPDATE = "update"
    AMBIGUOUS = "ambiguous"


@dataclass(slots=True)
class CharacterResolution:
    """Entity-resolution result connecting a candidate to existing canon."""

    decision: ResolutionDecision
    candidate: CharacterCandidate
    matched_character_id: str | None = None
    matched_character_name: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class VolumePreparationEntry:
    """Optional volume-scoped hint for important characters in the current run.

    This is intentionally lighter than a full narrative-function model. The
    file helps the workflow prioritize likely major characters for the current
    volume without turning story planning into a hard whitelist.
    """

    character_id: str | None = None
    canonical_name: str | None = None
    aliases: list[str] = field(default_factory=list)
    protagonist: bool = False
    viewpoint: bool = False
    volume_salience: str | None = None


@dataclass(slots=True)
class VolumePreparation:
    """Human-authored input that scopes the current volume's important cast."""

    known_characters: list[VolumePreparationEntry] = field(default_factory=list)
