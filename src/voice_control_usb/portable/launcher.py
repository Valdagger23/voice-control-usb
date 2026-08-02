"""Self-locating, signed-release launcher for the USB root executable."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
from typing import Protocol

from voice_control_usb.runtime_support import (
    AssistantRuntimePaths,
    ShowWindowRequestMonitor,
    inspect_instance_lock,
)
from voice_control_usb.starter.manifest import (
    ActiveRelease,
    MANIFEST_NAME,
    SIGNATURE_NAME,
    ManifestVerificationError,
    ReleaseManifest,
    UsbIdentity,
)


IDENTITY_NAME = "voice-control-usb.identity.json"
ACTIVE_RELEASE_NAME = "active-release.json"
RELEASES_NAME = "releases"


@dataclass(frozen=True, slots=True)
class PortableLaunchSpec:
    usb_root: Path
    cwd: Path
    command: tuple[str, ...]
    env_overrides: dict[str, str]


@dataclass(frozen=True, slots=True)
class PortableLaunchResult:
    launched: bool
    revealed_existing: bool
    release_id: str
    message: str


class ProcessLauncher(Protocol):
    def launch(self, spec: PortableLaunchSpec) -> object:
        """Launch the verified assistant process."""


class SubprocessLauncher:
    """Start the verified assistant without a shell or console flash."""

    def launch(self, spec: PortableLaunchSpec) -> object:
        env = os.environ.copy()
        env.update(spec.env_overrides)
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        return subprocess.Popen(  # noqa: S603
            spec.command,
            cwd=spec.cwd,
            env=env,
            shell=False,
            creationflags=creationflags,
        )


class PortableLauncher:
    """Verify the active USB release and open its visible command console."""

    def __init__(self, public_key: str, process_launcher: ProcessLauncher | None = None) -> None:
        normalized_key = public_key.strip()
        if not normalized_key:
            raise ValueError("The embedded release verification key is empty.")
        self.public_key = normalized_key
        self.process_launcher = process_launcher or SubprocessLauncher()

    def launch(self, usb_root: Path) -> PortableLaunchResult:
        root = usb_root.resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"USB root is unavailable: {root}")

        identity = UsbIdentity.load(root / IDENTITY_NAME)
        active = ActiveRelease.load(root / ACTIVE_RELEASE_NAME)
        release_dir = (root / RELEASES_NAME / active.release_id).resolve()
        self._require_within_root(root, release_dir)
        if not release_dir.is_dir():
            raise FileNotFoundError(f"Active Voice Control release is missing: {active.release_id}")

        manifest = ReleaseManifest.load(release_dir / MANIFEST_NAME)
        executable = manifest.verify(
            release_dir,
            release_dir / SIGNATURE_NAME,
            public_key=self.public_key,
            expected_usb_id=identity.usb_id,
            expected_release_id=active.release_id,
        )
        if not executable.is_file():
            raise FileNotFoundError("The verified Voice Control application is missing.")

        runtime_paths = AssistantRuntimePaths.from_cli(usb_root=str(root))
        show_monitor = ShowWindowRequestMonitor(runtime_paths.show_window_request_path)
        lock_status = inspect_instance_lock(runtime_paths.lock_path)
        if lock_status == "active":
            show_monitor.request()
            return PortableLaunchResult(
                launched=False,
                revealed_existing=True,
                release_id=active.release_id,
                message="Voice Control is already running; its window was opened.",
            )
        if lock_status == "invalid":
            raise RuntimeError(
                "Voice Control found an invalid runtime lock. Safely eject and reconnect the USB, "
                "or remove runtime\\assistant.lock after confirming Voice Control is closed."
            )

        show_monitor.clear()
        runtime_paths.shutdown_request_path.unlink(missing_ok=True)
        spec = PortableLaunchSpec(
            usb_root=root,
            cwd=release_dir,
            command=(
                str(executable),
                "--window",
                "--usb-root",
                str(root),
                "--runtime-dir",
                str(runtime_paths.runtime_dir),
            ),
            env_overrides={
                "VOICE_CONTROL_USB_USB_ROOT": str(root),
                "VOICE_CONTROL_USB_RUNTIME_DIR": str(runtime_paths.runtime_dir),
            },
        )
        self.process_launcher.launch(spec)
        return PortableLaunchResult(
            launched=True,
            revealed_existing=False,
            release_id=active.release_id,
            message="Voice Control opened.",
        )

    @staticmethod
    def _require_within_root(root: Path, candidate: Path) -> None:
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ManifestVerificationError("Active release path escapes the USB root.") from error


def resolve_usb_root(*, executable_path: Path | None = None, frozen: bool | None = None) -> Path:
    """Resolve the USB root from the launcher's own location."""

    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if executable_path is not None:
        return executable_path.resolve().parent
    if is_frozen:
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()
