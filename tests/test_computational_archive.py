"""Regression checks for the bounded public computational ZIP exception."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

MODULE = Path(__file__).resolve().parents[1] / "tools/check_computational_archive.py"
spec = importlib.util.spec_from_file_location("archive_gate", MODULE)
archive_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive_gate)


class ComputationalArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs/downloads").mkdir(parents=True)

    def bundle(self, name="tools/example.py", content=b"print('ready')\n", source_content=None, extra=None):
        source = self.root / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(content if source_content is None else source_content)
        archive = self.root / archive_gate.ARCHIVE
        with zipfile.ZipFile(archive, "w") as handle:
            handle.writestr(name, content)
            if extra:
                handle.writestr(*extra)
        manifest = {"schema": "mcl_public_computational_archive_v1", "archive": archive.name,
                    "bytes": archive.stat().st_size, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                    "files": [{"path": name, "source": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}]}
        (self.root / archive_gate.MANIFEST).write_text(json.dumps(manifest))
        return archive

    def test_exact_public_bytes_pass(self):
        self.bundle()
        result = archive_gate.validate(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["allowed_archives"], [archive_gate.ARCHIVE])

    def test_unlisted_member_fails(self):
        self.bundle(extra=("unlisted.py", b"pass\n"))
        self.assertEqual(archive_gate.validate(self.root)["status"], "FAIL")

    def test_source_mismatch_fails(self):
        self.bundle(source_content=b"different source\n")
        self.assertEqual(archive_gate.validate(self.root)["status"], "FAIL")

    def test_archive_tamper_fails(self):
        archive = self.bundle()
        with archive.open("ab") as handle:
            handle.write(b"modified")
        self.assertEqual(archive_gate.validate(self.root)["status"], "FAIL")

    def test_private_path_fails_even_when_manifest_matches(self):
        self.bundle(name="private_data/example.csv", content=b"x\n1\n")
        self.assertEqual(archive_gate.validate(self.root)["status"], "FAIL")

    def test_executable_fails_even_when_manifest_matches(self):
        self.bundle(name="tools/example.exe", content=b"MZ")
        self.assertEqual(archive_gate.validate(self.root)["status"], "FAIL")

    def test_traversal_and_platform_paths_fail(self):
        for name in ("../escape.py", "/abs.py", "C:/machine.py", "tools\\escape.py", "./source.py", "tools//source.py"):
            with self.subTest(name=name):
                self.assertFalse(archive_gate.safe_member(name))

    def test_missing_manifest_fails(self):
        self.bundle()
        (self.root / archive_gate.MANIFEST).unlink()
        self.assertEqual(archive_gate.validate(self.root)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
