#!/usr/bin/env python3
"""Acquire a minimal, non-personal MassGIS parcel/assessment slice for Central Boston."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


import os
TASK_ROOT = Path(os.environ.get("MCL_BOSTON_SOURCE_ROOT", Path(__file__).resolve().parents[1])).resolve()
RUN_ID = "boston_activity_prior_r1_20260922"
SOURCE_ID = "massgis_property_tax_parcels_feature_service_20260917"
SERVICE = "https://services1.arcgis.com/hGdibHYSPO59RG1h/ArcGIS/rest/services/Massachusetts_Property_Tax_Parcels/FeatureServer/0"
BBOX = [-71.105, 42.335, -71.045, 42.370]
FIELDS = [
    "OBJECTID", "GlobalID", "LOC_ID", "MAP_PAR_ID", "POLY_TYPE", "TOWN_ID",
    "PROP_ID", "FY", "USE_CODE", "CITY", "YEAR_BUILT", "BLD_AREA", "UNITS",
    "RES_AREA", "STORIES", "USE_DESC", "Shape__Area",
]
RAW_ROOT = TASK_ROOT / "raw" / "activity" / RUN_ID / "massgis_property_tax_parcels"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def request_json(url: str, attempts: int = 3, timeout: int = 45) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events = []
    for attempt in range(1, attempts + 1):
        started = time.time()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "MCL-Boston-Research/1.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read()
                status = getattr(response, "status", 200)
            value = json.loads(payload)
            if "error" in value:
                raise RuntimeError(json.dumps(value["error"], ensure_ascii=False))
            events.append({
                "attempt": attempt,
                "status": "success",
                "http_status": status,
                "bytes": len(payload),
                "seconds": round(time.time() - started, 3),
            })
            return value, events
        except Exception as exc:
            events.append({
                "attempt": attempt,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "seconds": round(time.time() - started, 3),
            })
            if attempt == attempts:
                raise
            time.sleep(min(2 ** attempt, 5))
    raise AssertionError("unreachable")


def query_url(**parameters: Any) -> str:
    return SERVICE + "/query?" + urllib.parse.urlencode(parameters)


def main() -> int:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    metadata_url = SERVICE + "?f=pjson"
    metadata, metadata_events = request_json(metadata_url)
    (RAW_ROOT / "layer_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    common = {
        "where": "1=1",
        "geometry": ",".join(str(value) for value in BBOX),
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "f": "json",
    }
    count_response, count_events = request_json(query_url(**common, returnCountOnly="true"))
    expected_count = int(count_response["count"])
    stats = json.dumps([{
        "statisticType": "count",
        "onStatisticField": "OBJECTID",
        "outStatisticFieldName": "record_count",
    }], separators=(",", ":"))
    municipality_response, municipality_events = request_json(query_url(
        **common,
        outStatistics=stats,
        groupByFieldsForStatistics="CITY,FY",
        orderByFields="CITY,FY",
        returnGeometry="false",
    ))
    municipalities = [feature["attributes"] for feature in municipality_response["features"]]
    with (RAW_ROOT / "municipality_fiscal_year_coverage.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["CITY", "FY", "record_count"])
        writer.writeheader()
        writer.writerows(municipalities)

    selected_field_metadata = []
    notes = {
        "GlobalID": "Hosted-layer record identifier; used as source_feature_id.",
        "LOC_ID": "MassGIS location identifier used to recognize stacked assessor records sharing one parcel geometry.",
        "BLD_AREA": "Assessor-reported building area. Official documentation warns that measurement basis varies by CAMA system; not treated as footprint or uniform floor area.",
        "UNITS": "Assessor-reported units; may include dwelling or non-residential units. Residential-only summaries also require the use classification.",
        "RES_AREA": "Assessor-reported residential/living area where supplied; local completeness and semantics vary.",
        "Shape__Area": "Service-side geometry area in the service CRS; metric overlay is recomputed locally in EPSG:32619.",
        "USE_DESC": "Official use description supplied with the hosted layer; grouped by an explicit project rule without overwriting the source value.",
    }
    metadata_lookup = {item["name"]: item for item in metadata["fields"]}
    for name in FIELDS:
        item = metadata_lookup[name]
        selected_field_metadata.append({
            "field": name,
            "alias": item.get("alias", ""),
            "esri_type": item.get("type", ""),
            "nullable": item.get("nullable", ""),
            "source_or_derived": "official_service_field",
            "project_note": notes.get(name, "Retained modelling field from the official service."),
        })
    with (RAW_ROOT / "selected_field_dictionary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected_field_metadata[0]))
        writer.writeheader()
        writer.writerows(selected_field_metadata)

    page_size = min(int(metadata.get("maxRecordCount", 2000)), 2000)
    output_path = RAW_ROOT / "massgis_parcel_assessment_slice.geojsonl.gz"
    seen_object_ids: set[int] = set()
    page_events = []
    record_count = 0
    with output_path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
            offset = 0
            while offset < expected_count:
                url = query_url(
                    **{**common, "f": "geojson"},
                    outFields=",".join(FIELDS),
                    returnGeometry="true",
                    outSR=4326,
                    orderByFields="OBJECTID",
                    resultOffset=offset,
                    resultRecordCount=page_size,
                )
                page, events = request_json(url)
                features = page.get("features", [])
                page_events.append({
                    "offset": offset,
                    "returned": len(features),
                    "exceeded_transfer_limit": bool(page.get("properties", {}).get("exceededTransferLimit", False)),
                    "attempts": events,
                })
                if not features:
                    break
                for feature in features:
                    object_id = int(feature["properties"]["OBJECTID"])
                    if object_id in seen_object_ids:
                        raise RuntimeError(f"Duplicate OBJECTID across pages: {object_id}")
                    seen_object_ids.add(object_id)
                    gzip_handle.write((json.dumps(feature, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
                    record_count += 1
                offset += len(features)
                if len(features) < page_size:
                    break
    if record_count != expected_count:
        raise RuntimeError(f"Downloaded {record_count} records; service count was {expected_count}")

    manifest = {
        "run_id": RUN_ID,
        "source_id": SOURCE_ID,
        "provider": "Commonwealth of Massachusetts Bureau of Geographic Information (MassGIS)",
        "official_landing_page": "https://www.mass.gov/info-details/massgis-data-property-tax-parcels",
        "official_service_url": SERVICE,
        "service_item_id": metadata.get("serviceItemId"),
        "downloaded_at_utc": utc_now(),
        "source_data_last_edit_epoch_ms": metadata.get("editingInfo", {}).get("dataLastEditDate"),
        "source_schema_last_edit_epoch_ms": metadata.get("editingInfo", {}).get("schemaLastEditDate"),
        "service_crs": metadata.get("spatialReference"),
        "requested_output_crs": "EPSG:4326",
        "study_bbox_wgs84": BBOX,
        "selection_rule": "Official parcel-assessment features whose geometry intersects the unchanged Central Boston core bbox; exact overlay to existing clipped H3 zones is a later derived step.",
        "selected_fields": FIELDS,
        "explicitly_not_requested": [
            "OWNER1", "OWN_ADDR", "OWN_CITY", "OWN_STATE", "OWN_ZIP", "OWN_CO",
            "SITE_ADDR", "FULL_STR", "LOCATION", "LS_BOOK", "LS_PAGE", "REG_ID",
        ],
        "privacy_note": "Owner, mailing, site-address and registry fields were not requested or stored.",
        "record_count": record_count,
        "municipality_fiscal_year_coverage": municipalities,
        "raw_file": output_path.relative_to(TASK_ROOT).as_posix(),
        "raw_file_bytes": output_path.stat().st_size,
        "raw_file_sha256": sha256_file(output_path),
        "metadata_sha256": sha256_file(RAW_ROOT / "layer_metadata.json"),
        "terms_note": "Official public MassGIS feature service; downstream package retains provider attribution and does not relicense source records.",
        "object_semantics": "Hosted layer contains stacked polygons where multiple assessor records link to one parcel. Assessment records and unique parcel geometries must be aggregated separately.",
        "request_evidence": {
            "metadata": metadata_events,
            "count": count_events,
            "municipality_statistics": municipality_events,
            "pages": page_events,
        },
    }
    (RAW_ROOT / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "run_id": RUN_ID,
        "records": record_count,
        "municipality_fiscal_year_coverage": municipalities,
        "raw_file_bytes": output_path.stat().st_size,
        "raw_file_sha256": manifest["raw_file_sha256"],
        "pages": len(page_events),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
