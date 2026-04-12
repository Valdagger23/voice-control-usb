"""Proposal persistence for unsupported commands."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from voice_control_usb.core.models import UnsupportedProposal


class ProposalStore:
    """Append unsupported commands to a reviewable JSONL file."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    def record(self, proposal: UnsupportedProposal) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(proposal)) + "\n")
