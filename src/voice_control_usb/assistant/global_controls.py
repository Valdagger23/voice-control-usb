"""Persistent global keyboard and mouse activation controls for Windows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from threading import Lock
from typing import Callable, Protocol


PUSH_TO_TALK = "push_to_talk"
TOGGLE_LISTENING = "toggle_listening"
ACTIVATION_MODES = (PUSH_TO_TALK, TOGGLE_LISTENING)
INPUT_TYPES = ("keyboard", "mouse")


@dataclass(frozen=True, slots=True)
class GlobalControlConfig:
    """One user-selected global input and its speech activation behavior."""

    enabled: bool = False
    input_type: str = "keyboard"
    code: str = "key:f8"
    display: str = "F8"
    mode: str = PUSH_TO_TALK

    def validated(self) -> "GlobalControlConfig":
        if not isinstance(self.enabled, bool):
            raise ValueError("Global control enabled state must be true or false.")
        if not all(
            isinstance(value, str)
            for value in (self.input_type, self.code, self.display, self.mode)
        ):
            raise ValueError("Global control input settings must be text.")
        if self.input_type not in INPUT_TYPES:
            raise ValueError("Global control input must be keyboard or mouse.")
        if not self.code.strip() or not self.display.strip():
            raise ValueError("Global control input cannot be empty.")
        if self.mode not in ACTIVATION_MODES:
            raise ValueError("Global control mode must be push-to-talk or toggle listening.")
        return GlobalControlConfig(
            enabled=bool(self.enabled),
            input_type=self.input_type,
            code=self.code.strip().casefold(),
            display=self.display.strip(),
            mode=self.mode,
        )


class GlobalControlStore:
    """Load and atomically save the user's global activation preference."""

    def __init__(self, path: Path | None) -> None:
        self.path = path

    def load(self) -> GlobalControlConfig:
        if self.path is None or not self.path.is_file():
            return GlobalControlConfig()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not load global control settings: {error}") from error
        if not isinstance(payload, dict):
            raise RuntimeError("Global control settings have an invalid format.")
        try:
            return GlobalControlConfig(
                enabled=payload.get("enabled", False),
                input_type=payload.get("input_type", "keyboard"),
                code=payload.get("code", "key:f8"),
                display=payload.get("display", "F8"),
                mode=payload.get("mode", PUSH_TO_TALK),
            ).validated()
        except ValueError as error:
            raise RuntimeError(f"Global control settings are invalid: {error}") from error

    def save(self, config: GlobalControlConfig) -> GlobalControlConfig:
        validated = config.validated()
        if self.path is None:
            return validated
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"version": 1, **asdict(validated)}, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return validated


class GlobalInputBackend(Protocol):
    """Pluggable source of system-wide key and mouse button events."""

    def start(
        self,
        on_press: Callable[[str, str, str], None],
        on_release: Callable[[str, str, str], None],
    ) -> None: ...

    def stop(self) -> None: ...


class PynputGlobalInputBackend:
    """Observe global key and mouse button events without suppressing them."""

    def __init__(self) -> None:
        self._keyboard_listener: object | None = None
        self._mouse_listener: object | None = None

    def start(
        self,
        on_press: Callable[[str, str, str], None],
        on_release: Callable[[str, str, str], None],
    ) -> None:
        try:
            from pynput import keyboard, mouse
        except ImportError as error:
            raise ImportError(
                "Global key and mouse controls require pynput. Install the Windows extras."
            ) from error

        def key_press(key: object) -> None:
            code, display = _normalize_key(key)
            on_press("keyboard", code, display)

        def key_release(key: object) -> None:
            code, display = _normalize_key(key)
            on_release("keyboard", code, display)

        def mouse_click(_x: int, _y: int, button: object, pressed: bool) -> None:
            code, display = _normalize_mouse_button(button)
            callback = on_press if pressed else on_release
            callback("mouse", code, display)

        self._keyboard_listener = keyboard.Listener(
            on_press=key_press,
            on_release=key_release,
        )
        self._mouse_listener = mouse.Listener(on_click=mouse_click)
        self._keyboard_listener.start()
        self._mouse_listener.start()

    def stop(self) -> None:
        for listener in (self._keyboard_listener, self._mouse_listener):
            if listener is not None:
                listener.stop()
        self._keyboard_listener = None
        self._mouse_listener = None


class GlobalInputController:
    """Match observed inputs, debounce presses, and support one-shot assignment."""

    def __init__(
        self,
        config: GlobalControlConfig,
        on_activation_press: Callable[[], None],
        on_activation_release: Callable[[], None],
        backend: GlobalInputBackend | None = None,
    ) -> None:
        self.config = config.validated()
        self.on_activation_press = on_activation_press
        self.on_activation_release = on_activation_release
        self.backend = backend or PynputGlobalInputBackend()
        self._pressed: set[tuple[str, str]] = set()
        self._captured: set[tuple[str, str]] = set()
        self._capture: Callable[[str, str, str], None] | None = None
        self._lock = Lock()

    def start(self) -> None:
        self.backend.start(self.handle_press, self.handle_release)

    def stop(self) -> None:
        self.backend.stop()

    def update(self, config: GlobalControlConfig) -> None:
        with self._lock:
            self.config = config.validated()
            self._pressed.clear()
            self._captured.clear()

    def capture_next(self, callback: Callable[[str, str, str], None]) -> None:
        with self._lock:
            self._capture = callback

    def cancel_capture(self) -> None:
        with self._lock:
            self._capture = None

    def handle_press(self, input_type: str, code: str, display: str) -> None:
        normalized = (input_type, code.casefold())
        with self._lock:
            capture = self._capture
            if capture is not None:
                self._capture = None
            if normalized in self._pressed:
                return
            self._pressed.add(normalized)
            if capture is not None:
                self._captured.add(normalized)
            config = self.config
        if capture is not None:
            capture(input_type, code.casefold(), display)
            return
        if (
            config.enabled
            and config.input_type == input_type
            and config.code == code.casefold()
        ):
            self.on_activation_press()

    def handle_release(self, input_type: str, code: str, _display: str) -> None:
        normalized = (input_type, code.casefold())
        with self._lock:
            was_pressed = normalized in self._pressed
            self._pressed.discard(normalized)
            was_captured = normalized in self._captured
            self._captured.discard(normalized)
            config = self.config
        if was_captured:
            return
        if (
            was_pressed
            and config.enabled
            and config.input_type == input_type
            and config.code == code.casefold()
        ):
            self.on_activation_release()


def mode_label(mode: str) -> str:
    return "PUSH TO TALK" if mode == PUSH_TO_TALK else "TOGGLE LISTENING"


def _normalize_key(key: object) -> tuple[str, str]:
    character = getattr(key, "char", None)
    if isinstance(character, str) and character:
        normalized = character.casefold()
        return f"char:{normalized}", character.upper()
    name = getattr(key, "name", None)
    if isinstance(name, str) and name:
        return f"key:{name.casefold()}", name.replace("_", " ").upper()
    virtual_key = getattr(key, "vk", None)
    if isinstance(virtual_key, int):
        return f"vk:{virtual_key}", f"KEY {virtual_key}"
    text = str(key).strip().casefold()
    if not text:
        raise ValueError("Windows reported an unknown key.")
    return f"key:{text}", text.upper()


def _normalize_mouse_button(button: object) -> tuple[str, str]:
    name = getattr(button, "name", None)
    normalized = str(name or button).removeprefix("Button.").casefold()
    return f"button:{normalized}", f"MOUSE {normalized.upper()}"
