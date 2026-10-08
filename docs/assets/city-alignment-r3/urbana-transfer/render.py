"""Display saved Urbana experiments with the audited Boston/Hong Kong figure grammar."""
from pathlib import Path
import sys,json,hashlib,csv,shutil
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[3]
sys.path.insert(0,str(W.parents[1]/'figure_alignment_r2'))
from atlas_style import *
ROOT=W.parents[3]
from embed_serif_fonts import embed_serif_fonts
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm,TwoSlopeNorm
from PIL import Image
SITE=W.parents[1]/'candidate_repo'; OUT=SITE/'docs/assets/city-alignment-r3/urbana-transfer';OUT.mkdir(parents=True,exist_ok=True)
SRC=ROOT/'deliveries/urbana_champaign_algorithm_transfer_r1';RUN=ROOT/'work/urbana_champaign_algorithm_transfer_r1/runs/berkeley_c2a_transfer_r2'
data=json.loads((W/'derived.json').read_text());matrix=json.loads((SRC/'RESULT_MATRIX.json').read_text());methods={r['method']:r for r in matrix['methods']}
def J(n):return json.loads((SRC/'figures'/f'{n}.plot.json').read_text())
def C(p):
    with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def frame(title,scope='T4 · 4 OD · 0.051623 PCE pulse',n=1,size=None):
    fig=new_figure('Urbana–Champaign',title,scope,figsize=size or (7.7,4.7))
    ax=fig.subplots(1,n,squeeze=False)[0];fig.subplots_adjust(left=.11,right=.96,bottom=.18,top=.72,wspace=.42)
    for a in ax:format_axes(a)
    return fig,ax
def save(fig,stem,title,stage,method,caption,payload):
    compact_header(fig)
    for ext in ['svg','png','pdf']:fig.savefig(OUT/f'{stem}.{ext}',dpi=240,bbox_inches='tight',pad_inches=.06,metadata={'Date':None} if ext=='svg' else None)
    embed_serif_fonts(OUT/f'{stem}.svg');plt.close(fig)
    (OUT/f'{stem}.plot_data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
    w,h=Image.open(OUT/f'{stem}.png').size
    rel='assets/city-alignment-r3/urbana-transfer/'+stem
    r={'id':'UC-R3-'+stem.upper(),'title':title,'src':rel+'.svg','width':w,'height':h,'caption':caption,'href':'volumes/urbana-champaign.html#uc-r3-'+stem,'anchor':'atlas-uc-r3-'+stem,'full':rel+'.svg','evidence':'volumes/urbana-champaign.html#uc-r3-'+stem,'stage':stage,'method':method,'links':[{'label':s,'href':rel+e} for s,e in [('SVG','.svg'),('PNG','.png'),('PDF','.pdf'),('Plot data','.plot_data.json'),('Source record','.source.json')]]}
    (OUT/f'{stem}.source.json').write_text(json.dumps({'figure':r,'renderer':{'file':'render.py','function':'main','style':'new_figure / format_axes / compact_header'},'solver_calls':0,'result_matrix_sha256':sha(SRC/'RESULT_MATRIX.json'),'derived_data_sha256':sha(W/'derived.json'),'status':'LOCAL_SAVED_RESULT_DERIVATIVE','exports':{ext:sha(OUT/f'{stem}.{ext}') for ext in ['svg','png','pdf']}},ensure_ascii=False,indent=2),encoding='utf8')
    records.append(r);print(stem,flush=True)
def dot(a,x,y,label=None,color=TEAL):a.plot(x,y,'o',color=color,label=label,ms=6);a.set_xlim(.5,1.5);a.set_xticks([1]);a.set_xlabel('Saved iteration');return a
def mapdraw(a,values,title,norm=None,cmap=FLOW_CMAP,included=None):
    seg=data['segments'];v=np.array(values);a.add_collection(LineCollection(seg,colors=ROAD,linewidths=.45,zorder=0));norm=norm or PowerNorm(.5,vmin=0,vmax=max(v.max(),1e-12));lc=LineCollection(seg,cmap=cmap,norm=norm,linewidths=.45+1.4*np.sqrt(np.abs(v)/(max(abs(v).max(),1e-30))));lc.set_array(np.ma.array(v,mask=~np.array(included,dtype=bool)) if included is not None else v);a.add_collection(lc);a.autoscale();a.set_aspect('equal');a.set_title(title,loc='left');a.set_xlabel('East (km)');a.set_ylabel('North (km)');a.grid(color=GRID,lw=.3);return lc
def main():
    d=J('UC_S01');fig,aa=frame('Static methods on the same selected demand','S72 · 72 OD · 321.630 PCE / hour',2)
    aa[0].bar(['FW','Finite'],d['Beckmann_pce_min'],color=[INK,TEAL]);aa[0].set_ylabel('Beckmann objective (PCE min)')
    for i,v in enumerate(d['Beckmann_pce_min']):aa[0].text(i,v*.5,f'{v:.6f}',ha='center',color='white',rotation=90)
    aa[1].scatter(['FW','Finite'],d['full_graph_relative_gap'],color=[INK,TEAL],s=45);aa[1].set_yscale('log');aa[1].axhline(1e-5,color=BLUE,ls='--',label='1e−5 gate');aa[1].set_ylabel('Full-graph relative gap');aa[1].legend(fontsize=8)
    save(fig,'static-comparison','Static methods on the same selected demand','static','finite-path','S72 FW initial loading and full 360-path finite reference agree. FW performed zero updates. Selected 72 OD are distinct from the original 418-OD city case.',d)
    d=J('UC_S02');fig,aa=frame('Native endpoints retain failed OD conservation','S72 · raw rank-26/52 states · no repaired flow',2)
    for key,col in [('rank26',INK),('rank52',TEAL)]:a=np.array(d[key]);aa[0].semilogy(a[:,0],a[:,1],'-o',label=key,color=col,ms=3)
    aa[0].axhline(d['OD_abs_gate_pce'],ls='--',color=BLUE,label='OD gate');aa[0].set_xlabel('Actual outer iteration');aa[0].set_ylabel('Maximum OD residual (PCE)');aa[0].legend(fontsize=8)
    sizes=J('UC_S04');x=np.arange(2);aa[1].bar(x-.16,[r['path_coordinates'] for r in sizes],.32,color=TEAL,label='Path coordinates');aa[1].bar(x+.16,[r['total_optimizer_variables'] for r in sizes],.32,color=INK,label='Total variables');aa[1].set_yscale('log');aa[1].set_xticks(x,['rank 26','rank 52']);aa[1].set_ylabel('Coordinate count (log scale)');aa[1].legend(fontsize=7,loc='lower left',bbox_to_anchor=(0,1.04))
    save(fig,'native-check','Native endpoints retain failed OD conservation','static','native-l3','Both ranks execute eight recorded outer steps but retain about 8.25e−5 PCE OD error above the 1e−6 gate. Total variables include explicit links; neither rank is accepted.',{'history':d,'dimensions':sizes})
    fig,aa=frame('Selected static physical-road loading','S72 · 72 OD · physical roads only',2)
    lc=mapdraw(aa[0],data['static'],'a  Saved FW physical flow');fig.colorbar(lc,ax=aa[0],fraction=.045,pad=.03,label='PCE / hour')
    flow=np.array(data['static']);aa[1].hist(flow[flow>0],bins=20,color=TEAL);aa[1].set_xlabel('Positive physical flow (PCE / hour)');aa[1].set_ylabel('Physical solver-arc count')
    save(fig,'static-map','Selected static physical-road loading','static','fw','All 11,365 physical solver arcs are retained. The 42 half-length A/B arcs use their separate geometric halves; serial pieces are not summed into a whole-road flow. Turns are excluded. This is S72 loading, separate from the full four-stage city case.',{'gids':data['gids'],'flow':data['static'],'projection':data['projection']})
    p=data['cg_paths'][0];arcs=p['arcs'];small=[a for a in arcs if a['arc_type'] in ['physical_road','turn_movement'] and int(a['from_time'])<9];states=list(dict.fromkeys([a[k].rsplit('@t',1)[0] for a in small for k in ['from_node_time_id','to_node_time_id']]))
    fig,aa=frame('Actual route through selected time layers','T4 · first computed CG path · 30 s layers',size=(8.7,5.2));a=aa[0]
    for arc in small:
        y1=states.index(arc['from_node_time_id'].rsplit('@t',1)[0]);y2=states.index(arc['to_node_time_id'].rsplit('@t',1)[0]);x1=int(arc['from_time']);x2=int(arc['to_time']);col=TEAL if arc['arc_type']=='physical_road' else BLUE;a.annotate('',(x2,y2),(x1,y1),arrowprops={'arrowstyle':'->','color':col,'lw':1.7})
        a.scatter([x1,x2],[y1,y2],color=col,s=17,zorder=3)
    a.set_yticks(range(len(states)),states,fontsize=7);a.set_xticks(range(5,10));a.set_xlabel('Time layer (30 seconds per step)');a.set_ylabel('Saved road states (IN / MID / OUT)');a.invert_yaxis();a.grid(color=GRID,lw=.5)
    save(fig,'time-layers','Actual route through selected time layers','construction','', 'An actual generated route fragment, not a drawn full network: road traversals advance time; turn transitions preserve time. M states denote split-road midpoints. Only selected saved arcs are shown. The full T4 graph has 1,429,496 arcs.',{'arcs':small,'graph_counts':J('UC_T01')})
    fig,aa=frame('Computed paths: time layers and fixed costs','T4 · four self-generated CG paths',2)
    for i,p in enumerate(data['cg_paths']):
        ar=[a for a in p['arcs'] if a['arc_type']=='physical_road'];aa[0].step(range(len(ar)),[int(a['to_time']) for a in ar],where='post',label=f'OD {i+1}',color=CATEGORIES[i])
    aa[0].set_xlabel('Physical traversal index');aa[0].set_ylabel('Arrival time layer');aa[0].legend(fontsize=7)
    d=J('UC_T06');aa[1].bar(range(4),[r['route_cost_minutes'] for r in d],color=CATEGORIES[:4]);aa[1].set_xticks(range(4),['OD 1','OD 2','OD 3','OD 4']);aa[1].set_ylabel('Fixed route objective cost (min)')
    save(fig,'computed-paths','Computed paths: time layers and fixed costs','construction','', 'Rounded physical arrival layers differ from original fixed objective minutes. Four saved legal paths contain physical and turn arcs; no waiting arc carries these paths. Sink ledger time is not physical queueing.',{'routes':d,'paths':data['cg_paths']})
    cg=C(RUN/'T/cg/history.csv');pi=[r for r in cg if r['phase']=='I'];p2=[r for r in cg if r['phase']=='II']
    fig,aa=frame('CG Phase I: artificial flow at the saved check');dot(aa[0],[1],[float(pi[0]['artificial_mass'])]);aa[0].axhline(1e-8,color=BLUE,ls='--',label='1e−8 PCE gate');aa[0].set_ylabel('Artificial flow (PCE)');aa[0].set_ylim(-2e-9,1.2e-8);aa[0].legend(fontsize=8)
    save(fig,'cg-phase1','CG Phase I: artificial flow at the saved check','finite','cg','One saved Phase-I round; artificial mass is already zero with four self-generated paths. This is an endpoint check, not a multi-round convergence curve.',pi)
    fig,aa=frame('CG Phase II: saved objective against exact LP');dot(aa[0],[1],[float(p2[0]['objective'])],label='CG endpoint');aa[0].axhline(methods['T_LP_EXACT_DAG']['objective_pce_min'],color=INK,ls='--',label='Exact-DAG LP');aa[0].set_ylim(.35,.4);aa[0].set_ylabel('Fixed-cost objective (PCE min)');aa[0].legend(fontsize=8)
    save(fig,'cg-objective','CG Phase II: saved objective against exact LP','finite','cg','One Phase-II record agrees with the same-model exact-DAG LP within floating-point precision. The separate HiGHS process failed; the reference is a separate independently certified mathematical LP endpoint.',p2)
    fig,aa=frame('CG closure: full-DAG pricing by phase',n=2)
    for a,rr,label in zip(aa,[pi,p2],['Phase I reduced cost (dimensionless)','Phase II reduced cost (min)']):dot(a,[1],[float(rr[0]['minimum_reduced_cost'])]);a.axhline(0,color=INK,lw=.6);a.set_ylabel(label);a.set_ylim(-1e-6,1e-6)
    save(fig,'cg-closure','CG closure: full-DAG pricing by phase','finite','cg','Independent full-DAG pricing checks every legal arc for each commodity. Phase-I artificial-flow and Phase-II travel-cost pricing have different units; their zero values are plotted separately.',cg)
    lr=C(RUN/'T/lr/history.csv');r=lr[0];fig,aa=frame('Lagrangian bounds at the actual saved iteration');dot(aa[0],[1],[float(r['best_dual'])],label='Valid lower bound',color=INK);dot(aa[0],[1],[float(r['best_primal'])],label='Feasible upper bound');aa[0].set_ylim(.35,.4);aa[0].set_ylabel('Fixed-cost bound (PCE min)');aa[0].legend(fontsize=8)
    save(fig,'lr-bounds','Lagrangian bounds at the actual saved iteration','finite','lagrangian','One actual iteration closes the bounds in this nonbinding-capacity T4 instance. Tiny signed roundoff remains in the saved values; no interpolated iterations or smoothed gap are created.',lr)
    fig,aa=frame('Capacity prices remain zero in this T4 instance',n=2);dot(aa[0],[1],[float(r['max_multiplier'])]);aa[0].set_ylabel('Maximum capacity price (min)');dot(aa[1],[1],[int(r['multiplier_positive_count'])]);aa[1].set_ylabel('Positive multiplier count');aa[1].set_ylim(-.05,1.05);aa[1].set_yticks([0,1])
    save(fig,'lr-prices','Capacity prices remain zero in this T4 instance','finite','lagrangian','The saved nonnegative multipliers are zero. Total pulse demand is below the minimum physical-arc capacity, so this experiment does not test a congested or binding bottleneck.',lr)
    pp=C(RUN/'T/lr/positive_paths.csv');rec=json.loads((RUN/'T/lr/recovery_history.json').read_text());fig,aa=frame('Lagrangian recovery: four feasible path flows',n=2)
    aa[0].bar(range(4),[float(p['flow']) for p in pp],color=CATEGORIES[:4]);aa[0].set_xticks(range(4),['OD 1','OD 2','OD 3','OD 4']);aa[0].set_ylabel('Recovered path flow (PCE / pulse)')
    a=aa[1];a.bar(['Recovered'],[rec[0]['objective']],color=TEAL);a.axhline(methods['T_LP_EXACT_DAG']['objective_pce_min'],ls='--',color=INK,label='Exact-DAG LP');a.set_ylabel('Feasible objective (PCE min)');a.legend(fontsize=8)
    save(fig,'lr-recovery','Lagrangian recovery: four feasible path flows','finite','lagrangian','Recovery uses LR-generated paths and the saved feasible endpoint. It is distinct from the dual lower-bound calculation and is not initialized by the LP or CG solution.',{'positive_paths':pp,'recovery':rec})
    d=J('UC_T05')[0];check=json.loads((RUN/'T/admm_main/independent_check.json').read_text());fig,aa=frame('ADMM objective: one completed cold-start update',n=3,size=(10.5,4.8))
    dot(aa[0],[1],[d['objective']],label='Own-x objective');aa[0].axhline(methods['T_LP_EXACT_DAG']['objective_pce_min'],ls='--',color=INK,label='Exact-DAG LP');aa[0].set_ylim(.35,.4);aa[0].set_ylabel('Fixed-cost objective (PCE min)');aa[0].legend(fontsize=7)
    q=check['reference_comparison'];aa[1].scatter(['Absolute error'],[q['absolute_difference']],color=INK,s=40);aa[1].set_yscale('log');aa[1].set_ylabel('Absolute objective error (PCE min)');aa[2].scatter(['Contract','True relative'],[q['contract_normalized_difference'],q['true_relative_difference']],color=[TEAL,BLUE],s=40);aa[2].set_yscale('log');aa[2].axhline(1e-4,color=INK,ls='--',label='Contract gate');aa[2].set_ylabel('Normalized error (dimensionless)');aa[2].tick_params(axis='x',rotation=20);aa[2].legend(fontsize=7)
    save(fig,'admm-objective','ADMM objective: one completed cold-start update','finite','admm','One actual update plus an independent cold confirmation. Absolute error is PCE min; contract-normalized error divides by max(1, |LP|), while true relative error divides by |LP|. Here LP < 1, so the last two differ. The objective gate remains 1e−4.',{'history':d,'comparison':q})
    fig,aa=frame('ADMM residuals and recorded stopping thresholds',n=2)
    for a,k,title in zip(aa,['primal','dual'],['Primal consensus (PCE)','Dual residual (PCE)']):
        val=d[k+'_residual'];gate=d[k+'_threshold'];a.scatter([1],[val if val>0 else 1e-16],color=TEAL,s=45);a.axhline(gate,color=BLUE,ls='--',label=f'Saved gate {gate:.4g}');a.set_yscale('log');a.set_xlim(.5,1.5);a.set_xticks([1]);a.set_xlabel('Completed update');a.set_ylabel(title);a.legend(fontsize=7)
        if val==0:a.annotate('True zero → display at 1e−16',(1,1e-16),xytext=(0,9),textcoords='offset points',ha='center',fontsize=7)
    save(fig,'admm-residuals','ADMM residuals and recorded stopping thresholds','finite','admm','Only one saved update exists. Exact zero is displayed at 1e−16 only for the logarithmic axis; all positive saved residuals remain unchanged. This solver receipt reports both residual quantities in PCE.',d)
    f=np.array(data['flows']['lp']);g=np.array(data['flows']['admm']);diff=g-f;fig=new_figure('Urbana–Champaign','ADMM and exact LP on physical roads','T4 · same pulse · own saved states',figsize=(9.2,8));aa=fig.subplots(2,2);fig.subplots_adjust(left=.09,right=.92,bottom=.09,top=.80,wspace=.4,hspace=.42)
    norm=PowerNorm(.5,vmin=0,vmax=max(f.max(),g.max()));
    for a,v,t in [(aa[0,0],f,'a  Exact LP'),(aa[0,1],g,'b  ADMM own x')]:lc=mapdraw(a,v,t,norm,included=data['in_t']);fig.colorbar(lc,ax=a,fraction=.04,pad=.03,label='PCE / pulse')
    mag=max(abs(diff).max(),1e-16);lc=mapdraw(aa[1,0],diff,'c  ADMM − exact LP',TwoSlopeNorm(vmin=-mag,vcenter=0,vmax=mag),DIFF_CMAP,included=data['in_t']);fig.colorbar(lc,ax=aa[1,0],fraction=.04,pad=.03,label='PCE / pulse')
    a=aa[1,1];a.scatter(f[np.array(data['in_t'])],g[np.array(data['in_t'])],s=5,alpha=.6,color=TEAL);a.plot([0,max(f.max(),g.max())],[0,max(f.max(),g.max())],ls='--',color=INK,lw=.8);a.set_xlabel('Exact LP physical flow (PCE / pulse)');a.set_ylabel('ADMM physical flow (PCE / pulse)');a.set_title('d  All T-included physical arcs',loc='left');format_axes(a)
    save(fig,'admm-physical','ADMM and exact LP on physical roads','finite','admm',f'Physical traversal flows from each method’s own state are summed over commodities/time per physical solver arc. All 11,365 physical arcs form the base map; 6,741 are instantiated in T and colored. The other 4,624 are uninstantiated context, not solved zero-flow arcs. Split A/B arcs use their own source-line halves. The frozen GMNS mapping is kept, without adding serial partial flows. Maximum absolute difference is {abs(diff).max():.8g} PCE. Absolute maps share a square-root color scale; signed differences use a symmetric scale. OSM contributors / ODbL; model flows, not observations.',{'gids':data['gids'],'lp':f.tolist(),'admm':g.tolist(),'difference':diff.tolist(),'included_in_T':data['in_t'],'projection':data['projection']})
    # Preserve the twelve prior method views as an appendix, with original numerical records.
    old=OUT/'original-method-figures';old.mkdir(exist_ok=True)
    for p in (SRC/'figures').iterdir():
        if p.is_file():shutil.copy2(p,old/p.name)
    for n in ['RESULT_MATRIX.json','GATES.json','INSTANCE_IDENTITY.json']:shutil.copy2(SRC/n,OUT/n)
    shutil.copy2(W/'DERIVATION.json',OUT/'DERIVATION.json');shutil.copy2(W/'render.py',OUT/'render.py');shutil.copy2(W/'prepare.py',OUT/'prepare.py');shutil.copy2(W/'derived.json',OUT/'derived.json')
    (W/'FIGURES.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8');shutil.copy2(W/'FIGURES.json',OUT/'FIGURES.json')
    (W/'RESULTS.json').write_text(json.dumps({'status':'BUILT','new_figures':len(records),'original_appendix_figures':12,'solver_calls':0,'unique_source_geometries':11344,'physical_solver_arcs':11365,'max_admm_lp_physical_difference':data['max_admm_lp_physical_difference']},indent=2),encoding='utf8')
if __name__=='__main__':main()
