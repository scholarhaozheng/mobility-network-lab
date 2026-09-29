#!/usr/bin/env python3
"""Render the two layered CG companions from checked, saved display records.

No optimization, pricing, model reconstruction, or network request is performed.
Requirements: Python 3.10+ and CairoSVG. SVG text and geometry are editable.
Usage: python tools/visuals/render_cg_layered_companions.py --repo-root .
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET

INK='#132C42'; TEAL='#087F8C'; MUTED='#5B7182'; BG='#F3F7FA'
AMBER='#DAA54A'; LINE='#CFDAE2'; BLUE='#427DA8'; TURN='#8066A7'
W,H=1460,1120

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path:Path)->list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

class SVG:
    def __init__(self)->None:
        self.a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                '<title>Source-grounded finite time-expanded graph and generated-column excerpt</title>',
                '<defs>']
        for name,col in [('teal',TEAL),('blue',BLUE),('amber',AMBER),('turn',TURN)]:
            self.a.append(f'<marker id="{name}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L7 3.5 L0 7Z" fill="{col}"/></marker>')
        self.a.append('</defs><rect width="100%" height="100%" fill="white"/>')
    def text(self,x,y,t,size=18,fill=INK,weight=400,anchor='start'):
        self.a.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(str(t))}</text>')
    def lines(self,x,y,text,size=18,fill=INK,lh=30,weight=400):
        for i,t in enumerate(text.split('\n')):self.text(x,y+i*lh,t,size,fill,weight)
    def rect(self,x,y,w,h,fill=BG,rx=12,stroke=None):
        self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
    def line(self,x1,y1,x2,y2,col=TEAL,sw=2,marker=None,dash=None,opacity=1,arc_id=None):
        self.a.append((f'<g data-arc-id="{html.escape(arc_id,quote=True)}">' if arc_id else '<g>')+
                      f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{col}" stroke-width="{sw}" opacity="{opacity}"'+
                      (f' marker-end="url(#{marker})"' if marker else '')+
                      (f' stroke-dasharray="{dash}"' if dash else '')+'/></g>')
    def path(self,d,col=TEAL,sw=2,marker=None):
        self.a.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"'+(f' marker-end="url(#{marker})"' if marker else '')+'/>')
    def circle(self,x,y,r,col,stroke='white',sw=1,opacity=1,state_id=None):
        self.a.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="{col}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"'+(f' data-state-id="{state_id}"' if state_id else '')+'/>')
    def poly(self,points,fill=BG,opacity=1):
        self.a.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+f'" fill="{fill}" stroke="{LINE}" opacity="{opacity}"/>')
    def label(self,x,y,w,t,size=15,col=TEAL):
        self.rect(x,y,w,30,'white',5,LINE);self.text(x+10,y+21,t,size,col,700)
    def save(self,path:Path):
        import cairosvg
        raw=(''.join(self.a)+'</svg>').encode()
        ET.fromstring(raw)
        path.with_suffix('.svg').write_bytes(raw)
        cairosvg.svg2png(bytestring=raw,write_to=str(path.with_suffix('.png')),output_width=W*2,output_height=H*2)


def draw(city:str,meta:dict,edges:list[dict],states:list[dict],out:Path,inputs:Path)->dict:
    m=meta[city];v=SVG();hk=city=='hong_kong';cname='Hong Kong' if hk else 'Boston'
    v.text(55,58,'FINITE SPACE–TIME COLUMN GENERATION',18,TEAL,700)
    v.text(55,105,'A road becomes a family of time-indexed movements.',34,INK,700)
    subtitle=('Hong Kong • recorded HK10 excerpt • t24–30, 30 s per step; not the full horizon' if hk else
              'Boston • recorded B07 excerpt • selected t0–10 layers, 3 s per step; not the full horizon')
    v.text(55,143,subtitle,17,MUTED)
    t0=min(m['display_time_indices']);step=62 if hk else 37;xstep=18 if hk else 10
    def p(n,t):
        x,y=m['base_xy'][str(n)];tt=int(t)-t0
        return 100+115*x+42*y+xstep*tt,705+32*y-28*x-step*tt
    base_ref='1000000076' if hk else '2032'
    # Planes are schematic positioning surfaces. All dots below are checked node-time states.
    for t in m['display_time_indices']:
        tt=t-t0;ax=142+xstep*tt;ay=737-step*tt
        v.poly([(ax-45,ay-100),(ax+425,ay-187),(ax+500,ay-27),(ax+30,ay+60)],'#F4F8FB',.86)
        v.text(ax-18,ay+36,f't = {t}',17,TEAL,700,'end')
    for s in states:
        x,y=p(s['base_state_id'],s['time']);v.circle(x,y,4,'#B3C9D5',opacity=.64,state_id=s['state_id'])
    # Every drawn graph edge has its exact saved arc ID in the SVG DOM.
    for e in sorted(edges,key=lambda x:x['role']=='selected'):
        x,y=p(e['from_physical_node_id'],e['from_time']);xx,yy=p(e['to_physical_node_id'],e['to_time'])
        typ=e['arc_type'];selected=e['role']=='selected'
        if typ=='waiting':col=AMBER;mark='amber';sw=3.4 if selected else 1.8;dash='4 4'
        elif typ=='turn_connector':col=TURN;mark='turn';sw=2.8 if selected else 2;dash=None
        else:col=TEAL if selected else BLUE;mark='teal' if selected else 'blue';sw=4.5 if selected else 1.8;dash=None
        v.line(x,y,xx,yy,col,sw,mark,dash,1 if selected else .58,e['arc_id'])
    important=set()
    for e in edges:
        if e['role']=='selected':
            important.add((e['from_physical_node_id'],e['from_time']))
            important.add((e['to_physical_node_id'],e['to_time']))
    for n,t in sorted(important,key=lambda a:(int(a[1]),a[0])):
        x,y=p(n,t);v.circle(x,y,6.8,TEAL)
        label=(m['state_aliases'][n] if hk else n)+f'@{t}'
        dx,dy=10,5
        if hk:
            if n=='1000000077':dx,dy=-12,-10
            if n=='1000002420':dx,dy=8,22
            if n=='1000002421':dx,dy=-10,-10
        else:
            if (n,t)==('1005','9'):dx,dy=10,7
            if (n,t)==('1005','10'):dx,dy=10,-6
        v.text(x+dx,y+dy,label,13,MUTED,600,anchor='end' if dx<0 else 'start')
    # Long identifiers are attached with leader lines, not guessed or visually truncated.
    if not hk:
        v.label(217,647,244,'explicit_link_18007_t0')
        v.label(380,511,244,'explicit_link_18005_t2')
        v.label(354,335,244,'explicit_link_17811_t5')
        v.label(554,180,174,'wait_1005_t9',14,AMBER)
        v.text(65,793,'Only selected time planes are shown; arrows keep their saved times.',13,MUTED)
    else:
        v.line(344,573,316,552,LINE,1);v.label(340,573,214,'arc_308368_t26')
        v.line(490,392,449,417,LINE,1);v.label(490,362,214,'arc_667532_t27')
        v.line(410,484,365,505,TURN,1);v.label(410,458,276,'arc_2000000055_t27  ·  Δt = 0',13,TURN)
        v.text(63,802,'A/B: entry/exit states; pale arcs: adjacent parts of the same HK10 path.',12.8,MUTED)
    # Three explanation cards follow the original Sioux template.
    v.rect(785,191,620,229,BG);v.text(812,226,'01 / CONSTRUCT THE COMPUTATIONAL NETWORK',15,TEAL,700)
    if hk:
        v.lines(812,261,'road-entry / road-exit state s  →  (s, t)\nmovement arc advances to its saved arrival time\nturn connector links road states at the same time\nwaiting arc advances one step at the same state',17,INK,32)
        v.text(812,403,'Original roads: 10468 → 10513 → 10526. Turns are not roads.',12.5,MUTED)
    else:
        v.lines(812,263,'physical node i  →  node-time (i, t)\nmovement arc  →  (i, t) → (j, t + travel steps)\nwaiting arc  →  (i, t) → (i, t + 1)\nOD connectors  →  source / eligible arrival sink',17.5,INK,36)
    v.rect(785,443,620,185,BG);v.text(812,479,'02 / ADD ONE GENERATED COLUMN',15,TEAL,700)
    if hk:
        v.lines(812,513,'HK10: A−@26 → A+@27 → B−@27 → B+@28\n308368 at t26–27; zero-time turn; 667532 at t27–28\nA−/A+ = 1000000076 / 1000000077\nB−/B+ = 1000002420 / 1000002421',16.5,INK,26)
        v.text(812,619,'ORACLE_R1_HK10_K1 · 77 arcs overall · 0.835215 PCE',12.8,MUTED)
    else:
        v.lines(812,513,'B07: 2032@0 → 1002@2 → 1004@5\n→ 1005@9 → 1005@10 (one waiting step).\nThe saved column then continues to 1492@19.',17.5,INK,30)
        v.text(812,619,'PHASEI_R1_GEN_B07_001 · full-column flow: 0.364622',12.8,MUTED)
    v.rect(785,650,620,147,'#EDF8F6');v.text(812,685,'03 / RE-SOLVE SHARED CAPACITY',15,TEAL,700)
    if hk:
        v.lines(812,718,'The restricted master enforces shared arc capacities.\nHK10 has no waiting arc in its complete saved column.\nNo separate cross-OD exchange is claimed for this excerpt.',16.5,INK,29)
    else:
        v.lines(812,718,'Recorded round-1 artificial-flow change (model vehicles):\nB07 −0.364622; B09 −1.083333; B10 +1.083333.\nBinding arc explicit_link_18164_t0: B10 → B09.',16.4,INK,29)
    # Legend: roles differ truthfully while order and typography remain parallel.
    v.line(80,832,120,832,TEAL,4.5);v.text(133,838,'selected column excerpt',13.8,INK)
    v.line(369,832,409,832,BLUE,2);v.text(420,838,'same-column context' if hk else 'other saved allowed arc',13.8,INK)
    v.line(699,832,739,832,TURN if hk else AMBER,2.5,None,None if hk else '4 4')
    v.text(750,838,'zero-time turn' if hk else 'waiting',13.8,INK)
    # Identical CG explanation strip; no numerical solve is implied by rendering.
    for x,w,h1,h2 in [(55,330,'Restricted master','Phase I: artificial-flow clearance'),(470,330,'Time-network pricing','Dual-adjusted candidate path'),(885,520,'Phase II + independent reference','Minimize cost; compare to the same arc-flow LP')]:
        v.rect(x,883,w,98,INK);v.text(x+18,919,h1,20,'white',700);v.text(x+18,949,h2,13,'#BDD0DB')
    v.line(385,932,465,932,TEAL,2,'teal');v.line(800,932,880,932,TEAL,2,'teal')
    v.path('M635 982 L635 1010 L220 1010 L220 982',TEAL,2,'teal');v.text(407,1036,'add selected column and re-solve',14,TEAL,500,'middle')
    if hk:
        footer='Schematic coordinates; exact routing states, arc IDs and times come from the approved HK10 excerpt. No observed GPS trajectory is shown.\nFull path arrival: t37; sink at t50 is bookkeeping, not physical waiting. The full horizon and terminal connections are omitted.'
    else:
        footer='Schematic coordinates; drawn arcs and node-time states match the saved graph. Selected planes omit intermediate layers, not travel time.\nFull path arrival: t19; sink at t100 is bookkeeping, not physical waiting. The capacity event is saved reoptimization, not a unique-cause claim.'
    v.lines(57,1071,footer,12.5,MUTED,21)
    stem=f'{city}_layered_space_time_construction'
    dest=out/stem;v.save(dest)
    caption=(f'{cname}: a source-grounded layered local cutaway from the accepted {m["demand_id"]} generated column. '
             f'One time step is {m["step_seconds"]} seconds. The displayed excerpt is not the complete path: '
             f'physical arrival is t{m["arrival_time_index"]}, while the terminal connector ends at t{m["sink_time_index"]} for bookkeeping. '
             'Only schematic display coordinates are chosen by the renderer; arc identities, endpoint states and times are taken from the saved records. '
             +('Entry/exit routing states and zero-time turns are distinguished from original physical roads. No waiting arc is present in the full HK10 column. ' if hk else
               'The selected t9–t10 waiting arc is an actual saved B07 arc. ')
             +'No scientific model was rerun. This is a model-generated path, not an observed trajectory.')
    (out/(stem+'.caption.md')).write_text(caption+'\n',encoding='utf-8')
    meta_out={'figure_id':stem,'city':cname,'generated_column_id':m['column_id'],'demand_id':m['demand_id'],
              'displayed_arc_ids':[r['arc_id'] for r in edges],
              'displayed_node_time_count':len(states),'time_indices':m['display_time_indices'],
              'step_seconds':m['step_seconds'],'full_physical_arrival_time':m['arrival_time_index'],
              'terminal_bookkeeping_time':m['sink_time_index'],'scientific_solver_calls':0,
              'renderer':str(Path(__file__).name),'renderer_sha256':sha(Path(__file__)),
              'display_inputs_sha256':sha(inputs),'display_edges_sha256':sha(out/f'{city}_display_edges.csv'),
              'display_states_sha256':sha(out/f'{city}_display_states.csv'),
              'source_input_hashes':meta['input_hashes'],'frozen_graph_membership_source':meta['graph_membership_check'],
              'svg_sha256':sha(dest.with_suffix('.svg')),'png_sha256':sha(dest.with_suffix('.png')),
              'rendering':'Deterministic vector text/geometry from saved display tables; not image-generation output.',
              'caption':caption}
    (out/(stem+'.source.json')).write_text(json.dumps(meta_out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return meta_out

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    args=parser.parse_args();out=args.repo_root.resolve()/'docs/assets/cg_layered_companions_r1'
    inputs=out/'DISPLAY_INPUTS.json'
    if not inputs.is_file():parser.error(f'Missing display inputs: {inputs}')
    meta=json.loads(inputs.read_text(encoding='utf-8'))
    for city in ['boston','hong_kong']:
        edges=rows(out/f'{city}_display_edges.csv');states=rows(out/f'{city}_display_states.csv')
        for e in edges:
            if int(e['to_time'])<int(e['from_time']):raise ValueError(f'Time reversal: {e["arc_id"]}')
            if e['arc_type']=='movement' and not e['physical_link_id']:raise ValueError('Missing physical-link mapping')
            if e['arc_type']!='movement' and e['physical_link_id']:raise ValueError('Nonmovement incorrectly mapped to a physical road')
        draw(city,meta,edges,states,out,inputs)
    print('Rendered two SVG/PNG companion pairs; scientific solver calls: 0.')
    return 0

if __name__=='__main__':raise SystemExit(main())
