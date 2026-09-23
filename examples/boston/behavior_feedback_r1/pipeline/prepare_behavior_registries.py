"""Create the model config, source/parameter registers, and CTPS request draft."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


RUN_ID = "behavior_feedback_r1"


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--run-dir", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    run = (args.run_dir or root / "runs" / RUN_ID).resolve()
    inputs, derived, docs = run / "inputs", run / "derived", run / "docs"
    for p in (inputs, derived, docs):
        p.mkdir(parents=True, exist_ok=True)

    repo_root = root.parents[1]
    report_pdf = repo_root / "tmp" / "pdfs" / "TDM23.2.0_Structures_and_Performance.pdf"
    source_defs = [
        ("gmns_plus_boston_116447ab", "GMNS Plus 21_Boston", "Han Zheng / GMNS Plus", "https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset", root / "raw/gmns_plus_21_boston/link.csv", "116447ab641cca1ed34797d019c8e704063393c3", "2025", "Apache-2.0", "official_observation", "directed road network and inherited source demand metadata", "redistributable_with_attribution"),
        ("acs2024_5yr_bg_census_reporter_mirror", "ACS 2024 5-year block-group estimates and TIGER 2024 geometry mirror", "U.S. Census Bureau data via Census Reporter", "https://api.censusreporter.org/", root / "raw/demographics/acs2024_5yr_bg/suffolk_025.json", "acs2024_5yr / TIGER 2024", "2020-2024", "public_domain_US_government; mirror attribution", "official_observation", "population and households area-weighted to H3", "redistributable_check_mirror_terms"),
        ("ctps_tdm23_2_0_report", "TDM23.2.0 Structures and Performance", "Central Transportation Planning Staff", "https://ctpsstaff.github.io/tdm23_users_guide/2.0/", report_pdf, "TDM23.2.0 report posted 2025", "model base years documented in report", "official_public_document", "regional_model_estimate", "trip rates, time factors, coefficients, occupancies, model structure", "link_or_redistribute_per_document_terms"),
        ("ctps_tdm23_2_0_x_mc", "TDM23.2.0 mode-choice report HTML", "Central Transportation Planning Staff", "https://ctpsstaff.github.io/tdm23_users_guide/2.0/reports/x_mc.html", inputs / "ctps_tdm23_2_0_mode_choice_report.html", "TDM23.2.0", "model output", "official_public_document", "regional_model_estimate", "regional base-model mode shares", "link_or_redistribute_per_document_terms"),
        ("massgis_property_assessment_20260917", "MassGIS standardized assessors parcels-derived activity prior", "MassGIS / municipal assessors", "https://www.mass.gov/info-details/massgis-data-standardized-assessors-parcels", root / "database/demand/scenarios/boston_activity_prior_r1_20260922/productions_attractions.csv", "local snapshot documented by prior run", "Boston/Cambridge assessment years differ", "MassGIS terms and municipal source terms", "official_observation", "nonresidential building-area attraction proxy", "derived_only_review_source_terms"),
        ("mbta_gtfs_mdb437_fall2026", "MBTA Fall 2026 GTFS", "MBTA via Mobility Database", "https://cdn.mbta.com/MBTA_GTFS.zip", root / "raw/gtfs/mdb-437_20260918.zip", "Fall 2026 version D", "2026", "MBTA open data terms; GTFS source attribution", "official_observation", "service-day schedule, stops, trips, fares", "archive_redistribution_unclear_keep_out_of_source_upload"),
        ("mbta_v3_vehicle_positions_20260921", "MBTA V3 bus vehicle positions short live window", "MBTA", "https://api-v3.mbta.com/vehicles?filter%5Broute_type%5D=3", root / "database/observations/gps_segments.csv", "boston_quality_r1_20260922", "2026-09-21", "MBTA open data terms", "official_observation", "pre-qualified exploratory stop-pair elapsed times", "publish_only_deidentified_derived_records"),
        ("openstreetmap_overpass_20260601", "Central Boston highway ways", "OpenStreetMap contributors / Overpass API", "https://overpass-api.de/", root / "raw/osm/behavior_feedback_r1/central_boston_highways.osm", "osm_base 2026-06-01T08:52:28Z", "2026", "ODbL 1.0", "official_observation", "walking and cycling graph", "ODbL_attribution_and_share_alike_apply"),
        ("bbbike_cambridgema_20260920", "BBBike CambridgeMa OSM extract", "BBBike / OpenStreetMap contributors", "https://download.bbbike.org/osm/bbbike/CambridgeMa/", root / "raw/osm/behavior_feedback_r1/CambridgeMa.osm.pbf", "2026-09-20", "2026", "ODbL 1.0", "official_observation", "validated fallback extract; not used after Overpass XML recovered", "ODbL_attribution_and_share_alike_apply"),
        ("h3_4_5_0", "H3 spatial index", "Uber", "https://h3geo.org/", root / "database/zones/zone.csv", "4.5.0", "n/a", "Apache-2.0", "engineering_assumption", "H3 r9/r7 zone system", "derived_geometry_with_attribution"),
        ("mcl_static_fw", "Mobility Computation Lab static Frank-Wolfe solver", "project code", "https://github.com/scholarhaozheng/mobility-network-lab", repo_root / "github_upload/algorithms/static_fw/tap_frank_wolfe.py", "local current", "2026", "MIT for original code", "engineering_assumption", "two controlled panel-only assignments", "source_publishable"),
    ]
    sources = []
    for sid, title, provider, url, path, version, sy, license_, status, use, redist in source_defs:
        sources.append({
            "source_id": sid, "title": title, "provider": provider, "source_url": url,
            "local_path": str(path), "version": version, "source_year": sy, "application_year": "2026",
            "acquired_or_verified_date": "2026-09-22", "license_or_terms": license_,
            "source_status": status, "used_for": use, "sha256": sha256(path),
            "redistribution_status": redist, "run_id": RUN_ID,
        })
    pd.DataFrame(sources).to_csv(inputs / "SOURCE_REGISTER.csv", index=False)

    columns = ["parameter_id", "model_id", "source_id", "version", "page_table_row", "symbol", "value", "unit",
               "sign_convention", "price_year", "population_purpose", "source_year", "application_year", "applicability",
               "transformation", "status"]
    params: list[dict] = []

    def add(pid, model, source, ref, symbol, value, unit, sign, price, pop, applicable, transform, status):
        params.append(dict(zip(columns, [pid, model, source, "TDM23.2.0", ref, symbol, value, unit, sign, price,
                                         pop, "report_2025_model_base_period", "2026", applicable, transform, status])))

    for purpose, value in {"HBW": 1.90, "HBSC": .59, "HBSR": 2.19, "HBPB": 2.38, "NHBW": .51, "NHBNW": 2.69}.items():
        add(f"tdm23_effective_hh_rate_{purpose}", "tdm23_trip_generation_transfer", "ctps_tdm23_2_0_report", "p148 Table 74", f"r_{purpose}", value, "person_trips/household/average_weekday", "positive production", None, purpose, "Central Boston ACS households; all household segments pooled", "multiply area-weighted ACS households", "transferred_parameter_not_local_calibration")
    for purpose, value in {"HBW": .692, "HBSC": .746, "HBSR": .509, "HBPB": .486, "NHBW": .446, "NHBNW": .398}.items():
        add(f"tdm23_peak_share_{purpose}", "tdm23_time_of_day_transfer", "ctps_tdm23_2_0_report", "p84 Table 37", f"peak_share_{purpose}", value, "fraction_combined_AM_PM", "positive share", None, purpose, "combined peak only; not relabelled 07:00-09:00", "stored without AM split", "transferred_parameter")
    for purpose, vals in {"HBW": (.268,.222), "HBPB": (.395,.375), "HBSR": (.218,.187), "HBSC": (.052,.886), "NHBW": (.485,.484), "NHBNW": (.412,.412)}.items():
        for direction, value in zip(("MD_PA", "MD_AP"), vals):
            add(f"tdm23_nonpeak_{direction.lower()}_{purpose}", "tdm23_pa_od_transfer", "ctps_tdm23_2_0_report", "p97 Table 47 current/lower block", f"{direction}_{purpose}", value, "fraction_of_nonpeak", "positive share", None, purpose, "midday PA/AP conversion", "multiply nonpeak share; reverse matrix for AP", "transferred_parameter")
    for symbol, value, unit in (("beta_IVTT_HBW", -.0201, "utility/minute"), ("beta_OVTT_HBW", -.0431, "utility/minute"), ("beta_COST_HBW", -.0613, "utility/2010_USD")):
        add(f"tdm23_hbw_{symbol.lower()}", "tdm23_hbw_nested_choice", "ctps_tdm23_2_0_report", "pp91-94 Tables 44-45", symbol, value, unit, "negative disutility", 2010 if "COST" in symbol else None, "HBW", "regional HBW mode choice", "only S1-to-S2 delta used", "original_model_estimate_transferred_not_local_reestimated")
    for mode, value in {"DA": 0, "S2": -.388, "S3": -.892, "TA": -1.452, "TW": -2.218, "BK": -3.649, "WK": -2.720, "RS": -2.500}.items():
        add(f"tdm23_hbw_asc_{mode.lower()}", "tdm23_hbw_nested_choice", "ctps_tdm23_2_0_report", "pp91-94 Tables 44-45", f"ASC_{mode}", value, "utility", "relative to DA reference", None, "HBW", "original full utility only; not used by base-share pivot", "stored without recomputing absolute utility", "original_model_estimate_not_executed_missing_inputs")
    for symbol in ("mu_Auto", "mu_NonMotor", "mu_Transit"):
        add(f"tdm23_hbw_missing_{symbol.lower()}", "tdm23_hbw_nested_choice", "ctps_tdm23_2_0_report", "Figures 16-18 pp89-90; numeric value not published", symbol, None, "dimensionless", "0<mu<=1 expected under implementation convention", None, "HBW", "required for full nested-logit reproduction", "no substitution; mu_Transit sensitivity grid only", "missing_external")
    for mode, value in {"DA":1.0, "S2":2.0, "S3":3.627, "RS":1.21}.items():
        add(f"tdm23_hbw_occupancy_{mode.lower()}", "person_to_vehicle", "ctps_tdm23_2_0_report", "p98 Table 49", f"occupancy_{mode}", value, "persons/vehicle", "divide persons by occupancy", None, "HBW", "road vehicle conversion", "applied to panel diagnostic", "transferred_parameter")
    add("gravity_beta_0_08", "regional_od_h3_gravity", "massgis_property_assessment_20260917", "inherited prior scenario", "beta", .08, "1/minute", "negative in exp(-beta*t)", None, "all transferred purposes", "distribution proxy", "retained for scenario isolation", "engineering_assumption")
    add("walk_speed_3mph", "osm_shortest_path", "ctps_tdm23_2_0_report", "p91 Table 41", "v_walk", 3.0, "mile/hour", "positive", None, "all", "walk routing", "distance/speed", "transferred_parameter")
    add("bike_speed_12mph", "osm_shortest_path", "ctps_tdm23_2_0_report", "p91 Table 41", "v_bike", 12.0, "mile/hour", "positive", None, "all", "bike routing", "distance/speed", "transferred_parameter")
    add("gtfs_local_bus_flat_fare", "gtfs_fare_approximation", "mbta_gtfs_mdb437_fall2026", "fare_products.txt prod_local_bus_*", "fare_local_bus", 1.70, "2026_USD/one_way", "positive cost", 2026, "transit users", "local bus only", "transfer rules not fully implemented", "official_observation_approximate_application")
    add("gtfs_rapid_transit_flat_fare", "gtfs_fare_approximation", "mbta_gtfs_mdb437_fall2026", "fare_products.txt prod_rapid_transit_*", "fare_subway", 2.40, "2026_USD/one_way", "positive cost", 2026, "transit users", "rapid transit only", "transfer rules not fully implemented", "official_observation_approximate_application")
    pd.DataFrame(params, columns=columns).to_csv(inputs / "PARAMETER_REGISTER.csv", index=False)

    config = {
        "schema_version": "mcl_behavior_feedback_1.0", "run_id": RUN_ID,
        "base_city_config": "config/city_config.yaml",
        "region": {"zone_system": "H3 r9", "zone_count": 177, "core_bbox_wgs84": [-71.105,42.335,-71.045,42.370]},
        "demand": {"statistics": "ACS 2024 5-year block groups", "generation": "TDM23.2.0 effective mean daily productions per household Table 74", "attraction": "MassGIS nonresidential building area proxy", "distribution": "doubly constrained gravity; beta=.08/min inherited assumption", "external_travel": "unknown_not_zero; spatial outside-share ledger only"},
        "pilot": {"purpose": "HBW", "service_date": "2026-09-21", "period": "midday exploratory", "departures": ["12:30:00","12:40:00","12:50:00"], "od_count": 36, "departure_weight": "equal thirds engineering transfer"},
        "skims": {"drive": "directed GMNS free flow; parking unknown", "walk_bike": "OSM allowed-way shortest paths", "transit": "time-dependent GTFS connection scan with actual calendar service", "fare": "GTFS v2 local flat-fare approximation; full transfer rules not implemented"},
        "choice": {"model": "TDM23 HBW regional base-share nested pivot sensitivity", "tree_preserved": True, "official_nest_scales_available": False, "mu_transit_grid": [0.25,0.5,0.75,1.0], "fw_boundary_variant": 1.0},
        "feedback": {"S1": "planned GTFS", "S2": "exploratory exact route+direction+stop-pair GPS overlay", "overlay_default": False, "observation_period": "2026-09-21 midday", "independent_validation": False},
        "assignment": {"solver": "solve_fw_refined", "runs": 2, "scope": "panel only, no background", "numeric_threads": 2},
    }
    (inputs / "behavior_feedback_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    model_spec = {
        "model_id": "ctps_tdm23_2_0_hbw_nested_base_share_pivot_sensitivity",
        "nests": {"Auto":["DA","S2","S3"], "NonMotor":["WK","BK"], "Transit":["TW","TA"], "SchoolBus":["SB"], "RideService":["RS"]},
        "source_base_shares": "derived/ctps_tdm23_base_mode_share.csv",
        "utility_change": "dV_TW = -0.0201*dIVTT_min -0.0431*dOVTT_min -0.0613*dCost_2010USD",
        "pivot_equation": "p_i|m' proportional to p_i|m*exp(dV_i/mu_m); P_m' proportional to P_m*exp(mu_m*log(sum_i p_i|m*exp(dV_i/mu_m)))",
        "missing": ["numeric nest scales", "full zonal socioeconomic inputs", "parking and terminal costs", "TA skim", "RS skim"],
        "status": "technical_sensitivity_not_full_TDM23_reproduction",
    }
    (inputs / "choice_model_spec.json").write_text(json.dumps(model_spec, indent=2), encoding="utf-8")

    # Correspondence is maintained separately from public registry generation.
    print(json.dumps({"sources": len(sources), "parameters": len(params), "config": str(inputs / "behavior_feedback_config.json"), "email_sent": False}, indent=2))


if __name__ == "__main__":
    main()
