"""Pure R11 repairs of existing displayed figures from frozen saved plot data.
No optimization, assignment, path search, network acquisition, or original writes.
"""
from pathlib import Path
import argparse, json, hashlib, zipfile, sys
import numpy as np
import style as fs
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm, Normalize
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Polygon
from pyproj import Transformer
from shapely import wkt
from shapely.ops import transform

REPO=Path(__file__).resolve().parents[2]
DOC=REPO/'docs'
RESULT=[]
ORIGINAL={}
OUT=None

def js(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return fs.sha256(p)
def source(p,role):
 p=Path(p);ORIGINAL[str(p)]=sha(p)
 return {'public_path':p.relative_to(REPO).as_posix(),'sha256':sha(p),'role':role}
def ax(fig,rect,title='',geo=False):
 a=fig.add_axes(rect);fs.format_axes(a,map_axis=geo)
 if title:a.set_title(title,loc='left',fontsize=11,fontweight='bold',pad=8)
 return a

def export(fig,old,city,title,instance,panels,quantity,unit,caption,srcs,extra=None):
 old=Path(old);stem=OUT/city/old.stem
 srcs=[*srcs,source(old,'Original preserved displayed SVG'),source(old.with_suffix('.source.json'),'Original frozen figure record')]
 record={'figure_id':'R11-KEEP-'+city+'-'+old.stem,'city':city,'instance':instance,'role':'spatial_comparison','conclusion':title,'panels':panels,'quantity':quantity,'unit':unit,'renderer':{'public_path':Path(__file__).relative_to(REPO).as_posix(),'sha256':sha(__file__)},'original_asset':old.relative_to(REPO).as_posix(),'original_asset_sha256':sha(old),'numerical_equivalence':'EXACT_SAVED_VECTOR_AND_BIN_MATCH','original_bytes_unchanged':True,**(extra or {})}
 record=fs.export_figure(fig,stem,record,caption=caption,sources=srcs)
 files={ext:str(stem.with_suffix('.'+ext)) for ext in ['svg','png','pdf','source.json','caption.md']}
 RESULT.append({'original':old.relative_to(REPO).as_posix(),'path':old.relative_to(REPO).as_posix(),'city':city,'title':title,'caption':caption,'staged_stem':str(stem),'files':files,'status':'RENDERED_PENDING_VISUAL_QA','original_sha256':sha(old),'sources':srcs,'numerical_equivalence':record['numerical_equivalence']})
 return stem

def map_hist(fig,segments,flow,edges,counts,vmax=None,origin='Local',hist_title='b  All physical links'):
 a=ax(fig,[.08,.18,.365,.60],'a  Saved physical flow',True)
 segments=[np.asarray(s,dtype=float) for s in segments]
 vals=np.asarray(flow,dtype=float); assert len(vals)==len(segments)
 allxy=np.concatenate(segments); lo=allxy.min(axis=0);hi=allxy.max(axis=0);pad=(hi-lo)*.035
 a.add_collection(LineCollection(segments,colors=fs.ROAD,linewidths=.48,zorder=1))
 mask=vals>1e-12;norm=PowerNorm(.5,0,float(vmax or vals.max()))
 lc=LineCollection([s for s,m in zip(segments,mask) if m],cmap=fs.FLOW_CMAP,norm=norm,linewidths=1.4,zorder=3);lc.set_array(vals[mask]);a.add_collection(lc)
 a.set(xlim=(lo[0]-pad[0],hi[0]+pad[0]),ylim=(lo[1]-pad[1],hi[1]+pad[1]),xlabel='East–west (km)',ylabel='North–south (km)');a.set_anchor('NW')
 a.xaxis.set_major_locator(MaxNLocator(4));a.yaxis.set_major_locator(MaxNLocator(4))
 fig.canvas.draw();b=a.get_position()
 ca=fig.add_axes([b.x1+.018,b.y0+.075*b.height,.017,b.height*.85]);cb=fig.colorbar(lc,cax=ca);cb.set_label('PCE / modeled hour',fontsize=8);cb.ax.tick_params(labelsize=7)
 h=ax(fig,[.64,b.y0,.32,b.height],hist_title)
 got,_=np.histogram(vals,bins=edges);assert np.array_equal(got,np.asarray(counts)),(got,counts)
 h.bar(np.asarray(edges)[:-1],counts,width=np.diff(edges),align='edge',color=fs.TEAL,edgecolor='white',linewidth=.35)
 h.set(xlabel='Physical-link flow (PCE / modeled hour)',ylabel='Directed physical links');h.yaxis.set_major_locator(MaxNLocator(5,integer=True));h.xaxis.set_major_locator(MaxNLocator(4))
 return {'map':{'count':len(vals),'positive_overlay_count':int(mask.sum()),'original_geometry_exact':True,'normalization':'PowerNorm(gamma=0.5)','bounds':[0,float(vmax or vals.max())]},'histogram':{'edges':list(edges),'counts':list(counts),'includes_exact_zeros':True,'count':len(vals)},'alignment':{'map_bounds':list(b.bounds),'histogram_bounds':list(h.get_position().bounds),'top_and_bottom_equal':True}}

def fw(city):
 old=DOC/f'assets/plot-semantics-r9/{city}/fw-physical-flow.svg';pd=old.with_suffix('.plot_data.json');d=js(pd);meta=js(old.with_suffix('.source.json'))
 title='Frank–Wolfe: physical flow and distribution'
 scope='25 zones · 600 ODs · 08:00–09:00 HBW' if city=='ann-arbor' else 'Original four-stage instance · one modeled hour'
 fig=fs.new_figure(city,title,scope,figsize=(10.6,6.5))
 hist=d['histogram'];parts=map_hist(fig,d['display_segments_local_km'],d['volume_pce'],hist['bins'],hist['counts'])
 parts.update({'projected_crs':d['projected_crs'],'local_origin_projected_metres':d['local_origin_projected_metres'],'physical_link_ids_exact':True,'saved_check_count':d['saved_check_count'],'actual_updates':d['actual_updates']})
 cap=meta['caption']+' R11 layout repair: map and all-link histogram share measured top and bottom panel bounds. The original saved physical-link IDs, exact flow vector, geographic vertices, display offsets, histogram edges and counts remain unchanged.'
 export(fig,old,city,title,scope,parts,'Saved physical flow; all-link frequency','PCE / modeled hour; directed physical links',cap,[source(pd,'Complete saved physical IDs, flow, geometry and histogram bins')])

def ann_transit():
 city='ann-arbor';old=DOC/'assets/city-alignment-r3/ann-arbor/aa-t01.svg';pd=old.with_suffix('.plot_data.json');gp=old.parent/'aa-s01.plot_data.json';d=js(pd);g=js(gp);meta=js(old.with_suffix('.source.json'))
 to_m=Transformer.from_crs(4326,26917,always_xy=True).transform;ox,oy=g['origin_m']
 def local(x,y,z=None):return (np.asarray(x)-ox)/1000,(np.asarray(y)-oy)/1000
 def xy(ll):
  q=np.asarray(ll,float);x,y=to_m(q[:,0],q[:,1]);return np.column_stack(local(x,y))
 lines=[xy(wkt.loads(s).coords) for s in g['physical_geometry_wkt']];polys=[transform(local,transform(to_m,wkt.loads(s))) for s in g['zone_geometry_wkt']]
 title='Scheduled stops and modeled mode availability';fig=fs.new_figure(city,title,'U-M service · 5 October 2026',figsize=(10.5,6.4));a=ax(fig,[.07,.18,.43,.60],'a  Saved U-M schedule stops',True)
 a.add_collection(LineCollection(lines,colors=fs.ROAD,linewidths=.4,zorder=1))
 for p in polys:a.add_patch(Polygon(np.asarray(p.exterior.coords),closed=True,facecolor='#edf5f2',edgecolor='#9cbeb8',lw=.6,zorder=2,alpha=.7))
 pts=xy([(s['longitude'],s['latitude']) for s in d['stops']]);a.scatter(pts[:,0],pts[:,1],c=fs.BLUE,s=15,edgecolors='white',lw=.4,zorder=5)
 a.set(xlim=(-3.05,3.05),ylim=(-3.05,3.05),xlabel='East–west (km)',ylabel='North–south (km)');a.set_anchor('NW');fig.canvas.draw();b=a.get_position()
 h=ax(fig,[.66,b.y0,.27,b.height],'b  Available directed OD pairs');vals=[d['availability'][m] for m in ['drive','transit','walk']]
 h.barh(range(3),vals,color=[fs.TEAL,fs.BLUE,fs.INK],height=.55);h.set(yticks=range(3),yticklabels=['Drive','U-M bus','Walk'],xlabel='Available ODs (out of 600)',xlim=(0,690));h.invert_yaxis();h.grid(False);h.grid(axis='x',color=fs.GRID,lw=.5)
 for i,v in enumerate(vals):h.text(v+12,i,str(v),va='center',fontsize=9)
 cap=meta['caption']+' R11 layout repair: both panels share the actual map top and bottom bounds; the stop count is stated here rather than overprinted on the map.'
 export(fig,old,city,title,'25 zones / 600 directed ODs / saved U-M service 2026-10-05',{'map':{'stops':63,'physical_links':len(lines),'zones':len(polys),'origin_m':[ox,oy],'projection':'EPSG:26917','limits_local_km':[-3.05,3.05]},'availability':dict(d['availability']),'alignment':{'map_bounds':list(b.bounds),'bar_bounds':list(h.get_position().bounds),'top_and_bottom_equal':True}},'Saved schedule stop location; modeled mode availability','local km; directed OD pairs',cap,[source(pd,'Saved stop positions and exact availability counts'),source(gp,'Original accepted zone and road geometries with projection origin')])

def uc_finite(project):
 city='urbana-champaign';old=DOC/f'assets/plot-semantics-r9/{city}/s72-finite-map-distribution.svg';pd=old.with_suffix('.plot_data.json');d=js(pd);meta=js(old.with_suffix('.source.json'));gp=DOC/d['public_geometry_identity']['path'];assert sha(gp)==d['public_geometry_identity']['sha256'];g=js(gp)
 assert g['gids']==d['physical_solver_link_ids'];assert g['source_gmns_ids']==d['source_gmns_ids']
 zpath=project/'deliveries/urbana_champaign_algorithm_transfer_r1/MCL_C02_Urbana_Algorithm_Transfer_R2_Private_Full.zip'
 member='MCL_C02_Urbana_Algorithm_Transfer_R2/run/S/finite_72/independent_check.json'
 with zipfile.ZipFile(zpath) as z:b=z.read(member)
 h=hashlib.sha256(b).hexdigest();assert h=='184a1de932a6c01928adf0fa1e2155afe9430ad419916a3eeb6de68bdaeb0e65';check=json.loads(b)
 assert all(r['residual_pce']==0 for r in d['all72_od_checks']);assert check['max_od_residual']==0 and check['demand_total']==d['frozen_demand_total_pce']
 fwdata=js(old.parent/'s72-fw-map-distribution.plot_data.json');vmax=max(max(d['own_saved_flow_pce_per_hour']),max(fwdata['own_saved_flow_pce_per_hour']))
 title='Finite paths: physical flow and distribution';fig=fs.new_figure(city,title,'S72 · 72 selected ODs · one modeled hour',figsize=(10.6,6.5));histo=d['panels']['histogram'];parts=map_hist(fig,g['segments'],d['own_saved_flow_pce_per_hour'],histo['edges'],histo['counts'],vmax)
 parts['physical_solver_link_ids_exact']=True;parts['source_gmns_ids_exact']=True;parts['projection']=d['projection'];parts['shared_same_instance_FW_colour_scale']=True
 check_summary={k:check[k] for k in ['instance_signature','method','max_od_residual','od_residual_sum','od_residual_l1','max_link_reconstruction_error','demand_total','path_count','node_od','gates','status']}
 cap=meta['caption']+' R11 layout repair: the map and histogram share measured bounds. The 72 zero-valued OD residuals are retained in the linked endpoint table, with the frozen mass-balance gates (absolute 1e-6 PCE; relative 1e-8; total OD L1 relative 1e-8). Their absence from a third status-only plot does not remove any OD record or change the accepted status.'
 stem=export(fig,old,city,title,'S72 / 72 selected ODs / 321.6296598827645 PCE in one hour',parts,'Own saved finite physical flow; all-link frequency','PCE / modeled hour; directed physical arcs',cap,[source(pd,'Own finite vector, bins and all 72 saved OD balance checks'),source(gp,'Exactly matched persistent physical solver IDs and split geometry'),source(old.parent/'s72-fw-map-distribution.plot_data.json','Same-instance saved FW vector for the shared color maximum'),{'source_id':'UC_R2_S72_FINITE_INDEPENDENT_CHECK','sha256':hashlib.sha256(b).hexdigest(),'role':'Frozen independent endpoint check; exact gate field names retained'}],{'removed_status_panel':{'reason':'All 72 OD residual values are exactly zero; endpoint table is clearer','unit':'PCE','source_field':'all72_od_checks[].residual_pce','independent_summary':check_summary}})
 table={'schema':'mcl_endpoint_table_r11','instance':'UC R2 S72 finite','quantity':'Saved path-flow sum minus frozen OD demand','unit':'PCE','source_fields':['all72_od_checks[].demand_pce','all72_od_checks[].saved_path_flow_sum_pce','all72_od_checks[].residual_pce'],'rows':d['all72_od_checks'],'independent_check':check_summary,'source_sha256':sha(pd),'independent_check_sha256':hashlib.sha256(b).hexdigest(),'gate_units':{'max_od_error_abs':'PCE','max_od_error_rel':'dimensionless','total_od_l1_rel':'dimensionless','negative_flow_abs':'PCE','link_reconstruction_abs':'PCE','full_relative_gap_abs':'dimensionless'}}
 stem.with_suffix('.endpoint-table.json').write_text(json.dumps(table,ensure_ascii=False,indent=2),'utf8')
 lines=['# S72 finite OD mass-balance endpoint','',f"All 72 saved OD residuals are exactly 0 PCE. Status: `{check['status']}`.",'','Frozen gates: max OD error absolute 1e-6 PCE; max OD error relative 1e-8; total OD L1 relative 1e-8. Gate field names and remaining checks are retained in JSON.','','| OD index | Frozen demand (PCE) | Saved path-flow sum (PCE) | Residual (PCE) |','|---:|---:|---:|---:|']
 lines += [f"| {r['od_index']} | {r['demand_pce']:.17g} | {r['saved_path_flow_sum_pce']:.17g} | {r['residual_pce']:.17g} |" for r in d['all72_od_checks']]
 stem.with_suffix('.endpoint-table.md').write_text('\n'.join(lines)+'\n','utf8');RESULT[-1]['files'].update({ext:str(stem.with_suffix('.'+ext)) for ext in ['endpoint-table.json','endpoint-table.md']})

def chicago_pricing():
 city='chicago';old=DOC/f'assets/plot-semantics-r9/{city}/cg-pricing-closure.svg';pd=old.with_suffix('.plot_data.json');d=js(pd);meta=js(old.with_suffix('.source.json'));title='Column generation: full-graph pricing closure'
 fig=fs.new_figure(city,title,'R2 T4 · both phases · all four commodities',figsize=(10.6,7.15));gs=fig.add_gridspec(2,2,left=.085,right=.91,top=.79,bottom=.13,wspace=.46,hspace=.32,height_ratios=[1,.70]);parts={}
 for i,(phase,unit,tol) in enumerate([(1,'dimensionless',d['gates']['phase_I_negative_reduced_cost_abs']),(2,'min',d['gates']['phase_II_negative_reduced_cost_abs_min'])]):
  rr=[r for r in d['saved_history'] if r['phase']==phase];label='I' if phase==1 else 'II';rounds=[r['round'] for r in rr];mins=[r['min_full_graph_reduced_cost'] for r in rr];v=np.asarray([r['pricing_by_od'] for r in rr]).T;assert np.array_equal(v.min(axis=0),mins)
  a=fig.add_subplot(gs[0,i]);fs.format_axes(a);a.step(rounds,mins,where='post',color=fs.TEAL,lw=1.6);a.scatter(rounds,mins,s=7,color=fs.TEAL,zorder=4);a.axhline(-tol,color=fs.BLUE,ls='--',lw=1.1,label=f'Gate: ≥ −{tol:g}');a.set(xlabel=f'Saved Phase {label} round',ylabel='Minimum reduced cost ('+unit+')');a.set_title(('a' if i==0 else 'b')+f'  Phase {label}: all-OD minimum',loc='left',fontsize=11,fontweight='bold',pad=8);a.legend(fontsize=7.5,loc='center');a.text(.98,.92,'Final: '+f'{mins[-1]:.3g}',transform=a.transAxes,ha='right',va='top',fontsize=8);a.xaxis.set_major_locator(MaxNLocator(6,integer=True))
  a=fig.add_subplot(gs[1,i]);im=a.imshow(v,origin='upper',aspect='auto',interpolation='nearest',cmap=fs.FLOW_CMAP.reversed(),norm=Normalize(float(v.min()),0),extent=(-.5,len(rr)-.5,3.5,-.5));a.set_yticks(range(4),d['od_order']);a.set_xlabel(f'Saved Phase {label} round');a.set_ylabel('Commodity');a.xaxis.set_major_locator(MaxNLocator(6,integer=True));a.set_title(('c' if i==0 else 'd')+f'  Phase {label}: every OD',loc='left',fontsize=11,fontweight='bold',pad=8)
  cb=fig.colorbar(im,ax=a,fraction=.043,pad=.04);cb.set_label('Reduced cost ('+unit+')',fontsize=8);cb.ax.tick_params(labelsize=7)
  parts['phase_'+label]={'rows':len(rr),'OD_count':4,'saved_column':'pricing_by_od','matrix':v.tolist(),'minimum':mins,'rounds':rounds,'unit':unit,'full_graph_minimum_check':'Exact array equality to min of all four saved OD reduced costs at every round','negative_gate':-tol,'heatmap_normalization':[float(v.min()),0]}
 cap=meta['caption']+' R11 layout repair: compact two-row spacing and shared serif bold panel headings; all 268 saved rounds and all four OD pricing values per round remain unchanged.'
 export(fig,old,city,title,'R2 T4 / 4 commodities / phase I 208 states and phase II 60 states',parts,'Full-graph reduced cost, all-OD minimum and each OD','Phase I dimensionless; Phase II min',cap,[source(pd,'Complete released CG history and phase-specific gates')],{'role':'iteration','saved_states':268,'numerical_equivalence':'EXACT_SAVED_HISTORY_AND_PER_OD_MATRIX_MATCH'})

def main():
 global OUT
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,required=True);p.add_argument('--project-root',type=Path,required=True);p.add_argument('--only',choices=['chicago-pricing']);a=p.parse_args();OUT=a.output_root
 if a.only:
  chicago_pricing()
 else:
  for city in ['ann-arbor','urbana-champaign','ithaca','chicago','pittsburgh']:fw(city)
  ann_transit();uc_finite(a.project_root);chicago_pricing()
 assert all(sha(Path(p))==h for p,h in ORIGINAL.items())
 if a.only and (OUT/'MANIFEST.json').exists():
  prev=js(OUT/'MANIFEST.json');items=[r for r in prev['figures'] if r['path'] not in {r['path'] for r in RESULT}]+RESULT;RESULT[:]=items
 out={'schema':'mcl_keep_repairs_render_r11','count':len(RESULT),'solver_calls':0,'matcher_calls':0,'page_mutations':0,'original_bytes_unchanged':True,'figures':RESULT};(OUT/'MANIFEST.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8')
 print(json.dumps({'count':len(RESULT),'output':str(OUT),'solver_calls':0}))
if __name__=='__main__':main()
