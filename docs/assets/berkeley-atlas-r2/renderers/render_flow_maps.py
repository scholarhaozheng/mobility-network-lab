"""Render saved-result physical flow comparisons; no solver or checkpoint access."""
import csv,json,math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm,TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator,FormatStrFormatter
from shapely import wkt
from plot_common import *

flow_rows=read_csv('admm_physical_flow.csv')
geometry_rows=read_csv('physical_geometry.csv')
flow={r['link_id']:r for r in flow_rows}
assert len(flow_rows)==len(flow)==len(geometry_rows)==2150
assert set(flow)=={r['link_id'] for r in geometry_rows}
ids=[r['link_id'] for r in geometry_rows]
segments=[np.asarray(wkt.loads(r['geometry_wkt']).coords) for r in geometry_rows]
all_xy=np.concatenate(segments)
low=all_xy.min(axis=0);high=all_xy.max(axis=0);span=high-low
extent=(low[0]-.035*span[0],high[0]+.035*span[0],low[1]-.035*span[1],high[1]+.035*span[1])
latitude=float(all_xy[:,1].mean());aspect=1/math.cos(math.radians(latitude))
lp=np.array([float(flow[k]['LP_flow_pce']) for k in ids])
cg=np.array([float(flow[k]['CG_flow_pce']) for k in ids])
lr=np.array([float(flow[k]['LR_flow_pce']) for k in ids])
admm=np.array([float(flow[k]['ADMM_flow_pce']) for k in ids])
delta=admm-lp;movement=np.array([int(flow[k]['has_movement'])==1 for k in ids])
assert np.array_equal(lp,cg) and np.array_equal(lp,lr)
assert np.allclose(delta,[float(flow[k]['ADMM_minus_LP_pce']) for k in ids],atol=0,rtol=0)
assert movement.sum()==2013 and (~movement).sum()==137
vmax=float(max(lp.max(),admm.max()));dmax=float(abs(delta).max())
absolute_norm=PowerNorm(gamma=.5,vmin=0,vmax=vmax)
signed_norm=TwoSlopeNorm(vmin=-dmax,vcenter=0,vmax=dmax)

contracts={
 'admm_physical_flow_comparison':{'core_conclusion':'Accepted T4 ADMM and independent same-instance LP have close objectives but distinct saved physical-link flows, with maximum absolute difference about 0.991 PCE.','archetype':'quantitative grid','panels':['ADMM own-x physical projection','Independent LP on the same graph','Signed ADMM minus LP','All2150physical-link scatter with identity'],'backend':'Python/matplotlib','exports':['300dpi PNG','editable SVG','PDF','exact plot-data JSON','caption','source record'],'risks':['Do not confuse objective acceptance with link-flow equality.','Absolute maps share one PowerNorm(.5); signed difference has its own symmetric scale.','All2150 IDs are retained;137 links have no movement support in the bounded T4 graph.','PCE is per bounded departure instance, not PCE/hour.']},
 'lp_cg_lr_physical_flow':{'core_conclusion':'The three accepted saved T4 physical projections (LP,CG,LR recovery) coincide across all2150physical links in this particular instance.','archetype':'quantitative grid','panels':['Common physical projection on full road geography','All-link identity scatter and exact equality summary'],'backend':'Python/matplotlib','exports':['300dpi PNG','editable SVG','PDF','exact plot-data JSON','caption','source record'],'risks':['This is equality of aggregate physical projections, not identical algorithm paths or a general theorem.','LR flow is its own feasible recovery, not a substituted LP flow.']}}
(HERE/'FLOW_FIGURE_CONTRACT.json').write_text(json.dumps(contracts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def map_axes(ax,title):
    format_axes(ax,map_axis=True)
    ax.set_aspect(aspect)
    ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:])
    ax.set_xlabel('Longitude (°E)');ax.set_ylabel('Latitude (°N)')
    ax.xaxis.set_major_locator(MaxNLocator(3));ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'));ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax.set_title(title,loc='left',weight='bold',pad=9)
    ax.add_collection(LineCollection(segments,colors='#d8dfe2',linewidths=.38,zorder=1))
    ax.add_collection(LineCollection([s for s,m in zip(segments,movement) if not m],colors='#a9b3ba',linewidths=.48,linestyles='dotted',zorder=2))

def absolute_map(ax,values,title,fig):
    map_axes(ax,title)
    positive=np.flatnonzero(values>0)
    col=LineCollection([segments[i] for i in positive],array=values[positive],cmap=FLOW_CMAP,norm=absolute_norm,linewidths=.45+1.15*absolute_norm(values[positive]),zorder=3)
    ax.add_collection(col)
    box=ax.get_position()
    cbax=fig.add_axes([box.x0,box.y0-.52/fig.get_figheight(),box.width,.08/fig.get_figheight()])
    cb=fig.colorbar(col,cax=cbax,orientation='horizontal')
    cb.set_ticks(np.linspace(0,vmax,5));cb.ax.xaxis.set_major_formatter(FormatStrFormatter('%.2g'))
    cb.set_label('PCE / bounded T4 instance',fontsize=8)
    cb.ax.tick_params(labelsize=7,pad=2,length=2)
    return col

def signed_map(ax,fig):
    map_axes(ax,'c  ADMM minus LP')
    nonzero=np.flatnonzero(delta!=0)
    col=LineCollection([segments[i] for i in nonzero],array=delta[nonzero],cmap=DIFF_CMAP,norm=signed_norm,linewidths=.45+1.15*np.sqrt(abs(delta[nonzero])/dmax),zorder=3)
    ax.add_collection(col)
    box=ax.get_position()
    cbax=fig.add_axes([box.x0,box.y0-.52/fig.get_figheight(),box.width,.08/fig.get_figheight()])
    cb=fig.colorbar(col,cax=cbax,orientation='horizontal')
    cb.set_ticks(np.linspace(-dmax,dmax,5));cb.ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    cb.set_label('ADMM − LP (PCE)',fontsize=8);cb.ax.tick_params(labelsize=7,pad=2,length=2)

def scatter_axes(ax,x,y,title,annotation,ylabel):
    format_axes(ax)
    m=max(float(x.max()),float(y.max()))
    ax.plot([0,m],[0,m],linestyle='--',color=INK,linewidth=1,label='Identity',zorder=1)
    ax.scatter(x,y,s=16,facecolors='white',edgecolors=TEAL,linewidths=.7,alpha=.8,label='All 2,150 links',zorder=2)
    ax.set_xlim(-.035*m,1.055*m);ax.set_ylim(-.035*m,1.055*m)
    ax.set_aspect('auto')
    ax.set_title(title,loc='left',weight='bold',pad=9)
    ax.set_xlabel('Independent LP (PCE / instance)');ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.text(.035,.965,annotation,transform=ax.transAxes,va='top',fontsize=8.5)
    ax.legend(loc='lower right',fontsize=7.5)

def panel_box(fig,left,top,width=.375):
    height=width*fig.get_figwidth()/fig.get_figheight()*(extent[3]-extent[2])/(extent[1]-extent[0])*aspect
    return [left,top-height,width,height]

fig=new_figure('berkeley','ADMM and LP physical-link flow','T4 / 4 OD / 30 s × 165 steps',figsize=(10.4,7.0))
a=fig.add_axes(panel_box(fig,.085,.80));b=fig.add_axes(panel_box(fig,.585,.80))
c=fig.add_axes(panel_box(fig,.085,.39));d=fig.add_axes(panel_box(fig,.585,.39))
absolute_map(a,admm,'a  ADMM own x · outer 170',fig)
absolute_map(b,lp,'b  Independent same-graph LP',fig)
signed_map(c,fig)
scatter_axes(d,lp,admm,'d  All matched physical links',f'n = 2,150 links\nmax |ADMM − LP| = {dmax:.3f} PCE\nObjective difference = 0.00532%','ADMM own x (PCE / instance)')
fig.text(.085,-.025,'Full 2,150-link road context; 137 dotted links have no movement arc in T4.  © OpenStreetMap contributors, ODbL 1.0.',fontsize=7.3,color=INK)
caption=('Saved Berkeley T4 physical-link projections for four assumed first-bin OD pulses (10.439304601 PCE), using the accepted ADMM own x at completed outer170 and an independently solved same-graph LP. '
         'Panels a–b share a PowerNorm(0.5) absolute color scale. Panel c uses a separate symmetric ADMM-minus-LP scale; panel d contains all2,150matched physical IDs and an identity line. '
         f'The maximum physical-flow difference is {dmax:.15g} PCE, despite a relative objective difference of0.00531869%. The objective gate does not establish link-flow equality. '
         'All 2,150 original road geometries are retained with longitude/latitude aspect correction. The 137 links without a movement arc in the bounded T4 graph remain zero and are shown dotted; missing sparse LP entries are zero-filled by physical ID. '
         'Flows are PCE over this bounded departure instance, not hourly counts or observed traffic. No optimizer was rerun. © OpenStreetMap contributors, ODbL1.0.')
caption=caption.replace('outer170','outer 170').replace('all2,150','all 2,150').replace('of0.005','of 0.005').replace('The137links','The 137 links').replace('ODbL1.0','ODbL 1.0')
data={'link_id':ids,'LP_flow_pce':lp.tolist(),'ADMM_flow_pce':admm.tolist(),'ADMM_minus_LP_pce':delta.tolist(),'has_movement':movement.tolist(),'absolute_scale':{'norm':'PowerNorm','gamma':.5,'vmin':0,'vmax':vmax},'difference_scale':{'norm':'TwoSlopeNorm','vmin':-dmax,'vcenter':0,'vmax':dmax},'coordinates':{'system':'longitude/latitude EPSG:4326','y_over_x_display_aspect':aspect,'all_road_vertices_retained':True},'maximum_absolute_difference_pce':dmax,'flow_unit':'PCE / bounded T4 instance'}
save(fig,'admm_physical_flow_comparison','ADMM and LP physical-link flow','Finite methods',caption,['ADMM physical projection','Independent LP physical projection','Signed physical-link difference','All-link identity comparison'],['admm_physical_flow.csv','physical_geometry.csv'],data)

fig=new_figure('berkeley','LP, CG and LR share this physical projection','T4 / accepted saved result',figsize=(10.3,4.1))
a=fig.add_axes(panel_box(fig,.085,.70));b=fig.add_axes(panel_box(fig,.585,.70))
absolute_map(a,lp,'a  Common saved physical flow',fig)
scatter_axes(b,lp,lr,'b  CG and recovered LR versus LP','n = 2,150 links\nmax |CG − LP| = 0 PCE\nmax |LR − LP| = 0 PCE\nAt stored numerical precision','CG and LR (PCE / instance)')
fig.text(.085,.015,'All physical links are included; 137 dotted links have no movement arc in T4.  © OpenStreetMap contributors, ODbL 1.0.',fontsize=7.3,color=INK)
caption=('The independent LP, complete-pricing CG and LR’s own feasible recovery give identical saved aggregate physical-link projections in this Berkeley T4 instance. '
         'The map uses the full2,150-link road inventory and the same absolute PowerNorm(0.5) scale as the ADMM–LP comparison. The scatter plots all2,150IDs; both CG and LR coincide with the identity line at stored precision. '
         'Each original sparse flow table stores340links; other physical IDs are zero-filled, including137without movement support in this bounded graph. This equality of physical projections does not imply identical paths, identical optimization trajectories, or equality in other instances. '
         'T4 contains four assumed first-bin OD pulses, not the full hourly demand. Units are PCE per bounded instance. No optimizer was rerun. © OpenStreetMap contributors, ODbL1.0.')
caption=caption.replace('full2,150','full 2,150').replace('all2,150IDs','all 2,150 IDs').replace('stores340links','stores 340 links').replace('including137without','including 137 without').replace('ODbL1.0','ODbL 1.0')
save(fig,'lp_cg_lr_physical_flow','LP, CG and LR share this physical projection','Finite methods',caption,['Common full-road physical projection','All-link equality comparison'],['admm_physical_flow.csv','physical_geometry.csv'],{'link_id':ids,'LP_flow_pce':lp.tolist(),'CG_flow_pce':cg.tolist(),'LR_flow_pce':lr.tolist(),'has_movement':movement.tolist(),'max_CG_minus_LP_pce':0.0,'max_LR_minus_LP_pce':0.0,'flow_unit':'PCE / bounded T4 instance'})
