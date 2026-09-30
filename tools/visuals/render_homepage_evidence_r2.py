#!/usr/bin/env python3
"""Render row-matched homepage previews from shipped public saved records.

Presentation only: no demand model, optimizer, matcher, pricing or solver calls.
The R1 previews and all original scientific figures remain untouched.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon as PatchPolygon
import numpy as np
from PIL import Image
from shapely import wkt
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/homepage_evidence_r2"
R1_MAP = ROOT / "tools/visuals/homepage_evidence_r1_map.csv"
CITIES = ("Boston", "Sioux Falls", "Hong Kong")
SLUG = {"Boston": "boston", "Sioux Falls": "sioux_falls", "Hong Kong": "hong_kong"}
NAVY, TEAL, LIGHT, ORANGE = "#17364a", "#087f8c", "#dce6eb", "#d99243"
CANVAS = (600, 360)
PLOT_BBOX = (0.10, 0.16, 0.80, 0.68)

ROW_SPECS = [
    ("01", "Source data and preparation", "source_network", "minimal base-network source map"),
    ("02", "GMNS network, zones and access", "gmns_objects", "GMNS object-relation map"),
    ("03", "Population, households and activity", "zone_triptych", "three-panel zone small multiple"),
    ("04", "Transit and pedestrian inputs", "transit_overlay", "transit/access overlay map"),
    ("05", "GPS, trajectory and detector evidence", "observation_relation", "observation-to-network relation map"),
    ("06", "01 / Trip generation — productions / attractions", "generation_pair", "two-panel zone map"),
    ("07", "02 / Trip distribution — zonal OD demand", "od_heatmap", "OD-matrix heatmap"),
    ("08", "03 / Mode choice — mode-specific demand", "mode_bars", "mode-share bar chart"),
    ("09", "04 / Traffic assignment — assigned network flows", "static_flow", "primary static physical-link flow map"),
    ("10", "Frank–Wolfe", "fw_flow", "FW physical-link flow map"),
    ("11", "Official tap-b Algorithm B", "algorithm_b_flow", "Algorithm B physical-link flow map"),
    ("12", "Finite-path reference", "finite_path", "finite-path reconstruction panel"),
    ("13", "Native Diagnostic L3 / compression", "l3_difference", "L3 reconstruction/difference panel"),
    ("14", "Network construction and generated columns", "layered_graph", "layered physical-to-time graph preview"),
    ("15", "Arc-flow LP reference", "lp_reference", "same-graph LP reference result panel"),
    ("16", "Two-phase column generation", "cg_triptych", "Phase I / Phase II / final-check triptych"),
    ("17", "Lagrangian", "lagrangian_summary", "dual/primal/gap summary"),
    ("18", "ADMM", "admm_summary", "residual/objective/flow summary"),
    ("19", "Query, tracing, exports and saved checks", "tool_card", "standard query/export result card"),
]

BASE = {
    "Boston": "examples/boston/gmns_exchange_r1/data/",
    "Hong Kong": "examples/hong-kong/gmns_pilot_r1/instance/",
}
SIOUX_LINKS = "examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/link.csv"
SIOUX_FINITE = "examples/sioux-falls/native_l3_r1/runs/SiouxFalls/B_BECKMANN/outer_04_link_flows.csv"
SIOUX_L3 = "examples/sioux-falls/native_l3_r1/runs/SiouxFalls/A_REG001/outer_04_link_flows.csv"
BOSTON_PATH = "examples/boston/assignment_methods_r1/reference/link_flow.csv"
BOSTON_L3 = "examples/boston/assignment_methods_r1/runs/rank26/outer_02_link_flows.csv"
HK_PHASE_B = "docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_b/"
HK_CG = "docs/assets/hong_kong/full_stack_r5/cg_run/"
B_CG = "docs/assets/boston/space_time_cg_r4/data/"
S_CG = "docs/assets/sioux/phase_i_r1/data/"

SOURCE_OVERRIDE = {
    "01": {"Boston": BASE["Boston"]+"link.csv", "Sioux Falls": SIOUX_LINKS, "Hong Kong": BASE["Hong Kong"]+"link.csv"},
    "02": {"Boston": BASE["Boston"]+"link.csv", "Sioux Falls": SIOUX_LINKS, "Hong Kong": BASE["Hong Kong"]+"link.csv"},
    "03": {"Boston": "examples/boston/population_r1/data/population_or_household_by_zone.csv", "Hong Kong": HK_PHASE_B+"zone_activity_r2.csv"},
    "04": {"Boston": BASE["Boston"]+"transit_stop_route_relation.csv", "Hong Kong": BASE["Hong Kong"]+"transit_stops.csv"},
    "05": {"Boston": "examples/boston/gmns_exchange_r1/figure_sample/gps_point_progress.csv", "Hong Kong": BASE["Hong Kong"]+"detector_to_link.csv"},
    "06": {"Boston": "docs/assets/boston/four_step_results_r1/data/hbw_midday_matrix.csv", "Hong Kong": HK_PHASE_B+"production_attraction_r2.csv"},
    "07": {"Boston": "docs/assets/boston/four_step_results_r1/data/hbw_midday_matrix.csv", "Hong Kong": HK_PHASE_B+"od_person_distribution_r2.csv"},
    "08": {"Boston": "docs/assets/boston/four_step_results_r1/data/selected_mode_response.csv", "Hong Kong": HK_PHASE_B+"mode_demand_by_od.csv"},
    "09": {"Boston": "examples/boston/scalable_tool_r1/runs/all/physical_link_flow.csv", "Sioux Falls": "algorithms/origin_based_algorithm_b/accepted_results/sioux_physical_link_flow.csv", "Hong Kong": HK_PHASE_B+"static_runs/full_algorithm_b/link_flow.csv"},
    "10": {"Boston": "examples/boston/scalable_tool_r1/runs/all/physical_link_flow.csv", "Sioux Falls": "docs/assets/algorithm_b_r21/source_panels/sioux_fw_flow.svg", "Hong Kong": "docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_static_fw_flow.png"},
    "11": {"Boston": "algorithms/origin_based_algorithm_b/accepted_results/boston_b1_physical_link_flow.csv", "Sioux Falls": "algorithms/origin_based_algorithm_b/accepted_results/sioux_physical_link_flow.csv", "Hong Kong": HK_PHASE_B+"static_runs/full_algorithm_b/link_flow.csv"},
    "12": {"Boston": BOSTON_PATH, "Sioux Falls": SIOUX_FINITE},
    "13": {"Boston": BOSTON_L3, "Sioux Falls": SIOUX_L3},
    "14": {"Boston": "docs/assets/three_city_r2/data/boston_construction_edges.csv", "Sioux Falls": "docs/assets/three_city_r2/data/sioux_construction_edges.csv", "Hong Kong": "docs/assets/three_city_r2/data/hong_kong_construction_edges.csv"},
    "15": {"Boston": B_CG+"validation_summary.json", "Sioux Falls": S_CG+"200_phase_ii_trace.csv", "Hong Kong": HK_CG+"full_cg_v1_phase_ii_objective_trace.csv"},
    "16": {"Boston": B_CG+"phase_i_total.csv", "Sioux Falls": S_CG+"200_phase_i_trace.csv", "Hong Kong": HK_CG+"full_cg_v1_phase_i_artificial_flow_trace.csv"},
    "17": {"Boston": "docs/cases/boston.md", "Sioux Falls": "docs/methods/distributed-assignment.md", "Hong Kong": "docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/lagrangian_run/history.csv"},
    "18": {"Boston": "docs/assets/admm_r2/figures/admm_boston_10od_case_sequence.png", "Sioux Falls": "docs/assets/admm_r2/figures/admm_sioux_200_case_sequence.png", "Hong Kong": "docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/admm_run/result.json"},
    "19": {"Boston": "examples/boston/SAVED_EXAMPLE.md", "Sioux Falls": "examples/sioux-falls/native_l3_r1/README.md", "Hong Kong": "docs/cases/hong-kong.md"},
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def records(rel: str) -> list[dict]:
    with (ROOT/rel).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def fig_axes(title: str, city: str, scope: str):
    fig = plt.figure(figsize=(6, 3.6), dpi=100, facecolor="white")
    fig.text(.07,.94,title,fontsize=12,weight="bold",color=NAVY,family="DejaVu Sans")
    map_rows={"Source data and preparation","GMNS network, zones and access","04 / Traffic assignment — assigned network flows","Frank–Wolfe","Official tap-b Algorithm B"}
    city_label="Sioux Falls · schematic" if city=="Sioux Falls" and title in map_rows else city
    fig.text(.93,.94,city_label,fontsize=8.5,color=TEAL,ha="right",family="DejaVu Sans")
    fig.text(.07,.055,scope,fontsize=7.4,color="#53697a",family="DejaVu Sans")
    return fig

def neutral(fig, status: str, detail: str):
    ax=fig.add_axes(PLOT_BBOX);ax.set_facecolor("#f4f7f8")
    ax.text(.5,.58,status,ha="center",va="center",fontsize=14,color=NAVY,weight="bold",transform=ax.transAxes)
    ax.text(.5,.42,detail,ha="center",va="center",fontsize=9,color="#526779",transform=ax.transAxes,wrap=True)
    ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_color(LIGHT)

def graph(city: str):
    """Return original physical link geometry only, plus physical node coordinates."""
    if city == "Sioux Falls":
        import networkx as nx
        rs=records(SIOUX_LINKS);g=nx.Graph()
        for r in rs:g.add_edge(r["from_node_id"],r["to_node_id"])
        pos=nx.spring_layout(g,seed=24,iterations=140)
        points={n:(float(v[0]),float(v[1])) for n,v in pos.items()}
        lines=[(r["link_id"],[points[r["from_node_id"]],points[r["to_node_id"]]]) for r in rs]
        return lines,points
    prefix=BASE[city]
    rs=records(prefix+"link.csv")
    lines=[]
    for r in rs:
        if r.get("mcl_link_class")!="physical" or not r.get("geometry"):continue
        geom=wkt.loads(r["geometry"])
        coords=list(geom.coords)
        lat=sum(p[1] for p in coords)/len(coords); k=math.cos(math.radians(lat))
        lines.append((r["link_id"],[(p[0]*k,p[1]) for p in coords]))
    points={}
    for r in records(prefix+"node.csv"):
        if r.get("x_coord") and r.get("y_coord"):
            x=float(r["x_coord"]);y=float(r["y_coord"])
            points[r["node_id"]]=(x*math.cos(math.radians(y)),y)
    return lines,points

def base_map(ax,city,flows=None,highlight=None,point_layer=False):
    lines,points=graph(city)
    segments=[coords for _,coords in lines]
    ax.add_collection(LineCollection(segments,colors="#c7d4db",linewidths=.55,alpha=.85,zorder=1))
    if flows:
        vals=np.array([max(0,float(flows.get(k,0))) for k,_ in lines]);cap=float(np.quantile(vals,.98)) if len(vals) else 1
        cap=max(cap,1e-9)
        colors=plt.cm.viridis(np.clip(vals/cap,0,1))
        widths=.65+2.2*np.clip(vals/cap,0,1)
        ax.add_collection(LineCollection(segments,colors=colors,linewidths=widths,alpha=.9,zorder=2))
    if highlight:
        hs=[coords for key,coords in lines if key in highlight]
        if hs:ax.add_collection(LineCollection(hs,colors=ORANGE,linewidths=2.3,alpha=.92,zorder=3))
    if point_layer:
        xy=np.array(list(points.values()))
        if len(xy):ax.scatter(xy[:,0],xy[:,1],s=.7,c=NAVY,alpha=.30,zorder=3)
    allxy=np.array([p for _,coords in lines for p in coords])
    xmin,ymin=allxy.min(axis=0);xmax,ymax=allxy.max(axis=0)
    dx=max(xmax-xmin,1e-9);dy=max(ymax-ymin,1e-9)
    ax.set_xlim(xmin-.04*dx,xmax+.04*dx);ax.set_ylim(ymin-.04*dy,ymax+.04*dy)
    ax.set_aspect("equal",adjustable="box");ax.axis("off")
    return lines,points

def zone_shapes(city):
    if city=="Boston":
        rs=records(BASE[city]+"zone.csv")
        return {r["name"]:wkt.loads(r["mcl_clipped_geometry_wkt"] or r["boundary"]) for r in rs if r.get("mcl_clipped_geometry_wkt") or r.get("boundary")}
    if city=="Hong Kong":
        data=json.loads((ROOT/(BASE[city]+"zone_geometry.geojson")).read_text(encoding="utf-8"))
        return {str(f["properties"].get("zone_id",f["id"] if "id" in f else i)):shape(f["geometry"]) for i,f in enumerate(data["features"])}
    return {}

def draw_zones(ax,city,values=None,cmap="YlGnBu"):
    shapes=zone_shapes(city); vals=values or {}
    vmax=max([float(v) for v in vals.values()] or [1]);cm=plt.get_cmap(cmap)
    for zid,geom in shapes.items():
        polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else [geom]
        for poly in polys:
            coords=np.asarray(poly.exterior.coords);lat=float(np.mean(coords[:,1]));coords[:,0]*=math.cos(math.radians(lat))
            color=cm(min(1,float(vals.get(zid,0))/max(vmax,1e-9))) if values is not None else "#d8eef0"
            ax.add_patch(PatchPolygon(coords,closed=True,facecolor=color,edgecolor="#a9c4cc",lw=.33))
    ax.autoscale_view();ax.set_aspect("equal",adjustable="box");ax.axis("off")
    return vmax

def numeric_rows(city,kind):
    if kind=="population":
        if city=="Boston":
            rows=records(SOURCE_OVERRIDE["03"][city]);_,attraction=numeric_rows(city,"generation")
            return ({r["zone_id"]:float(r["population_estimate_area_weighted"] or 0) for r in rows},{r["zone_id"]:float(r["households_estimate_area_weighted"] or 0) for r in rows},attraction)
        rows=records(SOURCE_OVERRIDE["03"][city]);return ({str(r["zone_id"]):float(r["population"] or 0) for r in rows},{str(r["zone_id"]):float(r["households"] or 0) for r in rows},{str(r["zone_id"]):float(r["employment_or_attraction_proxy"] or 0) for r in rows})
    if city=="Boston":
        rows=records(SOURCE_OVERRIDE["06"][city]);heads=[k for k in rows[0] if k!="origin_zone_id"]
        prod={r["origin_zone_id"]:sum(float(r[k] or 0) for k in heads) for r in rows}
        attr={k:sum(float(r[k] or 0) for r in rows) for k in heads}
        return prod,attr
    rows=records(SOURCE_OVERRIDE["06"][city]);p=defaultdict(float);a=defaultdict(float)
    for r in rows:p[str(r["zone_id"])]+=float(r["interzonal_production_person_trips_am"] or 0);a[str(r["zone_id"])]+=float(r["interzonal_attraction_person_trips_am"] or 0)
    return dict(p),dict(a)

def panel_axes(fig,n):
    gap=.025;left=.07;right=.05;total=1-left-right-gap*(n-1);width=total/n
    return [fig.add_axes((left+i*(width+gap),.19,width,.59)) for i in range(n)]

def render_data_panel(fig,row_id,city):
    template=next(x[2] for x in ROW_SPECS if x[0]==row_id)
    if template=="fw_flow" and city=="Sioux Falls":
        neutral(fig,"FW link vector not shipped","Accepted FW / Algorithm B parity figure remains linked; no inferred FW map.")
        return
    if template=="fw_flow" and city=="Hong Kong":
        ax=fig.add_axes((.07,.15,.86,.69));ax.imshow(Image.open(ROOT/SOURCE_OVERRIDE[row_id][city]).convert("RGB"));ax.axis("off")
        return
    if template in {"source_network","gmns_objects","static_flow","fw_flow","algorithm_b_flow","transit_overlay","observation_relation"}:
        ax=fig.add_axes(PLOT_BBOX)
        flows=None;highlight=None;node_layer=template=="gmns_objects"
        if template in {"static_flow","fw_flow"} and city=="Boston":
            flows={r["link_id"]:float(r["flow_pce_per_period"] or 0) for r in records(SOURCE_OVERRIDE[row_id][city])}
        elif template=="static_flow" and city=="Sioux Falls":
            flows={r["link_id"]:float(r["volume"] or 0) for r in records(SOURCE_OVERRIDE["11"][city])}
        elif template=="static_flow" and city=="Hong Kong":
            flows={r["link_id"]:float(r["volume"] or 0) for r in records(SOURCE_OVERRIDE["11"][city])}
        elif template=="algorithm_b_flow":
            flows={r["link_id"]:float(r["volume"] or 0) for r in records(SOURCE_OVERRIDE[row_id][city])}
        elif template=="transit_overlay" and city=="Boston":
            highlight={r["matched_link_id"] for r in records(BASE[city]+"transit_shape_conflation.csv") if r.get("matched_link_id")}
        elif template=="observation_relation" and city=="Boston":
            highlight={r["link_id"] for r in records(BASE[city]+"gps_path_links.csv") if r.get("link_id")}
        elif template=="observation_relation" and city=="Hong Kong":
            highlight={r["gmns_link_id"] for r in records(BASE[city]+"detector_to_link.csv") if r.get("gmns_link_id")}
        lines,points=base_map(ax,city,flows,highlight,node_layer)
        if template=="gmns_objects" and city!="Sioux Falls":
            # Zone boundaries and centroid symbols are separate from physical roads.
            shapes=zone_shapes(city)
            for geom in shapes.values():
                polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else [geom]
                for poly in polys:
                    coords=np.asarray(poly.exterior.coords);coords[:,0]*=math.cos(math.radians(float(np.mean(coords[:,1]))))
                    ax.plot(coords[:,0],coords[:,1],color="#5f9ca7",lw=.38,alpha=.8,zorder=4)
            cent=[p for k,p in points.items() if k.isdigit() and int(k)<=len(shapes)]
            if cent:ax.scatter([p[0] for p in cent],[p[1] for p in cent],marker="s",s=6,c=ORANGE,zorder=5)
        if template=="transit_overlay":
            stopfile=SOURCE_OVERRIDE[row_id][city]
            stops=records(stopfile)
            xy=[]
            for r in stops:
                x=r.get("stop_lon");y=r.get("stop_lat")
                if x and y:xy.append((float(x)*math.cos(math.radians(float(y))),float(y)))
            if xy:ax.scatter(*np.array(xy).T,s=8,c=TEAL,alpha=.8,zorder=5)
        if template=="observation_relation":
            obs=records(SOURCE_OVERRIDE[row_id][city]);xy=[]
            for r in obs:
                x=r.get("original_lon") or r.get("longitude");y=r.get("original_lat") or r.get("latitude")
                if x and y:xy.append((float(x)*math.cos(math.radians(float(y))),float(y)))
            if xy:ax.scatter(*np.array(xy).T,s=8,c=ORANGE,alpha=.8,zorder=5)
        if template in {"static_flow","fw_flow","algorithm_b_flow"}:
            fig.text(.91,.83,"local flow scale",ha="right",fontsize=7,color="#53697a")
        return
    if template=="zone_triptych":
        vals=numeric_rows(city,"population");axs=panel_axes(fig,3)
        for ax,v,label in zip(axs,vals,("Population","Households","Modeled HBW attraction" if city=="Boston" else "Attraction proxy")):
            if not v:ax.text(.5,.5,"No published\nzone proxy",ha="center",va="center",transform=ax.transAxes,fontsize=8)
            else:mx=draw_zones(ax,city,v);ax.text(.98,.02,f"max {mx:,.0f}",ha="right",transform=ax.transAxes,fontsize=7)
            ax.set_title(label,fontsize=8,color=NAVY)
        return
    if template=="generation_pair":
        vals=numeric_rows(city,"generation");axs=panel_axes(fig,2)
        for ax,v,label in zip(axs,vals,("Productions","Attractions")):
            mx=draw_zones(ax,city,v);ax.set_title(label,fontsize=8,color=NAVY);ax.text(.98,.02,f"max {mx:,.1f}",ha="right",transform=ax.transAxes,fontsize=7)
        return
    if template=="od_heatmap":
        if city=="Boston":
            rs=records(SOURCE_OVERRIDE[row_id][city]);cols=[k for k in rs[0] if k!="origin_zone_id"]
            mat=np.array([[float(r[k] or 0) for k in cols] for r in rs])
        else:
            rs=records(SOURCE_OVERRIDE[row_id][city]);ids=sorted({r["o_zone_id"] for r in rs}|{r["d_zone_id"] for r in rs},key=lambda x:int(x));ind={x:i for i,x in enumerate(ids)};mat=np.zeros((len(ids),len(ids)))
            for r in rs:mat[ind[r["o_zone_id"]],ind[r["d_zone_id"]]]+=float(r["person_trips_am"] or 0)
        ax=fig.add_axes((.16,.17,.62,.65));im=ax.imshow(mat,origin="lower",cmap="YlGnBu",aspect="auto",interpolation="nearest")
        ax.set_xlabel("Destination zone",fontsize=8);ax.set_ylabel("Origin zone",fontsize=8);ax.tick_params(labelsize=7)
        cb=fig.colorbar(im,ax=ax,fraction=.05,pad=.03);cb.ax.tick_params(labelsize=7);cb.set_label("person trips, local scale",fontsize=7)
        return
    if template=="mode_bars":
        if city=="Boston":
            rs=records(SOURCE_OVERRIDE[row_id][city]);code={r["mode"]:float(r["S1_probability"] or 0) for r in rs}
            pairs=[("Drive",sum(code.get(k,0) for k in ("DA","S2","S3"))),("Transit",sum(code.get(k,0) for k in ("TW","TA"))),("Walk",code.get("WK",0)),("Other",sum(code.get(k,0) for k in ("BK","SB","RS")))]
            scope="Boston S1 selected-OD probability"
        else:
            rs=records(SOURCE_OVERRIDE[row_id][city]);tot={m:sum(float(r[f"{m}_person_trips_am"] or 0) for r in rs) for m in ("drive","transit","walk")};den=sum(tot.values());pairs=[(m.title(),tot[m]/den) for m in ("drive","transit","walk")];scope="HK modeled AM person-trip shares"
        ax=fig.add_axes((.18,.2,.7,.58));order=["Drive","Transit","Walk","Other"]
        vals=dict(pairs);bars=ax.barh(order,[vals.get(k,0) for k in order],color=["#21759b","#5cae9c","#d99243", "#879ca8"])
        for i,b in enumerate(bars):
            label="n/a" if city=="Hong Kong" and order[i]=="Other" else f"{b.get_width():.1%}"
            ax.text(b.get_width()+.008,b.get_y()+b.get_height()/2,label,va="center",fontsize=8)
        ax.set_xlim(0,1.05);ax.invert_yaxis();ax.tick_params(labelsize=8);ax.set_xlabel(scope,fontsize=8)
        return
    if template in {"finite_path","l3_difference"}:
        a=records(BOSTON_PATH if city=="Boston" else SIOUX_FINITE)
        vals=np.array([float(r.get("volume") or r.get("explicit_v") or 0) for r in a])
        axs=panel_axes(fig,2);axs[0].hist(vals,bins=16,color=TEAL);axs[0].set_title("Reconstructed link flow",fontsize=8)
        if template=="l3_difference":
            b=records(BOSTON_L3 if city=="Boston" else SIOUX_L3)
            if city=="Boston":
                ref={r["link_id"]:float(r.get("volume") or 0) for r in a}
                diff=np.array([float(r.get("v_from_paths") or r.get("explicit_v") or 0)-ref[r["link_id"]] for r in b if r["link_id"] in ref])
                diff_title="Rank-26 minus path ref."
            else:
                diff=np.array([float(r["path_aggregate"])-float(r["explicit_v"]) for r in b])
                diff_title="A_REG001 path residual"
            axs[1].hist(diff,bins=16,color=ORANGE);axs[1].set_title(diff_title,fontsize=8)
        else:
            axs[1].bar(["Positive","Zero"],[int(np.count_nonzero(vals)),int(np.count_nonzero(vals==0))],color=[TEAL,LIGHT]);axs[1].set_title("Reconstruction support",fontsize=8)
        for ax in axs:ax.tick_params(labelsize=7)
        return
    if template=="layered_graph":
        rs=[r for r in records(SOURCE_OVERRIDE[row_id][city]) if r["arc_type"] not in {"source_connector","sink_connector"}]
        nodes=sorted({r["from_physical_node_id"] for r in rs}|{r["to_physical_node_id"] for r in rs},key=lambda x:(0,int(x)) if x.isdigit() else (1,x));rank={n:i for i,n in enumerate(nodes)}
        ax=fig.add_axes((.15,.29,.76,.49));styles={"movement":(TEAL,"-",2.2),"waiting":("#9baeb6","-",1.6),"turn_connector":(ORANGE,"--",1.7),"source_connector":(ORANGE,"--",1.7),"sink_connector":(ORANGE,"--",1.7)}
        for r in rs:
            x=[int(r["from_time"]),int(r["to_time"])];y=[rank[r["from_physical_node_id"]],rank[r["to_physical_node_id"]]];c,ls,lw=styles.get(r["arc_type"],("#778b94",":",1.3))
            ax.plot(x,y,color=c,ls=ls,lw=lw,alpha=.9,marker="o",ms=3)
        ax.set_yticks(range(len(nodes)),[n[-7:] for n in nodes],fontsize=6);ax.set_xlabel("Time step in accepted arc records",fontsize=7);ax.tick_params(axis="x",labelsize=7)
        ax.set_xlim(min(int(r["from_time"]) for r in rs)-.2,max(int(r["to_time"]) for r in rs)+.2);ax.grid(axis="x",color=LIGHT,lw=.6)
        fig.text(.53,.16,"Movement  •  waiting  - -  turn; terminal arcs in full A figure",ha="center",fontsize=7,color="#526779")
        return
    if template in {"cg_triptych","lp_reference","lagrangian_summary","admm_summary","tool_card"}:
        render_summary(fig,row_id,city)
        return
    raise ValueError((row_id,city,template))

def trace(rel,field):
    if not (ROOT/rel).exists():return []
    out=[]
    for r in records(rel):
        try:out.append(float(r[field]))
        except (KeyError,ValueError,TypeError):pass
    return out

def render_summary(fig,row_id,city):
    template=next(x[2] for x in ROW_SPECS if x[0]==row_id)
    if template=="cg_triptych":
        if city=="Boston":p1=trace(B_CG+"phase_i_total.csv","artificial_flow");p2=trace(B_CG+"phase_ii_objective.csv","objective");note="10/10 independent closure"
        elif city=="Sioux Falls":p1=trace(S_CG+"200_phase_i_trace.csv","total_artificial_flow");p2=trace(S_CG+"200_phase_ii_trace.csv","objective_value");note="200-OD example; 250-OD detailed"
        else:p1=trace(HK_CG+"full_cg_v1_phase_i_artificial_flow_trace.csv","total_artificial_flow");p2=trace(HK_CG+"full_cg_v1_phase_ii_objective_trace.csv","objective_value");note="HK10; 10/10 closure"
        axs=panel_axes(fig,3)
        for ax,data,title in ((axs[0],p1,"Phase I: artificial"),(axs[1],p2,"Phase II: objective")):
            ax.plot(range(len(data)),data,color=TEAL,lw=1.6,marker="o",ms=2.4);ax.set_title(title,fontsize=8);ax.tick_params(labelsize=7)
        if city=="Boston":
            metric=json.loads((ROOT/(B_CG+"validation_summary.json")).read_text(encoding="utf-8"))
            number=f'{metric["positive_physical_links"]} positive links';detail=f'LP Δ {metric["absolute_objective_difference"]:.1e}'
        elif city=="Sioux Falls":
            final=records(S_CG+"200_phase_ii_trace.csv")[-1];number="200-OD final check";detail=f'LP gap {float(final["gap_vs_reference"]):.2e}'
        else:
            final=records(HK_CG+"full_cg_v1_phase_ii_objective_trace.csv")[-1];number="HK10 final check";detail=f'LP gap {float(final["gap_vs_reference"]):.2e}'
        axs[2].text(.5,.67,number,ha="center",va="center",fontsize=8,color=NAVY,transform=axs[2].transAxes)
        axs[2].text(.5,.45,detail,ha="center",va="center",fontsize=7,color=TEAL,transform=axs[2].transAxes)
        axs[2].text(.5,.25,note,ha="center",va="center",fontsize=6.5,color="#526779",transform=axs[2].transAxes,wrap=True)
        axs[2].set_xticks([]);axs[2].set_yticks([]);axs[2].set_title("Flow / closure",fontsize=8)
        return
    if template=="lp_reference":
        ax=fig.add_axes((.14,.22,.72,.56));ax.set_facecolor("#f5f9fa")
        label={"Boston":"Own-graph 10-OD LP","Sioux Falls":"Historical selected-OD LP","Hong Kong":"R5 same-graph 10-OD LP"}[city]
        if city=="Boston":value=json.loads((ROOT/SOURCE_OVERRIDE[row_id][city]).read_text(encoding="utf-8"))["identical_graph_arc_lp_reference_objective"]
        elif city=="Sioux Falls":value=float(records(SOURCE_OVERRIDE[row_id][city])[0]["arc_lp_reference_objective"])
        else:value=float(records(SOURCE_OVERRIDE[row_id][city])[0]["arc_lp_reference_objective"])
        ax.text(.5,.69,label,ha="center",fontsize=12,color=NAVY,transform=ax.transAxes)
        ax.text(.5,.46,f"LP reference objective = {value:,.4f}",ha="center",fontsize=11,color=TEAL,transform=ax.transAxes)
        ax.text(.5,.25,"Own graph and OD set only; not cross-city comparable",ha="center",fontsize=8,color="#526779",transform=ax.transAxes)
        ax.set_xticks([]);ax.set_yticks([])
        return
    if template=="lagrangian_summary":
        axs=[fig.add_axes((.07,.28,.41,.50)),fig.add_axes((.53,.28,.41,.50))]
        if city=="Hong Kong":
            rs=records(SOURCE_OVERRIDE[row_id][city]);dual=[float(r["best_dual"]) for r in rs if r["best_dual"]];primal=[float(r["best_primal"]) for r in rs if r["best_primal"]]
            axs[0].plot(dual,color=TEAL,label="dual");axs[0].plot(primal,color=ORANGE,label="primal");axs[0].legend(fontsize=6);gap=0.7444;status="HK10 accepted; saved history"
        elif city=="Sioux Falls":
            axs[0].text(.5,.5,"Feasible recovered\nprimal, 200/250 OD",ha="center",va="center",fontsize=8,transform=axs[0].transAxes)
            gap=0.3177;status="250-OD: 0.3177%; 200-OD: 0.0746%"
        else:
            axs[0].text(.5,.5,"Feasible primal;\ngap gate missed",ha="center",va="center",fontsize=8,transform=axs[0].transAxes)
            gap=1.1002;status="Boston gated; frozen threshold 1%"
        if city=="Sioux Falls":labels=["200 OD","250 OD","Gate"];values=[0.0746,0.3177,1.0]
        else:labels=["Saved gap","Gate"];values=[gap,1.0]
        axs[1].barh(labels,values,color=[TEAL]*(len(values)-1)+[ORANGE]);axs[1].set_xlim(0,1.25);axs[1].tick_params(labelsize=7)
        axs[0].set_title("Dual / primal evidence",fontsize=8);axs[1].set_title("Certified gap (%)",fontsize=8)
        fig.text(.5,.18,status,ha="center",fontsize=8,color=NAVY)
        return
    if template=="admm_summary":
        axs=panel_axes(fig,3)
        status={"Boston":"R2_S accepted; 10 OD","Sioux Falls":"R2_S accepted; 200-OD example","Hong Kong":"Gated diagnostic; no accepted objective"}[city]
        if city!="Hong Kong":
            source=Image.open(ROOT/SOURCE_OVERRIDE[row_id][city]).convert("RGB")
            crops=((75,150,510,350),(1095,150,1535,350),(580,455,1025,670))
            for ax,box,title in zip(axs,crops,("Residuals","Objective / LP","Physical flow")):
                ax.imshow(source.crop(box));ax.set_title(title,fontsize=8);ax.axis("off")
        else:
            result=json.loads((ROOT/SOURCE_OVERRIDE[row_id][city]).read_text(encoding="utf-8"))
            for ax,title in zip(axs,("Residuals","Objective / LP","Physical flow")):
                ax.set_title(title,fontsize=8);ax.set_xticks([]);ax.set_yticks([])
            axs[0].barh(["Local balance","Gate"],[0.082467622,0.0],color=[ORANGE,TEAL]);axs[0].tick_params(labelsize=6)
            axs[1].text(.5,.5,"Not accepted\nfor this transfer",ha="center",va="center",fontsize=8,color=NAVY,transform=axs[1].transAxes)
            axs[2].text(.5,.5,"No accepted\nphysical flow",ha="center",va="center",fontsize=8,color=NAVY,transform=axs[2].transAxes)
        fig.text(.5,.12,status,ha="center",fontsize=8,color=NAVY)
        return
    if template=="tool_card":
        ax=fig.add_axes((.09,.2,.82,.59));ax.set_facecolor("#f2f7f8")
        cmd={"Boston":"GMNS trace → SQLite query/export","Sioux Falls":"Frozen input → native profile/check","Hong Kong":"Source/turn ledger → validation"}[city]
        ax.text(.05,.73,"ACTION",transform=ax.transAxes,fontsize=7,color=TEAL,weight="bold")
        ax.text(.05,.55,cmd,transform=ax.transAxes,fontsize=11,color=NAVY)
        ax.text(.05,.26,"Input ID → saved rows/files → documented checks",transform=ax.transAxes,fontsize=8,color="#53697a")
        ax.set_xticks([]);ax.set_yticks([])
        return

def render():
    OUT.mkdir(parents=True,exist_ok=True)
    r1={(r["subitem"],r["city"]):r for r in records("tools/visuals/homepage_evidence_r1_map.csv")}
    matrix=[]
    for row_id,title,template,graphic in ROW_SPECS:
        for city in CITIES:
            old=r1[(title,city)]
            source=SOURCE_OVERRIDE.get(row_id,{}).get(city,old["source_figure_or_data"])
            status=old["scope / status"]
            if source and not (ROOT/source).is_file():raise FileNotFoundError(source)
            fig=fig_axes(title,city,old["result_summary"])
            if status in {"outside benchmark","not demonstrated"} or not source:
                neutral(fig,"Not part of this case",old["result_summary"])
            else:render_data_panel(fig,row_id,city)
            rel=f"docs/assets/homepage_evidence_r2/row_{row_id}_{SLUG[city]}.png";dest=ROOT/rel
            fig.savefig(dest,dpi=100,facecolor="white",metadata={"Software":"MCL homepage evidence R2"})
            plt.close(fig)
            with Image.open(dest) as im:
                if im.size!=CANVAS:raise AssertionError((rel,im.size))
            target=old["evidence_page"]
            note="same renderer; absent stages use neutral status tile"
            if row_id=="09" and city in {"Sioux Falls","Hong Kong"}:note="primary static output is accepted Algorithm B modeled flow; not FW"
            if city=="Sioux Falls" and row_id in {"01","02","09","11"}:note += "; deterministic source-topology layout, not geographic coordinates"
            if row_id=="10" and city=="Sioux Falls":note="exact FW per-link vector not shipped; neutral preview preserves accepted comparison link"
            if row_id=="10" and city=="Hong Kong":note="accepted saved FW map image; numerical flow vector not shipped"
            row={"row_id":row_id,"row_title":title,"template_id":template,"graphic_type":graphic,"canvas_width":600,"canvas_height":360,"plot_bbox":str(PLOT_BBOX),"legend_contract":"fixed below/inside plot; local numeric scale","city":city,"data_or_figure_source":source,"source_hash":sha(ROOT/source) if source else "","result_scope":old["result_summary"],"target_page":target.split("#")[0],"target_anchor":target.split("#",1)[1] if "#" in target else "","status":status,"notes":note,"preview_path":rel,"preview_hash":sha(dest),"original_figure":old["source_figure_or_data"]}
            matrix.append(row)
            side={"preview_path":rel,"preview_hash":row["preview_hash"],"template_id":template,"city":city,"stage":title,"method":title if row_id in {"10","11","12","13","15","16","17","18"} else "","instance":old["result_summary"],"source_asset_or_data":source,"source_hash":row["source_hash"],"transform":"deterministic, source-qualified row-specific plot or neutral status","crop":"none","scale_behavior":"contain/equal physical geometry; local numeric scales","units":"as labelled in preview and detailed source","legend":row["legend_contract"],"target_page":row["target_page"],"target_anchor":row["target_anchor"]}
            dest.with_suffix(".source.json").write_text(json.dumps(side,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
    fields=list(matrix[0]);with_path=OUT/"ROW_TEMPLATE_MATRIX.csv"
    with with_path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(matrix)
    print(f"Rendered {len(matrix)} row previews via {len(ROW_SPECS)} shared row templates")
    return matrix

if __name__=="__main__":render()
