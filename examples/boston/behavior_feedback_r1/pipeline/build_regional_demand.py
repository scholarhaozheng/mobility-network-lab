"""Build an ACS-to-H3 demand transfer for the Central Boston pilot.

This script deliberately keeps three distinct objects separate:

* observed ACS block-group population/households;
* CTPS TDM23.2.0 regional effective production rates; and
* the local H3/road-network distribution proxy.

The resulting OD table is therefore a documented regional-parameter transfer,
not an observed OD matrix and not a full TDM23 reproduction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt


RUN_ID = "behavior_feedback_r1"
ACS_SOURCE_ID = "census_reporter_acs2024_5yr_bg_mirror"
TDM_SOURCE_ID = "ctps_tdm23_2_0_structures_performance_202503"
ACTIVITY_SOURCE_ID = "massgis_property_tax_parcels_feature_service_20260917"

# Table 74, TDM23.2.0 Structures and Performance, p. 148.
# These are Boston Region model effective mean daily productions per household.
EFFECTIVE_HH_RATES = {
    "HBW": 1.90,
    "HBSC": 0.59,
    "HBSR": 2.19,
    "HBPB": 2.38,
    "NHBW": 0.51,
    "NHBNW": 2.69,
}

# Table 37, p. 84. "Peak" combines AM and PM; it is not relabelled as AM.
PEAK_SHARES = {
    "HBW": 0.692,
    "HBSC": 0.746,
    "HBSR": 0.509,
    "HBPB": 0.486,
    "NHBW": 0.446,
    "NHBNW": 0.398,
}

# Table 47, p. 97, lower/current TDM23.2.0 block. Values partition non-peak.
NONPEAK_PA_TO_OD = {
    "HBW": {"MD_PA": 0.268, "MD_AP": 0.222, "NT_PA": 0.225, "NT_AP": 0.285},
    "HBPB": {"MD_PA": 0.395, "MD_AP": 0.375, "NT_PA": 0.063, "NT_AP": 0.167},
    "HBSR": {"MD_PA": 0.218, "MD_AP": 0.187, "NT_PA": 0.142, "NT_AP": 0.453},
    "HBSC": {"MD_PA": 0.052, "MD_AP": 0.886, "NT_PA": 0.008, "NT_AP": 0.054},
    "NHBW": {"MD_PA": 0.485, "MD_AP": 0.484, "NT_PA": 0.015, "NT_AP": 0.015},
    "NHBNW": {"MD_PA": 0.412, "MD_AP": 0.412, "NT_PA": 0.088, "NT_AP": 0.088},
}

# Official TDM23.2.0 base-model shares embedded in x_mc.html. Rows sum to 100
# subject to display rounding. They are regional outputs, not local observations.
TDM23_BASE_MODE_SHARE_PCT = {
    "HBW": {"DA": 72.650, "S2": 10.296, "S3": 3.579, "WK": 3.809, "BK": 1.789,
            "TW": 4.099, "TA": 2.789, "SB": 0.000, "RS": 0.989},
    "HBSC": {"DA": 1.916, "S2": 19.204, "S3": 28.709, "WK": 12.045, "BK": 1.104,
             "TW": 1.276, "TA": 0.010, "SB": 35.726, "RS": 0.010},
    "HBSR": {"DA": 31.487, "S2": 25.887, "S3": 26.866, "WK": 11.832, "BK": 2.069,
             "TW": 1.037, "TA": 0.144, "SB": 0.000, "RS": 0.678},
    "HBPB": {"DA": 47.393, "S2": 27.232, "S3": 12.294, "WK": 9.822, "BK": 1.127,
             "TW": 1.848, "TA": 0.056, "SB": 0.000, "RS": 0.228},
    "NHBW": {"DA": 73.723, "S2": 9.486, "S3": 3.584, "WK": 9.815, "BK": 0.711,
             "TW": 0.926, "TA": 0.000, "SB": 0.000, "RS": 1.756},
    "NHBNW": {"DA": 46.645, "S2": 24.966, "S3": 12.976, "WK": 12.905, "BK": 0.900,
              "TW": 1.032, "TA": 0.000, "SB": 0.000, "RS": 0.576},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_acs(raw_dir: Path) -> gpd.GeoDataFrame:
    rows: list[dict] = []
    geoms: list[gpd.GeoDataFrame] = []
    for county in ("suffolk_025", "middlesex_017", "norfolk_021"):
        data_path = raw_dir / f"{county}.json"
        geo_path = raw_dir / f"{county}_tiger2024.geojson"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        if data["release"]["id"] != "acs2024_5yr":
            raise RuntimeError(f"Unexpected ACS release in {data_path}: {data['release']}")
        for geoid, item in data["data"].items():
            rows.append(
                {
                    "source_geoid": geoid,
                    "source_name": data["geography"][geoid]["name"],
                    "county_file": county,
                    "population_estimate": item["B01003"]["estimate"]["B01003001"],
                    "population_moe": item["B01003"]["error"]["B01003001"],
                    "households_estimate": item["B11001"]["estimate"]["B11001001"],
                    "households_moe": item["B11001"]["error"]["B11001001"],
                }
            )
        g = gpd.read_file(geo_path)[["geoid", "geometry"]].rename(columns={"geoid": "source_geoid"})
        geoms.append(g)
    attrs = pd.DataFrame(rows)
    geo = pd.concat(geoms, ignore_index=True)
    out = gpd.GeoDataFrame(attrs.merge(geo, on="source_geoid", validate="one_to_one"), geometry="geometry", crs="EPSG:4326")
    return out


def ipf_matrix(prod: np.ndarray, attr: np.ndarray, kernel: np.ndarray, tol: float = 1e-9, max_iter: int = 1000) -> tuple[np.ndarray, int, float]:
    if prod.sum() <= 0 or attr.sum() <= 0:
        return np.zeros_like(kernel), 0, 0.0
    attr = attr * (prod.sum() / attr.sum())
    x = kernel.copy().astype(float)
    x[~np.isfinite(x)] = 0.0
    x *= np.outer(np.where(prod > 0, prod, 0.0), np.where(attr > 0, attr, 0.0))
    x += np.where((kernel > 0) & (np.outer(prod, attr) > 0), 1e-300, 0.0)
    err = math.inf
    for it in range(1, max_iter + 1):
        rs = x.sum(axis=1)
        rfac = np.divide(prod, rs, out=np.zeros_like(prod), where=rs > 0)
        x *= rfac[:, None]
        cs = x.sum(axis=0)
        cfac = np.divide(attr, cs, out=np.zeros_like(attr), where=cs > 0)
        x *= cfac[None, :]
        err = max(float(np.max(np.abs(x.sum(axis=1) - prod))), float(np.max(np.abs(x.sum(axis=0) - attr))))
        if err <= tol * max(1.0, float(prod.sum())):
            return x, it, err
    return x, max_iter, err


def haversine_minutes(lon: np.ndarray, lat: np.ndarray, detour_factor: float = 1.25, speed_mph: float = 25.0) -> np.ndarray:
    """Transparent geometric fallback for zones absent from the road impedance table."""
    radius_miles = 3958.7613
    lon_r = np.radians(lon)
    lat_r = np.radians(lat)
    dlon = lon_r[None, :] - lon_r[:, None]
    dlat = lat_r[None, :] - lat_r[:, None]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat_r[:, None]) * np.cos(lat_r[None, :]) * np.sin(dlon / 2) ** 2
    miles = 2 * radius_miles * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    minutes = miles * detour_factor / speed_mph * 60.0
    np.fill_diagonal(minutes, 0.5)
    return minutes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--run-dir", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    run = (args.run_dir or root / "runs" / RUN_ID).resolve()
    derived = run / "derived"
    reports = run / "reports"
    derived.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    raw_acs = root / "raw" / "demographics" / "acs2024_5yr_bg"
    acs = load_acs(raw_acs)

    zones_df = pd.read_csv(root / "database" / "zones" / "zone.csv", dtype={"zone_id": str, "full_cell_id": str})
    zones_df = zones_df[zones_df["zone_level"].eq("fine")].copy()
    zones = gpd.GeoDataFrame(
        zones_df[["zone_id", "full_cell_id", "centroid_lon", "centroid_lat", "clipped_area_km2"]].copy(),
        geometry=zones_df["clipped_geometry_wkt"].map(wkt.loads),
        crs="EPSG:4326",
    )
    core = zones.geometry.union_all()
    acs = acs[acs.intersects(core)].copy()

    acs_m = acs.to_crs("EPSG:32619")
    zones_m = zones.to_crs("EPSG:32619")
    acs_m["source_area_m2"] = acs_m.geometry.area
    core_m = gpd.GeoSeries([core], crs="EPSG:4326").to_crs("EPSG:32619").iloc[0]
    acs_m["core_overlap_area_m2"] = acs_m.geometry.intersection(core_m).area
    acs_m["core_area_share"] = acs_m["core_overlap_area_m2"] / acs_m["source_area_m2"]
    acs_m["population_estimate_in_core_area_weighted"] = acs_m["population_estimate"] * acs_m["core_area_share"]
    acs_m["households_estimate_in_core_area_weighted"] = acs_m["households_estimate"] * acs_m["core_area_share"]
    acs_stats = pd.DataFrame(acs_m.drop(columns="geometry"))
    acs_stats["acs_release"] = "ACS 2024 5-year (2020-2024)"
    acs_stats["allocation_method"] = "uniform_within_block_group_area_intersection"
    acs_stats["source_id"] = ACS_SOURCE_ID
    acs_stats.to_csv(derived / "acs_block_group_stats.csv", index=False)

    cross = gpd.overlay(
        acs_m[["source_geoid", "source_area_m2", "population_estimate", "households_estimate", "geometry"]],
        zones_m[["zone_id", "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    cross["overlap_area_m2"] = cross.geometry.area
    cross = cross[cross["overlap_area_m2"] > 0].copy()
    cross["source_area_share"] = cross["overlap_area_m2"] / cross["source_area_m2"]
    cross["allocated_population"] = cross["population_estimate"] * cross["source_area_share"]
    cross["allocated_households"] = cross["households_estimate"] * cross["source_area_share"]
    cross["allocation_method"] = "uniform_within_block_group_area_intersection"
    cross["source_id"] = ACS_SOURCE_ID
    cross_out = pd.DataFrame(cross.drop(columns="geometry"))
    cross_out.to_csv(derived / "acs_block_group_h3_crosswalk.csv", index=False)

    zone_demo = cross.groupby("zone_id", as_index=False).agg(
        population_estimate_area_weighted=("allocated_population", "sum"),
        households_estimate_area_weighted=("allocated_households", "sum"),
        contributing_block_groups=("source_geoid", "nunique"),
        overlap_area_m2=("overlap_area_m2", "sum"),
    )
    zone_demo = zones[["zone_id", "centroid_lon", "centroid_lat", "clipped_area_km2"]].merge(zone_demo, on="zone_id", how="left")
    for col in ("population_estimate_area_weighted", "households_estimate_area_weighted", "contributing_block_groups", "overlap_area_m2"):
        zone_demo[col] = zone_demo[col].fillna(0)
    zone_demo["geography_status"] = np.where(zone_demo["contributing_block_groups"] > 0, "covered", "no_intersecting_block_group")
    zone_demo["source_id"] = ACS_SOURCE_ID
    zone_demo["measurement_status"] = "ACS_ESTIMATE_AREA_WEIGHTED_TO_H3_NOT_POINT_OBSERVATION"
    zone_demo.to_csv(derived / "population_or_household_by_zone.csv", index=False)

    outside = acs_m[["source_geoid", "population_estimate", "households_estimate", "core_area_share"]].copy()
    outside["population_outside_core_area_weighted"] = outside["population_estimate"] * (1 - outside["core_area_share"])
    outside["households_outside_core_area_weighted"] = outside["households_estimate"] * (1 - outside["core_area_share"])
    outside["ledger_category"] = "source_block_group_share_outside_core"
    outside["flow_status"] = "SPATIAL_LEDGER_NOT_TRAVEL_FLOW"
    outside["external_person_trips"] = np.nan
    outside["external_trip_status"] = "UNKNOWN_NOT_ZERO_NO_REGIONAL_OD_INPUT"
    outside.to_csv(derived / "external_flow_ledger.csv", index=False)

    prior_pa = pd.read_csv(root / "database" / "demand" / "scenarios" / "boston_activity_prior_r1_20260922" / "productions_attractions.csv")
    activity = prior_pa[["zone_id", "attraction_prior_raw_official_nonres_bld_area_sqft"]].copy()
    zone_demo = zone_demo.merge(activity, on="zone_id", how="left")
    zone_demo["attraction_prior_raw_official_nonres_bld_area_sqft"] = zone_demo["attraction_prior_raw_official_nonres_bld_area_sqft"].fillna(0)
    attr_weight = zone_demo["attraction_prior_raw_official_nonres_bld_area_sqft"].to_numpy(float)
    if attr_weight.sum() <= 0:
        raise RuntimeError("MassGIS attraction prior is empty")
    attr_share = attr_weight / attr_weight.sum()

    tg_rows: list[dict] = []
    for purpose, rate in EFFECTIVE_HH_RATES.items():
        prod = zone_demo["households_estimate_area_weighted"].to_numpy(float) * rate
        attr = prod.sum() * attr_share
        for i, zrow in zone_demo.iterrows():
            tg_rows.append(
                {
                    "zone_id": zrow["zone_id"],
                    "purpose": purpose,
                    "households_estimate_area_weighted": zrow["households_estimate_area_weighted"],
                    "effective_daily_production_rate_per_household": rate,
                    "productions_person_trips_daily": prod[i],
                    "attractions_person_trips_daily": attr[i],
                    "peak_share_combined_am_pm": PEAK_SHARES[purpose],
                    "nonpeak_share_combined_midday_night": 1 - PEAK_SHARES[purpose],
                    "production_source_id": TDM_SOURCE_ID,
                    "attraction_source_id": ACTIVITY_SOURCE_ID,
                    "production_status": "REGIONAL_EFFECTIVE_RATE_TRANSFER_TO_ACS_HOUSEHOLDS_NOT_LOCAL_CALIBRATION",
                    "attraction_status": "MASSGIS_NONRESIDENTIAL_BUILDING_AREA_PROXY_NOT_EMPLOYMENT",
                    "unit": "person_trips_per_average_weekday",
                    "run_id": RUN_ID,
                }
            )
    tg = pd.DataFrame(tg_rows)
    tg.to_csv(derived / "trip_generation_by_purpose.csv", index=False)

    # Build a dense impedance/kernel matrix from the already-computed local road
    # travel-time matrix. beta is retained as an explicit inherited assumption.
    prior_od = pd.read_csv(root / "database" / "demand" / "scenarios" / "boston_activity_prior_r1_20260922" / "od_person.csv")
    zone_ids = zone_demo["zone_id"].tolist()
    pos = {z: i for i, z in enumerate(zone_ids)}
    impedance = np.full((len(zone_ids), len(zone_ids)), np.nan)
    impedance_source = np.full((len(zone_ids), len(zone_ids)), "", dtype=object)
    for row in prior_od.itertuples(index=False):
        if row.o_zone_id in pos and row.d_zone_id in pos:
            impedance[pos[row.o_zone_id], pos[row.d_zone_id]] = float(row.impedance_min)
            impedance_source[pos[row.o_zone_id], pos[row.d_zone_id]] = "existing_gmns_drive_free_flow_matrix"
    fallback = haversine_minutes(
        zone_demo["centroid_lon"].to_numpy(float),
        zone_demo["centroid_lat"].to_numpy(float),
    )
    missing_impedance = ~np.isfinite(impedance)
    impedance[missing_impedance] = fallback[missing_impedance]
    impedance_source[missing_impedance] = "geodesic_detour_1_25_at_25_mph_fallback"
    beta = 0.08
    kernel = np.where(np.isfinite(impedance), np.exp(-beta * impedance), 0.0)
    od_rows: list[dict] = []
    ipf_report: list[dict] = []
    for purpose in EFFECTIVE_HH_RATES:
        part = tg[tg["purpose"].eq(purpose)].set_index("zone_id").reindex(zone_ids)
        prod = part["productions_person_trips_daily"].to_numpy(float)
        attr = part["attractions_person_trips_daily"].to_numpy(float)
        mat, iterations, err = ipf_matrix(prod, attr, kernel)
        ipf_report.append({"purpose": purpose, "iterations": iterations, "max_margin_error": err, "daily_total": float(mat.sum())})
        nz_i, nz_j = np.nonzero(mat > 1e-10)
        npf = NONPEAK_PA_TO_OD[purpose]
        nonpeak = 1 - PEAK_SHARES[purpose]
        md_pa_share = nonpeak * npf["MD_PA"]
        md_ap_share = nonpeak * npf["MD_AP"]
        for i, j in zip(nz_i, nz_j):
            trips = float(mat[i, j])
            od_rows.append(
                {
                    "o_zone_id": zone_ids[i],
                    "d_zone_id": zone_ids[j],
                    "purpose": purpose,
                    "person_trips_daily_pa": trips,
                    "person_trips_midday_od": trips * md_pa_share + float(mat[j, i]) * md_ap_share,
                    "impedance_min_drive_free_flow_proxy": float(impedance[i, j]),
                    "impedance_source": impedance_source[i, j],
                    "distribution_model": "doubly_constrained_gravity_ipf",
                    "friction_function": "exp(-beta*drive_free_flow_minutes)",
                    "beta_per_minute": beta,
                    "beta_status": "INHERITED_ENGINEERING_ASSUMPTION_NOT_TDM23_CALIBRATED",
                    "od_status": "REGIONAL_PRODUCTION_RATE_ACTIVITY_ATTRACTION_TRANSFER_NOT_OBSERVED_OD",
                    "period_status": "TDM23_NONPEAK_AND_MD_PA_AP_FACTORS_APPLIED_WITHOUT_AM_RELABELING",
                    "run_id": RUN_ID,
                }
            )
    regional_od = pd.DataFrame(od_rows)
    regional_od.to_csv(derived / "regional_od_h3.csv", index=False)
    pd.DataFrame(ipf_report).to_csv(reports / "regional_od_balance.csv", index=False)

    mode_rows = []
    for purpose, shares in TDM23_BASE_MODE_SHARE_PCT.items():
        for mode, pct in shares.items():
            mode_rows.append(
                {
                    "purpose": purpose,
                    "mode": mode,
                    "share": pct / 100.0,
                    "share_percent_reported": pct,
                    "source_id": "ctps_tdm23_2_0_x_mc_base_model_output",
                    "status": "REGIONAL_MODEL_OUTPUT_BASELINE_NOT_LOCAL_OBSERVATION",
                }
            )
    pd.DataFrame(mode_rows).to_csv(derived / "ctps_tdm23_base_mode_share.csv", index=False)

    source_inputs = sorted(list(raw_acs.glob("*.json")) + list(raw_acs.glob("*.geojson")))
    summary = {
        "run_id": RUN_ID,
        "acs_release": "ACS 2024 5-year (2020-2024)",
        "acs_intersecting_block_groups": int(len(acs_stats)),
        "h3_fine_zones": int(len(zone_demo)),
        "h3_zones_with_acs_coverage": int((zone_demo["contributing_block_groups"] > 0).sum()),
        "population_area_weighted_in_core": float(zone_demo["population_estimate_area_weighted"].sum()),
        "households_area_weighted_in_core": float(zone_demo["households_estimate_area_weighted"].sum()),
        "daily_person_trip_total_all_purposes": float(tg.groupby("purpose")["productions_person_trips_daily"].sum().sum()),
        "purpose_daily_totals": {k: float(v) for k, v in tg.groupby("purpose")["productions_person_trips_daily"].sum().items()},
        "impedance_pair_count": int(impedance.size),
        "impedance_fallback_pair_count": int(missing_impedance.sum()),
        "impedance_fallback_method": "great_circle_distance_times_1.25_detour_at_25_mph; distribution-only proxy",
        "source_hashes": {str(p.relative_to(root)): sha256(p) for p in source_inputs},
        "interpretation": "ACS estimates are area-weighted to H3; TDM23 effective rates are transferred; attractions and OD distribution remain documented proxies.",
    }
    (reports / "regional_demand_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
