"""Tests for release-key operations used by the Windows packaging script."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from packaging_helpers import create_signing_material
from scripts.release_tool import export_public_key


class ReleaseToolTests(unittest.TestCase):
    def test_export_public_key_matches_existing_signing_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            private_key, expected_public_key = create_signing_material(root)
            exported_path = root / "launcher-public-key.txt"

            exported = export_public_key(private_key, exported_path)

            self.assertEqual(exported, expected_public_key)
            self.assertEqual(exported_path.read_text(encoding="ascii").strip(), expected_public_key)


if __name__ == "__main__":
    unittest.main()
