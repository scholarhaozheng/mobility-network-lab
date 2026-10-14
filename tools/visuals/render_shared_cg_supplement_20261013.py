"""Replot complete saved physical-flow vectors and Dev40/41 checkpoints.

No path optimization, original-data acquisition or CG solver is performed.
Physical projection verification occurred when plot JSON was prepared; this
renderer uses its complete vector and, where established, published geometry.
"""
import json,logging
from pathlib import Path
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm
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
 data=base.load(D/e['physical_flow_data']);values=np.asarray([r['integrated_flow'] for r in data['rows']]);ids=[r['physical_link_id'] for r in data['rows']];geo=data.get('geometry',{});geometry=geo.get('link_geometry',{})
 assert geometry and all(i in geometry for i in ids),'Complete same-ID geometry is required for the map template'
 coords=[np.asarray(geometry[i],dtype=float) for i in ids]
 local='Local kilometres' in geo.get('coordinate_system','');schematic='Schematic' in geo.get('coordinate_system','')
 # Existing geographic sources use lon/lat. Draw a local-km frame like the reference atlas.
 if not local and not schematic:
  xy=np.concatenate(coords);lon0,lat0=xy.mean(axis=0);scale=np.array([111.32*np.cos(np.deg2rad(lat0)),110.57]);coords=[(x-[lon0,lat0])*scale for x in coords]
 fig=base.new_figure(c['city_name'],'Final physical-link movement flow',c['case_id']+' / '+e['label'],figsize=(9,6))
 ax=fig.add_axes([.10,.16,.73,.59]);base.format_axes(ax,True)
 maximum=max(float(values.max()),1e-12);norm=PowerNorm(.5,vmin=0,vmax=maximum)
 ax.add_collection(LineCollection(coords,colors=base.ROAD,linewidths=.55,zorder=1))
 positive=values>0
 lc=LineCollection([coords[i] for i in np.flatnonzero(positive)],array=values[positive],cmap=base.FLOW_CMAP,norm=norm,linewidths=.65+1.7*np.sqrt(values[positive]/maximum),zorder=2)
 ax.add_collection(lc);ax.autoscale();ax.margins(.04);ax.set_aspect('equal');ax.set_xlabel('Schematic x' if schematic else 'Local easting (km)');ax.set_ylabel('Schematic y' if schematic else 'Local northing (km)')
 cb=fig.colorbar(lc,ax=ax,fraction=.035,pad=.03);cb.set_label('Integrated '+data['physical_flow_unit'],fontsize=8);cb.ax.tick_params(labelsize=7)
 cap=f"764e086 Boston/Hong Kong CG movement-only map template. Selected {c['case_id']} / {e['evidence_id']}: {len(values):,} directed physical links, {(values>0).sum():,} positive and {(values==0).sum():,} exact zeros. Projected path cost {data['projected_U']:.15g} matches U={e['U']:.15g}. Persistent IDs join this city's geometry; no static or other-method flow is reused. Square-root colour normalization; original integrated-flow units; virtual/wait/connector arcs excluded. "+('Schematic Sioux Falls topology, not geographic coordinates.' if schematic else 'Modelled accumulated movement, not observed traffic or instantaneous v/c.')
 save(fig,c,e,'physical-flow','Final physical-link movement flow',cap,'physical-flow.plot.json')
 p=AS/c['case_id']/e['evidence_id']/'physical-flow.source.json';s=base.load(p);s['complete_projection_inputs']=data['inputs'];s['geometry']={k:v for k,v in geo.items() if k!='link_geometry'};s['template_reference_commit']='764e086';s['plot_role']='CG physical movement map, not static assignment histogram';write(p,s)

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
