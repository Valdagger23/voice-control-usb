"""Contract tests for capability-neutral action routing."""

from __future__ import annotations

import unittest

from voice_control_usb.core.capabilities import (
    ActionResult,
    ActionSpec,
    CapabilityRegistry,
    SafetyClass,
)
from voice_control_usb.core.models import Command
from voice_control_usb.desktop.adapter import StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class CapabilityRegistryTests(unittest.TestCase):
    def test_registry_wraps_legacy_handler_message_in_structured_result(self) -> None:
        registry = CapabilityRegistry()
        spec = ActionSpec(
            capability_id="example",
            action_id="greet",
            description="Return a greeting.",
            argument_types={"name": str},
        )
        registry.register(spec, lambda command: f"Hello {command.arguments['name']}")

        result = registry.execute(
            Command(
                name="greet",
                action="greet",
                arguments={"name": "Valdas"},
                source_text="greet Valdas",
            )
        )

        self.assertEqual(
            result,
            ActionResult(
                capability_id="example",
                action_id="greet",
                message="Hello Valdas",
            ),
        )

    def test_registry_rejects_missing_unexpected_and_wrong_type_arguments(self) -> None:
        registry = CapabilityRegistry()
        spec = ActionSpec(
            capability_id="example",
            action_id="set_level",
            description="Set a numeric level.",
            argument_types={"level": int},
        )
        registry.register(spec, lambda command: "done")

        with self.assertRaisesRegex(ValueError, "missing arguments: level"):
            registry.execute(Command(name="missing", action="set_level"))
        with self.assertRaisesRegex(ValueError, "unexpected arguments: extra"):
            registry.execute(
                Command(
                    name="extra",
                    action="set_level",
                    arguments={"level": 1, "extra": "value"},
                )
            )
        with self.assertRaisesRegex(ValueError, "argument 'level' must be int"):
            registry.execute(
                Command(
                    name="wrong_type",
                    action="set_level",
                    arguments={"level": "high"},
                )
            )

    def test_registry_rejects_mismatched_structured_result_identity(self) -> None:
        registry = CapabilityRegistry()
        spec = ActionSpec(
            capability_id="example",
            action_id="run",
            description="Run the example.",
        )
        registry.register(
            spec,
            lambda command: ActionResult(
                capability_id="different",
                action_id="run",
                message="wrong",
            ),
        )

        with self.assertRaisesRegex(ValueError, "result identity"):
            registry.execute(Command(name="run", action="run"))

    def test_registry_accepts_declared_union_argument_types(self) -> None:
        registry = CapabilityRegistry()
        spec = ActionSpec(
            capability_id="example",
            action_id="set_value",
            description="Set a value.",
            argument_types={"value": (str, int, float)},
        )
        registry.register(spec, lambda command: "done")

        self.assertEqual(
            registry.execute(
                Command("set_value", "set_value", {"value": 1.5})
            ).message,
            "done",
        )
        with self.assertRaisesRegex(ValueError, "str or int or float"):
            registry.execute(Command("set_value", "set_value", {"value": object()}))

    def test_engine_exposes_capability_metadata_and_structured_results(self) -> None:
        engine = ExecutionEngine(
            excel=StubExcelAdapter(),
            desktop=StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )

        result = engine.execute_result(
            Command(name="open_excel", action="open_excel", source_text="open excel")
        )
        type_text = engine.registry.spec_for("type_text")
        shutdown = engine.registry.spec_for("shutdown")

        self.assertEqual(result.capability_id, "excel")
        self.assertEqual(result.action_id, "open_excel")
        self.assertEqual(result.message, "Excel session ready (stub)")
        self.assertEqual(
            {capability.capability_id for capability in engine.capabilities},
            {"excel", "desktop", "media", "browser", "workflow"},
        )
        assert type_text is not None
        self.assertTrue(type_text.reversible)
        assert shutdown is not None
        self.assertIs(shutdown.safety_class, SafetyClass.REQUIRES_CONFIRMATION)


if __name__ == "__main__":
    unittest.main()
