"""Run a source-backed TDM23 HBW base-share pivot sensitivity.

This is not a full TDM23 reproduction: the public report does not publish the
nest scale parameters or all zonal explanatory inputs.  It preserves the
reported tree and base shares, applies the published HBW time coefficients to
the S1->S2 skim change, and reports a grid of transit nest scales rather than
silently substituting an MNL.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


RUN_ID = "behavior_feedback_r1"
LEAVES = ("DA", "S2", "S3", "WK", "BK", "TW", "TA", "SB", "RS")
NEST = {"DA": "Auto", "S2": "Auto", "S3": "Auto", "WK": "NonMotor", "BK": "NonMotor",
        "TW": "Transit", "TA": "Transit", "SB": "SchoolBus", "RS": "RideService"}
MU_GRID = (0.25, 0.50, 0.75, 1.00)
OCCUPANCY = {"DA": 1.0, "S2": 2.0, "S3": 3.627, "RS": 1.21}
BETA_IVTT = -0.0201  # Table 44, HBW, per minute.
BETA_OVTT = -0.0431  # Table 44, HBW, per minute.
BETA_COST = -0.0613  # Table 44, HBW, per 2010 USD.
CPI_U_2010_ANNUAL = 218.056
CPI_U_2026_AUGUST = 334.980
NOMINAL_2026_TO_2010_USD = CPI_U_2010_ANNUAL / CPI_U_2026_AUGUST
CPI_SOURCE_URL_2010 = "https://www.bls.gov/news.release/archives/cpi_01142011.pdf"
CPI_SOURCE_URL_2026 = "https://www.bls.gov/news.release/archives/cpi_09112026.htm"


def fare_delta_2010_usd(s1_fare_nominal_2026: float, target_fare_nominal_2026: float) -> float:
    """One-time BLS CPI-U conversion for a selected-itinerary nominal fare delta."""
    if not np.isfinite(s1_fare_nominal_2026) or not np.isfinite(target_fare_nominal_2026):
        return math.nan
    return (target_fare_nominal_2026 - s1_fare_nominal_2026) * NOMINAL_2026_TO_2010_USD


def pivot_probabilities(base: dict[str, float], delta: dict[str, float], mu_transit: float) -> dict[str, float]:
    nest_totals: dict[str, float] = {}
    for leaf, p in base.items():
        nest_totals[NEST[leaf]] = nest_totals.get(NEST[leaf], 0.0) + p
    conditional: dict[str, float] = {leaf: p / nest_totals[NEST[leaf]] for leaf, p in base.items() if nest_totals[NEST[leaf]] > 0}
    nest_factor: dict[str, float] = {}
    leaf_cond_new: dict[str, float] = {}
    for nest, total in nest_totals.items():
        if total <= 0:
            nest_factor[nest] = 1.0
            continue
        leaves = [x for x in base if NEST[x] == nest and total > 0]
        mu = mu_transit if nest == "Transit" else 1.0
        denom = sum(conditional[x] * math.exp(delta.get(x, 0.0) / mu) for x in leaves)
        nest_factor[nest] = math.exp(mu * math.log(denom))
        for x in leaves:
            leaf_cond_new[x] = conditional[x] * math.exp(delta.get(x, 0.0) / mu) / denom
    root_denom = sum(nest_totals[n] * nest_factor[n] for n in nest_totals)
    return {
        leaf: 0.0 if base[leaf] <= 0 else nest_totals[NEST[leaf]] * nest_factor[NEST[leaf]] / root_denom * leaf_cond_new[leaf]
        for leaf in base
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--run-dir", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    run = (args.run_dir or root / "runs" / RUN_ID).resolve()
    derived, reports = run / "derived", run / "reports"

    shares = pd.read_csv(derived / "ctps_tdm23_base_mode_share.csv")
    shares = shares[shares["purpose"].eq("HBW")].set_index("mode")["share"].to_dict()
    # Normalize only reported rounding noise; retain all official leaf modes.
    shares = {m: float(shares[m]) / sum(float(shares[x]) for x in LEAVES) for m in LEAVES}
    skims = pd.read_csv(derived / "mode_specific_od_costs.csv")
    panel = pd.read_csv(derived / "validation_panel.csv")
    access = pd.read_csv(root / "database" / "zones" / "zone_access.csv", dtype={"zone_id": str, "access_node_id": str})
    access = access.set_index("zone_id")

    transit = skims[skims["mode"].eq("transit_walk_access")].copy()
    keys = ["od_id", "departure_time"]
    s1 = transit[transit["scenario_id"].eq("S1_planned_service")].set_index(keys)
    s2 = transit[transit["scenario_id"].eq("S2_exploratory_gps_overlay")].set_index(keys)
    srestore = transit[transit["scenario_id"].eq("Srestore_overlay_off_recomputed")].set_index(keys)

    probability_rows: list[dict] = []
    component_rows: list[dict] = []
    demand_rows: list[dict] = []
    vehicle_rows: list[dict] = []
    exclusion_rows: list[dict] = []
    for key in sorted(set(s1.index) & set(s2.index) & set(srestore.index)):
        od_id, departure = key
        r1, r2, rr = s1.loc[key], s2.loc[key], srestore.loc[key]
        od = panel.loc[panel["od_id"].eq(od_id)].iloc[0]
        person_weight = float(od.person_trips_midday_od) / 3.0
        statuses = skims[
            skims["od_id"].eq(od_id)
            & skims["departure_time"].eq(departure)
            & skims["mode"].isin(["drive", "walk", "bike", "transit_walk_access"])
        ]
        incomplete = statuses[~statuses["availability_status"].eq("available")]
        if not incomplete.empty:
            exclusion_rows.append({
                "od_id": od_id, "departure_time": departure, "eligible_person_trips": person_weight,
                "reason": ";".join(
                    f"{row.scenario_id}:{row.mode}:{row.availability_status}" for row in incomplete.itertuples(index=False)
                ),
                "status": "EXCLUDED_FROM_PROBABILITY_DENOMINATOR_AND_VEHICLE_ASSIGNMENT_NOT_ZERO_DEMAND",
            })
            continue
        both_available = r1.availability_status == "available" and r2.availability_status == "available"
        restore_available = r1.availability_status == "available" and rr.availability_status == "available"

        def utility_delta(target: pd.Series, available: bool, scenario_to: str) -> tuple[float, dict]:
            delta_ivtt = float(target.in_vehicle_min - r1.in_vehicle_min) if available else 0.0
            delta_ovtt = float((target.walk_min + target.wait_min) - (r1.walk_min + r1.wait_min)) if available else 0.0
            fares_known = available and np.isfinite(float(r1.fare_usd)) and np.isfinite(float(target.fare_usd))
            delta_cost_nominal = float(target.fare_usd - r1.fare_usd) if fares_known else math.nan
            delta_cost_2010 = fare_delta_2010_usd(float(r1.fare_usd), float(target.fare_usd)) if fares_known else math.nan
            time_utility = BETA_IVTT * delta_ivtt + BETA_OVTT * delta_ovtt
            delta_v = time_utility + (BETA_COST * delta_cost_2010 if fares_known else 0.0)
            utility_scope = "TIME_AND_GTFS_FARE_CPI_CONVERTED" if fares_known else "TIME_ONLY_FARE_UNKNOWN_NOT_ZERO"
            row = {
                "od_id": od_id,
                "departure_time": departure,
                "mode": "TW",
                "scenario_from": "S1_planned_service",
                "scenario_to": scenario_to,
                "s1_path_id": r1.path_id,
                "target_path_id": target.path_id,
                "s1_fare_nominal_usd": r1.fare_usd,
                "target_fare_nominal_usd": target.fare_usd,
                "fare_price_year": 2026,
                "fare_medium": target.get("fare_medium", None),
                "fare_rule": target.cost_status,
                "delta_ivtt_min": delta_ivtt,
                "delta_ovtt_min": delta_ovtt,
                "delta_cost_nominal_2026_usd": delta_cost_nominal,
                "cpi_u_2010_annual": CPI_U_2010_ANNUAL,
                "cpi_u_2026_august": CPI_U_2026_AUGUST,
                "nominal_2026_to_2010_factor": NOMINAL_2026_TO_2010_USD,
                "delta_cost_2010_usd": delta_cost_2010,
                "beta_ivtt_per_min": BETA_IVTT,
                "beta_ovtt_per_min": BETA_OVTT,
                "beta_cost_per_2010_usd": BETA_COST,
                "time_utility_delta": time_utility,
                "cost_utility_delta": BETA_COST * delta_cost_2010 if fares_known else math.nan,
                "delta_utility": delta_v,
                "utility_scope": utility_scope,
                "availability_status": "evaluated_both_scenarios" if available else "not_available_in_one_or_both_scenarios",
                "source_reference": "TDM23.2.0 Table 44; selected-itinerary GTFS Fares v2; BLS CPI-U 2010 annual and 2026-08",
            }
            return delta_v, row

        delta_v, s2_components = utility_delta(r2, both_available, "S2_exploratory_gps_overlay")
        restore_delta_v, restore_components = utility_delta(rr, restore_available, "Srestore_overlay_off_recomputed")
        component_rows.extend([s2_components, restore_components])
        for mu in MU_GRID:
            p1 = shares.copy()
            p2 = pivot_probabilities(shares, {"TW": delta_v}, mu)
            prestore = pivot_probabilities(shares, {"TW": restore_delta_v}, mu)
            for scenario, probs in (
                ("S1_planned_service", p1),
                ("S2_exploratory_gps_overlay", p2),
                ("Srestore_overlay_off_recomputed", prestore),
            ):
                for mode in LEAVES:
                    if mode in {"DA", "S2", "S3"}:
                        avail = "available_evaluated_from_drive_skim"
                    elif mode == "WK":
                        avail = "available_evaluated_from_walk_skim"
                    elif mode == "BK":
                        avail = "available_evaluated_from_bike_skim"
                    elif mode == "TW":
                        avail = "available_evaluated_from_gtfs_walk_access_skim"
                    elif mode in {"TA", "RS"}:
                        avail = "unknown_not_evaluated_base_share_retained"
                    else:
                        avail = "not_applicable_zero_reported_HBW_base_share"
                    p = float(probs[mode])
                    common = {
                        "od_id": od_id, "o_zone_id": od.o_zone_id, "d_zone_id": od.d_zone_id,
                        "departure_time": departure, "purpose": "HBW", "scenario_id": scenario,
                        "mu_transit_sensitivity": mu, "mu_status": "MISSING_OFFICIAL_VALUE_SENSITIVITY_GRID",
                        "mode": mode, "nest": NEST[mode], "probability": p,
                        "availability_status": avail,
                        "model_status": "TDM23_REGIONAL_BASE_SHARE_NESTED_PIVOT_NOT_FULL_TDM23_REPRODUCTION",
                    }
                    probability_rows.append(common)
                    persons = person_weight * p
                    demand_rows.append({**common, "eligible_person_trips": person_weight,
                                        "person_trips_by_mode": persons,
                                        "departure_weight_status": "EQUAL_THIRDS_ACROSS_THREE_DISCRETE_PILOT_DEPARTURES_NOT_OBSERVED_PROFILE"})
                    if mode in OCCUPANCY:
                        vehicles = persons / OCCUPANCY[mode]
                        if mode == "RS":
                            road_status = "included_occupied_passenger_trip_only_empty_repositioning_not_modeled_not_zero"
                            empty_status = "UNKNOWN_NOT_ZERO_EMPTY_REPOSITIONING_EXCLUDED"
                        else:
                            road_status = "included_private_auto_passenger_trip"
                            empty_status = "not_applicable"
                        vehicle_rows.append({
                            **common, "person_trips_by_mode": persons, "occupancy_persons_per_vehicle": OCCUPANCY[mode],
                            "vehicle_trips": vehicles, "road_leg_status": road_status,
                            "empty_repositioning_status": empty_status,
                            "assignment_inclusion": True,
                            "o_node_id": str(access.loc[od.o_zone_id, "access_node_id"]),
                            "d_node_id": str(access.loc[od.d_zone_id, "access_node_id"]),
                        })
                    elif mode == "TA":
                        vehicle_rows.append({
                            **common, "person_trips_by_mode": persons, "occupancy_persons_per_vehicle": np.nan,
                            "vehicle_trips": np.nan, "road_leg_status": "unknown_auto_access_leg_not_implemented",
                            "empty_repositioning_status": "not_applicable",
                            "assignment_inclusion": False,
                            "o_node_id": None, "d_node_id": None,
                        })
                    else:
                        vehicle_rows.append({
                            **common, "person_trips_by_mode": persons, "occupancy_persons_per_vehicle": np.nan,
                            "vehicle_trips": np.nan,
                            "road_leg_status": "not_private_road_vehicle_assignment_mode",
                            "empty_repositioning_status": "not_applicable",
                            "assignment_inclusion": False,
                            "o_node_id": None, "d_node_id": None,
                        })

    probs = pd.DataFrame(probability_rows)
    components = pd.DataFrame(component_rows)
    demand = pd.DataFrame(demand_rows)
    vehicles = pd.DataFrame(vehicle_rows)
    probs.to_csv(derived / "od_mode_probabilities.csv", index=False)
    components.to_csv(derived / "mode_utility_delta_components.csv", index=False)
    demand.to_csv(derived / "person_demand_by_mode.csv", index=False)
    vehicles.to_csv(derived / "person_to_vehicle_crosswalk.csv", index=False)
    exclusions = pd.DataFrame(exclusion_rows)
    exclusions.to_csv(derived / "mode_choice_exclusions.csv", index=False)

    probs[probs["scenario_id"].eq("Srestore_overlay_off_recomputed")].to_csv(
        derived / "srestore_od_mode_probabilities.csv", index=False
    )
    demand[demand["scenario_id"].eq("Srestore_overlay_off_recomputed")].to_csv(
        derived / "srestore_person_demand_by_mode.csv", index=False
    )
    vehicles[vehicles["scenario_id"].eq("Srestore_overlay_off_recomputed")].to_csv(
        derived / "srestore_person_to_vehicle_crosswalk.csv", index=False
    )

    # The executable FW interface uses only the explicitly labelled mu=1 root-scale
    # boundary diagnostic; every other value remains available as sensitivity output.
    boundary = vehicles[
        vehicles["mu_transit_sensitivity"].eq(1.0)
        & vehicles["assignment_inclusion"].astype(bool)
        & vehicles["vehicle_trips"].notna()
    ].copy()
    for scenario in ("S1_planned_service", "S2_exploratory_gps_overlay"):
        out_dir = run / "assignment_inputs" / scenario
        out_dir.mkdir(parents=True, exist_ok=True)
        part = boundary[boundary["scenario_id"].eq(scenario)]
        assignment = part.groupby(["o_node_id", "d_node_id"], as_index=False)["vehicle_trips"].sum()
        assignment = assignment.rename(columns={"o_node_id": "o_zone_id", "d_node_id": "d_zone_id", "vehicle_trips": "volume"})
        assignment.to_csv(out_dir / "demand.csv", index=False)
        source_link = root / "staging" / "assignment" / "boston_quality_r1_20260922" / "link.csv"
        pd.read_csv(source_link).to_csv(out_dir / "link.csv", index=False)

    check = probs.groupby(["od_id", "departure_time", "scenario_id", "mu_transit_sensitivity"])["probability"].sum()
    restore_keys = ["od_id", "departure_time", "mu_transit_sensitivity", "mode"]
    s1p = probs[probs["scenario_id"].eq("S1_planned_service")][restore_keys + ["probability"]]
    srp = probs[probs["scenario_id"].eq("Srestore_overlay_off_recomputed")][restore_keys + ["probability"]]
    restore_prob = s1p.merge(srp, on=restore_keys, how="outer", suffixes=("_s1", "_restore"), indicator=True)
    restore_prob["probability_abs_error"] = (
        restore_prob["probability_s1"] - restore_prob["probability_restore"]
    ).abs()
    s1d = demand[demand["scenario_id"].eq("S1_planned_service")][restore_keys + ["person_trips_by_mode"]]
    srd = demand[demand["scenario_id"].eq("Srestore_overlay_off_recomputed")][restore_keys + ["person_trips_by_mode"]]
    restore_demand = s1d.merge(srd, on=restore_keys, how="outer", suffixes=("_s1", "_restore"), indicator=True)
    restore_demand["person_demand_abs_error"] = (
        restore_demand["person_trips_by_mode_s1"] - restore_demand["person_trips_by_mode_restore"]
    ).abs()
    restore_comparison = restore_prob.merge(
        restore_demand[restore_keys + ["person_demand_abs_error"]], on=restore_keys, how="outer"
    )
    restore_comparison.to_csv(derived / "srestore_model_comparison.csv", index=False)
    restore_error = float(restore_prob["probability_abs_error"].max())
    restore_demand_error = float(restore_demand["person_demand_abs_error"].max())
    negative_control = json.loads((reports / "srestore_negative_control.json").read_text(encoding="utf-8"))
    summary = {
        "run_id": run.name,
        "model_id": "ctps_tdm23_2_0_regional_base_share_hbw_nested_pivot_sensitivity",
        "tree": {"Auto": ["DA", "S2", "S3"], "NonMotor": ["WK", "BK"], "Transit": ["TW", "TA"], "SchoolBus": ["SB"], "RideService": ["RS"]},
        "mu_transit_grid": list(MU_GRID),
        "official_mu_transit_available": False,
        "other_nest_mu": 1.0,
        "fw_mu_transit_boundary": 1.0,
        "probability_rows": len(probs),
        "eligible_od_departure_rows": int(probs[["od_id", "departure_time"]].drop_duplicates().shape[0]),
        "excluded_od_departure_rows": int(len(exclusions)),
        "excluded_person_trip_weight_not_zeroed": float(exclusions["eligible_person_trips"].sum()) if len(exclusions) else 0.0,
        "max_probability_sum_error": float((check - 1).abs().max()),
        "s2_rows_with_nonzero_delta_utility": int(
            (
                components["scenario_to"].eq("S2_exploratory_gps_overlay")
                & (components["delta_utility"].abs() > 1e-12)
            ).sum()
        ),
        "s2_rows_with_nonzero_nominal_fare_delta": int(
            (
                components["scenario_to"].eq("S2_exploratory_gps_overlay")
                & (components["delta_cost_nominal_2026_usd"].abs() > 1e-12)
            ).sum()
        ),
        "s2_rows_time_only_due_unknown_fare": int(
            (
                components["scenario_to"].eq("S2_exploratory_gps_overlay")
                & components["utility_scope"].eq("TIME_ONLY_FARE_UNKNOWN_NOT_ZERO")
            ).sum()
        ),
        "cost_price_conversion": {
            "nominal_fare_year": 2026,
            "coefficient_price_year": 2010,
            "cpi_u_2010_annual": CPI_U_2010_ANNUAL,
            "cpi_u_2026_august": CPI_U_2026_AUGUST,
            "factor_2026_to_2010": NOMINAL_2026_TO_2010_USD,
            "source_2010": CPI_SOURCE_URL_2010,
            "source_2026": CPI_SOURCE_URL_2026,
        },
        "srestore_max_probability_error": restore_error,
        "srestore_max_person_demand_error": restore_demand_error,
        "srestore_negative_control": negative_control,
        "rs_vehicle_branch": "occupied_passenger_trip_only_using_1_21_persons_per_vehicle_empty_repositioning_unknown_not_zero",
        "ta_vehicle_branch": "not_loaded_auto_access_leg_not_implemented",
        "fw_interface_variant": "mu_transit_1.0_root_scale_boundary_diagnostic_not_empirical",
        "interpretation": "Regional-base-share nested-pivot sensitivity. S1 does not use absolute local cost to predict shares; this is not a local calibration, a full TDM23 run, or empirical validation.",
    }
    (reports / "mode_choice_feedback_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
