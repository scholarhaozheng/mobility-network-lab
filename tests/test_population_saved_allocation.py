"""Negative and released-table checks for the no-solver population verifier."""
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/population"))
from verify_saved_allocation import verify  # noqa: E402


class SavedAllocationChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        source = ROOT / "examples/boston/population_r1/data"
        for name in ("acs_block_group_stats.csv", "acs_block_group_h3_crosswalk.csv", "population_or_household_by_zone.csv"):
            shutil.copy2(source / name, self.folder / name)
        accepted = ROOT / "examples/boston/behavior_feedback_r1_semantic_fix_r1/data"
        for name in ("trip_generation_by_purpose.csv", "external_flow_ledger.csv"):
            shutil.copy2(accepted / name, self.folder / name)

    def tearDown(self):
        self.temp.cleanup()

    def check(self):
        return verify(self.folder, self.folder / "trip_generation_by_purpose.csv",
                      self.folder / "external_flow_ledger.csv")

    def alter(self, filename, edit):
        path = self.folder / filename
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields, rows = list(reader.fieldnames), list(reader)
        fields, rows = edit(fields, rows)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fields, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows)

    def test_released_tables(self):
        result = self.check()
        self.assertEqual(result["source_block_groups"], 174)
        self.assertEqual(result["covered_h3_zones"], 177)

    def test_truncated_leading_zero_sensitive_geoid_fails(self):
        def edit(fields, rows):
            rows[0]["source_geoid"] = "15000US25025010131"
            return fields, rows
        self.alter("acs_block_group_stats.csv", edit)
        with self.assertRaises(ValueError): self.check()

    def test_tampered_weight_fails(self):
        def edit(fields, rows):
            rows[0]["source_area_share"] = str(float(rows[0]["source_area_share"]) + .01)
            return fields, rows
        self.alter("acs_block_group_h3_crosswalk.csv", edit)
        with self.assertRaises(ValueError): self.check()

    def test_tampered_production_fails(self):
        def edit(fields, rows):
            rows[0]["productions_person_trips_daily"] = str(float(rows[0]["productions_person_trips_daily"]) + 1)
            return fields, rows
        self.alter("trip_generation_by_purpose.csv", edit)
        with self.assertRaises(ValueError): self.check()

    def test_missing_field_fails(self):
        def edit(fields, rows):
            fields.remove("households_estimate")
            return fields, rows
        self.alter("acs_block_group_stats.csv", edit)
        with self.assertRaises(ValueError): self.check()


if __name__ == "__main__":
    unittest.main()
