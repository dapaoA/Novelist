"""JSON import/export helpers for the character knowledge base."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from src.characters.models import (
    AppearanceProfile,
    BackgroundProfile,
    CapabilityProfile,
    Character,
    CharacterCandidate,
    CharacterCore,
    CharacterResolution,
    ConditionProfile,
    IdentityProfile,
    MotivationProfile,
    ProfileDepth,
    SocialProfile,
    SystemStatsProfile,
    VolumePreparation,
    VolumePreparationEntry,
    normalize_name,
    normalize_unique_strings,
)

INPUT_KNOWLEDGE_DIR = Path("input/knowledge")
INPUT_VOLUME_PREPARATION_PATH = Path("input/volume_preparation.json")
INTERMEDIATE_KNOWLEDGE_DIR = Path("intermediate/knowledge")
CHARACTERS_FILENAME = "characters.json"
VOLUME_PREPARATION_FILENAME = "volume_preparation.json"
AMBIGUOUS_RESOLUTIONS_FILENAME = "ambiguous_resolutions.json"
DISCOVERED_CANDIDATES_FILENAME = "discovered_candidates.json"


def load_characters_from_knowledge_dir(directory: str | Path) -> list[Character]:
    """Load canonical characters from a knowledge directory if it exists.

    Args:
        directory: Directory that may contain the persisted character JSON file.

    Returns:
        A list of canonical characters loaded from disk, or an empty list when
        the knowledge file does not exist yet.

    Raises:
        ValueError: If the knowledge file exists but does not contain the
            expected top-level JSON array.
    """
    path = Path(directory) / CHARACTERS_FILENAME
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("Character knowledge file must contain a JSON array.")
    return [character_from_dict(item) for item in payload]


def save_characters_to_knowledge_dir(
    characters: list[Character],
    directory: str | Path,
) -> Path:
    """Persist canonical characters as a JSON snapshot in a knowledge directory.

    Args:
        characters: Canonical character records to serialize.
        directory: Destination directory for the knowledge snapshot.

    Returns:
        The full path to the written JSON snapshot file.
    """
    path = Path(directory) / CHARACTERS_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(
            [character_to_dict(character) for character in characters],
            file,
            ensure_ascii=False,
            indent=2,
        )
    return path


def load_volume_preparation(path: str | Path) -> VolumePreparation | None:
    """Load optional volume-scoped preparation input for the current run.

    Args:
        path: File path that may contain the JSON preparation payload.

    Returns:
        The parsed preparation model when the file exists, otherwise `None`.

    Raises:
        ValueError: If the file exists but does not contain the expected JSON
            object structure.
    """
    preparation_path = Path(path)
    if not preparation_path.exists():
        return None
    with preparation_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError("Volume preparation file must contain a JSON object.")
    return volume_preparation_from_dict(payload)


def save_ambiguous_resolutions_to_knowledge_dir(
    resolutions: list[CharacterResolution],
    directory: str | Path,
) -> Path:
    """Persist ambiguous identity-resolution results for manual inspection.

    Args:
        resolutions: Ambiguous resolution results collected during the run.
        directory: Destination knowledge directory for the JSON report.

    Returns:
        The full path to the written ambiguity report.
    """
    return _save_json_report(
        [resolution_to_dict(resolution) for resolution in resolutions],
        Path(directory) / AMBIGUOUS_RESOLUTIONS_FILENAME,
    )


def save_discovered_candidates_to_knowledge_dir(
    candidates: list[CharacterCandidate],
    directory: str | Path,
) -> Path:
    """Persist newly discovered candidates for post-run inspection.

    Args:
        candidates: Candidates that the workflow treated as new characters.
        directory: Destination knowledge directory for the JSON report.

    Returns:
        The full path to the written discovery report.
    """
    return _save_json_report(
        [candidate_to_dict(candidate) for candidate in candidates],
        Path(directory) / DISCOVERED_CANDIDATES_FILENAME,
    )


def character_to_dict(character: Character) -> dict[str, Any]:
    """Serialize a canonical character into a stable JSON-ready dictionary.

    Args:
        character: Canonical character record to serialize.

    Returns:
        A JSON-ready dictionary that preserves the aggregate structure.
    """
    return {
        "id": character.id,
        "profile_depth": character.profile_depth.value,
        "core": asdict(character.core),
        "identity": _optional_profile_to_dict(character.identity),
        "background": _optional_profile_to_dict(character.background),
        "motivation": _optional_profile_to_dict(character.motivation),
        "capabilities": _optional_profile_to_dict(character.capabilities),
        "conditions": _optional_profile_to_dict(character.conditions),
        "social": _optional_profile_to_dict(character.social),
        "appearance": _optional_profile_to_dict(character.appearance),
        "system_stats": _optional_profile_to_dict(character.system_stats),
        "metadata": dict(character.metadata),
        "created_at": character.created_at.isoformat(),
        "updated_at": character.updated_at.isoformat(),
    }


def character_from_dict(payload: dict[str, Any]) -> Character:
    """Deserialize a canonical character from JSON knowledge storage.

    Args:
        payload: JSON dictionary previously produced by `character_to_dict`.

    Returns:
        The reconstructed canonical character record.
    """
    return Character(
        id=payload["id"],
        core=CharacterCore(**payload["core"]),
        profile_depth=ProfileDepth(payload["profile_depth"]),
        identity=_optional_profile_from_dict(IdentityProfile, payload.get("identity")),
        background=_optional_profile_from_dict(BackgroundProfile, payload.get("background")),
        motivation=_optional_profile_from_dict(MotivationProfile, payload.get("motivation")),
        capabilities=_optional_profile_from_dict(CapabilityProfile, payload.get("capabilities")),
        conditions=_optional_profile_from_dict(ConditionProfile, payload.get("conditions")),
        social=_optional_profile_from_dict(SocialProfile, payload.get("social")),
        appearance=_optional_profile_from_dict(AppearanceProfile, payload.get("appearance")),
        system_stats=_optional_profile_from_dict(SystemStatsProfile, payload.get("system_stats")),
        metadata=dict(payload.get("metadata", {})),
        created_at=_parse_datetime(payload.get("created_at")),
        updated_at=_parse_datetime(payload.get("updated_at")),
    )


def candidate_to_dict(candidate: CharacterCandidate) -> dict[str, Any]:
    """Serialize a discovery candidate into a stable JSON-ready dictionary.

    Args:
        candidate: Discovery candidate to serialize.

    Returns:
        A JSON-ready dictionary representing the candidate payload.
    """
    return {
        "canonical_name": candidate.canonical_name,
        "aliases": list(candidate.aliases),
        "profile_depth": candidate.profile_depth.value if candidate.profile_depth is not None else None,
        "salient_concept": candidate.salient_concept,
        "stable_tendencies": list(candidate.stable_tendencies),
        "identity": _optional_profile_to_dict(candidate.identity),
        "background": _optional_profile_to_dict(candidate.background),
        "motivation": _optional_profile_to_dict(candidate.motivation),
        "capabilities": _optional_profile_to_dict(candidate.capabilities),
        "conditions": _optional_profile_to_dict(candidate.conditions),
        "social": _optional_profile_to_dict(candidate.social),
        "appearance": _optional_profile_to_dict(candidate.appearance),
        "system_stats": _optional_profile_to_dict(candidate.system_stats),
        "metadata": dict(candidate.metadata),
    }


def resolution_to_dict(resolution: CharacterResolution) -> dict[str, Any]:
    """Serialize an identity-resolution result into a JSON-ready dictionary.

    Args:
        resolution: Identity-resolution result to serialize.

    Returns:
        A JSON-ready dictionary that preserves the decision and evidence.
    """
    return {
        "decision": resolution.decision.value,
        "candidate": candidate_to_dict(resolution.candidate),
        "matched_character_id": resolution.matched_character_id,
        "matched_character_name": resolution.matched_character_name,
        "reason": resolution.reason,
    }


def volume_preparation_from_dict(payload: dict[str, Any]) -> VolumePreparation:
    """Deserialize a volume-preparation file into a structured model.

    Args:
        payload: Parsed JSON object from `input/volume_preparation.json`.

    Returns:
        The reconstructed volume-preparation model.

    Raises:
        ValueError: If the payload does not contain the expected list of
            `known_characters`.
    """
    known_characters_payload = payload.get("known_characters", [])
    if not isinstance(known_characters_payload, list):
        raise ValueError("`known_characters` must be a JSON array.")

    known_characters: list[VolumePreparationEntry] = []
    for item in known_characters_payload:
        if not isinstance(item, dict):
            raise ValueError("Each volume-preparation character entry must be a JSON object.")
        known_characters.append(
            VolumePreparationEntry(
                character_id=_normalize_optional_text(item.get("character_id")),
                canonical_name=_normalize_optional_text(item.get("canonical_name")),
                aliases=normalize_unique_strings(item.get("aliases", []) or []),
                protagonist=bool(item.get("protagonist", False)),
                viewpoint=bool(item.get("viewpoint", False)),
                volume_salience=_normalize_optional_text(item.get("volume_salience")),
            )
        )

    return VolumePreparation(known_characters=known_characters)


def _optional_profile_to_dict(profile: object | None) -> dict[str, Any] | None:
    """Serialize an optional nested dataclass profile when present.

    Args:
        profile: Optional nested profile dataclass.

    Returns:
        A JSON-ready dictionary when a profile is present, otherwise `None`.
    """
    if profile is None:
        return None
    return asdict(profile)


def _save_json_report(payload: list[dict[str, Any]], path: Path) -> Path:
    """Write a JSON report file under the intermediate knowledge directory.

    Args:
        payload: JSON-ready list payload to write.
        path: Destination file path for the report.

    Returns:
        The written report path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return path


def _optional_profile_from_dict(profile_cls: type, payload: dict[str, Any] | None) -> object | None:
    """Deserialize an optional nested dataclass profile when present.

    Args:
        profile_cls: Dataclass type used to rebuild the nested profile.
        payload: Serialized profile dictionary, if present.

    Returns:
        The reconstructed nested profile, or `None` when no payload exists.
    """
    if payload is None:
        return None
    return profile_cls(**payload)


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse persisted timestamps while tolerating older snapshot omissions.

    Args:
        value: ISO 8601 timestamp string or `None` for older snapshots.

    Returns:
        A parsed `datetime` value, or `None` when the timestamp was omitted.
    """
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _normalize_optional_text(value: Any) -> str | None:
    """Normalize optional string values loaded from JSON input.

    Args:
        value: Raw JSON value that may contain `None`, empty text, or a string.

    Returns:
        A normalized string or `None` when the value is absent or blank.
    """
    if value is None:
        return None
    normalized = normalize_name(str(value))
    return normalized or None
