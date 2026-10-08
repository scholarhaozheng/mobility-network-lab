"""Berkeley finite-time figures from frozen saved tables only.

This module only reads explicit plot inputs. It does not import solver code,
checkpoints, scientific entry points or legacy renderers with side effects.
"""
from pathlib import Path
import argparse, inspect, json
import numpy as np
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
from matplotlib.collections import LineCollection
import plot_common as pc

HERE=Path(__file__).resolve().parent


def values(rows,key,missing=False):
    return np.asarray([np.nan if missing and r.get(key) in ('',None) else float(r[key]) for r in rows])


def panel(ax,title):
    pc.format_axes(ax)
    ax.set_axisbelow(True)
    ax.set_title(title,loc='left',fontsize=10,weight='bold',pad=9)


def emit(fig,stem,title,stage,caption,panels,sources,data,function,validation,formulas):
    # Content and geometry checks happen before saving; no numerical state is changed.
    rec=pc.save(fig,stem,title,stage,caption,panels,sources,plot_data=data)
    rec['plotter']={'path':'render_finite.py','function':function.__name__,
                    'line':inspect.getsourcelines(function)[1],'sha256':pc.sha(__file__)}
    rec['renderer']={'file':'tools/visuals/berkeley_alignment_r2/render_finite.py','function':function.__name__,
                     'line':inspect.getsourcelines(function)[1]}
    rec['numeric_validation']=validation
    rec['metric_formulas']=formulas
    rec['scope']='Accepted bounded Berkeley T4 saved-result presentation; modeled PCE, not observed traffic.'
    (pc.OUT/(stem+'.source.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
    return rec


def t01_computed_column():
    name='t01_computed_column.plot_data.json';data=pc.read_json(name);selected=data['selected']
    path_name='t01_selected_path.csv';geometry_name='physical_geometry.csv'
    movements=pc.read_csv(path_name);roads=pc.read_csv(geometry_name)
    def coordinates(wkt):
        assert wkt.startswith('LINESTRING (') and wkt.endswith(')')
        return np.asarray([[float(v) for v in pair.strip().split()] for pair in wkt[12:-1].split(',')])
    geometry={int(row['link_id']):coordinates(row['geometry_wkt']) for row in roads}
    route=[geometry[int(row['link_id'])] for row in movements]
    assert len(route)==89 and len(set(row['link_id'] for row in movements))==89
    assert all(np.allclose(route[i][-1],route[i+1][0],rtol=0,atol=1e-7) for i in range(88))
    assert [int(row['from_time_step']) for row in movements]==list(range(5,94))
    assert [int(row['to_time_step']) for row in movements]==list(range(6,95))
    times=np.asarray(data['physical_time_step'],float)
    distance=np.asarray(data['physical_distance_m'],float)
    assert len(times)==len(distance)==91 and np.all(np.diff(times)>=0) and np.all(np.diff(distance)>=0)
    assert selected['movement_arcs']==89 and selected['flow_pce']==7.5
    assert times[-1]==selected['physical_arrival_time_index']==94 and data['terminal_bookkeeping_time_step']==165
    elapsed=(times-selected['departure_time_index'])*.5
    assert elapsed[-1]==selected['physical_elapsed_minutes']==44.5
    fixed=selected['fixed_objective_cost_minutes']
    assert np.isclose(sum(float(row['cost_min']) for row in movements),fixed,rtol=0,atol=1e-12)
    sink_elapsed=(selected['bookkeeping_sink_time_index']-selected['departure_time_index'])*.5
    fig=pc.new_figure('berkeley','Computed column: route, cost and model time','T4 / T02 column 1 / 7.5 PCE',figsize=(11.3,6.8))
    a=fig.add_axes([.075,.14,.43,.655]);pc.format_axes(a,map_axis=True)
    a.set_title('a  Actual 89-movement road path',loc='left',fontsize=10,weight='bold',pad=9)
    a.add_collection(LineCollection(list(geometry.values()),colors=pc.ROAD,linewidths=.65,zorder=1))
    a.add_collection(LineCollection(route,colors=pc.TEAL,linewidths=2,zorder=2))
    vertices=np.vstack(route);lo=vertices.min(axis=0);hi=vertices.max(axis=0)
    a.set_xlim(lo[0]-.004,hi[0]+.004);a.set_ylim(lo[1]-.005,hi[1]+.005)
    a.set_aspect(1/np.cos(np.deg2rad(vertices[:,1].mean())))
    origin=route[0][0];destination=route[-1][-1]
    a.scatter(*origin,s=47,facecolor='white',edgecolor=pc.INK,lw=1.3,zorder=4)
    a.scatter(*destination,s=42,marker='s',facecolor=pc.TEAL,edgecolor='white',lw=.8,zorder=4)
    a.annotate('Origin',origin,xytext=(7,-15),textcoords='offset points',fontsize=9,weight='bold')
    a.annotate('Destination',destination,xytext=(7,8),textcoords='offset points',fontsize=9,weight='bold')
    a.set(xlabel='Longitude (°)',ylabel='Latitude (°)')
    a.xaxis.set_major_locator(MaxNLocator(4));a.yaxis.set_major_locator(MaxNLocator(4))
    a.xaxis.set_major_formatter(StrMethodFormatter('{x:.3f}'));a.yaxis.set_major_formatter(StrMethodFormatter('{x:.3f}'))
    a.text(.035,.035,'2.6023 km  ·  7.5 PCE',transform=a.transAxes,fontsize=9,weight='bold',bbox={'facecolor':'white','edgecolor':'none','pad':3})
    a=fig.add_axes([.635,.525,.31,.27]);panel(a,'b  Saved physical-distance progression')
    a.plot(elapsed,distance/1000,color=pc.TEAL,lw=1.6)
    a.scatter(elapsed,distance/1000,s=8,color=pc.TEAL,zorder=3)
    a.scatter([elapsed[-1]],[distance[-1]/1000],s=32,color=pc.TEAL,zorder=4)
    a.set(xlim=(-1,48.0),ylim=(-.06,2.88),xlabel='Elapsed rounded state-clock time (min)',ylabel='Cumulative physical distance (km)')
    a.text(.035,.955,'91 saved vertices',transform=a.transAxes,va='top',fontsize=8.5)
    a.annotate('Physical arrival\n08:47:00',xy=(elapsed[-1],distance[-1]/1000),xytext=(23,2.57),fontsize=8.5,
               arrowprops={'arrowstyle':'-','lw':.65,'color':pc.INK},ha='left',va='top')
    a.xaxis.set_major_locator(MaxNLocator(5));a.yaxis.set_major_locator(MaxNLocator(5))
    a=fig.add_axes([.705,.14,.24,.23]);panel(a,'c  Three distinct time quantities')
    quantities=[fixed,selected['physical_elapsed_minutes'],sink_elapsed]
    labels=['Fixed road cost','Physical clock','Sink accounting']
    a.barh(np.arange(3),quantities,height=.48,color=[pc.TEAL,pc.BLUE,'#a7b7be'])
    a.set_yticks(np.arange(3),labels);a.invert_yaxis();a.set_xlim(0,101)
    a.set_xlabel('Minutes, with different model meanings')
    a.grid(False,axis='y');a.grid(axis='x',color=pc.GRID,lw=.5)
    for y,v in enumerate(quantities):a.text(v+2.2,y,f'{v:.5f}' if y==0 else f'{v:.1f}',va='center',fontsize=9)
    a.xaxis.set_major_locator(MaxNLocator(4))
    caption=("Saved positive T02 column 1 carries 7.5 PCE. Panel a joins all 89 saved, ordered movement link IDs to the real physical-road geometry; consecutive endpoints and time steps are verified. The map shows the route with nearby model roads as context, using longitude/latitude and a latitude-adjusted aspect ratio. Panel b retains all 91 supplied distance/time vertices for these movements; positions use the rounded 30-second state clock, not an observed trajectory. The path accumulates 2.6023 km, departs at 08:02:30 and physically arrives at 08:47:00 (44.5 elapsed minutes). Panel c separates the unchanged 3.90345 fixed objective minutes from that rounded elapsed time and the H165 sink at 09:22:30 (80 minutes after departure). The terminal sink is accounting, not extra physical travel. This is a computed route, not a schematic full time-layer network.")
    output={**data,'selected_movement_chain':movements}
    return emit(fig,'t01_computed_column','Computed column: route, cost and model time','T4 construction',caption,
      {'a':'Actual ordered movement path joined to physical road geometry','b':'Saved distance against elapsed rounded model clock','c':'Fixed cost, physical elapsed clock and terminal bookkeeping time'},[name,path_name,geometry_name],output,t01_computed_column,
      {'saved_vertices':len(times),'road_movements':89,'all_vertices_retained':True,'positive_columns_retained_in_plot_data':len(data['positive_columns']),
       'matched_movement_geometries':len(route),'consecutive_physical_endpoints_match':True,'consecutive_state_clocks_match':True,'road_cost_sum_matches_saved_column':True,
       'fixed_objective_minutes':fixed,'physical_elapsed_minutes':44.5,'bookkeeping_elapsed_minutes':sink_elapsed,'terminal_is_travel':False},
      {'elapsed_minutes':'(physical_time_step - departure_time_index) * 0.5','distance_km':'physical_distance_m / 1000','sink_elapsed_minutes':'(165 - 5) * 0.5','route':'Selected saved movement link IDs joined to physical_geometry.geometry_wkt in route_index order','map_aspect':'1 / cos(mean route latitude); geographic coordinates are unaltered','data_transform':'Unit conversion and ID-based geometry join only; no invented route geometry or interpolation checkpoints.'})


def t02_cg_phases():
    name='t02_cg_phases.plot_data.json';data=pc.read_json(name);pi=data['phase_i'];pii=data['phase_ii']
    gates_name='t02_frozen_pricing_gates.json';gates=pc.read_json(gates_name)
    reference='accuracy_objective_vs_lp.plot_data.json';lp=pc.read_json(reference)['same_T4_LP_objective_pce_minutes']
    assert len(pi)==5 and len(pii)==3
    assert [r['round'] for r in pi]==list(range(5)) and [r['round'] for r in pii]==list(range(3))
    assert pi[-1]['artificial_flow']==0 and pii[-1]['pool_columns']==10
    fig=pc.new_figure('berkeley','Column generation: feasibility and pricing','T4 / five Phase I and three Phase II records',figsize=(10.8,8.0))
    a=fig.add_axes([.09,.565,.35,.24]);panel(a,'a  Phase I: artificial-flow clearance')
    x=values(pi,'round');y=values(pi,'artificial_flow')
    a.step(x,y,where='post',color=pc.TEAL,lw=1.6);a.scatter(x,y,s=23,color=pc.TEAL,zorder=3)
    a.axhline(0,color=pc.INK,lw=.65);a.set(xlim=(-.18,4.25),ylim=(-.08,1.45),xlabel='Saved Phase I round',ylabel='Artificial flow (PCE)')
    a.set_xticks(range(5));a.text(.98,.96,'Zero at round 4',transform=a.transAxes,ha='right',va='top',fontsize=8.5)
    a=fig.add_axes([.585,.565,.365,.24]);panel(a,'b  Phase II: real-cost objective')
    x=values(pii,'round');y=values(pii,'master_objective')
    a.axhline(lp,color=pc.BLUE,lw=1,ls='--',label='Same-T4 arc-flow LP')
    a.step(x,y,where='post',color=pc.TEAL,lw=1.6,label='Restricted master');a.scatter(x,y,s=25,color=pc.TEAL,zorder=3)
    a.set(xlim=(-.12,2.15),ylim=(43.15,47.25),xlabel='Saved Phase II round',ylabel='Objective (PCE·min)');a.set_xticks(range(3));a.legend(loc='upper right',fontsize=8)
    a.text(.98,.21,f'LP {lp:.8f}',transform=a.transAxes,ha='right',va='center',fontsize=8,color=pc.BLUE)
    # Different phase objectives imply different reduced-cost units, so use two axes.
    a=fig.add_axes([.09,.145,.145,.245]);panel(a,'c  Full-graph pricing')
    x=values(pi,'round');y=values(pi,'min_full_graph_reduced_cost');a.axhline(0,color=pc.INK,lw=.65)
    a.plot(x,y,'o-',color=pc.TEAL,lw=1.3,ms=3.5)
    a.set(xlim=(-.18,4.2),ylim=(-1.12,.14),xlabel='Phase I round',ylabel='Minimum reduced cost (unitless)');a.set_xticks([0,2,4])
    a=fig.add_axes([.325,.145,.115,.245]);pc.format_axes(a);a.set_axisbelow(True)
    x=values(pii,'round');y=values(pii,'min_full_graph_reduced_cost');a.axhline(0,color=pc.INK,lw=.65)
    a.plot(x,y,'o-',color=pc.BLUE,lw=1.3,ms=3.5)
    a.set(xlim=(-.12,2.2),ylim=(-2.95,.34),xlabel='Phase II round',ylabel='Minimum reduced cost (min)');a.set_xticks([0,1,2]);a.yaxis.set_major_locator(MaxNLocator(4))
    a.text(.98,.04,'Final\n−4.44 × 10⁻¹⁶\nGate −10⁻⁷',transform=a.transAxes,ha='right',va='bottom',fontsize=7.5)
    a=fig.add_axes([.585,.145,.365,.245]);panel(a,'d  Saved column-pool growth')
    rows=pi+pii;x=np.arange(len(rows));y=values(rows,'pool_columns')
    a.step(x,y,where='post',color=pc.TEAL,lw=1.4);a.scatter(x[:5],y[:5],color=pc.TEAL,s=22,label='Phase I',zorder=3);a.scatter(x[5:],y[5:],color=pc.BLUE,s=22,label='Phase II',zorder=3)
    a.axvline(4.5,color=pc.INK,lw=.7,ls=':');a.set(xlim=(-.25,7.4),ylim=(3.5,11),xlabel='Recorded phase and round',ylabel='Available columns')
    a.set_xticks(x,['I·'+str(r['round']) for r in pi]+['II·'+str(r['round']) for r in pii],fontsize=7)
    a.yaxis.set_major_locator(MaxNLocator(integer=True));a.legend(loc='upper left',fontsize=8,ncol=2)
    caption=("All five Phase I and three Phase II saved records are shown. Phase I minimizes artificial flow in PCE and clears it at round 4. Phase II minimizes real PCE·min cost, reaching the independent same-T4 LP value 43.66742440800644 at saved round 1; its complete-graph pricing record then closes at round 2 with minimum reduced cost −4.4408920985e−16 minutes and ten columns. Panel c gives Phase I's dimensionless reduced costs and Phase II's minute-valued reduced costs separate axes. The actual frozen tolerances are 1e−8 PCE artificial flow and 1e−8 dimensionless negative reduced cost in Phase I, and 1e−7 minutes negative reduced cost in Phase II; a column is added only when reduced cost is below the negative tolerance. Zero is the plotted reference line; the Phase II tolerance is annotated separately because the two are indistinguishable at this scale. Panel d retains the repeated eight-column checkpoint at the phase transition. Lines connect saved records; no unsaved rounds, smoothed values or extra solver iterations are inserted.")
    output={**data,'frozen_pricing_gates':gates}
    return emit(fig,'t02_cg_phases','Column generation: feasibility and pricing','T4 column generation',caption,
      {'a':'Phase I artificial flow','b':'Phase II real-cost objective and same-T4 LP','c':'Full-graph reduced costs on separate phase-unit axes','d':'Column-pool size at every saved checkpoint'},[name,reference,gates_name],output,t02_cg_phases,
      {'phase_i_rows':len(pi),'phase_ii_rows':len(pii),'all_rows_retained':True,'total_plot_checkpoints':8,
       'phase_i_terminal_artificial_flow':pi[-1]['artificial_flow'],'phase_ii_terminal_reduced_cost':pii[-1]['min_full_graph_reduced_cost'],
       'phase_ii_terminal_objective':pii[-1]['master_objective'],'lp_reference':lp,'terminal_columns':10,'frozen_phase_i_gates':gates['phase_i'],'frozen_phase_ii_gates':gates['phase_ii'],'phase_ii_terminal_pricing_pass':pii[-1]['min_full_graph_reduced_cost']>=-gates['phase_ii']['negative_reduced_cost_abs']},
      {'phase_i_objective':'sum artificial PCE','phase_ii_objective':'saved master_objective in PCE·min','phase_i_pricing_units':'PCE/PCE = dimensionless','phase_ii_pricing_units':'(PCE·min)/PCE = min','pool_growth':'saved pool_columns; no interpolation or synthetic checkpoints'})


def t03_lr_bounds_physical():
    name='t03_lr_bounds_physical.plot_data.json';data=pc.read_json(name);history=data['LR_history']
    recovery_name='t03_recovery_history.json';recovery=pc.read_json(recovery_name)
    reference='accuracy_objective_vs_lp.plot_data.json';lp=pc.read_json(reference)['same_T4_LP_objective_pce_minutes']
    x=values(history,'iteration');low=values(history,'best_dual');high=values(history,'best_primal',True);gap=values(history,'gap',True)*100
    assert len(history)==10 and np.isnan(high[:9]).all() and np.isnan(gap[:9]).all()
    assert len(recovery)==2 and recovery[0]['feasible'] is False and recovery[0]['objective'] is None and recovery[1]['feasible'] is True
    assert recovery[0]['iteration']==1 and recovery[1]['iteration']==10
    assert high[-1]==recovery[-1]['objective'] and gap[-1]<1.0
    fig=pc.new_figure('berkeley','Lagrangian bounds and primal recovery','T4 / ten saved iterations / two recovery calls',figsize=(10.6,7.5))
    a=fig.add_axes([.10,.565,.35,.24]);panel(a,'a  Best bounds and same-T4 LP')
    a.axhline(lp,color=pc.BLUE,lw=1,ls='--',label='Same-T4 arc-flow LP')
    a.step(x,low,where='post',color=pc.TEAL,lw=1.5,label='Best dual lower bound');a.scatter(x,low,s=13,color=pc.TEAL,zorder=3)
    a.plot(x,high,'o',color=pc.INK,ms=5,label='Feasible recovered upper',zorder=4)
    a.set(xlim=(.6,10.45),ylim=(43.555,43.745),xlabel='Lagrangian iteration',ylabel='Objective / bound (PCE·min)')
    a.yaxis.set_major_formatter(StrMethodFormatter('{x:.2f}'));a.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=5));a.legend(loc='upper left',fontsize=7.5)
    a=fig.add_axes([.595,.565,.35,.24]);panel(a,'b  Available primal–dual certificate')
    a.axhline(1,color=pc.BLUE,lw=1.1,ls='--',label='Frozen 1% gate');a.plot(x,gap,'o',color=pc.TEAL,ms=5)
    a.set(xlim=(.6,10.5),ylim=(0,1.15),xlabel='Lagrangian iteration',ylabel='Certified gap (%)');a.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=5))
    a.text(.04,.47,'No feasible upper bound\nat iterations 1–9',transform=a.transAxes,fontsize=8.5,color=pc.INK)
    a.annotate(f'{gap[-1]:.6f}%',xy=(10,gap[-1]),xytext=(6.5,.43),fontsize=9,color=pc.TEAL,arrowprops={'arrowstyle':'-','lw':.65,'color':pc.TEAL})
    a.legend(loc='upper left',fontsize=8)
    a=fig.add_axes([.10,.145,.35,.245]);panel(a,'c  Saved path-pool growth')
    pool=values(history,'path_pool_size');a.step(x,pool,where='post',color=pc.TEAL,lw=1.5);a.scatter(x,pool,s=22,color=pc.TEAL,zorder=3)
    a.set(xlim=(.6,10.45),ylim=(3.5,6.8),xlabel='Lagrangian iteration',ylabel='Paths in the saved pool');a.set_yticks([4,5,6]);a.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=5))
    a.text(.96,.91,'4 → 6 paths',transform=a.transAxes,ha='right',va='top',fontsize=9)
    a=fig.add_axes([.595,.145,.35,.245]);panel(a,'d  Separate recovery LP calls')
    for r in recovery:
        a.scatter([r['iteration']],[r['path_count']],s=62,facecolors=pc.TEAL if r['feasible'] else 'white',edgecolors=pc.TEAL if r['feasible'] else pc.BLUE,lw=1.3,zorder=3,label='Feasible recovery' if r['feasible'] else 'Infeasible recovery')
    a.set(xlim=(.3,10.7),ylim=(3.35,7.15),xlabel='Lagrangian iteration at saved LP call',ylabel='Paths available to recovery LP');a.set_xticks([1,10]);a.set_yticks([4,5,6,7])
    a.legend(loc='upper left',fontsize=7.8)
    a.annotate('Null objective',xy=(1,4),xytext=(2.2,3.68),fontsize=8,color=pc.BLUE,arrowprops={'arrowstyle':'-','lw':.65,'color':pc.BLUE})
    a.annotate('43.66742441\nPCE·min',xy=(10,6),xytext=(7.15,4.6),fontsize=8,color=pc.TEAL,arrowprops={'arrowstyle':'-','lw':.65,'color':pc.TEAL},ha='center')
    caption=("All ten saved Berkeley T4 Lagrangian iterations are retained. The best valid dual bound is 43.58459836422644 PCE·min; individual relaxed dual iterates are different and are not feasible primal costs. The own-pool recovery is infeasible at iteration 1 with four paths and feasible at iteration 10 with six paths, yielding 43.667424408006426 PCE·min. Its certified relative gap is 0.0018967467145784354 (0.18967467145784354%), within the frozen 1% gate. Before iteration 10, best-primal and gap values are absent and remain unplotted. The same-graph LP value 43.66742440800644 is a separate numerical reference, not a substituted LR flow. Panel d shows exactly the two saved recovery calls, with the infeasible call's null objective kept missing. The original 340-row positive physical-flow comparison is retained unchanged in the accompanying plot-data record; this diagnostic figure does not imply that those rows cover the entire 2,150-link physical graph.")
    output={**data,'recovery_history':recovery}
    return emit(fig,'t03_lr_bounds_physical','Lagrangian bounds and primal recovery','T4 Lagrangian',caption,
      {'a':'Best valid dual and available feasible upper versus same-T4 LP','b':'Available certified gap against frozen1%gate','c':'Saved path-pool growth','d':'Two actual separate recovery LP attempts'},[name,recovery_name,reference],output,t03_lr_bounds_physical,
      {'LR_history_rows':len(history),'missing_primal_rows':int(np.isnan(high).sum()),'missing_gap_rows':int(np.isnan(gap).sum()),'recovery_calls':len(recovery),'infeasible_objective_remains_null':recovery[0]['objective'] is None,'final_best_dual':low[-1],'final_best_primal':high[-1],'final_gap_percent':gap[-1],'gate_percent':1.0,'all_physical_comparison_rows_retained':len(data['physical_links'])},
      {'bounds':'history.best_dual and only nonempty history.best_primal','gap_percent':'100 * history.gap (available only at iteration10)','pool_growth':'history.path_pool_size','recovery':'saved recovery_history checkpoints only; null objective never zero-imputed'})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',choices=['t01','t02','t03'],nargs='+');args=parser.parse_args()
    funcs={'t01':t01_computed_column,'t02':t02_cg_phases,'t03':t03_lr_bounds_physical}
    records=[fn() for key,fn in funcs.items() if not args.only or key in args.only]
    (HERE/'FINITE_RENDER_RECEIPT.json').write_text(json.dumps({'status':'RENDERED_PENDING_VISUAL_QA','solver_calls':0,'candidate_written':False,'figures':[{'stem':r['id'],'validation':r['numeric_validation']} for r in records]},ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':main()
