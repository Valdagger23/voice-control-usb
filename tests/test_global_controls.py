from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from voice_control_usb.assistant.global_controls import (
    GlobalControlConfig,
    GlobalControlStore,
    GlobalInputController,
    PUSH_TO_TALK,
    TOGGLE_LISTENING,
)
from voice_control_usb.assistant.tray import TrayController, create_brand_icon


class FakeInputBackend:
    def __init__(self) -> None:
        self.on_press = None
        self.on_release = None
        self.started = False
        self.stopped = False

    def start(self, on_press, on_release) -> None:
        self.on_press = on_press
        self.on_release = on_release
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class GlobalControlStoreTests(unittest.TestCase):
    def test_defaults_are_disabled_and_settings_persist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "global-controls.json"
            store = GlobalControlStore(path)

            self.assertFalse(store.load().enabled)
            saved = store.save(
                GlobalControlConfig(
                    enabled=True,
                    input_type="mouse",
                    code="button:x2",
                    display="MOUSE X2",
                    mode=TOGGLE_LISTENING,
                )
            )

            self.assertEqual(store.load(), saved)
            self.assertNotIn(".tmp", path.name)

    def test_invalid_saved_settings_fail_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "global-controls.json"
            path.write_text('{"enabled": true, "mode": "always"}', encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "settings are invalid"):
                GlobalControlStore(path).load()

            path.write_text('{"enabled": "false"}', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "enabled state"):
                GlobalControlStore(path).load()


class GlobalInputControllerTests(unittest.TestCase):
    def test_matching_input_is_debounced_and_release_is_reported(self) -> None:
        backend = FakeInputBackend()
        events: list[str] = []
        controller = GlobalInputController(
            GlobalControlConfig(enabled=True, code="key:f8", display="F8"),
            lambda: events.append("press"),
            lambda: events.append("release"),
            backend=backend,
        )
        controller.start()

        controller.handle_press("keyboard", "key:f8", "F8")
        controller.handle_press("keyboard", "key:f8", "F8")
        controller.handle_release("keyboard", "key:f8", "F8")

        self.assertEqual(events, ["press", "release"])
        controller.stop()
        self.assertTrue(backend.started)
        self.assertTrue(backend.stopped)

    def test_assignment_capture_does_not_activate_the_old_binding(self) -> None:
        events: list[str] = []
        captured: list[tuple[str, str, str]] = []
        controller = GlobalInputController(
            GlobalControlConfig(enabled=True, code="key:f8", display="F8"),
            lambda: events.append("press"),
            lambda: events.append("release"),
            backend=FakeInputBackend(),
        )
        controller.capture_next(lambda *value: captured.append(value))

        controller.handle_press("keyboard", "key:f8", "F8")
        controller.handle_release("keyboard", "key:f8", "F8")

        self.assertEqual(captured, [("keyboard", "key:f8", "F8")])
        self.assertEqual(events, [])

    def test_mouse_binding_and_runtime_update_are_supported(self) -> None:
        events: list[str] = []
        controller = GlobalInputController(
            GlobalControlConfig(),
            lambda: events.append("press"),
            lambda: events.append("release"),
            backend=FakeInputBackend(),
        )
        controller.update(
            GlobalControlConfig(
                enabled=True,
                input_type="mouse",
                code="button:middle",
                display="MOUSE MIDDLE",
                mode=PUSH_TO_TALK,
            )
        )

        controller.handle_press("mouse", "button:middle", "MOUSE MIDDLE")
        controller.handle_release("mouse", "button:middle", "MOUSE MIDDLE")

        self.assertEqual(events, ["press", "release"])


class TrayBrandTests(unittest.TestCase):
    def test_brand_icon_is_a_square_rgba_image(self) -> None:
        icon = create_brand_icon(64)

        self.assertEqual(icon.size, (64, 64))
        self.assertEqual(icon.mode, "RGBA")

    def test_tray_default_action_opens_window_and_exit_action_closes(self) -> None:
        class FakeMenuItem:
            def __init__(self, text, action, **options) -> None:
                self.text = text
                self.action = action
                self.options = options

        class FakeMenu:
            SEPARATOR = object()

            def __init__(self, *items) -> None:
                self.items = items

        class FakeIcon:
            def __init__(self, name, image, title, menu) -> None:
                self.name = name
                self.image = image
                self.title = title
                self.menu = menu
                self.detached = False
                self.refreshed = False
                self.stopped = False

            def run_detached(self) -> None:
                self.detached = True

            def update_menu(self) -> None:
                self.refreshed = True

            def stop(self) -> None:
                self.stopped = True

        fake_pystray = SimpleNamespace(
            Menu=FakeMenu,
            MenuItem=FakeMenuItem,
            Icon=FakeIcon,
        )
        events: list[str] = []
        controller = TrayController(
            lambda: events.append("open"),
            lambda: events.append("exit"),
            lambda: "Global control: OFF",
        )

        with patch.dict("sys.modules", {"pystray": fake_pystray}):
            controller.start()
            icon = controller.icon
            self.assertTrue(icon.detached)
            self.assertTrue(icon.menu.items[0].options["default"])
            icon.menu.items[0].action(None, None)
            icon.menu.items[-1].action(None, None)
            controller.refresh()
            self.assertTrue(icon.refreshed)
            controller.stop()

        self.assertEqual(events, ["open", "exit"])
        self.assertTrue(icon.stopped)


if __name__ == "__main__":
    unittest.main()
