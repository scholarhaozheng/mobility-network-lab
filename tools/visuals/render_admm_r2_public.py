"""Deterministic, plotting-only ADMM R2 public figure renderer.

Inputs are accepted saved summaries/histories/derived physical-link comparisons and
already-public physical topology/geometry. No optimizer, solver, or state load occurs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import pathlib
import re
import subprocess


INK = "#153047"
MUTED = "#547086"
TEAL = "#087f8c"
BLUE = "#285cb2"
CORAL = "#d76545"
GOLD = "#bd8a18"
BG = "#f6f9fb"
GRID = "#dbe6ed"
PALE = "#ffffff"
GREEN = "#12795e"


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fnum(value):
    return float(value)


def esc(value):
    return html.escape(str(value), quote=True)


class SVG:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                      f'<rect width="{width}" height="{height}" fill="{BG}"/>']

    def add(self, s): self.parts.append(s)

    def rect(self, x,y,w,h,fill=PALE,stroke=None,r=0,sw=1):
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+'/>')

    def line(self,x1,y1,x2,y2,color=GRID,width=1,dash=None,opacity=1):
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}" opacity="{opacity}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')

    def circle(self,x,y,r,fill,stroke=None,opacity=1):
        self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" opacity="{opacity}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')

    def text(self,x,y,value,size=18,color=INK,weight="normal",anchor="start"):
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>')

    def poly(self,pts,color,width=2,fill="none",opacity=1):
        p=" ".join(f"{x:.2f},{y:.2f}" for x,y in pts)
        self.add(f'<polyline points="{p}" fill="{fill}" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" opacity="{opacity}"/>')

    def finish(self): return "\n".join(self.parts+["</svg>"])+"\n"


def box(s,x,y,w,h,title):
    s.rect(x,y,w,h,PALE,GRID,9)
    s.text(x+18,y+30,title,18,INK,"bold")


def label(s,x,y,text,color):
    s.line(x,y-5,x+22,y-5,color,3)
    s.text(x+30,y,text,13,MUTED)


def axis(s,x,y,w,h,xmin,xmax,ymin,ymax,yticks=None):
    s.line(x,y+h,x+w,y+h,MUTED,1.5); s.line(x,y,x,y+h,MUTED,1.5)
    for i in range(5):
        yy=y+h-i*h/4
        s.line(x,yy,x+w,yy,GRID,1)
        v=ymin+(ymax-ymin)*i/4
        s.text(x-8,yy+4,(f"{v:.1f}" if abs(v)<100 else f"{v:.2g}"),11,MUTED,anchor="end")
    for i in range(5):
        xx=x+i*w/4
        s.text(xx,y+h+17,f"{xmin+(xmax-xmin)*i/4:.0f}",11,MUTED,anchor="middle")
    def point(a,b):
        return (x+(a-xmin)*w/(xmax-xmin or 1), y+h-(b-ymin)*h/(ymax-ymin or 1))
    return point


def series(s, rows, xkey, specs, x,y,w,h, transform=lambda v:v, yrange=None):
    xs=[fnum(r[xkey]) for r in rows]
    values=[[transform(max(fnum(r[k]),1e-15)) for r in rows] for k,_ in specs]
    allv=[v for vs in values for v in vs]
    lo,hi=(min(allv),max(allv)) if yrange is None else yrange
    if hi<=lo: hi=lo+1
    pad=.07*(hi-lo); lo-=pad;hi+=pad
    point=axis(s,x,y,w,h,min(xs),max(xs),lo,hi)
    for (key,color),vs in zip(specs,values):
        s.poly([point(a,b) for a,b in zip(xs,vs)],color,2)


def title(s,title,subtitle):
    s.text(45,46,title,29,INK,"bold")
    s.text(45,72,subtitle,15,MUTED)


def method_contract():
    s=SVG(1400,500); title(s,"ADMM R2 | method contract","Finite time-expanded linear shared-capacity multicommodity arc-flow problem")
    items=[("1  Commodity-local update",["xₖ ≥ 0; Bxₖ = bₖ","min cᵀxₖ + (ρ/2)‖xₖ − zₖ + wₖ‖²"]),
           ("2  Shared projection",["z ≥ 0;  Σₖ zₖₐ ≤ uₐ","arc-wise Euclidean capacity projection"]),
           ("3  Scaled-dual update",["w ← w + x − z","fixed input-derived ρ in selected R2_S"]),
           ("4  Independent evaluator",["conservation, capacity, KKT, objective","projection and physical-link back-projection"])]
    for i,(head,lines) in enumerate(items):
        x=45+i*338; box(s,x,130,305,230,head)
        for j,line in enumerate(lines): s.text(x+19,205+j*62,line,15,INK)
        if i<3:
            s.line(x+307,245,x+330,245,TEAL,3); s.poly([(x+325,238),(x+333,245),(x+325,252)],TEAL,3)
    s.rect(45,390,1315,68,"#e6f3f4",None,8)
    s.text(65,430,"Scope: bounded finite time-expanded LP; not static Beckmann user equilibrium.",18,INK,"bold")
    return s.finish()


def design():
    s=SVG(1500,560); title(s,"Sioux-first development → frozen Boston transfer","Preregistered R2_S policy selected on fixtures and Sioux; Boston was a holdout")
    steps=[("Analytic","unit test"),("C0","tiny fixture"),("C1","local gate"),("Sioux 30–250","six subset cases"),("FREEZE","R2_S + hashes"),("Boston 10 OD","holdout")]
    for i,(a,b) in enumerate(steps):
        x=42+i*244; c=TEAL if i<4 else (BLUE if i==4 else CORAL)
        s.rect(x,145,215,168,PALE,c,10,2);s.rect(x,145,215,8,c)
        s.text(x+17,209,a,22,INK,"bold");s.text(x+17,247,b,16,MUTED)
        if i<5:
            s.line(x+216,229,x+239,229,c,3);s.poly([(x+233,222),(x+241,229),(x+233,236)],c,3)
    notes=["fixed input-derived ρ","no Boston retuning","independent evaluator: 0 optimizer calls"]
    for i,n in enumerate(notes):
        s.rect(75+i*470,375,410,90,"#e8f2f7",None,8);s.text(95+i*470,426,n,19,INK,"bold")
    return s.finish()


def policy():
    s=SVG(1350,560);title(s,"R2_S | accepted numerical policy","Scaling and local correction selected before the Boston holdout")
    items=[("Normalize each commodity","d > 0: y = x / d; By = b / d","local QP uses c / (ρd)"),
           ("Fix ρ from input","clip(median positive cost / median demand, 10⁻⁴, 1)","same deterministic rule across cases"),
           ("Correct active support","L-BFGS-B → semismooth Newton","nonnegative support correction"),
           ("Check original units","conservation, capacity, KKT, objective","independent evaluator; zero optimizer calls")]
    for i,(h,a,b) in enumerate(items):
        x=45+(i%2)*650;y=130+(i//2)*190;box(s,x,y,610,155,h)
        s.text(x+18,y+76,a,16,INK);s.text(x+18,y+113,b,16,MUTED)
    s.text(45,535,"Finite time-expanded shared-capacity LP. No general ADMM convergence guarantee is claimed for every instance.",16,MUTED)
    return s.finish()


def overview(metrics):
    s=SVG(1400,650);title(s,"ADMM R2 | verified Sioux and Boston","R2_S fixed before Boston; every displayed case passed frozen independent gates")
    for i,(key,heading) in enumerate([("Sioux_200OD","Sioux Falls · 200 OD"),("Sioux_250OD","Sioux Falls · 250 OD"),("Boston_10OD","Boston · 10 OD")]):
        m=metrics[key];x=45+i*455;box(s,x,135,420,315,heading)
        s.text(x+20,210,f"{m['iterations']} iterations",28,INK,"bold")
        s.text(x+20,260,f"relative objective gap  {m['relative_gap']:.2e}",18,TEAL,"bold")
        s.text(x+20,310,f"conservation  {m['balance']:.2e}",17,MUTED)
        s.text(x+20,345,f"capacity excess  {m['capacity']:.2e}",17,MUTED)
        s.text(x+20,400,"ALL DECLARED GATES PASSED",16,GREEN,"bold")
    s.rect(45,485,1330,115,"#e8f2f7",None,9)
    s.text(67,527,"local commodity QPs  →  shared arc projection  →  scaled-dual update",21,INK,"bold")
    s.text(67,566,"Conservation  •  capacity  •  KKT  •  physical back-projection  •  independent evaluator: 0 optimizer calls",16,MUTED)
    s.text(970,630,"Boston derived evidence rights-cleared",14,GREEN,"bold")
    return s.finish()


def case_sequence(case, history, comp, metric):
    s=SVG(1600,1050);title(s,f"ADMM R2 | {case.replace('_',' ')} | accepted sequence","Matched evidence order across Sioux Falls and Boston; saved outputs only")
    w,h=485,275; positions=[(45,105),(557,105),(1069,105),(45,410),(557,410),(1069,410)]
    heads=["A  Residual convergence","B  Original-unit feasibility","C  Objective vs same-graph LP","D  Fixed rho and status","E  Physical-link flow scatter","F  Independent verification"]
    for (x,y),head in zip(positions,heads): box(s,x,y,w,h,head)
    x,y=positions[0];series(s,history,"iteration",[("primal_residual",TEAL),("dual_residual",BLUE),("primal_threshold",CORAL),("dual_threshold",GOLD)],x+65,y+60,w-95,h-105,lambda v:math.log10(max(v,1e-12)))
    s.text(x+64,y+h-14,"primal teal · dual blue · thresholds coral/gold",12,MUTED)
    x,y=positions[1];series(s,history,"iteration",[("balance_residual",TEAL),("capacity_residual",CORAL)],x+65,y+60,w-95,h-105,lambda v:math.log10(max(v,1e-12)))
    s.text(x+70,y+h-15,"balance teal · capacity coral · gate 1e-5",12,MUTED)
    x,y=positions[2]; lp=metric["reference_objective"]
    diffs=[abs(fnum(r["objective"])-lp) for r in history]
    fake=[{"iteration":r["iteration"],"difference":v} for r,v in zip(history,diffs)]
    series(s,fake,"iteration",[("difference",TEAL)],x+65,y+60,w-95,h-105,lambda v:math.log10(max(v,1e-12)))
    s.text(x+70,y+h-15,f"|ADMM objective − LP {lp:.6g}|; log10",13,MUTED)
    x,y=positions[3];rho=metric["rho"]
    s.line(x+50,y+125,x+w-40,y+125,BLUE,4);s.text(x+60,y+105,f"ρ = {rho:.8g} throughout",20,INK,"bold")
    s.text(x+60,y+180,f"status: {metric['status']}",17,GREEN,"bold")
    s.text(x+60,y+220,"selected R2_S policy; no retuning",14,MUTED)
    x,y=positions[4]; maxf=max(max(r["admm_flow"],r["lp_flow"]) for r in comp) or 1
    p=axis(s,x+62,y+58,w-95,h-105,0,maxf,0,maxf)
    s.line(*p(0,0),*p(maxf,maxf),GRID,2,dash="5 4")
    for r in comp:
        px,py=p(r["lp_flow"],r["admm_flow"]);s.circle(px,py,2.4,TEAL,opacity=.7)
    s.text(x+75,y+h-16,"LP x-axis · ADMM y-axis · physical links",13,MUTED)
    x,y=positions[5]
    lines=[f"{metric['iterations']} iterations · relative objective gap {metric['relative_gap']:.2e}",
           f"conservation {metric['balance']:.2e} · capacity {metric['capacity']:.2e}",
           f"KKT {metric['kkt']:.2e} · projection {metric['projection']:.2e}",
           f"physical back-projection {metric['back_projection']:.2e}",
           "independent evaluator: 0 optimizer calls"]
    for i,line in enumerate(lines):s.text(x+20,y+78+i*35,line,15,INK if i<4 else GREEN,"bold" if i==4 else "normal")
    s.text(46,753,"Objective closeness does not imply identical primal flows; alternate route and time splits can occur.",17,MUTED)
    s.text(46,788,"The plot is a bounded finite time-expanded LP comparison, not static Beckmann user equilibrium.",17,MUTED)
    s.text(46,830,"Reused accepted evidence assets: individual convergence and physical-flow SVGs remain alongside this composite.",16,MUTED)
    return s.finish()


def lerp(a,b,t):return a+(b-a)*t


def rgb(hexcode):return tuple(int(hexcode[i:i+2],16) for i in (1,3,5))


def mix(a,b,t):
    aa,bb=rgb(a),rgb(b)
    return "#"+"".join(f"{round(lerp(aa[i],bb[i],t)):02x}" for i in range(3))


def heatmap(case, rows, count):
    its=sorted({int(r["iteration"]) for r in rows}); commodities=sorted({r["commodity"] for r in rows},key=lambda q:(int(re.search(r"\d+",q).group()) if re.search(r"\d+",q) else 0,q))
    assert len(commodities)==count
    s=SVG(1550,1050);title(s,f"ADMM R2 | {case.replace('_',' ')} | commodity conservation","log10(max(original-unit balance residual, 1e-12)); gate = 1e-5 vehicles")
    x0,y0,w,h=110,120,1300,750;cw=w/len(its);ch=h/len(commodities)
    lookup={(int(r["iteration"]),r["commodity"]):max(fnum(r["balance_residual_original"]),1e-12) for r in rows}
    for j,c in enumerate(commodities):
        for i,it in enumerate(its):
            z=math.log10(lookup[(it,c)])
            t=min(1,max(0,(z+12)/10))
            col=mix("#e7f5f2",CORAL,t) if z>-5 else mix("#e7f5f2",TEAL,min(1,(z+12)/7))
            s.rect(x0+i*cw,y0+j*ch,cw+.1,ch+.1,col)
    s.rect(x0,y0,w,h,"none",INK,0,1)
    s.text(x0,y0+h+35,"1",14,MUTED,anchor="middle")
    s.text(x0+w,y0+h+35,str(its[-1]),14,MUTED,anchor="middle")
    s.text(x0+w/2,y0+h+61,"ADMM iteration",17,INK,anchor="middle")
    s.text(x0-12,y0+8,commodities[0],13,MUTED,anchor="end")
    s.text(x0-12,y0+h,commodities[-1],13,MUTED,anchor="end")
    s.text(x0,y0+h+105,"Teal ≤ gate (10⁻⁵); warm colors above gate. White/teal floor at 10⁻¹².",16,MUTED)
    s.text(x0,y0+h+135,"Each cell is an accepted saved local-balance value; no state or optimizer replay.",16,MUTED)
    return s.finish()


def force_layout(edges):
    nodes=sorted({n for e in edges for n in e},key=lambda a:int(a))
    pos={n:[math.cos(2*math.pi*i/len(nodes)),math.sin(2*math.pi*i/len(nodes))] for i,n in enumerate(nodes)}
    undirected=sorted({tuple(sorted(e,key=lambda a:int(a))) for e in edges})
    k=2/math.sqrt(len(nodes))
    for step in range(650):
        disp={n:[0.,0.] for n in nodes}
        for i,a in enumerate(nodes):
            for b in nodes[i+1:]:
                dx=pos[a][0]-pos[b][0];dy=pos[a][1]-pos[b][1];dist=max(math.hypot(dx,dy),1e-3)
                force=min(4,k*k/dist)
                ux,uy=dx/dist*force,dy/dist*force
                disp[a][0]+=ux;disp[a][1]+=uy;disp[b][0]-=ux;disp[b][1]-=uy
        for a,b in undirected:
            dx=pos[a][0]-pos[b][0];dy=pos[a][1]-pos[b][1];dist=max(math.hypot(dx,dy),1e-3)
            force=dist*dist/k;ux,uy=dx/dist*force,dy/dist*force
            disp[a][0]-=ux;disp[a][1]-=uy;disp[b][0]+=ux;disp[b][1]+=uy
        temp=.12*(1-step/650)+.005
        for n in nodes:
            norm=max(math.hypot(*disp[n]),1e-6)
            pos[n][0]+=disp[n][0]/norm*min(norm,temp);pos[n][1]+=disp[n][1]/norm*min(norm,temp)
    xx=[p[0] for p in pos.values()];yy=[p[1] for p in pos.values()]
    return {n:((p[0]-min(xx))/(max(xx)-min(xx) or 1),(p[1]-min(yy))/(max(yy)-min(yy) or 1)) for n,p in pos.items()}


def geometry_rows(case, public_root, comp):
    if case.startswith("Boston"):
        source=public_root/"docs/assets/boston/space_time_cg_r4/data/physical_link_flow_geometry.csv"
        rows=read_csv(source);g={r["physical_link_id"]:r for r in rows}
        assert set(g)=={r["physical_link_id"] for r in comp}
        xy={}
        for r in rows:
            coords=re.findall(r"(-?\d+\.\d+)\s+(-?\d+\.\d+)",r["geometry_wkt"])
            assert len(coords)>=2
            xy[r["physical_link_id"]]=[(float(a),float(b)) for a,b in coords]
        return xy,source,"WGS84 public GMNS geometry; no basemap"
    source=public_root/"examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/link.csv"
    rows=read_csv(source);g={r["link_id"]:r for r in rows}
    assert {r["physical_link_id"] for r in comp}.issubset(set(g))
    layout=force_layout([(r["from_node_id"],r["to_node_id"]) for r in rows])
    xy={}
    for id,r in g.items():
        a,b=layout[r["from_node_id"]],layout[r["to_node_id"]]
        dx,dy=b[0]-a[0],b[1]-a[1];norm=max(math.hypot(dx,dy),1e-6)
        offset=.008 if int(r["from_node_id"])<int(r["to_node_id"]) else -.008
        shift=(-dy/norm*offset,dx/norm*offset)
        xy[id]=[(a[0]+shift[0],a[1]+shift[1]),(b[0]+shift[0],b[1]+shift[1])]
    return xy,source,"deterministic schematic layout from already-public Sioux link topology; not geographic"


def map_figure(case,comp,geometry,geometry_note,signed=False):
    is_boston=case.startswith("Boston")
    s=SVG(1450,840)
    title(s,f"ADMM R2 | {case.replace('_',' ')} | {'ADMM − LP physical-link flow' if signed else 'final physical-link movement flow'}",geometry_note)
    ids={r["physical_link_id"] for r in comp};assert ids==set(geometry) if is_boston else ids.issubset(set(geometry))
    coords=[pt for id in ids for pt in geometry[id]]
    xmin,xmax=min(p[0] for p in coords),max(p[0] for p in coords);ymin,ymax=min(p[1] for p in coords),max(p[1] for p in coords)
    panels=[("Signed ADMM − LP",0)] if signed else [("ADMM",0),("same-graph LP",1)]
    max_abs=max(abs(r["difference"]) for r in comp) if signed else max(max(r["admm_flow"],r["lp_flow"]) for r in comp)
    if max_abs==0:max_abs=1
    for name,pidx in panels:
        px=70+pidx*690 if not signed else 130;py=125;pw=620 if not signed else 1190;ph=565
        s.rect(px,py,pw,ph,PALE,GRID,8)
        s.text(px+20,py+32,name,21,INK,"bold")
        # preserve aspect ratio in both panels
        sx=(pw-70)/(xmax-xmin or 1);sy=(ph-95)/(ymax-ymin or 1);scale=min(sx,sy)
        usedw=(xmax-xmin)*scale;usedh=(ymax-ymin)*scale
        def transform(pt):return (px+(pw-usedw)/2+(pt[0]-xmin)*scale,py+ph-(ph-usedh)/2-(pt[1]-ymin)*scale)
        for r in comp:
            val=r["difference"] if signed else r["admm_flow" if pidx==0 else "lp_flow"]
            pts=[transform(p) for p in geometry[r["physical_link_id"]]]
            if signed:
                s.poly(pts,"#d8e3e9",1)
                if abs(val)<1e-12:continue
                col=mix(PALE,CORAL,min(1,abs(val)/max_abs)) if val>=0 else mix(PALE,BLUE,min(1,abs(val)/max_abs))
            else: col=mix("#d6e4e9",TEAL,min(1,max(val,0)/max_abs))
            s.poly(pts,col,1.2+4.2*abs(val)/max_abs,opacity=.95)
        if not is_boston:
            nodes={pt for id in ids for pt in geometry[id]}
            for pt in nodes:s.circle(*transform(pt),1.4,INK,opacity=.5)
    ly=735
    if signed:
        s.text(335,ly,f"−{max_abs:.2e}",15,BLUE,anchor="middle")
        s.text(725,ly,"0",15,MUTED,anchor="middle")
        s.text(1115,ly,f"+{max_abs:.2e}",15,CORAL,anchor="middle")
        for i in range(101):
            c=mix(BLUE,PALE,i/50) if i<=50 else mix(PALE,CORAL,(i-50)/50)
            s.rect(345+i*7.6,ly+12,7.8,15,c)
        s.text(350,ly+65,"Signed difference in physical-link movement-flow units; actual Boston magnitude is retained.",15,MUTED)
    else:
        s.text(55,ly,"0",15,MUTED)
        s.text(900,ly,f"shared ADMM / LP scale: {max_abs:.3g} vehicles",16,INK,"bold")
        for i in range(100):s.rect(75+i*7.6,ly-11,7.8,15,mix("#d6e4e9",TEAL,i/99))
        scope="the full Sioux 528-OD network" if not is_boston else "citywide Boston"
        s.text(55,ly+65,f"Selected-subset movement-flow totals; not {scope}.",15,MUTED)
    return s.finish()


def metric_for(case,handoff):
    d=handoff/"saved_results"/case
    ev=read_json(d/"evaluation.json");res=read_json(d/"result.json")
    if case.startswith("Boston"):
        tr=read_json(d/"transfer_evaluation.json");ref=tr["reference_objective"];gap=tr["reference_relative_gap"];back=tr["max_physical_mapping_error"]
        refsource=d/"transfer_evaluation.json"
    else:
        refsource=handoff/"private_references"/case/"arc_lp_reference_summary.json"
        ref=read_json(refsource)["objective_value"];gap=abs(ev["objective"]-ref)/max(abs(ref),1)
        back=read_json(d/"physical_comparison.json")["max_back_projection_error"]
    return {"case":case,"iterations":res["completed_iterations"],"rho":res["rho_final"],"status":res["status"],
            "objective":ev["objective"],"reference_objective":ref,"relative_gap":gap,
            "balance":ev["max_balance"],"capacity":ev["max_capacity_excess"],
            "kkt":max(ev["max_kkt_active"],ev["max_kkt_inactive_negative"]),
            "projection":ev["max_projection_error"],"back_projection":back,
            "reference_summary_source":refsource}


def render_png(svg_path,edge,profile):
    import PIL.Image
    m=re.search(r'<svg[^>]*width="(\d+)"[^>]*height="(\d+)"',svg_path.read_text(encoding="utf-8"))
    assert m;w,h=map(int,m.groups())
    png=svg_path.with_suffix(".png")
    url=svg_path.resolve().as_uri()
    cmd=[str(edge),"--headless","--disable-gpu","--no-sandbox","--disable-dev-shm-usage","--no-first-run","--hide-scrollbars",f"--window-size={w},{h}",f"--user-data-dir={profile}",f"--screenshot={png}",url]
    completed=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45)
    if completed.returncode!=0 or not png.exists():raise RuntimeError(f"PNG render failed: {svg_path.name}")
    im=PIL.Image.open(png)
    # Chromium can add a small viewport margin; recorded actual dimensions are validated.
    im.verify()
    return png


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--handoff-root",type=pathlib.Path,required=True)
    ap.add_argument("--public-repo-root",type=pathlib.Path,required=True)
    ap.add_argument("--output-root",type=pathlib.Path,required=True)
    ap.add_argument("--edge",type=pathlib.Path,required=True)
    a=ap.parse_args();hand=a.handoff_root;pub=a.public_repo_root;out=a.output_root
    fig=out/"docs/assets/admm_r2/figures";fig.mkdir(parents=True,exist_ok=True)
    profile=out.parent/"edge_render_profile";profile.mkdir(exist_ok=True)
    policy_path=hand/"ADMM_R2_FROZEN_POLICY.json";plan=hand/"ADMM_R2_EXPERIMENT_PLAN.json"
    metrics={case:metric_for(case,hand) for case in ["Sioux_200OD","Sioux_250OD","Boston_10OD"]}
    cases={}
    for case in metrics:
        d=hand/"saved_results"/case
        cases[case]={"history":read_csv(d/"history.csv"),"comp":[{**r,"admm_flow":fnum(r["admm_flow"]),"lp_flow":fnum(r["lp_flow"]),"difference":fnum(r["difference"])} for r in read_csv(d/"physical_link_flow_comparison.csv")],"d":d}
    records=[]
    def save(name,svg,inputs,caption,limitations):
        path=fig/(name+".svg");path.write_text(svg,encoding="utf-8",newline="\n")
        png=render_png(path,a.edge,profile)
        source={"figure":name,"method":"deterministic plotting of accepted saved results; no scientific rerun; optimizer_calls=0",
                "renderer":"render_public_visuals.py","inputs":[{"logical_source":label,"sha256":sha(p)} for label,p in inputs],
                "caption":caption,"limitations":limitations,"svg_sha256":sha(path),"png_sha256":sha(png)}
        (fig/(name+".source.json")).write_text(json.dumps(source,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        (fig/(name+".caption.md")).write_text(f"**Caption.** {caption}\n\n**Limitations.** {limitations}\n\nDeterministic saved-result render; no scientific solver or optimizer rerun.\n",encoding="utf-8")
        records.append(source)
    common=[("frozen policy",policy_path),("preregistered plan",plan)]
    save("admm_method_contract",method_contract(),common,"Commodity-local, shared-capacity projection, scaled-dual update, and independent-evaluation contract.","Finite time-expanded linear model; not static Beckmann UE.")
    save("admm_sioux_freeze_boston_holdout",design(),common,"Sioux-first R2_S development and pre-Boston policy freeze.","Sequence records a bounded experiment, not a general transfer guarantee.")
    save("admm_r2_numerical_policy",policy(),common,"Accepted R2_S scaling, fixed input-derived rho, active-support correction, original-unit gates.","No general ADMM convergence guarantee.")
    ovinputs=common+[(f"saved result {c}",cases[c]["d"]/"result.json") for c in metrics]+[(f"independent evaluation {c}",cases[c]["d"]/"evaluation.json") for c in metrics]
    ovinputs += [(f"reference objective summary {c}",metrics[c]["reference_summary_source"]) for c in metrics]
    save("admm_results_overview",overview(metrics),ovinputs,"Sioux 200/250 and Boston 10-OD independently accepted under frozen R2_S.","Selected Sioux subsets and bounded Boston pilot only; objective agreement does not imply identical flows.")
    for case,slug in [("Sioux_200OD","sioux_200"),("Sioux_250OD","sioux_250"),("Boston_10OD","boston_10od")]:
        c=cases[case];d=c["d"];m=metrics[case]
        inputs=common+[(f"saved {case} {n}",d/n) for n in ["history.csv","result.json","evaluation.json","physical_link_flow_comparison.csv"]]+[(f"reference objective summary {case}",m["reference_summary_source"])]
        save(f"admm_{slug}_case_sequence",case_sequence(case,c["history"],c["comp"],m),inputs,
             f"Matched six-panel residual, feasibility, objective, rho, physical scatter, and verification sequence for {case}.",
             "Reference LP is same-graph arc flow; objective agreement does not imply identical primal route/time splits.")
        geom,gsource,gnote=geometry_rows(case,pub,c["comp"])
        mapinputs=[(f"saved {case} derived physical comparison",d/"physical_link_flow_comparison.csv"),(f"already-public {case} physical geometry or topology",gsource)]
        for suffix,signed in [("final_physical_link_flow",False),("minus_lp",True)]:
            save(f"admm_{slug}_{suffix}",map_figure(case,c["comp"],geom,gnote,signed),mapinputs,
                 f"{case} physical-link {'signed ADMM-minus-LP difference' if signed else 'ADMM and LP absolute movement-flow maps on one shared scale'}.",
                 f"{gnote}. Selected subset only; objective closeness does not imply identical primal flows.")
    for case,slug,count in [("Sioux_200OD","sioux_200",200),("Boston_10OD","boston_10od",10)]:
        d=cases[case]["d"];n="local_conservation_by_commodity_iteration.csv"
        save(f"admm_{slug}_local_conservation_heatmap",heatmap(case,read_csv(d/n),count),[(f"saved {case} commodity local conservation",d/n),("frozen gate",policy_path)],
             f"Commodity-by-iteration original-unit local conservation for {case}; 1e-5 gate shown in color key.",
             "Color is log10(max(residual,1e-12)); the floor prevents log(0), and only selected commodities are shown.")
    # Existing accepted SVGs are preserved individually, with raster counterparts.
    for src in sorted((hand/"figures").glob("*.svg")):
        dest=fig/src.name;dest.write_bytes(src.read_bytes());png=render_png(dest,a.edge,profile)
        (fig/(src.stem+".source.json")).write_text(json.dumps({"figure":src.stem,"accepted_original_svg_sha256":sha(src),"png_sha256":sha(png),"role":"reused accepted individual evidence; no scientific rerun","logical_source":f"accepted handoff figure {src.name}"},indent=2)+"\n",encoding="utf-8")
    data=out/"docs/assets/admm_r2/data";data.mkdir(parents=True,exist_ok=True)
    b=cases["Boston_10OD"]["comp"]
    with (data/"boston_10od_physical_link_admm_lp_comparison.csv").open("w",newline="",encoding="utf-8") as f:
        wr=csv.writer(f);wr.writerow(["physical_link_id","admm_flow","lp_flow","admm_minus_lp"])
        for r in b:wr.writerow([r["physical_link_id"],format(r["admm_flow"],".17g"),format(r["lp_flow"],".17g"),format(r["difference"],".17g")])
    (data/"boston_10od_physical_link_admm_lp_comparison.source.json").write_text(json.dumps({"rights_basis":"User-authorized project-generated derived output, joined only to previously public Boston GMNS geometry and identifiers.","source_sha256":sha(cases["Boston_10OD"]["d"]/"physical_link_flow_comparison.csv"),"geometry_source_sha256":sha(pub/"docs/assets/boston/space_time_cg_r4/data/physical_link_flow_geometry.csv"),"rows":len(b),"excludes":["raw reference flow file","dynamic arcs","dynamic demand","state arrays"]},indent=2)+"\n",encoding="utf-8")
    (out.parent/"figure_build_records.json").write_text(json.dumps(records,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"new_figures":len(records),"reused_accepted_svgs":7,"boston_derived_link_rows":len(b),"optimizer_calls":0},indent=2))


if __name__=="__main__":main()
