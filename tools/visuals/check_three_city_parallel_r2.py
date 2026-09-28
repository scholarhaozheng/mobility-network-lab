#!/usr/bin/env python3
"""No-solve R2 checks for visible evidence, source-matched figures and scope gates."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "docs/assets/three_city_r2"
ERRORS: list[str] = []
CHECKS = 0


def check(ok, message):
    global CHECKS
    CHECKS += 1
    if not ok:
        ERRORS.append(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def section(text, heading):
    pat = re.compile(rf"(?m)^## {re.escape(heading)}\s*$")
    m = pat.search(text)
    if m is None:
        return ""
    n = re.search(r"(?m)^## ", text[m.end():])
    return text[m.end():m.end() + n.start() if n else len(text)]


finite_headings = [
    "Case role, scope, and model statistics",
    "From the physical network to the finite time-expanded graph",
    "A generated column as a time-indexed path",
    "Phase I restores feasibility",
    "Shared capacity couples different OD demands",
    "Phase II improves the real-path objective",
    "From time-expanded flows back to final physical-link movement flow",
    "Reference-objective agreement",
    "Independent pricing closure",
    "Reproduction, evidence boundary, and limits",
]
landing_headings = [
    "Role in the repository", "Scope and statistics", "GMNS, zones, and source evidence",
    "Demand, transit, and observations", "Static assignment", "Finite time-expanded algorithms",
    "Independent verification", "City-specific evidence and limits", "Reproduction",
]
readme = read("README.md")
check("<details>" not in readme, "README still closes primary evidence")
for phrase in ("GMNS is the common object contract", "Population, Households & Activity Preparation",
               "Four stages, with explicit inputs and outputs", "GPS and service evidence",
               "Static, fixed-demand", "Finite space–time, fixed-cost", "python -B tools/mcl_results.py",
               "FW scale ladder", "official TAPLab registered-adapter", "task-local TAPLab-compatible",
               "ADMM R2", "Lagrangian", "Independent pricing closure"):
    check(phrase.lower() in readme.lower(), f"README missing visible requirement: {phrase}")
check("static assignment → finite time-expanded graph" not in readme,
      "README still describes a serial static-to-finite model pipeline")
orders = [readme.find(f"## 0{i} /") for i in range(1, 8)]
check(all(p >= 0 for p in orders) and orders == sorted(orders), "README architecture is not 01→07")
for city, landing, finite in (
    ("boston", "boston.md", "boston-space-time.md"),
    ("sioux", "sioux-falls.md", "sioux-space-time.md"),
    ("hong_kong", "hong-kong.md", "hong-kong-space-time.md"),
):
    case = read(f"docs/cases/{landing}")
    page = read(f"docs/cases/{finite}")
    for name, txt in ((landing, case), (finite, page)):
        check("<details>" not in txt, f"{name}: primary evidence is closed")
    for name, txt, headings in ((landing, case, landing_headings), (finite, page, finite_headings)):
        at = [txt.find("## " + h) for h in headings]
        check(all(p >= 0 for p in at) and at == sorted(at), f"{name}: common headings missing/out of order")
    check("|" in section(case,"Scope and statistics"), f"{landing}: scope table not visible in scope section")
    for family, heading in (
        ("physical_to_time_expanded_graph", finite_headings[1]),
        ("generated_column_time_indexed_path", finite_headings[2]),
        ("time_expanded_to_physical_link_flow", finite_headings[6]),
    ):
        filename=f"{city}_{family}.png"
        check(filename in section(page,heading), f"{finite}: {filename} not under matching heading")
        check(filename in readme, f"README lacks three-city representation family: {filename}")
    check(f"{city}_finite_space_time_case_sequence.png" in section(page,finite_headings[0]),
          f"{finite}: re-rendered sequence absent from scope section")
    for needle, heading in (
        ("phase_i", finite_headings[3]), ("phase_ii", finite_headings[5]),
        ("final_physical_link", finite_headings[6]),
    ):
        content=section(page,heading).lower()
        aliases=(needle,"phase2") if needle=="phase_ii" else (needle,)
        check(any(alias in content for alias in aliases), f"{finite}: saved {needle} evidence not visible under its heading")
    check(len(section(page,finite_headings[9])) > 400, f"{finite}: reproduction details not moved")

# The original singular scientific figures remain linked, excluding only the
# superseded R1 A schematic with invented adjacency.
for filename, tokens in {
    "boston-space-time.md": ("boston_phase_i_artificial_flow.png", "boston_phase_i_od_clearance.png",
                             "boston_shared_capacity_event.png", "boston_phase_ii_objective.png",
                             "boston_pricing_closure_continuation.png", "boston_pricing_closure_by_demand.png"),
    "sioux-space-time.md": ("sioux_falls_200od_phase_i_academic.png", "sioux_falls_250od_phase_i_academic.png",
                            "sioux_shared_capacity_canonical.png", "sioux_200od_phase2_objective_trace.png",
                            "sioux_250od_phase2_objective_trace.png", "od_level_phase_i_clearance.png"),
    "hong-kong-space-time.md": ("hk_cg_phase_i_artificial_flow.png", "hk_cg_phase_i_by_demand.png",
                                "hk_cg_phase_ii_objective.png", "hk_cg_pricing_closure.png",
                                "hk_cg_final_physical_link_movement_flow.png"),
}.items():
    page=read("docs/cases/" + filename)
    for token in tokens:
        check(token in page, f"{filename}: accepted scientific figure de-linked: {token}")

expected_source_hash = {
    "boston":"66fbcd70d53fc18c483a11250cdc3a827e9c1b04f5c1e21a5e8453a6f4a9b672",
    "sioux":"788410034bd123069f6703cba0627e8177623f4ddc1b153f666b9d1af65bd97a",
    "hong_kong":"49fe5250cdbef0297f2829e9443c4be01adc5342e81f72b63211c1a62f6cae28",
}
hk_source=ROOT/"docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/case/dynamic_arc.csv"
check(sha(hk_source)==expected_source_hash["hong_kong"], "Hong Kong frozen dynamic-arc SHA changed")
hk_rows={r["arc_id"]:r for r in rows(hk_source)}
b_pub={r["arc_id"]:r for r in rows(ROOT/"docs/assets/boston/space_time_cg_r4/data/construction_path_arcs.csv")}
s_prov=json.loads(read("docs/assets/presentation_r3/FIGURE_PROVENANCE.json"))
s_allowed=set(s_prov["selected_path"]) | set(s_prov["allowed_displayed_arcs"])
renderer=ROOT/"tools/visuals/render_three_city_parallel_r2.py"
code=renderer.read_text(encoding="utf-8")
check('aspect="auto"' not in code and 'aspect="equal"' in code and "extent=" not in code,
      "R2 renderer risks anisotropic map stretching")
for city in expected_source_hash:
    edges=rows(ASSET/"data"/f"{city}_construction_edges.csv")
    edge_map={r["arc_id"]:r for r in edges}
    check(len(edges)==len(edge_map) and len(edges)>=8, f"{city}: duplicate/too few source arcs")
    check({r["evidence_record_sha256"] for r in edges}=={expected_source_hash[city]},
          f"{city}: accepted source dynamic-arc hash changed")
    for r in edges:
        check(r["from_node_time_id"] and r["to_node_time_id"] and r["from_time"] and r["to_time"] and r["arc_type"],
              f"{city}: incomplete literal arc row {r['arc_id']}")
        check(r["arc_type"]=="movement" or not r["physical_link_id"],
              f"{city}: nonphysical arc misidentified as a physical road {r['arc_id']}")
        if city=="hong_kong":
            saved=hk_rows.get(r["arc_id"])
            check(saved is not None, f"HK cutaway arc absent from frozen graph {r['arc_id']}")
        elif city=="boston":saved=b_pub.get(r["arc_id"])
        else:
            check(r["arc_id"] in s_allowed, f"Sioux arc outside accepted displayed source set {r['arc_id']}")
            saved=None
        if saved:
            for key in ("arc_type","from_node_time_id","to_node_time_id","from_time","to_time","physical_link_id"):
                check(r[key]==saved[key], f"{city}: accepted source row mismatch {r['arc_id']}:{key}")
    for family in ("A","B","C","D"):
        stem={"A":"physical_to_time_expanded_graph","B":"generated_column_time_indexed_path",
              "C":"time_expanded_to_physical_link_flow","D":"finite_space_time_case_sequence"}[family]
        base=ASSET/f"{city}_{stem}"
        side=json.loads(base.with_suffix(".source.json").read_text(encoding="utf-8"))
        check(side["representation_family"]==family, f"{city} {family}: wrong family")
        check(side["renderer_sha256"]==sha(renderer), f"{city} {family}: stale renderer hash")
        check(side["png_sha256"]==sha(base.with_suffix(".png")), f"{city} {family}: stale PNG hash")
        check(side["svg_sha256"]==sha(base.with_suffix(".svg")), f"{city} {family}: stale SVG hash")
        for rel,digest in side["input_sha256"].items():
            check((ROOT/rel).is_file() and sha(ROOT/rel)==digest, f"{city} {family}: input hash mismatch {rel}")
        if family=="A":
            check(set(side["plotted_arc_ids"]).issubset(edge_map), f"{city}: plotted A edge outside saved table")
            check(len(side["time_layers"])>=4, f"{city}: fewer than four explicit A time layers")
        if family=="B":
            check(side.get("time_unit"), f"{city}: B time-step unit missing")
            check("sink" in side.get("sink_bookkeeping_note","").lower(), f"{city}: B sink bookkeeping not explained")
        if family=="C":
            fields=side.get("audit_fields",{})
            check(set(fields)=={"Physical links","Positive-flow links","Mapping failures","Reconstruction residual","Flow units"},
                  f"{city}: C audit fields not identical")
            check("native" in side.get("image_aspect_policy",""), f"{city}: C aspect policy absent")

cross=rows(ASSET/"data/hong_kong_physical_to_routing_crosswalk.csv")
check(len(cross)==2 and all(r["original_from_node_id"]!=r["routing_entry_node_id"] for r in cross),
      "HK physical roads and routing states collapsed")
disclosure=json.loads((ASSET/"DISCLOSURE_STATUS_R2.json").read_text(encoding="utf-8"))
check(disclosure["owner_artifact_level_publication_approval"]=="PENDING", "HK new path disclosure silently approved")
check(disclosure["identity_and_final_flow_local_verification"]["final_positive_flow_pce"]==0.8352150831808043,
      "HK final positive-flow identity missing")
for rel in disclosure["pending_paths"]:
    check((ROOT/rel).is_file(), f"HK pending publication path not tracked: {rel}")

for name,required in (
    ("GMNS_READABLE.md",("physical", "Observation evidence", "Sioux Falls")),
    ("STATIC_READABLE.md",("Algorithm B route", "Boston B1", "Sioux Falls")),
    ("FINITE_READABLE.md",("Sioux · 200 OD", "Sioux · 250 OD", "One model time step", "Number of model steps", "Elapsed model horizon")),
):
    md=(ROOT/"docs/data/three_city_r2"/name).read_text(encoding="utf-8")
    for item in required:check(item.lower() in md.lower(), f"{name}: missing readable scope {item}")
    check("physical_subnetwork_nodes_links" not in md, f"{name}: raw snake_case table still shown")

result={"status":"PASS" if not ERRORS else "FAIL","checks":CHECKS,"errors":ERRORS,
        "publication_status":"READY_FOR_REVIEW; Hong Kong new path disclosure PENDING",
        "scientific_solver_rerun":False}
print(json.dumps(result,indent=2,ensure_ascii=False))
raise SystemExit(0 if not ERRORS else 1)
