"""Speech activation controls for session mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

from voice_control_usb.audio.transcriber import SpeechTranscriber

SESSION_EXIT_COMMANDS = {"exit", "quit"}


@dataclass(frozen=True, slots=True)
class SpeechActivation:
    """Speech activation result produced by an activator."""

    payload: str | None = None
    should_exit: bool = False


class SpeechActivator:
    """Activation boundary for controlled speech capture."""

    prompt: str = "voice-control-usb speech> "

    def next_activation(
        self,
        transcriber: SpeechTranscriber,
        input_stream: TextIO,
        output_stream: TextIO,
        *,
        interactive: bool,
    ) -> SpeechActivation | None:
        raise NotImplementedError


class ManualRecordSpeechActivator(SpeechActivator):
    """Existing explicit `record ...` activation flow."""

    prompt = "voice-control-usb speech> "

    def next_activation(
        self,
        transcriber: SpeechTranscriber,
        input_stream: TextIO,
        output_stream: TextIO,
        *,
        interactive: bool,
    ) -> SpeechActivation | None:
        while True:
            raw_line = input_stream.readline()
            if raw_line == "":
                if interactive:
                    output_stream.write("\n")
                return None

            activation = raw_line.strip()
            if not activation:
                continue
            if activation.casefold() in SESSION_EXIT_COMMANDS:
                return SpeechActivation(should_exit=True)
            if not activation.casefold().startswith("record"):
                output_stream.write("Speech mode expects 'record <utterance>' or 'quit'.\n")
                output_stream.flush()
                continue
            return SpeechActivation(payload=activation)


class EnterToTalkSpeechActivator(SpeechActivator):
    """Controlled push-to-talk using Enter as the activation trigger."""

    prompt = "voice-control-usb ptt> "

    def next_activation(
        self,
        transcriber: SpeechTranscriber,
        input_stream: TextIO,
        output_stream: TextIO,
        *,
        interactive: bool,
    ) -> SpeechActivation | None:
        while True:
            raw_line = input_stream.readline()
            if raw_line == "":
                if interactive:
                    output_stream.write("\n")
                return None

            activation = raw_line.rstrip("\r\n")
            stripped = activation.strip()
            if stripped.casefold() in SESSION_EXIT_COMMANDS:
                return SpeechActivation(should_exit=True)
            if stripped:
                output_stream.write("Push-to-talk mode expects Enter to record or 'quit'.\n")
                output_stream.flush()
                continue

            if transcriber.requires_manual_transcript():
                if interactive:
                    output_stream.write("Speak now (stub text): ")
                    output_stream.flush()
                transcript_line = input_stream.readline()
                if transcript_line == "":
                    if interactive:
                        output_stream.write("\n")
                    return None
                return SpeechActivation(payload=transcript_line.strip())

            return SpeechActivation(payload="record")
