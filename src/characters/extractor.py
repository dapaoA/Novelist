"""LangChain-based character discovery extraction using structured output."""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.characters.interfaces import CharacterExtractor
from src.characters.models import (
    AppearanceProfile,
    CapabilityProfile,
    CharacterCandidate,
    ConditionProfile,
    SocialProfile,
    normalize_unique_strings,
)
from src.utils.config import get_api_base_url, get_api_key, get_model_name


class CapabilityProfilePayload(BaseModel):
    """Discovery-time subset of the capability module.

    Discovery stays conservative. These fields exist so the extractor can
    capture durable, explicit strengths or limitations without pretending to
    infer the whole long-term character model.
    """

    cognitive: list[str] = Field(default_factory=list)
    social: list[str] = Field(default_factory=list)
    physical: list[str] = Field(default_factory=list)
    practical: list[str] = Field(default_factory=list)


class ConditionProfilePayload(BaseModel):
    """Discovery-time subset of persistent conditions and vulnerabilities."""

    persistent_conditions: list[str] = Field(default_factory=list)
    vulnerabilities: list[str] = Field(default_factory=list)


class SocialProfilePayload(BaseModel):
    """Discovery-time subset of durable social placement fields."""

    class_status: str | None = None
    rank: str | None = None
    faction: str | None = None
    occupation: str | None = None
    obligations: list[str] = Field(default_factory=list)
    reputation: list[str] = Field(default_factory=list)


class AppearanceProfilePayload(BaseModel):
    """Discovery-time subset of the appearance module."""

    summary: str | None = None
    distinguishing_features: list[str] = Field(default_factory=list)


class CharacterCandidatePayload(BaseModel):
    """Structured output schema for a single discovered character candidate."""

    canonical_name: str = Field(
        description="Primary character name exactly as it should appear in the registry."
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternate names, nicknames, or titles that refer to the same character.",
    )
    salient_concept: str | None = Field(
        default=None,
        description="One-sentence memory hook summarizing who the character is in the text.",
    )
    stable_tendencies: list[str] = Field(
        default_factory=list,
        description="Two to four durable behavioral anchors explicitly supported by the text.",
    )
    capabilities: CapabilityProfilePayload | None = Field(
        default=None,
        description="Durable capabilities or limitations that the text makes explicit.",
    )
    conditions: ConditionProfilePayload | None = Field(
        default=None,
        description="Persistent conditions, fragilities, or vulnerabilities explicitly stated in the text.",
    )
    social: SocialProfilePayload | None = Field(
        default=None,
        description="Durable social placement such as rank, class, faction, occupation, or reputation.",
    )
    appearance: AppearanceProfilePayload | None = Field(
        default=None,
        description="Visible description worth carrying forward for continuity when clearly stated.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional extension data derived directly from the same text.",
    )


class CharacterExtractionResponse(BaseModel):
    """Top-level structured output schema for discovery extraction."""

    characters: list[CharacterCandidatePayload] = Field(
        default_factory=list,
        description="All distinct character candidates found in the provided text.",
    )


class LangChainCharacterExtractor(CharacterExtractor):
    """Discover sparse character candidates from story text with structured output.

    This class is intentionally discovery-focused. It extracts core identity and
    cheap summary fields first, then attaches only the optional modules that are
    directly supported by the text. Relationship edges are intentionally not
    flattened into the character profile because those will eventually live in a
    separate graph layer.
    """

    def __init__(
        self,
        llm: ChatOpenAI | None = None,
        *,
        temperature: float = 0.0,
        provider: str | None = None,
    ) -> None:
        """Initialize the discovery extractor."""
        self.llm = llm or ChatOpenAI(
            openai_api_key=get_api_key(),
            base_url=get_api_base_url(),
            model=get_model_name(),
            temperature=temperature,
        )
        self.provider = provider or self._detect_provider()
        self.structured_llm = self.llm.with_structured_output(CharacterExtractionResponse)
        self.structured_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You extract reusable character knowledge from fiction, outlines, or story notes. "
                        "Focus on stable person-level information. "
                        "Return only characters supported by the text. "
                        "Do not invent missing details. "
                        "Prefer a sparse record over a speculative one. "
                        "Do not turn pairwise relationships into character fields. "
                        "Use empty lists or null when information is not present."
                    ),
                ),
                (
                    "human",
                    (
                        "Extract characters from the following text.\n\n"
                        "For each character, prioritize:\n"
                        "1. canonical_name\n"
                        "2. aliases\n"
                        "3. salient_concept\n"
                        "4. stable_tendencies\n"
                        "Optional modules should be filled only when the text explicitly supports durable facts.\n\n"
                        "Text:\n{text}"
                    ),
                ),
            ]
        )
        self.structured_retry_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You extract sparse reusable character knowledge. "
                        "A previous structured-output attempt failed. "
                        "Return only schema-compliant, text-supported character data. "
                        "Do not add commentary or invent facts."
                    ),
                ),
                (
                    "human",
                    (
                        "Retry the character extraction for the text below.\n\n"
                        "Text:\n{text}"
                    ),
                ),
            ]
        )
        self.json_fallback_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You extract sparse reusable character knowledge from fiction or story notes. "
                        "Return valid JSON only with this shape: "
                        "{\"characters\": [{\"canonical_name\": str, \"aliases\": [str], "
                        "\"salient_concept\": str | null, \"stable_tendencies\": [str], "
                        "\"capabilities\": {\"cognitive\": [str], \"social\": [str], "
                        "\"physical\": [str], \"practical\": [str]} | null, "
                        "\"conditions\": {\"persistent_conditions\": [str], \"vulnerabilities\": [str]} | null, "
                        "\"social\": {\"class_status\": str | null, \"rank\": str | null, "
                        "\"faction\": str | null, \"occupation\": str | null, "
                        "\"obligations\": [str], \"reputation\": [str]} | null, "
                        "\"appearance\": {\"summary\": str | null, \"distinguishing_features\": [str]} | null, "
                        "\"metadata\": object}]}. "
                        "Do not wrap the JSON in markdown fences. "
                        "Do not include unsupported characters or invented details."
                    ),
                ),
                (
                    "human",
                    (
                        "Extract characters from the following text.\n\n"
                        "Text:\n{text}"
                    ),
                ),
            ]
        )

    def extract(self, text: str) -> list[CharacterCandidate]:
        """Extract discovery candidates from raw text."""
        if not text.strip():
            raise ValueError("Extraction text cannot be empty.")

        try:
            return self._extract_with_structured_output(text, prompt=self.structured_prompt)
        except Exception as structured_error:
            return self._extract_with_provider_fallback(text, structured_error)

    def _detect_provider(self) -> str:
        """Infer the current LLM provider from environment configuration."""
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        if os.getenv("DEEPSEEK_API_KEY"):
            return "deepseek"
        return "unknown"

    def _extract_with_structured_output(
        self,
        text: str,
        *,
        prompt: ChatPromptTemplate,
    ) -> list[CharacterCandidate]:
        """Run the primary structured-output discovery path."""
        response = self.structured_llm.invoke(prompt.format_messages(text=text))
        return [self._to_candidate(character) for character in response.characters]

    def _extract_with_provider_fallback(
        self,
        text: str,
        structured_error: Exception,
    ) -> list[CharacterCandidate]:
        """Choose a recovery path after structured output fails."""
        try:
            if self.provider == "openai":
                return self._extract_with_structured_output(
                    text,
                    prompt=self.structured_retry_prompt,
                )
        except Exception:
            pass

        try:
            return self._extract_with_json_fallback(text)
        except Exception:
            raise RuntimeError(
                "Character discovery extraction failed for both structured output and "
                f"{self.provider} fallback paths."
            ) from structured_error

    def _extract_with_json_fallback(self, text: str) -> list[CharacterCandidate]:
        """Recover from structured-output failures using manual JSON parsing."""
        message = self.llm.invoke(self.json_fallback_prompt.format_messages(text=text))
        payload = self._parse_json_response(message.content)
        response = CharacterExtractionResponse.model_validate(payload)
        return [self._to_candidate(character) for character in response.characters]

    def _parse_json_response(self, content: str | list[Any]) -> dict[str, Any]:
        """Parse raw LLM content into a JSON object for schema validation."""
        raw_content = self._coerce_message_content(content).strip()
        cleaned_content = self._strip_code_fences(raw_content)
        payload = json.loads(cleaned_content)
        if not isinstance(payload, dict):
            raise ValueError("Character extraction JSON payload must be an object.")
        return payload

    def _coerce_message_content(self, content: str | list[Any]) -> str:
        """Convert provider-specific message content into plain text."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _strip_code_fences(self, content: str) -> str:
        """Remove optional markdown code fences around a JSON response."""
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return stripped

    def _to_candidate(self, payload: CharacterCandidatePayload) -> CharacterCandidate:
        """Convert validated LLM output into the discovery domain model."""
        return CharacterCandidate(
            canonical_name=" ".join(payload.canonical_name.strip().split()),
            aliases=normalize_unique_strings(payload.aliases),
            salient_concept=self._normalize_optional_text(payload.salient_concept),
            stable_tendencies=normalize_unique_strings(payload.stable_tendencies),
            capabilities=self._to_capabilities(payload.capabilities),
            conditions=self._to_conditions(payload.conditions),
            social=self._to_social(payload.social),
            appearance=self._to_appearance(payload.appearance),
            metadata=dict(payload.metadata),
        )

    def _to_capabilities(
        self,
        payload: CapabilityProfilePayload | None,
    ) -> CapabilityProfile | None:
        """Convert the optional capability payload into the domain profile."""
        if payload is None:
            return None
        profile = CapabilityProfile(
            cognitive=normalize_unique_strings(payload.cognitive),
            social=normalize_unique_strings(payload.social),
            physical=normalize_unique_strings(payload.physical),
            practical=normalize_unique_strings(payload.practical),
        )
        return profile if self._has_any_list_data(profile.cognitive, profile.social, profile.physical, profile.practical) else None

    def _to_conditions(
        self,
        payload: ConditionProfilePayload | None,
    ) -> ConditionProfile | None:
        """Convert the optional condition payload into the domain profile."""
        if payload is None:
            return None
        profile = ConditionProfile(
            persistent_conditions=normalize_unique_strings(payload.persistent_conditions),
            vulnerabilities=normalize_unique_strings(payload.vulnerabilities),
        )
        return profile if self._has_any_list_data(profile.persistent_conditions, profile.vulnerabilities) else None

    def _to_social(self, payload: SocialProfilePayload | None) -> SocialProfile | None:
        """Convert the optional social payload into the domain profile."""
        if payload is None:
            return None
        profile = SocialProfile(
            class_status=self._normalize_optional_text(payload.class_status),
            rank=self._normalize_optional_text(payload.rank),
            faction=self._normalize_optional_text(payload.faction),
            occupation=self._normalize_optional_text(payload.occupation),
            obligations=normalize_unique_strings(payload.obligations),
            reputation=normalize_unique_strings(payload.reputation),
        )
        if any(
            value is not None
            for value in (profile.class_status, profile.rank, profile.faction, profile.occupation)
        ) or self._has_any_list_data(profile.obligations, profile.reputation):
            return profile
        return None

    def _to_appearance(
        self,
        payload: AppearanceProfilePayload | None,
    ) -> AppearanceProfile | None:
        """Convert the optional appearance payload into the domain profile."""
        if payload is None:
            return None
        profile = AppearanceProfile(
            summary=self._normalize_optional_text(payload.summary),
            distinguishing_features=normalize_unique_strings(payload.distinguishing_features),
        )
        if profile.summary is not None or self._has_any_list_data(profile.distinguishing_features):
            return profile
        return None

    def _normalize_optional_text(self, value: str | None) -> str | None:
        """Normalize optional text fields from the structured output."""
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    def _has_any_list_data(self, *groups: list[str]) -> bool:
        """Return `True` when at least one normalized list still has content."""
        return any(group for group in groups)
