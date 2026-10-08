"""Restore static scientific figures from already-public saved evidence.

No solver, interpolation, private data, or failed candidate is used. Existing
method-specific road maps remain canonical; endpoint figures supplement them.
"""
from pathlib import Path
import argparse,csv,json,sys
import numpy as np
from matplotlib.ticker import MaxNLocator,ScalarFormatter
from style import new_figure,format_axes,export_figure,TEAL,BLUE,INK,CATEGORIES,sha256
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'docs'
REG= D/'assets/figure-contract-r11/DISPLAY_REGISTRY.json'
R=json.loads(REG.read_text(encoding='utf-8'))
ITEMS=[]
OUT=None

def read(p):return json.loads((D/p).read_text(encoding='utf-8'))
def source(p):return {'public_path':'docs/'+p,'sha256':sha256(D/p)}
def table_sources(tid):
 return [{'public_path':s['public_path'],'sha256':s['sha256']} for s in R['tables'][tid]['sources']]
def rows(tid,block=0):return R['tables'][tid]['blocks'][block]['rows']
def originals(tid):return [old for old,ids in R['table_mapping'].items() if tid in ids]
def make(tid,title,scope,n=2,height=4.7):
 city=R['tables'][tid]['city'];f=new_figure(city,title,scope,figsize=(4.25*n,height))
 axes=f.subplots(1,n,squeeze=False)[0]
 f.subplots_adjust(left=.09,bottom=.22,right=.975,top=.73,wspace=.48)
 for a in axes:format_axes(a)
 return f,axes

def named(ax,title):ax.set_title(title,loc='left',fontsize=10,weight='bold',pad=8)
def numeric(ax):ax.ticklabel_format(axis='y',style='plain',useOffset=False)
def dots(ax,labels,vals,title,ylabel,baseline=False,symlog=False,annotate=False):
 x=np.arange(len(labels)); vals=np.asarray(vals,dtype=float)
 ax.scatter(x,vals,s=34,c=CATEGORIES[:len(x)],zorder=4,edgecolors='white',linewidth=.5)
 ax.set_xticks(x,labels);ax.tick_params(axis='x',labelsize=8)
 ax.set_xlim(-.45,len(x)-.55);ax.set_ylabel(ylabel);named(ax,title)
 if baseline:ax.axhline(0,color=INK,lw=.65,zorder=1)
 if symlog:ax.set_yscale('symlog',linthresh=1e-15)
 else:numeric(ax)
 if len(set(vals))==1:
  v=float(vals[0]);pad=max(abs(v)*.06,1e-15)
  ax.set_ylim(v-pad,v+pad)
 if annotate:
  for a,b in zip(x,vals):ax.annotate((f'{b:.9g}' if abs(b)>1 else f'{b:.3g}'),(a,b),xytext=(0,9),textcoords='offset points',ha='center',fontsize=7.6)
 ax.margins(y=.2)

def finish(tid,fig,title,stem,caption,panels,sources=None,data=None,meaning='Endpoint metrics supplement existing own-method physical-flow maps.'):
 city=R['tables'][tid]['city']; target=OUT/city/stem
 sources=sources or table_sources(tid)
 rec=export_figure(fig,target,{'figure_id':'R12-'+stem.upper(),'city':city,'instance':R['tables'][tid].get('scope','saved instance'),'role':'saved-state-check','conclusion':meaning,'panels':panels,'quantity':[p.get('metric','') for p in panels],'unit':[p.get('unit','') for p in panels],'renderer_path':'tools/figures/render_static_r12.py','renderer_sha256':sha256(__file__),'saved_states':(data or {}).get('saved_states',None),'preserves_true_zero':True,'interpolation':False,'failed_candidates_displayed':False},caption,sources)
 if data is not None:target.with_suffix('.plot.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 ITEMS.append({'table_id':tid,'city':city,'title':title,'staged_stem':str(target),'originals':originals(tid),'caption':caption,'sources':sources,'input_hashes':{s['public_path']:s['sha256'] for s in sources},'meaning':meaning,'dimensions':rec['dimensions'],'status':'RENDERED_PENDING_VISUAL_QA'})
 print('RENDERED',tid,flush=True)

def initial(tid,objective,gap,gate,scope,sourcefiles,extra=''):
 title='Frank–Wolfe: the saved initial check';fig,aa=make(tid,title,scope)
 ax=aa[0];named(ax,'a  Saved objective');ax.scatter([0],[objective],c=TEAL,s=42,zorder=4);ax.set(xlim=(-.5,.5),xticks=[0],xlabel='Saved iteration',ylabel='Beckmann objective (PCE·min/h)');pad=max(abs(objective)*.05,1);ax.set_ylim(objective-pad,objective+pad);numeric(ax);ax.annotate(f'{objective:.9g}',(0,objective),xytext=(0,12),textcoords='offset points',ha='center',fontsize=9)
 ax=aa[1];named(ax,'b  Relative-gap stopping check');ax.scatter([0],[gap],c=BLUE,s=42,zorder=4,label='Saved gap');ax.axhline(gate,color=INK,linestyle='--',lw=1,label=f'Gate = {gate:g}');ax.set(xlim=(-.5,.5),xticks=[0],xlabel='Saved iteration',ylabel='Relative gap (dimensionless)',ylim=(-.13*gate,1.30*gate));ax.annotate(f'{gap:.6g}',(0,gap),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9);ax.legend(loc='upper right',fontsize=7.7)
 caption=f'Only the actual saved iteration 0 is shown: objective {objective:.15g} PCE·min/h and relative gap {gap:.15g}, against the unchanged {gate:g} stopping gate. There were zero updates. Each panel contains a single numerical point; no missing trajectory or second state is inferred. The companion physical-flow map reads this method’s own saved vector. '+extra
 finish(tid,fig,title,tid,caption,[{'metric':'Beckmann objective','unit':'PCE·min/h'},{'metric':'relative gap','unit':'dimensionless'}],[source(p) for p in sourcefiles],{'iteration':[0],'objective':[objective],'relative_gap':[gap],'gate':gate,'saved_states':1},'One saved initial state is displayed truthfully as a point, not converted to a table.')

def initial_all():
 j=read('assets/city-alignment-r3/ann-arbor/aa-a02.plot_data.json');v=j['fw_trace'][0]
 initial('aa-original-initial-check',float(v['beckmann_objective']),float(v['relative_gap']),j['relative_gap_threshold'],'ORIGINAL S600 · 600 OD · 0 UPDATES',['assets/city-alignment-r3/ann-arbor/aa-a02.plot_data.json'],'This original 1e−4-gate instance is distinct from the later S600 1e−5-gate run, which saved iterations 0 and 1.')
 for city in ['urbana-champaign','ithaca','pittsburgh']:
  p=f'assets/city-alignment-r3/{city}/trace.source.json';j=read(p);a,b=j['panels']
  initial(city+'-initial-fw',a['values'][0],b['values'][0],b['threshold'],'ORIGINAL FOUR-STAGE INSTANCE · 0 UPDATES',[p],'This frozen original demand instance is not relabelled as a later selected-demand or transit-revision run.')
 tid='berkeley-fw-initial-check';v={x['Metric']:x['Saved value'] for x in rows(tid)}
 initial(tid,float(v['Objective']),float(v['Relative gap']),float(v['Relative-gap gate']),'S72 · 72 OD · 953.049842714 PCE/h',['assets/city-alignment-r3/berkeley/fw_saved_check.plot_data.json'],'The saved signed gap numerator is 2.7284841053187847e−12 PCE·min/h; the independent endpoint evaluator remains a separate numerical evaluation.')

def ann_endpoints():
 tid='aa-static-endpoints';rr=rows(tid);title='Static optimality on two separate demand instances';fig,aa=make(tid,title,'S600 AND S72 · INDEPENDENT ENDPOINTS',height=5.1)
 for i,scope in enumerate(['S600','S72']):
  r=[x for x in rr if x['Instance']==scope];labels=[x['Method'].replace('Sparse fixed-path FW','Finite-path\nFW').replace('Algorithm B','Algorithm\nB') for x in r];v=[float(x['Signed full-graph gap (printed)']) for x in r]
  dots(aa[i],labels,v,chr(97+i)+'  '+scope,'Signed full-graph relative gap',baseline=True,symlog=False,annotate=True)
  aa[i].set_ylim((-3e-16,1e-16) if scope=='S600' else (0,1.5e-11));aa[i].ticklabel_format(axis='y',style='sci',scilimits=(0,0),useOffset=False,useMathText=True);aa[i].yaxis.set_major_locator(MaxNLocator(4))
 caption='Accepted static endpoints are grouped by their own frozen demand instance. S600 has separate FW, sparse fixed-path FW and Algorithm B results; S72 has FW, finite-path and Native26/52 endpoints. Method categories are not iterations and are not joined. Signed near-zero gaps retain the exact precision printed in the approved SVG, including negative floating-point roundoff. The later S600 FW and finite-path FW have two saved rows (iterations 0 and 1); no unsupplied numerical intermediate is constructed. S72 Native methods accepted initialization with zero updates. Existing method-specific physical maps remain the spatial evidence.'
 finish(tid,fig,title,'aa-static-signed-gaps',caption,[{'metric':'S600 signed full-graph gap','unit':'dimensionless'},{'metric':'S72 signed full-graph gap','unit':'dimensionless'}],data={'endpoints':rr,'saved_states':'categorical endpoints, not iterations'})

def uc_native():
 tid='uc-native-od-gates';p='assets/algorithm-transfer-r8/urbana-champaign/UC_S02_C1.plot.json';j=read(p);title='Native L3: original-OD conservation';fig,aa=make(tid,title,'S72 · 72 ORIGINAL OD · 9 SAVED OUTER CHECKS',n=2,height=5.1)
 for ax,key,label,color,marker,letter in zip(aa,['rank26','rank52'],['Rank 26','Rank 52'],[TEAL,BLUE],['o','s'],['a','b']):
  x,y=np.array(j[key],float).T;ax.plot(x,y,color=color,marker=marker,ms=4,lw=1.25,label=label)
  ax.axhline(j['OD_abs_gate_pce'],color=INK,ls='--',lw=1,label='Original OD gate');ax.set(yscale='log',ylim=(1e-8,2),xlabel='Saved outer iteration',ylabel='Maximum original-OD residual (PCE/h)',xticks=[1,3,5,7,9]);ax.legend(fontsize=8,loc='lower left');named(ax,letter+'  '+label)
 caption='All nine actual saved outer checks are retained for the accepted S72 Native26 and Native52 runs, using the original 72-OD conservation metric. The frozen gate is 1e−6 PCE/h; both runs first meet it at outer 9. Lines join actual saved iterations only, without smoothing or invented points. Earlier high residuals belong to these ultimately accepted trajectories. The two panels use identical ordinate limits. Rank 26 uses 98 path coordinates and rank 52 uses 124; each retains 26,602 explicit-link variables. These dimension counts are distinct from iteration counts.'
 finish(tid,fig,title,'uc-native-od-conservation',caption,[{'metric':'maximum original-OD residual','unit':'PCE/h'}],[source(p),source('assets/city-alignment-r3/urbana-transfer/original-method-figures/UC_S04.plot.json')],{**j,'saved_states':9},'The complete accepted method history uses the same conservation objective as the reference-city diagnostic.')

def endpoint_pair(tid,scope,labels,objectives,gaps,sources,caption):
 title='Static objective and optimality checks';fig,aa=make(tid,title,scope,height=5.0)
 dots(aa[0],labels,objectives,'a  Saved method objectives','Beckmann objective (PCE·min/h)',annotate=True)
 dots(aa[1],labels,gaps,'b  Full-graph relative gap','Signed relative gap',baseline=True,symlog=True,annotate=True)
 finish(tid,fig,title,tid,caption,[{'metric':'Beckmann objective','unit':'PCE·min/h'},{'metric':'full-graph relative gap','unit':'dimensionless'}],sources,{'method':labels,'objective':objectives,'signed_gap':gaps,'saved_states':'categorical endpoints'})

def pairs():
 tid='uc-s72-method-endpoints';p='assets/city-alignment-r3/urbana-transfer/static-comparison.plot_data.json';j=read(p)
 endpoint_pair(tid,'S72 · 72 OD · 321.629659883 PCE/h',j['methods'],j['Beckmann_pce_min'],j['full_graph_relative_gap'],[source(p)],'FW and finite-path K=5 each retain their own independent saved S72 endpoint. The identical Beckmann values are shown as two distinct method-category points, with signed full-graph gaps on a separate axis. Method categories are not iterations. The existing FW and finite-path physical-flow maps and all-link histograms remain the primary spatial evidence; these scalar checks are supplementary. The 418-OD full-city and revised-transit demands are separate instances.')
 tid='pittsburgh-s72-endpoints';r=rows(tid)
 endpoint_pair(tid,'S72 · 72 OD · 149.921423895 PCE/h',[x['Method'] for x in r],[x['Objective checked (PCE·min/h)'] for x in r],[x['Full relative gap'] for x in r],table_sources(tid),'Independent FW and finite-path endpoints on the same selected Pittsburgh S72 demand. Both checked objectives equal 763.227941458126 PCE·min/h and both saved OD and reconstruction residuals are zero. Categorical points are never connected as an iteration history. The companion method-specific maps and distributions retain all 56,384 physical links and their own saved vectors.')

def endpoints_diagnostic(tid,scope,labels,obj,gap,od,recon):
 title='Accepted static endpoints and feasibility';fig,aa=make(tid,title,scope,n=3,height=5.0)
 delta=np.asarray(obj)-obj[0];dots(aa[0],labels,delta,'a  Objective difference from FW','Objective − FW (PCE·min/h)',baseline=True,symlog=True)
 dots(aa[1],labels,gap,'b  Signed full-graph gap','Relative gap (dimensionless)',baseline=True,symlog=True)
 ax=aa[2];x=np.arange(len(labels));ax.scatter(x-.06,od,color=TEAL,s=30,label='OD conservation',zorder=4);ax.scatter(x+.06,recon,color=BLUE,marker='s',s=25,label='Link reconstruction',zorder=4);ax.set_xticks(x,labels);ax.set(xlim=(-.5,len(x)-.5),ylabel='Maximum absolute residual (PCE/h)',yscale='symlog');ax.set_yscale('symlog',linthresh=1e-15);ax.axhline(0,color=INK,lw=.65);named(ax,'c  Original-coordinate feasibility');ax.legend(fontsize=7.5,loc='upper left');ax.set_ylim(-4e-16,max([*od,*recon])*150)
 caption=f'Independent accepted endpoints on {scope}. Panels show signed objective difference from the same-instance FW endpoint ({obj[0]:.15g} PCE·min/h), signed full-graph relative gap, and maximum original-OD and link-reconstruction residuals. Categories are method identities, not iteration numbers; no connecting trajectory is drawn. The signed symmetric-log axes retain exact zeros and negative roundoff, with a linear interval of ±1e−15 in each panel’s stated unit. The accompanying method-specific physical-flow figures remain the map evidence; scalar agreement does not imply identical flow.'
 finish(tid,fig,title,tid,caption,[{'metric':'signed objective difference from FW','unit':'PCE·min/h'},{'metric':'signed full-graph relative gap','unit':'dimensionless'},{'metric':'original-OD and reconstruction residuals','unit':'PCE/h'}],data={'methods':labels,'objective':obj,'signed_objective_difference_from_FW':delta.tolist(),'signed_relative_gap':gap,'max_original_OD_residual':od,'max_reconstruction_residual':recon,'saved_states':'categorical endpoints'})

def diagnostic_all():
 tid='berkeley-s72-endpoints';r=rows(tid)
 endpoints_diagnostic(tid,'S72 · 72 OD · 953.049842714 PCE/h',['FW','Finite','Native\n26','Native\n52'],[x['Objective (PCE·min/h)'] for x in r],[x['Relative gap'] for x in r],[x['Max OD error (PCE/h)'] for x in r],[x['Max reconstruction (PCE/h)'] for x in r])
 tid='ith-static-endpoints';r=rows(tid)
 endpoints_diagnostic(tid,'S110 · 110 OD · 421.261325634 PCE/h',['FW','Finite','Native\n26','Native\n52'],[float(x['Objective (PCE·min/h)']) for x in r],[float(x['Signed full relative gap']) for x in r],[float(x['Max OD error (PCE/h)']) for x in r],[float(x['Max reconstruction error (PCE/h)']) for x in r])

def chicago_native():
 tid='chi-native-endpoints';p='assets/gap-20261008/chicago/C06_NATIVE_B_INCREMENT.public_plot.json';j=read(p);r=next(x for x in j['Native_new_controls'] if x['method']=='Native80');assert all(r['checks'].values())
 title='Native80: accepted original-coordinate endpoint';fig,aa=make(tid,title,'S20 · 20 MAJOR + 80 MINOR PATH COORDINATES',n=3,height=4.8)
 metrics=[('a  Full-graph relative gap','Relative gap (dimensionless)',r['full_graph_gap']),('b  Original-OD conservation','Maximum residual (PCE/h)',r['max_OD_error_pce']),('c  Link reconstruction','Maximum residual (PCE/h)',r['max_link_reconstruction_pce'])]
 for ax,(title0,label,val) in zip(aa,metrics):
  dots(ax,['Native80'],[val],title0,label,annotate=True);ax.set_ylim(0,val*1.55);ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0),useOffset=False,useMathText=True);ax.yaxis.set_major_locator(MaxNLocator(4))
 caption='The accepted Native80 endpoint uses the full uncompressed 80-dimensional minor representation (U=I80), with 20 major paths; no compression advantage is claimed. Its checked objective is 5601.461468294976 PCE·min/h. The three panels show the actual full-graph gap, original-OD residual and link-reconstruction residual with their own units. Each is a single method endpoint, not an iteration trajectory. Public accepted data do not include this method’s complete physical-flow vector, so no flow map is inferred from FW or another representation.'
 finish(tid,fig,title,'chicago-native80-endpoint',caption,[{'metric':x[0][3:],'unit':x[1]} for x in metrics],[source(p)],{'accepted_endpoint':r,'saved_states':1},'Accepted Native80 scalar results remain visible without failed representation plots or borrowed physical flow.')

def main():
 global OUT
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();OUT=args.output
 initial_all();ann_endpoints();uc_native();pairs();diagnostic_all();chicago_native()
 omitted=[{'table_id':'berkeley-s72-pool','action':'merge_into_existing_flow_caption','reason':'Existing S72 FW map and all-link histogram already show the same own vector. Retain 72 OD, 360 paths, 72 major / 288 minor paths and 1480 zero links in caption; no duplicate chart.'},{'table_id':'uc-s72-dimensions','action':'merge_into_native_caption','reason':'Structural dimension counts do not need a second chart. Preserve 98/124 path coordinates plus 26602 explicit-link variables in Native caption; these are not iteration counts.'},{'table_id':'chicago-s20-dimensions','action':'remove_from_page','reason':'This old dimensions card describes failed Native26/52 representations. Native80 accepted representation is disclosed on its own plot.'}]
 result={'schema':'mcl-static-figures-r12','items':ITEMS,'dispositions':omitted,'existing_physical_maps_reused':True,'failed_attempts_on_plots':False,'solver_calls':0,'status':'RENDERED_PENDING_VISUAL_QA'}
 (OUT.parent.parent/'STATIC_RENDER_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
