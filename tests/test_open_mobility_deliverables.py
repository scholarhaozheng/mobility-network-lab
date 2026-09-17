from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "open-mobility"

import sys

sys.path.insert(0, str(ROOT / "src"))

from mobilitylab.data.open_mobility import (  # noqa: E402
    AmbiguousCityError,
    query_city_evidence,
)
from mobilitylab.omdv.gtfs import parse_gtfs_zip  # noqa: E402


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class OpenMobilityDeliverableTests(unittest.TestCase):
    def test_public_tables_match_accepted_accounting(self) -> None:
        cities = read_rows("city_evidence.csv")
        content_city = read_rows("content_city.csv")
        relations = read_rows("source_content_city.csv")
        self.assertEqual(len(cities), 11_422)
        self.assertEqual(len({row["city_id"] for row in cities}), 11_422)
        self.assertEqual(len(content_city), 12_442)
        self.assertEqual(
            sum(
                row["source_link_status"]
                == "CONTENT_CITY_ONLY_NO_MAPPED_SOURCE_RECORD"
                for row in content_city
            ),
            2,
        )
        self.assertEqual(
            sum(
                row["relationship_status"] == "SOURCE_CONTENT_CITY_LINK"
                for row in relations
            ),
            14_328,
        )
        self.assertEqual(
            sum(
                row["relationship_status"]
                == "SOURCE_CONTENT_ONLY_NO_CITY_LINK"
                for row in relations
            ),
            2_377,
        )

    def test_named_queries_and_duplicate_state(self) -> None:
        city_path = DATA / "city_evidence.csv"
        relation_path = DATA / "source_content_city.csv"
        hong_kong = query_city_evidence(
            city_path,
            relation_path,
            city_name="Hong Kong",
            country="CHN",
            include_relations=True,
        )
        self.assertEqual(hong_kong["status"], "matched_unique")
        self.assertEqual(hong_kong["relationship_count"], 2)
        cairo = query_city_evidence(
            city_path, relation_path, city_name="Cairo", country="EGY"
        )
        self.assertEqual(
            cairo["matches"][0]["gtfs_all_retained_completeness_status"],
            "no_stop_content",
        )
        with self.assertRaises(AmbiguousCityError):
            query_city_evidence(
                city_path, relation_path, city_name="Lawrence", country="USA"
            )
        missing = query_city_evidence(
            city_path,
            relation_path,
            city_name="Definitely Missing",
            country="USA",
        )
        self.assertEqual(missing["status"], "not_found")

    def test_content_parser_runs_without_extracting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            zip_path = Path(temporary) / "fixture.zip"
            members = {
                "agency.txt": "agency_id,agency_name,agency_url,agency_timezone\nA,Example,https://example.com,UTC\n",
                "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\nS,Stop,1.0,2.0\n",
                "routes.txt": "route_id,agency_id,route_type\nR,A,3\n",
                "trips.txt": "route_id,service_id,trip_id\nR,WK,T\n",
                "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nT,00:00:00,00:00:00,S,1\n",
                "calendar.txt": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\nWK,1,1,1,1,1,0,0,20260101,20261231\n",
            }
            with zipfile.ZipFile(zip_path, "w") as archive:
                for name, value in members.items():
                    archive.writestr(name, value)
            report = parse_gtfs_zip(zip_path)
            self.assertEqual(report["metrics"]["parse_status"], "parsed")
            self.assertEqual(report["metrics"]["stop_time_row_count"], 1)
            self.assertEqual(report["metrics"]["invalid_stop_references"], 0)
            self.assertFalse((Path(temporary) / "stops.txt").exists())

    def test_product_catalog_hash_checks_are_recorded(self) -> None:
        catalog = json.loads(
            (ROOT / "catalog" / "open-data-products.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(
            all(item["hash_check"] == "match" for item in catalog["source_files"])
        )
        self.assertEqual(catalog["checks"]["city_rows"], 11_422)


if __name__ == "__main__":
    unittest.main()
