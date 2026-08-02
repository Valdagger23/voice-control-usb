"""Runtime path and instance-guard helpers for development and packaged execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Callable


class DuplicateInstanceError(RuntimeError):
    """Raised when an assistant instance is already active for the same runtime directory."""


def package_root(*, packaged_base: Path | None = None) -> Path:
    """Return the package root for source or packaged execution."""

    base = packaged_base or getattr(sys, "_MEIPASS", None)
    if base is not None:
        return Path(base).resolve() / "voice_control_usb"
    return Path(__file__).resolve().parent


def resolve_packaged_data_path(
    *relative_parts: str,
    packaged_base: Path | None = None,
) -> Path:
    """Resolve required bundled data files in source and packaged runs."""

    path = package_root(packaged_base=packaged_base).joinpath(*relative_parts)
    if not path.is_file():
        joined = "/".join(relative_parts)
        raise FileNotFoundError(
            f"Required runtime data file not found: {joined} (looked for {path})"
        )
    return path


@dataclass(frozen=True, slots=True)
class AssistantRuntimePaths:
    """Explicit runtime paths passed into the assistant process."""

    usb_root: Path | None
    runtime_dir: Path

    @classmethod
    def from_cli(
        cls,
        *,
        usb_root: str | None = None,
        runtime_dir: str | None = None,
    ) -> "AssistantRuntimePaths":
        """Resolve CLI-provided runtime paths safely."""

        resolved_usb_root = Path(usb_root).resolve() if usb_root else None
        if resolved_usb_root is not None and not resolved_usb_root.is_dir():
            raise RuntimeError(f"Configured USB root does not exist: {resolved_usb_root}")

        if runtime_dir:
            resolved_runtime_dir = Path(runtime_dir).resolve()
        elif resolved_usb_root is not None:
            resolved_runtime_dir = (resolved_usb_root / "runtime").resolve()
        else:
            resolved_runtime_dir = Path("runtime").resolve()

        resolved_runtime_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            usb_root=resolved_usb_root,
            runtime_dir=resolved_runtime_dir,
        )

    @property
    def proposal_path(self) -> Path:
        return self.runtime_dir / "proposals" / "unsupported_commands.jsonl"

    @property
    def audit_path(self) -> Path:
        return self.runtime_dir / "audit" / "events.jsonl"

    @property
    def lock_path(self) -> Path:
        return self.runtime_dir / "assistant.lock"


class AssistantInstanceGuard:
    """Cross-platform lock file guard for packaged assistant instances."""

    def __init__(
        self,
        lock_path: Path,
        *,
        pid_provider: Callable[[], int] | None = None,
    ) -> None:
        self.lock_path = lock_path
        self.pid_provider = pid_provider or os.getpid
        self._owned = False

    def acquire(self) -> None:
        """Acquire the runtime lock or raise when another live instance owns it."""

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        current_pid = int(self.pid_provider())

        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                payload = self._read_payload()
                existing_pid = int(payload.get("pid", 0) or 0)
                if existing_pid and not self._pid_is_running(existing_pid):
                    self.lock_path.unlink(missing_ok=True)
                    continue
                raise DuplicateInstanceError(
                    f"Assistant already running for runtime directory: {self.lock_path.parent}"
                )

            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(
                        {
                            "pid": current_pid,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "lock_path": str(self.lock_path),
                        },
                        handle,
                    )
            except Exception:
                self.lock_path.unlink(missing_ok=True)
                raise

            self._owned = True
            return

    def release(self) -> None:
        """Release the runtime lock if this process owns it."""

        if not self._owned:
            return
        self.lock_path.unlink(missing_ok=True)
        self._owned = False

    def _read_payload(self) -> dict[str, object]:
        try:
            content = self.lock_path.read_text(encoding="utf-8")
        except OSError:
            return {}
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    @staticmethod
    def _pid_is_running(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
