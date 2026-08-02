"""Persistent per-user speech accuracy settings and learned corrections."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from difflib import SequenceMatcher
import json
import os
from pathlib import Path


WINDOWS_SAPI = "windows_sapi"
LOCAL_WHISPER = "local_whisper"
SUPPORTED_SPEECH_PROVIDERS = (WINDOWS_SAPI, LOCAL_WHISPER)
SUPPORTED_LOCALES = ("en-IE", "en-GB", "en-US", "en")
SUPPORTED_MODELS = ("base.en", "small.en", "medium.en")


def normalize_phrase(value: str) -> str:
    return " ".join(value.strip().split())


@dataclass(frozen=True, slots=True)
class SpeechProfile:
    """Settings that tune capture, recognition, and deterministic recovery."""

    provider: str = WINDOWS_SAPI
    microphone: str = ""
    locale: str = "en-IE"
    model: str = "small.en"
    confidence_threshold: float = 0.45
    command_matching: bool = True
    corrections: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SpeechProfile":
        provider = str(payload.get("provider", WINDOWS_SAPI)).strip().casefold()
        if provider not in SUPPORTED_SPEECH_PROVIDERS:
            raise ValueError(f"Unsupported speech provider: {provider}")
        microphone = normalize_phrase(str(payload.get("microphone", "")))
        locale = str(payload.get("locale", "en-IE")).strip()
        if locale not in SUPPORTED_LOCALES:
            raise ValueError(f"Unsupported speech locale: {locale}")
        model = str(payload.get("model", "small.en")).strip()
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported local speech model: {model}")
        threshold = payload.get("confidence_threshold", 0.45)
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise ValueError("Speech confidence threshold must be a number.")
        threshold = float(threshold)
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Speech confidence threshold must be between 0 and 1.")
        command_matching = payload.get("command_matching", True)
        if not isinstance(command_matching, bool):
            raise ValueError("Command matching setting must be true or false.")
        raw_corrections = payload.get("corrections", {})
        if not isinstance(raw_corrections, dict):
            raise ValueError("Speech corrections must be an object.")
        if len(raw_corrections) > 250:
            raise ValueError("Speech profile supports at most 250 personal corrections.")
        corrections: dict[str, str] = {}
        for raw_heard, raw_intended in raw_corrections.items():
            heard = normalize_phrase(str(raw_heard))
            intended = normalize_phrase(str(raw_intended))
            if not heard or not intended:
                raise ValueError("Speech corrections cannot contain empty phrases.")
            if len(heard) > 300 or len(intended) > 300:
                raise ValueError("Speech correction phrases cannot exceed 300 characters.")
            corrections[heard.casefold()] = intended
        return cls(
            provider=provider,
            microphone=microphone,
            locale=locale,
            model=model,
            confidence_threshold=threshold,
            command_matching=command_matching,
            corrections=corrections,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "provider": self.provider,
            "microphone": self.microphone,
            "locale": self.locale,
            "model": self.model,
            "confidence_threshold": self.confidence_threshold,
            "command_matching": self.command_matching,
            "corrections": dict(sorted(self.corrections.items())),
        }

    def with_correction(self, heard: str, intended: str) -> "SpeechProfile":
        normalized_heard = normalize_phrase(heard)
        normalized_intended = normalize_phrase(intended)
        if not normalized_heard or not normalized_intended:
            raise ValueError("Both the heard and intended phrases are required.")
        corrections = dict(self.corrections)
        corrections[normalized_heard.casefold()] = normalized_intended
        payload = self.to_dict()
        payload["corrections"] = corrections
        return SpeechProfile.from_dict(payload)

    def without_correction(self, heard: str) -> "SpeechProfile":
        corrections = dict(self.corrections)
        corrections.pop(normalize_phrase(heard).casefold(), None)
        return replace(self, corrections=corrections)


class SpeechProfileStore:
    """Load and atomically persist the portable user's speech profile."""

    def __init__(self, path: Path | None) -> None:
        self.path = path

    def load(self, *, fallback_provider: str = WINDOWS_SAPI) -> SpeechProfile:
        if self.path is None or not self.path.is_file():
            provider = fallback_provider if fallback_provider in SUPPORTED_SPEECH_PROVIDERS else WINDOWS_SAPI
            return SpeechProfile(provider=provider)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Speech accuracy settings could not be read: {error}") from error
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise RuntimeError("Speech accuracy settings use an unsupported format.")
        try:
            return SpeechProfile.from_dict(payload)
        except ValueError as error:
            raise RuntimeError(f"Speech accuracy settings are invalid: {error}") from error

    def save(self, profile: SpeechProfile) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(profile.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)


@dataclass(frozen=True, slots=True)
class PhraseInterpretation:
    text: str
    source: str = "unchanged"
    score: float | None = None


def apply_personal_correction(
    transcript: str,
    profile: SpeechProfile,
    *,
    alternatives: tuple[str, ...] = (),
) -> PhraseInterpretation:
    """Apply exact learned corrections without guessing inside free-form values."""

    for candidate in (transcript, *alternatives):
        normalized = normalize_phrase(candidate)
        intended = profile.corrections.get(normalized.casefold())
        if intended is not None:
            return PhraseInterpretation(intended, "personal", 1.0)
    return PhraseInterpretation(normalize_phrase(transcript))


def match_safe_static_command(
    transcript: str,
    candidates: tuple[str, ...],
    *,
    minimum_score: float = 0.86,
    minimum_margin: float = 0.06,
) -> PhraseInterpretation:
    """Recover one clearly dominant safe, static command phrase."""

    normalized = normalize_phrase(transcript).casefold()
    if not normalized:
        return PhraseInterpretation(transcript)
    first_word = normalized.split(maxsplit=1)[0]
    scored = sorted(
        (
            (SequenceMatcher(None, normalized, candidate.casefold()).ratio(), candidate)
            for candidate in candidates
            if candidate.casefold().split(maxsplit=1)[0] == first_word
        ),
        reverse=True,
    )
    if not scored or scored[0][0] < minimum_score:
        return PhraseInterpretation(transcript)
    runner_up = scored[1][0] if len(scored) > 1 else 0.0
    if scored[0][0] - runner_up < minimum_margin:
        return PhraseInterpretation(transcript)
    return PhraseInterpretation(scored[0][1], "command_match", scored[0][0])
