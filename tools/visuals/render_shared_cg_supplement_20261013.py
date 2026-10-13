"""Replot complete saved physical-flow vectors and Dev40/41 checkpoints.

No path optimization, original-data acquisition or CG solver is performed.
Physical projection verification occurred when plot JSON was prepared; this
renderer uses its complete vector and, where established, published geometry.
"""
import json,logging
from pathlib import Path
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import render_shared_cg_20261013 as base
logging.getLogger('fontTools.subset').setLevel(logging.ERROR)
AS=base.AS;D=base.ROOT/'docs'
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def save(fig,c,e,stem,title,caption,datafile='plot-data.json'):
 base.save(fig,c,e,stem,title,caption)
 p=AS/c['case_id']/e['evidence_id']/(stem+'.source.json');s=base.load(p)
 s.update(renderer=Path(__file__).relative_to(base.ROOT).as_posix(),renderer_sha256=base.sha(Path(__file__)),style_helper='tools/visuals/render_shared_cg_20261013.py',style_helper_sha256=base.sha(Path(base.__file__)),data=datafile,data_sha256=base.sha(p.parent/datafile))
 write(p,s);e['figures'][-1]['data']=(p.parent/datafile).relative_to(D).as_posix()
def physical(c,e):
 data=base.load(D/e['physical_flow_data']);values=np.asarray([r['integrated_flow'] for r in data['rows']]);ids=[r['physical_link_id'] for r in data['rows']];geometry=data.get('geometry',{}).get('link_geometry',{});mapped=bool(geometry) and all(i in geometry for i in ids)
 fig=base.new_figure(c['city_name'],'Physical flow and distribution',c['case_id']+' · '+e['label'],figsize=(10,5.3));ax=fig.add_axes([.07,.23,.48,.48]);right=fig.add_axes([.66,.23,.30,.48]);base.format_axes(right)
 if mapped:
  coords=[geometry[i] for i in ids];lc=LineCollection(coords,array=values,cmap='YlGnBu',norm=Normalize(0,max(values)),linewidths=.45+2.4*values/max(values));ax.add_collection(lc);ax.autoscale();ax.set_aspect('equal');ax.axis('off');cb=fig.colorbar(lc,ax=ax,fraction=.04,pad=.02);cb.set_label(data['physical_flow_unit']);ax.set_title('Same-U movement-flow projection',fontsize=10)
 else:
  base.format_axes(ax);ax.plot(np.arange(1,len(values)+1),np.sort(values)[::-1],color=base.TEAL,lw=1.5);ax.set_xlabel('All physical model edges, sorted by flow');ax.set_ylabel('Integrated '+data['physical_flow_unit']);ax.set_title('Complete physical-edge distribution',fontsize=10)
 right.hist(values,bins=min(45,max(10,int(np.sqrt(len(values))))),color=base.TEAL,edgecolor='white',linewidth=.35);right.set_xlabel('Integrated '+data['physical_flow_unit']);right.set_ylabel('Number of physical edges');right.set_title('Same complete vector',fontsize=10)
 fig.text(.075,.105,f'{len(values):,} physical edges · {np.count_nonzero(values>1e-10):,} positive above 1e−10 · objective projection checked against selected U',fontsize=8.7)
 fig.text(.075,.048,'Time-integrated modeled movement; not observed traffic or an instantaneous v/c.',fontsize=8.5)
 cap=f"Complete saved-path projection for {c['case_id']} / {e['evidence_id']}: {len(values):,} physical edges; reconstructed path cost {data['projected_U']:.15g} matches selected U={e['U']:.15g}. Movement flow is integrated over the frozen releases. Virtual/wait/connector arcs are excluded. Split physical model edges keep their separate IDs. "+('Only the already-published road geometry is reused; all flow values come from this selected run.' if mapped else 'This complete edge distribution does not assert an unverified geographic join.')
 save(fig,c,e,'physical-flow','Column generation: physical flow and distribution',cap,'physical-flow.plot.json')
 p=AS/c['case_id']/e['evidence_id']/'physical-flow.source.json';s=base.load(p);s['complete_projection_inputs']=data['inputs'];write(p,s)
def research(c,e):
 data=base.load(AS/c['case_id']/e['evidence_id']/'plot-data.json')
 if e['evidence_id']=='dev40-research':
  fig=base.new_figure(c['city_name'],'Dev40: actual source-generated column rounds',c['case_id']+' · research record',figsize=(9,4.7));ax=fig.add_axes([.12,.23,.8,.48]);base.format_axes(ax);xx=[r['round'] for r in data['round_history']]+[4];yy=[r['restricted_delta'] for r in data['round_history']]+[e['U']-data['fresh_source_base_upper']];ax.step(xx,yy,where='post',color=base.TEAL);ax.scatter(xx,yy,color=base.TEAL,s=35);ax.set_xticks(xx,['RMP 1','RMP 2','RMP 3','Final RMP']);ax.set_ylabel('Restricted cost change vs fresh base (PCE·min)');fig.text(.12,.07,'Partial pricing in the three add rounds; separate full-Q bound certificate remains OPEN.',fontsize=9)
  save(fig,c,e,'research-rounds','Dev40: three add rounds and final RMP','Saved restricted objective changes against this run’s own fresh seed. The fourth point is the saved final RMP, not a fourth column-add round. No historical best endpoint is spliced into the curve.')
 elif e['evidence_id']=='dev41-checkpoint':
  # Field labels below are fixed checkpoint quantities, checked against the archived JSON.
  fig=base.new_figure(c['city_name'],'Dev41: solved pool versus pending columns',c['case_id']+' · checkpoint, no final certified bounds',figsize=(9,4.8));ax=fig.add_axes([.12,.26,.8,.43]);base.format_axes(ax);ax.bar([0,1,2],[data['history'][-1]['columns_before'],data['history'][-1]['positive_columns'],data['column_count']],color=[base.BLUE,base.TEAL,'#bcccd0']);ax.set_xticks([0,1,2],['RMP 2: solved columns','RMP 2: positive columns','After adding: pending pool']);ax.set_ylabel('Columns (not CG iterations)');fig.text(.12,.1,'32 internal LP iterations belong to RMP 2; the 1200-column pool has not been solved.',fontsize=9)
  save(fig,c,e,'checkpoint-pool','Dev41: actual checkpoint and pending RMP','The saved checkpoint records a 600-column solved RMP, 314 positive columns, then 600 additional columns. The resulting 1200-column pool is pending a new RMP. No final objective, lower bound or convergence claim is supplied.')
def main():
 cat=base.load(AS/'catalog.json')
 for c in cat['cases']:
  for e in c['evidence']:
   stems=['physical-flow'] if e.get('physical_flow_data') else ['research-rounds'] if e['evidence_id']=='dev40-research' else ['checkpoint-pool'] if e['evidence_id']=='dev41-checkpoint' else []
   if not stems:continue
   old=e['figures'];e['figures']=[f for f in old if not any(f['id'].endswith('-'+s) for s in stems)]
   if e.get('physical_flow_data'):physical(c,e)
   else:research(c,e)
   order={f['id']:i for i,f in enumerate(old)};e['figures'].sort(key=lambda f:order.get(f['id'],999))
  print(c['case_id'],flush=True)
 write(AS/'catalog.json',cat)
if __name__=='__main__':main()
