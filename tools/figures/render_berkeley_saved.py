"""Regenerate Berkeley presentation from already-public saved plot inputs only.
No optimizer, matcher, experiment entry point, or private input is imported.
Run: python tools/figures/render_berkeley_saved.py --output PATH
"""
from pathlib import Path
import sys, json, csv, argparse, types, importlib.util, hashlib, inspect
import numpy as np
from matplotlib import pyplot as plt
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import style as st
REPO=HERE.parents[1]; DOCS=REPO/'docs'; RECIPES=HERE/'recipes'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def pin(p):return {'public_path':Path(p).relative_to(REPO).as_posix(),'sha256':st.sha256(p)}
def load(name):
 spec=importlib.util.spec_from_file_location(name,RECIPES/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 result=[]
 def emit(fig,stem,title,caption,panels,inputs,original,instance='Berkeley frozen bounded T4',role='spatial',saved_states=0):
  for text in list(fig.texts):
   if text not in getattr(fig,'_mcl_header_artists',[]):text.remove()
  sources=[pin(p) for p in inputs]+[pin(RECIPES/p) for p in ['render_admm.py','render_finite.py','render_flow_maps.py','render_lr_diagnostics.py','render_lr_flow.py']]
  rec=st.export_figure(fig,out/stem,dict(figure_id='R11-BERKELEY-'+stem.upper(),city='berkeley',instance=instance,role=role,saved_states=saved_states,conclusion=title,panels=panels,quantity='As separately labelled by panel',unit='As separately labelled by panel',original_asset=original),caption,sources)
  result.append({'original':original,'stem':str(out/stem),'figure_id':rec['figure_id'],'caption':caption,'title':title,'status':rec['status']})
  return {**rec,'id':stem}
 # Minimal adapter exposing only the public saved-data directory.
 pc=types.ModuleType('plot_common');pc.__dict__.update({k:getattr(st,k) for k in ['new_figure','format_axes','compact_header','INK','TEAL','BLUE','ROAD','GRID','FLOW_CMAP','DIFF_CMAP']})
 pc.HERE=out;pc.INPUTS=DOCS/'assets/berkeley-atlas-r2/data';pc.OUT=out;pc.sha=st.sha256;pc.read_json=lambda n:read(pc.INPUTS/n);pc.read_csv=lambda n:rows(pc.INPUTS/n)
 def save(fig,stem,title,stage,caption,panels,sources,plot_data=None):
  if stem=='lp_cg_lr_physical_flow':plt.close(fig);return {'id':stem}
  role='iteration' if stem=='admm_convergence' else 'spatial'
  return emit(fig,stem,title,caption,panels,[pc.INPUTS/s for s in sources],'assets/berkeley-atlas-r2/'+stem+'.svg',role=role,saved_states=170 if role=='iteration' else 0)
 pc.save=save;sys.modules['plot_common']=pc
 load('render_admm').convergence();load('render_finite').t01_computed_column();load('render_flow_maps')
 rd=load('render_lr_diagnostics');data_path=DOCS/'assets/berkeley-lr-r6/lr_bounds.plot_data.json';data=read(data_path)
 def lr_emit(fig,stem,title,caption,panels,data,output_dir,**kwargs):
  inp=[data_path]
  if stem=='lp_cg_lr_physical_flow':inp += [DOCS/'assets/berkeley-lr-r6/lp_cg_lr_physical_flow.plot_data.json',pc.INPUTS/'physical_geometry.csv']
  return emit(fig,stem,title,caption,panels,inp,'assets/berkeley-lr-r6/'+stem+'.svg',instance='Berkeley T4 cold-start diagnostic 300; original accepted 10 retained separately',role='iteration' if stem!='lp_cg_lr_physical_flow' else 'spatial',saved_states=300)
 rd.emit=lr_emit;rd._footer=lambda *a:None
 for f in [rd.lr_bounds,rd.lr_prices,rd.lr_recovery]:f(data,out)
 # Build a temporary join table entirely from public physical plot data.
 flowdata=read(DOCS/'assets/berkeley-lr-r6/lp_cg_lr_physical_flow.plot_data.json');base=read(DOCS/'assets/berkeley-atlas-r2/admm_physical_flow_comparison.plot_data.json')
 flowdata=flowdata['figure_data'];ids=flowdata['link_id'];assert ids==base['link_id'];tmp=out/'lr_public_join.csv'
 with tmp.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['link_id','LP_flow_pce','CG_flow_pce','LR_flow_pce','ADMM_flow_pce','has_movement']);w.writeheader()
  for i,id in enumerate(ids):w.writerow(dict(link_id=id,LP_flow_pce=flowdata['LP_flow_pce'][i],CG_flow_pce=flowdata['CG_flow_pce'][i],LR_flow_pce=flowdata['LR_flow_pce'][i],ADMM_flow_pce=base['ADMM_flow_pce'][i],has_movement=int(flowdata['has_movement'][i])))
 load('render_lr_flow').render(data,tmp,pc.INPUTS/'physical_geometry.csv',out)
 # Three complete demand-stage displays; retain all 13 zones and original bins.
 root=DOCS/'assets/six-city-r3-1/berkeley';p=root/'plot_data/f10_generation/f10_generation.plot_data.csv';r=rows(p);x=np.arange(len(r));assert len(r)==13
 fig=st.new_figure('berkeley','Trip generation','13 zones / 08:00–09:00',figsize=(10,4.6));ax=fig.add_axes([.085,.22,.87,.55]);st.format_axes(ax)
 ax.bar(x-.19,[float(v['production']) for v in r],.38,color=st.TEAL,label='Production');ax.bar(x+.19,[float(v['attraction']) for v in r],.38,color=st.BLUE,label='Attraction');ax.set_xticks(x,[v['zone'] for v in r],rotation=40,ha='right');ax.set(xlabel='Model zone',ylabel='Person trips / declared hour');ax.legend()
 meta=read(root/'f10_generation.source.json');emit(fig,'f10_generation','Trip generation',meta['caption'],['All 13 productions and attractions'],[p,root/'f10_generation.source.json'],'assets/six-city-r3-1/berkeley/f10_generation.svg',instance='Berkeley 13-zone frozen one-hour demand',role='demand')
 basep=root/'plot_data/f11_distribution';z=rows(basep/'zone_order.csv');r=rows(basep/'distribution_matrix.csv');by={(v['origin_zone_id'],v['destination_zone_id']):float(v['person_trips_per_hour']) for v in r};matrix=np.array([[by[(a['zone_id'],b['zone_id'])] for b in z] for a in z]);assert matrix.shape==(13,13)
 fig=st.new_figure('berkeley','Trip distribution','Complete 13-zone OD matrix',figsize=(10.4,5.4));a=fig.add_axes([.08,.19,.35,.6]);st.format_axes(a);cm=st.FLOW_CMAP.copy();cm.set_bad('#ccd4d9');masked=np.ma.array(matrix,mask=np.eye(13,dtype=bool));im=a.imshow(masked,cmap=cm,interpolation='none',origin='upper');a.set_xticks(range(13),[v['label'] for v in z],rotation=90);a.set_yticks(range(13),[v['label'] for v in z]);a.set(xlabel='Destination zone',ylabel='Origin zone',title='a  Interzonal person trips');cb=fig.colorbar(im,ax=a,fraction=.045,pad=.04);cb.set_label('Person trips / h')
 a=fig.add_axes([.65,.19,.30,.6]);st.format_axes(a);hist=rows(basep/'distribution_histogram.csv');lo=np.array([float(v['lower']) for v in hist]);up=np.array([float(v['upper']) for v in hist]);a.bar(lo,[int(v['directed_pairs']) for v in hist],up-lo,align='edge',color=st.TEAL,edgecolor='white');a.set(xlabel='Person trips / h',ylabel='Positive directed OD pairs',title='b  Complete positive-OD distribution')
 meta=read(root/'f11_distribution.source.json');emit(fig,'f11_distribution','Trip distribution',meta['caption'],['Complete 13x13 matrix; intrazonal cells excluded','All 90 positive OD; 12 original bins'],[basep/'distribution_matrix.csv',basep/'zone_order.csv',basep/'distribution_histogram.csv',root/'f11_distribution.source.json'],'assets/six-city-r3-1/berkeley/f11_distribution.svg',instance='Berkeley 13-zone frozen one-hour demand',role='demand')
 p=root/'plot_data/f12_mode_choice/f12_mode_choice.plot_data.csv';r=rows(p);fig=st.new_figure('berkeley','Mode choice','Saved OD-specific logit aggregation',figsize=(10.4,4.6));axes=fig.subplots(1,3);fig.subplots_adjust(left=.085,right=.96,bottom=.19,top=.75,wspace=.55)
 for a,key,label,title in zip(axes,['person_trips','share','weighted_generalized_min'],['Person trips / h','Share (%)','Generalized cost (min)'],['a  Modeled demand','b  Mode share','c  Trip-weighted cost']):
  st.format_axes(a);v=[float(q[key])*(100 if key=='share' else 1) for q in r];a.bar([q['mode'].capitalize() for q in r],v,color=[st.TEAL,st.BLUE,st.INK]);a.set(ylabel=label,title=title);a.set_ylim(0,max(v)*1.18)
  for i,n in enumerate(v):a.text(i,n+max(v)*.025,f'{n:.2f}',ha='center',fontsize=8)
 meta=read(root/'f12_mode_choice.source.json');emit(fig,'f12_mode_choice','Mode choice',meta['caption'],['Person trips/h','Percent share','Generalized minutes'],[p,root/'f12_mode_choice.source.json'],'assets/six-city-r3-1/berkeley/f12_mode_choice.svg',instance='Berkeley 13-zone frozen one-hour demand',role='demand')
 (out/'RENDER_RESULT.json').write_text(json.dumps({'status':'RENDERED_PENDING_VISUAL_QA','items':result,'solver_calls':0},ensure_ascii=False,indent=2),encoding='utf-8');print('Rendered',len(result),'Berkeley figures')
if __name__=='__main__':main()
