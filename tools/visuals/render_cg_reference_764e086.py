"""Additional views of the original 764e086 CG records; saved CSV only."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent/'berkeley_alignment_r2'))
from atlas_style import new_figure,format_axes,compact_header,TEAL,BLUE
from embed_serif_fonts import embed_serif_fonts
from PIL import Image
A=ROOT/'docs/assets/shared-cg-20261013/reference-764e086'
def rows(p):
 with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(fig,city,stem,title,caption,data,sources):
 out=A/city;out.mkdir(parents=True,exist_ok=True);compact_header(fig)
 for ext in ['png','svg']:fig.savefig(out/(stem+'.'+ext),dpi=300,bbox_inches='tight',pad_inches=.055,metadata={'Date':None}if ext=='svg'else None)
 embed_serif_fonts(out/(stem+'.svg'));plt.close(fig)
 dp=out/(stem+'.plot.json');dp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
 provenance={'reference_commit':'764e0862e4f9a8d473b7bbcc04545b47dd6b0178','city':city,'renderer':Path(__file__).relative_to(ROOT).as_posix(),'renderer_sha256':sha(Path(__file__)),'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in sources],'data':dp.name,'data_sha256':sha(dp),'caption':caption,'source_and_reuse_notice':'../../NOTICE.txt','new_solver_run':False,'exports':{ext:sha(out/(stem+'.'+ext))for ext in ['png','svg']}}
 (out/(stem+'.source.json')).write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf8');(out/(stem+'.caption.txt')).write_text(caption+'\n',encoding='utf8')
 with Image.open(out/(stem+'.png'))as im:w,h=im.size
 rel=(out/stem).relative_to(ROOT/'docs').as_posix()
 return {'id':'cg-reference-'+city+'-'+stem,'title':title,'src':rel+'.svg','png':rel+'.png','data':dp.relative_to(ROOT/'docs').as_posix(),'source':rel+'.source.json','caption':caption,'width':w,'height':h}
def main():
 result={}
 for city in ['boston','hong-kong']:
  p=ROOT/('docs/assets/boston/space_time_cg_r4/data/phase_i_total.csv'if city=='boston'else'docs/assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_i_artificial_flow_trace.csv')
  rr=rows(p);key='artificial_flow'if city=='boston'else'total_artificial_flow';x=[int(r['round'])for r in rr];y=[float(r[key])for r in rr];unit='vehicles'if city=='boston'else'PCE'
  fig=new_figure(city,'Phase I restores feasibility','Original 10-OD record / total-flow view',figsize=(9,5.4));ax=fig.add_axes([.13,.22,.8,.54]);format_axes(ax);ax.step(x,y,where='post',color=TEAL,lw=1.6);ax.scatter(x,y,s=19,color=TEAL);ax.set(xlabel='Saved Phase I round',ylabel='Artificial flow ('+unit+')')
  caption=f'The same original 764e086 {city} run as the total-plus-per-OD heatmap: {len(x)} saved states, rounds {min(x)}–{max(x)}. Total artificial flow {y[0]:.12g} → {y[-1]:.12g} {unit}. This is an alternative view of the same data, not an additional experiment.'
  result[city]=[save(fig,city,'phase-i-total','Phase I: total artificial flow',caption,{'round':x,'artificial_flow':y,'unit':unit,'role':'Alternative view of the original total + per-OD figure'},[p])]
 p=ROOT/'docs/assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_ii_objective_trace.csv';rr=rows(p);x=np.array([int(r['round'])for r in rr]);v=np.array([float(r['objective_value'])for r in rr]);lp=float(rr[0]['arc_lp_reference_objective'])
 assert len(rr)==2 and list(x)==[0,1]
 fig=new_figure('hong-kong','Phase II objective','R5 / 10 OD / one actual update',figsize=(9,5.4));ax=fig.add_axes([.13,.22,.8,.54]);format_axes(ax);ax.step(x,v,where='post',color=TEAL,lw=1.6);ax.scatter(x[:1],v[:1],s=25,facecolor='white',edgecolor=TEAL,label='Initial saved state');ax.scatter(x[1:],v[1:],s=25,color=TEAL,label='Strict improvement');ax.axhline(lp,ls='--',color=BLUE,label='Same-graph arc-flow LP');ax.set(xlabel='Phase II round',ylabel='Objective (vehicle-minutes)',xticks=[0,1],xlim=(-.08,1.12));ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.legend(fontsize=8,loc='upper right')
 cap='Original Hong Kong R5 saved Phase II states 0 and 1: one real update, not a sampled long trajectory. Objective 75.07523596555359 → 75.03632985794832 vehicle-minutes; same-graph arc-flow LP 75.03632985794819. Uses the Boston 764e086 objective/LP-reference plotting target. Independent complete-path pricing closure remains a separate figure and certificate.'
 result['hong-kong'].append(save(fig,'hong-kong','phase-ii','Phase II objective',cap,{'round':x.tolist(),'objective':v.tolist(),'same_graph_arc_lp_objective':lp,'unit':'vehicle-minutes','updates':1},[p]))
 (A/'additional-figures.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('Rendered three saved-data reference views')
if __name__=='__main__':main()
