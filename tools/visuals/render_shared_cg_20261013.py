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
from atlas_style import new_figure,format_axes,compact_header,INK,TEAL,BLUE,GRID,ROAD,FLOW_CMAP
from embed_serif_fonts import embed_serif_fonts
import matplotlib.pyplot as plt
from PIL import Image
AS=ROOT/'docs/assets/shared-cg-20261013'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unit(c):return 'native cost × original volume' if c['case_id'].startswith('sioux') else 'vehicle·min' if c['city']=='hong-kong' else 'PCE·min'
def save(fig,c,e,stem,title,caption):
 out=AS/c['case_id']/e['evidence_id'];compact_header(fig)
 # Reference atlas exports use 300 dpi PNG and embedded DejaVu Serif SVG.
 for ext in ['svg','png']:
  fig.savefig(out/(stem+'.'+ext),dpi=300,bbox_inches='tight',pad_inches=.055,metadata={'Date':None} if ext=='svg' else None)
 embed_serif_fonts(out/(stem+'.svg'));plt.close(fig)
 with Image.open(out/(stem+'.png')) as im:w,h=im.size
 (out/(stem+'.caption.txt')).write_text(caption+'\n',encoding='utf8')
 record={'case_id':c['case_id'],'evidence_id':e['evidence_id'],'renderer':'tools/visuals/render_shared_cg_20261013.py','renderer_sha256':sha(Path(__file__)),'style':'Existing atlas C / DejaVu Serif / navy and teal','data':'plot-data.json','data_sha256':sha(out/'plot-data.json'),'upper_certificate':e.get('upper_certificate'),'lower_certificate':e.get('lower_certificate'),'snapshot':'2026-10-13 22:26 Asia/Shanghai','new_solver_run':False,'source_and_reuse_notice':'../../NOTICE.txt','source_basis':'../../SOURCE_BASIS.json','caption':caption,'exports':{ext:sha(out/(stem+'.'+ext)) for ext in ['png','svg']}}
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
 rows=[r for r in e['history'] if r['phase']==phase]
 fig=new_figure(c['city_name'],'Phase I restores feasibility' if phase=='I' else 'Phase II objective',c['case_id']+' / '+e['label'],figsize=(9,5.4))
 ax=fig.add_axes([.13,.22,.80,.54]);format_axes(ax)
 if not rows:
  ax.axis('off');ax.text(.5,.55,'Saved feasible FIFO seed',ha='center',fontsize=13,color=INK);ax.text(.5,.38,'No Phase-I RMP history',ha='center',fontsize=10)
  caption='This run begins from the separately checked feasible FIFO seed. No Phase-I RMP states were saved; an artificial-flow trajectory is not inferred.'
 else:
  x=np.array([r['round'] for r in rows]);y=np.array([r['artificial_mass' if phase=='I' else 'true_primal_objective'] for r in rows],dtype=float)
  ax.step(x,y,where='post',color=TEAL,lw=1.6)
  if phase=='I':
   ax.scatter(x,y,s=22,color=TEAL,zorder=4)
   ax.set_ylabel('Artificial flow ('+('original volume' if c['city']=='sioux-falls' else 'vehicles' if c['city']=='hong-kong' else 'PCE')+')')
   caption=f'All {len(rows)} saved Phase-I RMP states, unsmoothed, including true zero. The quantity is the saved artificial-demand total, not the perturbed Phase-I objective. Boston/Hong Kong total-flow staircase template. The shared-core snapshot has no per-OD artificial-flow history, so its reference heatmap cannot be reproduced from these records.'
  else:
   delta=np.r_[np.nan,np.diff(y)];tol=np.maximum(1,np.abs(y))*1e-12
   strict=delta < -tol;level=np.abs(delta)<=tol;other=~(strict|level)
   for mask,mark,label,face in [(strict,'o','Saved objective decrease',TEAL),(level,'s','Saved numerical nonincrease','white'),(other,'D','Initial / other saved state',BLUE)]:
    if mask.any():ax.scatter(x[mask],y[mask],s=24,marker=mark,facecolors=face,edgecolors=TEAL if face!=BLUE else BLUE,label=label,zorder=4)
   # A dual certificate is not relabelled as an independently solved arc-flow LP.
   same=e['upper_build']==e['lower_build'] and abs(e['gap_signed'])<=1e-8
   if same:ax.axhline(e['L'],ls='--',color=BLUE,lw=1,label='Certified same-instance lower bound')
   ax.set_ylabel('Objective ('+unit(c)+')');ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.legend(fontsize=8,loc='best')
   caption=f'All {len(rows)} saved Phase-II real-cost states from this run. The Boston objective-staircase template is used; marker categories are derived from consecutive saved values (relative numerical comparison tolerance 1e−12), not claimed as original solver commit labels. Bounds belong to their separate certificate card and never replace this trajectory. No cross-version line joins.'
  ax.set_xlabel('Saved Phase '+phase+' RMP round')
  if len(x)==1:ax.set_xlim(x[0]-.5,x[0]+.5);ax.set_xticks(x)
  else:ax.set_xlim(x[0]-.25,x[-1]+.3)
  fig.text(.13,.065,f'{len(rows)} saved states; RMP rounds are distinct from internal LP iterations.',fontsize=8.5)
 save(fig,c,e,stem,'Column generation: Phase I feasibility' if phase=='I' else 'Column generation: Phase II real cost',caption)

def pricing(c,e):
 fig=new_figure(c['city_name'],'Column pool and full-graph pricing',c['case_id']+' / '+e['label'],figsize=(12,7))
 rows=e['history'];ph2=[r for r in rows if r['phase']=='II'];ph1=[r for r in rows if r['phase']=='I']
 ax=fig.add_axes([.08,.49,.35,.25]);format_axes(ax);ax.set_title('a  Restricted-master pool',loc='left',weight='bold')
 ax.step(range(1,len(rows)+1),[r['column_count'] for r in rows],where='post',color=TEAL,marker='o',ms=3);ax.set(xlabel='Saved RMP state (both phases)',ylabel='Columns')
 for rs,pos,title,unit_label in [(ph2,[.57,.49,.35,.25],'b  Phase II reduced cost','Minimum reduced cost ('+('native cost' if c['city']=='sioux-falls' else 'min')+')'),(ph1,[.08,.12,.35,.23],'c  Phase I reduced cost','Phase-I objective units')]:
  ax=fig.add_axes(pos);format_axes(ax);ax.set_title(title,loc='left',weight='bold')
  if rs:
   xx=[r['round'] for r in rs];yy=[r['minimum_reduced_cost'] for r in rs];ax.step(xx,yy,where='post',color=BLUE,lw=1.4);ax.scatter(xx,yy,s=16,color=BLUE)
   if len(xx)==1:ax.set_xlim(xx[0]-.5,xx[0]+.5);ax.set_xticks(xx)
  else:ax.text(.5,.5,'No Phase-I RMP history',ha='center',transform=ax.transAxes,fontsize=9)
  ax.axhline(-1e-6,color=INK,ls='--',lw=.8);ax.set(xlabel='Saved RMP round',ylabel=unit_label)
 ax=fig.add_axes([.57,.12,.35,.23]);format_axes(ax);ax.set_title('d  Final original pricing gate',loc='left',weight='bold')
 if ph2:
  value=ph2[-1]['minimum_reduced_cost'];ax.scatter([0],[value],s=33,color=BLUE);ax.set_xticks([0],['Final Phase-II RMP']);lo=min(value,-1e-6);hi=max(value,0);margin=max(hi-lo,1e-6)*.28;ax.set_ylim(lo-margin,hi+margin);ax.set_xlim(-.6,.6);ax.annotate(f'{value:.7g}',(0,value),xytext=(8,8),textcoords='offset points',fontsize=8)
 ax.axhline(-1e-6,color=INK,ls='--',label='Original −10⁻⁶ gate');ax.set_ylabel('Reduced cost ('+('native cost' if c['city']=='sioux-falls' else 'min')+')');ax.legend(fontsize=8,loc='lower right')
 save(fig,c,e,'pricing','Column generation: pool growth and pricing','Boston four-panel pricing layout: complete saved pool growth, signed Phase-II and Phase-I pricing, and the final unchanged original gate. Phase-I objective units and Phase-II costs remain separate. Only a global pricing minimum was saved; no independent per-OD or ungenerated-path bars are manufactured. A small bound gap does not certify the final RMP pricing gate.')

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
   e['figures']=[f for f in e.get('figures',[]) if not any(f['id'].endswith('-'+s) for s in ['bounds','phase-i','phase-ii','pricing','nonbinding'])]
   if e.get('U') is None:continue
   bounds(c,e)
   if e['history']:
    series(c,e,'I','phase-i');series(c,e,'II','phase-ii');pricing(c,e)
   elif e['nonbinding_checks']:nonbinding(c,e)
  print(c['case_id'],flush=True)
 (AS/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':render()
