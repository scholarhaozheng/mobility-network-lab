"""Phase II objective and signed reference gap, using saved results only."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator,FuncFormatter
from PIL import Image
R=Path(__file__).resolve().parents[2];D=R/'docs';A=D/'assets/shared-cg-20261013';O=A/'selected-three-phase-ii'
sys.path.insert(0,str(Path(__file__).parent/'berkeley_alignment_r2'))
from atlas_style import new_figure,format_axes,compact_header,TEAL,BLUE,INK
from embed_serif_fonts import embed_serif_fonts
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render(case,evidence,city,scope,x,y,reference,reference_kind,unit,inputs):
 x=np.array(x,dtype=int);y=np.array(y,dtype=float);assert len(x)==len(y)>0 and np.all(np.diff(x)>0)
 assert np.isfinite(reference) and reference!=0 and np.all(np.isfinite(y))
 difference=y-reference;relative=100*difference/abs(reference);linear_band=1e-10
 ref_label='Same-graph arc-flow LP' if reference_kind=='independent_arc_lp' else 'Verified full-graph lower bound'
 fig=new_figure(city,'Phase II: objective and reference gap',scope,figsize=(9,5.4))
 left=fig.add_axes([.11,.23,.32,.48]);right=fig.add_axes([.60,.23,.33,.48])
 for ax in [left,right]:
  format_axes(ax);ax.set_xlabel('Saved Phase II round');ax.set_xlim(x[0]-.25,x[-1]+.25);ax.xaxis.set_major_locator(MaxNLocator(5,integer=True))
  if len(x)<=3:ax.set_xticks(x)
 left.set_title('a  Objective trajectory',loc='left',weight='bold',fontsize=10)
 if len(x)>1:left.step(x,y,where='post',lw=1.5,color=TEAL)
 left.scatter(x[:1],y[:1],facecolors='white',edgecolors=TEAL,s=26,zorder=4)
 left.scatter(x[1:],y[1:],color=TEAL,s=19,zorder=4)
 left.axhline(reference,color=BLUE,ls='--',lw=1,label=ref_label)
 left.set_ylabel('Objective ('+unit+')');left.ticklabel_format(axis='y',style='plain',useOffset=False)
 # Do not magnify floating-point noise into a visually substantial descent.
 span=max(float(np.ptp(np.r_[y,reference])),abs(reference)*1e-6)
 left.set_ylim(min(y.min(),reference)-span*.10,max(y.max(),reference)+span*.27)
 left.yaxis.set_major_locator(MaxNLocator(5));left.legend(loc='upper right',fontsize=7.5)
 right.set_title('b  Relative gap to reference',loc='left',weight='bold',fontsize=10)
 right.axhspan(-linear_band,linear_band,color='#eef4f5',zorder=0)
 right.axhline(0,color='#83949c',lw=.7,zorder=1)
 if len(x)>1:right.step(x,relative,where='post',lw=1.5,color=BLUE)
 right.scatter(x[:1],relative[:1],facecolors='white',edgecolors=BLUE,s=26,zorder=4)
 right.scatter(x[1:],relative[1:],color=BLUE,s=19,zorder=4)
 right.set_yscale('symlog',linthresh=linear_band,linscale=1)
 right.set_ylabel('100 (J − Jref) / |Jref| (%)')
 maximum=max(float(np.abs(relative).max()),linear_band)
 if maximum<=linear_band:
  right.set_ylim(-1.4*linear_band,1.4*linear_band);right.set_yticks([-linear_band,0,linear_band])
 else:
  ceiling=int(np.ceil(np.log10(maximum)));ticks=sorted(set([0,10.**int(np.floor(np.log10(maximum)))]+[10.**e for e in range(-10,ceiling+1,3)]))
  if relative.min() < -linear_band:ticks=[-v for v in reversed(ticks[1:])]+ticks
  right.set_yticks(ticks);right.set_ylim(min(float(relative.min())*2,-linear_band*1.3),max(float(relative.max())*2,linear_band*1.3))
 right.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:'0' if v==0 else f'{v:g}'))
 right.text(.98,.96,f'Final: {relative[-1]:.3g}%',ha='right',va='top',transform=right.transAxes,fontsize=8)
 states=f'{len(x)} saved states · {len(x)-1} recorded transitions' if len(x)>1 else 'One saved state · no within-phase trajectory'
 fig.text(.11,.105,states,fontsize=8)
 fig.text(.11,.045,'Right: signed symlog · linear within ±1e−10% (display band, not a stopping gate).',fontsize=8)
 cap=f'{case} / {evidence}. Left: all {len(x)} saved Phase II objective states, rounds {x[0]}–{x[-1]}, {y[0]:.16g} → {y[-1]:.16g} {unit}. Right: signed 100 × (J − Jref) / |Jref|, using the fixed {ref_label.lower()} Jref={reference:.16g} from this same instance and result version. Final signed difference={difference[-1]:.16g} {unit}; relative difference={relative[-1]:.16g}%. The reference is fixed across rounds, not a time-varying lower-bound history. The symlog linear band ±1e-10 percentage points is for display and is not an acceptance threshold. True zero and negative rounding residuals are retained. '+('Only one Phase II state was saved; no transition or line is invented. ' if len(x)==1 else '')+'Objective agreement is not independent pricing closure. No solver run, interpolation, smoothing or cross-instance substitution.'
 out=O/case/evidence;out.mkdir(parents=True,exist_ok=True);stem='phase-ii-pair';compact_header(fig)
 for ext in ['png','svg']:fig.savefig(out/(stem+'.'+ext),dpi=300,bbox_inches='tight',pad_inches=.055,metadata={'Date':None} if ext=='svg' else None)
 embed_serif_fonts(out/(stem+'.svg'));plt.close(fig)
 data={'case_id':case,'evidence_id':evidence,'round':x.tolist(),'objective':y.tolist(),'unit':unit,'fixed_reference':reference,'reference_kind':reference_kind,'reference_label':ref_label,'signed_difference':difference.tolist(),'signed_relative_percent':relative.tolist(),'relative_formula':'100 * (objective - fixed_reference) / abs(fixed_reference)','display_scale':'symlog','display_linear_band_percent':linear_band,'panel_order':['objective','signed_relative_gap_to_fixed_reference'],'composition':'left_right','saved_states':len(x),'recorded_transitions':len(x)-1}
 dp=out/(stem+'.plot.json');dp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8');sp=out/(stem+'.source.json')
 sp.write_text(json.dumps({'case_id':case,'evidence_id':evidence,'renderer':Path(__file__).relative_to(R).as_posix(),'renderer_sha256':sha(Path(__file__)),'inputs':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)} for p in inputs],'data':dp.name,'data_sha256':sha(dp),'exports':{ext:sha(out/(stem+'.'+ext)) for ext in ['png','svg']},'caption':cap,'new_solver_run':False,'source_and_reuse_notice':'../../../NOTICE.txt'},indent=2)+'\n',encoding='utf8')
 (out/(stem+'.caption.txt')).write_text(cap+'\n',encoding='utf8')
 with Image.open(out/(stem+'.png')) as im:w,h=im.size
 return {'id':f'cg-{case}-{evidence}-phase-ii-pair','title':'Phase II objective: trajectory + reference gap','src':(out/(stem+'.svg')).relative_to(D).as_posix(),'png':(out/(stem+'.png')).relative_to(D).as_posix(),'data':dp.relative_to(D).as_posix(),'source':sp.relative_to(D).as_posix(),'caption':cap,'width':w,'height':h}
def main():
 figures={};p=D/'assets/boston/space_time_cg_r4/data/phase_ii_objective.csv';q=p.with_name('validation_summary.json');rr=rows(p)
 key='boston_reference_764e086/original';figures[key]=render(*key.split('/'),'Boston','Original accepted CG / 10 OD',[int(r['round']) for r in rr],[float(r['objective']) for r in rr],read(q)['identical_graph_arc_lp_reference_objective'],'independent_arc_lp','vehicle-min',[p,q])
 p=D/'assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_ii_objective_trace.csv';rr=rows(p)
 key='hong_kong_reference_764e086/original';figures[key]=render(*key.split('/'),'Hong Kong','Original accepted CG / 10 OD',[int(r['round']) for r in rr],[float(r['objective_value']) for r in rr],float(rr[0]['arc_lp_reference_objective']),'independent_arc_lp','vehicle-min',[p])
 for n in [200,250]:
  p=D/f'assets/sioux/phase_i_r1/data/{n}_phase_ii_trace.csv';rr=rows(p);key=f'sioux_{n}_original/original'
  figures[key]=render(*key.split('/'),'Sioux Falls',f'Historical original CG / {n} OD',[int(r['round']) for r in rr],[float(r['objective_value']) for r in rr],float(rr[0]['arc_lp_reference_objective']),'independent_arc_lp','native cost × original volume',[p])
 for c in read(A/'catalog.json')['cases']:
  if c['city'] not in ['boston','hong-kong','sioux-falls']:continue
  for e in c['evidence']:
   p=A/c['case_id']/e['evidence_id']/'plot-data.json';q=p.with_name('lower-certificate.json');u=p.with_name('upper-certificate.json');d=read(p);cert=read(q);upper=read(u)
   assert cert['status']=='PASS_FULL_GRAPH' and cert['verified_full_graph_lower_bound']==d['L']==e['L']
   assert cert['source_hashes']==upper['source_hashes'] and cert['original_demands']==c['OD']
   assert e['upper_build']==e['lower_build']
   rr=[r for r in d['history'] if r['phase']=='II'];key=c['case_id']+'/'+e['evidence_id']
   unit='native cost × original volume' if c['city']=='sioux-falls' else 'vehicle-min' if c['city']=='hong-kong' else 'PCE-min'
   figures[key]=render(*key.split('/'),c['city_name'],f"{c['OD']} OD / {e['evidence_id']}",[r['round'] for r in rr],[r['true_primal_objective'] for r in rr],d['L'],'verified_full_graph_lower_bound',unit,[p,q,u])
 (O/'figures.json').write_text(json.dumps(figures,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(f'Rendered {len(figures)} Phase II pairs from saved results; no solver')
if __name__=='__main__':main()
