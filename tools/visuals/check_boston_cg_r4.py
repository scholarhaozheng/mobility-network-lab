#!/usr/bin/env python3
"""Read-only numerical and provenance checks for released Boston CG plot inputs.

No solver or private research archive is needed. Run from any working directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ASSET = Path(__file__).resolve().parents[2] / "docs/assets/boston/space_time_cg_r4"
DATA = ASSET / "data"


def table(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    v = json.loads((DATA / "validation_summary.json").read_text(encoding="utf-8"))
    phys = table("physical_link_flow_geometry.csv")
    assert len(phys) == 125 and len({r["physical_link_id"] for r in phys}) == 125
    assert len({r["from_node_id"] for r in phys} | {r["to_node_id"] for r in phys}) == 90
    assert sum(float(r["flow"]) > 1e-9 for r in phys) == v["positive_physical_links"] == 52
    assert all(r["geometry_wkt"].startswith("LINESTRING") for r in phys)

    total = table("phase_i_total.csv")
    by = table("phase_i_by_demand.csv")
    assert [int(r["round"]) for r in total] == list(range(91))
    assert abs(float(total[0]["artificial_flow"]) - 20.55361289739253) < 1e-9
    assert abs(float(total[-1]["artificial_flow"])) < 1e-9
    assert all(float(total[i+1]["artificial_flow"]) <= float(total[i]["artificial_flow"]) + 1e-8 for i in range(90))
    per_round = defaultdict(list)
    for r in by: per_round[int(r["round"])].append(float(r["artificial_flow"]))
    assert all(len(per_round[i]) == 10 and abs(sum(per_round[i]) - float(total[i]["artificial_flow"])) < 1e-7 for i in range(91))

    event = table("phase_i_round1_capacity_exchange.csv")
    assert len(event) == 8
    for arc in ("explicit_link_18164_t0", "explicit_link_18117_t4", "explicit_link_18140_t7"):
        rr = {r["state"]: r for r in event if r["arc_id"] == arc}
        assert rr["before"]["demand_ids_using_arc"] == "B10" and rr["after"]["demand_ids_using_arc"] == "B09"
        assert all(abs(float(r["capacity_consuming_flow"]) - float(r["capacity"])) < 1e-9 for r in rr.values())
    chosen = json.loads((DATA / "phase_i_round1_selected_column.json").read_text(encoding="utf-8"))
    assert chosen["selected_candidate_demand"] == "B07"
    assert "explicit_link_17946_t10" in chosen["arc_sequence"]

    p2 = table("phase_ii_objective.csv")
    assert [int(r["round"]) for r in p2] == list(range(16))
    assert abs(float(p2[0]["objective"]) - 64.82967648341466) < 1e-9
    assert abs(float(p2[-1]["objective"]) - 64.39686151152952) < 1e-9
    assert all(float(p2[i+1]["objective"]) <= float(p2[i]["objective"]) + 1e-8 for i in range(15))

    closure = table("closure_continuation.csv")
    by_demand = table("closure_by_demand.csv")
    assert [int(r["round"]) for r in closure] == list(range(6))
    assert int(closure[0]["pool_count"]) == 152 and int(closure[-1]["pool_count"]) == 167
    assert all(r["commit"] == "DEGENERATE_NONINCREASE" for r in closure[1:])
    assert all(abs(float(r["objective"]) - v["final_objective"]) < 1e-8 for r in closure)
    assert len(by_demand) == 10 and {r["demand_id"] for r in by_demand} == {f"B{i:02d}" for i in range(1,11)}
    assert all(r["closure_pass"] == "True" and float(r["min_ungenerated_reduced_cost"]) >= -float(r["tolerance"]) for r in by_demand)
    assert abs(v["final_objective"] - v["identical_graph_arc_lp_reference_objective"]) == v["absolute_objective_difference"]
    assert v["receiver_check"] == "pending" and v["r4_added_columns_final_flow"] == 0

    path = json.loads((DATA / "construction_path.json").read_text(encoding="utf-8"))
    arcs = table("construction_path_arcs.csv")
    assert path["arc_sequence"].split("|") == [r["arc_id"] for r in arcs]
    assert any(r["arc_type"] == "waiting" for r in arcs)
    assert arcs[0]["arc_type"] == "source_connector" and arcs[-1]["arc_type"] == "sink_connector"
    assert all(arcs[i]["to_node_time_id"] == arcs[i+1]["from_node_time_id"] for i in range(len(arcs)-1))

    manifest = json.loads((ASSET / "figure_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["figures"]) == 10
    for name, meta in manifest["figures"].items():
        for fmt in ("png", "svg"):
            p = ASSET / f"{name}.{fmt}"
            assert hashlib.sha256(p.read_bytes()).hexdigest() == meta[f"{fmt}_sha256"]
        for filename, digest in meta["plot_input_sha256"].items():
            assert hashlib.sha256((DATA / filename).read_bytes()).hexdigest() == digest
    print(json.dumps({"status": "PASS", "figures": len(manifest["figures"]), "physical_links": len(phys),
                      "phase_i_rounds": 90, "phase_ii_rounds": 15, "pricing_demands_pass": 10,
                      "objective_gap": v["absolute_objective_difference"], "receiver_check": "pending"}, indent=2))


if __name__ == "__main__":
    main()
