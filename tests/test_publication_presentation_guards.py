"""Regression fixtures for current atlas structure and exact HK disclosure."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/visuals"))
sys.path.insert(0, str(ROOT / "tools"))
from check_readme_pages import parse_atlas_data
from check_hk10_publication import (RECEIPT, RECORDS, PROTECTED_SECTIONS,
                                   expected_scope, protected_hash, sha, validate)
from freeze_hk10_publication import build_record


class AtlasDataTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "docs/assets/reading/atlas-data.js").read_text(encoding="utf-8")

    def test_base_and_additive_cities_are_parsed(self):
        model = parse_atlas_data(self.source)
        self.assertEqual(len(model["cities"]), 9)
        self.assertIn("berkeley", {city["id"] for city in model["cities"]})

    def test_appended_unknown_code_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unexpected trailing"):
            parse_atlas_data(self.source + "\nwindow.MCL_ATLAS_MODEL.cities=[];")

    def test_duplicate_city_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate atlas city"):
            parse_atlas_data(self.source.replace('"id":"ann-arbor"', '"id":"boston"', 1))

    def test_bad_json_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_atlas_data(self.source.replace('"cities":[', '"cities":[INVALID', 1))


class HKPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        cls.root = Path(cls.fixture.name)
        pages, science, _ = expected_scope(ROOT)
        for path in set(pages) | set(science) | set(RECORDS):
            target = cls.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        cls.record = build_record(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def write_record(self, record):
        (self.root / RECEIPT).write_text(json.dumps(record), encoding="utf-8")

    def setUp(self):
        self.write_record(self.record)

    def test_current_presentation_keeps_exact_scientific_scope(self):
        result = validate(self.root)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["protected_sections"], 5)
        self.assertGreater(result["scientific_hashes_retained"], 30)

    def test_page_byte_tamper_is_rejected(self):
        path = self.root / "README.md"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\nUnrecorded publication change\n")
            self.assertIn("HK10 continuation file missing or changed: README.md", validate(self.root)["errors"])
        finally:
            path.write_bytes(original)

    def test_changed_scientific_payload_cannot_be_refrozen(self):
        path = self.root / "docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n")
            self.assertEqual(validate(self.root)["status"], "FAIL")
            with self.assertRaisesRegex(ValueError, "changed HK scientific asset"):
                build_record(self.root)
        finally:
            path.write_bytes(original)

    def test_scientific_text_change_fails_even_with_new_page_hash(self):
        path = self.root / "docs/cases/hong-kong.html"
        original = path.read_bytes()
        try:
            text = original.decode("utf-8")
            self.assertIn("model-generated", text)
            path.write_text(text.replace("model-generated", "observed-real-world", 1), encoding="utf-8")
            altered = copy.deepcopy(self.record)
            altered["current_presentation_paths_sha256"]["docs/cases/hong-kong.html"] = sha(path)
            self.write_record(altered)
            self.assertIn("HK10 scientific presentation content changed: docs/cases/hong-kong.html", validate(self.root)["errors"])
        finally:
            path.write_bytes(original)

    def test_receipt_cannot_expand_scope_or_claim_new_approval(self):
        altered = copy.deepcopy(self.record)
        altered["new_artifact_level_scientific_approval"] = True
        altered["current_presentation_paths_sha256"]["docs/assets/unapproved.csv"] = "0" * 64
        self.write_record(altered)
        result = validate(self.root)
        self.assertIn("HK10 continuation changes the allowed presentation page set", result["errors"])
        self.assertIn("HK10 continuation overstates authority: new_artifact_level_scientific_approval", result["errors"])

    def test_altered_historical_baseline_is_rejected(self):
        altered = copy.deepcopy(self.record)
        altered["baseline_presentation_paths_sha256"]["README.md"] = "0" * 64
        self.write_record(altered)
        self.assertIn("HK10 continuation old page hashes differ from historical records", validate(self.root)["errors"])

    def test_only_empty_compatibility_anchors_are_normalized(self):
        base = '<main><p>77 model-generated arcs</p></main>'
        self.assertEqual(protected_hash(base, 'main'), protected_hash('<main><a id="alias"></a><p>77 model-generated arcs</p></main>', 'main'))
        self.assertNotEqual(protected_hash(base, 'main'), protected_hash('<main><a id="alias">A changed scientific claim</a><p>77 model-generated arcs</p></main>', 'main'))


if __name__ == "__main__":
    unittest.main()
