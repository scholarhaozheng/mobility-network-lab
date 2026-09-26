"""No-solver integrity checks for the accepted ADMM R2 public release."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "admm_r2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ADMMR2PublicSaved(unittest.TestCase):
    def test_frozen_source_and_plan(self):
        record = json.loads((ASSETS / "provenance" / "experiment_plan_sha256.json").read_text(encoding="utf-8"))
        self.assertEqual(record["selected_variant"], "R2_S")
        self.assertTrue(record["frozen_before_boston"])
        self.assertEqual(record["independent_evaluator_optimizer_calls"], 0)
        self.assertEqual(digest(ASSETS / "provenance" / "experiment_plan.json"), record["accepted_plan_sha256"])
        for name, expected in record["source_sha256"].items():
            self.assertEqual(digest(ROOT / "algorithms" / "admm_r2" / name), expected, name)

    def test_complete_figure_family_and_hashes(self):
        figures = ASSETS / "figures"
        svg = sorted(figures.glob("*.svg"))
        self.assertEqual(len(svg), 22)
        self.assertEqual(len(list(figures.glob("*.png"))), 22)
        self.assertEqual(len(list(figures.glob("*.caption.md"))), 15)
        for image in svg:
            stem = image.stem
            self.assertTrue((figures / f"{stem}.png").is_file(), stem)
            sidecar = json.loads((figures / f"{stem}.source.json").read_text(encoding="utf-8"))
            svg_hash = sidecar.get("svg_sha256", sidecar.get("accepted_original_svg_sha256"))
            self.assertEqual(digest(image), svg_hash, stem)
            self.assertEqual(digest(figures / f"{stem}.png"), sidecar["png_sha256"], stem)

    def test_boston_derived_table_and_rights_boundary(self):
        table = ASSETS / "data" / "boston_10od_physical_link_admm_lp_comparison.csv"
        with table.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 125)
        self.assertEqual(set(rows[0]), {"physical_link_id", "admm_flow", "lp_flow", "admm_minus_lp"})
        self.assertEqual(len({row["physical_link_id"] for row in rows}), 125)
        for row in rows:
            self.assertAlmostEqual(float(row["admm_flow"]) - float(row["lp_flow"]),
                                   float(row["admm_minus_lp"]), places=10)
        source = json.loads(table.with_suffix(".source.json").read_text(encoding="utf-8"))
        self.assertEqual(source["rows"], 125)
        self.assertEqual(source["geometry_source_sha256"], digest(
            ROOT / "docs" / "assets" / "boston" / "space_time_cg_r4" / "data" / "physical_link_flow_geometry.csv"))
        self.assertFalse(list(ASSETS.rglob("state.npz")))
        self.assertFalse(list(ASSETS.rglob("dynamic_arc.csv")))
        self.assertFalse(list(ASSETS.rglob("dynamic_demand.csv")))
        self.assertFalse(list(ASSETS.rglob("*reference_flow*.csv")))
        self.assertFalse(list((ASSETS / "data").glob("sioux*.csv")))

    def test_case_and_method_pages(self):
        for relative in ("docs/methods/admm-space-time.md", "docs/cases/sioux-admm.md",
                         "docs/cases/boston-admm.md"):
            markdown = ROOT / relative
            self.assertTrue(markdown.is_file())
            self.assertTrue(markdown.with_suffix(".html").is_file())
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("admm_results_overview.png", readme)
        self.assertIn("Boston 10 OD | 253 | 6.68e-6", readme)
        for stem in (
            "convergence_Sioux_200OD", "convergence_Sioux_250OD", "convergence_Boston_10OD",
            "admm_sioux_200_local_conservation_heatmap",
            "admm_boston_10od_local_conservation_heatmap",
            "admm_sioux_200_final_physical_link_flow", "admm_sioux_250_final_physical_link_flow",
            "admm_boston_10od_final_physical_link_flow",
            "admm_sioux_200_minus_lp", "admm_sioux_250_minus_lp", "admm_boston_10od_minus_lp",
        ):
            self.assertIn(f"docs/assets/admm_r2/figures/{stem}.png", readme, stem)
        self.assertIn("A separate 250-OD commodity heatmap was not released", readme)
        self.assertNotIn("admm_sioux_250_local_conservation_heatmap", readme)
        homepage = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="admm-r2-figures"', homepage)
        for stem in (
            "convergence_Sioux_200OD", "convergence_Sioux_250OD", "convergence_Boston_10OD",
            "admm_sioux_200_local_conservation_heatmap",
            "admm_boston_10od_local_conservation_heatmap",
            "admm_sioux_200_final_physical_link_flow", "admm_sioux_250_final_physical_link_flow",
            "admm_boston_10od_final_physical_link_flow",
            "admm_sioux_200_minus_lp", "admm_sioux_250_minus_lp", "admm_boston_10od_minus_lp",
        ):
            self.assertIn(f"assets/admm_r2/figures/{stem}.png", homepage, stem)


if __name__ == "__main__":
    unittest.main()
