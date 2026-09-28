#!/usr/bin/env python3
"""Render matched, source-checked three-city representation figures; no solver calls."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/three_city_r1"
DATA = OUT / "data"
SLATE = "#203747"
MUTED = "#5f7180"
TEAL = "#087f83"
BLUE = "#377baa"
RUST = "#b96248"
GRAY = "#d6e0e5"

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 9,
    "axes.spines.right": False, "axes.spines.top": False, "legend.frameon": False,
    "savefig.facecolor": "white", "figure.facecolor": "white", "svg.hashsalt": "three-city-parallel-r1",
})

CASE = {
    "boston": {
        "label": "Boston", "scope": "90 physical nodes · 125 directed links · 10 OD · 3 s × 100 steps",
        "a_nodes": ["2032", "1002", "1004", "1005"], "a_links": ["18007", "18005", "17811"],
        "a_times": [0, 2, 5, 9, 10], "a_wait": "wait_1005_t9",
        "column_id": "PHASEI_R1_GEN_B07_001", "column_flow": "0.364622 model vehicles",
        "b_data": "docs/assets/boston/space_time_cg_r4/data/construction_path_arcs.csv",
        "geometry": "docs/assets/boston/space_time_cg_r4/data/physical_link_flow_geometry.csv",
        "b_ids": ["source_B07", "explicit_link_18007_t0", "explicit_link_18005_t2", "explicit_link_17811_t5",
                  "wait_1005_t9", "explicit_link_17946_t10", "explicit_link_17947_t13", "explicit_link_15592_t16", "sink_B07_1492_t19"],
        "a_source": "docs/assets/boston/space_time_cg_r4/data/construction_path.json",
        "map": "docs/assets/boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png",
        "validation": "docs/assets/boston/space_time_cg_r4/data/validation_summary.json",
        "phase_i": "docs/assets/boston/space_time_cg_r4/boston_phase_i_artificial_flow.png",
        "shared": "docs/assets/boston/space_time_cg_r4/boston_shared_capacity_event.png",
        "phase_ii": "docs/assets/boston/space_time_cg_r4/boston_phase_ii_objective.png",
        "closure": "Independent pricing closure established · 10/10 demands",
        "flow_stats": ["125 directed physical links", "52 positive-flow links", "0 material capacity violations",
                       "Link reconstruction error: not separately published"],
        "flow_unit": "modeled vehicle flow over the finite horizon",
    },
    "sioux": {
        "label": "Sioux Falls", "scope": "24 physical nodes · 64/69 selected links · 200/250 OD",
        "a_nodes": ["8", "6", "5", "9"], "a_links": ["xs_link19", "xs_link15", "local allowed arcs"],
        "a_times": [0, 1, 2, 3, 4, 5, 6], "a_wait": "wait_8_t0",
        "column_id": "GEN_XS170_001", "column_flow": "500 vehicles in saved reallocation event",
        "b_data": "docs/assets/presentation_r3/FIGURE_PROVENANCE.json",
        "b_ids": ["source_XS170", "xs_link19_t0", "xs_link15_t2", "sink_XS170_5_t6"],
        "a_source": "docs/assets/presentation_r3/FIGURE_PROVENANCE.json",
        "map": "docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png",
        "map_250": "docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png",
        "validation": "docs/datasets/sioux-200od.md",
        "validation_250": "docs/datasets/sioux-250od.md",
        "phase_i": "docs/assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png",
        "shared": "docs/assets/presentation_r5/sioux_shared_capacity_canonical.png",
        "phase_ii": "docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png",
        "closure": "Independent pricing closure not established · 200/250 OD",
        "flow_stats": ["64 / 69 selected directed links", "Positive-link count: not published",
                       "Arc-to-link mapping checked independently", "Max reconstruction difference: 5.46e−12 / 1.09e−11"],
        "flow_unit": "modeled vehicle flow over each selected horizon",
    },
    "hong_kong": {
        "label": "Hong Kong", "scope": "111 selected physical links · 10 OD · 30 s × 50 steps",
        "a_nodes": ["10468", "10513", "10526", "turn state"],
        "a_links": ["308368", "667532", "turn connector"], "a_times": [0, 1, 2, 3],
        "a_wait": "saved waiting arc",
        "column_id": "ORACLE_R1_HK10_K1", "column_flow": "0.835215083 PCE final flow",
        "b_data": "docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv",
        "geometry": "docs/assets/hong_kong/full_stack_r5/case/selected_physical_links.csv",
        "a_source": "docs/assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.source.json",
        "map": "docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png",
        "validation": "docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.source.json",
        "phase_i": "docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.png",
        "shared": None,
        "phase_ii": "docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.png",
        "closure": "Independent pricing closure established · 10/10 demands",
        "flow_stats": ["111 selected directed physical links", "69 positive-flow links",
                       "Public projection check: passed", "Exact arc-to-link error: not separately published"],
        "flow_unit": "modeled PCE flow over the finite horizon",
    },
}

FAMILY = {
    "A": "physical_to_time_expanded_graph",
    "B": "generated_column_time_indexed_path",
    "C": "time_expanded_to_physical_link_flow",
    "D": "finite_space_time_case_sequence",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_record(slug: str, letter: str, inputs: list[str], caption: str, extra: dict | None = None) -> None:
    name = f"{slug}_{FAMILY[letter]}"
    output = OUT / name
    record = {
        "figure_id": name, "scientific_status": "saved-result rendering; no solver call",
        "city": CASE[slug]["label"], "representation_family": letter,
        "input_sha256": {rel: sha(ROOT / rel) for rel in sorted(set(inputs))},
        "renderer_version": "three-city-parallel-r1",
        "renderer_sha256": sha(Path(__file__)),
        "svg_sha256": sha(output.with_suffix(".svg")), "png_sha256": sha(output.with_suffix(".png")),
        "caption": caption, "scientific_solver_rerun": False,
    }
    if extra:
        record.update(extra)
    output.with_suffix(".source.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".caption.md").write_text(caption + "\n", encoding="utf-8")


def save(fig: plt.Figure, slug: str, letter: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{slug}_{FAMILY[letter]}"
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight", metadata={"Date": None})
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight", dpi=180)
    svg = path.with_suffix(".svg")
    svg.write_text("\n".join(s.rstrip() for s in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    plt.close(fig)


def blank(ax: plt.Axes) -> None:
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)


def arrow(ax: plt.Axes, a: tuple[float, float], b: tuple[float, float], color: str, width: float = 1.7, alpha: float = 1) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=10, linewidth=width,
                                 color=color, alpha=alpha, connectionstyle="arc3"))


def draw_a(slug: str) -> None:
    c = CASE[slug]
    fig = plt.figure(figsize=(11.4, 3.45))
    grid = fig.add_gridspec(1, 3, width_ratios=[1.1, .8, 1.55], left=.045, right=.98, top=.85, bottom=.12, wspace=.12)
    p, rule, time = [fig.add_subplot(grid[i]) for i in range(3)]
    for ax in (p, rule, time): blank(ax)
    for ax, label in zip((p, rule, time), ("a  Physical subnetwork", "b  Mapping rule", "c  Local finite-graph slice")):
        ax.text(.02, 1.03, label, transform=ax.transAxes, ha="left", va="bottom", fontweight="bold", color=SLATE, fontsize=10)
    nodes = c["a_nodes"]
    xs = np.linspace(.12, .88, len(nodes))
    ys = [.56 + .13 * np.sin(i * 2.1) for i in range(len(nodes))]
    for i in range(len(nodes) - 1):
        arrow(p, (xs[i]+.035, ys[i]), (xs[i+1]-.035, ys[i+1]), TEAL, 2.2)
        if i < len(c["a_links"]): p.text((xs[i]+xs[i+1])/2, min(ys[i],ys[i+1])-.12, str(c["a_links"][i]), ha="center", fontsize=7, color=MUTED)
    p.scatter(xs, ys, s=180, facecolor="white", edgecolor=SLATE, zorder=4)
    for x,y,n in zip(xs,ys,nodes): p.text(x,y+.12, str(n), ha="center", color=SLATE, fontsize=8)
    p.text(.02,.11,"Directed physical links; IDs retained",fontsize=8,color=MUTED)
    rule.text(.06,.73,"(node, t)",fontsize=14,color=SLATE)
    rule.text(.5,.73,"→",fontsize=15,color=TEAL)
    rule.text(.06,.53,"link ℓ at t",fontsize=13,color=SLATE)
    rule.text(.5,.53,"→ movement arc",fontsize=11,color=TEAL)
    rule.text(.06,.32,"same node, t+1 → waiting",fontsize=9,color=MUTED)
    rule.text(.06,.16,"OD endpoints → source / sink",fontsize=9,color=MUTED)
    tt = c["a_times"]
    tx = np.linspace(.12,.9,len(tt))
    for x,t in zip(tx,tt):
        time.plot([x,x],[.16,.86],color=GRAY,lw=.8)
        time.text(x,.07,f"t={t}",ha="center",fontsize=8,color=MUTED)
    y0,y1=.63,.36
    time.scatter(tx,[y0]*len(tt),s=31,facecolor="white",edgecolor=MUTED,zorder=3)
    time.scatter(tx,[y1]*len(tt),s=31,facecolor="white",edgecolor=MUTED,zorder=3)
    for i in range(len(tt)-1):
        arrow(time,(tx[i]+.02,y0),(tx[i+1]-.02,y0),"#9eafb8",1.2,.8)
    if len(tt)>2:
        arrow(time,(tx[0]+.02,y0-.015),(tx[min(2,len(tt)-1)]-.02,y1+.015),TEAL,2.4)
    # Explicit demand-specific connectors in the local schematic; neither is a road.
    arrow(time,(.015,.70),(tx[0]-.02,y0+.01),RUST,1.5)
    arrow(time,(tx[-1]+.015,y1-.01),(.985,.27),RUST,1.5)
    time.text(.015,.76,"source",fontsize=7,color=RUST)
    time.text(.83,.20,"sink",fontsize=7,color=RUST)
    time.text(.04,.92,"sample movement",fontsize=8,color=TEAL)
    time.text(.04,.2,"waiting",fontsize=8,color=MUTED)
    time.text(.72,.91,"demand-specific\nconnectors",ha="left",va="top",fontsize=7,color=RUST)
    save(fig,slug,"A")
    inputs=[c["a_source"]]
    if slug=="hong_kong": inputs.append("docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/case/dynamic_arc.csv")
    source_record(slug,"A",inputs,
                  f"{c['label']}: a local, source-grounded physical-to-time construction slice. Full finite-graph size remains the case statistic; schematic coordinates are not geography. Movement, waiting and demand-specific connectors are distinct objects.",
                  {"display_coordinates":"schematic", "full_scope":c["scope"], "source_sink_note":"explicit schematic source and sink arrows are demand-specific computational connectors, not physical roads"})


def rows_b(slug: str) -> list[dict[str,str]]:
    c=CASE[slug]
    if slug=="sioux":
        return [
            {"arc_id":"source_XS170","arc_type":"source_connector","from_time":"0","to_time":"0","physical_link_id":""},
            {"arc_id":"xs_link19_t0","arc_type":"movement","from_time":"0","to_time":"2","physical_link_id":"19"},
            {"arc_id":"xs_link15_t2","arc_type":"movement","from_time":"2","to_time":"6","physical_link_id":"15"},
            {"arc_id":"sink_XS170_5_t6","arc_type":"sink_connector","from_time":"6","to_time":"6","physical_link_id":""},
        ]
    with (ROOT/c["b_data"]).open(newline="",encoding="utf-8") as handle:
        rows=list(csv.DictReader(handle))
    if slug=="boston":
        selected=[row for row in rows if row["arc_id"] in c["b_ids"]]
        if [row["arc_id"] for row in selected]!=c["b_ids"]: raise ValueError("Boston path arc order mismatch")
        return selected
    if len(rows)!=77 or rows[0]["arc_type"]!="source_connector" or rows[-1]["arc_type"]!="sink_connector":
        raise ValueError("Hong Kong selected column identity mismatch")
    return rows


def draw_b(slug: str) -> None:
    c=CASE[slug]; rows=rows_b(slug)
    movements=[r for r in rows if r["arc_type"]=="movement"]
    fig=plt.figure(figsize=(11.4,3.7))
    grid=fig.add_gridspec(1,2,width_ratios=[.9,1.1],left=.05,right=.97,top=.85,bottom=.12,wspace=.14)
    route,sequence=[fig.add_subplot(grid[i]) for i in range(2)]
    for ax in (route,sequence): blank(ax)
    route.text(.02,1.04,"a  Directed physical-route order",transform=route.transAxes,fontweight="bold",fontsize=10,color=SLATE)
    sequence.text(.02,1.04,"b  Ordered time-indexed arcs",transform=sequence.transAxes,fontweight="bold",fontsize=10,color=SLATE)
    count=len(movements)
    if c.get("geometry"):
        with (ROOT/c["geometry"]).open(newline="",encoding="utf-8") as handle:
            geo_rows=list(csv.DictReader(handle))
        id_field="physical_link_id" if slug=="boston" else "link_id"
        geom_field="geometry_wkt" if slug=="boston" else "geometry"
        geo={r[id_field]:r[geom_field] for r in geo_rows}
        def xy(wkt: str) -> tuple[list[float],list[float]]:
            body=wkt[wkt.find("(")+1:wkt.rfind(")")]
            pts=[tuple(float(n) for n in re.split(r"\s+",part.strip())[:2]) for part in body.split(",")]
            return [p[0] for p in pts],[p[1] for p in pts]
        all_x=[];all_y=[]
        for wkt in geo.values():
            x,y=xy(wkt);route.plot(x,y,color="#d7e0e4",lw=.7,zorder=1);all_x+=x;all_y+=y
        for r in movements:
            link=r["physical_link_id"]
            if link in geo:
                x,y=xy(geo[link]);route.plot(x,y,color=TEAL,lw=2.5,zorder=2)
        first=movements[0]["physical_link_id"];last=movements[-1]["physical_link_id"]
        if first in geo and last in geo:
            x0,y0=xy(geo[first]);x1,y1=xy(geo[last])
            route.scatter([x0[0],x1[-1]],[y0[0],y1[-1]],s=50,facecolor="white",edgecolor=SLATE,zorder=4)
            route.annotate("origin",(x0[0],y0[0]),xytext=(5,7),textcoords="offset points",fontsize=7,color=SLATE)
            route.annotate("destination",(x1[-1],y1[-1]),xytext=(5,7),textcoords="offset points",fontsize=7,color=SLATE)
        dx=max(all_x)-min(all_x);dy=max(all_y)-min(all_y)
        route.set_xlim(min(all_x)-.03*dx,max(all_x)+.03*dx)
        route.set_ylim(min(all_y)-.03*dy,max(all_y)+.03*dy)
        route.set_aspect("equal",adjustable="box")
    else:
        xx=np.linspace(.13,.87,count+1); yy=.52+.13*np.sin(np.linspace(0,2.8,count+1))
        route.plot(xx,yy,color=TEAL,lw=3)
        route.scatter(xx,yy,s=70,facecolor="white",edgecolor=SLATE,zorder=3)
        for i,r in enumerate(movements):
            route.text((xx[i]+xx[i+1])/2,min(yy[i],yy[i+1])-.09,r["physical_link_id"],ha="center",fontsize=8,color=TEAL)
        route.text(xx[0],yy[0]+.14,"node 8",ha="center",fontsize=8,color=SLATE)
        route.text(xx[1],yy[1]+.14,"node 6",ha="center",fontsize=8,color=SLATE)
        route.text(xx[-1],yy[-1]+.14,"node 5",ha="center",fontsize=8,color=SLATE)
    display=rows if len(rows)<=9 else [*rows[:4],{"arc_id":"… complete 77-row table linked below …","arc_type":"","from_time":"","to_time":"","physical_link_id":""},*rows[-3:]]
    top=.89; step=.087 if len(display)>8 else .11
    sequence.text(.02,.96,"arc ID",fontsize=8,fontweight="bold",color=MUTED)
    sequence.text(.59,.96,"time",fontsize=8,fontweight="bold",color=MUTED)
    sequence.text(.78,.96,"type",fontsize=8,fontweight="bold",color=MUTED)
    for i,row in enumerate(display):
        y=top-i*step
        typ=row["arc_type"]
        color=TEAL if typ=="movement" else (RUST if "connector" in typ else MUTED)
        name=row["arc_id"]
        if len(name)>31:name=name[:28]+"…"
        sequence.text(.02,y,name,fontsize=7.4,color=color)
        sequence.text(.59,y,f"{row['from_time']} → {row['to_time']}" if row["from_time"] else "",fontsize=7.4,color=MUTED)
        sequence.text(.78,y,typ.replace("_connector"," conn."),fontsize=7.2,color=color)
    save(fig,slug,"B")
    source_record(slug,"B",[c["b_data"]]+([c["geometry"]] if c.get("geometry") else []),
                  f"{c['label']}: one accepted generated column shown as physical-route order and time-indexed arc order; source/sink and any waiting/turn arcs retain their distinct types. {c['column_id']} has {c['column_flow']}. This is not a reference-LP path.",
                  {"column_id":c["column_id"],"selected_arc_count":len(rows),"movement_arc_count":count,
                   "waiting_arc_count":sum(r["arc_type"]=="waiting" for r in rows),
                   "full_sequence_source":c["b_data"]})


def show_image(ax: plt.Axes, rel: str, title: str) -> None:
    blank(ax)
    img=plt.imread(ROOT/rel)
    ax.imshow(img,extent=[0,1,.07,.93],aspect="auto")
    ax.text(.02,1.02,title,transform=ax.transAxes,fontweight="bold",fontsize=10,color=SLATE)


def draw_c(slug: str) -> None:
    c=CASE[slug]
    fig=plt.figure(figsize=(11.4,3.7))
    grid=fig.add_gridspec(1,2,width_ratios=[.73,1.27],left=.05,right=.97,top=.85,bottom=.1,wspace=.12)
    audit,map_ax=[fig.add_subplot(grid[i]) for i in range(2)]
    blank(audit)
    audit.text(.02,1.04,"a  Aggregation and audit",transform=audit.transAxes,fontweight="bold",fontsize=10,color=SLATE)
    audit.text(.02,.86,"fℓ = Σ xₐ",fontsize=20,color=SLATE,fontweight="bold")
    audit.text(.02,.75,"movement arc a maps to physical link ℓ",fontsize=8.5,color=MUTED)
    for i,line in enumerate(c["flow_stats"]):
        audit.text(.02,.58-i*.125,"•  "+line,fontsize=9,color=SLATE)
    audit.text(.02,.035,c["flow_unit"],fontsize=8,color=MUTED)
    if slug=="sioux":
        blank(map_ax)
        img1=plt.imread(ROOT/c["map"]); img2=plt.imread(ROOT/c["map_250"])
        map_ax.imshow(img1,extent=[0,.49,.15,.88],aspect="auto")
        map_ax.imshow(img2,extent=[.51,1,.15,.88],aspect="auto")
        map_ax.text(.02,1.04,"b  200 OD",transform=map_ax.transAxes,fontweight="bold",fontsize=10,color=SLATE)
        map_ax.text(.52,1.04,"c  250 OD",transform=map_ax.transAxes,fontweight="bold",fontsize=10,color=SLATE)
    else:
        show_image(map_ax,c["map"],"b  Final directed physical-link movement flow")
    save(fig,slug,"C")
    inputs=[c["map"],c["validation"]]
    if slug=="sioux":inputs += [c["map_250"],c["validation_250"]]
    source_record(slug,"C",inputs,
                  f"{c['label']}: accepted final movement-arc flow aggregated to persistent directed physical-link IDs. The figure shows {c['flow_unit']}; nonphysical connectors are excluded. Unpublished audit quantities are labeled as such, not set to zero.",
                  {"flow_statistics":c["flow_stats"],"map_mode":"accepted saved-result image embedded in same-format evidence plate"})


def draw_d(slug: str) -> None:
    c=CASE[slug]
    fig,axes=plt.subplots(3,2,figsize=(11.4,7.8))
    fig.subplots_adjust(left=.045,right=.985,top=.93,bottom=.08,hspace=.29,wspace=.14)
    panels=[
        ("a  Physical network → finite graph",f"docs/assets/three_city_r1/{slug}_{FAMILY['A']}.png"),
        ("b  One generated column",f"docs/assets/three_city_r1/{slug}_{FAMILY['B']}.png"),
        ("c  Phase-I feasibility restoration",c["phase_i"]),
        ("d  Shared-capacity coupling",c["shared"]),
        ("e  Phase-II objective / reference",c["phase_ii"]),
        ("f  Back-projection and closure",f"docs/assets/three_city_r1/{slug}_{FAMILY['C']}.png"),
    ]
    for ax,(title,rel) in zip(axes.flat,panels):
        blank(ax)
        ax.text(.01,1.01,title,transform=ax.transAxes,fontweight="bold",fontsize=9,color=SLATE)
        if rel:
            ax.imshow(plt.imread(ROOT/rel),extent=[0,1,0,1],aspect="auto")
        else:
            ax.text(.5,.55,"Not demonstrated",ha="center",va="center",fontsize=14,color=MUTED)
            ax.text(.5,.40,"No accepted record-level cross-OD event released",ha="center",fontsize=8,color=MUTED)
    axes[2,1].text(.5,-.13,c["closure"],transform=axes[2,1].transAxes,ha="center",fontsize=8,color=TEAL if "established ·" in c["closure"] else MUTED)
    save(fig,slug,"D")
    inputs=[rel for _,rel in panels if rel]
    source_record(slug,"D",inputs,
                  f"{c['label']}: same-format six-panel sequence separates graph construction, one actual generated column, Phase-I artificial flow, shared-capacity status, Phase-II reference-objective evidence, and final-flow back-projection with truthful closure status.",
                  {"panel_order":[title for title,_ in panels],"independent_pricing_status":c["closure"],
                   "shared_capacity_status":"Not demonstrated" if not c["shared"] else "Saved event"})


def main() -> None:
    for slug in CASE:
        draw_a(slug); draw_b(slug); draw_c(slug); draw_d(slug)
    print("Rendered 12 same-format SVG/PNG figure pairs from accepted saved evidence")


if __name__=="__main__":
    main()
