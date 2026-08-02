"""Trusted USB starter and watcher implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from time import monotonic, sleep
from typing import Callable, Protocol

from voice_control_usb.starter.config import StarterConfig
from voice_control_usb.runtime_support import inspect_instance_lock
from voice_control_usb.starter.manifest import (
    ActiveRelease,
    MANIFEST_NAME,
    SIGNATURE_NAME,
    ManifestVerificationError,
    ReleaseManifest,
    UsbIdentity,
)


@dataclass(frozen=True, slots=True)
class UsbVolume:
    """Detected removable volume metadata."""

    mount_path: Path
    volume_label: str


@dataclass(frozen=True, slots=True)
class LaunchSpec:
    """Resolved launch details for the USB-hosted assistant."""

    usb_root: Path
    cwd: Path
    executable_path: Path
    release_id: str
    command: tuple[str, ...]
    env_overrides: dict[str, str]


@dataclass(frozen=True, slots=True)
class StarterResult:
    """Outcome of a starter scan cycle."""

    launched: bool
    message: str
    usb_root: Path | None = None


class ProcessHandle(Protocol):
    """Subset of subprocess state needed for duplicate prevention."""

    def poll(self) -> int | None:
        """Return None while the launched assistant is still running."""


class VolumeProvider(Protocol):
    """List removable volumes visible to the local starter."""

    def list_volumes(self) -> list[UsbVolume]:
        """Return detected removable volumes."""


class ProcessLauncher(Protocol):
    """Launch the USB-hosted assistant."""

    def launch(self, spec: LaunchSpec) -> ProcessHandle:
        """Start the assistant process and return a handle."""


class SubprocessLauncher:
    """Start the assistant via subprocess without shell execution."""

    def launch(self, spec: LaunchSpec) -> ProcessHandle:
        env = os.environ.copy()
        env.update(spec.env_overrides)
        return subprocess.Popen(  # noqa: S603
            spec.command,
            cwd=spec.cwd,
            env=env,
            shell=False,
        )


class StarterLogger:
    """Append timestamped starter events to a local log file when configured."""

    def __init__(self, path: Path | None) -> None:
        self.path = path

    def write(self, message: str) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} {message}\n")


class TrustedUsbStarter:
    """Validate a trusted USB payload before launch."""

    def __init__(
        self,
        config: StarterConfig,
        volume_provider: VolumeProvider,
        launcher: ProcessLauncher | None = None,
        logger: StarterLogger | None = None,
        sleeper: Callable[[float], None] = sleep,
        monotonic_clock: Callable[[], float] = monotonic,
    ) -> None:
        self.config = config
        self.volume_provider = volume_provider
        self.launcher = launcher or SubprocessLauncher()
        self.logger = logger or StarterLogger(config.log_path)
        self._sleep = sleeper
        self._monotonic = monotonic_clock
        self._running_process: ProcessHandle | None = None
        self._running_usb_root: Path | None = None

    def scan_and_launch(self) -> StarterResult:
        """Detect a trusted USB and launch the assistant if needed."""

        self._clear_finished_process()
        if self._running_process is not None and self._running_usb_root is not None:
            return self._record(
                StarterResult(
                    launched=False,
                    message=f"Assistant already running from {self._running_usb_root}.",
                    usb_root=self._running_usb_root,
                )
            )

        trusted_volumes = self.find_trusted_volumes()
        if not trusted_volumes:
            return self._record(StarterResult(launched=False, message="Trusted USB not detected."))
        if len(trusted_volumes) > 1:
            return self._record(
                StarterResult(
                    launched=False,
                    message="Multiple trusted USB volumes detected. Launch skipped.",
                )
            )

        volume = trusted_volumes[0]
        try:
            spec = self.build_launch_spec(volume)
        except (FileNotFoundError, ManifestVerificationError, RuntimeError, ValueError) as error:
            return self._record(
                StarterResult(
                    launched=False,
                    message=str(error),
                    usb_root=volume.mount_path,
                )
            )

        lock_path = spec.usb_root / "runtime" / "assistant.lock"
        lock_status = inspect_instance_lock(lock_path)
        if lock_status == "active":
            return self._record(
                StarterResult(
                    launched=False,
                    message=f"Assistant already running from {spec.usb_root}.",
                    usb_root=spec.usb_root,
                )
            )
        if lock_status == "invalid":
            return self._record(
                StarterResult(
                    launched=False,
                    message=(
                        "Assistant runtime lock is invalid. Confirm no assistant process is "
                        "running before removing the lock."
                    ),
                    usb_root=spec.usb_root,
                )
            )
        if lock_status == "stale":
            lock_path.unlink(missing_ok=True)

        try:
            self._running_process = self.launcher.launch(spec)
        except OSError as error:
            return self._record(
                StarterResult(
                    launched=False,
                    message=f"Assistant launch failed: {error}",
                    usb_root=volume.mount_path,
                )
            )
        self._running_usb_root = volume.mount_path
        return self._record(
            StarterResult(
                launched=True,
                message=f"Launched assistant from trusted USB: {volume.mount_path}",
                usb_root=volume.mount_path,
            )
        )

    def run_watch_loop(self, *, iterations: int | None = None) -> None:
        """Poll for the trusted USB until stopped."""

        completed = 0
        while iterations is None or completed < iterations:
            self.scan_and_launch()
            completed += 1
            if iterations is not None and completed >= iterations:
                break
            self._sleep(self.config.poll_interval_seconds)

    def find_trusted_volumes(self) -> list[UsbVolume]:
        """Return all currently trusted removable volumes."""

        return [volume for volume in self.volume_provider.list_volumes() if self.is_trusted_volume(volume)]

    def is_trusted_volume(self, volume: UsbVolume) -> bool:
        """Validate the removable-volume label and host-pinned USB identity."""

        if volume.volume_label.casefold() != self.config.expected_volume_label.casefold():
            return False
        try:
            identity = UsbIdentity.load(self.identity_path(volume))
        except ManifestVerificationError:
            return False
        return identity.usb_id == self.config.expected_usb_id

    def identity_path(self, volume: UsbVolume) -> Path:
        """Return the host-configured identity path for a candidate volume."""

        return self._resolve_within_usb_root(volume.mount_path.resolve(), self.config.identity_file)

    def build_launch_spec(self, volume: UsbVolume) -> LaunchSpec:
        """Resolve the assistant command and environment for a trusted USB."""

        usb_root = volume.mount_path.resolve()
        identity = UsbIdentity.load(
            self._resolve_within_usb_root(usb_root, self.config.identity_file)
        )
        if identity.usb_id != self.config.expected_usb_id:
            raise ManifestVerificationError("USB identity does not match this prepared host.")
        active = ActiveRelease.load(
            self._resolve_within_usb_root(usb_root, self.config.active_release_file)
        )
        releases_root = self._resolve_within_usb_root(usb_root, self.config.releases_dir)
        release_dir = self._resolve_within_usb_root(
            releases_root,
            active.release_id,
        )
        if not release_dir.is_dir():
            raise FileNotFoundError(f"Active release directory is missing: {release_dir}")
        manifest = ReleaseManifest.load(release_dir / MANIFEST_NAME)
        executable_path = manifest.verify(
            release_dir,
            release_dir / SIGNATURE_NAME,
            public_key=self.config.manifest_public_key,
            expected_usb_id=identity.usb_id,
            expected_release_id=active.release_id,
        )
        if not executable_path.is_file():
            raise FileNotFoundError(f"Packaged assistant executable is missing: {executable_path}")
        runtime_dir = (usb_root / "runtime").resolve()
        shutdown_request = runtime_dir / "shutdown.request"
        shutdown_request.unlink(missing_ok=True)

        return LaunchSpec(
            usb_root=usb_root,
            cwd=release_dir,
            executable_path=executable_path,
            release_id=active.release_id,
            command=(
                str(executable_path),
                "--window",
                "--start-minimized",
                "--usb-root",
                str(usb_root),
                "--runtime-dir",
                str(runtime_dir),
            ),
            env_overrides={
                "VOICE_CONTROL_USB_USB_ROOT": str(usb_root),
                "VOICE_CONTROL_USB_RUNTIME_DIR": str(runtime_dir),
            },
        )

    def request_safe_shutdown(self) -> StarterResult:
        """Request cooperative assistant exit and wait for its runtime lock to clear."""

        trusted_volumes = self.find_trusted_volumes()
        if not trusted_volumes:
            return self._record(StarterResult(False, "Trusted USB not detected."))
        if len(trusted_volumes) > 1:
            return self._record(
                StarterResult(False, "Multiple trusted USB volumes detected. Shutdown skipped.")
            )
        volume = trusted_volumes[0]
        runtime_dir = (volume.mount_path.resolve() / "runtime").resolve()
        lock_path = runtime_dir / "assistant.lock"
        request_path = runtime_dir / "shutdown.request"
        if not lock_path.exists():
            request_path.unlink(missing_ok=True)
            return self._record(
                StarterResult(False, "Assistant is not running; USB is ready for removal.", volume.mount_path)
            )

        runtime_dir.mkdir(parents=True, exist_ok=True)
        request_path.write_text(
            f'{{"requested_at":"{datetime.now(timezone.utc).isoformat()}"}}\n',
            encoding="utf-8",
        )
        deadline = self._monotonic() + self.config.shutdown_timeout_seconds
        while lock_path.exists() and self._monotonic() < deadline:
            self._sleep(0.1)
        if lock_path.exists():
            return self._record(
                StarterResult(
                    False,
                    "Assistant did not stop in time. Do not remove the USB yet.",
                    volume.mount_path,
                )
            )
        request_path.unlink(missing_ok=True)
        self._running_process = None
        self._running_usb_root = None
        return self._record(
            StarterResult(False, "Assistant stopped; USB is ready for removal.", volume.mount_path)
        )

    @staticmethod
    def _resolve_within_usb_root(usb_root: Path, relative_path: str) -> Path:
        normalized_relative_path = relative_path.replace("\\", "/")
        if Path(normalized_relative_path).is_absolute():
            raise ValueError(f"Invalid USB layout path must be relative: {relative_path}")
        candidate = (usb_root / normalized_relative_path).resolve()
        try:
            candidate.relative_to(usb_root)
        except ValueError as error:
            raise ValueError(
                f"Invalid USB layout path escapes trusted USB root: {relative_path}"
            ) from error
        return candidate

    def _clear_finished_process(self) -> None:
        if self._running_process is None:
            return
        if self._running_process.poll() is None:
            return
        self._running_process = None
        self._running_usb_root = None

    def _record(self, result: StarterResult) -> StarterResult:
        self.logger.write(result.message)
        return result
