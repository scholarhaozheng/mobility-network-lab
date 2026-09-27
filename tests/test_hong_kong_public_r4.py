"""No-solve guards for the bounded Hong Kong R2–R5 public integration."""
import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs/assets/hong_kong/full_stack_r5"


class HongKongPublicR4(unittest.TestCase):
    def test_current_pages_and_three_city_matrix(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        matrix = readme.split("## 02 / What each case demonstrates", 1)[1].split(
            '<a id="boston"></a>', 1
        )[0]
        self.assertIn("| Boston | Sioux Falls | Hong Kong bounded case |", matrix)
        for phrase in ("4.3502187198", "75.03632985794835", "10/10 demands", "0.7444%"):
            self.assertIn(phrase, readme)
        case = (ROOT / "docs/cases/hong-kong-space-time.md").read_text(encoding="utf-8")
        self.assertIn("ADMM R2", case)
        self.assertIn("no accepted objective", case)
        for page in (
            "docs/cases/hong-kong.md",
            "docs/cases/hong-kong-four-stage.md",
            "docs/cases/hong-kong-static-assignment.md",
            "docs/cases/hong-kong-space-time.md",
            "docs/datasets/hong-kong-gmns.md",
            "docs/methods/hong-kong-evidence-contract.md",
        ):
            self.assertTrue((ROOT / page).is_file(), page)
            self.assertTrue((ROOT / page).with_suffix(".html").is_file(), page)

    def test_public_candidate_is_exact_and_redacted(self):
        manifest = json.loads((BUNDLE / "HASH_MANIFEST.json").read_text(encoding="utf-8"))
        actual = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*") if p.is_file()}
        self.assertEqual(actual - {"HASH_MANIFEST.json"}, set(manifest))
        self.assertFalse(list(BUNDLE.rglob("*.html")))
        self.assertFalse((BUNDLE / "case/dynamic_columns.csv").exists())
        self.assertFalse((BUNDLE / "closure/CLOSURE_FINAL_POOL.csv").exists())
        cert = json.loads((BUNDLE / "closure/INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json").read_text(encoding="utf-8"))
        self.assertTrue(cert["independent_pricing_closure_established"])
        self.assertEqual(cert["demand_count"], 10)
        with (BUNDLE / "HONG_KONG_CG_R5_FIGURE_MANIFEST.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 26)


if __name__ == "__main__":
    unittest.main()
