"""No-solve integrity checks for the cumulative current-results public update."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HK = ROOT / "examples" / "hong-kong" / "gmns_pilot_r1"
DIST = ROOT / "algorithms" / "distributed_assignment"


class CurrentResultsPublicR1(unittest.TestCase):
    def test_hong_kong_manifest_and_gate(self):
        with (HK / "MANIFEST_SHA256.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 63)
        for row in rows:
            path = HK / row["relative_path"]
            data = path.read_bytes()
            self.assertEqual(len(data), int(row["bytes"]), row["relative_path"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"], row["relative_path"])
        gate = json.loads((HK / "instance" / "ASSIGNMENT_GATE.json").read_text(encoding="utf-8"))
        self.assertIs(gate["assignment_ready"], False)
        self.assertIs(gate["assignment_run"], False)
        self.assertIs(gate["solver_invoked"], False)
        self.assertEqual(len(list((HK / "visuals").glob("*.svg"))), 5)

    def test_lagrangian_and_admm_selected_rows(self):
        with (DIST / "lagrangian_r2" / "SIOUX_ACCEPTED_RESULT_SUMMARY.csv").open(newline="", encoding="utf-8") as handle:
            lag = {row["case"]: row for row in csv.DictReader(handle)}
        with (DIST / "admm_r1" / "ADMM_ACCEPTED_RESULT_SUMMARY.csv").open(newline="", encoding="utf-8") as handle:
            admm = {row["case"]: row for row in csv.DictReader(handle)}
        self.assertEqual(set(lag), {"Sioux_200OD", "Sioux_250OD"})
        self.assertEqual(set(admm), set(lag))
        for case in lag:
            self.assertEqual(lag[case]["evaluation_status"], "PASS")
            lower = float(lag[case]["dual_bound"])
            upper = float(lag[case]["feasible_primal"])
            self.assertLessEqual(lower, upper)
            self.assertAlmostEqual((upper - lower) / upper, float(lag[case]["duality_gap"]), places=10)
            self.assertEqual(admm[case]["status"], "PASS")
            self.assertEqual(admm[case]["capacity_and_conservation_gate"], "PASS")
            objective = float(admm[case]["admm_objective_vehicle_min"])
            reference = float(admm[case]["arc_lp_objective_vehicle_min"])
            self.assertAlmostEqual((objective - reference) / reference,
                                   float(admm[case]["relative_difference_fraction"]), places=10)
            stem = case.lower() + "_objective_difference"
            for suffix in (".svg", ".png"):
                self.assertTrue((DIST / "admm_r1" / "figures" / (stem + suffix)).is_file())

    def test_gated_claims_visible_without_regressing_cg(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for claim in ("1.1002%", "6.062 min", "assignment_ready=false",
                      "independent pricing closure for 10/10 demands"):
            self.assertIn(claim, readme)
        self.assertIn("independent_pricing_closure_established = false",
                      (ROOT / "docs" / "cases" / "sioux-space-time.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
