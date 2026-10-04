"""Reproducible, explicitly transferred TCS engineering demand scenario."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
B = ROOT / "phase_b"
B.mkdir(exist_ok=True)


def read(name):
    with (B / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write(name, rows, fields):
    with (B / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


zones = sorted(read("zone_activity_r2.csv"), key=lambda r: int(r["zone_id"]))
ids = [int(z["zone_id"]) for z in zones]
n = len(ids)
assert n == 95
idx = {z: i for i, z in enumerate(ids)}
pop = np.array([float(z["population"]) for z in zones])
cost_rows = read("mode_costs_by_od.csv")
drive = np.full((n, n), np.inf)
cost = {}
for r in cost_rows:
    i, j = idx[int(r["o_zone_id"])], idx[int(r["d_zone_id"])]
    drive[i, j] = float(r["drive_time_min"])
    cost[i, j] = r
assert np.isfinite(drive[~np.eye(n, dtype=bool)]).all()

# TCS 2022 final main report, Table 3.3 p.10 and E.2.13 p.iii:
# 1.69 mechanised trips/person/weekday; 13% in 08:00-09:00.
# Purpose totals, million/day: HBW 5.103, HBS 1.162, HBO 5.139, NHB+EB 0.959.
purpose_totals = {"HBW": 5.103, "HBS": 1.162, "HBO": 5.139, "NHB_EB": 0.959}
shares = {k: v / sum(purpose_totals.values()) for k, v in purpose_totals.items()}
trip_rate = 1.69
am_share = 0.13
capture = {"low": 0.20, "base": 0.30, "high": 0.40}
beta = {"low": 0.025, "base": 0.05, "high": 0.08}
intrazonal_fraction = 0.05  # explicit engineering allowance, not locally estimated


def attractions(purpose):
    a = []
    for z in zones:
        res = float(z["residential_activity"])
        com = float(z["commercial_activity"])
        ins = float(z["institutional_activity"])
        tr = float(z["transport_activity"])
        mix = float(z["mixed_use_activity"])
        p = float(z["population"])
        if purpose == "HBW":
            x = 1 + com + .4 * mix + .5 * tr
        elif purpose == "HBS":
            x = 1 + ins + .1 * mix
        elif purpose == "HBO":
            x = 1 + .25 * com + .2 * mix + .2 * res + .1 * p
        else:
            x = 1 + .3 * com + .25 * ins + .2 * mix + .1 * tr
        a.append(x)
    return np.array(a, dtype=float)


def ipf(prod, attr, impedance):
    # Strictly positive on all directed reachable interzonal cells only.
    mat = np.exp(-impedance * drive)
    mat[~np.isfinite(mat)] = 0.0
    np.fill_diagonal(mat, 0.0)
    mat *= prod[:, None]
    for iteration in range(10000):
        rs = mat.sum(axis=1)
        if np.any(rs <= 0):
            raise ValueError("IPF row has no reachable attraction")
        mat *= (prod / rs)[:, None]
        cs = mat.sum(axis=0)
        if np.any(cs <= 0):
            raise ValueError("IPF column has no reachable production")
        mat *= (attr / cs)[None, :]
        residual = max(np.max(np.abs(mat.sum(axis=1) - prod)),
                       np.max(np.abs(mat.sum(axis=0) - attr)))
        if residual < 1e-8:
            return mat, iteration + 1, residual
    raise ValueError(f"IPF did not balance, residual={residual}")


pa_rows = []
od_purpose = []
od_total = np.zeros((n, n))
balance = {}
for purpose, share in shares.items():
    produced = pop * trip_rate * am_share * capture["base"] * share
    intra = produced * intrazonal_fraction
    interprod = produced - intra
    potential = attractions(purpose)
    attr = potential / potential.sum() * interprod.sum()
    matrix, iters, residual = ipf(interprod, attr, beta["base"])
    od_total += matrix
    balance[purpose] = {
        "generated_person_trips": float(produced.sum()),
        "intrazonal_excluded_person_trips": float(intra.sum()),
        "interzonal_person_trips": float(matrix.sum()),
        "ipf_iterations": iters,
        "max_absolute_row_or_column_residual": float(residual),
        "attraction_basis": "official building footprint*reported storeys with name keyword use proxy; purpose-specific fixed weights",
    }
    for i, z in enumerate(ids):
        pa_rows.append({"zone_id": z, "purpose": purpose,
                        "population": pop[i], "generation_person_trips_am": produced[i],
                        "intrazonal_excluded_person_trips_am": intra[i],
                        "interzonal_production_person_trips_am": interprod[i],
                        "interzonal_attraction_person_trips_am": attr[i],
                        "attraction_proxy_weight": potential[i],
                        "parameter_grade": "TCS_TERRITORY_TRANSFER_PLUS_ENGINEERING_CAPTURE_AND_ACTIVITY_PROXY"})
    for (i, j), r in cost.items():
        od_purpose.append({"o_zone_id": ids[i], "d_zone_id": ids[j],
                           "purpose": purpose, "person_trips_am": matrix[i, j],
                           "drive_time_min": drive[i, j], "impedance_beta_per_min": beta["base"],
                           "o_access_node_id": r["o_access_node_id"],
                           "d_access_node_id": r["d_access_node_id"]})

write("production_attraction_r2.csv", pa_rows, list(pa_rows[0]))
write("od_person_distribution_r2.csv", od_purpose, list(od_purpose[0]))

# This is a choice sensitivity over TCS-seeded trip opportunities. The survey's
# mechanised-trip rate does not establish a local all-mode trip total or walk share.
choice_variants = {
    "low_drive": {"lambda": .06, "drive_asc": -1.6, "transit_asc": 0., "walk_asc": .6},
    "base": {"lambda": .07, "drive_asc": -1., "transit_asc": 0., "walk_asc": .5},
    "high_drive": {"lambda": .08, "drive_asc": -.4, "transit_asc": 0., "walk_asc": .4},
}


def probabilities(r, spec):
    raw = {}
    for mode in ("drive", "transit", "walk"):
        v = r[{"drive": "drive_generalized_min",
               "transit": "transit_generalized_min",
               "walk": "walk_time_min"}[mode]]
        if v in ("", None):
            continue
        raw[mode] = spec[mode + "_asc"] - spec["lambda"] * float(v)
    m = max(raw.values())
    expo = {k: math.exp(v - m) for k, v in raw.items()}
    denom = sum(expo.values())
    return {k: expo.get(k, 0.0) / denom for k in ("drive", "transit", "walk")}


probrows = []
moderows = []
lineage = []
drive_rows = []
for (i, j), r in sorted(cost.items()):
    q = float(od_total[i, j])
    variants = {name: probabilities(r, spec) for name, spec in choice_variants.items()}
    p = variants["base"]
    probrows.append({"o_zone_id": ids[i], "d_zone_id": ids[j],
                     **{f"{mode}_prob_{name}": variants[name][mode]
                        for name in variants for mode in ("drive", "transit", "walk")},
                     "choice_status": "ENGINEERING_SENSITIVITY_NOT_LOCAL_CALIBRATION"})
    occupancy = 1.5
    vehicle_pce = q * p["drive"] / occupancy
    moderows.append({"o_zone_id": ids[i], "d_zone_id": ids[j],
                     "total_trip_opportunities_person_am": q,
                     "drive_person_trips_am": q * p["drive"],
                     "transit_person_trips_am": q * p["transit"],
                     "walk_person_trips_am": q * p["walk"],
                     "drive_occupancy_person_per_vehicle": occupancy,
                     "drive_vehicles_am": vehicle_pce,
                     "drive_pce_factor": 1.0,
                     "loaded_drive_pce_per_one_hour_am": vehicle_pce,
                     "analysis_period": "generic_weekday_08_00_09_00",
                     "scenario_status": "UNVALIDATED_FOUR_STAGE_ENGINEERING_SCENARIO"})
    lineage.append({"o_zone_id": ids[i], "d_zone_id": ids[j],
                    "o_access_node_id": r["o_access_node_id"],
                    "d_access_node_id": r["d_access_node_id"],
                    "drive_cost_status": r["drive_cost_status"],
                    "walk_cost_status": r["walk_status"],
                    "transit_cost_status": r["transit_status"],
                    "tcs_source": "TCS_2022_MAIN_TABLE_3_3_AND_E_2_13_TERRITORY_TRANSFER",
                    "activity_source": "2021_SSG_PLUS_CSDI_BUILDING_PROXY",
                    "demand_status": "MODELLED_NOT_OBSERVED"})
    drive_rows.append({"o_zone_id": r["o_access_node_id"],
                       "d_zone_id": r["d_access_node_id"], "volume": vehicle_pce,
                       "source_o_zone_id": ids[i], "source_d_zone_id": ids[j],
                       "scenario_tier": "four_stage_full"})

for name, rows in (("mode_probabilities_by_od.csv", probrows),
                   ("mode_demand_by_od.csv", moderows),
                   ("OD_LINEAGE.csv", lineage)):
    write(name, rows, list(rows[0]))
static = B / "static_input"
static.mkdir(exist_ok=True)
with (static / "four_stage_full_demand.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(drive_rows[0]))
    w.writeheader()
    w.writerows(drive_rows)

generated = sum(x["generated_person_trips"] for x in balance.values())
intra = sum(x["intrazonal_excluded_person_trips"] for x in balance.values())
inter = float(od_total.sum())
assert abs(generated - intra - inter) < 1e-7
assert abs(sum(float(r["total_trip_opportunities_person_am"]) for r in moderows) - inter) < 1e-6
assert abs(sum(sum(float(r[x]) for x in ("drive_person_trips_am", "transit_person_trips_am", "walk_person_trips_am")) for r in moderows) - inter) < 1e-6
report = {"status": "PASS", "zone_count": n, "positive_directed_interzonal_pairs": len(cost),
          "purpose_components": balance,
          "tcs_mechanised_reference_person_trips_per_day": float(pop.sum() * trip_rate),
          "capture_fraction_base": capture["base"],
          "external_or_uncaptured_reference_person_trips_am": float(pop.sum() * trip_rate * am_share * (1 - capture["base"])),
          "generated_local_trip_opportunities_person_am": generated,
          "intrazonal_excluded_person_am": intra,
          "unreachable_excluded_person_am": 0.0,
          "interzonal_trip_opportunities_person_am": inter,
          "drive_person_am": sum(float(r["drive_person_trips_am"]) for r in moderows),
          "transit_person_am": sum(float(r["transit_person_trips_am"]) for r in moderows),
          "walk_person_am": sum(float(r["walk_person_trips_am"]) for r in moderows),
          "drive_pce_per_one_hour_am": sum(float(r["loaded_drive_pce_per_one_hour_am"]) for r in moderows),
          "total_conservation_residual": generated - intra - inter,
          "rate_sensitivity_local_generated_person_am": {
              k: float(pop.sum() * trip_rate * am_share * v) for k, v in capture.items()},
          "impedance_beta_sensitivity_per_min": beta,
          "interpretation": "Engineering trip-opportunity scenario transferred from territory-wide mechanised TCS. Walk mode is a counterfactual choice; neither total nor shares are locally observed or calibrated."}
(B / "DISTRIBUTION_BALANCE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
(B / "MODE_CHOICE_SOURCE_AND_SENSITIVITY.md").write_text(
    "# Four-stage policy and evidence\n\n"
    "The 2022 Transport Department Travel Characteristics Survey final main report, Table 3.3 (p. 10), "
    "reports 1.69 weekday mechanised trips per person and purpose totals HBW 5.103m, HBS 1.162m, "
    "HBO 5.139m, NHB+EB 0.959m. Executive summary E.2.13 reports about 13% of daily "
    "mechanised trips in 08:00–09:00. These territory-wide values are transferred, not local estimates. "
    "Source: https://www.td.gov.hk/en/publications_and_press_releases/publications/free_publications/tcsfr/index.html\n\n"
    "The assumed local/internal capture is 0.20/0.30/0.40 (low/base/high). The remainder is "
    "uncaptured or external and is retained in the ledger. Intrazonal demand is 5% of generated "
    "local trip opportunities and excluded from interzonal assignment. Production uses SSG population. "
    "Attractions are normalized purpose-specific building/activity proxies, not observed employment. "
    "Gravity uses exp(-β × turn-aware drive minutes), β=0.025/0.05/0.08 per minute, with IPF "
    "to balance rows and columns. No local impedance calibration is claimed.\n\n"
    "Mode choice is a sensitivity-only multinomial logit. The base time coefficient is 0.07/min "
    "with constants drive=-1, transit=0, walk=0.5; variants are saved by OD. These coefficients "
    "are engineering choices. The TCS mechanised rate provides a trip-opportunity reference; "
    "introducing walk in the choice set is a counterfactual scenario, not an observed local all-mode total. "
    "Drive occupancy 1.5 persons/vehicle, PCE factor 1, 08:00–09:00 period are engineering assumptions. "
    "Transit costs use GTFS generic Monday service and exact published pair fares; walking costs use "
    "the conservative pedestrian subgraph with explicit fallback status. No local mode-share calibration "
    "or traffic forecast claim is made.\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("status", "positive_directed_interzonal_pairs", "generated_local_trip_opportunities_person_am", "interzonal_trip_opportunities_person_am", "drive_pce_per_one_hour_am")}, indent=2))
