"""Runtime-switchable speech transcriber backed by a persistent speech profile."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from voice_control_usb.audio.local_whisper import LocalWhisperSpeechTranscriber
from voice_control_usb.audio.speech_profile import (
    LOCAL_WHISPER,
    SpeechProfile,
    SpeechProfileStore,
)
from voice_control_usb.audio.transcriber import SpeechTranscriber, TranscriptionResult
from voice_control_usb.audio.windows_sapi import WindowsSapiSpeechTranscriber


ProviderFactory = Callable[[SpeechProfile], SpeechTranscriber]


class ProfiledSpeechTranscriber(SpeechTranscriber):
    """Delegate capture to the provider selected in the user's saved profile."""

    def __init__(
        self,
        store: SpeechProfileStore,
        model_root: Path,
        *,
        fallback_provider: str = "windows_sapi",
        provider_override: str | None = None,
        microphone_override: str | None = None,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        self.store = store
        self.model_root = model_root
        self.provider_factory = provider_factory or self._default_provider_factory
        self.profile = store.load(fallback_provider=fallback_provider)
        if provider_override:
            self.profile = replace(self.profile, provider=provider_override)
        if microphone_override:
            self.profile = replace(self.profile, microphone=microphone_override.strip())
        self._delegate = self.provider_factory(self.profile)

    @property
    def provider_name(self) -> str:
        return self.profile.provider

    def configure(self, profile: SpeechProfile, *, persist: bool = True) -> None:
        previous = self._delegate
        previous.stop_capture()
        delegate = self.provider_factory(profile)
        if profile.microphone:
            delegate.select_input_device(profile.microphone)
        self.profile = profile
        self._delegate = delegate
        if persist:
            self.store.save(profile)

    def remember_correction(self, heard: str, intended: str) -> None:
        updated = self.profile.with_correction(heard, intended)
        self.profile = updated
        self.store.save(updated)

    def remove_correction(self, heard: str) -> None:
        updated = self.profile.without_correction(heard)
        self.profile = updated
        self.store.save(updated)

    def available_input_devices(self) -> tuple[str, ...]:
        return self._delegate.available_input_devices()

    def available_input_devices_for(self, profile: SpeechProfile) -> tuple[str, ...]:
        return self.provider_factory(profile).available_input_devices()

    def select_input_device(self, name: str | None) -> None:
        self._delegate.select_input_device(name)
        updated = replace(self.profile, microphone=(name or "").strip())
        if updated != self.profile:
            self.profile = updated
            self.store.save(updated)

    def transcribe_result(self, audio_source: str | None = None) -> TranscriptionResult:
        return self._delegate.transcribe_result(audio_source)

    def transcribe(self, audio_source: str | None = None) -> str:
        return self._delegate.transcribe(audio_source)

    def prepare_capture(self) -> None:
        self._delegate.prepare_capture()

    def stop_capture(self) -> None:
        self._delegate.stop_capture()

    def requires_manual_transcript(self) -> bool:
        return self._delegate.requires_manual_transcript()

    def _default_provider_factory(self, profile: SpeechProfile) -> SpeechTranscriber:
        if profile.provider == LOCAL_WHISPER:
            return LocalWhisperSpeechTranscriber(
                model_root=self.model_root,
                model_name=profile.model,
                locale=profile.locale,
                device_name=profile.microphone or None,
            )
        return WindowsSapiSpeechTranscriber(device_name=profile.microphone or None)
