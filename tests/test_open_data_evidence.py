"""Data-free checks for the compact OMDV-derived evidence catalog."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mobilitylab.data.evidence import headline_metrics, load_evidence_catalog


class OpenDataEvidenceTests(unittest.TestCase):
    def test_catalog_contract_and_accepted_values(self):
        metrics = headline_metrics(load_evidence_catalog())
        self.assertEqual(metrics["global_city_frame.ghsl_urban_centres"], 11422)
        self.assertEqual(metrics["gtfs_static.all_retained_unique_content_hashes"], 4425)
        self.assertEqual(metrics["gtfs_static.cities_with_inside_polygon_stop_evidence"], 2959)
        self.assertEqual(metrics["gtfs_realtime.endpoint_representatives"], 2465)

    def test_layers_cannot_be_summed(self):
        catalog = load_evidence_catalog()
        self.assertFalse(catalog["layers_are_additive"])
        self.assertTrue(all(layer["additive_across_layers"] is False for layer in catalog["layers"]))

    def test_authorized_omdv_code_is_hash_allowlisted(self):
        provenance = json.loads((ROOT / "catalog" / "omdv-provenance.json").read_text())
        self.assertEqual(
            provenance["code_redistribution_status"],
            "selected_original_files_authorized_mit",
        )
        allowlist = json.loads(
            (ROOT / provenance["authorized_file_allowlist"]).read_text()
        )
        copied_sources = {
            item["path"]
            for item in provenance["candidate_code_files"]
            if item["public_tree_action"] == "copied_authorized_mit"
        }
        self.assertEqual(
            copied_sources,
            {
                "src/omdv/geospatial/external_city_universe.py",
                "src/omdv/geospatial/city_matching.py",
                "src/omdv/ingest/mobility_database.py",
                "src/omdv/ingest/catalog_summary.py",
            },
        )
        for item in allowlist["files"]:
            target = ROOT / item["destination_path"]
            self.assertTrue(target.is_file())
            self.assertEqual(
                hashlib.sha256(target.read_bytes()).hexdigest(),
                item["destination_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
