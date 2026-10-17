"""Current V1 physical-flow helper; no historical curve renderers or solver.

Invoke tools/visuals/render_cg_v1_20261017.py to reproduce the displayed figures.
That entry supplies the output writer while this helper preserves map geometry.
"""
from pathlib import Path
import json
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm
from berkeley_alignment_r2.atlas_style import new_figure,format_axes,INK,ROAD,FLOW_CMAP
R=Path(__file__).resolve().parents[2];D=R/'docs'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def scope(c):return f"Dev48 · {c['OD']:,} OD · {c['case_id'].split('_')[-1]} ×{c['scale']:g}"
def save(*args,**kwargs):
 raise RuntimeError('Use render_cg_v1_20261017.py with --redraw-maps or --maps-only.')
def physical(c,centered=False):
 data=read(D/next(f['data']for f in c['figures']if f['id'].endswith('physical-flow')));values=np.array([r['integrated_flow']for r in data['rows']]);ids=[r['physical_link_id']for r in data['rows']];geo=data['geometry'];coords=[np.array(geo['link_geometry'][i],float)for i in ids];local='Local kilometres'in geo.get('coordinate_system','');schematic='Schematic'in geo.get('coordinate_system','')
 if not local and not schematic:
  xy=np.concatenate(coords);lon0,lat0=xy.mean(axis=0);scale=np.array([111.32*np.cos(np.deg2rad(lat0)),110.57]);coords=[(x-[lon0,lat0])*scale for x in coords]
 fig=new_figure(c['city_name'],'Final physical-link movement flow',scope(c),figsize=(8,4.394)if centered else(9,6));ax=fig.add_axes([.14,.18,.70,.60]if centered else[.10,.16,.73,.59]);format_axes(ax,True);maximum=max(float(values.max()),1e-12);norm=PowerNorm(.5,vmin=0,vmax=maximum)
 ax.add_collection(LineCollection(coords,colors=ROAD,linewidths=.55,zorder=1));positive=values>0;lc=LineCollection([coords[i]for i in np.flatnonzero(positive)],array=values[positive],cmap=FLOW_CMAP,norm=norm,linewidths=.65+1.7*np.sqrt(values[positive]/maximum),zorder=2);ax.add_collection(lc);ax.autoscale();ax.margins(.04);ax.set_aspect('equal');ax.set_xlabel('Schematic x'if schematic else'Local easting (km)');ax.set_ylabel('Schematic y'if schematic else'Local northing (km)');cb=fig.colorbar(lc,ax=ax,fraction=.035,pad=.03);cb.set_label('Integrated '+data['physical_flow_unit'],fontsize=8);cb.ax.tick_params(labelsize=7)
 if centered:
  # Center the rendered map/colorbar group, preserving equal geographic scale.
  fig.canvas.draw();renderer=fig.canvas.get_renderer()
  boxes=[axis.get_tightbbox(renderer)for axis in [ax,cb.ax]]
  offset=.5-(min(b.x0 for b in boxes)+max(b.x1 for b in boxes))/(2*fig.bbox.width)
  for axis in [ax,cb.ax]:
   box=axis.get_position();axis.set_position([box.x0+offset,box.y0,box.width,box.height])
  for text in fig._mcl_header_artists:text.set_x(.5);text.set_ha('center')
 cap=f"{c['case_id']} / {c['run_id']} / Dev48. Full same-run movement vector: {len(values):,} directed model physical links, {(values>0).sum():,} positive and {(values==0).sum():,} exact zeros. Integrated over all {c['events']:,} original release events and the full arrival tail; {data['physical_flow_unit']}, not hourly flow or instantaneous v/c. Recomputed original path cost {data['projected_U']:.16g}; independent U={c['U']:.16g}. "+('Full AON/FIFO base minus transferred donor mass plus selected replacement paths; signatures and shared group mass checked. 'if c['solver_branch']=='new_joint_delta_cg'else'')+"Persistent physical IDs join same-city geometry only; no other-method traffic is reused. Virtual, wait, connector and turn arcs are excluded. Original separate physical subedges retain their geometry; no parent-road double aggregation. Square-root colour normalization spans the actual vector. "+('Schematic Sioux topology, not geographic coordinates.'if schematic else'Model scenario, not observed traffic.')
 return save(c,fig,'physical-flow','Final physical-link movement flow',cap)
