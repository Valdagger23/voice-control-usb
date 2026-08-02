"""Capability bindings for editable user-created routines."""

from __future__ import annotations

from voice_control_usb.core.capabilities import ActionBinding, ActionSpec, CapabilityRegistry, SafetyClass
from voice_control_usb.core.models import Command
from voice_control_usb.core.user_routines import UserRoutineStore


def routine_action_specs() -> list[ActionSpec]:
    return [
        ActionSpec("routine", "create_user_routine", "Create an editable routine.", argument_types={"routine_name": str}),
        ActionSpec("routine", "run_user_routine", "Run a saved routine.", argument_types={"routine_name": str}),
        ActionSpec("routine", "list_user_routines", "List saved routines."),
        ActionSpec("routine", "edit_user_routine", "Open a routine for editing.", argument_types={"routine_name": str}),
        ActionSpec("routine", "delete_user_routine", "Delete a saved routine.", safety_class=SafetyClass.REQUIRES_CONFIRMATION, argument_types={"routine_name": str}),
    ]


class UserRoutineCapability:
    capability_id = "routine"

    def __init__(self, store: UserRoutineStore, registry: CapabilityRegistry) -> None:
        self.store = store
        self.registry = registry

    def bindings(self) -> list[ActionBinding]:
        handlers = {
            "create_user_routine": self._create,
            "run_user_routine": self._run,
            "list_user_routines": self._list,
            "edit_user_routine": self._edit,
            "delete_user_routine": self._delete,
        }
        return [ActionBinding(spec, handlers[spec.action_id]) for spec in routine_action_specs()]

    def _create(self, command: Command) -> str:
        routine = self.store.create(self._name(command))
        return f"Created routine: {routine.name}. Add commands in the Routine Builder."

    def _run(self, command: Command) -> str:
        name = self._name(command)
        commands = self.store.parsed_commands(name)
        if not commands:
            raise ValueError(f"Routine has no commands: {name}")
        results = [self.registry.execute(step).message for step in commands]
        return f"Routine '{self.store.get(name).name}' completed {len(results)} step(s): " + " -> ".join(results)

    def _list(self, command: Command) -> str:
        routines = self.store.list()
        return "Saved routines: " + ("; ".join(item.name for item in routines) if routines else "<none>")

    def _edit(self, command: Command) -> str:
        routine = self.store.get(self._name(command))
        if routine is None:
            raise ValueError(f"Routine not found: {self._name(command)}")
        return f"Routine ready to edit: {routine.name} ({len(routine.commands)} step(s))."

    def _delete(self, command: Command) -> str:
        routine = self.store.delete(self._name(command))
        return f"Deleted routine: {routine.name}"

    @staticmethod
    def _name(command: Command) -> str:
        name = command.arguments.get("routine_name")
        if not isinstance(name, str):
            raise ValueError("Routine name must be text.")
        return name
