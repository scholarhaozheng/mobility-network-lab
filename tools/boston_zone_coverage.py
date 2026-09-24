"""Render source H3-zone production/attraction for a selected Boston OD panel."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path


def rows(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def ring(wkt):
    if not wkt.startswith("POLYGON ((") or "))" not in wkt:return []
    try:
        return [tuple(float(x) for x in pair.strip().split()[:2])
                for pair in wkt.split("((",1)[1].split("))",1)[0].split(",")]
    except (ValueError,IndexError):return []


def main():
    started=time.perf_counter()
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--panel",required=True,type=Path)
    ap.add_argument("--zones",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--tier-label",required=True)
    a=ap.parse_args()
    out=a.output.resolve()
    for src in (a.panel.resolve(),a.zones.resolve()):
        if out==src or src in out.parents or out in src.parents:raise ValueError("source/output overlap")
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty output")
    panel=rows(a.panel)
    zones={r["zone_id"]:r for r in rows(a.zones) if r.get("zone_level")=="fine"}
    production=defaultdict(float);attraction=defaultdict(float)
    for r in panel:
        o,d=r["o_zone_id"],r["d_zone_id"]
        if o not in zones or d not in zones:raise ValueError("selected zone absent from supplied zone.csv")
        q=float(r["person_trips_midday_od"])
        if not math.isfinite(q) or q<0:raise ValueError("invalid person mass")
        production[o]+=q;attraction[d]+=q
    out.mkdir(parents=True)
    table=[]
    for zid,z in sorted(zones.items()):
        table.append({"zone_id":zid,"centroid_lon":z["centroid_lon"],"centroid_lat":z["centroid_lat"],
                      "production_person_midday":production.get(zid,0.0),
                      "attraction_person_midday":attraction.get(zid,0.0),
                      "selected_origin":int(zid in production),"selected_destination":int(zid in attraction)})
    with (out/"source_zone_coverage.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    factor=111.32*math.cos(math.radians(42.35))
    def xy(lon,lat):return ((lon+71.08)*factor,(lat-42.35)*111.32)
    outlines=[]
    for z in zones.values():
        coords=ring(z.get("clipped_geometry_wkt", ""))
        if len(coords)>=3:outlines.append([xy(*p) for p in coords])
    points={zid:xy(float(z["centroid_lon"]),float(z["centroid_lat"])) for zid,z in zones.items()}
    fig,axes=plt.subplots(1,2,figsize=(13.5,7),dpi=160,sharex=True,sharey=True)
    fig.patch.set_facecolor("white")
    total=sum(production.values())
    for ax,field,color,title in ((axes[0],production,"#087e8b","Selected origins · production"),
                                 (axes[1],attraction,"#dd8b32","Selected destinations · attraction")):
        ax.set_facecolor("#f7fafb")
        if outlines:ax.add_collection(LineCollection(outlines,colors="#d5e2e6",linewidths=.6,zorder=1))
        ax.scatter([x for x,y in points.values()],[y for x,y in points.values()],s=3,c="#aabcc4",zorder=2)
        active=[(points[zid],q) for zid,q in field.items() if q>0]
        ax.scatter([p[0][0] for p in active],[p[0][1] for p in active],
                   s=[18+135*math.sqrt(q/max(total,1e-12)) for _,q in active],c=color,
                   alpha=.82,edgecolors="white",linewidths=.4,zorder=3)
        ax.set_title(title,loc="left",fontsize=13,color="#102c3e")
        ax.set_aspect("equal")
        ax.set_xlabel("East–west distance from −71.08° (km)")
    axes[0].set_ylabel("North–south distance from 42.35° (km)")
    fig.suptitle(f"Boston HBW midday | {a.tier_label} source-zone coverage",fontsize=17,x=.07,ha="left",color="#102c3e")
    panel_hash=sha(a.panel)
    fig.text(.07,.025,f"{len(panel):,} selected source OD · {total:,.3f} saved person trips · panel {panel_hash[:12]} · expansion factor 1 · no empirical validation\n"
             f"Production/attraction bubbles use square-root area; H3 zones are distinct from physical road access nodes.",
             fontsize=8,color="#536b78")
    fig.subplots_adjust(left=.07,right=.96,top=.87,bottom=.14,wspace=.08)
    fig.savefig(out/"source_zone_coverage.png",dpi=160)
    fig.savefig(out/"source_zone_coverage.svg")
    plt.close(fig)
    info={"status":"PLOTTED","tier_label":a.tier_label,"source_od":len(panel),
          "source_person_mass":total,"distinct_origin_zones":len(production),
          "distinct_destination_zones":len(attraction),"all_fine_zones":len(zones),
          "panel_sha256":panel_hash,"zones_sha256":sha(a.zones),
          "source_table_sha256":sha(out/"source_zone_coverage.csv"),
          "plot_seconds":time.perf_counter()-started}
    temporary=out/"plot.json.partial"
    temporary.write_text(json.dumps(info,indent=2),encoding="utf-8")
    temporary.replace(out/"plot.json")
    print(json.dumps(info))


if __name__=="__main__":main()
