"""Pure saved-public-data and native-SVG legacy figure renderer.
No optimizer, matching code, private Full archive, downloader or model builder is imported.
Scientific SVG geometry is preserved by the explicit vector-transform route.
"""
from pathlib import Path
import json,argparse,re,copy,hashlib,subprocess,sys,xml.etree.ElementTree as ET
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from PIL import Image,ImageChops
import textwrap
try:
 from .style import *
except ImportError:
 from style import *
NS='http://www.w3.org/2000/svg';TAG=lambda x:'{'+NS+'}'+x
ET.register_namespace('',NS);ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
HERE=Path(__file__).resolve().parent

def concise_caption(text):
    text=re.sub(r'\u00a9 OpenStreetMap contributors(?:; road-derived data|\s*\u00b7)?\s+ODbL 1\.0\.?','',text)
    return text.replace('https://www.openstreetmap.org/copyright','').strip()

def vector_caption(p,removed):
    i=p['inventory_index'];notes=[]
    if i in [15,36,38,54,73,128,169,138,180]:notes=removed[2:]
    if i==79:notes=['Shattuck / Center.',*removed[1:]]
    additional={
      50:'Own ADMM physical-road vector and exact LP on the frozen four-OD pulse. The signed map shows roundoff-sized differences; this is a final spatial state comparison.',
      135:'These retained compressed Native rank-26/52 endpoints remain below their acceptance gates. The later accepted uncompressed Native80 run is separate evidence.',
      139:'Each panel shows the saved input-cost seed path for one OD. Initial path support alone establishes no optimization or capacity-feasibility conclusion.',
      147:'Color encodes the number of saved generated columns using each physical road.',
      151:'The retained own ADMM x remains infeasible; its displayed road values are diagnostic.'}
    if i in additional:notes.append(additional[i])
    return concise_caption(' '.join([p['caption'],*notes]))

def text_of(g):
 texts=[''.join(x.itertext()) for x in g.iter() if x.tag==TAG('text')]
 if not texts:texts=[x.text.strip()for x in g.iter()if x.tag is ET.Comment and x.text]
 return ' '.join(texts)
def geometry_hash(g):
 rows=[]
 def walk(n,is_text=False):
  is_text=is_text or n.get('id','').startswith('text_')or n.tag in [TAG('text'),TAG('tspan')]
  if not is_text and n.tag in [TAG(x)for x in ['path','rect','circle','ellipse','polygon','polyline','line','image','use']]:
   if not n.get('id','').startswith(('DejaVu','Liberation','STIX')):rows.append((n.tag,sorted(n.attrib.items())))
  for child in n:walk(child,is_text)
 walk(g)
 return hashlib.sha256(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),len(rows)
def source_bind(plan):
 return [{'public_path':plan['original_path'],'sha256':plan['original_sha256'],'role':'Unchanged prior display asset'}]+[{'public_path':p,'sha256':sha256(REPO/p),'role':'Approved saved public plot data'}for p in plan['plot_data']]
def base_record(p):
 return {'figure_id':p['figure_id']+'-R11','city':p['city'],'instance':p['caption'],'role':'saved-result presentation','conclusion':p['title'],'panels':p['panels']or'Preserved independent scientific panels','quantity':'Actual quantities and units retained in axes and source data','unit':'See panel axes; no conversion','render_method':p['render_method'],'original_asset':p['original_path'],'original_asset_sha256':p['original_sha256'],'original_home_ids':p['original_home_ids'],'original_volume_anchors':p['original_volume_anchors']}
def finish(stem,record):
 record['exports']={ext:sha256(stem.with_suffix('.'+ext))for ext in ['svg','png','pdf']}
 with Image.open(stem.with_suffix('.png'))as im:record['dimensions']=list(im.size)
 stem.with_suffix('.source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');return record

def render_data(p,stem):
 d=json.loads((REPO/p['plot_data'][0]).read_text(encoding='utf8'));i=p['inventory_index'];cap=p['caption'];rec=base_record(p)
 if i==40:
  fig=new_figure(p['city'],p['title'],figsize=(8,4));ax=fig.add_subplot();fig.subplots_adjust(left=.12,right=.97,bottom=.18,top=.78);arcs=d['arcs'];states=list(dict.fromkeys(a[k].rsplit('@t',1)[0]for a in arcs for k in ['from_node_time_id','to_node_time_id']))
  for a in arcs:
   x1,x2=int(a['from_time']),int(a['to_time']);y1=states.index(a['from_node_time_id'].rsplit('@t',1)[0]);y2=states.index(a['to_node_time_id'].rsplit('@t',1)[0]);c=TEAL if a['arc_type']=='physical_road'else BLUE;ax.annotate('',(x2,y2),(x1,y1),arrowprops={'arrowstyle':'->','color':c,'lw':1.7});ax.scatter([x1,x2],[y1,y2],s=17,color=c,zorder=3)
  ax.legend(handles=[Line2D([0],[0],color=TEAL,lw=1.7,label='Physical-road traversal'),Line2D([0],[0],color=BLUE,lw=1.7,label='Zero-time turn')],loc='upper right',fontsize=8)
  cap+=' The seven selected saved arcs follow one computed route: teal marks physical-road traversal and blue marks zero-time turn transitions. State spacing is schematic; no assigned-flow magnitude is encoded.'
  ax.set_yticks(range(len(states)),states,fontsize=8);ax.set_xticks(range(5,10));ax.set_xlabel('Time layer (30 seconds per step)');ax.set_ylabel('Saved road state');ax.invert_yaxis();format_axes(ax);ax.grid(color=GRID,lw=.5);rec.update(quantity='Saved physical-road and turn-arc incidence',unit='30-second time layers',panels=[{'metric':'actual saved route segment','arc_records':len(arcs),'state_count':len(states)}])
 elif i==41:
  fig=new_figure(p['city'],p['title'],figsize=(9,4));aa=fig.subplots(1,2);fig.subplots_adjust(left=.08,right=.96,bottom=.18,top=.76,wspace=.38)
  for j,path in enumerate(d['paths']):
   ar=[a for a in path['arcs']if a['arc_type']=='physical_road'];aa[0].step(range(len(ar)),[int(a['to_time'])for a in ar],where='post',label='OD '+str(j+1),color=CATEGORIES[j])
  aa[0].set_xlabel('Physical traversal index');aa[0].set_ylabel('Arrival time layer');aa[0].set_title('a  Saved path timing',loc='left');aa[0].legend(fontsize=8);aa[1].bar(range(4),[float(r['route_cost_minutes'])for r in d['routes']],color=CATEGORIES[:4]);aa[1].set_xticks(range(4),['OD 1','OD 2','OD 3','OD 4']);aa[1].set_ylabel('Fixed route cost (min)');aa[1].set_title('b  Objective cost',loc='left');[format_axes(a)for a in aa];rec.update(quantity='Arrival layers and fixed route objective costs',unit='30-second steps; minutes',panels=['four saved physical-route arrival sequences','four exact saved route costs'])
 elif i in [49,188]:
  uc=i==49;vals=np.array(d['absolute_balance_residual_pce']if uc else d['absolute_residual_pce'],float);nodes=d['node_ids']if uc else d['node_labels'];labels=d['row_labels']if uc else d['commodity_labels'];floor=d['display']['vmin']if uc else d['display_floor_pce'];gate=d['display']['vmax']if uc else d['display_ceiling_and_gate_pce'];count=d['full_node_count']if uc else d['all_node_count']
  fig=new_figure(p['city'],p['title'],figsize=(11.7,4));ax=fig.add_axes([.07,.33,.83,.38]);im=ax.imshow(np.maximum(vals,floor),aspect='auto',norm=LogNorm(floor,gate),cmap=FLOW_CMAP,interpolation='nearest');ax.set_xticks(range(len(nodes)),nodes,rotation=90,fontsize=7);ax.set_yticks(range(len(labels)),labels,fontsize=8);ax.set_xlabel('Selected time-node identity');cb=fig.colorbar(im,ax=ax,fraction=.024,pad=.025);cb.set_label('Absolute balance residual (PCE)');rec.update(quantity='Absolute original-commodity node-balance residual',unit='PCE',panels=[{'grid_shape':list(vals.shape),'all_nodes_checked':count,'display_floor_pce':floor,'ceiling_and_gate_pce':gate,'saved_completed_updates':1,'raw_values_sha256':hashlib.sha256(vals.tobytes()).hexdigest()}]);cap+=' The heatmap is the saved final spatial conservation state, not an iteration-history heatmap. The displayed color floor and unchanged gate are retained; all exact raw residual values remain in the linked public plot data.'
 elif i==134:
  fig=new_figure(p['city'],p['title'],figsize=(12,4));aa=fig.subplots(1,3);fig.subplots_adjust(left=.065,right=.97,bottom=.20,top=.74,wspace=.47);fw=d['FW'];aa[0].semilogy([int(r['iteration'])for r in fw],[abs(float(r['relative_gap']))for r in fw],'-o',color=TEAL,ms=3);aa[0].set_xlabel('FW saved update');aa[0].set_ylabel('Absolute full-graph relative gap');aa[0].set_title('a  FW process',loc='left')
  for rank,col in [('26',TEAL),('52',BLUE)]:
   rows=d['Native'][rank];x=np.arange(1,len(rows)+1);aa[1].semilogy(x,[abs(float(r['full_relative_gap']))for r in rows],'-o',label='rank '+rank,color=col,ms=3);aa[2].semilogy(x,[float(r['max_abs_od_residual'])for r in rows],'-o',label='rank '+rank,color=col,ms=3)
  aa[1].axhline(d['Native']['26'][-1]['gates']['full_relative_gap_abs'],color=INK,ls='--',lw=.8,label='Gap gate');aa[2].axhline(d['Native']['26'][-1]['gates']['max_od_error_abs'],color=INK,ls='--',lw=.8,label='Absolute OD term')
  for a in aa[1:]:a.set_xlabel('Saved Native outer record');a.legend(fontsize=7)
  aa[1].set_ylabel('Absolute full-graph relative gap');aa[1].set_title('b  Native gap',loc='left');aa[2].set_ylabel('Maximum OD residual (PCE/h)');aa[2].set_title('c  Native conservation',loc='left');[format_axes(a)for a in aa];cap+=' These are the retained six FW states and twelve original Native outer records per rank, not the later accepted uncompressed Native80 run. The compressed Native rank-26/52 endpoints remain unaccepted.';rec.update(quantity='Absolute full-graph gap and original-unit OD residual',unit='dimensionless; PCE/h',panels=['6 FW saved states','12 Native records per rank: full gap','12 Native records per rank: conservation'])
 elif i==148:
  fig=new_figure(p['city'],p['title'],figsize=(8.4,3.5));ax=fig.add_subplot();fig.subplots_adjust(left=.10,right=.96,bottom=.19,top=.74);ax.plot([int(r['iteration'])for r in d],[float(r['best_dual'])for r in d],color=TEAL,label='Best valid lower bound');ax.set_xlabel('Actual pure-LR iteration');ax.set_ylabel('Dual lower bound (PCE·min)');format_axes(ax);ax.legend(loc='lower right',fontsize=8);cap+=' All 759 original pure-subgradient LR records are shown. This run has no own feasible upper bound, so no certified gap is drawn. The newly accepted self-priced recovery hybrid is a distinct run and does not change this failure.';rec.update(quantity='Best valid dual lower bound',unit='PCE·min',panels=[{'saved_records':len(d),'own_feasible_upper_bound':None,'certified_gap':None}],saved_states=len(d))
 else:raise ValueError(i)
 rec['scope_note']=cap;return export_figure(fig,stem,rec,concise_caption(cap),source_bind(p))

def render_vector(p,stem,a):
 src=REPO/p['original_path'];parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True));old=ET.fromstring(src.read_bytes(),parser=parser);root=copy.deepcopy(old);figure=root.find(TAG('g'));assert figure is not None
 removed=[];defs=ET.Element(TAG('defs'))
 for ch in list(figure):
  if ch.get('id','').startswith('text_'):
   removed.append(text_of(ch))
   for de in ch.findall('.//'+TAG('defs')):
    for v in list(de):defs.append(copy.deepcopy(v))
   figure.remove(ch)
  elif ch.get('id')=='patch_1':figure.remove(ch)
 figure.insert(0,defs)
 # Same-size input-layer schematic: bookkeeping sentences in figure text move outside, never discard arc rows.
 root.set('style','background:transparent')
 for style in root.findall('.//'+TAG('style')):
  if style.text:style.text=style.text.replace('"Times New Roman"','"DejaVu Serif"')
 # All source scientific elements remain literal; typography above/below the plots is replaced.
 before_hash,geometry_count=geometry_hash(figure);temp=stem.with_suffix('.body.svg');temp.parent.mkdir(parents=True,exist_ok=True);temp.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
 fontdir=Path(matplotlib.get_data_path())/'fonts/ttf'
 def pdfconvert(inp,out):
  cmd=[a.pdf_python,str(HERE/'svg_to_pdf.py'),str(inp),str(out),'--font-dir',str(fontdir)]
  if a.pdf_package_dir:cmd+=['--package-dir',a.pdf_package_dir]
  return subprocess.run(cmd,check=True,capture_output=True,text=True)
 pdfconvert(temp,temp.with_suffix('.pdf'))
 subprocess.run([a.pdftoppm,'-singlefile','-png','-r','72',str(temp.with_suffix('.pdf')),str(temp.with_suffix(''))],check=True,capture_output=True)
 with Image.open(temp.with_suffix('.png'))as im:
  rgb=im.convert('RGB');bbox=ImageChops.difference(rgb,Image.new('RGB',rgb.size,'white')).point(lambda z:255 if z>3 else 0).getbbox()
 assert bbox
 pad=2.0;x=max(0,bbox[0]-pad);y=max(0,bbox[1]-pad);w=bbox[2]-bbox[0]+2*pad;h=bbox[3]-bbox[1]+2*pad
 # Generate the actual standardized header using the shared style module; body axes are a measured placeholder only.
 fig=new_figure(p['city'],p['title'],figsize=((w+8)/72,(h+90)/72));height=h+90;width=w+8;ax=fig.add_axes([4/width,4/height,w/width,h/height]);ax.set_axis_off()
 for t in fig._mcl_header_artists:t.set_x(4/width)
 fig._mcl_header_artists[1].set_text(textwrap.fill(p['title'],max(15,int(w/8.0))))
 cap=vector_caption(p,removed)
 rec=base_record(p);rec.update(vector_body_geometry_sha256=before_hash,vector_body_geometry_count=geometry_count,removed_figure_text=removed,vector_transform={'crop_origin_svg_units':[x,y],'crop_size_svg_units':[w,h],'scientific_geometry_transformed':False,'only_uniform_outer_translation':True},raw_data_replot=False)
 rec=export_figure(fig,stem,rec,concise_caption(cap),source_bind(p),close=False);fig.canvas.draw();renderer=fig.canvas.get_renderer();tight=fig.get_tightbbox(renderer);axbbox=ax.get_window_extent(renderer);newx=axbbox.x0/fig.dpi*72-tight.x0*72+.055*72;newy=(tight.y1*72+.055*72)-axbbox.y1/fig.dpi*72
 new=ET.fromstring(stem.with_suffix('.svg').read_bytes())
 # Prefix only fresh header IDs; unchanged scientific-body identities remain intact.
 for el in new.iter():
  if el.get('id') and el.get('id')!='embedded-serif-fonts':el.set('id','r11-header-'+el.get('id'))
 g=ET.Element(TAG('g'),{'id':'preserved-scientific-body','transform':f'translate({newx-x:.9f} {newy-y:.9f})'});figure.set('id','preserved-original-figure');g.append(figure)
 # Definitions outside figure include clip paths and image gradients; copy without renaming any referenced IDs.
 for child in list(root):
  if child.tag==TAG('defs'):new.append(copy.deepcopy(child))
 new.append(g);after_hash,count=geometry_hash(figure);assert before_hash==after_hash and count==geometry_count
 stem.with_suffix('.svg').write_bytes(ET.tostring(new,encoding='utf-8',xml_declaration=True));plt.close(fig)
 # Normalize embedded font subsets after all original editable labels are present.
 sv=stem.with_suffix('.svg');markup=sv.read_text(encoding='utf8');markup=re.sub(r'<style[^>]*id="embedded-serif-fonts"[^>]*>.*?</style>','',markup,flags=re.S);sv.write_text(markup,encoding='utf8');rec['font']=embed_serif_fonts(sv)
 outlined=any(el.tag==TAG('use') and any(z in el.get('{http://www.w3.org/1999/xlink}href','') for z in ['DejaVu','STIX','Liberation']) for el in figure.iter())
 rec['font'].update(all_labels_editable=not outlined,retained_outlined_legacy_labels=outlined,editability_scope='The new city/title and any original live text are editable. Original outlined glyph labels remain outlined to preserve numerical evidence.')
 cv=pdfconvert(stem.with_suffix('.svg'),stem.with_suffix('.pdf'))
 subprocess.run([a.pdftoppm,'-singlefile','-png','-r','300',str(stem.with_suffix('.pdf')),str(stem)],check=True,capture_output=True)
 rec['pdf_converter_diagnostics']=cv.stderr[-3000:];rec['vector_body_post_sha256']=after_hash;rec['vector_geometry_preserved']=before_hash==after_hash;rec['vector_transform']['outer_translation_svg_units']=[newx-x,newy-y]
 for ext in ['svg','png','pdf']:temp.with_suffix('.'+ext).unlink(missing_ok=True)
 return finish(stem,rec)


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',default=str(HERE/'legacy_manifest.json'));ap.add_argument('--output',required=True);ap.add_argument('--pdf-python',default=sys.executable);ap.add_argument('--pdf-package-dir');ap.add_argument('--pdftoppm',default='pdftoppm');ap.add_argument('--indices',default='');a=ap.parse_args();plans=json.loads(Path(a.manifest).read_text(encoding='utf8'));wanted={int(x)for x in a.indices.split(',')if x};out=Path(a.output);result=[]
 for p in plans:
  if wanted and p['inventory_index']not in wanted:continue
  assert sha256(REPO/p['original_path'])==p['original_sha256']
  stem=out/p['city']/p['stem'];stem.parent.mkdir(parents=True,exist_ok=True)
  rec=render_data(p,stem)if p['render_method']=='data-replot'else render_vector(p,stem,a)
  result.append({'inventory_index':p['inventory_index'],'old_asset':p['original_path'],'city':p['city'],'render_method':p['render_method'],'output_stem':str(stem),'svg':str(stem.with_suffix('.svg')),'png':str(stem.with_suffix('.png')),'pdf':str(stem.with_suffix('.pdf')),'source':str(stem.with_suffix('.source.json')),'caption':str(stem.with_suffix('.caption.md')),'title':p['title'],'original_sha256':p['original_sha256'],'exports':rec['exports'],'dimensions':rec['dimensions'],'status':'RENDERED_PENDING_VISUAL_QA'})
  print(json.dumps({'done':p['inventory_index'],'method':p['render_method'],'output':str(stem)},ensure_ascii=False),flush=True)
 (out/'render-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
