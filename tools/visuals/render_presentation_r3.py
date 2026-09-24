#!/usr/bin/env python3
"""Render the framework/case boards from released display inputs; no model calls.
Dependencies: Pillow, CairoSVG and Matplotlib (font discovery only).
Existing maps are composed, not recomputed. SVG contains editable text/geometry.
Different rendering-library versions can produce different image bytes.
"""
from pathlib import Path
import html,json,csv,math,textwrap,hashlib
from PIL import Image,ImageDraw,ImageFont
try:
    import cairosvg
except ImportError:
    cairosvg = None

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--framework-only', action='store_true', help='Regenerate the generic overview without touching saved case figures')
    args=parser.parse_args()
    S=Path(__file__).resolve().parents[2]; OUT=S/'docs/assets/presentation_r3';OUT.mkdir(parents=True,exist_ok=True)
    INK='#132C42'; TEAL='#087F8C'; CYAN='#49C5B6'; MUTED='#5B7182'; BG='#F3F7FA'; AMBER='#DAA54A'; LINE='#CFDAE2'; BLUE='#427DA8'
    def esc(s):return html.escape(str(s))
    class SVG:
     def __init__(self,w,h):
      self.w=w;self.h=h;self.a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8Z" fill="{TEAL}"/></marker><linearGradient id="dark" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#112A42"/><stop offset="1" stop-color="#1F4758"/></linearGradient></defs><rect width="100%" height="100%" fill="white"/>']
     def rect(self,x,y,w,h,fill=BG,rx=12,stroke=None):self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
     def text(self,x,y,t,size=18,fill=INK,weight=400,anchor='start'):
      self.a.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(t)}</text>')
     def lines(self,x,y,t,size=17,fill=MUTED,lh=25,weight=400):
      for i,line in enumerate(t.split('\n')):self.text(x,y+i*lh,line,size,fill,weight)
     def line(self,x1,y1,x2,y2,c=TEAL,sw=2,arrow=False,dash=None,opacity=1):self.a.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}" opacity="{opacity}"'+(' marker-end="url(#arr)"' if arrow else '')+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
     def path(self,d,c=TEAL,sw=2,arrow=False,dash=None):self.a.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{sw}"'+(' marker-end="url(#arr)"' if arrow else '')+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
     def circle(self,x,y,r,c,stroke='white',sw=1):self.a.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="{stroke}" stroke-width="{sw}"/>')
     def polygon(self,points,fill=BG,stroke=LINE,opacity=1):self.a.append(f'<polygon points="'+ ' '.join(f'{x},{y}' for x,y in points)+f'" fill="{fill}" stroke="{stroke}" opacity="{opacity}"/>')
     def save(self,stem):
      b=(''.join(self.a)+'</svg>').encode();(OUT/(stem+'.svg')).write_bytes(b)
      if cairosvg:
       cairosvg.svg2png(bytestring=b,write_to=str(OUT/(stem+'.png')),output_width=self.w*2,output_height=self.h*2)
    # Generic framework: no city geography, identifiers or result numbers.
    v=SVG(1440,1060);v.rect(0,0,1440,1060,'url(#dark)',0)
    v.text(55,68,'MOBILITY COMPUTATION LAB',20,CYAN,700);v.text(55,120,'One framework. Explicit inputs. Traceable computation.',35,'white',700)
    v.text(55,156,'Conceptual overview — capability support and case evidence are listed separately.',17,'#BDD0DB')
    v.rect(55,197,1330,90,'#234B5C');v.text(78,230,'GMNS DATA FOUNDATION',17,CYAN,700)
    v.text(78,268,'zones + hierarchy  •  centroids + access  •  directed physical links  •  source IDs + units',23,'white',600)
    v.rect(55,317,1330,133,'#234B5C');v.text(78,349,'UPSTREAM PREPARATION  /  NOT A FIFTH STAGE',17,CYAN,700)
    v.rect(78,366,390,62,'#315e6d');v.text(94,390,'Statistics + source boundaries',16,'white',600);v.text(94,414,'Population / households',14,'#dce9ee')
    v.rect(488,366,330,62,'#315e6d');v.text(505,390,'Activity evidence',16,'white',600);v.text(505,414,'Distinct attraction attributes',14,'#dce9ee')
    v.rect(838,366,523,62,'#315e6d');v.text(855,390,'Version + field + geography checks → zone allocation',15,'white',600)
    v.text(855,414,'Zonal attributes + provenance → declared generation model',14,'#dce9ee')
    v.text(478,404,'+',19,CYAN,700,'middle');v.line(819,397,836,397,CYAN,2,True)
    v.path('M1020 428 L1020 466 L208 466 L208 484',CYAN,2,True)
    xs=[55,395,735,1075];titles=['Trip generation','Trip distribution','Mode choice','Traffic assignment'];subs=['Activities → productions / attractions','Margins + impedance → person OD','Costs + a declared model → mode demand','Vehicle OD → selected network method']
    for i,x in enumerate(xs):
     v.rect(x,485,310,112,'white');v.text(x+19,513,f'0{i+1}',16,TEAL,700);v.text(x+19,543,titles[i],22,INK,700);v.text(x+19,574,subs[i],13,MUTED)
     if i<3:v.line(x+310,541,x+331,541,CYAN,2,True)
    v.rect(55,631,645,103,'#234B5C');v.text(77,664,'OBSERVATION PATH',17,CYAN,700);v.text(77,697,'GPS / service evidence → QC → map matching → parameters',17,'white');v.text(77,719,'Supported cost inputs; not automatic passenger-OD recovery.',12,'#BDD0DB')
    v.path('M700 682 L870 682 L870 599',CYAN,2,True)
    v.rect(735,778,650,100,'#234B5C');v.text(757,808,'STATIC FIXED-DEMAND METHODS',16,CYAN,700);v.text(757,842,'Frank–Wolfe  |  finite-path reference  |  native Diagnostic L3',17,'white');v.text(757,863,'Beckmann objective • different representations • original-space checks',12,'#BDD0DB')
    v.rect(55,778,650,100,'#234B5C');v.text(77,808,'FINITE SPACE–TIME METHOD',16,CYAN,700);v.text(77,842,'Time expansion → Phase I → Phase II / column generation',17,'white');v.text(77,863,'Linear cost + explicit capacities • same-instance arc-flow LP reference',12,'#BDD0DB')
    v.path('M1230 598 L1230 763',CYAN,2,True);v.path('M1230 610 L710 610 L710 760 L670 760 L670 778',CYAN,2,True)
    v.rect(55,924,1330,72,'white');v.text(79,966,'OUTPUT CONTRACT',16,TEAL,700);v.text(310,966,'path / link flow  •  demand accounting  •  validation  •  reproducible maps & tables',21,INK,600)
    v.line(380,878,380,922,CYAN,2,True);v.line(1060,878,1060,922,CYAN,2,True)
    v.text(57,1034,'Supplied vehicle OD may enter directly at assignment. Household rates are one case-specific generation model, not a universal requirement.',13,'#BDD0DB')
    v.save('framework_overview')
    if args.framework_only:
     print('Regenerated framework overview only')
     return 0
    # Source-grounded CG exploded local subgraph; horizontal wires not falsely actual movement arcs.
    display=json.loads((OUT/'DISPLAY_MODEL.json').read_text())
    topo=display['topology'];cap=display['capacity_rows'];lookup={x['arc_id']:x for x in cap}; selected=['8','6','5','9','4'];base={'8':(0,1),'6':(1,0),'5':(2,1),'9':(1,2),'4':(3,0)}
    def P(n,t):
     x,y=base[n];return 100+115*x+42*y+19*t,710+32*y-28*x-63*t
    v=SVG(1460,1120);v.text(55,58,'FINITE SPACE–TIME COLUMN GENERATION',18,TEAL,700);v.text(55,105,'A road becomes a family of time-indexed movements.',34,INK,700);v.text(55,143,'Sioux Falls • source-grounded local construction view • time indices 0–6, not the full horizon',17,MUTED)
    # show bottom to top low emphasis time layers
    for t in range(7):
     a=P('8',t); pts=[(a[0]-45,a[1]-100),(a[0]+425,a[1]-187),(a[0]+500,a[1]-27),(a[0]+30,a[1]+60)]
     v.polygon(pts,'#F4F8FB',LINE,.86)
     v.text(a[0]-39,a[1]+36,f't = {t}',17,TEAL,700)
     for n in selected:
      x,y=P(n,t);v.circle(x,y,4.5,'#B3C9D5');v.text(x+9,y+4,n,12,MUTED)
    # actual allowed movement and wait arc occurrences in selected slice
    used=[]
    for r in cap:
     t=int(r['from_time']);tt=int(r['to_time']);typ=r['arc_type']; aid=r['arc_id'];stem=aid.split('_t')[0]
     if typ=='movement' and stem in topo:
      u,w=topo[stem]
      if u in selected and w in selected and 0<=t<tt<=6:
       x,y=P(u,t);xx,yy=P(w,tt);v.line(x,y,xx,yy,BLUE,1,False,None,.24);used.append(aid)
     elif typ=='waiting' and 0<=t<tt<=6:
      n=aid.split('_')[1]
      if n in selected:
       x,y=P(n,t);xx,yy=P(n,tt);v.line(x,y,xx,yy,AMBER,1,False,'3 4',.65);used.append(aid)
    for aid in ['xs_link19_t0','xs_link15_t2']:
     r=lookup[aid];u,w=topo[aid.split('_t')[0]];x,y=P(u,int(r['from_time']));xx,yy=P(w,int(r['to_time']));v.line(x,y,xx,yy,TEAL,5,True);v.circle(x,y,7,TEAL);v.circle(xx,yy,7,TEAL)
     mx,my=(x+xx)/2,(y+yy)/2;v.rect(mx+13,my-17,176,32,'white',6,LINE);v.text(mx+23,my+4,aid,15,TEAL,700)
    v.rect(785,191,620,229,BG);v.text(812,226,'01 / CONSTRUCT THE COMPUTATIONAL NETWORK',15,TEAL,700)
    v.lines(812,263,'physical node i  →  node-time (i, t)\nmovement arc    →  (i, t) → (j, t + travel time)\nwaiting arc       →  (i, t) → (i, t + one step)\nOD connectors  →  source / eligible arrival sink',18,INK,36)
    v.rect(785,443,620,179,BG);v.text(812,479,'02 / ADD ONE REAL COLUMN',15,TEAL,700)
    v.lines(812,514,'Saved XS170: 8 at t0 → 6 at t2 → 5 at t6\nsource_XS170 → xs_link19_t0 → xs_link15_t2\n→ sink_XS170_5_t6',18,INK,31)
    v.text(812,606,'Highlighted path is recorded; other lines are a local allowed-arc slice.',12,MUTED)
    v.rect(785,647,620,150,'#EDF8F6');v.text(812,682,'03 / RE-SOLVE SHARED CAPACITY',15,TEAL,700)
    v.lines(812,718,'XS170 reroutes 500 units off xs_link21_t1.\nXS169 uses those 500 units; artificial flow drops.\nThe shared arc remains at 5,050.193 / 5,050.193.',18,INK,29)
    v.line(80,832,120,832,TEAL,5);v.text(133,838,'selected saved path',14,INK);v.line(342,832,382,832,BLUE,2);v.text(393,838,'other allowed movement',14,INK);v.line(670,832,710,832,AMBER,2,False,'4 4');v.text(720,838,'waiting',14,INK)
    # loop: aesthetic footer RMP and pricing, explicit phaseI vs II
    for x,w,h1,h2 in [(55,330,'Restricted master','Phase I: artificial-flow clearance'),(470,330,'Time-network pricing','Dual-adjusted candidate path'),(885,520,'Phase II + independent reference','Minimize cost; compare to the same arc-flow LP')]:
     v.rect(x,883,w,98,INK);v.text(x+18,919,h1,20,'white',700);v.text(x+18,949,h2,13,'#BDD0DB')
    v.line(385,932,465,932,TEAL,2,True);v.path('M635 982 L635 1010 L220 1010 L220 982',TEAL,2,True);v.text(407,1036,'add selected column and re-solve',14,TEAL,500,'middle');v.line(800,932,880,932,TEAL,2,True)
    v.lines(57,1071,'Schematic display coordinates; saved node/link/time identities and the selected path are preserved. The full source/sink horizon is omitted.\nThe 500-unit exchange is a recorded RMP mechanism, not a proof of a unique required path. No congestion-propagation or DTA claim.',13,MUTED,21)
    v.save('sioux_space_time_construction')
    # A paired table/mechanism infographic with no newly simulated values.
    v=SVG(1440,730);v.text(55,57,'WHY PHASE I NEEDS PRICING',18,TEAL,700);v.text(55,102,'A new path for one OD can clear artificial flow for another.',32,INK,700)
    v.text(55,142,'Recorded Sioux Falls event: round 34 in the 200-OD case, round 39 in the 250-OD case.',17,MUTED)
    for x,label,after in [(55,'BEFORE ADDING THE XS170 PATH',False),(770,'AFTER MASTER REOPTIMIZATION',True)]:
     v.rect(x,187,615,334,BG);v.text(x+25,225,label,17,TEAL,700)
     v.text(x+25,267,'Shared time arc  xs_link21_t1',23,INK,700)
     a=5050.193; totalw=550;sc=totalw/a;y=301
     others=a-650.193
     v.rect(x+25,y,others*sc,62,'#BECFD8',0);v.rect(x+25+others*sc,y,(650.193 if after else 150.193)*sc,62,TEAL,0)
     if not after:v.rect(x+25+(others+150.193)*sc,y,500*sc,62,AMBER,0)
     v.text(x+25,394,'Arc load / capacity: 5,050.193 / 5,050.193',18,INK,600)
     v.lines(x+25,433,('XS170 on this arc: 500 → 0\nXS169 on this arc: 150.193 → 650.193' if after else 'XS170 uses its delayed route: 500 units\nXS169 still needs 500 more units of capacity'),17,MUTED,31)
    v.line(680,345,755,345,TEAL,3,True)
    v.rect(55,554,1330,93,INK);v.text(80,591,'THE NETWORK EFFECT',15,CYAN,700);v.text(80,625,'XS170 demand stays at 500; XS169 artificial mass decreases by 500; the capacity constraint stays binding.',20,'white',600)
    v.text(55,689,'Saved primal-flow evidence explains the exchange. The raw reported capacity dual remains approximately −1 under its solver convention.',14,MUTED)
    v.save('sioux_capacity_exchange')
    # Composition uses original maps; retains full axes/legends, removes only whitespace/title repetition.
    from matplotlib import font_manager
    font=font_manager.findfont('DejaVu Sans');bold=font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans',weight='bold'))
    def ft(size,b=False):return ImageFont.truetype(bold if b else font,size)
    W,H=2400,1800; im=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(im)
    draw.text((60,34),'BOSTON  /  CONTROLLED METHOD COMPARISON',font=ft(28,True),fill=TEAL)
    draw.text((60,82),'Same 26 endpoint ODs. Same 203.660479 vehicle trips. Same physical network.',font=ft(30,True),fill=INK)
    base=S/'docs/assets/boston/assignment_methods_r1'
    entries=[(0,0,'FW • ABS_PLANNED','boston_abs_planned_fw_flow.png'),(1,0,'Native L3 • rank 26','boston_abs_planned_l3_rank26_flow.png'),(2,0,'Native L3 • rank 52','boston_abs_planned_l3_rank52_flow.png'),(1,1,'rank 26 minus FW','boston_abs_planned_l3_rank26_minus_fw.png'),(2,1,'rank 52 minus FW','boston_abs_planned_l3_rank52_minus_fw.png')]
    for col,row,title,name in entries:
     x=50+col*790;y=164+row*736;draw.text((x+10,y),title,font=ft(27,True),fill=INK)
     pic=Image.open(base/name).convert('RGB'); ww,hh=pic.size
     # All five are exports of the same figure geometry: keep plot, axes and numeric colorbar.
     crop=pic.crop((int(.293*ww),int(.083*hh),int(.958*ww),int(.931*hh)))
     crop.thumbnail((750,664),Image.Resampling.LANCZOS);im.paste(crop,(x+(760-crop.width)//2,y+47))
    x=65;y=933
    draw.rounded_rectangle((x,y,x+700,y+594),radius=24,fill=BG)
    for j,line in enumerate(['READ THIS AS A SMALL-INSTANCE CHECK','Absolute maps share one flow scale.','Difference maps share a zero-centred scale.','','Maximum |L3 − FW| ≈ 5.89 × 10⁻⁶','model vehicle trips per physical link.','','The accepted L3 points have small','OD deficits within declared tolerance.','They are not exact-equilibrium certificates.','','This is NOT the expanded 17,522-OD run.']):
     draw.text((x+26,y+28+j*43),line,font=ft(22,j in [0,4]),fill=TEAL if j==0 else INK)
    draw.text((60,1677),'Original numerical outputs are unchanged. New layout only; no solver or map matching was run.',font=ft(25),fill=MUTED)
    draw.text((60,1720),'Source: saved ABS_PLANNED FW and accepted L3 outer-02 files. Original full-size maps and precision CSV remain linked.',font=ft(23),fill=MUTED)
    im.save(OUT/'boston_method_comparison.png',optimize=True)
    # Main Phase-I comparison: two supplied plots, same interpretive row, no interpolation of traces.
    Sfig=S/'docs/assets/sioux/phase_i_r1'; cw=2400;ch=1270;im=Image.new('RGB',(cw,ch),'white');d=ImageDraw.Draw(im)
    d.text((60,30),'SIOUX FALLS / TWO RECORDED PHASE-I CLEARANCE RUNS',font=ft(29,True),fill=TEAL)
    for i,(od,rounds) in enumerate([(200,51),(250,62)]):
     p=Image.open(Sfig/f'sioux_falls_{od}od_phase_i_academic.png').convert('RGB');p.thumbnail((1120,965),Image.Resampling.LANCZOS);x=55+i*1190
     d.text((x,86),f'{od} ODs  •  artificial flow reaches zero at round {rounds}',font=ft(25,True),fill=INK);im.paste(p,(x+(1120-p.width)//2,140))
    d.text((60,1155),'One saved run per size, different caps: this is descriptive evidence, not a scaling-law or timing benchmark.',font=ft(24),fill=MUTED)
    d.text((60,1200),'New columns redistribute shared capacity. Phase II then reduces actual path cost on the feasible real-path pool.',font=ft(24),fill=MUTED)
    im.save(OUT/'sioux_phase_i_pair.png',optimize=True)
    # Source record for all visual products.
    meta={'figure_type':{'framework_overview':'conceptual schema, no city results','sioux_space_time_construction':'schematic layout of actual local node/time/arc identities','sioux_capacity_exchange':'saved before/after mechanism, not a counterfactual experiment','boston_method_comparison':'layout-only composite of accepted maps, full numerical legends retained','sioux_phase_i_pair':'layout-only composite of supplied trace figures'},'local_time_slice':[0,6],'selected_nodes':selected,'selected_path':['source_XS170','xs_link19_t0','xs_link15_t2','sink_XS170_5_t6'],'selected_movement_topology':{a:topo[a] for a in ['xs_link19','xs_link15']},'allowed_displayed_arcs':used,'no_model_runs':True,'source_hashes':display['source_hashes']}
    (OUT/'FIGURE_PROVENANCE.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Assets generated',list(p.name for p in OUT.iterdir()))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
