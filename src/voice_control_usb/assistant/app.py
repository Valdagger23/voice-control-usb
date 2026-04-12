"""Assistant orchestration for the deterministic MVP."""

from __future__ import annotations

from pathlib import Path

from voice_control_usb.core.parser import CommandParser
from voice_control_usb.core.proposals import ProposalStore
from voice_control_usb.excel.adapter import StubExcelAdapter
from voice_control_usb.executor.engine import ExecutionEngine


class AssistantApp:
    """Glue parser, executor, and proposal logging together."""

    def __init__(self, proposal_path: Path) -> None:
        self.parser = CommandParser()
        self.executor = ExecutionEngine(excel=StubExcelAdapter())
        self.proposals = ProposalStore(proposal_path)

    def handle_text(self, text: str) -> str:
        parsed = self.parser.parse(text)
        if parsed.command:
            return self.executor.execute(parsed.command)

        assert parsed.proposal is not None
        self.proposals.record(parsed.proposal)
        return f"Unsupported command logged for review: {parsed.proposal.reason}"
