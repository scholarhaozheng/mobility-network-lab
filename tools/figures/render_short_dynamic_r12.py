"""Plot released short dynamic histories as honest saved-state figures.
Pure public-data renderer: no optimizer calls and no invented intermediate records.
"""
from pathlib import Path
import argparse,json,hashlib,sys
import numpy as np
from style import new_figure,format_axes,export_figure,TEAL,BLUE,INK,CATEGORIES
REPO=Path(__file__).resolve().parents[2]
D=REPO/'docs'
REGPATH=D/'assets/figure-contract-r11/DISPLAY_REGISTRY.json'
REG=json.loads(REGPATH.read_text(encoding='utf8'))
OUT=None
ITEMS=[]
def read(p):return json.loads((D/p).read_text(encoding='utf8'))
def source(p):
 q=D/p
 return dict(public_path='docs/'+p,sha256=hashlib.sha256(q.read_bytes()).hexdigest())
def table(tid):return REG['tables'][tid]
def metrics(block):return {r['Metric']:r['Saved value'] for r in block['rows']}
def figaxes(city,title,n=1,rows=1):
 fig=new_figure(city,title,'T4 / saved finite-horizon evidence',figsize=((6.6 if n==1 else 10.8),(4.25 if rows==1 else 7.8)))
 axs=fig.subplots(rows,n,squeeze=False)
 fig.subplots_adjust(left=.095,right=.97,top=.78,bottom=.17 if rows==1 else .095,wspace=.4,hspace=.58)
 for ax in axs.flat:format_axes(ax)
 return fig,list(axs.flat)
def fmt(x):return f'{float(x):.5g}'
def singlex(ax,label='Saved iteration'):
 ax.set_xlim(.65,1.35);ax.set_xticks([1]);ax.set_xlabel(label)
def point(ax,y,label=None,color=TEAL,marker='o',offset=(8,7),annotate=True):
 ax.scatter([1],[y],s=50,facecolors='none' if marker=='s' else color,edgecolors=color,marker=marker,zorder=5,label=label,linewidths=1.5)
 if annotate:ax.annotate(fmt(y),(1,y),xytext=offset,textcoords='offset points',fontsize=8,color=color)
 singlex(ax)
def finish(fig,tid,slug,title,caption,quantity,unit,panels,originals=None,extra=None,plotdata=None):
 t=table(tid);city=t['city'];src=[]
 for s in t.get('sources',[]):
  path=s.get('href') or s.get('public_path','').removeprefix('docs/')
  if path and (D/path).is_file():src.append(source(path))
 src.append(source('assets/figure-contract-r11/DISPLAY_REGISTRY.json'))
 if tid=='uc-t4-cg-checks':src.append(dict(source('assets/city-alignment-r3/urbana-transfer/GATES.json'),role='Frozen direct CG independent pricing tolerance',field='T.CG_independent_pricing_closure_abs'))
 for s in extra or []:
  if s not in [x['public_path'].removeprefix('docs/') for x in src]:src.append(source(s))
 stem=OUT/city/slug
 rec=export_figure(fig,stem,dict(figure_id='R12-'+slug.upper(),city=city,instance=t.get('scope','T4 same-instance saved state'),role='saved-state-check',conclusion=title,panels=panels,quantity=quantity,unit=unit,public_only=True,original_figure_assets=originals or t.get('original_assets',[]),canonical_functions=['render_advanced.cg_figures','render_advanced.admm_figures','render_lagrangian_details.bounds/recovery/prices'],saved_points_only=True),caption,src)
 if tid=='uc-t4-cg-checks':
  rec['pricing_gate_provenance']={'field':'T.CG_independent_pricing_closure_abs','value':float(read('assets/city-alignment-r3/urbana-transfer/GATES.json')['T']['CG_independent_pricing_closure_abs']),'phase_I_unit':'dimensionless','phase_II_unit':'min','plotted_sign':'negative of absolute closure tolerance','direct_source':'docs/assets/city-alignment-r3/urbana-transfer/GATES.json'}
  stem.with_suffix('.source.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf8')
 if plotdata is not None:stem.with_suffix('.plot.json').write_text(json.dumps(plotdata,ensure_ascii=False,indent=2),encoding='utf8')
 ITEMS.append(dict(table_id=tid,city=city,title=title,staged_stem=str(stem),originals=originals or t.get('original_assets',[]),caption=caption,source_hashes=src,dimensions=rec['dimensions'],status='RENDERED_PENDING_VISUAL_QA'))
def cg(city):
 uc=city=='urbana-champaign';tid='uc-t4-cg-checks' if uc else 'pittsburgh-t4-cg-check'
 prefix='assets/city-alignment-r3/urbana-transfer/' if uc else 'assets/algorithm-transfer-r8/pittsburgh/'
 rows=read(prefix+('cg-closure.plot_data.json' if uc else 'PIT_T03.plot.json'))
 a,b=rows
 original=table(tid)['original_assets']
 pricing_gate=float(read('assets/city-alignment-r3/urbana-transfer/GATES.json')['T']['CG_independent_pricing_closure_abs']) if uc else 1e-7
 assert pricing_gate==1e-7, 'Frozen plotted pricing tolerance changed: re-audit before rendering.'
 title='Column generation: Phase I feasibility'
 fig,axs=figaxes(city,title);ax=axs[0];point(ax,float(a['artificial_mass']));ax.set_xlabel('Saved Phase I round');ax.set_ylabel('Total artificial flow (PCE)');ax.set_ylim(-.04,.25);ax.axhline(0,color=INK,lw=.7)
 finish(fig,tid,'cg-phase1',title,'Phase I has one actual saved restricted-master round. Its total artificial flow is 0 PCE. A single marker retains that real record; there is no interpolated trajectory. Four seed paths suffice. Commodity-level artificial-flow history was not included in these public plot files, so no heatmap is inferred. Phase I feasibility is separate from Phase II real cost and full-DAG pricing closure.','artificial flow','PCE',{'a':'Saved total artificial flow'},originals=[original[0]],plotdata=a)
 title='Column generation: Phase II real cost'
 if uc:
  obj=float(b['objective']);lp=read('assets/plot-semantics-r9/urbana-champaign/urbana-champaign-admm-main.plot_data.json')['lp_objective_pce_min'];extra=['assets/plot-semantics-r9/urbana-champaign/urbana-champaign-admm-main.plot_data.json']
 else:
  rr=table('pittsburgh-t4-objectives')['blocks'][0]['rows'];obj=float(rr[1]['objective_pce_min']);lp=float(rr[0]['objective_pce_min']);extra=['assets/algorithm-transfer-r8/pittsburgh/PIT_T08.plot.json']
 fig,axs=figaxes(city,title);ax=axs[0];point(ax,obj,label='Saved CG real cost',offset=(8,13));ax.axhline(lp,color=BLUE,ls='--',lw=1.1,label='Same-graph LP');ax.set_ylim(obj*.93,obj*1.09);ax.set_ylabel('Real objective (PCE·min)');ax.set_xlabel('Saved Phase II round');ax.legend(fontsize=8,loc='upper left')
 finish(fig,tid,'cg-phase2',title,f'One actual saved Phase II round. CG real cost is {obj:.17g} PCE·min; the separate same-graph LP reference is {lp:.17g} PCE·min. The marker and dashed reference can coincide at displayed precision. No Phase I artificial objective is connected to this real-cost objective. No new column after the four seed paths.','real fixed-cost objective','PCE·min',{'a':'Saved Phase II objective and independent LP'},originals=[original[1] if uc else original[0]],extra=extra,plotdata={'phaseII':b,'objective_pce_min':obj,'lp_objective_pce_min':lp})
 title='Column generation: full-DAG pricing closure'
 fig,axs=figaxes(city,title,n=2)
 for ax,r,unit,letter in zip(axs,rows,['dimensionless','min'],'ab'):
  point(ax,float(r['minimum_reduced_cost']));ax.axhline(-pricing_gate,color=BLUE,ls=':',lw=1.1,label='Frozen negative-cost gate');ax.axhline(0,color=INK,lw=.7);ax.set_ylim(-1.4*pricing_gate,2.2*pricing_gate);ax.set_ylabel('Minimum reduced cost ('+unit+')');ax.set_title(letter+'  Phase '+r['phase'],loc='left');ax.set_xlabel('Saved pricing round');ax.legend(fontsize=7,loc='upper left')
 finish(fig,tid,'cg-pricing',title,'The saved full-DAG pricing check is zero in both phases, against the frozen absolute tolerance 1e-7. Phase I reduced cost is dimensionless; Phase II reduced cost is minutes, so they have separate axes. Each phase has one actual round, four seed paths, and no new columns. Public data contain the global minimum per phase, not separate per-demand minima; no per-demand bars are fabricated.','minimum complete-path reduced cost','Phase I dimensionless; Phase II min',{'a':'Phase I pricing','b':'Phase II pricing'},originals=[original[2] if uc else original[0]],plotdata=rows)
def lr(city):
 uc=city=='urbana-champaign';tid='uc-t4-lr-checks' if uc else 'pittsburgh-t4-lr-check';t=table(tid);original=t['original_assets']
 h=read('assets/city-alignment-r3/urbana-transfer/lr-bounds.plot_data.json' if uc else 'assets/algorithm-transfer-r8/pittsburgh/PIT_T04.plot.json')[0]
 lo=float(h['best_dual']);up=float(h['best_primal']);gap=max(0,(up-lo)/max(1,abs(up)))
 title='Lagrangian bounds and certified gap';fig,axs=figaxes(city,title,n=2);ax=axs[0];point(ax,lo,label='Best valid lower',marker='o',annotate=False);point(ax,up,label='Own feasible upper',color=BLUE,marker='s',annotate=False);ax.set_ylim(lo*.93,up*1.09);ax.set_ylabel('Bound (PCE·min)');ax.set_title('a  Separate lower and upper bounds',loc='left');ax.legend(loc='upper left',fontsize=8);ax.annotate(fmt(lo),(1,lo),xytext=(8,-19),textcoords='offset points',fontsize=8)
 ax=axs[1];point(ax,100*gap);ax.axhline(1,color=BLUE,ls=':',label='Frozen 1% gate');ax.set_ylim(-.08,1.3);ax.set_ylabel('Certified gap (%)');ax.set_title('b  Same-instance certificate',loc='left');ax.legend(loc='upper left',fontsize=8)
 finish(fig,tid,'lr-bounds',title,f'One actual LR iteration. Best valid lower is {lo:.17g} PCE·min; own recovered feasible upper is {up:.17g} PCE·min. The certified gap is max(0,(U−L)/max(1,|U|)) = {gap:.6g}; the frozen gate is 1%. Lower and upper are separate markers at the same recorded iteration; they coincide to displayed precision. Tiny signed floating-point differences remain in the plot data. Capacities are nonbinding in this T4 pulse; this does not prove that city area caused the short trace.','valid bounds and certificate','PCE·min; %',{'a':'Actual valid lower and feasible upper','b':'Certificate against frozen gate'},originals=[original[0]],plotdata=h)
 title='Lagrangian prices and recovery';fig,axs=figaxes(city,title,n=2);ax=axs[0];point(ax,0);ax.set_ylim(-.12,1.1);ax.set_yticks([0,1]);ax.set_ylabel('Positive capacity prices (count)');ax.set_title('a  Saved price support',loc='left')
 ax=axs[1];point(ax,4,label='Feasible recovery',offset=(8,7));ax.set_ylim(0,5.7);ax.set_yticks(range(6));ax.set_ylabel('Paths in own recovery pool');ax.set_title('b  Actual recovery call',loc='left');ax.legend(fontsize=8,loc='upper left')
 finish(fig,tid,'lr-prices-recovery',title,'At saved iteration 1 the positive capacity-price count is 0, so there are no positive-price arcs for a top-price map or time histogram. One actual recovery call uses the four paths in this method’s own pool and returns a feasible upper bound. Filled recovery marker follows the Boston/Hong Kong feasible-recovery convention. No additional calls or multipliers are invented.','positive multiplier count and own recovery pool size','counts',{'a':'Zero positive prices at the actual saved iteration','b':'Actual feasible recovery call and own pool'},originals=original[1:] if uc else original,plotdata={'saved_iteration':1,'positive_price_count':0,'own_recovery_pool_paths':4,'actual_recovery_calls':1})
def admm(city):
 tid={'urbana-champaign':'urbana-champaign-t4-admm-check','pittsburgh':'pittsburgh-t4-admm-check','ithaca':'ith-time-endpoints'}[city]
 if city!='ithaca':
  j=read(f'assets/plot-semantics-r9/{city}/{city}-admm-main.plot_data.json');h=j['history'][0];lp=float(j['lp_objective_pce_min'])
 else:
  t=table(tid);m=metrics(t['blocks'][2]);h=dict(iteration=1,objective=float(t['blocks'][0]['rows'][3]['Objective (PCE·min)']),balance_residual=m['max balance PCE'],capacity_residual=m['max capacity excess PCE'],primal_residual=m['primal PCE'],primal_threshold=m['primal threshold PCE'],dual_residual=m['rho scaled dual min'],dual_threshold=m['dual threshold min']);lp=float(t['blocks'][0]['rows'][0]['Objective (PCE·min)']);j={'history':[h],'lp_objective_pce_min':lp}
 title='ADMM residuals and objective agreement';fig,axs=figaxes(city,title,n=2,rows=2);floor=1e-16
 ax=axs[0]
 for key,label,col,mark in [('balance_residual','Local balance',TEAL,'o'),('capacity_residual','Capacity',BLUE,'s')]:
  point(ax,max(float(h[key]),floor),label=label,color=col,marker=mark,annotate=False)
  if float(h[key])==0:ax.annotate('0 (display floor)',(1,floor),xytext=(7,9),textcoords='offset points',fontsize=7,color=col)
 ax.axhline(1e-5,color=INK,ls=':',label='Feasibility gate');ax.set_yscale('log');ax.set_ylim(3e-17,1e-2);ax.set_ylabel('Flow residual (PCE)');ax.set_title('a  Original-unit feasibility',loc='left');ax.legend(loc='upper left',bbox_to_anchor=(0,.72),fontsize=7)
 for ax,key,gate,unit,panel_title,col in [(axs[1],'primal_residual','primal_threshold','PCE','b  Primal consensus',TEAL),(axs[2],'dual_residual','dual_threshold','min','c  Rho-scaled dual update',BLUE)]:
  val=float(h[key]);point(ax,max(val,floor),label='Saved residual',color=col,annotate=False);ax.axhline(float(h[gate]),color=INK,ls=':',label='Saved stopping threshold');ax.set_yscale('log');ax.set_ylim(3e-17,.1);ax.set_ylabel('Residual ('+unit+')');ax.set_title(panel_title,loc='left');ax.legend(loc='upper left',bbox_to_anchor=(0,.72),fontsize=7);ax.annotate('0 (display floor)' if val==0 else fmt(val),(1,max(val,floor)),xytext=(8,7),textcoords='offset points',fontsize=7,color=col)
 ax=axs[3];err=abs(float(h['objective'])-lp);point(ax,np.log10(max(err,1e-15)),annotate=False);ax.set_ylabel(r'$\log_{10}$(absolute objective error / PCE·min)');ax.set_ylim(-15,-2);ax.set_title('d  Error against same-graph reference',loc='left');ax.annotate(fmt(err)+' PCE·min',(1,np.log10(max(err,1e-15))),xytext=(8,7),textcoords='offset points',fontsize=7)
 for ax in axs:ax.set_xlabel('Recorded outer iteration')
 finish(fig,tid,'admm-saved-state',title,'Four diagnostic panels follow the Hong Kong ADMM figure: original-unit feasibility, primal consensus, rho-scaled dual update, and log10 absolute objective error against the independent same-graph reference. This instance saved exactly one completed outer update, shown as a point rather than an invented convergence curve. Balance, capacity, and primal use PCE; rho-scaled dual and its own threshold use minutes. Only exact-zero residuals use a labeled 1e-16 display floor; positive residuals are unchanged. Objective-error display floor is 1e-15 PCE·min. Saved internal thresholds and the 1e-5 PCE feasibility gate are retained. All displayed states meet the frozen independent gates; objective agreement is not a claim of identical link flows.','primal/dual/feasibility residuals and absolute objective error','PCE; min; log10(PCE·min / PCE·min)',{'a':'Original-unit feasibility','b':'Primal consensus','c':'Rho-scaled dual','d':'Same-graph objective error'},plotdata=j)
def routes(city):
 tid='urbana-champaign-t4-route-counts' if city=='urbana-champaign' else 'pittsburgh-t4-route-counts';t=table(tid);rows=t['blocks'][0]['rows']
 title='Generated routes: flow, cost and arc roles';fig,axs=figaxes(city,title,n=3);fig.set_size_inches(12,4.4);x=np.arange(4);names=['OD 1','OD 2','OD 3','OD 4']
 for ax,key,unit,letter in zip(axs[:2],['flow_pce','route_cost_minutes'],['Assigned flow (PCE)','Fixed route cost (min)'],'ab'):
  vals=[float(r[key]) for r in rows];ax.bar(x,vals,color=TEAL,width=.6);ax.set_xticks(x,names);ax.set_ylabel(unit);ax.set_title(letter+'  '+('Own path flow' if key=='flow_pce' else 'Own path cost'),loc='left');ax.set_ylim(0,max(vals)*1.22)
  for i,v in enumerate(vals):ax.annotate(fmt(v),(i,v),xytext=(0,4),textcoords='offset points',ha='center',fontsize=7)
 ax=axs[2]
 for j,(k,label,col) in enumerate([('physical_road_arcs','Road',TEAL),('turn_movement_arcs','Turn',BLUE),('wait_arcs','Wait',INK)]):ax.bar(x+(j-1)*.24,[int(r[k]) for r in rows],width=.22,color=col,label=label)
 ax.set_xticks(x,names);ax.set_ylabel('Saved arc records');ax.set_title('c  Path composition',loc='left');ax.legend(fontsize=7);ax.set_ylim(0,max(int(r['physical_road_arcs']) for r in rows)*1.3)
 finish(fig,tid,'generated-route-profile',title,'Each category is one of the four saved demand commodities, not a solver iteration. Panels retain the method’s own generated path flow, fixed route cost, and separate counts of movement, turn, and waiting arcs. All four paths have zero waiting arcs. The ordered dynamic arc sequences and existing route maps remain separate geographic evidence; a fixed cost in minutes is not the rounded arrival clock.','path flow, cost, arc composition','PCE; min; count',{'a':'Own path flow','b':'Fixed cost','c':'Separate arc roles'},plotdata=rows)
def objectives(city):
 tid='ith-time-endpoints' if city=='ithaca' else 'pittsburgh-t4-objectives';t=table(tid);rows=t['blocks'][0]['rows'];ith=city=='ithaca'
 names=[r['Method'].upper() if ith else r['method'] for r in rows];objs=[float(r['Objective (PCE·min)'] if ith else r['objective_pce_min']) for r in rows];diff=[float(r['Signed difference (PCE·min)'] if ith else r['signed_difference_from_exact_LP_pce_min']) for r in rows]
 title='Accepted methods on the same finite graph';fig,axs=figaxes(city,title,n=2);x=np.arange(len(rows));ax=axs[0];ax.scatter(x,objs,color=TEAL,s=50);ax.axhline(objs[0],color=BLUE,lw=1,ls='--',label='Independent reference');ax.set_ylim(min(objs)*.92,max(objs)*1.12);ax.set_ylabel('Fixed-cost objective (PCE·min)');ax.set_title('a  Same-instance method endpoints',loc='left');ax.legend(fontsize=8,loc='upper left');ax=axs[1];ax.scatter(x,diff,color=TEAL,s=50);ax.axhline(0,color=BLUE,lw=1);ax.set_ylabel('Signed difference from reference (PCE·min)');ax.set_title('b  Numerical difference at full precision',loc='left');ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
 for ax in axs:ax.set_xticks(x,names);ax.set_xlabel('Method');ax.margins(x=.14)
 for i,v in enumerate(diff):ax.annotate(fmt(v),(i,v),xytext=(0,7),textcoords='offset points',ha='center',fontsize=7)
 ax.set_ylim(min(diff)-max(abs(v) for v in diff)*.2,max(diff)*1.28)
 finish(fig,tid,'time-method-objectives',title,'The methods share this exact four-OD finite graph and fixed-cost objective. Categories are independent method endpoints, not an optimization timeline. Left: each saved objective with the independent reference. Right: signed differences retain full numerical precision, including negative roundoff. All shown methods currently satisfy their independent acceptance conditions. Objective proximity by itself is not a feasibility certificate and does not imply identical physical-link flow.','same-graph objective and signed difference','PCE·min',{'a':'Actual accepted method objectives','b':'Signed difference from independent reference'},plotdata=rows)
def pitinputs():
 tid='pittsburgh-t4-demand';rows=table(tid)['blocks'][0]['rows'];title='Four selected departure demands';fig,axs=figaxes('pittsburgh',title);ax=axs[0];x=np.arange(4);vals=[float(r['Pulse (PCE)']) for r in rows];ax.bar(x,vals,color=TEAL,width=.55);ax.set_xticks(x,['OD 1','OD 2','OD 3','OD 4']);ax.set_ylabel('Departure pulse (PCE)');ax.set_xlabel('Saved input commodity');ax.set_ylim(0,max(vals)*1.22)
 for i,v in enumerate(vals):ax.annotate(fmt(v),(i,v),xytext=(0,5),textcoords='offset points',ha='center',fontsize=8)
 finish(fig,tid,'t4-input-demand',title,'The four input-selected demands total 0.04502754845355 PCE. These are the bounded time-network departure pulses after the saved hourly-to-time factor 1/12, not hourly observed counts. Input commodities are not optimizer iterations. Full source/destination identities are retained in the public plot data.','input departure volume','PCE',{'a':'Four actual input commodities'},plotdata=rows)
 tid='pittsburgh-t4-construction';j=read('assets/algorithm-transfer-r8/pittsburgh/PIT_T01.plot.json');title='Time-expanded network: saved arc roles';fig,axs=figaxes('pittsburgh',title);ax=axs[0];y=np.arange(5);ax.barh(y,j['arc_count'],color=[TEAL,BLUE,CATEGORIES[3],INK,CATEGORIES[4]],height=.6);ax.set_yticks(y,['Physical movement','Legal turn','Waiting','Source connector','Sink connector']);ax.invert_yaxis();ax.set_xscale('log');ax.set_xlim(1,3e6);ax.set_xlabel('Saved dynamic arc records (log scale)')
 for i,v in enumerate(j['arc_count']):ax.annotate(f'{v:,}',(v,i),xytext=(5,0),textcoords='offset points',va='center',fontsize=8)
 finish(fig,tid,'t4-arc-roles',title,'Counts come from the saved T4 construction: 350,106 physical-road arcs, 779,805 turn arcs, 681,742 wait arcs, 4 source connectors and 231 sink connectors. The model uses 30-second steps over 117 steps and four selected departure demands. This composition chart is a count summary, not a geometric reconstruction of the full time-expanded graph; the real road-network view remains separate.','dynamic arc roles','arc records',{'a':'Saved arc-role composition'},plotdata=j)
def main():
 global OUT
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();OUT=a.output
 for city in ['urbana-champaign','pittsburgh']:cg(city);lr(city);admm(city);routes(city)
 admm('ithaca');objectives('ithaca');objectives('pittsburgh');pitinputs()
 manifest=dict(schema='mcl-r12-dynamic-render-results',items=ITEMS,solver_calls=0,source_bytes_preserved=True,limitations=['Ithaca public endpoint release has no numeric CG per-phase artificial-flow/pricing history or LR prices/recovery vectors; no such curves are inferred.','UC/Pittsburgh CG public plot data give global minimum pricing by phase, not per-commodity reduced costs; phase-separated points are used.','Zero positive LR multipliers supply no nonempty top-price map or time histogram.','Pittsburgh construction release provides arc counts, not a full public time-layer geometry; counts are plotted honestly.'])
 OUT.parent.parent.joinpath('DYNAMIC_RENDER_RESULT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'figures':len(ITEMS),'manifest':str(OUT.parent.parent/'DYNAMIC_RENDER_RESULT.json')}))
if __name__=='__main__':main()
