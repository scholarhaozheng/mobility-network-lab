"""No-solve regression checks for case coverage and accepted figure bindings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "docs/assets/boston/assignment_methods_r1"
STEMS = (
    "boston_abs_planned_fw_flow",
    "boston_abs_planned_l3_rank26_flow",
    "boston_abs_planned_l3_rank52_flow",
    "boston_abs_planned_l3_rank26_minus_fw",
    "boston_abs_planned_l3_rank52_minus_fw",
)
GMNS = ("gmns_connected_layers.png", "gps_to_gmns_evidence.png")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    i, j = text.find(start), text.find(end)
    if i < 0 or j <= i:
        raise AssertionError(f"missing or misplaced case section: {start}")
    return text[i:j]


def coverage(readme: str, home: str, detail: str) -> None:
    for image in GMNS:
        if f'gmns_in_action_r1/{image}' not in readme or f'gmns_in_action_r1/{image}' not in home:
            raise AssertionError(f"accepted inline GMNS evidence missing: {image}")
    b_readme = section(readme, "## Boston case · saved assignment methods", "## Sioux Falls benchmark series")
    s_readme = section(readme, "## Sioux Falls benchmark series", "## Mobility data support")
    b_home = section(home, 'id="boston-case"', 'id="sioux-case"')
    s_home = section(home, 'id="sioux-case"', "</main>")
    for text in (b_readme, b_home, detail):
        for token in ("ABS_PLANNED", "FW", "130", "rank 26", "rank 52", "outer 02"):
            if token not in text:
                raise AssertionError(f"Boston case lacks {token}")
        for stem in STEMS:
            if stem + ".png" not in text:
                raise AssertionError(f"Boston case lacks embedded {stem}")
        if "boston_panel_flow_s1.png" in text and "boston_abs_planned_fw_flow.png" not in text:
            raise AssertionError("semantic S1 image substituted for ABS_PLANNED FW")
    for text in (s_readme, s_home):
        for token in ("static FW", "A_REG001", "B_BECKMANN", "4.381867%", "200OD", "250OD"):
            if token.lower() not in text.lower():
                raise AssertionError(f"Sioux case lacks {token}")


def source_binding(manifest: dict) -> None:
    if manifest.get("source_archive_sha256") != "c2a7f64115659aa9c338f48c64aa17e7b3b084ebd4f1175dbbf29f9fc0075112":
        raise AssertionError("wrong accepted Boston native archive")
    if manifest.get("statistics", {}).get("matched_physical_links") != 5091:
        raise AssertionError("map link coverage is not 5091")
    if manifest.get("flow_columns") != {"FW": "volume", "full_path": "volume",
                                         "rank26": "v_from_paths", "rank52": "v_from_paths"}:
        raise AssertionError("map reads a wrong result column")
    if manifest.get("selected_runs") != {"FW": "ABS_PLANNED", "rank26": "outer_02", "rank52": "outer_02"}:
        raise AssertionError("map selects wrong scenario or native iterate")
    base = ROOT / "examples/boston/assignment_methods_r1"
    for key, relative in manifest.get("source_members", {}).items():
        source = base / relative
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != manifest.get("source_hashes", {}).get(key):
            raise AssertionError(f"mapped source member mismatch: {key}")
    names = manifest.get("image_hashes", {})
    for stem in STEMS:
        for suffix in ("png", "svg"):
            filename = f"{stem}.{suffix}"
            file = ASSET / filename
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != names.get(filename):
                raise AssertionError(f"missing or changed map: {filename}")
    table = ASSET / manifest["plotting_table"]
    if hashlib.sha256(table.read_bytes()).hexdigest() != manifest.get("table_sha256"):
        raise AssertionError("full-precision plotting table differs")
    if manifest["signed_normalization"]["min"] != -manifest["signed_normalization"]["max"]:
        raise AssertionError("difference maps lack shared zero-centred range")


class CaseFirstPresentation(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = read("README.md")
        self.home = read("docs/index.html")
        self.detail = read("docs/cases/boston-assignment.html")
        self.manifest = json.loads(read("docs/assets/boston/assignment_methods_r1/BOSTON_ASSIGNMENT_FIGURE_SOURCES.json"))

    def test_actual_primary_surfaces(self) -> None:
        coverage(self.readme, self.home, self.detail)

    def test_negative_gmns_image_removal(self) -> None:
        for image in GMNS:
            with self.assertRaisesRegex(AssertionError, "GMNS"):
                coverage(self.readme.replace("gmns_in_action_r1/" + image, "badge.png"), self.home, self.detail)
            with self.assertRaisesRegex(AssertionError, "GMNS"):
                coverage(self.readme, self.home.replace("gmns_in_action_r1/" + image, "badge.png"), self.detail)

    def test_negative_boston_method_removal(self) -> None:
        for token in ("rank 26", "rank 52", "130", "FW"):
            with self.assertRaises(AssertionError):
                altered = self.readme.replace(token, "removed")
                coverage(altered, self.home, self.detail)

    def test_negative_old_s1_map_substitution(self) -> None:
        with self.assertRaises(AssertionError):
            altered = self.home.replace("boston_abs_planned_fw_flow.png", "boston_panel_flow_s1.png")
            coverage(self.readme, altered, self.detail)

    def test_actual_map_sources_and_hashes(self) -> None:
        source_binding(self.manifest)

    def test_case_numbers_follow_registered_saved_rows(self) -> None:
        runs = json.loads(read("catalog/case-runs.json"))["runs"]
        b_readme = section(self.readme, "## Boston case · saved assignment methods", "## Sioux Falls benchmark series")
        s_readme = section(self.readme, "## Sioux Falls benchmark series", "## Mobility data support")
        b_home = section(self.home, 'id="boston-case"', 'id="sioux-case"')
        s_home = section(self.home, 'id="sioux-case"', "</main>")
        for run in runs:
            if run["run_id"] in ("boston-abs-planned-fw", "boston-abs-planned-full-path",
                                 "boston-abs-planned-l3-rank26-outer02", "boston-abs-planned-l3-rank52-outer02",
                                 "sioux-native-l3-a-reg001-outer04", "sioux-native-l3-b-beckmann-outer04"):
                pages = (b_readme, b_home) if run["case_id"] == "boston" else (s_readme, s_home)
                value = str(run["objective"])
                for page in pages:
                    if value not in page.replace(",", ""):
                        raise AssertionError(f"registered objective missing from primary case: {run['run_id']}")

    def test_negative_map_source_binding(self) -> None:
        for field, bad in (("flow_columns", {**self.manifest["flow_columns"], "rank52": "ref_volume"}),
                           ("selected_runs", {**self.manifest["selected_runs"], "rank26": "outer_01"})):
            with self.assertRaises(AssertionError):
                source_binding({**self.manifest, field: bad})
        with self.assertRaises(AssertionError):
            source_binding({**self.manifest, "statistics": {"matched_physical_links": 5090}})

    def test_no_solver_import_in_saved_inspector(self) -> None:
        inspector = read("tools/mcl_results.py")
        for forbidden in ("SolverFactory", "scipy.optimize", "minimize(", "solve_fw_refined", "build_path_pool"):
            self.assertNotIn(forbidden, inspector)

    def test_saved_inspector_negative_ids_and_missing_data(self) -> None:
        tool = ROOT / "tools/mcl_results.py"
        unknown = subprocess.run([sys.executable, "-B", str(tool), "show", "--run", "not-registered"],
                                 capture_output=True, text=True)
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("unknown registered run", unknown.stderr)
        with tempfile.TemporaryDirectory() as folder:
            missing = subprocess.run([sys.executable, "-B", str(tool), "verify-saved", "--run",
                                      "boston-abs-planned-l3-rank26-outer02", "--data-root", folder],
                                     capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("missing", missing.stderr)


if __name__ == "__main__":
    unittest.main()
