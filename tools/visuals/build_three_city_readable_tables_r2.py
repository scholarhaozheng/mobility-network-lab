#!/usr/bin/env python3
"""Repeatable presentation-only metric rows from the stable R1 source CSVs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/data/three_city_r1"
OUT = ROOT / "docs/data/three_city_r2"
OUT.mkdir(parents=True, exist_ok=True)


def read(name):
    path = SOURCE / f"THREE_CITY_{name}_STATISTICS.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle)), path


def table(heads, lines, note, name, source):
    out = ["| Metric | " + " | ".join(heads) + " |",
           "|---|" + "---|" * len(heads)]
    for label, values in lines:
        assert len(values) == len(heads), (label, values)
        out.append("| " + label + " | " + " | ".join(str(x).replace("|", "/") for x in values) + " |")
    out += ["", note, "", f"[Machine-readable CSV](../three_city_r1/{source.name}) · [Readable-table source record]({name}.source.json).", ""]
    dest = OUT / f"{name}.md"
    dest.write_text("\n".join(out), encoding="utf-8")
    record = {"source_csv": f"../three_city_r1/{source.name}",
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "builder": "tools/visuals/build_three_city_readable_tables_r2.py",
              "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "output_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
              "scientific_solver_rerun": False}
    (OUT / f"{name}.source.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


gmns, gsrc = read("GMNS")
b, s, h = gmns
gheads = ["Boston · city-data case", "Sioux Falls · benchmark", "Hong Kong · bounded city case"]
glines = [
    ("Directed physical roads", [f"{r['physical_nodes']} nodes / {r['directed_physical_links']} links" for r in gmns]),
    ("Fine / parent zones", [f"{r['fine_zones']} / {r['parent_zones']}" for r in gmns]),
    ("Centroids / nonphysical access", [f"{r['centroids']} / {r['nonphysical_connectors']}" for r in gmns]),
    ("Transit service layer", [r["transit_stops_routes"] for r in gmns]),
    ("Observation evidence", [r["observation_records"] for r in gmns]),
    ("Evidence grade", [r["data_evidence_status"] for r in gmns]),
]
table(gheads, glines, "Observation counts have different meanings and are not pooled. Sioux is a supplied-demand benchmark, not a demographic or GPS build.", "GMNS_READABLE", gsrc)

static, ssrc = read("STATIC_ASSIGNMENT")
sheads = ["Boston B1 · conditional 2 h", "Sioux Falls · classic 528 OD", "Hong Kong · bounded 1 h"]
slines = [
    ("Physical-node / positive OD pairs", [r["static_od_pairs"] for r in static]),
    ("Assigned demand and period", [r["assigned_demand_and_unit"] for r in static]),
    ("Mathematical problem", [r["cost_model"] for r in static]),
    ("FW evidence", [r["fw_status"] for r in static]),
    ("Algorithm B route", [r["algorithm_b_status"] for r in static]),
    ("Objective and independent gap", [r["objective_gap_certificate"] for r in static]),
    ("Path-to-link reconstruction", [r["physical_link_back_projection"] for r in static]),
]
table(sheads, slines, "Boston B1 is a matched-method holdout, not Boston's largest accepted FW tier. Objectives and demands are not comparable across cities or with finite fixed-cost models.", "STATIC_READABLE", ssrc)

finite, fsrc = read("FINITE_TIME_EXPANDED")
bf, sf, hf = finite
fheads = ["Boston · 10 OD", "Sioux · 200 OD", "Sioux · 250 OD", "Hong Kong · 10 OD"]


def pair(value, delimiter=" / "):
    parts = value.split(delimiter)
    if len(parts) != 2:
        raise ValueError(f"Expected paired Sioux value: {value!r}")
    return [x.strip() for x in parts]


sioux_links = ["24 nodes / 64 links", "24 nodes / 69 links"]
sioux_dyn = ["1,192 nodes / 9,406 arcs", "1,292 nodes / 11,254 arcs"]
flines = [
    ("Selected physical subnetwork", ["90 nodes / 125 links", *sioux_links, "100 nodes / 111 links"]),
    ("Selected OD demands", ["10", "200", "250", "10"]),
    ("One model time step", ["3 s", "seconds not reported", "seconds not reported", "30 s"]),
    ("Number of model steps", ["100", "not reported in public summary", "not reported in public summary", "50"]),
    ("Elapsed model horizon", ["300 s", "not derivable from released summary", "not derivable from released summary", "1,500 s"]),
    ("Dynamic graph", ["9,110 nodes / 22,217 arcs", *sioux_dyn, "11,954 nodes / 24,910 arcs"]),
    ("Same-graph reference LP objective", [bf["reference_lp_objective_vehicle_min"], *pair(sf["reference_lp_objective_vehicle_min"]), hf["reference_lp_objective_vehicle_min"]]),
    ("CG Phase-I zero round", [bf["cg_phase_i_zero_round"], *pair(sf["cg_phase_i_zero_round"]), hf["cg_phase_i_zero_round"]]),
    ("Final CG column pool", [bf["final_column_pool"], *pair(sf["final_column_pool"]), hf["final_column_pool"]]),
    ("CG independent full-DAG pricing", [bf["independent_pricing_closure"], "Not established", "Not established", hf["independent_pricing_closure"]]),
    ("Lagrangian status / gap", [bf["lagrangian_status_gap"], "Accepted; 0.0746% duality gap", "Accepted; 0.3177% duality gap", hf["lagrangian_status_gap"]]),
    ("ADMM status / own-LP difference", [bf["admm_status_residual_gate"], "Accepted R2_S; 6.30e−6", "Accepted R2_S; 7.16e−6", hf["admm_status_residual_gate"]]),
]
table(fheads, flines, "Fixed-cost, hard-capacity finite problems; each column is a separate graph. Objective values are vehicle-minutes, but no cross-city ranking is implied. CG pricing closure does not transfer to Lagrangian or ADMM.", "FINITE_READABLE", fsrc)
print("Built three readable metric-row tables from stable source CSVs")
