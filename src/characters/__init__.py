"""Character domain package."""

from importlib import import_module

from src.characters.interfaces import (
    CharacterExtractor,
    CharacterResolver,
    CharacterStore,
    CharacterUpdateExtractor,
)
from src.characters.knowledge import (
    AMBIGUOUS_RESOLUTIONS_FILENAME,
    CHARACTERS_FILENAME,
    DISCOVERED_CANDIDATES_FILENAME,
    INPUT_KNOWLEDGE_DIR,
    INPUT_VOLUME_PREPARATION_PATH,
    INTERMEDIATE_KNOWLEDGE_DIR,
    load_volume_preparation,
    load_characters_from_knowledge_dir,
    save_ambiguous_resolutions_to_knowledge_dir,
    save_characters_to_knowledge_dir,
    save_discovered_candidates_to_knowledge_dir,
)
from src.characters.models import (
    AppearanceProfile,
    BackgroundProfile,
    CapabilityProfile,
    Character,
    CharacterCandidate,
    CharacterCore,
    CharacterResolution,
    CharacterUpdateCandidate,
    ConditionProfile,
    IdentityProfile,
    MotivationProfile,
    ProfileDepth,
    ResolutionDecision,
    SocialProfile,
    SystemStatsProfile,
    VolumePreparation,
    VolumePreparationEntry,
)
from src.characters.resolver import SimpleCharacterResolver
from src.characters.service import CharacterService
from src.characters.updater import SimpleCharacterUpdateExtractor

__all__ = [
    "AppearanceProfile",
    "AMBIGUOUS_RESOLUTIONS_FILENAME",
    "BackgroundProfile",
    "CHARACTERS_FILENAME",
    "CapabilityProfile",
    "Character",
    "CharacterCandidate",
    "CharacterCore",
    "CharacterExtractor",
    "CharacterKnowledgeWorkflow",
    "CharacterKnowledgeWorkflowResult",
    "CharacterResolution",
    "CharacterService",
    "CharacterStore",
    "CharacterUpdateCandidate",
    "CharacterUpdateExtractor",
    "ConditionProfile",
    "DISCOVERED_CANDIDATES_FILENAME",
    "IdentityProfile",
    "INPUT_KNOWLEDGE_DIR",
    "INPUT_VOLUME_PREPARATION_PATH",
    "INTERMEDIATE_KNOWLEDGE_DIR",
    "LangChainCharacterExtractor",
    "MotivationProfile",
    "ProfileDepth",
    "ResolutionDecision",
    "SocialProfile",
    "SimpleCharacterResolver",
    "SimpleCharacterUpdateExtractor",
    "SystemStatsProfile",
    "CharacterResolver",
    "VolumePreparation",
    "VolumePreparationEntry",
    "load_volume_preparation",
    "load_characters_from_knowledge_dir",
    "save_ambiguous_resolutions_to_knowledge_dir",
    "save_characters_to_knowledge_dir",
    "save_discovered_candidates_to_knowledge_dir",
]

_LAZY_ATTRS = {
    "LangChainCharacterExtractor": ("src.characters.extractor", "LangChainCharacterExtractor"),
    "CharacterKnowledgeWorkflow": ("src.characters.workflow", "CharacterKnowledgeWorkflow"),
    "CharacterKnowledgeWorkflowResult": ("src.characters.workflow", "CharacterKnowledgeWorkflowResult"),
}


def __getattr__(name: str):
    """Lazily import heavy integrations so lightweight submodules stay cheap."""
    if name not in _LAZY_ATTRS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_ATTRS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
