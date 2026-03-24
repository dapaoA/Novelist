"""End-to-end character knowledge workflow for novel runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.characters.interfaces import CharacterExtractor, CharacterResolver, CharacterUpdateExtractor
from src.characters.knowledge import (
    INPUT_VOLUME_PREPARATION_PATH,
    INPUT_KNOWLEDGE_DIR,
    INTERMEDIATE_KNOWLEDGE_DIR,
    load_volume_preparation,
    load_characters_from_knowledge_dir,
    save_ambiguous_resolutions_to_knowledge_dir,
    save_characters_to_knowledge_dir,
    save_discovered_candidates_to_knowledge_dir,
)
from src.characters.models import (
    Character,
    CharacterCandidate,
    CharacterResolution,
    ProfileDepth,
    ResolutionDecision,
    VolumePreparation,
    VolumePreparationEntry,
)
from src.characters.resolver import SimpleCharacterResolver
from src.characters.service import CharacterService
from src.characters.stores import InMemoryCharacterStore
from src.characters.updater import SimpleCharacterUpdateExtractor


@dataclass(slots=True)
class CharacterKnowledgeWorkflowResult:
    """Summarize what the workflow changed during a novel run."""

    loaded_characters: list[Character] = field(default_factory=list)
    volume_preparation: VolumePreparation | None = None
    preparation_warnings: list[str] = field(default_factory=list)
    created_characters: list[Character] = field(default_factory=list)
    updated_characters: list[Character] = field(default_factory=list)
    discovered_candidates: list[CharacterCandidate] = field(default_factory=list)
    resolutions: list[CharacterResolution] = field(default_factory=list)
    ambiguous_resolutions: list[CharacterResolution] = field(default_factory=list)
    snapshot_path: Path | None = None
    ambiguous_report_path: Path | None = None
    discovered_candidates_path: Path | None = None


class CharacterKnowledgeWorkflow:
    """Coordinate discovery, resolution, updates, and snapshot export.

    The workflow is intentionally lightweight for the current terminal-only
    environment. It auto-applies proposals, but it already keeps extraction,
    resolution, and patch generation as separate steps so the future IDE can
    insert a human review layer without rewriting the pipeline.
    """

    def __init__(
        self,
        *,
        discovery_extractor: CharacterExtractor | None = None,
        update_extractor: CharacterUpdateExtractor | None = None,
        resolver: CharacterResolver | None = None,
        input_knowledge_dir: str | Path = INPUT_KNOWLEDGE_DIR,
        volume_preparation_path: str | Path = INPUT_VOLUME_PREPARATION_PATH,
        snapshot_knowledge_dir: str | Path = INTERMEDIATE_KNOWLEDGE_DIR,
        default_profile_depth: ProfileDepth = ProfileDepth.CORE,
    ) -> None:
        """Initialize the workflow with pluggable pipeline stages.

        Args:
            discovery_extractor: Optional discovery extractor override.
            update_extractor: Optional recurring-character updater override.
            resolver: Optional identity-resolution strategy override.
            input_knowledge_dir: Human-editable knowledge directory imported at
                the start of the run.
            volume_preparation_path: Optional volume-scoped preparation file
                that gives the resolver a strong prior over important
                characters for the current run.
            snapshot_knowledge_dir: Machine-written snapshot directory exported
                at the end of the run.
            default_profile_depth: Profile depth assigned to newly discovered
                characters when the discovery candidate does not override it.
        """
        self.input_knowledge_dir = Path(input_knowledge_dir)
        self.volume_preparation_path = Path(volume_preparation_path)
        self.snapshot_knowledge_dir = Path(snapshot_knowledge_dir)
        self.default_profile_depth = default_profile_depth
        self.store = InMemoryCharacterStore()
        self.service = CharacterService(self.store)
        self._loaded_characters_cache: list[Character] | None = None
        self._volume_preparation_loaded = False
        self._volume_preparation_cache: VolumePreparation | None = None
        if discovery_extractor is None:
            from src.characters.extractor import LangChainCharacterExtractor

            discovery_extractor = LangChainCharacterExtractor()
        self.discovery_extractor = discovery_extractor
        self.update_extractor = update_extractor or SimpleCharacterUpdateExtractor(
            enabled_modules={"core", "capabilities", "conditions", "social", "appearance"}
        )
        self.resolver = resolver or SimpleCharacterResolver()

    def process_text(self, text: str) -> CharacterKnowledgeWorkflowResult:
        """Import prior knowledge, process fresh text, and export a snapshot.

        Args:
            text: Fresh novel-related text to scan for character knowledge.

        Returns:
            A structured summary of imported knowledge, created records,
            applied updates, resolution decisions, and the exported snapshot.
        """
        loaded_characters = self._load_existing_knowledge()
        volume_preparation = self._load_volume_preparation()
        prepared_characters, preparation_warnings = self._resolve_prepared_characters(volume_preparation)
        created_characters: list[Character] = []
        updated_characters: list[Character] = []
        discovered_candidates: list[CharacterCandidate] = []
        resolutions: list[CharacterResolution] = []
        ambiguous_resolutions: list[CharacterResolution] = []

        for candidate in self.discovery_extractor.extract(text):
            resolution = self._resolve_candidate(candidate, prepared_characters)
            resolutions.append(resolution)

            if resolution.decision is ResolutionDecision.CREATE:
                discovered_candidates.append(candidate)
                created_characters.append(
                    self.service.create_character_from_candidate(
                        candidate,
                        profile_depth=self.default_profile_depth,
                    )
                )
                continue

            if resolution.decision is ResolutionDecision.UPDATE:
                existing_character = self.service.get_character_by_id(resolution.matched_character_id or "")
                if existing_character is None:
                    continue
                update_candidate = self.update_extractor.propose_update(candidate, existing_character)
                if update_candidate is None:
                    continue
                updated_characters.append(self.service.apply_update_candidate(update_candidate))
                continue

            if resolution.decision is ResolutionDecision.AMBIGUOUS:
                ambiguous_resolutions.append(resolution)

        snapshot_path = save_characters_to_knowledge_dir(
            self.service.list_characters(),
            self.snapshot_knowledge_dir,
        )
        ambiguous_report_path = save_ambiguous_resolutions_to_knowledge_dir(
            ambiguous_resolutions,
            self.snapshot_knowledge_dir,
        )
        discovered_candidates_path = save_discovered_candidates_to_knowledge_dir(
            discovered_candidates,
            self.snapshot_knowledge_dir,
        )
        return CharacterKnowledgeWorkflowResult(
            loaded_characters=loaded_characters,
            volume_preparation=volume_preparation,
            preparation_warnings=preparation_warnings,
            created_characters=created_characters,
            updated_characters=updated_characters,
            discovered_candidates=discovered_candidates,
            resolutions=resolutions,
            ambiguous_resolutions=ambiguous_resolutions,
            snapshot_path=snapshot_path,
            ambiguous_report_path=ambiguous_report_path,
            discovered_candidates_path=discovered_candidates_path,
        )

    def _load_existing_knowledge(self) -> list[Character]:
        """Import editable knowledge from `input/knowledge` when present.

        Returns:
            The list of imported canonical characters loaded for this run.

        Raises:
            ValueError: If an imported character violates canonical validation
                rules such as duplicate names or aliases.
        """
        if self._loaded_characters_cache is not None:
            return list(self._loaded_characters_cache)

        characters = load_characters_from_knowledge_dir(self.input_knowledge_dir)
        for character in characters:
            # Imported knowledge is user-editable, so it must pass through the
            # service layer instead of bypassing canonical validation rules.
            self.service.import_character(character)
        self._loaded_characters_cache = list(characters)
        return list(characters)

    def _load_volume_preparation(self) -> VolumePreparation | None:
        """Load optional volume-scoped preparation input once per workflow.

        Returns:
            The parsed volume-preparation model when present, otherwise `None`.
        """
        if self._volume_preparation_loaded:
            return self._volume_preparation_cache

        self._volume_preparation_cache = load_volume_preparation(self.volume_preparation_path)
        self._volume_preparation_loaded = True
        return self._volume_preparation_cache

    def _resolve_prepared_characters(
        self,
        volume_preparation: VolumePreparation | None,
    ) -> tuple[list[Character], list[str]]:
        """Map preparation entries onto canonical characters already in storage.

        Args:
            volume_preparation: Optional human-authored preparation input for
                the current run.

        Returns:
            A tuple containing:
            - canonical characters referenced by the preparation file
            - non-fatal warnings for preparation entries that could not be
              linked to imported canonical knowledge
        """
        if volume_preparation is None:
            return [], []

        prepared_characters: list[Character] = []
        prepared_ids: set[str] = set()
        warnings: list[str] = []

        for entry in volume_preparation.known_characters:
            character = self._resolve_preparation_entry(entry)
            if character is None:
                warnings.append(
                    "Volume preparation entry could not be matched to imported knowledge: "
                    f"{self._describe_preparation_entry(entry)}"
                )
                continue
            if character.id not in prepared_ids:
                prepared_ids.add(character.id)
                prepared_characters.append(character)

        return prepared_characters, warnings

    def _resolve_preparation_entry(self, entry: VolumePreparationEntry) -> Character | None:
        """Resolve one preparation entry to a canonical character when possible.

        Args:
            entry: Volume-preparation entry to resolve against imported canon.

        Returns:
            The matching canonical character when found, otherwise `None`.
        """
        if entry.character_id is not None:
            character = self.service.get_character_by_id(entry.character_id)
            if character is not None:
                return character

        if entry.canonical_name is not None:
            character = self.service.find_character(entry.canonical_name)
            if character is not None:
                return character

        for alias in entry.aliases:
            character = self.service.find_character(alias)
            if character is not None:
                return character

        return None

    def _resolve_candidate(
        self,
        candidate: CharacterCandidate,
        prepared_characters: list[Character],
    ) -> CharacterResolution:
        """Resolve a candidate with optional preference for prepared characters.

        Args:
            candidate: Discovery candidate extracted from the generated text.
            prepared_characters: Canonical characters explicitly referenced by
                `input/volume_preparation.json`.

        Returns:
            A final resolution result used by the create/update workflow.
        """
        if prepared_characters:
            preferred_resolution = self.resolver.resolve(candidate, prepared_characters)
            if preferred_resolution.decision is not ResolutionDecision.CREATE:
                preferred_resolution.reason = (
                    "Resolved against the volume preparation shortlist. "
                    f"{preferred_resolution.reason or ''}"
                ).strip()
                return preferred_resolution

        return self.resolver.resolve(candidate, self.service.list_characters())

    def _describe_preparation_entry(self, entry: VolumePreparationEntry) -> str:
        """Build a compact label for warnings about unresolved preparation data.

        Args:
            entry: Preparation entry that failed to match imported knowledge.

        Returns:
            A short human-readable label for logs and workflow summaries.
        """
        parts = [
            value
            for value in (entry.character_id, entry.canonical_name, ", ".join(entry.aliases))
            if value
        ]
        return " / ".join(parts) if parts else "<unnamed preparation entry>"
