"""Trusted USB starter and watcher implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from time import sleep
from typing import Protocol

from voice_control_usb.starter.config import StarterConfig


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
    ) -> None:
        self.config = config
        self.volume_provider = volume_provider
        self.launcher = launcher or SubprocessLauncher()
        self.logger = logger or StarterLogger(config.log_path)
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
        except FileNotFoundError as error:
            return self._record(
                StarterResult(
                    launched=False,
                    message=str(error),
                    usb_root=volume.mount_path,
                )
            )
        self._running_process = self.launcher.launch(spec)
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
            sleep(self.config.poll_interval_seconds)

    def find_trusted_volumes(self) -> list[UsbVolume]:
        """Return all currently trusted removable volumes."""

        return [volume for volume in self.volume_provider.list_volumes() if self.is_trusted_volume(volume)]

    def is_trusted_volume(self, volume: UsbVolume) -> bool:
        """Validate volume label and trust marker together."""

        return (
            volume.volume_label.casefold() == self.config.expected_volume_label.casefold()
            and self.marker_path(volume).is_file()
        )

    def marker_path(self, volume: UsbVolume) -> Path:
        """Return the required trust marker path for a candidate volume."""

        return volume.mount_path / self.config.trust_marker

    def build_launch_spec(self, volume: UsbVolume) -> LaunchSpec:
        """Resolve the assistant command and environment for a trusted USB."""

        usb_root = volume.mount_path.resolve()
        cwd = (usb_root / self.config.assistant_workdir).resolve()
        executable_path = (usb_root / self.config.assistant_relative_executable).resolve()
        if not executable_path.is_file():
            raise FileNotFoundError(
                f"Packaged assistant executable not found on trusted USB: {executable_path}"
            )

        return LaunchSpec(
            usb_root=usb_root,
            cwd=cwd,
            executable_path=executable_path,
            command=(str(executable_path),),
            env_overrides={},
        )

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
