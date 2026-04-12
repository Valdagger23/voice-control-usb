"""Assistant orchestration for the deterministic MVP."""

from __future__ import annotations

from pathlib import Path

from voice_control_usb.core.parser import CommandParser
from voice_control_usb.core.proposals import ProposalStore
from voice_control_usb.desktop.adapter import DesktopAdapter, StubDesktopAdapter
from voice_control_usb.desktop.registry import AppAliasRegistry
from voice_control_usb.excel.adapter import ExcelAdapter, StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class AssistantApp:
    """Glue parser, executor, and proposal logging together."""

    def __init__(
        self,
        proposal_path: Path,
        excel: ExcelAdapter | None = None,
        desktop: DesktopAdapter | None = None,
    ) -> None:
        self.parser = CommandParser()
        self.executor = ExecutionEngine(
            excel=excel or StubExcelAdapter(),
            desktop=desktop or StubDesktopAdapter(aliases=AppAliasRegistry.load_default()),
        )
        self.proposals = ProposalStore(proposal_path)

    def handle_text(self, text: str) -> str:
        parsed = self.parser.parse(text)
        if parsed.command:
            return self.executor.execute(parsed.command)

        assert parsed.proposal is not None
        self.proposals.record(parsed.proposal)
        return f"Unsupported command logged for review: {parsed.proposal.reason}"
