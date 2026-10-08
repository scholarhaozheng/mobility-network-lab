"""Plot a selected LR recovery against fixed LP/CG physical projections."""
from pathlib import Path
import csv,math
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm
from matplotlib.ticker import MaxNLocator,FormatStrFormatter
from shapely import wkt
import render_lr_diagnostics as rd

def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def render(data,flow_csv,geometry_csv,output_dir):
    data=rd.normalize_input(data)
    geometry=rows(geometry_csv);flows=rows(flow_csv);byid={r['link_id']:r for r in flows};ids=[r['link_id'] for r in geometry]
    assert len(geometry)==len(ids)==len(set(ids))==len(flows)==len(byid)==2150 and set(ids)==set(byid)
    values={k:np.array([float(byid[i][k+'_flow_pce']) for i in ids]) for k in ['LP','CG','LR']}
    assert all(np.isfinite(v).all() and v.min()>=-1e-8 for v in values.values())
    movement=np.array([int(byid[i]['has_movement'])==1 for i in ids]);assert movement.sum()==2013
    segments=[np.asarray(wkt.loads(r['geometry_wkt']).coords) for r in geometry]
    coords=np.vstack(segments);lo=coords.min(axis=0);hi=coords.max(axis=0);span=hi-lo;aspect=1/math.cos(math.radians(float(coords[:,1].mean())))
    admm_max=max(float(r['ADMM_flow_pce']) for r in flows) if 'ADMM_flow_pce' in flows[0] else 0
    vmax=max(admm_max,*[float(v.max()) for v in values.values()]);norm=PowerNorm(.5,vmin=0,vmax=vmax)
    diff={k:float(np.max(np.abs(values[k]-values['LP']))) for k in ['CG','LR']}
    selected=data['run'].get('selected_recovery_iteration','selected')
    n=int(data['run']['iterations']);first=int(data['run']['first_certified_iteration'])
    heading='LP, CG and recovered LR physical flow'
    fig=rd.new_figure('berkeley',heading,f'T4 / {n}-iteration extended diagnostic / own LR recovery',figsize=(10.4,4.8))
    width=.35;height=width*fig.get_figwidth()/fig.get_figheight()*span[1]/span[0]*aspect
    ax=fig.add_axes([.085,.79-height,width,height]);rd.format_axes(ax,map_axis=True);ax.set_aspect(aspect)
    ax.set(xlim=(lo[0]-.035*span[0],hi[0]+.035*span[0]),ylim=(lo[1]-.035*span[1],hi[1]+.035*span[1]),xlabel='Longitude (°E)',ylabel='Latitude (°N)')
    ax.set_title('a  LR own recovered physical flow',loc='left',fontsize=10,weight='bold',pad=10)
    for axis in [ax.xaxis,ax.yaxis]:axis.set_major_locator(MaxNLocator(4));axis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax.add_collection(LineCollection(segments,colors='#d8dfe2',linewidths=.38,zorder=1))
    ax.add_collection(LineCollection([s for s,m in zip(segments,movement) if not m],colors='#a9b3ba',linewidths=.48,linestyles='dotted',zorder=2))
    pos=np.flatnonzero(values['LR']>0)
    col=LineCollection([segments[i] for i in pos],array=values['LR'][pos],cmap=rd.FLOW_CMAP,norm=norm,linewidths=.45+1.15*norm(values['LR'][pos]),zorder=3);ax.add_collection(col)
    box=ax.get_position();cax=fig.add_axes([box.x0,box.y0-.12,box.width,.018]);cb=fig.colorbar(col,cax=cax,orientation='horizontal');cb.set_label('PCE / bounded T4 instance',fontsize=8);cb.ax.tick_params(labelsize=7);cb.set_ticks(np.linspace(0,vmax,5));cb.ax.xaxis.set_major_formatter(FormatStrFormatter('%.2g'))
    cb.solids.set_rasterized(False)
    ax=fig.add_axes([.59,.25,.35,.54]);rd.format_axes(ax);ax.set_title('b  All 2,150 physical links',loc='left',fontsize=10,weight='bold',pad=10)
    maximum=max(v.max() for v in values.values());ax.plot([0,maximum],[0,maximum],color=rd.INK,ls='--',lw=1,label='Identity')
    ax.scatter(values['LP'],values['CG'],s=28,facecolors='none',edgecolors=rd.BLUE,linewidths=.65,label='CG',zorder=2)
    ax.scatter(values['LP'],values['LR'],s=11,color=rd.TEAL,alpha=.7,label='LR own recovery',zorder=3)
    ax.set(xlim=(-.035*maximum,1.055*maximum),ylim=(-.035*maximum,1.055*maximum),xlabel='Independent LP (PCE / instance)',ylabel='CG or recovered LR (PCE / instance)')
    ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.text(.035,.96,f'max |CG − LP| = {diff["CG"]:.3g} PCE\nmax |LR − LP| = {diff["LR"]:.3g} PCE',transform=ax.transAxes,va='top',fontsize=8)
    ax.legend(loc='lower right',fontsize=7.5)
    fig.text(.085,.035,'Full road inventory; 137 dotted links have no movement arc in T4.  © OpenStreetMap contributors, ODbL 1.0.',fontsize=7.3,color=rd.INK)
    comparison=('The stored aggregate physical projections coincide exactly in this instance.' if diff['LR']==0 and diff['CG']==0 else 'The separately stored vectors are compared without assuming that accepted objective values imply identical link flows.')
    caption=(f'The {n}-iteration same-rule cold-start LR diagnostic retains the original T4 model and the official 1% gate, first met at iteration {first}. '
      f'The map uses LR’s own selected feasible recovery (saved recovery iteration {selected}), joined by physical-link ID to all 2,150 road geometries. '
      'The scatter includes every road ID and compares the unchanged independent LP and CG projections with the selected LR projection. '
      f'Maximum absolute differences from LP are {diff["CG"]:.17g} PCE for CG and {diff["LR"]:.17g} PCE for LR. {comparison} '
      'Colors and widths use PowerNorm(0.5), retaining the absolute scale used by the existing ADMM–LP map unless new values require a larger maximum. '
      'The 137 physical links with no admitted T4 movement arc remain distinct as dotted background links. Flows are PCE over the bounded departure instance, not PCE/hour. '
      'The original accepted 10-iteration evidence is retained separately. No LP flow was substituted for the LR recovery. © OpenStreetMap contributors, ODbL 1.0.')
    if data['run'].get('validation_status')=='PASS':
        caption += ' Independent diagnostic audit passed.'
        if data['run'].get('formal_evaluation_status')!='PASS':
            caption += ' The original formal-entry replay is pending at this export; the extended diagnostic is not labelled formally accepted.'
    plot={'run':data['run'],'original_accepted':data['original_accepted'],'link_id':ids,**{k+'_flow_pce':v.tolist() for k,v in values.items()},'has_movement':movement.tolist(),'max_CG_minus_LP_pce':diff['CG'],'max_LR_minus_LP_pce':diff['LR'],'map_norm':{'type':'PowerNorm','gamma':.5,'vmin':0,'vmax':vmax},'flow_unit':'PCE / bounded T4 instance'}
    return rd.emit(fig,'lp_cg_lr_physical_flow',heading,caption,{'a':'Selected LR own recovery on all physical road geometries','b':'All-link CG and LR comparison with fixed independent LP'},data,output_dir,plot_data=plot,function=render)
