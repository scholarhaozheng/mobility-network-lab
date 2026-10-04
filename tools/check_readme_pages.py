#!/usr/bin/env python3
"""Validate the current reading homepage, four volumes and reproducibility entry.

The retired preview-table/220px contracts are replaced by the approved text-only
coverage table and canonical atlas/volume links. Historical scientific source,
statistics and scope guards remain below; publication_gate.py additionally
validates frozen payloads and the dated presentation record.
"""
from __future__ import annotations
import hashlib, html, json, re
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'

def read(p):return p.read_text(encoding='utf8')
def refs(text):return re.findall(r'\]\(([^)]+)\)',text)+re.findall(r'(?:href|src|data-reproduction-base)=[\"\']([^\"\']+)',text)
def images(text):return re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)+re.findall(r'<img\b[^>]*\bsrc=[\"\']([^\"\']+)',text)
def target(source,raw):
 u=urlsplit(html.unescape(raw))
 if u.scheme or u.netloc:return None,''
 return ((source.parent/unquote(u.path)).resolve() if u.path else source.resolve()),unquote(u.fragment)
_CACHE={}
def ids(p):
 if p not in _CACHE:
  text=read(p) if p.is_file() else ''
  found=set(re.findall(r'\bid=["\']([^"\']+)',text))
  if p.suffix=='.md':
   for title in re.findall(r'^#{1,6}\s+(.+)$',text,re.M):found.add(re.sub(r'[^\w\s-]','',title.lower()).replace(' ','-'))
  _CACHE[p]=found
 return _CACHE[p]

def main():
 errors=[];checks=0
 def check(ok,message):
  nonlocal checks
  checks+=1
  if not ok:errors.append(message)
 readme=read(ROOT/'README.md');home=read(DOCS/'index.html');s=BeautifulSoup(home,'html.parser')
 headings=['01 / What this project adds','02 / Complete project structure','03 / Case coverage and selected evidence','04 / Explore the three cases','05 / Run and inspect','06 / Attribution, scope and further reading']
 check(all(x in readme and x in home for x in headings),'Six-block research entry missing')
 for needle in ('[Hao Zheng](https://scholarhaozheng.github.io/)','under the guidance of **[Professor Xuesong Zhou](https://search.asu.edu/profile/2182101)**','[General Modeling Network Specification (GMNS)](https://github.com/zephyr-data-specs/GMNS)','[TAPLab: An Open Laboratory for Reproducible Traffic Assignment Experiments](https://github.com/asu-trans-ai-lab/TAPLab)','official [tap-b Algorithm B](https://github.com/spartalab/tap-b)','Project-specific work includes assembling and adapting the Boston, Sioux Falls, and Hong Kong cases'):
  check(needle in readme,'Author/upstream attribution missing: '+needle)
 for phrase in ('City-to-model representations','Computational implementations and diagnostics','Reusable cross-city computational tools'):
  check(phrase in home and phrase in readme and phrase in read(DOCS/'contributions.md'),'Contribution missing: '+phrase)
 check('TAPLite' not in readme+home,'Algorithm B incorrectly named TAPLite')
 check('Controlled cross-instance evidence' not in readme+read(DOCS/'contributions.md'),'Rejected contribution wording returned')
 check('model-generated' in readme and 'calibrated citywide forecast' in readme,'Bounded evidence scope missing')
 check('These evidence layers are not additive' in readme and '0.3.0-rc5' in readme and 'separately versioned' in readme,'Open-data/generic-engine version scope missing')
 for ref in ('REPRODUCTION_QUICKSTART.md','experiments/README.md','tools/mcl_reproduce.py','reproduce.html','reproduction.html'):
  check(ref in readme,'README code/data/run/verification entry missing: '+ref)
 check('mcl_reproduce.py list' in readme,'README runner command missing')
 for city in ('overview','boston','sioux-falls','hong-kong'):
  check(f'volumes/{city}.html' in home,'Homepage volume entry missing: '+city)
 for legacy in ('framework','coverage','cg-experiments','boston','sioux-falls','hong-kong'):
  check(s.find(id=legacy) is not None,'Homepage compatibility anchor missing: '+legacy)
 matrix=s.select_one('table.coverage-matrix')
 check(matrix is not None and len(matrix.select('tbody tr:not(.matrix-group)'))==19,'Coverage matrix must have nineteen text rows')
 check(matrix is not None and not matrix.find('img'),'Section 03 must be text-only')
 for row in matrix.select('tbody tr:not(.matrix-group)') if matrix else []:
  check(len(row.find_all(['th','td'],recursive=False))==4,'Coverage row must compare exactly three cities')
 cards=s.select('.atlas-card[data-figure]');check(len(cards)==80,'Homepage retains 80 cards after two L3 reference comparisons move to long volumes')
 check(not any(c['data-figure'].lower()=='g-f115' for c in cards),'Saved Sioux column belongs only in the long volume')
 volumes={city:BeautifulSoup(read(DOCS/f'volumes/{city}.html'),'html.parser') for city in ('overview','boston','sioux-falls','hong-kong')}
 for city,cid,slug in [('boston','C-BOSTON-ABS-L3','c-boston-abs-l3'),('hong-kong','C-HK-L3-STATIC','c-hk-l3-static')]:
  check(not any(c['data-figure']==cid for c in cards),'L3 reference comparison must remain in long volume: '+cid)
  check(volumes[city].find(id='stage-13-native-l3--'+slug) is not None,'L3 figure lost from long volume: '+cid)
  check(s.find('a',href='volumes/'+city+'.html#stage-13-native-l3--'+slug) is not None,'L3 long-volume entry missing: '+cid)
 for c in cards:
  image=c.find('img');anchor=c.select_one('a.atlas-image-link') or (image.find_parent('a') if image else None)
  check(bool(image and anchor),'Atlas card lacks linked image: '+c['data-figure'])
  if not anchor:continue
  dest,fragment=target(DOCS/'index.html',anchor.get('href',''))
  check(dest.is_file() and fragment in ids(dest),'Atlas image does not reach exact volume figure: '+c['data-figure'])
  if dest.is_file():
   vol=volumes.get(dest.stem);figure=vol.find(id=fragment) if vol else None
   if figure and not figure.find('img'):figure=figure.find_next('figure')
   target_imgs=figure.find_all('img') if figure else []
   source_image=target(DOCS/'index.html',image['src'])[0]
   check(any(target(dest,im['src'])[0]==source_image for im in target_imgs),'Linked volume does not display same figure: '+c['data-figure'])
 for city,vol in volumes.items():
  check(vol.html.get('lang')=='en','Volume language must be English: '+city)
  check(vol.find('a',href='../index.html') is not None,'Volume back link missing: '+city)
  check(vol.find(id='current-reproduction') is not None,'Volume current reproduction status missing: '+city)
  numbers={'overview':'01','boston':'02','sioux-falls':'03','hong-kong':'04'}
  md=DOCS/f'volumes/{numbers[city]}-{city}.md'
  check(md.is_file(),'Downloadable reading volume missing: '+city)
  if md.is_file():
   markdown=read(md)
   for img in vol.find_all('img'):check(img['src'] in markdown,'Markdown export lost volume image: '+city+' '+img['src'])
  check('not yet part of the public GitHub release' not in str(vol) and 'Independent review draft' not in str(vol),'Review-only label in public volume: '+city)
 sioux=volumes['sioux-falls'];check(len(sioux.select('figure[data-instance-od="200"]'))==9 and len(sioux.select('figure[data-instance-od="250"]'))==9,'Sioux must retain nine figures per finite instance')
 check(sioux.find(attrs={'data-figure':'G-F115'}) is not None or 'g-f115.svg' in str(sioux),'Saved generated column missing from Sioux volume')
 for needle in ('supplied vehicle OD','mode choice','historical Sioux CG','assignment stage only'):
  check(needle.lower() in readme.lower(),'Reproduction scope disclosure missing: '+needle)
 css=read(DOCS/'assets/reading/atlas.css');check('DejaVu Serif' in css and 'ui-monospace' in css,'Homepage serif/monospace typography contract missing')
 for name in ('DejaVuSerif.ttf','DejaVuSerif-Bold.ttf','LICENSE-DejaVu.txt','dejavu-serif.css'):
  check((DOCS/'assets/fonts'/name).is_file(),'Shared licensed font asset missing: '+name)
 model_js=read(DOCS/'assets/reading/atlas-data.js');model=json.loads(model_js.split('=',1)[1].strip().rstrip(';'))
 check(len(model['cities'])==3,'Atlas runtime must contain all three cities')
 app=read(DOCS/'assets/reading/atlas.js');check(all(x in app for x in ('atlas-view','sioux-od','av-stage-jumpbar')),'Atlas view/stage/instance controls missing')
 diagram=DOCS/'assets/atlas/project-map.svg';svg=read(diagram)
 check(svg.count('href=')>=26,'Clickable project map modules missing')
 for raw in re.findall(r'(?:xlink:)?href="([^"]+)"',svg):
  p,fragment=target(diagram,raw)
  if p:check(p.is_file() and (not fragment or fragment in ids(p)),'Broken project-map destination: '+raw)
 # Frozen source record guards preserved from the earlier checker.
 source=json.loads(read(DOCS/'assets/project_structure_r3/project_structure.source.json'))
 hashes={'docs/assets/project_structure_r3/project_structure_model.json':source['model_sha256'],'docs/assets/project_structure_r2/project_structure_model.json':source['source_ledger_sha256'],'tools/visuals/render_project_structure_r3.py':source['renderer_sha256'],**source['outputs_sha256']}
 for rel,expected in hashes.items():check((ROOT/rel).is_file() and hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,'Historical project-map source/output hash mismatch: '+rel)
 walk=read(DOCS/'full-walkthrough.md');cg=read(DOCS/'methods/space-time-cg.md');capabilities=read(DOCS/'capabilities.md')
 check('77-arc' in walk and 'model-generated' in walk.lower(),'Historical walkthrough lost bounded HK10 disclosure')
 for title in ('### A. City-data and GMNS statistics','### B. Static-assignment statistics','### C. Finite time-expanded statistics'):
  check(title in capabilities and title in walk,'Original comparable statistics lost: '+title)
 for needle in ('| **Phase I** |','| **Phase II** |','| **Pricing certificate** |','boston_sioux_cg_parallel_overview.png'):
  check(needle in cg and needle in walk,'Historical CG technical evidence missing: '+needle)
 check('<a id="cg-experiments"></a>' in cg,'Historical CG compatibility anchor missing')
 for metric in ('11,422','2,959','2,465','1,516','13 standards'):check(metric in walk,'Historical open-data evidence lost: '+metric)
 check(len(images(walk))>=74,'Historical walkthrough figures lost')
 for raw in images(walk):
  p,_=target(DOCS/'full-walkthrough.md',raw);check(p is not None and p.is_file(),'Missing historical walkthrough figure: '+raw)
 for rel,needle in (('docs/cases/boston-admm.md','convergence_Boston_10OD.png'),('docs/cases/sioux-admm.md','convergence_Sioux_200OD.png'),('docs/cases/sioux-admm.md','convergence_Sioux_250OD.png'),('docs/cases/boston-algorithm-b.md','boston_b1_fw_flow_compact.svg'),('docs/cases/sioux-algorithm-b.md','sioux_fw_flow_compact.svg'),('docs/cases/boston.md','endpoint_all_coverage.png'),('docs/architecture.md','framework_overview.png')):
  check(needle in read(ROOT/rel),'Historical canonical evidence missing: '+rel)
 # Validate every local file target; exact fragments on the maintained reading surfaces.
 pages=sorted(DOCS.rglob('*.html'))
 current={DOCS/'index.html',DOCS/'reproduce.html',DOCS/'reproduction.html',DOCS/'reproduction/experiment-catalog.html',*(DOCS/'volumes').glob('*.html')}
 inventory=DOCS/'assets/reproduction/inventory.json';record_ids=set()
 if inventory.is_file():
  data=json.loads(read(inventory));records=data.get('experiments',data.get('records',[])) if isinstance(data,dict) else data
  record_ids={x.get('id') for x in records if isinstance(x,dict)}
 for p in [ROOT/'README.md',DOCS/'index.md',*(DOCS/'volumes').glob('0*.md'),*pages]:
  text=read(p)
  if p in current:
   check(not re.search(r'https?://(?:localhost|127\.0\.0\.1)|[A-Z]:[\\/]|(?:href|src)=[\"\']/?reading/|stage[34]/20261004',text),'Machine-specific or draft route in publication: '+str(p.relative_to(ROOT)))
   if p.suffix=='.html':
    soup=BeautifulSoup(text,'html.parser');all_ids=[t['id'] for t in soup.find_all(id=True)]
    check(len(all_ids)==len(set(all_ids)),'Duplicate HTML IDs: '+str(p.relative_to(ROOT)))
    check(soup.find('link',rel='icon') is not None,'Missing favicon: '+str(p.relative_to(ROOT)))
  for raw in refs(text):
   if raw.startswith(('javascript:','data:')):continue
   check(raw.count('#')<=1,'Multiple fragments in link: '+str(p.relative_to(ROOT))+' '+raw)
   dest,fragment=target(p,raw)
   if dest is None:continue
   check(dest.exists(),'Broken local target: '+str(p.relative_to(ROOT))+' -> '+raw)
   if fragment and (p in current or p.suffix=='.md') and dest.suffix in ('.html','.md') and dest.is_file():
    dynamic=dest==DOCS/'reproduce.html' and fragment in record_ids
    check(dynamic or fragment in ids(dest),'Broken local fragment: '+str(p.relative_to(ROOT))+' -> '+raw)
 print(json.dumps({'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors,'home_cards':len(cards),'coverage_rows':19,'volumes':4,'pages_html_files':len(pages),'historical_scientific_guards_retained':True,'visual_qa_performed':False},indent=2))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
