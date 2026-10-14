"""Selected CG Phase I composition, from saved records only (no solver)."""
from pathlib import Path
import csv, json, hashlib, sys, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from PIL import Image
R=Path(__file__).resolve().parents[2]; D=R/'docs'; A=D/'assets/shared-cg-20261013'; O=A/'selected-three'
sys.path.insert(0,str(Path(__file__).parent/'berkeley_alignment_r2'))
from atlas_style import new_figure,format_axes,compact_header,TEAL,FLOW_CMAP,INK
from embed_serif_fonts import embed_serif_fonts
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def draw(case,evidence,city,scope,x,total,labels,matrix,unit,inputs):
 x=np.asarray(x);total=np.asarray(total,dtype=float);n=len(labels)
 assert len(x)==len(total) and len(set(x))==len(x) and np.all(np.diff(x)>0)
 if matrix is not None:
  matrix=np.asarray(matrix,dtype=float);assert matrix.shape==(len(x),n)
  assert np.all(matrix>=-1e-7) and np.allclose(matrix.sum(axis=1),total,rtol=1e-9,atol=1e-6)
 fig=new_figure(city,'Phase I: artificial flow',scope,figsize=(9,5.4))
 ax=fig.add_axes([.10,.22,.31,.49]);format_axes(ax)
 ax.set_title('a  Total artificial flow',loc='left',weight='bold',fontsize=10)
 ax.step(x,total,where='post',color=TEAL,lw=1.5);ax.scatter(x,total,s=12,color=TEAL,zorder=3)
 ax.set(xlabel='Saved Phase I round',ylabel='Artificial flow ('+unit+')',xlim=(x[0]-.25,x[-1]+.25))
 ax.xaxis.set_major_locator(MaxNLocator(5,integer=True));ax.ticklabel_format(axis='y',style='plain',useOffset=False)
 ax=fig.add_axes([.56,.22,.34,.49]);format_axes(ax);ax.set_title('b  Per-OD heatmap',loc='left',weight='bold',fontsize=10)
 transform='none'
 if matrix is None:
  ax.axis('off');ax.text(.5,.62,'Per-OD history not saved',ha='center',va='center',fontsize=10,color=INK,transform=ax.transAxes)
  ax.text(.5,.39,'Aggregate totals cannot recover\nthe OD-by-round matrix.\nNo other run is substituted.',ha='center',va='center',fontsize=8.5,linespacing=1.6,transform=ax.transAxes)
 else:
  # Cells represent actual saved rounds; no interpolation between OD records.
  edges=np.r_[x[0]-.5,(x[:-1]+x[1:])/2,x[-1]+.5]
  heat=matrix.T
  if n>10:heat=np.log10(1+heat);transform='log10(1 + flow)'
  im=ax.pcolormesh(edges,np.arange(n+1)-.5,heat,cmap=FLOW_CMAP,vmin=0,vmax=4 if n>10 else float(matrix.max()),shading='flat',rasterized=False)
  ax.set_ylim(n-.5,-.5);ax.set(xlabel='Saved Phase I round',ylabel='OD identifier');ax.grid(False)
  ticks=np.arange(n) if n<=10 else np.unique(np.r_[0,np.arange(49,n,50),n-1])
  ax.set_yticks(ticks,[labels[i] for i in ticks]);ax.tick_params(axis='y',labelsize=7.5)
  ax.xaxis.set_major_locator(MaxNLocator(5,integer=True))
  cax=fig.add_axes([.925,.22,.015,.49]);cb=fig.colorbar(im,cax=cax);cb.ax.tick_params(labelsize=7)
  cb.set_label('log₁₀(1 + flow)' if n>10 else 'Artificial flow ('+unit+')',fontsize=8)
 fig.text(.10,.075,f'{len(x)} saved states · rounds {x[0]}–{x[-1]} · total {total[0]:.7g} → {total[-1]:.7g}',fontsize=8.5)
 caption=f'{case} / {evidence}: total artificial flow on the left; '+('each OD from the same saved run on the right. ' if matrix is not None else 'the missing per-OD history is explicitly identified on the right. ')+f'All {len(x)} saved Phase I states (rounds {x[0]}–{x[-1]}); {total[0]:.15g} → {total[-1]:.15g} {unit}. '+('Heatmap colour is log10(1 + flow), with the same 0–4 scale for Sioux 200/250; saved numeric values remain untransformed. ' if n>10 and matrix is not None else '')+'No smoothing, interpolation, new solve or cross-version substitution.'
 out=O/case/evidence;out.mkdir(parents=True,exist_ok=True);stem='phase-i-combined';compact_header(fig)
 for ext in ['png','svg']:fig.savefig(out/(stem+'.'+ext),dpi=300,bbox_inches='tight',pad_inches=.055,metadata={'Date':None} if ext=='svg' else None)
 embed_serif_fonts(out/(stem+'.svg'));plt.close(fig)
 dp=out/(stem+'.plot.json');dp.write_text(json.dumps({'case_id':case,'evidence_id':evidence,'round':x.tolist(),'total_artificial_flow':total.tolist(),'unit':unit,'od_labels':labels,'per_od_artificial_flow':None if matrix is None else matrix.tolist(),'per_od_status':'NOT_SAVED' if matrix is None else 'SAVED_SAME_RUN','heatmap_transform':transform,'panel_order':['total_artificial_flow','per_od_heatmap'],'composition':'left_right'},indent=2)+'\n',encoding='utf8')
 sp=out/(stem+'.source.json');sp.write_text(json.dumps({'case_id':case,'evidence_id':evidence,'renderer':Path(__file__).relative_to(R).as_posix(),'renderer_sha256':sha(Path(__file__)),'inputs':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)} for p in inputs],'data':dp.name,'data_sha256':sha(dp),'exports':{e:sha(out/(stem+'.'+e)) for e in ['png','svg']},'caption':caption,'new_solver_run':False,'source_and_reuse_notice':'../../../NOTICE.txt'},indent=2)+'\n',encoding='utf8')
 (out/(stem+'.caption.txt')).write_text(caption+'\n',encoding='utf8')
 with Image.open(out/(stem+'.png')) as im:w,h=im.size
 return {'id':f'cg-{case}-{evidence}-phase-i-combined','title':'Phase I: total artificial flow + per-OD heatmap','src':(out/(stem+'.svg')).relative_to(D).as_posix(),'png':(out/(stem+'.png')).relative_to(D).as_posix(),'data':dp.relative_to(D).as_posix(),'source':sp.relative_to(D).as_posix(),'caption':caption,'width':w,'height':h}
def main():
 result={};p=D/'assets/boston/space_time_cg_r4/data/phase_i_total.csv';q=p.with_name('phase_i_by_demand.csv');rr=rows(p);per=rows(q)
 x=[int(r['round']) for r in rr];labels=sorted({r['demand_id'] for r in per});lookup={(int(r['round']),r['demand_id']):float(r['artificial_flow']) for r in per}
 assert len(lookup)==len(x)*len(labels)
 key='boston_reference_764e086/original';result[key]=draw(*key.split('/'),'Boston','Original accepted CG / 10 OD',x,[float(r['artificial_flow']) for r in rr],labels,[[lookup[(i,k)] for k in labels] for i in x],'vehicles',[p,q])
 p=D/'assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_i_artificial_flow_trace.csv';rr=rows(p);cols=sorted(k for k in rr[0] if re.fullmatch(r'HK\d+_artificial_flow',k))
 key='hong_kong_reference_764e086/original';result[key]=draw(*key.split('/'),'Hong Kong','Original accepted CG / 10 OD',[int(r['round']) for r in rr],[float(r['total_artificial_flow']) for r in rr],[k.split('_')[0] for k in cols],[[float(r[k]) for k in cols] for r in rr],'PCE',[p])
 for n in [200,250]:
  p=D/f'assets/sioux/phase_i_r1/data/{n}_phase_i_trace.csv';rr=rows(p);cols=sorted([k for k in rr[0] if re.fullmatch(r'XS\d+_artificial_flow',k)],key=lambda k:int(re.search(r'\d+',k)[0]));assert len(cols)==n
  key=f'sioux_{n}_original/original';result[key]=draw(*key.split('/'),'Sioux Falls',f'Historical original CG / {n} OD',[int(r['round']) for r in rr],[float(r['total_artificial_flow']) for r in rr],[k.split('_')[0] for k in cols],[[float(r[k]) for k in cols] for r in rr],'original flow units',[p])
 p=A/'catalog.json'
 for c in read(p)['cases']:
  if c['city'] not in ['boston','hong-kong','sioux-falls']:continue
  for e in c['evidence']:
   rr=[r for r in e['history'] if r['phase']=='I'];assert rr
   key=c['case_id']+'/'+e['evidence_id'];unit='original volume' if c['city']=='sioux-falls' else 'vehicles' if c['city']=='hong-kong' else 'PCE'
   result[key]=draw(*key.split('/'),c['city_name'],f"{c['OD']} OD / {e['evidence_id']}",[r['round'] for r in rr],[r['artificial_mass'] for r in rr],[],None,unit,[p])
 (O/'figures.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(f'Rendered {len(result)} Phase I composites; saved records only')
if __name__=='__main__':main()
