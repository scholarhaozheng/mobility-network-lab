"""Maintain CG controls in the existing atlas and canonical city volumes."""
from pathlib import Path
import json,re,html,copy
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[2];D=R/'docs';A=D/'assets/shared-cg-20261013'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def edit(p,s):
 b=p.read_bytes();s=s.replace('\r\n','\n');p.write_bytes(s.replace('\n','\r\n'if b'\r\n'in b else'\n').encode('utf8'))
def balanced(s,start,tag):
 depth=0
 for m in re.finditer(r'</?'+tag+r'\b[^>]*>',s[start:],re.I):
  depth+=-1 if m[0].startswith('</')else 1
  if not depth:return start+m.end()
 raise ValueError((start,tag))
def component_span(s,city):
 for m in re.finditer(r'<section\b[^>]*class="[^"]*\bcg-component\b[^>]*>',s):
  if 'data-cg-city="'+city+'"'in m[0]:return m.start(),balanced(s,m.start(),'section')
 return None
esc=html.escape
cat=read(A/'catalog.json');refs=read(A/'reference-764e086/reference-layouts.json');additional=read(A/'reference-764e086/additional-figures.json')
for city,ref in refs.items():
 original_home=BeautifulSoup(ref['home_original_html'],'html.parser')
 for f in ref['figures'].values():
  im=original_home.find('img',src=f['src'])
  if im:f['home_id']=im.find_parent('div',class_='atlas-card')['id']
 keys=['c-boston-cg-phase1','g-f079','g-f073','c-boston-cg-closure']if city=='boston'else['c-hk-cg-phase1',None,'g-f092','g-f093']
 ref['ordered']=[additional[city][0],ref['figures'][keys[0]],ref['figures'][keys[1]]if keys[1]else additional[city][1],ref['figures'][keys[2]],ref['figures'][keys[3]]]
 if city=='boston':
  # The original physical-flow anchor also belongs to the earlier finite overview.
  # Keep it there; this comparison view receives its own stable target.
  ref['ordered'][3]=dict(ref['ordered'][3],id='cg-reference-boston-physical-flow')
 parent=next(c for c in cat['cases']if c['city']==city)
 c={'case_id':city.replace('-','_')+'_reference_764e086','city':city,'city_name':parent['city_name'],'OD':10,'scale':1,'events':10,'dt_seconds':parent['dt_seconds'],'horizon_steps':parent['horizon_steps'],'reference':True,'default_evidence':'original','lineage':{'release_rule':'Original fixed ten-OD pulse; unchanged 764e086 model.'},'evidence':[{'evidence_id':'original','label':'Original accepted CG · 764e086','figures':ref['ordered'],'history':[],'reference':True}]}
 c['reference_anchors']=[x['id']for x in BeautifulSoup(ref['home_original_html']+ref['volume_original_html'],'html.parser').select('[id]')]
 cat['cases'].insert(0,c);cat['defaults'][city]=c['case_id']

sioux_path=A/'sioux-comparison/new-figures.json'
sioux=read(sioux_path)if sioux_path.exists()else None
if sioux:
 retained=read(A/'sioux-comparison/retained-figures.json')
 for n in [250,200]:
  parent=next(c for c in cat['cases']if c['case_id']==f'sioux_{n}_H')
  c={k:copy.deepcopy(v)for k,v in parent.items()if k!='evidence'}
  c.update(case_id=f'sioux_{n}_original',reference=True,reference_label='original historical CG',sioux_reference=True,reference_anchors=[],default_evidence='original')
  c['evidence']=[{'evidence_id':'original','label':'Historical original CG · independent pricing open','figures':sioux['historical'][str(n)]+retained[str(n)],'history':[]}]
  cat['cases'].insert(0,c)
 cat['defaults']['sioux-falls']='sioux_200_original'

titles=['Phase I: total artificial flow','Phase I: total and per-OD heatmap','Phase II objective','Final physical-link movement flow','Independent pricing closure']
selected=read(A/'selected-three/figures.json')
phase_ii_pairs=read(A/'selected-three-phase-ii/figures.json')
selected_cities={'boston','hong-kong','sioux-falls'}
def card(c,e,f,title,volume=False):
 pre='../'if volume else'';fid=f['id']if volume else f.get('home_id','atlas-'+f['id']);href=pre+f['src']if volume else'volumes/'+c['city']+'.html?cg-case='+c['case_id']+'&amp;cg-evidence='+e['evidence_id']+'#'+f['id']
 cap='<p class="atlas-final-caption">'+esc(f['caption'])+'</p>'
 if not volume:cap='<details class="atlas-card-notes"><summary>Description, units and scope</summary>'+cap+'</details>'
 links=[]
 if not volume:links.append('<a href="'+href+'">Same figure in city record</a>')
 for label,k in [('PNG','png'),('SVG','src'),('Plot data','data'),('Source','source')]:
  if f.get(k):links.append('<a href="'+pre+f[k]+'">'+label+'</a>')
 alias='<span id="figure-'+f['id']+'"></span>'if volume and not c.get('reference')else''
 return '<div class="atlas-card conservative-card cg-figure" data-figure="'+f['id']+'" id="'+fid+'">'+alias+'<h5>'+title+'</h5><a class="atlas-image" href="'+href+'"><img src="'+pre+f['src']+'" alt="'+esc(title)+'" width="'+str(f['width'])+'" height="'+str(f['height'])+'" loading="lazy"></a>'+cap+'<p class="atlas-final-links">'+' · '.join(links)+'</p></div>'
def missing(title,why):return '<div class="atlas-card conservative-card cg-unavailable" data-figure="unavailable-'+re.sub(r'[^a-z0-9]+','-',title.lower())+'"><h5>'+title+'</h5><p>'+esc(why)+'</p></div>'
def gallery(cards,cols):return '<div class="atlas-gallery cg-gallery" data-columns="'+str(cols)+'">'+''.join(cards)+'</div>'
def scope(c):
 dt=c.get('dt_seconds');h=c['horizon_steps'];t=(f'Δt {dt:g} s · {h:,} steps ({dt*h/60:g} min)'if dt else f'{h:,} native time steps; seconds not defined')
 release='single frozen pulse'if c['events']==c['OD']else'one-hour uniform release'
 return f"{c['OD']:,} ODs · vehicle demand ×{c['scale']:g} · {t} · {release}"
def selected_panel(c,e,volume):
 first=selected[c['case_id']+'/'+e['evidence_id']]
 if c.get('sioux_reference'):
  new=sioux['historical'][str(c['OD'])];figs=[first,new[1],new[2]]
 elif c.get('reference'):
  ff=refs[c['city']]['ordered'];figs=[first,ff[2],ff[3]]
 else:
  by={Path(f['src']).stem:f for f in e['figures']};figs=[first,by['phase-ii'],by['physical-flow']]
 figs[1]=phase_ii_pairs[c['case_id']+'/'+e['evidence_id']]
 # Keep old anchors, diagnostics and complete original explanations available.
 earlier=BeautifulSoup(panel(c,e,volume,'five'),'html.parser')
 heading=earlier.find(class_='atlas-method-heading',recursive=False).extract()
 instance=earlier.find(class_='atlas-method-instance',recursive=False).extract()
 summary=earlier.find(class_='atlas-method-summary',recursive=False)
 if summary:
  if c.get('reference'):summary.decompose()
  else:summary['class']=['cg-saved-result-status']
 for f in earlier.select('.cg-figure'):
  if f.get('data-figure') in {x['id'] for x in figs}:f.decompose()
 for g in earlier.select('.cg-gallery'):
  if not g.find(class_='atlas-card'):g.decompose()
 for d in earlier.select('details[open]'):del d['open']
 text='One saved result: Phase I total artificial flow and per-OD heatmap, Phase II objective beside its relative reference gap, then final physical-link movement flow.'
 if not c.get('reference'):text+=' Per-OD history was not saved for this version; the first card identifies the missing matrix.'
 if c.get('sioux_reference'):text+=' Historical independent full-DAG pricing closure remains unestablished.'
 chosen_titles=['Phase I: total artificial flow + per-OD heatmap','Phase II objective','Final physical-link movement flow']
 return str(heading)+str(instance)+'<p class="atlas-method-summary">'+text+'</p>'+gallery([card(c,e,f,t,volume) for f,t in zip(figs,chosen_titles)],3)+'<details class="cg-supporting-records"><summary>Independent pricing, earlier views and source records</summary>'+str(earlier)+'</details>'
def panel(c,e,volume=False,layout='five'):
 if layout=='selected':return selected_panel(c,e,volume)
 pre='../'if volume else'';ref=refs.get(c['city'])if c.get('reference')else None
 if c.get('sioux_reference'):
  n=str(c['OD']);new=sioux['historical'][n];old=retained[n]
  header='<h5 class="atlas-method-heading">Two-phase column generation</h5><p class="atlas-method-instance">'+esc(scope(c)+' · Historical original CG')+'</p><p class="atlas-method-summary">Compare the original Sioux views with the Boston/Hong Kong plotting targets. The two Phase I views use the same saved run. Historical independent full-DAG pricing closure remains unestablished; newer shared-core certificates are separate result choices.</p>'
  if layout=='original':return header+gallery([card(c,e,f,f['title'],volume)for f in old],3)
  result=header+gallery([card(c,e,new[0],titles[0],volume),card(c,e,old[0],titles[1],volume)],2)+gallery([card(c,e,new[1],titles[2],volume),card(c,e,new[2],titles[3],volume),missing(titles[4],'No independent full-DAG pricing closure was established for this historical run. Its saved k-shortest stop and objective agreement do not supply the Boston/Hong Kong per-OD closure vector. Newer shared-core certificates belong to their own result versions.')],3)
  result+='<h5 class="atlas-method-heading">Retained Sioux views · same historical run</h5>'+gallery([card(c,e,f,f['title'],volume)for f in old[1:]],2)
  result+='<p class="cg-evidence-links"><a href="'+pre+'reproduction/experiment-catalog.html#sioux-cg-'+n+'">Historical computation and source records</a> · <a href="'+pre+'assets/shared-cg-20261013/sioux-comparison/FIGURE_INVENTORY.html">All Sioux CG views and comparison guide</a></p>'
  return result
 if ref and layout=='original':return ref['volume_original_html'if volume else'home_original_html']
 heading='<h5 class="atlas-method-heading"'+(' id="'+c['city']+'-finite-cg"'if c.get('reference')and not volume else'')+'>Two-phase column generation</h5>'
 top=heading+'<p class="atlas-method-instance">'+esc(scope(c)+' · '+e['label'])+'</p>'
 if ref:
  figs=ref['ordered'];cards=[card(c,e,f,title,volume)for f,title in zip(figs,titles)]
  top+='<p class="atlas-method-summary">The two Phase I cards are alternative views of one saved experiment. Compare total flow, OD-level feasibility, objective, physical movement and independent pricing.</p>'
  result=top+gallery(cards[:2],2)+gallery(cards[2:],3)
  if volume:
   notes=BeautifulSoup(ref['volume_original_html'],'html.parser')
   shown={f['id']for f in figs}
   for f in notes.select('figure'):
    if f.get('id')in shown:f.decompose()
   result+='<details class="cg-lineage"><summary>Original methods, saved records and source details</summary>'+str(notes)+'</details>'
  result+='<p class="cg-evidence-links"><a href="'+pre+'assets/shared-cg-20261013/RESULT_CODE_INDEX.html#'+c['case_id']+'">Original experiment code and reproduction register</a> · <a href="'+pre+'assets/shared-cg-20261013/reference-764e086/reference-layouts.json">764e086 figure/source bindings</a></p>'
  return result
 by={Path(f['src']).stem:f for f in e['figures']};h=e.get('history',[]);has1=any(x['phase']=='I'for x in h);has2=any(x['phase']=='II'for x in h)
 brief=e['status']+'.'
 if e.get('U')is not None:brief+=f" U={e['U']:.12g}; L={e['L']:.12g}; gap={e['gap_display_pct']:.9g}%."
 if e.get('nonbinding_checks'):brief+=' The saved full-graph capacity certificate is nonbinding; no CG outer iterations were required.'
 top+='<p class="atlas-method-summary">'+esc(brief)+'</p>'
 cards=[card(c,e,by['phase-i'],titles[0],volume)if has1 else missing(titles[0],'No Phase I iteration history was recorded for this result. A feasible seed or nonbinding certificate is documented below.'),missing(titles[1],'The shared-core result did not save artificial flow for each OD at each round. A per-OD heatmap cannot be reconstructed from aggregate totals.'),card(c,e,by['phase-ii'],titles[2],volume)if has2 else missing(titles[2],'No Phase II objective trajectory is saved for this result. Available endpoints or research-round records are shown separately below.'),card(c,e,by['physical-flow'],titles[3],volume)if 'physical-flow'in by else missing(titles[3],'A complete physical-link projection of this result’s own upper solution is not established. No flow from another result is substituted.'),missing(titles[4],'An independent per-OD ungenerated-path pricing vector was not saved in this shared-core snapshot. The RMP pricing history and bound certificate below have their own meanings and gates.')]
 if sioux and c['city']=='sioux-falls':
  f=sioux['shared_certificates'][c['case_id']+'/'+e['evidence_id']]
  cards[4]=card(c,e,f,f['title'],volume)
 if layout=='original':
  indices=[1,3,4]if c['city']=='hong-kong'else[1,2,4];result=top+gallery([cards[i]for i in indices],3)
 else:result=top+gallery(cards[:2],2)+gallery(cards[2:],3)
 extras=[f for f in e['figures']if Path(f['src']).stem in ['bounds','nonbinding','pricing','research-rounds','checkpoint-pool','time-scope']]
 result+='<details class="cg-certificate-scope"'+(' open'if c['city']=='sioux-falls'else'')+'><summary>Saved certificates, RMP pricing and demand scope</summary>'+gallery([card(c,e,f,'RMP pool and pricing diagnostics'if Path(f['src']).stem=='pricing'else f['title'],volume)for f in extras],2)+'</details>'
 result+='<details class="cg-lineage"><summary>Demand, model identity, source and current limits</summary><p>'+esc(c['parent_note'])+'</p><p>'+esc(c['lineage']['release_rule'])+'</p><p>Upper producer: '+esc(str(e['upper_build']))+'; lower producer: '+esc(str(e['lower_build']))+'.</p><p>Saved global RMP pricing is not relabelled as independent per-OD complete-path pricing.</p></details>'
 result+='<p class="cg-evidence-links"><a href="'+pre+'assets/shared-cg-20261013/RESULT_CODE_INDEX.html#'+c['case_id']+'--'+e['evidence_id']+'">Code for this result</a> · <a href="'+pre+'assets/shared-cg-20261013/REPRODUCTION.html">Data, certificates and reproduction</a></p>'
 return result
for c in cat['cases']:
 c['selected_three']=c['city'] in selected_cities
 for e in c['evidence']:
  for volume in [False,True]:
   for layout in ['five','original']:e[('volume'if volume else'home')+'_'+layout+'_html']=panel(c,e,volume,layout)
   if c['selected_three']:e[('volume'if volume else'home')+'_selected_html']=panel(c,e,volume,'selected')
  e['home_html']=e['home_selected_html'if c['selected_three']else'home_five_html'];e['volume_html']=e['volume_selected_html'if c['selected_three']else'volume_five_html']
def controls(city):
 name=cat['cities'][city]
 return '<div class="cg-controls">'+''.join('<label>'+label+'<select '+attr+' aria-label="'+esc(name+' '+label)+'"></select></label>'for label,attr in [('OD scope / demand factor','data-cg-od'),('Time model / experiment','data-cg-case'),('Result version','data-cg-evidence')])+'</div>'
def component(city,volume=False):
 c=next(c for c in cat['cases']if c['case_id']==cat['defaults'][city]);e=next(e for e in c['evidence']if e['evidence_id']==c['default_evidence'])
 return '<section class="cg-component" id="shared-cg-'+city+'" data-cg-city="'+city+'" data-cg-volume="'+str(volume).lower()+'" data-cg-template="764e086">'+controls(city)+'<div class="cg-body">'+e['volume_html'if volume else'home_html']+'</div></section>'
presentation=copy.deepcopy(cat)
for c in presentation['cases']:
 for e in c['evidence']:e.pop('history',None)
(A/'catalog.js').write_text('window.MCL_CG_CATALOG='+json.dumps(presentation,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
for name in ['index.html','index-coverage-city.html','index-coverage-stage.html']:
 p=D/name;s=p.read_text(encoding='utf8')
 for city in cat['defaults']:
  span=component_span(s,city);assert span,city
  new=component(city)
  if city in refs and 'data-cg-template="764e086"'not in s[span[0]:s.index('>',span[0])+1]:
   s=s[:span[0]]+s[span[1]:];soup=BeautifulSoup(s,'html.parser');legacy=soup.select_one('section[data-stage="'+city+'-finite"] details.cg-legacy');assert legacy
   start=s.index('<details',s.index('id="'+city+'-finite"'));# Locate the actual legacy opening, not a card note.
   m=re.search(r'<details\b[^>]*class="cg-legacy"[^>]*>',s[start:]);assert m;start+=m.start();end=balanced(s,start,'details');s=s[:start]+new+s[end:]
  else:s=s[:span[0]]+new+s[span[1]:]
 s=re.sub(r'(shared-cg-20261013/(?:catalog.js|switch.js|style.css))\?v=[^"<> ]+',r'\1?v=20261014-cg-phase-ii-pair',s)
 s=re.sub(r'(assets/reading/atlas.js)(?:\?v=[^"<> ]+)?',r'\1?v=20261014-cg-phase-ii-pair',s);edit(p,s)
mdmap={'boston':'02-boston','hong-kong':'04-hong-kong','sioux-falls':'03-sioux-falls'}
for city in cat['defaults']:
 p=D/'volumes'/(city+'.html');s=p.read_text(encoding='utf8');span=component_span(s,city);assert span
 if city in refs and 'data-cg-template="764e086"'not in s[span[0]:s.index('>',span[0])+1]:
  s=s[:span[0]]+s[span[1]:];ref=refs[city];start=s.index('<h3 id="'+ref['volume_start']+'"');end=s.index('<h3 id="'+ref['volume_end']+'"');s=s[:start]+component(city,True)+s[end:]
 else:s=s[:span[0]]+component(city,True)+s[span[1]:]
 s=re.sub(r'(shared-cg-20261013/(?:catalog.js|switch.js|style.css))\?v=[^"<> ]+',r'\1?v=20261014-cg-phase-ii-pair',s);edit(p,s)
 p=D/'volumes'/(mdmap.get(city,city)+'.md');s=p.read_text(encoding='utf8');block='<!-- SHARED_CG_20261013_START -->\n'+component(city,True)+'\n<!-- SHARED_CG_20261013_END -->'
 if city in refs and 'data-cg-template="764e086"'not in s:
  s=re.sub(r'<!-- SHARED_CG_20261013_START -->.*?<!-- SHARED_CG_20261013_END -->','',s,flags=re.S);start=s.index('<span id="'+refs[city]['volume_start']+'"></span>');end=s.index('<span id="'+refs[city]['volume_end']+'"></span>');s=s[:start]+block+'\n\n'+s[end:]
 else:s,n=re.subn(r'<!-- SHARED_CG_20261013_START -->.*?<!-- SHARED_CG_20261013_END -->',lambda m:block,s,flags=re.S);assert n==1
 edit(p,s)
p=D/'index.md';s=p.read_text(encoding='utf8');s=re.sub(r'CG figure maintenance \(14 October\):.*?\n','CG figure maintenance (14 October): Boston, Hong Kong and Sioux Falls now use the selected three-card arrangement: Phase I total artificial flow beside the same-run per-OD heatmap, Phase II objective beside its signed relative gap to a fixed same-instance reference, and final physical-link movement flow. OD, time model and result selectors retain separate saved experiments; missing shared-core per-OD history is explicit. Independent pricing and earlier views remain in folded supporting records. [Per-result reproduction code](assets/shared-cg-20261013/RESULT_CODE_INDEX.html).\n',s);edit(p,s)
print('Integrated selected three-card CG layout for Boston, Hong Kong and Sioux Falls')
if __name__=='__main__':pass
