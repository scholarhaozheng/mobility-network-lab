#!/usr/bin/env python3
"""Render R2 three-city figures from saved public cutaway tables and result CSVs.

No network compilation, path search, pricing, optimization or model fitting occurs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/assets/three_city_r2"
DATA=OUT/"data"
INK="#213744"; MUTED="#586d7b"; TEAL="#087f83"; RUST="#b45e43"
GRAY="#a9bac3"; PURPLE="#7c70a3"; PALE="#d9e3e8"
COLORS={"movement":TEAL,"waiting":GRAY,"turn_connector":RUST,
        "zone_connector":PURPLE,"source_connector":RUST,"sink_connector":RUST}
FAMILY={"A":"physical_to_time_expanded_graph","B":"generated_column_time_indexed_path",
        "C":"time_expanded_to_physical_link_flow","D":"finite_space_time_case_sequence"}
mpl.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","DejaVu Sans","sans-serif"],
    "svg.fonttype":"none","pdf.fonttype":42,"font.size":9,"savefig.facecolor":"white",
    "figure.facecolor":"white","axes.spines.top":False,"axes.spines.right":False,
    "svg.hashsalt":"three-city-parallel-r2"})

CASE={
"boston":{"label":"Boston","scope":"90 physical nodes · 125 links · 10 OD",
    "time":"3 s / model step","column":"PHASEI_R1_GEN_B07_001","demand":"B07",
    "flow":"0.364622 model vehicles","arrival":"physical arrival t19; sink t100 is bookkeeping",
    "edges":"docs/assets/three_city_r2/data/boston_construction_edges.csv",
    "path":"docs/assets/boston/space_time_cg_r4/data/construction_path_arcs.csv",
    "geometry":"docs/assets/boston/space_time_cg_r4/data/physical_link_flow_geometry.csv",
    "map":"docs/assets/boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png",
    "phase_i":"docs/assets/boston/space_time_cg_r4/data/phase_i_total.csv",
    "phase_ii":"docs/assets/boston/space_time_cg_r4/data/phase_ii_objective.csv",
    "event":"docs/assets/boston/space_time_cg_r4/data/phase_i_round1_od_change.csv",
    "reference":64.3968615115296,"links":"125","positive":"52",
    "mapping":"Not reported in public evidence","residual":"Not reported in public evidence",
    "unit":"modeled vehicles over finite horizon","closure":"Established · 10/10",
    "shared":"B07/B09/B10 recorded exchange"},
"sioux":{"label":"Sioux Falls","scope":"24 nodes · 64/69 selected links · 200/250 OD",
    "time":"1 model step (seconds not published)","column":"GEN_XS170_001","demand":"XS170",
    "flow":"500 model vehicles in recorded exchange","arrival":"physical arrival t6; sink t32 is bookkeeping",
    "edges":"docs/assets/three_city_r2/data/sioux_construction_edges.csv",
    "path":"docs/assets/three_city_r2/data/sioux_construction_edges.csv",
    "map":"docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png",
    "map_250":"docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png",
    "phase_i":"docs/assets/sioux/phase_i_r1/data/200_phase_i_trace.csv",
    "phase_ii":"docs/assets/sioux/phase_i_r1/data/200_phase_ii_trace.csv",
    "event":"docs/assets/presentation_r5/data/sioux_shared_capacity_saved.csv",
    "reference":943155.589771,"links":"64 / 69","positive":"Not reported in public evidence",
    "mapping":"Not reported in public evidence","residual":"5.46e−12 / 1.09e−11 vehicles",
    "unit":"modeled vehicles over each selected horizon","closure":"Not established · 200/250 OD",
    "shared":"XS170/XS169 recorded 500-vehicle exchange"},
"hong_kong":{"label":"Hong Kong","scope":"100 selected physical nodes · 111 links · 10 OD",
    "time":"30 s / model step","column":"ORACLE_R1_HK10_K1","demand":"HK10",
    "flow":"0.835215 PCE","arrival":"physical arrival t37; sink t50 is bookkeeping",
    "edges":"docs/assets/three_city_r2/data/hong_kong_construction_edges.csv",
    "path":"docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv",
    "geometry":"docs/assets/hong_kong/full_stack_r5/case/selected_physical_links.csv",
    "crosswalk":"docs/assets/three_city_r2/data/hong_kong_physical_to_routing_crosswalk.csv",
    "map":"docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png",
    "phase_i":"docs/assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_i_artificial_flow_trace.csv",
    "phase_ii":"docs/assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_ii_objective_trace.csv",
    "reference":75.03632985794819,"links":"111","positive":"69",
    "mapping":"Not reported in public evidence","residual":"Not reported in public evidence",
    "unit":"modeled PCE over finite horizon","closure":"Established · 10/10",
    "shared":"Not demonstrated"},
}


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def read(rel:str)->list[dict[str,str]]:
    with (ROOT/rel).open(newline="",encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def save(fig:plt.Figure,slug:str,fam:str,inputs:list[str],caption:str,extra:dict|None=None)->None:
    OUT.mkdir(parents=True,exist_ok=True)
    stem=f"{slug}_{FAMILY[fam]}"; target=OUT/stem
    fig.savefig(target.with_suffix(".svg"),bbox_inches="tight",metadata={"Date":None})
    fig.savefig(target.with_suffix(".png"),bbox_inches="tight",dpi=190)
    plt.close(fig)
    svg=target.with_suffix(".svg")
    svg.write_text("\n".join(x.rstrip() for x in svg.read_text(encoding="utf-8").splitlines())+"\n",encoding="utf-8")
    source={"figure_id":stem,"city":CASE[slug]["label"],"representation_family":fam,
        "scientific_status":"saved-result rendering; no solver call",
        "renderer_version":"three-city-parallel-r2","renderer_sha256":sha(Path(__file__)),
        "input_sha256":{rel:sha(ROOT/rel) for rel in sorted(set(inputs))},
        "svg_sha256":sha(svg),"png_sha256":sha(target.with_suffix(".png")),
        "caption":caption,"scientific_solver_rerun":False}
    if extra:source.update(extra)
    target.with_suffix(".source.json").write_text(json.dumps(source,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    target.with_suffix(".caption.md").write_text(caption+"\n",encoding="utf-8")


def arrow(ax,a,b,color,width=1.6,style="-|>"):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle=style,mutation_scale=10,linewidth=width,color=color,
                                 shrinkA=2,shrinkB=2,connectionstyle="arc3"))


def no_axes(ax):
    ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(False)


def graph_rows(slug:str)->list[dict[str,str]]:
    rows=read(CASE[slug]["edges"])
    if not rows or len({r["arc_id"] for r in rows})!=len(rows):raise ValueError("construction edge table invalid")
    for r in rows:
        if not(r["from_node_time_id"] and r["to_node_time_id"] and r["arc_type"]):
            raise ValueError(f"arc lacks an endpoint/type: {r['arc_id']}")
    return rows


def physical_links(slug:str,rows:list[dict[str,str]])->list[tuple[str,str,str]]:
    if slug=="hong_kong":
        cross=read(CASE[slug]["crosswalk"])
        return [(r["physical_link_id"],r["original_from_node_id"],r["original_to_node_id"]) for r in cross]
    out=[];seen=set()
    for r in rows:
        link=r["physical_link_id"]
        if r["arc_type"]=="movement" and link and link not in seen:
            out.append((link,r["from_physical_node_id"],r["to_physical_node_id"]));seen.add(link)
    return out


def draw_a(slug:str)->None:
    c=CASE[slug];rows=graph_rows(slug)
    fig=plt.figure(figsize=(13.8,8.4))
    grid=fig.add_gridspec(2,2,width_ratios=[1.35,.65],height_ratios=[.38,.62],
                         left=.055,right=.98,top=.91,bottom=.075,wspace=.13,hspace=.20)
    physical=fig.add_subplot(grid[0,0]);rule=fig.add_subplot(grid[0,1]);time=fig.add_subplot(grid[1,:])
    for ax,title in zip((physical,rule,time),("a  Directed physical-link subgraph","b  Mapping","c  Saved finite-graph cutaway")):
        no_axes(ax);ax.set_title(title,loc="left",fontweight="bold",color=INK,fontsize=11,pad=17)
    links=physical_links(slug,rows)
    chain=[links[0][1]]+[x[2] for x in links]
    x=np.linspace(.08,.92,len(chain));y=.53+.07*np.sin(np.arange(len(chain))*1.1)
    physical.set_xlim(0,1);physical.set_ylim(0,1)
    for i,(link,tail,head) in enumerate(links):
        if chain[i]!=tail or chain[i+1]!=head:raise ValueError(f"non-contiguous physical road chain: {slug} {link}")
        arrow(physical,(x[i]+.02,y[i]),(x[i+1]-.02,y[i+1]),TEAL,2)
        physical.text((x[i]+x[i+1])/2,min(y[i],y[i+1])-.10,link,ha="center",fontsize=7,color=MUTED)
    physical.scatter(x,y,s=135,facecolor="white",edgecolor=INK,zorder=3)
    for px,py,node in zip(x,y,chain):physical.text(px,py+.11,node,ha="center",fontsize=7,color=INK)
    if slug=="hong_kong":
        physical.text(.03,.14,"Only 308368 and 667532 are physical roads.\nRouting entry/exit IDs appear at right.",fontsize=7.5,color=MUTED)
    else:physical.text(.03,.14,"Only saved directed physical-link adjacencies are drawn.",fontsize=7.5,color=MUTED)
    rule.set_xlim(0,1);rule.set_ylim(0,1)
    if slug=="hong_kong":
        lines=["original road link ℓ","→ entry/exit routing states","→ movement arc at t","turn connector ≠ road","waiting keeps routing state"]
    else:lines=["physical node i","→ time-indexed state (i,t)","directed road link ℓ","→ movement arc","same state at t+1 → waiting"]
    for i,line in enumerate(lines):rule.text(.04,.82-i*.14,line,fontsize=9 if i<3 else 8,color=TEAL if "→" in line else INK)
    rule.text(.04,.07,f"{c['time']} · {c['scope']}",fontsize=7.5,color=MUTED,wrap=True)
    # Every drawn arrow below is a row of the published cutaway edge table.
    active=[r for r in rows if r["arc_type"] not in {"source_connector","sink_connector"}]
    times=sorted({int(r["from_time"]) for r in active}|{int(r["to_time"]) for r in active})
    if len(times)<4:raise ValueError("fewer than four explicit time layers")
    states=[]
    for r in active:
        for key in ("from_physical_node_id","to_physical_node_id"):
            if r[key] not in states:states.append(r[key])
    if slug=="hong_kong":
        states=["1000000076","1000000077","1000002420","1000002421"]
    else:
        states=sorted(states,key=lambda s:(chain.index(s) if s in chain else 999,s))
    xx={t:i for i,t in enumerate(times)};yy={state:len(states)-1-i for i,state in enumerate(states)}
    time.set_xlim(-.65,len(times)-.35);time.set_ylim(-1.5,len(states)+.9)
    for t in times:
        time.axvline(xx[t],color=PALE,lw=.75,zorder=0)
        time.text(xx[t],-.55,f"t{t}",ha="center",fontsize=7.5,color=MUTED)
    for state,pos in yy.items():
        lab=state if slug!="hong_kong" else {"1000000076":"308368 entry","1000000077":"308368 exit",
            "1000002420":"667532 entry","1000002421":"667532 exit"}.get(state,state)
        time.text(-.62,pos,lab,ha="left",va="center",fontsize=7,color=INK)
    for r in active:
        a=(xx[int(r["from_time"])],yy[r["from_physical_node_id"]])
        b=(xx[int(r["to_time"])],yy[r["to_physical_node_id"]])
        if a==b:raise ValueError(f"self-loop displayed without time advancement: {r['arc_id']}")
        arrow(time,a,b,COLORS[r["arc_type"]],2 if r["display_role"]=="movement" else 1.35)
        time.scatter([a[0],b[0]],[a[1],b[1]],s=16,facecolor="white",edgecolor=INK,zorder=4)
    terminals=[r for r in rows if r["arc_type"] in {"source_connector","sink_connector"}]
    term=" · ".join(f"{r['arc_id']}: t{r['from_time']}→t{r['to_time']}" for r in terminals)
    time.text(0,-1.11,"Terminal examples (saved connectors; sink horizon is bookkeeping): "+term,
              ha="left",fontsize=6.6,color=RUST)
    time.text(len(times)-1,len(states)+.5,"Nonuniform layer spacing only for legibility; arrows follow saved endpoint states.",
              ha="right",fontsize=6.8,color=MUTED)
    inputs=[c["edges"]]
    if slug=="hong_kong":inputs.append(c["crosswalk"])
    caption=(f"{c['label']}: a source-matched local subgraph of the accepted finite time-expanded graph. "
             "All displayed edges have literal arc IDs, endpoint states, types and time indices in the linked edge table. "
             "Schematic coordinates are not geographic; terminal sink time is bookkeeping, not physical waiting.")
    save(fig,slug,"A",inputs,caption,{"plotted_arc_ids":[r["arc_id"] for r in active],
        "source_edge_table":c["edges"],"time_layers":times,"aspect_policy":"native geometry; schematic graph coordinates"})


def path_rows(slug:str)->list[dict[str,str]]:
    c=CASE[slug]
    if slug=="sioux":
        index={r["arc_id"]:r for r in graph_rows(slug)}
        return [index[k] for k in ("source_XS170","xs_link19_t0","xs_link15_t2","sink_XS170_5_t6")]
    return read(c["path"])


def draw_b(slug:str)->None:
    c=CASE[slug];rows=path_rows(slug)
    if rows[0]["arc_type"]!="source_connector" or rows[-1]["arc_type"]!="sink_connector":
        raise ValueError("accepted path endpoints missing")
    fig=plt.figure(figsize=(13,4.8))
    grid=fig.add_gridspec(1,2,width_ratios=[1.05,1.35],left=.055,right=.975,top=.81,bottom=.18,wspace=.13)
    route,seq=[fig.add_subplot(grid[0,i]) for i in range(2)]
    route.set_title("a  Directed physical-link route",loc="left",fontweight="bold",fontsize=11,color=INK)
    seq.set_title("b  Ordered dynamic arcs",loc="left",fontweight="bold",fontsize=11,color=INK)
    movements=[r for r in rows if r["arc_type"]=="movement"]
    if slug=="sioux":
        no_axes(route);route.set_xlim(0,1);route.set_ylim(0,1)
        pts=[(.10,.52),(.49,.68),(.88,.50)]
        for i,r in enumerate(movements):
            arrow(route,pts[i],pts[i+1],TEAL,3)
            route.text((pts[i][0]+pts[i+1][0])/2,.42,r["physical_link_id"],ha="center",fontsize=8,color=TEAL)
        for pt,node in zip(pts,("8","6","5")):
            route.scatter([pt[0]],[pt[1]],s=65,facecolor="white",edgecolor=INK,zorder=3)
            route.text(pt[0],pt[1]+.13,"node "+node,ha="center",fontsize=8)
    else:
        geom=read(c["geometry"]);field="physical_link_id" if slug=="boston" else "link_id"
        wktfield="geometry_wkt" if slug=="boston" else "geometry"
        mapped={r[field]:r[wktfield] for r in geom}
        def xy(wkt:str):
            body=wkt[wkt.find("(")+1:wkt.rfind(")")]
            pts=[tuple(float(v) for v in part.split()[:2]) for part in body.split(",")]
            return np.asarray(pts)
        # Light bounded context, then the actual selected physical-link order.
        for wkt in mapped.values():
            a=xy(wkt);route.plot(a[:,0],a[:,1],color=PALE,lw=.65,zorder=1)
        for r in movements:
            if r["physical_link_id"] not in mapped:raise ValueError("movement link absent from physical map")
            a=xy(mapped[r["physical_link_id"]]);route.plot(a[:,0],a[:,1],color=TEAL,lw=2.4,zorder=3)
            mid=a[len(a)//2];route.scatter([mid[0]],[mid[1]],s=5,color=TEAL,zorder=4)
        start=xy(mapped[movements[0]["physical_link_id"]])[0]
        end=xy(mapped[movements[-1]["physical_link_id"]])[-1]
        route.scatter([start[0],end[0]],[start[1],end[1]],s=55,facecolor="white",edgecolor=INK,zorder=5)
        route.annotate("origin",start,xytext=(5,9),textcoords="offset points",fontsize=7)
        route.annotate("destination",end,xytext=(5,9),textcoords="offset points",fontsize=7)
        route.set_aspect("equal",adjustable="box");no_axes(route)
    seq.set_xlim(0,1);seq.set_ylim(0,1);no_axes(seq)
    display=rows if len(rows)<=9 else [*rows[:4],None,*rows[-3:]]
    seq.text(.01,.95,"arc ID",fontsize=8,fontweight="bold",color=MUTED)
    seq.text(.60,.95,"index",fontsize=8,fontweight="bold",color=MUTED)
    seq.text(.78,.95,"role",fontsize=8,fontweight="bold",color=MUTED)
    y0=.88;step=.095 if len(display)>7 else .115
    for i,r in enumerate(display):
        y=y0-i*step
        if r is None:
            seq.text(.01,y,f"… {len(rows)-7} exact intervening arcs in source table …",fontsize=8,color=MUTED)
            continue
        color=COLORS.get(r["arc_type"],MUTED)
        name=r["arc_id"]
        if len(name)>31:name=name[:28]+"…"
        seq.text(.01,y,name,fontsize=8,color=color)
        seq.text(.60,y,f"{r['from_time']}→{r['to_time']}",fontsize=8,color=INK)
        seq.text(.78,y,r["arc_type"].replace("_connector"," conn.").replace("_"," "),fontsize=7.5,color=color)
    fig.text(.055,.96,f"{c['label']} · {c['demand']} / {c['column']} · {c['flow']} · {c['time']}",
             ha="left",va="top",fontsize=10,color=INK)
    fig.text(.055,.06,c["arrival"]+". Only movement arcs map to directed physical links.",fontsize=8,color=MUTED)
    if slug=="hong_kong":fig.text(.055,.025,"Model-generated path, not an UrbanNav/GPS observation. Node fields are turn-expanded routing states, not original road intersections.",fontsize=7.5,color=RUST)
    caption=(f"{c['label']}: one accepted generated column ({c['demand']}, {c['column']}, {c['flow']}). "
             f"One time index is {c['time']}. {c['arrival']}. The ordered source table gives all arc IDs and link mappings."
             +( " This specifically approved Hong Kong excerpt is model-generated, not an observed trajectory." if slug=="hong_kong" else ""))
    inputs=[c["path"]]+([c["geometry"]] if c.get("geometry") else [])
    save(fig,slug,"B",inputs,caption,{"column_id":c["column"],"demand_id":c["demand"],
         "time_unit":c["time"],"arc_count":len(rows),"sink_bookkeeping_note":c["arrival"],
         "disclosure_status":"APPROVED_EXACT_HK10_PATH" if slug=="hong_kong" else "ACCEPTED_PUBLIC"})


def image_native(ax,rel:str)->None:
    img=plt.imread(ROOT/rel)
    ax.imshow(img,interpolation="nearest",aspect="equal")
    ax.set_anchor("C");ax.axis("off")


def draw_c(slug:str)->None:
    c=CASE[slug];fig=plt.figure(figsize=(13.8,8.1))
    grid=fig.add_gridspec(2,1,height_ratios=[.30,.70],left=.055,right=.98,top=.91,bottom=.07,hspace=.12)
    audit=fig.add_subplot(grid[0,0]);audit.axis("off")
    audit.set_title("a  Movement-only aggregation audit",loc="left",fontweight="bold",fontsize=11,color=INK)
    audit.text(.02,.75,r"$f_{\ell}=\sum_{a:\,\mathrm{type}(a)=\mathrm{movement},\,p(a)=\ell}x_a$",fontsize=13,color=INK)
    fields=[("Physical links",c["links"]),("Positive-flow links",c["positive"]),
            ("Mapping failures",c["mapping"]),("Reconstruction residual",c["residual"]),
            ("Flow units",c["unit"])]
    for i,(k,v) in enumerate(fields):
        x=.02+i*.195
        audit.text(x,.43,k,fontsize=8,color=MUTED)
        audit.text(x,.28,v,fontsize=8.5,color=INK,wrap=True)
    if slug=="sioux":
        inner=grid[1,0].subgridspec(1,2,wspace=.08)
        for i,(key,label) in enumerate((("map","b  200 OD"),("map_250","c  250 OD"))):
            ax=fig.add_subplot(inner[0,i]);image_native(ax,c[key]);ax.set_title(label,loc="left",fontsize=10,fontweight="bold",color=INK)
        inputs=[c["map"],c["map_250"]]
    else:
        ax=fig.add_subplot(grid[1,0]);image_native(ax,c["map"])
        ax.set_title("b  Accepted final physical-link movement-flow map",loc="left",fontsize=10,fontweight="bold",color=INK)
        inputs=[c["map"]]
    fig.text(.055,.025,"Nonphysical source, sink, zone and turn connectors are not counted as roads or physical-link flow.",fontsize=8,color=MUTED)
    caption=(f"{c['label']}: saved final movement-arc flow aggregated by persistent physical-link ID. "
             "The same five audit fields are shown for all cities; unavailable released values are explicitly not reported. "
             "Accepted maps retain their original aspect ratios."
             +(" Sioux Falls uses the accepted deterministic schematic layout, not geographic coordinates."
               if slug=="sioux" else ""))
    save(fig,slug,"C",inputs,caption,{"audit_fields":dict(fields),"image_aspect_policy":"native; no anisotropic resampling"})


def trace(rel:str,xcol:str,ycol:str)->tuple[np.ndarray,np.ndarray]:
    rows=read(rel)
    return np.array([float(r[xcol]) for r in rows]),np.array([float(r[ycol]) for r in rows])


def draw_d(slug:str)->None:
    c=CASE[slug]
    fig,ax=plt.subplots(2,3,figsize=(15.3,8.6))
    fig.subplots_adjust(left=.055,right=.975,top=.88,bottom=.11,hspace=.38,wspace=.28)
    titles=("a  Saved finite-graph arcs","b  One generated column","c  Phase-I artificial flow",
            "d  Shared-capacity evidence","e  Phase-II objective / LP reference","f  Final physical projection")
    for a,title in zip(ax.flat,titles):
        a.set_title(title,loc="left",fontsize=10,fontweight="bold",color=INK,pad=12)
        a.spines[["top","right"]].set_visible(False)
        a.tick_params(labelsize=7)
    # A: actual cutaway arc times and roles, no nested composite.
    edges=[r for r in graph_rows(slug) if r["arc_type"] not in {"source_connector","sink_connector"}]
    for i,r in enumerate(edges):
        ax[0,0].plot([int(r["from_time"]),int(r["to_time"])],[i,i],color=COLORS[r["arc_type"]],lw=2.2,marker="o",ms=3)
    ax[0,0].set_yticks(range(len(edges)),[r["arc_id"][:18] for r in edges],fontsize=6)
    ax[0,0].set_xlabel("model time index",fontsize=8)
    # B: selected physical-link order, not a miniature full route poster.
    movements=[r for r in path_rows(slug) if r["arc_type"]=="movement"]
    ids=[r["physical_link_id"] for r in movements]
    if len(ids)>9:ids=[*ids[:4],"…",*ids[-4:]]
    ax[0,1].plot(range(len(ids)),[0]*len(ids),color=TEAL,lw=2,marker="o",ms=5)
    for i,label in enumerate(ids):ax[0,1].text(i,.08,label,ha="center",fontsize=6,rotation=35)
    ax[0,1].set_ylim(-.3,.48);ax[0,1].set_xlim(-.5,len(ids)-.5);ax[0,1].set_yticks([]);ax[0,1].set_xticks([])
    ax[0,1].set_xlabel(f"{c['demand']} · {c['flow']}",fontsize=8)
    # C/E: direct saved CSV plotting, not pasted multi-panel images.
    xi,yi=trace(c["phase_i"],"round","artificial_flow" if slug=="boston" else "total_artificial_flow")
    ax[0,2].plot(xi,yi,color=TEAL,lw=1.8);ax[0,2].scatter([xi[-1]],[yi[-1]],color=TEAL,s=20)
    example="200-OD example · " if slug=="sioux" else ""
    ax[0,2].set_xlabel(example+"Phase-I round",fontsize=8)
    ax[0,2].set_ylabel("artificial flow ("+("PCE" if slug=="hong_kong" else "model vehicles")+")",fontsize=8)
    if slug=="boston":
        xii,yii=trace(c["phase_ii"],"round","objective")
    else:xii,yii=trace(c["phase_ii"],"round","objective_value")
    ax[1,1].plot(xii,yii,color=TEAL,lw=1.8,marker="o",ms=3)
    ax[1,1].axhline(c["reference"],color=RUST,lw=1.2,ls="--")
    ax[1,1].set_xlabel(example+"Phase-II round",fontsize=8);ax[1,1].set_ylabel("vehicle-minutes",fontsize=8)
    # D: a deliberately bounded mechanism panel.
    event=ax[1,0];event.spines[["left","bottom"]].set_visible(False)
    if slug=="hong_kong":
        event.set_xticks([]);event.set_yticks([])
        event.text(.05,.62,"Not demonstrated",transform=event.transAxes,fontsize=16,color=MUTED)
        event.text(.05,.46,"No accepted before/after cross-OD event",transform=event.transAxes,fontsize=8,color=MUTED)
    elif slug=="boston":
        record=read(c["event"])
        # The public table records B07/B09/B10 artificial-flow changes.
        vals=[]
        for r in record:
            key=next((r[k] for k in ("demand_id","od_id","demand") if k in r),None)
            change=next((r[k] for k in ("delta","artificial_flow_change","artificial_change","delta_artificial_flow") if k in r),None)
            if key in {"B07","B09","B10"} and change is not None:vals.append((key,float(change)))
        if {x[0] for x in vals}!={"B07","B09","B10"}:raise ValueError("Boston saved B07/B09/B10 event rows missing")
        categories=[x[0] for x in vals];changes=[x[1] for x in vals]
        event.barh(categories,changes,color=[TEAL if v<0 else RUST for v in changes],height=.55)
        event.axvline(0,color=INK,lw=.8);event.set_xlabel("Round-1 Δ artificial flow (model vehicles)",fontsize=8)
        event.set_xlim(-1.5,1.5);event.set_xticks([-1.5,-1,-.5,0,.5,1,1.5]);event.set_yticks(range(len(categories)),categories)
        for i,v in enumerate(changes):event.text(v+(.04 if v>=0 else -.04),i,f"{v:+.3f}",
            ha="left" if v>=0 else "right",va="center",fontsize=8,color=INK)
        event.spines["bottom"].set_visible(True);event.tick_params(labelsize=8)
    else:
        record=read(c["event"])
        before=next(r for r in record if r["case"]=="200_od" and r["stage"]=="before")
        after=next(r for r in record if r["case"]=="200_od" and r["stage"]=="after")
        categories=["XS170","XS169"]
        changes=[float(after["xs170_on_arc"])-float(before["xs170_on_arc"]),
                 float(after["xs169_on_arc"])-float(before["xs169_on_arc"])]
        event.barh(categories,changes,color=[TEAL,RUST],height=.55)
        event.axvline(0,color=INK,lw=.8);event.set_xlabel("200-OD Δ use of xs_link21_t1 (model vehicles)",fontsize=8)
        event.set_xlim(-650,650);event.set_xticks([-500,-250,0,250,500]);event.set_yticks(range(2),categories)
        for i,v in enumerate(changes):event.text(v+(18 if v>=0 else -18),i,f"{v:+.0f}",
            ha="left" if v>=0 else "right",va="center",fontsize=8,color=INK)
        event.spines["bottom"].set_visible(True);event.tick_params(labelsize=8)
    # F: physical-link count + qualified closure label; full map is in family C.
    final=ax[1,2];final.spines[["left","bottom"]].set_visible(False)
    final.set_xticks([]);final.set_yticks([])
    final.text(.04,.72,f"{c['links']} directed physical links",transform=final.transAxes,fontsize=13,color=INK)
    final.text(.04,.54,(f"{c['positive']} positive-flow links" if slug!="sioux" else
                         "Positive-flow links: not reported in released summary"),
               transform=final.transAxes,fontsize=10,color=TEAL)
    final.text(.04,.29,"CG pricing closure: "+c["closure"],transform=final.transAxes,fontsize=9,color=MUTED)
    final.text(.04,.15,"Full saved-result map: separate family C",transform=final.transAxes,fontsize=8,color=MUTED)
    banner=("200-OD plotted traces; 250-OD reference retained separately" if slug=="sioux" else c["scope"])
    fig.text(.055,.965,c["label"]+" · finite saved-result sequence · "+banner,fontsize=13,color=INK,fontweight="bold",va="top")
    scope_note={"boston":"a/b: Boston 10-OD cutaway and B07 column · c/e: same 10-OD CG traces · d: round-1 B07/B09/B10 · f: 125-link projection.",
                "sioux":"a/b: saved XS170 cutaway · c/e: 200-OD traces only · d: 200-OD recorded exchange (also documented for 250 OD) · f: 200/250 summary.",
                "hong_kong":"a/b: HK10 cutaway and model-generated column · c/e: unchanged 10-OD R5 CG · d: no accepted event · f: 111-link projection."}[slug]
    fig.text(.055,.045,scope_note,fontsize=7.7,color=MUTED)
    inputs=[c["edges"],c["path"],c["phase_i"],c["phase_ii"]]+([c["event"]] if c.get("event") else [])
    caption=(f"{c['label']}: six saved-data panels in a shared order. {scope_note} "
             f"The full map and complete path remain in standalone figures; CG independent pricing closure is {c['closure'].lower()}. "
             "No scientific solver was rerun.")
    save(fig,slug,"D",inputs,caption,{"panel_order":list(titles),"nested_posters":False,
        "time_unit":c["time"],"shared_capacity_status":c["shared"],
        "panel_instance_scope":scope_note,
        "capacity_bar_categories":categories if slug!="hong_kong" else [],
        "capacity_bar_changes":changes if slug!="hong_kong" else [],
        "capacity_bar_unit":"model vehicles" if slug!="hong_kong" else "not applicable",
        "disclosure_status":"APPROVED_EXACT_HK10_PATH" if slug=="hong_kong" else "ACCEPTED_PUBLIC"})


def main()->None:
    parser=argparse.ArgumentParser(description="Render saved-data three-city figure families only")
    parser.add_argument("--city",choices=CASE,action="append",help="city to render; default all")
    parser.add_argument("--family",choices=FAMILY,action="append",help="family to render; default A/B/C/D")
    args=parser.parse_args()
    selected_cities=args.city or list(CASE)
    selected_families=args.family or list(FAMILY)
    draw={"A":draw_a,"B":draw_b,"C":draw_c,"D":draw_d}
    for slug in selected_cities:
        for family in selected_families:draw[family](slug)
    print(f"Rendered {len(selected_cities)*len(selected_families)} R2 source-matched SVG/PNG families without a solver call")


if __name__=="__main__":main()
