"""Sioux CG comparison views, using saved results only; no numerical solve."""
from pathlib import Path
import csv,json,hashlib,sys,re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm
from PIL import Image
R=Path(__file__).resolve().parents[2];D=R/'docs';A=D/'assets/shared-cg-20261013';O=A/'sioux-comparison'
sys.path.insert(0,str(Path(__file__).parent/'berkeley_alignment_r2'))
from atlas_style import new_figure,format_axes,compact_header,TEAL,BLUE,FLOW_CMAP
from embed_serif_fonts import embed_serif_fonts
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(fig,n,branch,stem,title,caption,data,inputs):
 out=O/str(n)/branch;out.mkdir(parents=True,exist_ok=True);compact_header(fig)
 for ext in ['png','svg']:fig.savefig(out/(stem+'.'+ext),dpi=300,bbox_inches='tight',pad_inches=.055,metadata={'Date':None}if ext=='svg'else None)
 embed_serif_fonts(out/(stem+'.svg'));plt.close(fig)
 dp=out/(stem+'.plot.json');dp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
 sp=out/(stem+'.source.json');sp.write_text(json.dumps({'instance':n,'branch':branch,'renderer':Path(__file__).relative_to(R).as_posix(),'renderer_sha256':sha(Path(__file__)),'inputs':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)}for p in inputs],'data':dp.name,'data_sha256':sha(dp),'exports':{x:sha(out/(stem+'.'+x))for x in ['png','svg']},'caption':caption,'new_solver_run':False,'source_and_reuse_notice':'../../../NOTICE.txt'},indent=2)+'\n',encoding='utf8')
 (out/(stem+'.caption.txt')).write_text(caption+'\n',encoding='utf8')
 with Image.open(out/(stem+'.png'))as im:w,h=im.size
 rel=(out/stem).relative_to(D).as_posix()
 return {'id':f'cg-sioux{n}-{branch}-{stem}','title':title,'src':rel+'.svg','png':rel+'.png','data':dp.relative_to(D).as_posix(),'source':sp.relative_to(D).as_posix(),'caption':caption,'width':w,'height':h}
def historical(n):
 figs=[];p=D/f'assets/sioux/phase_i_r1/data/{n}_phase_i_trace.csv';rr=rows(p);x=[int(r['round'])for r in rr];y=[float(r['total_artificial_flow'])for r in rr]
 cols=sorted([k for k in rr[0]if re.fullmatch(r'XS\d+_artificial_flow',k)],key=lambda k:int(re.search(r'\d+',k)[0]));assert len(cols)==n
 matrix=np.array([[float(r[k])for k in cols]for r in rr]);assert np.allclose(matrix.sum(axis=1),y,rtol=1e-9,atol=1e-6)
 fig=new_figure('Sioux Falls','Phase I restores feasibility',f'Historical CG / {n} OD / total-flow view',figsize=(9,5.4));ax=fig.add_axes([.13,.22,.8,.54]);format_axes(ax);ax.step(x,y,where='post',color=TEAL,lw=1.6);ax.scatter(x,y,s=15,color=TEAL);ax.set(xlabel='Saved Phase I round',ylabel='Artificial flow (original flow units)')
 cap=f'Historical {n}-OD CG: {len(x)} saved states, rounds {x[0]}–{x[-1]}; artificial flow {y[0]:.12g} → {y[-1]:.12g}. The same saved run as the retained total/per-OD heatmap, not Dev18. No interpolation or new solve.'
 figs.append(save(fig,n,'original','phase-i-total','Phase I: total artificial flow',cap,{'round':x,'artificial_flow':y,'unit':'original flow units'},[p]))
 p=D/f'assets/sioux/phase_i_r1/data/{n}_phase_ii_trace.csv';rr=rows(p);x=np.array([int(r['round'])for r in rr]);y=np.array([float(r['objective_value'])for r in rr]);lp=float(rr[0]['arc_lp_reference_objective'])
 fig=new_figure('Sioux Falls','Phase II objective',f'Historical CG / {n} OD / {len(x)} saved states',figsize=(9,5.4));ax=fig.add_axes([.13,.22,.8,.54]);format_axes(ax);ax.step(x,y,where='post',color=TEAL,lw=1.6);ax.scatter(x[:1],y[:1],s=24,facecolor='white',edgecolor=TEAL,label='Initial state');ax.scatter(x[1:],y[1:],s=24,color=TEAL,label='Saved improvement');ax.axhline(lp,color=BLUE,ls='--',lw=1,label='Same-graph arc-flow LP');ax.set(xlabel='Phase II round',ylabel='Native cost × original volume',xticks=x);ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.legend(loc='upper right',fontsize=8)
 cap=f'Historical {n}-OD CG: {len(x)} saved Phase II objective states, {len(x)-1} updates; {y[0]:.12g} → {y[-1]:.12g}; own-graph LP {lp:.12g}. Objective agreement is not an independent full-DAG pricing certificate. Original native units are retained.'
 figs.append(save(fig,n,'original','phase-ii','Phase II objective',cap,{'round':x.tolist(),'objective':y.tolist(),'same_graph_arc_lp':lp,'unit':'native cost × original volume'},[p]))
 p=D/f'assets/shared-cg-20261013/sioux-comparison/{n}/historical-map-input.json';d=load(p);flow=d['flow'];geom=d['geometry'];keys=list(flow);segments=[geom[k]for k in geom]
 fig=new_figure('Sioux Falls','Final physical-link movement flow',f'Historical CG / {n} OD / map-only view',figsize=(9,6));ax=fig.add_axes([.1,.19,.73,.58]);format_axes(ax);ax.add_collection(LineCollection(segments,colors='#d8e1e3',linewidths=.7));lc=LineCollection([geom[k]for k in keys],array=np.array([flow[k]for k in keys]),cmap=FLOW_CMAP,norm=PowerNorm(.5,vmin=0,vmax=d['common_flow_max']),linewidths=2);ax.add_collection(lc);ax.autoscale();ax.margins(.06);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([]);ax.grid(False);ax.set_xlabel('Schematic topology · not geographic coordinates');cb=fig.colorbar(lc,ax=ax,fraction=.045,pad=.04);cb.set_label('Summed movement-flow units')
 cap=f'Historical {n}-OD CG final movement-arc audit, summed by physical link: {len(flow)} selected links. Map-only alternative to the retained schematic-map/ranked-distribution card. Grey context is outside the selected graph, not measured zero. The 200/250 views share the same colour range. No Dev18 flow is borrowed.'
 figs.append(save(fig,n,'original','physical-map','Final physical-link movement flow',cap,d,[p,R/d['audit_source']]))
 return figs
def certificate(n,branch):
 p=A/f'sioux_{n}_H/{branch}/upper-certificate.json';d=load(p);assert d['status']=='PASS_FULL_GRAPH'
 u=d['original_objective'];l=d['verified_full_graph_lower_bound'];gap=d['relative_gap_raw'];v=d['maximum_full_graph_potential_inequality_violation']
 fig=new_figure('Sioux Falls','Independent full-graph certificate',f'{n} OD / {branch} / saved aggregate checks',figsize=(9,5.8));ax=fig.add_axes([.13,.24,.4,.5]);format_axes(ax);ax.scatter([0,1],[u,l],s=42,color=[BLUE,TEAL]);ax.set_xticks([0,1],['Feasible objective','Verified lower bound']);ax.set_ylabel('Native cost × original volume');ax.ticklabel_format(axis='y',style='plain',useOffset=False);ax.set_ylim(u*.9995,u*1.0005);ax.text(.02,.95,f'Signed relative gap: {gap:.4g}',transform=ax.transAxes,va='top',fontsize=8)
 ax=fig.add_axes([.68,.24,.25,.5]);format_axes(ax);ax.scatter([0],[v],s=44,color=TEAL,zorder=3);ax.axhline(0,lw=.6,color=BLUE);ax.set_xticks([0],['All-arc check']);ax.set_xlim(-.5,.5);ax.set_ylim(-1e-6,1e-6);ax.set_ylabel('Maximum potential-inequality violation');ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0));ax.text(.5,.65,f'{v:g} (saved exact value)\n{d["all_original_arcs"]:,} original arcs\n{d["original_demands"]} demands',ha='center',transform=ax.transAxes,fontsize=8)
 cap=f'{branch}, {n} OD: saved independent verifier checks every original dynamic arc and demand source/sink. U={u:.15g}, L={l:.15g}, signed gap={gap:.15g}; maximum potential inequality violation={v:g}. This is an aggregate full-graph certificate, not a per-OD ungenerated-path pricing bar chart. No per-OD pricing values are invented; the historical original CG branch does not inherit this certificate.'
 return save(fig,n,branch,'independent-certificate','Independent pricing: aggregate full-graph certificate',cap,d,[p])
def main():
 result={'historical':{},'shared_certificates':{}}
 for n in [200,250]:
  result['historical'][str(n)]=historical(n)
  for branch in ['dev18','historical-best']:result['shared_certificates'][f'sioux_{n}_H/{branch}']=certificate(n,branch)
 (O/'new-figures.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Rendered six historical alternatives and four saved aggregate certificates; no optimizer')
if __name__=='__main__':main()
