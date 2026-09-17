from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mobilitylab.data.catalog_city_workflow import run_catalog_city_workflow
from mobilitylab.omdv.geospatial.city_matching import (
    MATCHED_STATUS,
    match_feeds_to_cities_by_name,
)
from mobilitylab.omdv.geospatial.external_city_universe import (
    read_external_city_universe,
)
from mobilitylab.omdv.ingest.mobility_database import (
    clean_mobility_database_catalog,
)

CATALOG = ROOT / "examples" / "data-tools" / "feeds_sample.csv"
CITIES = ROOT / "examples" / "data-tools" / "external_city_universe_sample.csv"


class AuthorizedOmdvFunctionTests(unittest.TestCase):
    def test_selected_original_functions_run_on_authorized_fixtures(self) -> None:
        feeds = clean_mobility_database_catalog(CATALOG)
        cities = read_external_city_universe(CITIES)
        match_cities = cities.rename(columns={"external_city_id": "city_id"})
        matches = match_feeds_to_cities_by_name(feeds, match_cities)

        self.assertEqual(len(feeds), 5)
        self.assertEqual(set(feeds["feed_type"]), {"gtfs", "gtfs_rt", "gbfs"})
        self.assertEqual(len(cities), 8)
        self.assertEqual(int((matches["match_status"] == MATCHED_STATUS).sum()), 4)
        sao = matches.loc[matches["feed_id"] == "mdb-005"].iloc[0]
        self.assertEqual(sao["match_status"], "unmatched_other")

    def test_workflow_is_input_dependent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            first = run_catalog_city_workflow(CATALOG, CITIES, base / "first")

            changed_cities = pd.read_csv(CITIES)
            changed_cities.loc[
                changed_cities["external_city_id"] == "sample-ext-london", "city_name"
            ] = "London changed"
            changed_path = base / "changed_cities.csv"
            changed_cities.to_csv(changed_path, index=False)
            second = run_catalog_city_workflow(
                CATALOG, changed_path, base / "second"
            )

            self.assertEqual(first["quality"]["matched_feed_records"], 4)
            self.assertEqual(second["quality"]["matched_feed_records"], 2)
            self.assertNotEqual(
                first["inputs"]["cities"]["sha256"],
                second["inputs"]["cities"]["sha256"],
            )

    def test_ambiguous_and_missing_keys_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            catalog = base / "catalog.csv"
            cities = base / "cities.csv"
            pd.DataFrame(
                {
                    "source_id": ["ambiguous", "no-country", "no-city"],
                    "data_type": ["GTFS", "GTFS", "GTFS"],
                    "country_code": ["GB", "", "GB"],
                    "municipality": ["London", "London", ""],
                }
            ).to_csv(catalog, index=False)
            pd.DataFrame(
                {
                    "external_city_id": ["london-1", "london-2"],
                    "city_name": ["London", "London"],
                    "country_iso2": ["GB", "GB"],
                    "country_name": ["United Kingdom", "United Kingdom"],
                    "population": [1, 2],
                    "latitude": [51.5, 51.6],
                    "longitude": [-0.1, -0.2],
                    "source_dataset": ["test", "test"],
                    "source_year": [2026, 2026],
                    "is_capital": [True, True],
                    "is_megacity": [False, False],
                    "notes": ["", ""],
                }
            ).to_csv(cities, index=False)

            report = run_catalog_city_workflow(catalog, cities, base / "out")
            statuses = report["quality"]["match_status_counts"]
            self.assertEqual(report["quality"]["ambiguous_city_keys"], 1)
            self.assertEqual(statuses["ambiguous_city_key"], 1)
            self.assertEqual(statuses["unmatched_missing_country"], 1)
            self.assertEqual(statuses["unmatched_missing_municipality"], 1)

    def test_nonempty_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "out"
            out.mkdir()
            (out / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_catalog_city_workflow(CATALOG, CITIES, out)


class DataToolCliTests(unittest.TestCase):
    def test_public_cli_writes_and_reports_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "cli-output"
            command = [
                sys.executable,
                "-B",
                str(ROOT / "tools" / "mcl_data.py"),
                "catalog-city-match",
                "--catalog",
                str(CATALOG),
                "--cities",
                str(CITIES),
                "--output",
                str(out),
            ]
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            stdout_report = json.loads(completed.stdout)
            file_report = json.loads(
                (out / "quality_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(stdout_report, file_report)
            self.assertEqual(file_report["quality"]["matched_feed_records"], 4)
            for required in (
                "normalized_catalog.csv",
                "standardized_cities.csv",
                "feed_city_matches.csv",
                "city_feed_summary.csv",
                "quality_report.json",
            ):
                self.assertTrue((out / required).is_file(), required)


if __name__ == "__main__":
    unittest.main()
