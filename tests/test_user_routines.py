"""Persistence, editing, ordering, execution, and safety tests for user routines."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.core.user_routines import UserRoutineStore
from voice_control_usb.excel.adapter import StubExcelAdapter


class UserRoutineStoreTests(unittest.TestCase):
    def test_routine_edits_persist_and_preserve_left_to_right_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "routines.json"
            store = UserRoutineStore(path)
            store.create("Morning setup")
            store.add_command("Morning setup", "open excel")
            store.add_command("Morning setup", "go to A1")
            store.add_command("Morning setup", "enter ready")
            store.move_command("Morning setup", 2, 1)
            store.update_command("Morning setup", 1, "enter started")

            reloaded = UserRoutineStore(path)

            self.assertEqual(
                reloaded.get("morning SETUP").commands,
                ("open excel", "enter started", "go to A1"),
            )

    def test_routines_reject_unknown_blocked_nested_and_control_commands(self) -> None:
        store = UserRoutineStore()
        store.create("Safe")

        for command in (
            "not a real command",
            "run command dir",
            "confirm",
            "start Safe routine",
        ):
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    store.add_command("Safe", command)

    def test_rename_remove_and_delete_are_case_insensitive(self) -> None:
        store = UserRoutineStore()
        store.create("Work Day")
        store.add_command("work day", "open excel")
        store.remove_command("WORK DAY", 0)
        renamed = store.rename("work day", "Office Start")
        deleted = store.delete("office start")

        self.assertEqual(renamed.name, "Office Start")
        self.assertEqual(deleted.name, "Office Start")
        self.assertEqual(store.list(), ())


class UserRoutineExecutionTests(unittest.TestCase):
    def test_safe_routine_runs_each_command_in_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir)
            excel = StubExcelAdapter()
            app = AssistantApp(
                proposal_path=path / "unsupported.jsonl",
                routine_path=path / "routines.json",
                excel=excel,
            )
            app.handle_text("create routine Data entry")
            app.routines.set_commands(
                "Data entry",
                ["open excel", "go to B4", "enter complete", "go right"],
            )

            result = app.handle_text("start Data entry routine")

            self.assertIn("completed 4 step(s)", result)
            self.assertEqual(excel.cells["B4"], "complete")
            self.assertEqual(excel.current_cell, "C4")

    def test_sensitive_routine_requires_one_confirmation_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir)
            app = AssistantApp(
                proposal_path=path / "unsupported.jsonl",
                routine_path=path / "routines.json",
            )
            app.routines.create("Close work")
            app.routines.set_commands("Close work", ["open excel", "close workbook"])

            pending = app.handle_text("run Close work routine")
            confirmed = app.handle_text("confirm")

            self.assertTrue(pending.startswith("[CONFIRMATION REQUIRED]"))
            self.assertIn("Routine 'Close work' completed 2 step(s)", confirmed)

    def test_voice_routine_management_and_confirmed_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir)
            app = AssistantApp(
                proposal_path=path / "unsupported.jsonl",
                routine_path=path / "routines.json",
            )

            self.assertIn("Created routine: Focus", app.handle_text("create routine Focus"))
            self.assertIn("Focus", app.handle_text("list routines"))
            self.assertIn("ready to edit", app.handle_text("edit routine Focus"))
            self.assertIn("CONFIRMATION REQUIRED", app.handle_text("delete routine Focus"))
            self.assertIn("Deleted routine: Focus", app.handle_text("confirm"))


if __name__ == "__main__":
    unittest.main()
