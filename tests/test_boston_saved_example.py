"""Focused safety checks for the saved-result entry point (standard library only)."""

from __future__ import annotations

import csv
import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "examples" / "boston" / "run_saved_example.py"
COMPONENT = SCRIPT.parent / "behavior_feedback_r1_semantic_fix_r1"
spec = importlib.util.spec_from_file_location("run_saved_example", SCRIPT)
assert spec and spec.loader
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class SavedExampleSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        private_root = os.environ.get("BOSTON_TEST_TMP")
        self.temporary = tempfile.TemporaryDirectory(dir=private_root)
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_manifest(self, source_file: str = "data/sample.csv") -> Path:
        data = self.root / "component" / "data"
        data.mkdir(parents=True)
        manifest = data / "public_table_manifest.csv"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("table_name", "source_file", "expected_rows", "sha256"))
            writer.writerow(("sample", source_file, 1, "0" * 64))
        return manifest

    def accepted_manifest(self) -> Path:
        source_root = Path(os.environ.get("BOSTON_TEST_DATA", COMPONENT))
        source = source_root / "data" / "public_table_manifest.csv"
        if not source.is_file():
            self.fail("Set BOSTON_TEST_DATA to the accepted extracted public component.")
        data = self.root / "component" / "data"
        data.mkdir(parents=True)
        destination = data / source.name
        shutil.copy2(source, destination)
        return destination

    def run_cli(self, data: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--data-dir", str(data),
                               "--output", str(output)], capture_output=True, text=True)

    def test_missing_mandatory_csv_fails(self) -> None:
        self.accepted_manifest()
        output = self.root / "out"
        completed = self.run_cli(self.root / "component", output)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Missing mandatory CSV", completed.stderr)
        self.assertFalse(output.exists())

    def test_hash_mismatch_fails(self) -> None:
        manifest = self.accepted_manifest()
        with manifest.open("r", encoding="utf-8", newline="") as handle:
            first = next(csv.DictReader(handle))
        target = self.root / "component" / first["source_file"]
        target.write_text("source_id\nchanged\n", encoding="utf-8")
        output = self.root / "out"
        completed = self.run_cli(self.root / "component", output)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Hash mismatch", completed.stderr)
        self.assertFalse(output.exists())

    def test_manifest_traversal_rejected(self) -> None:
        manifest = self.accepted_manifest()
        with manifest.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["source_file"] = "data/../outside.csv"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["table_name", "source_file", "expected_rows", "sha256"])
            writer.writeheader()
            writer.writerows(rows)
        output = self.root / "out"
        completed = self.run_cli(self.root / "component", output)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Unsafe manifest", completed.stderr)
        self.assertFalse(output.exists())

    def test_output_overlap_rejected(self) -> None:
        data = self.root / "component"
        data.mkdir()
        completed = self.run_cli(data, data / "results")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("overlaps", completed.stderr)
        self.assertFalse((data / "results").exists())

    def test_builder_preserves_leading_zero_identifier(self) -> None:
        manifest = self.make_manifest()
        (manifest.parent / "sample.csv").write_text("zone_id,person_trips\n00123,2\n", encoding="utf-8")
        database = self.root / "tiny.sqlite"
        command = [sys.executable, "-B", str(COMPONENT / "build_public_database.py"),
                   "--manifest", str(manifest), "--output", str(database)]
        completed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        connection = sqlite3.connect(database)
        try:
            self.assertEqual(connection.execute("SELECT zone_id,typeof(zone_id) FROM sample").fetchone(), ("00123", "text"))
        finally:
            connection.close()

    def test_help_has_no_output_side_effect(self) -> None:
        output = self.root / "not-created"
        completed = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help", "--output", str(output)],
                                   capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Rebuild and inspect", completed.stdout)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
