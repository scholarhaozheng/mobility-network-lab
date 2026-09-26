#!/usr/bin/env python3
"""Render the accepted, bounded Boston CG figures from published plot inputs only.

This script does not call an optimizer or inspect private research directories.
Run: python -B tools/visuals/render_boston_cg_r4.py
Or regenerate only a terminology-inconsistent Phase-II panel with --only phase-ii.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import numpy as np
from shapely import wkt

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "docs/assets/boston/space_time_cg_r4"
DATA = ASSET / "data"
NAVY = "#173247"
TEAL = "#087f8c"
MINT = "#4cb8a9"
CORAL = "#d35d47"
AMBER = "#d59833"
SLATE = "#637c8d"
PALE = "#e8eff2"
BG = "#fbfcfd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelcolor": NAVY, "text.color": NAVY,
                     "xtick.color": SLATE, "ytick.color": SLATE,
                     "axes.edgecolor": "#c8d5dc", "grid.color": "#dce6ea",
                     "svg.fonttype": "none", "savefig.facecolor": "white"})


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def j(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


manifest = {}


def save(fig, name, title, alt, caption, inputs):
    fig.savefig(ASSET / f"{name}.png", dpi=180, bbox_inches="tight", pad_inches=.18)
    fig.savefig(ASSET / f"{name}.svg", bbox_inches="tight", pad_inches=.18)
    plt.close(fig)
    manifest[name] = {"title": title, "alt": alt, "caption": caption,
                      "plot_inputs": inputs,
                      "png_sha256": hashlib.sha256((ASSET / f"{name}.png").read_bytes()).hexdigest(),
                      "svg_sha256": hashlib.sha256((ASSET / f"{name}.svg").read_bytes()).hexdigest()}


def head(fig, title, subtitle):
    fig.text(.055, .965, title, fontsize=18, fontweight="bold", color=NAVY, va="top")
    fig.text(.055, .91, subtitle, fontsize=9.5, color=SLATE, va="top")


def flow_map(ax, labels=True):
    rr = rows("physical_link_flow_geometry.csv")
    segs, vals = [], []
    for x in rr:
        geom = wkt.loads(x["geometry_wkt"])
        xy = np.asarray(geom.coords)
        segs.append(xy)
        vals.append(float(x["flow"]))
    ax.add_collection(LineCollection(segs, colors="#d5e0e5", linewidths=1.7, zorder=1))
    positive = [(s, v) for s, v in zip(segs, vals) if v > 1e-9]
    lc = LineCollection([s for s, _ in positive], cmap="YlGnBu", norm=Normalize(0, max(vals)),
                        linewidths=[1.7 + 3.8 * v / max(vals) for _, v in positive], zorder=2)
    lc.set_array(np.asarray([v for _, v in positive]))
    ax.add_collection(lc)
    ax.autoscale()
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    if labels:
        ax.text(.02, .02, f"52 / 125 directed links carry positive final flow", transform=ax.transAxes,
                color=NAVY, fontsize=9, bbox={"facecolor": "white", "edgecolor": "none", "alpha": .86})
    return lc


def figure_a():
    fig, ax = plt.subplots(figsize=(9.5, 6.3)); fig.patch.set_facecolor(BG)
    head(fig, "Boston | final physical-link movement flow", "Accepted bounded pilot · 90 nodes · 125 directed links · 10 ODs · 3 s/step · 100-step horizon")
    fig.subplots_adjust(top=.84, bottom=.12, left=.08, right=.88)
    lc = flow_map(ax)
    cb = fig.colorbar(lc, ax=ax, fraction=.034, pad=.025); cb.set_label("Final path-flow projection (pilot units)")
    fig.text(.06, .035, "R3→R4: physical-link flows unchanged within numerical precision; not citywide Boston traffic.", fontsize=9, color=SLATE)
    save(fig, "boston_cg_final_physical_link_flow", "Final physical-link flow",
         "Bounded Boston pilot street map: 52 of 125 directed physical links have positive final CG flow; pale links have zero flow.",
         "R3 accepted final-column flow joined on physical_link_id to accepted GMNS Plus 21_Boston geometry. R4 adds zero-final-flow certificate columns and leaves final physical-link movement flow unchanged within numerical precision; this is not a citywide traffic map.",
         ["physical_link_flow_geometry.csv", "validation_summary.json"])


def figure_b():
    arcs = rows("construction_path_arcs.csv"); path = j("construction_path.json")
    fig = plt.figure(figsize=(12.2, 6.6)); fig.patch.set_facecolor(BG)
    head(fig, "Boston | physical path → time-indexed column", "Actual final B07 column PHASEI_R1_GEN_B07_001 · flow 0.364622 · local slice of 9,110-node / 22,217-arc DAG")
    ax0 = fig.add_axes([.055, .20, .36, .60]); ax1 = fig.add_axes([.49, .20, .46, .60])
    flow = {x["physical_link_id"]: wkt.loads(x["geometry_wkt"]) for x in rows("physical_link_flow_geometry.csv")}
    ids = [x["physical_link_id"] for x in arcs if x["arc_type"] == "movement"]
    for k in ids:
        xy = np.asarray(flow[k].coords); ax0.plot(xy[:,0], xy[:,1], color=TEAL, lw=3.3)
        m = xy[len(xy)//2]; ax0.text(m[0], m[1], k, fontsize=7.5, color=NAVY)
    ax0.autoscale(); ax0.set_aspect("equal", adjustable="datalim"); ax0.axis("off")
    ax0.set_title("Physical movement sequence", loc="left", fontsize=12, fontweight="bold")
    pnodes = list(dict.fromkeys([x["from_physical_node_id"] for x in arcs if x["arc_type"] in ("movement", "waiting")] + ["1492"]))
    y = {n: len(pnodes)-i for i,n in enumerate(pnodes)}
    for n,v in y.items():
        ax1.axhline(v, color="#dce6ea", lw=.8, zorder=0)
        ax1.text(-.5, v, n, ha="right", va="center", fontsize=8, color=SLATE)
    for x in arcs:
        typ = x["arc_type"]
        if typ == "source_connector":
            ax1.annotate("source B07", xy=(0,y["2032"]), xytext=(0,y["2032"]+1.3),
                         arrowprops={"arrowstyle":"->","color":AMBER}, color=AMBER, ha="center", fontsize=8)
        elif typ == "sink_connector":
            ax1.annotate("sink B07 (t100)", xy=(19,y["1492"]), xytext=(14,y["1492"]-1.2),
                         arrowprops={"arrowstyle":"->","color":CORAL}, color=CORAL, fontsize=8)
        else:
            a=(float(x["from_time"]),y[x["from_physical_node_id"]]); b=(float(x["to_time"]),y[x["to_physical_node_id"]])
            color = AMBER if typ == "waiting" else TEAL
            ax1.annotate("", xy=b, xytext=a, arrowprops={"arrowstyle":"-|>","color":color,"lw":2.5})
            if typ == "waiting": ax1.text(9.1,y["1005"]+.32,"wait 1005 · t9→10",fontsize=8,color=AMBER)
    ax1.set_xlim(-1.5,21.5); ax1.set_ylim(-1, len(pnodes)+2); ax1.set_xlabel("time step (3 seconds each)")
    ax1.set_yticks([]); ax1.grid(axis="x", alpha=.7); ax1.set_title("Actual dynamic arc sequence", loc="left", fontsize=12, fontweight="bold")
    fig.text(.06,.055,"Movement = teal   •   waiting = amber   •   source / sink = labeled connectors. Sink time t100 is annotated, not drawn to x-scale.",fontsize=8.6,color=SLATE)
    save(fig,"boston_space_time_construction","Physical-to-space–time construction",
         "Actual B07 final path: physical link sequence on the left and movement, wait at node 1005, source, and sink dynamic arcs on the right.",
         "Local cutaway of accepted path PHASEI_R1_GEN_B07_001, positive final flow 0.364622. Every displayed physical node/link and time index comes from the saved R4 pool and R3 dynamic records; this is not the complete 9,110-node/22,217-arc network.",
         ["construction_path.json","construction_path_arcs.csv","construction_path_nodes.csv","physical_link_flow_geometry.csv"])


def figure_c():
    r=rows("phase_i_total.csv"); x=np.array([int(z["round"]) for z in r]); y=np.array([float(z["artificial_flow"]) for z in r])
    fig,ax=plt.subplots(figsize=(9.5,5.2)); fig.patch.set_facecolor(BG)
    head(fig,"Boston | Phase I feasibility restoration","Actual accepted 90-round trace · artificial flow, not physical link flow")
    fig.subplots_adjust(top=.80,bottom=.18,left=.10,right=.95)
    ax.step(x,y,where="post",color=TEAL,lw=2.5); ax.scatter([0,90],[y[0],y[-1]],color=[CORAL,TEAL],zorder=4)
    ax.annotate(f"{y[0]:.6f} at start",(0,y[0]),xytext=(8,-24),textcoords="offset points",color=CORAL)
    ax.annotate("zero at round 90",(90,0),xytext=(-116,19),textcoords="offset points",color=TEAL,
                arrowprops={"arrowstyle":"->","color":TEAL})
    ax.set(xlim=(0,91),ylim=(-.5,max(y)*1.13),xlabel="Phase-I round",ylabel="Total artificial flow")
    ax.grid(axis="y",alpha=.75)
    save(fig,"boston_phase_i_artificial_flow","Phase-I total artificial flow",
         "Step trace of total artificial flow falling from 20.553613 to zero by round 90, using every saved round value without smoothing.",
         "The accepted Phase-I enriched trace records 20.5536128974 at round 0 and zero at round 90. The step curve shows all saved values, without interpolation or smoothing.",
         ["phase_i_total.csv"])


def figure_d():
    r=rows("phase_i_by_demand.csv"); ods=sorted({z["demand_id"] for z in r}); a=np.zeros((len(ods),91))
    for z in r:a[ods.index(z["demand_id"]),int(z["round"])]=float(z["artificial_flow"])
    fig,ax=plt.subplots(figsize=(11,5.5)); fig.patch.set_facecolor(BG)
    head(fig,"Boston | OD-level Phase-I clearance","B01–B10 · actual per-demand artificial flow across 90 rounds")
    fig.subplots_adjust(top=.80,bottom=.19,left=.11,right=.92)
    im=ax.imshow(a,aspect="auto",origin="upper",interpolation="nearest",cmap="YlGnBu",extent=(-.5,90.5,9.5,-.5))
    ax.set_yticks(range(10),ods);ax.set_xlabel("Phase-I round");ax.set_xticks([0,15,30,45,60,75,90]);
    cb=fig.colorbar(im,ax=ax,fraction=.03,pad=.02);cb.set_label("Artificial flow")
    fig.text(.10,.045,"Rows can darken temporarily even while the total declines: feasibility restoration is coupled across ODs.",fontsize=9,color=SLATE)
    save(fig,"boston_phase_i_od_clearance","OD-level Phase-I clearance",
         "Heatmap of B01 through B10 artificial flow by Phase-I round, including temporary increases for individual demands.",
         "Each cell is a saved per-demand artificial-flow value. Temporary rises in an OD row are permitted even as the total declines; the event panel shows one recorded cross-OD exchange.",
         ["phase_i_by_demand.csv","phase_i_total.csv"])


def figure_e():
    r=rows("phase_i_round1_capacity_exchange.csv"); chosen=j("phase_i_round1_selected_column.json")
    by={(z["arc_id"],z["state"]):z for z in r}
    ids=["explicit_link_18164_t0","explicit_link_18117_t4","explicit_link_18140_t7","explicit_link_17946_t10"]
    fig=plt.figure(figsize=(12,6.5));fig.patch.set_facecolor(BG)
    head(fig,"Boston | a recorded shared-capacity exchange","Phase-I round 1 · selected new B07 column PHASEI_R1_GEN_B07_001 · before/after LP optima")
    ax=fig.add_axes([.07,.26,.56,.53]); ay=fig.add_axes([.70,.26,.25,.53])
    for i,arc in enumerate(ids):
        before=by[(arc,"before")];after=by[(arc,"after")]; cap=float(after["capacity"])
        yy=3-i
        ax.barh(yy+.18,float(before["capacity_consuming_flow"]),height=.31,color=SLATE,label="before" if i==0 else None)
        ax.barh(yy-.18,float(after["capacity_consuming_flow"]),height=.31,color=TEAL,label="after" if i==0 else None)
        ax.plot([cap,cap],[yy-.42,yy+.42],color=CORAL,lw=1.6)
        ax.text(cap+.035,yy+.18,(before["demand_ids_using_arc"] or "—")+" → "+(after["demand_ids_using_arc"] or "—"),fontsize=8,va="center")
    ax.set_yticks(range(4),["17946 t10 · selected B07 path","18140 t7 · shared","18117 t4 · shared","18164 t0 · shared"])
    ax.set_xlim(0,1.85);ax.set_xlabel("Dynamic-arc capacity-consuming flow (red tick = capacity 1.0833)")
    ax.legend(loc="lower right",frameon=False,ncol=2);ax.grid(axis="x",alpha=.5)
    od={z["demand_id"]:z for z in rows("phase_i_round1_od_change.csv")}
    for yy,k in zip([2,1,0],["B07","B09","B10"]):
        v=float(od[k]["delta"]);ay.barh(yy,v,color=TEAL if v<0 else CORAL,height=.53)
        ay.text(v+(.03 if v>=0 else -.03),yy,f"{v:+.3f}",ha="left" if v>=0 else "right",va="center",fontsize=9)
    ay.axvline(0,color=NAVY,lw=.8);ay.set_yticks([2,1,0],["B07","B09","B10"]);ay.set_xlim(-1.45,1.45)
    ay.set_xlabel("Change in artificial flow");ay.set_title("Cross-OD reallocation",fontsize=10,fontweight="bold")
    fig.text(.07,.18,"The three shared arcs stay full (1.0833 / 1.0833), while their recorded user changes B10 → B09. B07's selected-path arc fills from 0.",fontsize=9,color=NAVY)
    fig.text(.07,.135,"Raw SciPy/HiGHS capacity marginals: 18140 t7 −1.000 → −0.000; 18164 t0 −0.000 → −1.000. Original sign retained.",fontsize=8.8,color=SLATE)
    fig.text(.07,.09,"These before/after optimal solutions do not prove the B07 column was uniquely necessary for the reallocation.",fontsize=8.7,color=CORAL)
    save(fig,"boston_shared_capacity_event","Shared-capacity and cross-OD event",
         "Phase-I round-one before/after comparison: three full dynamic arcs switch use from B10 to B09; B07's new path fills a different arc; B07/B09 artificial flow falls while B10 rises.",
         "Accepted round-1 before/after capacity-usage and dual records. Full arcs 18164 t0, 18117 t4 and 18140 t7 switch recorded user B10→B09 without changing total arc load. B07's selected path fills 17946 t10. The solver's raw HiGHS marginal sign is retained. These LP snapshots establish an exchange, not unique necessity of the selected column.",
         ["phase_i_round1_capacity_exchange.csv","phase_i_round1_od_change.csv","phase_i_round1_selected_column.json"])


def figure_f():
    r=rows("phase_ii_objective.csv");v=j("validation_summary.json");x=np.array([int(z["round"]) for z in r]);y=np.array([float(z["objective"]) for z in r])
    fig,ax=plt.subplots(figsize=(9.5,5.2));fig.patch.set_facecolor(BG)
    head(fig,"Boston | Phase II objective and arc-flow LP reference","Reference on the same finite time-expanded graph · not the static FW/Beckmann objective")
    fig.subplots_adjust(top=.80,bottom=.18,left=.12,right=.95)
    ax.plot(x,y,color=TEAL,lw=2.2,zorder=2)
    for typ,color,mark in [("STRICT_OBJECTIVE_IMPROVEMENT",TEAL,"o"),("DEGENERATE_NONINCREASE",AMBER,"s")]:
        q=[z for z in r if z["commit_classification"]==typ]
        ax.scatter([int(z["round"]) for z in q],[float(z["objective"]) for z in q],c=color,marker=mark,s=42,label=typ.replace("_"," ").title(),zorder=3)
    ref=v["identical_graph_arc_lp_reference_objective"]
    ax.axhline(ref,color=CORAL,ls="--",lw=1.4,label="Arc-flow LP reference")
    ax.annotate("round 15 · reference-level match",(15,y[-1]),xytext=(6,28),textcoords="offset points",color=NAVY,
                arrowprops={"arrowstyle":"->","color":NAVY})
    ax.set(xlim=(-.2,15.8),xlabel="Phase-II round",ylabel="Restricted-master objective")
    ax.grid(axis="y",alpha=.65);ax.legend(frameon=False,fontsize=8,loc="upper right")
    save(fig,"boston_phase_ii_objective","Phase-II objective and reference",
         "Saved Boston Phase-II objective falls from 64.829676 to 64.396862 over 15 rounds; strict and degenerate commits have different markers, with the arc-flow LP reference line for the same finite time-expanded graph.",
         "Accepted R3 Phase-II round log. Round 15 establishes reference-objective agreement with the arc-flow LP on the same finite time-expanded graph. Square markers are degenerate nonincreasing commits, distinct from strict improvement. The R4 continuation later establishes independent pricing closure without changing the final objective.",
         ["phase_ii_objective.csv","validation_summary.json"])


def figure_g():
    v=j("validation_summary.json");fig=plt.figure(figsize=(10.7,5.8));fig.patch.set_facecolor(BG)
    head(fig,"Boston | final validation and reference check","One accepted bounded pilot · R3 objective match plus R4 independent full-DAG pricing closure")
    groups=[("Phase I",[("Zero round","90"),("Real columns added","90")]),
            ("Phase II",[("Rounds","15"),("Columns added","52"),("R3 pool","152")]),
            ("R4 closure",[("Continuation rounds","5"),("Certificate columns","15, all zero final flow"),("Final pool","167")]),
            ("Independent checks",[("Objective",f'{v["final_objective"]:.14f}'),
                                    ("Arc-LP reference",f'{v["identical_graph_arc_lp_reference_objective"]:.14f}'),
                                    ("Absolute gap",f'{v["absolute_objective_difference"]:.2e}'),
                                    ("Max demand residual",f'{v["max_demand_residual"]:.2e}'),
                                    ("Capacity violations","0"),("Full-DAG pricing", "10/10 pass at 1e−6"),
                                    ("Second machine","pending")])]
    axes=[fig.add_axes([.055,.54,.41,.29]),fig.add_axes([.53,.54,.41,.29]),
          fig.add_axes([.055,.13,.41,.31]),fig.add_axes([.53,.13,.41,.31])]
    for ax,(label,items) in zip(axes,groups):
        ax.set_facecolor("#eef5f6");ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values():spine.set_visible(False)
        ax.text(.045,.90,label,fontweight="bold",fontsize=12,color=TEAL,transform=ax.transAxes,va="top")
        n=len(items)
        for i,(k,value) in enumerate(items):
            yy=.72-i*(.67/max(n-1,1));ax.text(.05,yy,k,fontsize=8.5,transform=ax.transAxes,va="center")
            ax.text(.95,yy,value,fontsize=8.5,fontweight="bold",ha="right",transform=ax.transAxes,va="center")
    save(fig,"boston_cg_validation","Boston CG validation panel",
         "Four-panel numerical summary of Phase I, Phase II, R4 closure and independent checks; reference gap is about 5.68e-14; second-machine check pending.",
         "Saved R2/R3/R4 accepted checks on one 90-node/125-link/10-OD graph. R4 adds 15 zero-final-flow certificate columns, yields 167 columns and passes independent full-DAG pricing for all ten demands at 1e-6. Same-graph arc-flow objective agrees to numerical precision; second-machine receiver verification remains pending.",
         ["validation_summary.json"])


def figure_i():
    r=rows("closure_continuation.csv");x=np.array([int(z["round"]) for z in r]);pool=np.array([int(z["pool_count"]) for z in r]);rc=np.array([float(z["min_ungenerated_reduced_cost"]) if z["min_ungenerated_reduced_cost"] else np.nan for z in r]);
    fig,(a,b)=plt.subplots(1,2,figsize=(11,4.9));fig.patch.set_facecolor(BG)
    head(fig,"Boston | R4 closure continuation","Five degenerate nonincreasing rounds add certificate columns, not newly used physical routes")
    fig.subplots_adjust(top=.75,bottom=.20,left=.09,right=.95,wspace=.28)
    a.step(x,pool,where="post",color=TEAL,lw=2.4);a.scatter(x,pool,color=TEAL,s=27)
    a.set(xlim=(-.2,5.3),ylim=(149,170),xlabel="Continuation round",ylabel="Restricted-master pool size");a.grid(axis="y",alpha=.6)
    a.annotate("152 → 167",(5,167),xytext=(-80,-24),textcoords="offset points",color=NAVY)
    b.plot(x[1:],rc[1:],marker="o",color=CORAL,lw=2.2);b.axhline(-1e-6,color=AMBER,ls="--",label="−1e−6 threshold")
    b.set(xlim=(.8,5.3),xlabel="Continuation round",ylabel="Min ungenerated reduced cost");b.grid(axis="y",alpha=.6);b.legend(frameon=False,fontsize=8)
    fig.text(.09,.055,"Objective remains 64.39686151152954 (within numerical precision). Every continuation commit: DEGENERATE_NONINCREASE.",fontsize=8.7,color=SLATE)
    save(fig,"boston_pricing_closure_continuation","R4 closure continuation",
         "Five R4 continuation rounds raise the column pool from 152 to 167 while minimum ungenerated reduced cost reaches numerical zero; objective stays at the optimum.",
         "Accepted R4 continuation trace. All 15 added columns have zero final flow. The degenerate nonincreasing additions complete a full-path-space dual/pricing certificate rather than changing final physical traffic.",
         ["closure_continuation.csv","validation_summary.json"])


def figure_j():
    r=rows("closure_by_demand.csv");d=[z["demand_id"] for z in r];v=np.array([float(z["min_ungenerated_reduced_cost"]) for z in r]);tol=float(r[0]["tolerance"])
    fig,(ax,zoom)=plt.subplots(1,2,figsize=(10.8,5.0),gridspec_kw={"width_ratios":[1.18,1]});fig.patch.set_facecolor(BG)
    head(fig,"Boston | independent pricing closure by demand","Full-DAG ungenerated-path reduced cost · all 10 demands pass at tolerance 1e−6")
    fig.subplots_adjust(top=.76,bottom=.21,left=.08,right=.97,wspace=.28)
    ax.bar(d,v,color=MINT);ax.axhline(0,color=NAVY,lw=.8)
    ax.tick_params(axis="x",labelrotation=45);ax.set_ylabel("Min ungenerated reduced cost")
    ax.set_title("All ten demands · full range",fontsize=10,fontweight="bold");ax.grid(axis="y",alpha=.6)
    near=[(name,val) for name,val in zip(d,v) if abs(val)<tol]
    zoom.scatter([name for name,_ in near],[val for _,val in near],color=TEAL,s=34,zorder=3)
    zoom.axhline(-tol,color=CORAL,ls="--",lw=2,label="−1e−6 threshold")
    zoom.axhline(0,color=NAVY,lw=.8)
    zoom.set_ylim(-1.45e-6,.45e-6);zoom.tick_params(axis="x",labelrotation=45)
    zoom.set_title("Eight near-zero demands · threshold zoom",fontsize=10,fontweight="bold")
    zoom.grid(axis="y",alpha=.6);zoom.legend(frameon=False,loc="lower left",fontsize=8)
    fig.text(.08,.06,"B02 and B06 have positive margins. B09 ≈ −8.9e−16 is floating-point zero, not an improving path; KKT and pricing are distinct.",fontsize=8.6,color=SLATE)
    save(fig,"boston_pricing_closure_by_demand","Independent closure by demand",
         "Bar plot for B01–B10 minimum ungenerated-path reduced costs with a visible minus-one-millionth tolerance line; all ten pass.",
         "The R4 independent full-DAG pricing check returns no ungenerated path below −1e−6 for B01–B10. Values near machine zero are not improving columns. This is separate from existing-path stationarity/KKT checks and does not describe Sioux pricing closure.",
         ["closure_by_demand.csv"])


def figure_h():
    a=rows("phase_i_total.csv");b=rows("phase_ii_objective.csv");c=rows("closure_continuation.csv")
    fig=plt.figure(figsize=(12,7.1));fig.patch.set_facecolor(BG)
    head(fig,"Boston | one bounded CG pilot, independently pricing-closed","90 physical nodes · 125 directed links · 10 ODs · 3-second steps · 100-step horizon")
    ax0=fig.add_axes([.055,.51,.41,.31]);ax1=fig.add_axes([.55,.51,.39,.31]);ax2=fig.add_axes([.055,.12,.41,.29]);ax3=fig.add_axes([.55,.12,.39,.29])
    flow_map(ax0,False);ax0.set_title("01 · 52 positive-flow links",loc="left",fontsize=10,fontweight="bold")
    ax1.step([int(z["round"]) for z in a],[float(z["artificial_flow"]) for z in a],where="post",color=TEAL,lw=2)
    ax1.set_title("02 · Phase I artificial flow → 0",loc="left",fontsize=10,fontweight="bold");ax1.set_xlabel("round");ax1.grid(axis="y",alpha=.5)
    ax2.plot([int(z["round"]) for z in b],[float(z["objective"]) for z in b],color=TEAL,lw=2)
    ax2.axhline(j("validation_summary.json")["identical_graph_arc_lp_reference_objective"],ls="--",color=CORAL)
    ax2.set_title("03 · Phase II matches arc-LP reference",loc="left",fontsize=10,fontweight="bold");ax2.set_xlabel("round");ax2.grid(axis="y",alpha=.5)
    ax3.set_facecolor("#edf5f6");ax3.set_xticks([]);ax3.set_yticks([])
    for spine in ax3.spines.values():spine.set_visible(False)
    ax3.text(.07,.82,"04 · Independent full-DAG certificate",transform=ax3.transAxes,fontsize=10,fontweight="bold")
    ax3.text(.07,.56,"10 / 10 demands pass",transform=ax3.transAxes,color=TEAL,fontsize=18,fontweight="bold")
    ax3.text(.07,.34,"152 → 167 columns · +15 zero-flow",transform=ax3.transAxes,fontsize=10)
    ax3.text(.07,.15,"second-machine receiver check pending",transform=ax3.transAxes,fontsize=9,color=SLATE)
    save(fig,"boston_cg_summary_panel","Boston CG summary composite",
         "Four-panel Boston bounded-pilot summary: final road-flow map, Phase-I clearance, Phase-II reference objective, and R4 ten-demand pricing certificate.",
         "Composed summary of the same accepted bounded Boston pilot, not four different scales. Final physical-link movement flow has 52 positive-flow links; Phase I clears at round 90; Phase II establishes reference-objective agreement on the same finite time-expanded graph; R4 establishes 10/10 independent pricing closure with 15 zero-flow certificate columns.",
         ["physical_link_flow_geometry.csv","phase_i_total.csv","phase_ii_objective.csv","closure_continuation.csv","closure_by_demand.csv","validation_summary.json"])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",choices=("phase-ii",),help="Redraw one saved-result figure without touching other figure assets")
    args=parser.parse_args()
    functions=(figure_f,) if args.only=="phase-ii" else (figure_a,figure_b,figure_c,figure_d,figure_e,figure_f,figure_g,figure_i,figure_j,figure_h)
    for fn in functions:
        fn()
    provenance=j("figure_source_provenance.json")
    for name,item in manifest.items():
        item["plot_input_sha256"]={p:hashlib.sha256((DATA/p).read_bytes()).hexdigest() for p in item["plot_inputs"]}
    if args.only:
        previous=json.loads((ASSET/"figure_manifest.json").read_text(encoding="utf-8"))
        previous["figures"].update(manifest)
        manifest_to_write=previous
    else:
        manifest_to_write={"source_provenance":"data/figure_source_provenance.json",
          "source_file_hashes":provenance["source_files_sha256"],"figures":manifest}
    (ASSET/"figure_manifest.json").write_text(json.dumps(manifest_to_write,indent=2),encoding="utf-8")
    print("Rendered",len(manifest),"Boston CG PNG/SVG figure pairs")


if __name__ == "__main__":
    main()
