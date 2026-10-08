"""Rebuild R11 display figures from exact released public aggregate data only.

No solver, matcher, private input, or network access. Preserve the approved GAP
source files; write derivatives to an explicitly selected output directory.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from matplotlib.ticker import MaxNLocator
try:
    from . import style as S
except ImportError:
    import style as S

REPO=Path(__file__).resolve().parents[2]
PUBLIC=REPO/'docs/assets/gap-20261008'
CAT=json.loads((PUBLIC/'INCREMENT_CONSUMPTION_RESULT.json').read_text(encoding='utf-8'))
ALLOWED={x['source_archive_target']:x for x in CAT['records']}
FIGURES=[]; TABLES=[]; MAPPING={}; OUT=None
OLD_ADMM_PATH='docs/assets/algorithm-transfer-r8/chicago/C06_T_ADMM_main_plot_data.json'
OLD_ADMM_SHA='d761c62c48c081e75ff4cdd7fd276117badf9c1da313cb6332b98584a547f827'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source(city,name):
    rel='docs/assets/gap-20261008/'+city+'/'+name
    item=ALLOWED[rel];p=REPO/rel
    if sha(p)!=item['sha256']: raise ValueError('Released source changed: '+rel)
    return {'public_path':rel,'sha256':item['sha256']}
def data(city,name):return json.loads((REPO/source(city,name)['public_path']).read_text(encoding='utf-8'))
def text(city,name):return (REPO/source(city,name)['public_path']).read_text(encoding='utf-8')
def rows(city,name):return list(csv.DictReader(io.StringIO(text(city,name))))
def cite(city,names):return [source(city,n) for n in names]
def notice(city,filename):return ALLOWED['docs/assets/gap-20261008/'+city+'/'+filename]['notice']
def figure(city,title,scope,wide=False):
    f=S.new_figure(city,title,scope,figsize=(9,4.9) if wide else (8,4.9))
    return f

def emit(f,city,stem,family,instance,title,role,conclusion,panels,quantity,unit,caption,names,saved_states=None,extra_sources=None):
    record={'figure_id':stem,'city':city,'instance':instance,'role':role,'conclusion':conclusion,'panels':panels,'quantity':quantity,'unit':unit,'original_family':family,'archetype':'quantitative grid','generator_public_path':'tools/figures/render_gap_progress.py','generator_sha256':sha(__file__),'data_transform':'Saved values; scalar display conversions only. No fitted or interpolated states.','source_status':'S0 release_v002; receiver status recorded separately from frozen producer metadata.'}
    if saved_states is not None:record['saved_states']=saved_states
    caption=caption+' '+notice(city,names[0])
    sources=cite(city,names)+(extra_sources or [])
    result=S.export_figure(f,OUT/city/stem,record,caption=caption,sources=sources)
    result.pop('text_audit',None)
    FIGURES.append({'family':family,'city':city,'stem':stem,'title':title,'files':{ext:city+'/'+stem+'.'+ext for ext in ['png','svg','pdf','source.json','caption.md']},'caption':caption,'instance':instance,'role':role,'sources':sources,'dimensions':result['dimensions']})
    MAPPING.setdefault(family,{'figures':[],'tables':[],'original_source':'docs/assets/gap-20261008/'+city+'/'+family+'.png'})['figures'].append(city+'/'+stem)

def table(city,tid,family,title,columns,records,caption,names,scope):
    item={'table_id':tid,'family':family,'city':city,'title':title,'columns':columns,'rows':records,'caption':caption+' '+notice(city,names[0]),'scope':scope,'sources':cite(city,names),'source_status':'S0 release_v002; frozen producer statuses retained in original data','no_new_solver_calls':True}
    TABLES.append(item);MAPPING.setdefault(family,{'figures':[],'tables':[],'original_source':'docs/assets/gap-20261008/'+city+'/'+family+'.png'})['tables'].append(tid)

def one_ax(f,left=.12):
    ax=f.add_axes([left,.17,.96-left,.57]);S.format_axes(ax);ax.set_axisbelow(True);return ax

def temporal(ax,x,y,label=None,color=None,marker='o',log=False):
    ax.plot(x,y,color=color or S.TEAL,lw=1.6,marker=marker,ms=3.4,label=label)
    if log:ax.set_yscale('log')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.margins(x=.025)


def joined_admm_history():
    """Join two already-public histories after exact overlap verification."""
    oldpath=REPO/OLD_ADMM_PATH
    if sha(oldpath)!=OLD_ADMM_SHA:raise ValueError('Original public ADMM source changed')
    old=json.loads(oldpath.read_text(encoding='utf-8'))
    new=data('chicago','C06_ADMM_GAP_INCREMENT.public_plot.json')['actual_history_from_outer9']
    fields=['iteration','rho','objective','primal_residual','dual_residual','primal_threshold','dual_threshold','capacity_residual','balance_residual']
    overlap={k:{'old':old[-1][k],'new':new[0][k],'equal':float(old[-1][k])==float(new[0][k])} for k in fields}
    assert all(v['equal'] for v in overlap.values()),'ADMM overlap mismatch'
    assert [int(x['iteration']) for x in old]==list(range(1,10))
    assert [int(x['iteration']) for x in new]==list(range(9,34))
    h=[]
    for row in old[:-1]:
        rr={k:float(row[k]) for k in fields}
        rr.update(primal_over_gate=rr['primal_residual']/rr['primal_threshold'],dual_over_gate=rr['dual_residual']/rr['dual_threshold'])
        h.append(rr)
    h+=new
    assert [int(x['iteration']) for x in h]==list(range(1,34))
    sources=[{'public_path':OLD_ADMM_PATH,'sha256':OLD_ADMM_SHA},source('chicago','C06_ADMM_GAP_INCREMENT.public_plot.json')]
    payload={'schema':'mcl_public_admm_history_join_r11','sources':sources,'overlap_outer':9,'overlap_exact_numeric_checks':overlap,'saved_states':33,'transform':'Public original states 1–8 plus public increment states 9–33. Original 1–8 residual ratios are residual divided by that row’s own saved threshold. No interpolation.','records':h}
    (OUT/'chicago').mkdir(parents=True,exist_ok=True)
    (OUT/'chicago/chi-admm-history.plot.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return h,[sources[0]]

def urbana():
    city='urbana-champaign';a=data(city,'UC_GAP_C1.plot.json');names=['Frozen baseline','GTFS revision'];labels=['Original input','Timetable revision'];modes=['drive','walk','transit'];colors=[S.INK,'#80c3bd',S.TEAL]
    f=figure(city,'Mode demand under two transit inputs','418 OD / fixed person demand',True);gs=f.add_gridspec(1,2,left=.16,right=.97,bottom=.19,top=.73,wspace=.34,width_ratios=[1.6,1]);ax=f.add_subplot(gs[0]);bx=f.add_subplot(gs[1]);S.format_axes(ax);S.format_axes(bx)
    left=np.zeros(2)
    for mode,col in zip(modes,colors):
        vals=[a['person_trips_by_mode'][n][mode] for n in names];ax.barh(range(2),vals,left=left,height=.47,color=col,label=mode.title());left+=vals
    ax.set_yticks(range(2),labels);ax.invert_yaxis();ax.set_xlabel('Person trips / modeled hour');ax.set_xlim(0,3150);ax.set_title('a  Conditional mode demand',loc='left');ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.19),fontsize=8);ax.grid(False);ax.grid(axis='x',color=S.GRID,lw=.5);ax.set_axisbelow(True)
    vals=[a['vehicle_pce_per_hour'][n] for n in names];bx.barh(range(2),vals,color=[S.INK,S.TEAL],height=.47);bx.set_yticks(range(2),[]);bx.invert_yaxis();bx.set_xlabel('Vehicle demand (PCE/h)');bx.set_xlim(0,2450);bx.set_title('b  Assigned vehicle demand',loc='left');bx.grid(False);bx.grid(axis='x',color=S.GRID,lw=.5);bx.set_axisbelow(True)
    for i,v in enumerate(vals):bx.text(v+45,i,f'{v:,.1f}',va='center',fontsize=8)
    emit(f,city,'uc-mode-demand','UC_GAP_C1',a['input_revision'],'Mode demand under two transit inputs','scenario_comparison','Dated timetable availability changes the conditional split under fixed total person demand.',['Mode person trips','Vehicle PCE/h'],'mode demand and vehicle demand',['person trips per modeled hour','PCE/h'],'The person total is 2,989.8528 across 418 OD. The timetable revision predicts 461.581416 transit person trips and 1,667.089946 PCE/h, versus 1,963.648313 PCE/h under the earlier mode inputs. Both totals are engineering predictions; their different demands do not compare solver quality.',['UC_GAP_C1.plot.json','UC_GAP_C1.caption.md'])
    b=data(city,'UC_GAP_C2.plot.json');vals=b['transit_person_weighted_mean_generalized_min_components'];f=figure(city,'Scheduled transit cost components','418 OD / four departure queries');ax=one_ax(f,.24);v=list(vals.values());ax.barh(range(len(v)),v,color=S.TEAL,height=.55);ax.set_yticks(range(len(v)),list(vals));ax.invert_yaxis();ax.set_xlabel('Transit-person-weighted generalized minutes');ax.set_xlim(0,max(v)*1.22);ax.grid(False);ax.grid(axis='x',color=S.GRID,lw=.5)
    for k,val in enumerate(v):ax.text(val+.16,k,f'{val:.2f}',va='center',fontsize=8)
    emit(f,city,'uc-transit-cost','UC_GAP_C2','UC_MODE_TRANSIT_EXTENSION_20261008_R2','Scheduled transit cost components','input_evidence','The scheduled transit option has separate access, wait, ride, transfer and fare costs.',['Five transit cost components'],'transit-person-weighted generalized cost','minutes','Costs use the 2026-10-07 CUMTD schedule, directed walking access and a stated adult fare scenario. The 1,672 queries are 418 OD × four departure samples, not passenger observations.',['UC_GAP_C2.plot.json','UC_GAP_C2.caption.md'])

def pittsburgh():
    city='pittsburgh';d=data(city,'PIT_G05.plot.json');f=figure(city,'Native conservation through outer 14','S72 / ranks 26 and 52');ax=one_ax(f,.14)
    for rank,col,mark in [('26',S.INK,'o'),('52',S.TEAL,'s')]:
        h=d['series'][rank];x=[r['outer'] for r in h];y=[r['max_abs_od_residual_pce'] for r in h];temporal(ax,x,y,'Rank '+rank,col,mark,True)
    ax.axhline(d['gate_pce'],ls='--',lw=1,color='#65757d',label='Original OD gate');ax.axvline(8.5,color='#9ba4a8',ls=':',lw=1);ax.set_xlabel('Completed ALM outer iteration');ax.set_ylabel('Maximum OD residual (PCE in modeled hour)');ax.set_ylim(3e-8,2);ax.set_xticks(range(1,15));ax.legend(loc='upper right',fontsize=8)
    emit(f,city,'pit-native-conservation','PIT_G05',d['model_id'],'Native conservation through outer 14','iteration','Both saved Native ranks meet the original OD gate at outer 14 after continuation.',['Maximum original-coordinate OD residual'],'maximum absolute OD residual',d['unit'],'Each rank has 14 saved outer states. The divider separates original outers 1–8 from continuation 9–14. At outer 14 the rank 26/52 residuals are 8.0701348e−8 and 2.6256443e−7 PCE; the original gate is 1e−6 PCE. Other original-space gates are checked separately.',['PIT_G05.plot.json','PIT_G05.caption.txt'],14)

def chicago():
    city='chicago';d=data(city,'C06_HOUSEHOLDS_GAP.plot.json');pts=d['points'];f=figure(city,'Household allocation to the five model zones','ACS 2019–2023 / original zones');ax=one_ax(f,.29);v=[r['allocated_households']/1000 for r in pts];ax.barh(range(5),v,color=S.TEAL,height=.57);ax.set_yticks(range(5),[r['zone_id']+'  '+r['name'] for r in pts]);ax.invert_yaxis();ax.set_xlim(0,29);ax.set_xlabel('Area-allocated households (thousands)');ax.grid(False);ax.grid(axis='x',color=S.GRID,lw=.5)
    for k,val in enumerate(v):ax.text(val+.35,k,f'{val:.2f}',va='center',fontsize=8)
    emit(f,city,'chi-household-allocation','C06_HOUSEHOLDS_GAP',d['model_id'],'Household allocation to the five model zones','input_evidence','A traceable area allocation supplies a supplemental household field for the same five zones.',['Allocated households by zone'],'area-allocated households','households','The five estimates total 51,874.133727 households. ACS tract totals are allocated by area; these are not observed model-zone counts or confidence intervals. Original population, demand inputs and S/T results are unchanged. The approved original retains the zone-location map; this derivative uses only public aggregate values.',['C06_HOUSEHOLDS_GAP.plot.json','C06_HOUSEHOLDS_GAP.caption.md'])
    d=data(city,'C06_LR_SELF_POOL_GAP.plot.json');p1=d['phase1'];p2=d['phase2'];names=['C06_LR_SELF_POOL_GAP.plot.json','C06_LR_SELF_POOL_GAP.caption.md'];inst=d['independent_endpoint']['method']
    f=figure(city,'Own-pool feasibility recovery','T4 / self-priced LR hybrid');ax=one_ax(f,.13);temporal(ax,[r['round'] for r in p1],[r['artificial_pce'] for r in p1]);ax.set_xlabel('Own feasibility-pricing round');ax.set_ylabel('Artificial unserved demand (PCE)');ax.set_ylim(bottom=-.6)
    emit(f,city,'chi-lr-feasibility','C06_LR_SELF_POOL_GAP',inst,'Own-pool feasibility recovery','iteration','The hybrid removes its own restricted-pool artificial demand over 26 pricing rounds.',['Artificial demand in own path pool'],'artificial unserved demand','PCE','These are the hybrid’s 26 own-pool feasibility rounds. They precede the separate 10 original-cost iterations; they are not 36 equivalent subgradient steps. The earlier pure LR failure remains a distinct result.',names,len(p1))
    f=figure(city,'Lagrangian bounds and own recovery','T4 / self-priced LR hybrid');ax=one_ax(f,.13);x=[r['iteration'] for r in p2];temporal(ax,x,[r['best_upper'] for r in p2],'Own feasible upper',S.INK);temporal(ax,x,[r['best_lower'] for r in p2],'Full-graph lower',S.TEAL,marker='s');ax.set_xlabel('Original-cost pricing iteration');ax.set_ylabel('Objective bound (PCE·min)');ax.legend(loc='upper right',fontsize=8)
    emit(f,city,'chi-lr-bounds','C06_LR_SELF_POOL_GAP',inst,'Lagrangian bounds and own recovery','iteration','The saved hybrid closes its own feasible upper and full-graph lower bounds.',['Own upper and full-graph lower'],'objective bound','PCE·min','All 10 original-cost iterations are retained. At the independently checked endpoint, lower=239.1173646810 and upper=241.2268172335 PCE·min. Recovery uses the hybrid’s own path pool; the bounds do not relabel the earlier pure LR result.',names,len(p2))
    f=figure(city,'Lagrangian certificate gap','T4 / self-priced LR hybrid');ax=one_ax(f,.13);temporal(ax,x,[100*r['signed_bound_gap'] for r in p2]);ax.axhline(1,color='#65757d',ls='--',lw=1,label='Original 1% gate');ax.set_xlabel('Original-cost pricing iteration');ax.set_ylabel('Signed bound gap (%)');ax.set_ylim(bottom=0);ax.legend(loc='upper right',fontsize=8)
    emit(f,city,'chi-lr-certificate','C06_LR_SELF_POOL_GAP',inst,'Lagrangian certificate gap','iteration','The signed own-pool certificate reaches 0.8744685%, below its unchanged 1% gate.',['Signed bound certificate'],'(upper−lower)/max(1,abs(upper))','percent','Gap is (own feasible upper−full-graph lower)/max(1,|own feasible upper|). The 10 saved original-cost points end at 0.8744685%. Producer-pending words in the frozen source are historical; S0 release_v002 accepts the named hybrid at its original gate.',names,len(p2))
    d=data(city,'C06_NATIVE_B_INCREMENT.public_plot.json');h=d['B_reported_history'];ep=d['B_independent_endpoint'];f=figure(city,'Algorithm B: full-graph gap','S20 / original demand');ax=one_ax(f,.13);temporal(ax,[r['iteration'] for r in h],[r['reported_relative_gap'] for r in h],'Solver history',S.TEAL,log=True);ax.scatter([h[-1]['iteration']],[ep['full_graph_signed_relative_gap']],s=38,facecolors='white',edgecolors=S.INK,marker='s',label='Independent endpoint',zorder=4);ax.axhline(1e-5,ls='--',color='#65757d',lw=1,label='Original gate');ax.set_xlabel('Algorithm B iteration');ax.set_ylabel('Full-graph relative gap');ax.set_xticks(range(1,7));ax.legend(fontsize=8,loc='upper right')
    emit(f,city,'chi-algorithm-b-gap','C06_NATIVE_B_INCREMENT','CH_S20_STATIC_BPR','Algorithm B: full-graph gap','iteration','Algorithm B reaches its original full-graph gate on the frozen S20 instance.',['Reported gap and independently recomputed endpoint'],'full-graph relative gap','dimensionless','The 6 recorded Algorithm B iterations end at an independently recomputed 1.5807459e−9 full-graph relative gap. The original 1e−5 gate is unchanged. Its approved source PNG retains a flow map; map coordinates are not included in the public plot data and are not reconstructed here.',['C06_NATIVE_B_INCREMENT.public_plot.json','C06_NATIVE_B_INCREMENT.caption.md'],len(h))
    nr=[]
    for r in d['Native_new_controls']:
        nr.append({'method':r['method'],'representation':'U=I80; full minor coordinates' if r['method']=='Native80' else 'Frozen compressed representation','objective_PCE_min_per_h':r['objective_pce_min'],'full_graph_gap':r['full_graph_gap'],'restricted_pool_gap':r['restricted_pool_gap'],'max_OD_error_PCE_per_h':r['max_OD_error_pce'],'max_reconstruction_error_PCE_per_h':r['max_link_reconstruction_pce'],'producer_status':r['status'],'current_S0_status':'Accepted' if r['method']=='Native80' else 'Original gap gate failed'})
    table(city,'chi-native-endpoints','C06_NATIVE_B_INCREMENT','Native representation endpoints',list(nr[0]),nr,'The three rows are distinct representation endpoints, not iterations. Native26/52 remain above the original 1e−5 gap gate. Native80 is the complete 80-dimensional minor representation and establishes no compression advantage.',['C06_NATIVE_B_INCREMENT.public_plot.json','C06_NATIVE_B_INCREMENT.caption.md'],'Frozen S20; hourly demand; public scalar endpoints only')
    h,old_sources=joined_admm_history();x=[r['iteration'] for r in h];names=['C06_ADMM_GAP_INCREMENT.public_plot.json','C06_ADMM_GAP_INCREMENT.caption.md'];chapter=text(city,'VOLUME_GAP_APPENDIX_S0.md');match=re.search(r'241\.2185242449435',chapter);assert match;ref=float(match.group());inst='CH_T4_30S_66.53295454563035PCE'
    f=figure(city,'ADMM: saved objective and external reference','T4 / original gates not met');ax=one_ax(f,.13);temporal(ax,x,[r['objective'] for r in h],'Raw x objective',S.INK);ax.axhline(ref,color=S.TEAL,ls='--',lw=1.2,label='Accepted CG reference');ax.set_xlabel('Completed outer iteration');ax.set_ylabel('Objective (PCE·min)');ax.legend(loc='lower right',fontsize=8)
    emit(f,city,'chi-admm-objective','C06_ADMM_GAP_INCREMENT',inst,'ADMM: saved objective and external reference','iteration','ADMM’s saved raw objective approaches an external accepted reference but its own feasibility gates still fail.',['Saved raw x objective and accepted CG reference'],'raw linear objective','PCE·min','All 33 saved outers are retained by joining public original outers 1–8 with increment outers 9–33 after exact numeric agreement of every common field at outer 9. The accepted CG reference 241.2185242449435 PCE·min is read from the approved city addendum and is an external evaluation only. The ADMM endpoint is not a feasible upper bound because capacity fails.',names+['VOLUME_GAP_APPENDIX_S0.md'],len(h),old_sources)
    f=figure(city,'ADMM: shared-capacity violation','T4 / original gates not met');ax=one_ax(f,.13);temporal(ax,x,[r['capacity_residual'] for r in h],color=S.INK);ax.set_yscale('symlog',linthresh=1e-7);ax.axhline(1e-5,color='#65757d',ls='--',lw=1,label='Original capacity gate');ax.set_xlabel('Completed outer iteration');ax.set_ylabel('Maximum capacity excess (PCE)');ax.legend(fontsize=8,loc='center left',bbox_to_anchor=(.01,.35))
    emit(f,city,'chi-admm-capacity','C06_ADMM_GAP_INCREMENT',inst,'ADMM: shared-capacity violation','iteration','The saved endpoint retains 1.491228076 PCE excess and fails its original capacity gate.',['Shared capacity excess'],'maximum capacity violation','PCE','All 33 saved outers are retained, with the repeated outer 9 verified before joining the two public sources. Capacity excess ends at 1.491228076 PCE, above the 1e−5 PCE gate. The symmetric-log axis keeps exact zero valid; no missing values were filled.',names,len(h),old_sources)
    f=figure(city,'ADMM: primal and dual stopping checks','T4 / original gates not met');ax=one_ax(f,.13);temporal(ax,x,[r['primal_over_gate'] for r in h],'Primal / own threshold',S.INK,log=True);temporal(ax,x,[r['dual_over_gate'] for r in h],'Dual / own threshold',S.TEAL,marker='s');ax.axhline(1,color='#65757d',ls='--',lw=1,label='Both ratios must be ≤1');ax.set_xlabel('Completed outer iteration');ax.set_ylabel('Residual / its original threshold');ax.legend(loc='upper right',fontsize=8)
    emit(f,city,'chi-admm-stopping','C06_ADMM_GAP_INCREMENT',inst,'ADMM: primal and dual stopping checks','iteration','Both original stopping ratios remain above 1 at the saved outer 33 endpoint.',['Primal and dual normalized by respective original thresholds'],'residual divided by its own stopping threshold','dimensionless','All 33 saved records retain each residual and its own threshold. Original outers 1–8 and increment 9–33 are joined after exact agreement at their repeated outer 9. At outer 33 the primal and dual ratios are 618.267 and 174.736. Rho remains in the original downloadable data; its separate history panel is omitted according to the selected figure contract.',['C06_ADMM_GAP_INCREMENT.public_plot.json','C06_ADMM_GAP_INCREMENT.caption.md'],len(h),old_sources)

def ann_arbor():
    city='ann-arbor';svg=text(city,'AA_GAP_STATIC.svg');nodes=ET.fromstring(svg);printed=[''.join(n.itertext()).strip() for n in nodes.iter() if n.tag.split('}')[-1]=='text'];assert '-1.15e-16' in printed and '1.03e-11' in printed
    rr=[{'cohort':'S600','method':m,'signed_full_graph_gap_printed':v,'current_S0_status':'Accepted','process_scope':'New saved S600 method'} for m,v in [('FW','-1.15e-16'),('Sparse fixed-path FW','-2.31e-16'),('Algorithm B','-2.31e-16')]]
    rr += [{'cohort':'S72','method':m,'signed_full_graph_gap_printed':'1.03e-11','current_S0_status':'Accepted','process_scope':'Initialization; 0 updates' if m.startswith('Native') else 'Separate frozen S72 endpoint'} for m in ['FW','Finite path','Native26','Native52']]
    table(city,'aa-static-endpoints','AA_GAP_STATIC','Static endpoints on separate S600 and S72 instances',list(rr[0]),rr,'The signed gaps retain only the rounded precision actually printed in the approved SVG; no private high-precision plot data is exported. The stated absolute gap gate is 1e−5. S600 and S72 are separate instances. Native600, new-choice FW and T1/T4 remain unsolved.',['AA_GAP_STATIC.svg','AA_GAP_STATIC.caption.md','AA_STATIC_GAP_ADDENDUM_S0.md'],'Two distinct frozen static cohorts; no invented trajectory')

def ithaca():
    city='ithaca';r=rows(city,'ITH_GC01_Employment.plot.csv');f=figure(city,'Employment allocation and spatial accounting limits','11 model zones / LODES 2020');ax=one_ax(f,.17);lo=[float(x['fully_contained_block_jobs']) for x in r];hi=[float(x['full_intersecting_block_jobs']) for x in r];v=[float(x['area_allocated_jobs_scenario']) for x in r];y=np.arange(len(r));ax.hlines(y,lo,hi,color='#b7cbd1',lw=4,zorder=1);ax.scatter(lo,y,color=S.INK,marker='|',s=45,label='Fully contained blocks',zorder=2);ax.scatter(hi,y,facecolors='white',edgecolors=S.INK,s=25,label='All intersecting blocks',zorder=2);ax.scatter(v,y,color=S.TEAL,s=25,label='Area-allocation scenario',zorder=3);ax.set_yticks(y,[x['zone_id'][-6:] for x in r]);ax.invert_yaxis();ax.set_ylabel('2020 tract suffix');ax.set_xlabel('Workplace jobs (JT00, C000)');ax.grid(False);ax.grid(axis='x',color=S.GRID,lw=.5);ax.legend(loc='lower right',fontsize=8)
    emit(f,city,'ith-employment-allocation','ITH_GC01_Employment','ITHACA_11ZONE_LODES2020','Employment allocation and spatial accounting limits','input_evidence','Employment totals retain explicit uncertainty from partially intersected census blocks.',['Per-zone contained/intersected accounting range and area estimate'],'workplace jobs','jobs','Grey spans run from fully contained to all intersecting blocks; they are spatial accounting limits, not confidence intervals. Totals are 7,493 contained, 8,752.529 area-allocated and 10,858 intersecting-block jobs. This supplement did not replace the frozen HBO activity attraction.',['ITH_GC01_Employment.plot.csv','ITH_GC01_Employment.caption.txt'])
    rr=rows(city,'ITH_GC02B_Observation_Counts.plot.csv')
    table(city,'ith-observation-bridge','ITH_GC02B_Observation_Counts','Source-link bridge diagnostics',list(rr[0]),rr,'The 60 R2 candidates remain geometric candidates; 21 other links are outside retained-SCC endpoints and 6 were excluded by access handling. The 27 links remain unbridged. No exact route is reconstructed or new legal-turn validation claimed.',['ITH_GC02B_Observation_Counts.plot.csv','ITH_GC02B_Observation_Counts.caption.txt'],'Diagnostic aggregate; 87 source links')
    rr=rows(city,'ITH_GC03_S_Endpoints.plot.csv');table(city,'ith-static-endpoints','ITH_GC03_S_Endpoints','S110 static endpoint comparison',list(rr[0]),rr,'Every numeric string from the released CSV is preserved. Static objectives have units PCE·min/h and original-coordinate flow errors PCE/h; historical machine field names are retained without rescaling. Negative roundoff gaps remain signed. These method rows are endpoints, not four iterations. FW saved 0 updates; Native26/52 each reached their original gates after 4 actual outer iterations.',['ITH_GC03_S_Endpoints.plot.csv','ITH_GC03_S_Endpoints.caption.txt','VOLUME_ADDENDUM_S0.md'],'S110;421.261325634 PCE/h;47,938 original solver arcs')
    rr=rows(city,'ITH_GC04_T_Endpoints.plot.csv')
    for row in rr:row['current_S0_status']='Accepted saved-state numeric' if row['method']=='admm' else 'Accepted'
    table(city,'ith-time-endpoints','ITH_GC04_T_Endpoints','T4 finite-time endpoint comparison',list(rr[0]),rr,'The original producer status remains in the status column; current S0 acceptance is separate. All CSV numeric strings are preserved. Contract normalization divides by max(1,|reference|)=1; true relative difference divides by 0.9184282689393537. Objective proximity alone is not feasibility. CG solved each phase once; LR and ADMM each retain one completed iteration. No short convergence curve is fabricated.',['ITH_GC04_T_Endpoints.plot.csv','ITH_GC04_T_Endpoints.caption.txt','VOLUME_ADDENDUM_S0.md'],'T4; 0.656755360434 PCE pulse;fixed cost PCE·min')
    r=rows(city,'ITH_GC05_Count_Coverage.plot.csv');f=figure(city,'Historical count-record coverage','NYSDOT / 2015–2019 snapshot',True);gs=f.add_gridspec(1,2,left=.09,right=.97,bottom=.19,top=.74,wspace=.35)
    for k,(field,col,title,ylab) in enumerate([('source_records',S.INK,'a  Source records','Records'),('distinct_RCSTA_in_year',S.TEAL,'b  Sites within each year','Distinct RCSTA codes')]):
        ax=f.add_subplot(gs[k]);S.format_axes(ax);x=[int(z['count_year']) for z in r];v=[int(z[field]) for z in r];ax.bar(x,v,color=col,width=.62);ax.set_xticks(x);ax.set_xlabel('Source measurement year');ax.set_ylabel(ylab);ax.set_title(title,loc='left');ax.set_ylim(0,max(v)*1.19);ax.set_axisbelow(True)
        for xx,vv in zip(x,v):ax.text(xx,vv+max(v)*.025,str(vv),ha='center',fontsize=8)
    emit(f,city,'ith-count-record-coverage','ITH_GC05_Count_Coverage','NYSDOT_SHORT_COUNTS_2015_2019','Historical count-record coverage','diagnostic','The acquired historical snapshot contains 294 records with uneven yearly coverage.',['Source records by year','Within-year unique RCSTA codes'],'source-record and site counts',['records','sites'],'The bounded acquisition contains 294 records and 76 unique RCSTA sites overall. Sites repeat across years; the annual site counts must not be added as distinct sites. Directional and combined count records are not summed vehicle volumes, and this is not a calibrated 2026 holdout.',['ITH_GC05_Count_Coverage.plot.csv','ITH_GC05_Count_Coverage.caption.txt'])
    rr=[{'measure':'Source year','value':'2022','unit':'year'},{'measure':'Matched worksheet records','value':'51','unit':'records'},{'measure':'Historical station codes','value':'17','unit':'RCSTA codes'},{'measure':'Rows with new source coordinates','value':'3','unit':'records'},{'measure':'Station-ID matches without new coordinates','value':'48','unit':'records'},{'measure':'Published plotted count range','value':'5–781','unit':'vehicles in average weekday 11:00–12:00'}]
    table(city,'ith-counts-2022-summary','ITH_GC06_Counts_2022','2022 count evidence and location limits',list(rr[0]),rr,'Summary values come from the approved caption and SVG. The original SVG preserves the 51 source-direction points. No private source-row CSV is reconstructed, and no count is converted to PCE. Combined and directional records must not be summed; 48 station-ID joins do not establish current recorder positions.',['ITH_GC06_Counts_2022.caption.txt','ITH_GC06_Counts_2022.svg'],'Diagnostic only; no calibration, simultaneous observation or fresh holdout')
    MAPPING['ITH_GC06_Counts_2022']['retained_public_svg']='docs/assets/gap-20261008/ithaca/ITH_GC06_Counts_2022.svg'

def main():
    global OUT
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-root',type=Path,required=True);a=ap.parse_args();OUT=a.output_root.resolve();OUT.mkdir(parents=True,exist_ok=True)
    if OUT==PUBLIC.resolve() or PUBLIC.resolve() in OUT.parents:raise ValueError('Do not overwrite released source assets.')
    urbana();pittsburgh();chicago();ann_arbor();ithaca()
    tables={'schema':'mcl_gap14_endpoint_tables_r11','tables':TABLES,'generator_public_path':'tools/figures/render_gap_progress.py','generator_sha256':sha(__file__),'solver_calls':0,'matcher_calls':0,'private_input_reads':0}
    (OUT/'endpoint_tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['# Released GAP evidence: endpoint and diagnostic tables','']
    for t in TABLES:
        md += ['## '+t['title'],'',t['scope'],'','| '+' | '.join(t['columns'])+' |','|'+'|'.join(['---']*len(t['columns']))+'|']
        for r in t['rows']:md.append('| '+' | '.join(str(r.get(k,'')).replace('|',' / ') for k in t['columns'])+' |')
        md += ['',t['caption'],'','Sources: '+', '.join('`'+s['public_path']+'` SHA256 `'+s['sha256']+'`' for s in t['sources']),'']
    (OUT/'endpoint_tables.md').write_text('\n'.join(md),encoding='utf-8')
    out={'schema':'mcl_gap14_display_derivatives_r11','source_release':'release_v002','source_files_unchanged':True,'generator_public_path':'tools/figures/render_gap_progress.py','generator_sha256':sha(__file__),'figures':FIGURES,'tables':'endpoint_tables.json','additional_public_derivatives':['chicago/chi-admm-history.plot.json'],'original_to_display':MAPPING,'solver_calls':0,'matcher_calls':0,'private_input_reads':0,'visual_qa':'PENDING_ACTUAL_VIEW_IMAGE'}
    (OUT/'manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(FIGURES),'tables':len(TABLES),'families':len(MAPPING),'output_root':str(OUT)}))
if __name__=='__main__':main()