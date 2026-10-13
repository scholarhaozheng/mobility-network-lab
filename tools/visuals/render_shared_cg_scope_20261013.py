"""Plot frozen release definitions, without compiling graphs or running solvers."""
from pathlib import Path
import json,hashlib,sys
import matplotlib.pyplot as plt
from PIL import Image
import render_shared_cg_20261013 as base
AS=base.AS

def render_case(c):
 out=AS/c['case_id']/'scope';out.mkdir(exist_ok=True)
 data={k:c[k] for k in ['case_id','OD','events','dt_seconds','release_steps','horizon_steps','scale','base_demand','layer','lineage','parent_note','source_hashes']}
 for k in ['release_indices','pulse_volume']:
  if k in c:data[k]=c[k]
 data['scope']='Saved demand compilation rule; not an optimizer history or observed departures'
 p=out/'plot-data.json';p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 dt=c['dt_seconds'];factor=dt/60 if dt is not None else 1
 fig=base.new_figure(c['city_name'],'Demand releases and finite time horizon',c['case_id']+' · frozen assignment scope',figsize=(9,4.8))
 ax=fig.add_axes([.15,.31,.77,.38]);base.format_axes(ax)
 horizon=c['horizon_steps']*factor
 ax.barh([0],[horizon],height=.26,color=base.BLUE,label='Finite graph horizon')
 if c['release_steps'] is not None:
  length=c['release_steps']*factor
  ax.barh([1],[length],height=.26,color=base.TEAL)
  ax.text(length+max(horizon,.1)*.015,1,f"{c['release_steps']:,} equal release steps",va='center',fontsize=8)
  period=f"{c['base_demand']:.9f} PCE/h parent × {c['scale']:g} (vehicle OD only)"
 else:
  xx=[v*factor for v in c['release_indices']];ax.scatter(xx,[1]*len(xx),s=55,color=base.TEAL,zorder=4)
  ax.annotate('Saved departure pulse(s)',(xx[0],1),xytext=(9,11),textcoords='offset points',fontsize=8)
  period=f"Pulse volume {c['pulse_volume']:.9g} in original model flow units"
 ax.set_yticks([0,1],['Graph horizon','Demand release']);ax.set_ylim(-.6,1.65);ax.set_xlim(-horizon*.025,horizon*1.11)
 ax.set_xlabel('Model time (min)' if dt is not None else 'Native time-step index (seconds not established)')
 fig.text(.15,.17,f"{c['OD']:,} OD · {c['events']:,} release events · {c['layer']} · "+(f'Δt = {dt:g} s' if dt is not None else 'native step'),fontsize=10)
 fig.text(.15,.105,period,fontsize=9)
 fig.text(.15,.045,'H/Q discretisation and synthetic ×2 stress do not recompute the upstream four stages.',fontsize=8.4)
 base.compact_header(fig)
 for ext in ['svg','png']:fig.savefig(out/('time-scope.'+ext),dpi=220,bbox_inches='tight',pad_inches=.055,metadata={'Date':None} if ext=='svg' else None)
 base.embed_serif_fonts(out/'time-scope.svg');plt.close(fig)
 caption=(f"{c['case_id']}: {c['lineage']['release_rule']}. Graph horizon {c['horizon_steps']} steps. "
          +c['parent_note']+' The release count is not a CG iteration count. This scope diagram is shared by evidence versions of the same frozen case.')
 (out/'time-scope.caption.txt').write_text(caption+'\n',encoding='utf8')
 provenance={'case_id':c['case_id'],'renderer':Path(__file__).relative_to(base.ROOT).as_posix(),'renderer_sha256':base.sha(Path(__file__)),'data':'plot-data.json','data_sha256':base.sha(p),'input_hashes':c['source_hashes'],'snapshot':'2026-10-13 22:26 Asia/Shanghai','new_solver_run':False,'caption':caption,'exports':{ext:base.sha(out/('time-scope.'+ext)) for ext in ['svg','png']}}
 (out/'time-scope.source.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 with Image.open(out/'time-scope.png') as im:w,h=im.size
 rel=out.relative_to(base.ROOT/'docs').as_posix()
 return {'id':'cg-'+c['case_id']+'-time-scope','title':'CG demand releases and time horizon','src':rel+'/time-scope.svg','png':rel+'/time-scope.png','data':rel+'/plot-data.json','source':rel+'/time-scope.source.json','caption':caption,'width':w,'height':h}

def main():
 cat=base.load(AS/'catalog.json')
 for c in cat['cases']:
  f=render_case(c)
  for e in c['evidence']:
   e['figures']=[x for x in e['figures'] if not x['id'].endswith('-time-scope')]+[f]
  print(c['case_id'],flush=True)
 (AS/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
