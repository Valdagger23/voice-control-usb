"""Deterministic routing through capability-neutral action contracts."""

from __future__ import annotations

from voice_control_usb.core.builtin_capabilities import (
    WorkflowCapability,
    assistant_action_specs,
)
from voice_control_usb.browser.adapter import BrowserAdapter, StubBrowserAdapter
from voice_control_usb.browser.capability import BrowserCapability
from voice_control_usb.core.capabilities import (
    ActionBinding,
    ActionResult,
    Capability,
    CapabilityRegistry,
)
from voice_control_usb.core.models import Command
from voice_control_usb.core.workflows import WorkflowRegistry
from voice_control_usb.desktop.adapter import DesktopAdapter
from voice_control_usb.desktop.capability import DesktopCapability
from voice_control_usb.excel.adapter import ExcelAdapter
from voice_control_usb.excel.capability import ExcelCapability
from voice_control_usb.media.adapter import MediaAdapter, StubMediaAdapter
from voice_control_usb.media.capability import MediaCapability


class ExecutionEngine:
    """Route approved commands through registered capability bindings."""

    def __init__(
        self,
        excel: ExcelAdapter,
        desktop: DesktopAdapter,
        media: MediaAdapter | None = None,
        browser: BrowserAdapter | None = None,
        workflow_registry: WorkflowRegistry | None = None,
    ) -> None:
        # Compatibility views retained while callers migrate to capabilities.
        self.excel = excel
        self.desktop = desktop
        self.media = media or StubMediaAdapter()
        self.browser = browser or StubBrowserAdapter()
        self.handlers = {}

        self.workflow_registry = workflow_registry or WorkflowRegistry.load_default()
        self.registry = CapabilityRegistry(assistant_action_specs())
        self.capabilities: list[Capability] = []

        self._register_capability(ExcelCapability(excel))
        self._register_capability(DesktopCapability(desktop))
        self._register_capability(MediaCapability(self.media))
        self._register_capability(BrowserCapability(self.browser))
        self.workflow_registry.validate_contracts(self.registry)
        self._register_capability(
            WorkflowCapability(
                workflows=self.workflow_registry,
                action_registry=self.registry,
            )
        )

    def execute(self, command: Command) -> str:
        """Compatibility boundary returning the existing user-visible message."""

        return self.execute_result(command).message

    def execute_result(self, command: Command) -> ActionResult:
        """Execute an approved command and return its structured capability result."""

        try:
            return self.registry.execute(command)
        except ValueError as error:
            if self.registry.spec_for(command.action) is None:
                raise ValueError(
                    f"Unsupported command routed to executor: {command.action}"
                ) from error
            raise

    def _register_capability(self, capability: Capability) -> None:
        bindings = capability.bindings()
        for binding in bindings:
            self._register_binding(binding)
        self.capabilities.append(capability)

    def _register_binding(self, binding: ActionBinding) -> None:
        self.registry.register(binding.spec, binding.handler)
        self.handlers[binding.spec.action_id] = binding.handler
