"""Render frozen plot data only. This script never imports a CG solver.

Contract: bound endpoints belong to their named producer; history uses every
saved RMP row within its own phase. No interpolation across builds or fake
iteration history for nonbinding certificates. Reuses the current atlas style.
"""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/visuals/berkeley_alignment_r2'))
from atlas_style import new_figure,format_axes,compact_header,INK,TEAL,BLUE,GRID
from embed_serif_fonts import embed_serif_fonts
import matplotlib.pyplot as plt
from PIL import Image
AS=ROOT/'docs/assets/shared-cg-20261013'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unit(c):return 'native cost × original volume' if c['case_id'].startswith('sioux') else 'vehicle·min' if c['city']=='hong-kong' else 'PCE·min'
def save(fig,c,e,stem,title,caption):
 out=AS/c['case_id']/e['evidence_id'];compact_header(fig)
 for ext in ['svg','png']:
  fig.savefig(out/(stem+'.'+ext),dpi=220,bbox_inches='tight',pad_inches=.055,metadata={'Date':None} if ext=='svg' else None)
 embed_serif_fonts(out/(stem+'.svg'));plt.close(fig)
 with Image.open(out/(stem+'.png')) as im:w,h=im.size
 (out/(stem+'.caption.txt')).write_text(caption+'\n',encoding='utf8')
 record={'case_id':c['case_id'],'evidence_id':e['evidence_id'],'renderer':'tools/visuals/render_shared_cg_20261013.py','renderer_sha256':sha(Path(__file__)),'style':'Existing atlas C / DejaVu Serif / navy and teal','data':'plot-data.json','data_sha256':sha(out/'plot-data.json'),'upper_certificate':e.get('upper_certificate'),'lower_certificate':e.get('lower_certificate'),'snapshot':'2026-10-13 22:26 Asia/Shanghai','new_solver_run':False,'caption':caption,'exports':{ext:sha(out/(stem+'.'+ext)) for ext in ['png','svg']}}
 (out/(stem+'.source.json')).write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 base=(out/stem).relative_to(ROOT/'docs').as_posix()
 e['figures'].append({'id':'cg-'+c['case_id']+'-'+e['evidence_id']+'-'+stem,'title':title,'src':base+'.svg','png':base+'.png','data':(out/'plot-data.json').relative_to(ROOT/'docs').as_posix(),'source':base+'.source.json','caption':caption,'width':w,'height':h})

def bounds(c,e):
 u,l=e['U'],e['L'];fig=new_figure(c['city_name'],'Certified bounds on the frozen instance',c['case_id']+' · '+e['label'],figsize=(9,4.6))
 ax=fig.add_axes([.12,.29,.51,.42]);format_axes(ax)
 ax.scatter([l,u],[0,1],c=[TEAL,BLUE],s=75,zorder=4)
 ax.set_yticks([0,1],['Lower bound L','Feasible upper U']);ax.set_ylim(-.65,1.65)
 delta=max(abs(u-l),max(abs(u),1)*1e-5);ax.set_xlim(min(u,l)-delta*.22,max(u,l)+delta*.22)
 ax.ticklabel_format(axis='x',style='plain',useOffset=False);ax.tick_params(axis='x',labelrotation=12)
 ax.set_xlabel(unit(c));ax.set_title('Matched endpoints; not a trajectory',fontsize=10)
 ax.annotate(f'{l:.12g}',(l,0),xytext=(0,-19),textcoords='offset points',ha='center',fontsize=8,color=TEAL)
 ax.annotate(f'{u:.12g}',(u,1),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8,color=BLUE)
 fig.text(.69,.66,'Relative gap',fontsize=10,color=INK)
 fig.text(.69,.56,f"{e['gap_display_pct']:.9g}%",fontsize=18,color=TEAL)
 fig.text(.69,.45,'(U − L) / |U|',fontsize=10)
 fig.text(.69,.34,'Raw signed value retained\nin downloadable plot data.',fontsize=8.5)
 state='OPEN bounds' if e['gap_display_pct']>.01 else ('Gap accepted; RMP pricing OPEN' if 'pricing gate open' in e['status'] else 'Numerical certificate')
 fig.text(.12,.115,state,fontsize=10,weight='bold',color=INK)
 fig.text(.12,.055,'No comparison across H/Q, demand factors or cost models.',fontsize=8,color=INK)
 caption=f"{e['label']}: U={u:.15g}, L={l:.15g} {unit(c)}. Signed relative gap {e['gap_signed']:.15g}. Upper: {e['upper_build']}; lower: {e['lower_build']}. {e['status']}. These are endpoint certificates, not a multi-round curve. Values within 1e−12 relative tolerance display as zero; raw signs remain in data."
 save(fig,c,e,'bounds','Column generation: bounds and certificate',caption)

def series(c,e,phase,stem):
 rows=[r for r in e['history'] if r['phase']==phase];fig=new_figure(c['city_name'],'Phase I: feasibility' if phase=='I' else 'Phase II: real objective and lower bound',c['case_id']+' · '+e['label'],figsize=(9,4.8));ax=fig.add_axes([.12,.23,.81,.47]);format_axes(ax)
 if not rows:
  ax.axis('off');ax.text(.5,.55,'No Phase-I RMP trace in this saved run.',ha='center',va='center',fontsize=12);ax.text(.5,.35,'Feasible FIFO seed → Phase II',ha='center',va='center',fontsize=10);caption='This cold S2 run starts from the separately stored feasible FIFO seed. There is no Phase-I curve to fabricate.'
 else:
  x=[r['round'] for r in rows]
  if phase=='I':
   y=[r['artificial_mass'] for r in rows];ax.step(x,y,where='post',color=TEAL,lw=1.9);ax.scatter(x,y,s=12,color=TEAL,zorder=4);ax.axhline(1e-8,color=BLUE,ls='--',lw=1,label='Artificial-flow gate 1e−8');ax.set_ylabel('Artificial flow ('+('original volume' if c['city']=='sioux-falls' else 'vehicle' if c['city']=='hong-kong' else 'PCE')+')');ax.legend(fontsize=8);caption=f'All {len(rows)} saved Phase-I RMP states, at their actual round indices. Artificial flow is separate from the perturbed Phase-I objective; true zero is retained.'
  else:
   up=[r['true_primal_objective'] for r in rows];lo=[r.get('full_graph_lower_bound') for r in rows]
   ax.step(x,up,where='post',color=BLUE,lw=1.7,label='Saved feasible primal U');ax.scatter(x,up,s=13,color=BLUE,zorder=4)
   good=[i for i,v in enumerate(lo) if v is not None and math.isfinite(v)]
   ax.step([x[i] for i in good],[lo[i] for i in good],where='post',color=TEAL,lw=1.4,label='Saved full-graph L');ax.scatter([x[i] for i in good],[lo[i] for i in good],s=11,color=TEAL)
   ax.set_ylabel(unit(c));ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.legend(fontsize=8)
   caption=f'All {len(rows)} saved Phase-II RMP states from this run, without smoothing or cross-version joins. The historical run lower bound is preserved; independently rechecked certificate rounding and the separate Pittsburgh dual mix are not substituted into this trace.'
  ax.set_xlabel('Saved Phase-'+phase+' RMP round (not LP internal iterations)')
  if len(x)==1:ax.set_xlim(x[0]-.5,x[0]+.5);ax.set_xticks(x)
  fig.text(.12,.07,f"{len(rows)} saved states · {e.get('rmp_calls')} total RMP calls in this run",fontsize=9)
 save(fig,c,e,stem,'Column generation: Phase I feasibility' if phase=='I' else 'Column generation: Phase II real cost',caption)

def pricing(c,e):
 fig=new_figure(c['city_name'],'Full-graph pricing: both phase units retained',c['case_id']+' · '+e['label'],figsize=(9,4.8))
 for j,phase in enumerate(['I','II']):
  ax=fig.add_axes([.095+j*.475,.26,.375,.43]);format_axes(ax);rs=[r for r in e['history'] if r['phase']==phase]
  if rs:
   x=[r['round'] for r in rs];y=[r['minimum_reduced_cost'] for r in rs];ax.step(x,y,where='post',color=TEAL,lw=1.6);ax.scatter(x,y,s=13,color=TEAL,zorder=4)
   if len(x)==1:ax.set_xlim(x[0]-.5,x[0]+.5);ax.set_xticks(x)
   ax.annotate(f"last {y[-1]:.6g}",(x[-1],y[-1]),xytext=(-3,10),textcoords='offset points',ha='right',fontsize=8)
  else:ax.text(.5,.5,'No saved Phase-I RMP',ha='center',transform=ax.transAxes)
  ax.axhline(-1e-6,color=BLUE,ls='--',lw=1,label='Original gate −1e−6');ax.set_xlabel('Saved RMP round');ax.set_title('Phase '+phase,fontsize=11);ax.set_ylabel('Minimum reduced cost\n'+('Phase-I objective units' if phase=='I' else ('native cost' if c['city']=='sioux-falls' else 'min')));ax.legend(fontsize=7.5,loc='lower right')
 fig.text(.10,.07,'A small bound gap does not imply the final RMP pricing gate is met.',fontsize=9)
 save(fig,c,e,'pricing','Column generation: original pricing gate','Every saved reduced cost is retained, separately for Phase I and Phase II. The original final-RMP gate is −1e−6. Negative endpoints are not removed when the bound-gap test passes. RMP rounds are distinct from internal LP iterations.')

def nonbinding(c,e):
 ck=e['nonbinding_checks'];fig=new_figure(c['city_name'],'Nonbinding shortest-path certificate',c['case_id']+' · no CG outer iterations required',figsize=(9,4.5));ax=fig.add_axes([.13,.28,.8,.4]);format_axes(ax)
 ratio=ck['AON_maximum_original_capacity_ratio'];ax.barh(['Maximum timed load / capacity'],[ratio],height=.28,color=TEAL);ax.axvline(1,color=BLUE,ls='--',label='Capacity limit');ax.set_xlim(0,1.12);ax.set_xlabel('Maximum physical entry load / capacity');ax.text(ratio+.02,0,f'{ratio:.6f}',va='center');ax.legend(loc='upper right')
 fig.text(.13,.12,'All '+format(c['events'],',')+' release events represented by saved uniform paths.',fontsize=9)
 fig.text(.13,.06,'Full-graph lower bound + feasible shortest paths; no invented convergence curve.',fontsize=8.5)
 save(fig,c,e,'nonbinding','Column generation: nonbinding capacity check',f"Saved maximum timed capacity ratio {ratio:.12g}; overloaded physical edges: {ck['AON_capacity_overloaded_original_edges']}. This frozen-instance certificate represents {c['events']:,} release events, not that many optimization iterations. It does not prove geographic support is too small.")

def render():
 cat=load(AS/'catalog.json')
 for c in cat['cases']:
  for e in c['evidence']:
   e['figures']=[]
   if e.get('U') is None:continue
   bounds(c,e)
   if e['history']:
    series(c,e,'I','phase-i');series(c,e,'II','phase-ii');pricing(c,e)
   elif e['nonbinding_checks']:nonbinding(c,e)
  print(c['case_id'],flush=True)
 (AS/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':render()
