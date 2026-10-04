"""Build a no-JavaScript catalog from the same evidence-backed reader records."""
from pathlib import Path
import html,json,re
ROOT=Path(__file__).resolve().parents[1]
SITE='https://scholarhaozheng.github.io/mobility-network-lab/'
REPO='https://github.com/scholarhaozheng/mobility-network-lab/'
def esc(x):return html.escape(str(x),quote=True)
def link(url,label):return '<a href="'+esc(url)+'">'+esc(label)+'</a>'
def local(url):return url if url.startswith(('https://','http://')) else '../'+url

def main():
 text=(ROOT/'docs/assets/reproduction/data.js').read_text(encoding='utf-8')
 data=json.loads(text.removeprefix('window.MCL_REPRODUCTION=').strip().removesuffix(';'))
 out=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Static experiment catalog · Mobility Computation Lab</title><meta name="description" content="Browse every experiment, its supported commands, environment and verification evidence without JavaScript."><link rel="icon" href="../assets/mcl-globe.svg" type="image/svg+xml"><link rel="canonical" href="'+SITE+'reproduction/experiment-catalog.html"><meta property="og:type" content="website"><meta property="og:title" content="Static experiment catalog · Mobility Computation Lab"><meta property="og:description" content="Experiment status, data, commands and validation evidence without JavaScript."><meta name="twitter:card" content="summary"><link rel="stylesheet" href="../assets/presentation-r3.css"><link rel="stylesheet" href="../assets/fonts/dejavu-serif.css"><style>body{font-family:"DejaVu Serif",Georgia,serif}main{max-width:1080px}section{margin:30px 0;padding-top:12px;border-top:1px solid #ccd8df;scroll-margin-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%}td,th{padding:8px;text-align:left;vertical-align:top}.status{font-weight:bold}.notice{padding:12px;background:#f2f6f8}.record-index{max-height:28rem;overflow:auto}details{margin:12px 0}code{overflow-wrap:anywhere}</style></head><body><a class="skip-link" href="#catalog-main">Skip to main content</a><main class="mcl-page" id="catalog-main" tabindex="-1"><nav aria-label="Reproduction"><a href="../index.html">Home</a> · <a href="../reproduction.html">Reproduction guide</a> · <a href="../reproduce.html">Experiment catalog</a></nav><h1>Static experiment catalog</h1><p>This page uses the same statuses and evidence as the interactive catalog. It works without JavaScript. A verified workflow applies to the stated inputs and scope; inspecting historical output is not a new computation.</p><p><strong>Start here:</strong> <a href="../downloads/computational-checkout.zip">Download the computational checkout</a>, extract it and open a terminal in its root. Select an experiment below, follow its environment instructions, then run and verify into a new or empty output directory. <a href="'+REPO+'blob/main/REPRODUCTION_QUICKSTART.md">Read the quickstart</a>.</p><p>Documentation: 20261004-r18. Computational source, inputs and receipts retain their immutable r14 identities.</p><details class="record-index" open><summary>All experiment records</summary><ul>']
 names={'boston':'Boston','sioux-falls':'Sioux Falls','hong-kong':'Hong Kong','shared':'Public tools / controls'}
 for e in data['records']:
  s=e['reproductionStatus'];out.append('<li>'+link('#'+e['id'],names.get(e['city'],e['city'])+' · '+e['title'])+' — '+esc(s['label'])+'</li>')
 out.append('</ul></details>')
 for e in data['records']:
  s=e['reproductionStatus'];r=e.get('recipe');rr=e.get('recoveredRecipe');scope=s.get('scope') or e.get('scope') or ''
  out.append('<section id="'+esc(e['id'])+'"><h2>'+esc(e['title'])+'</h2><p>'+esc(names.get(e['city'],e['city']))+' / <code>'+esc(e['id'])+'</code></p><p class="status">'+esc(s['label'])+'</p><p>'+esc(scope if isinstance(scope,str) else json.dumps(scope))+'</p>')
  if s.get('externalInputsRequired'):out.append('<p class="notice">This workflow requires external source inputs. Its recorded validation covers the stated source snapshot or prepared inputs; obtain the exact required files before running.</p>')
  out.append('<p>'+link('../reproduce.html#'+e['id'],'Open this experiment in the interactive catalog')+'</p>')
  files=[m for m in e.get('materials',[]) if m.get('role') in ('frozen_input','upstream_source')]
  out.append('<details><summary>Data and exact input identities</summary><ul>')
  for m in files:
   url=m.get('downloadUrl') or m.get('sourceUrl') or m.get('browseUrl');name=m.get('path') or m.get('title') or 'Source data'
   out.append('<li>'+(link(url,name) if url else esc(name))+((' — SHA-256: <code>'+esc(m['sha256'])+'</code>') if m.get('sha256') else '')+'</li>')
  out.append('</ul><p>'+link(REPO+'blob/reproduction-2026-10-04-r14/DATA_LICENSES.md','Source attribution and data access terms')+'</p></details>')
  if r:
   env=r.get('environment',{});venv=env.get('venv') or '.venv';python='.\\'+venv+'\\Scripts\\python.exe';version=env.get('setup_python') or '3.12';requirements=env.get('requirements') or 'requirements-tested.txt'
   command='py -'+version+' -m venv '+venv+'\n'+python+' -m pip install -r '+requirements+'\n'
   if r.get('setup',{}).get('windows'):command+='\n'+r['setup']['windows']+'\n'
   command+='\n'+python+' tools/mcl_reproduction_check.py --experiment '+r['id']+' --environment\n'+python+' tools/mcl_reproduce.py describe '+r['id']+'\n'+python+' tools/mcl_reproduce.py run '+r['id']+' --output results/'+r['id']+'\n'+python+' tools/mcl_reproduce.py verify '+r['id']+' --run results/'+r['id']
   out.append('<details><summary>Environment, run and verification commands (Windows PowerShell)</summary><p>Use the required interpreter and any native prerequisites below. Validation was performed on Windows; other platforms are not certified by these receipts.</p><pre><code>'+esc(command)+'</code></pre>')
   if r.get('setupGuideUrl'):out.append('<p>'+link(local(r['setupGuideUrl']),'Native environment instructions')+'</p>')
   if r.get('setup',{}).get('note'):out.append('<p>'+esc(r['setup']['note'])+'</p>')
   out.append('</details><details><summary>Expected results and acceptance thresholds</summary><p>'+esc(r.get('verificationSummary',''))+'</p><pre>'+esc(json.dumps({'metrics':r.get('metrics',{}),'tolerances':r.get('tolerances',{})},indent=2))+'</pre></details>')
  elif rr:
   out.append('<details><summary>Environment and supported commands</summary><p>Use the exact environment documented for this workflow. Activate the created environment before the commands below; python must resolve to that environment, not the system interpreter.</p>')
   if rr.get('guideUrl'):out.append('<p>'+link(rr['guideUrl'],'Environment and method instructions')+'</p>')
   setup=rr.get('environment',{}).get('setup') or rr.get('environment',{}).get('instructions')
   hk_native=e['id'].startswith('HK-H1-L3-')
   if hk_native:
    native=next(x['recipe'] for x in data['records'] if x.get('recipe',{}).get('id')=='boston-native-l3-ranks26-52')
    setup='py -3.12 -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -r requirements-tested.txt\n\n'+native['setup']['windows'].replace('Clean installation and both native ranks were verified.','Install the pinned native environment; a fresh Hong Kong native rerun is not certified by this setup text.')
    out.append('<p>Windows PowerShell: the controller uses the native Python 3.9 interpreter and IPOPT configured by these commands. Conda is required.</p>')
   if e['city']=='boston' and setup:
    setup=('\n'.join(setup) if isinstance(setup,list) else setup)+'\npython -m pip install PyYAML==6.0.3'
   if e['id'].startswith('sioux-cg-'):
    setup='py -3.11 -m venv .venv-legacy-recovered\npython -m pip install -r requirements-reproduction-public-controls.txt\npython -m pip install PyYAML==6.0.3'
   command_python='python'
   if setup and not hk_native:
    setup='\n'.join(setup) if isinstance(setup,list) else setup
    match=re.search(r'-m venv (\S+)',setup)
    if match:
     command_python='.\\'+match[1]+'\\Scripts\\python.exe'
     setup='\n'.join(command_python+line[6:] if line.startswith('python ') and '-m venv ' not in line else line for line in setup.splitlines())
     out.append('<p>Windows PowerShell: these commands call the created environment interpreter explicitly; activation is not required.</p>')
   if not setup:out.append('<pre><code>'+esc(json.dumps(rr.get('environment',{}),indent=2))+'</code></pre>')
   if setup:out.append('<pre><code>'+esc('\n'.join(setup) if isinstance(setup,list) else setup)+'</code></pre>')
   out.append('<p>Run computes a new result; inspect checks retained evidence. A workflow without a run action cannot be newly computed through this entry.</p>')
   for action,command in rr.get('commands',{}).items():
    if not hk_native and command.startswith('python '):command=command_python+command[6:]
    if hk_native:
     command=command.replace('python -B', '& (Join-Path $nativePrefix '+chr(39)+'python.exe'+chr(39)+') -B',1)
     if action=='run':command+=' --ipopt "$env:MCL_IPOPT"'
    out.append('<h3>'+esc(action.title())+'</h3><pre><code>'+esc(command)+'</code></pre>')
   out.append('<p>'+link(rr['manifestUrl'],'Exact configuration, inputs, outputs and validation contract')+'</p></details>')
  else:out.append('<p>No supported run command is registered for this record. See the scope and remaining requirements before attempting a historical reconstruction.</p>')
  if rr and rr.get('verificationMetrics'):
   out.append('<details><summary>Recorded verification metrics for this scope</summary><pre>'+esc(json.dumps(rr['verificationMetrics'],indent=2))+'</pre></details>')
  if s.get('receiptUrl'):out.append('<p>'+link(local(s['receiptUrl']),'Execution or inspection evidence')+'</p>')
  if e.get('missing'):out.append('<details><summary>Remaining requirements</summary><ul>'+''.join('<li>'+esc(m if isinstance(m,str) else json.dumps(m))+'</li>' for m in e['missing'])+'</ul></details>')
  out.append('<p>'+link('#catalog-main','Back to experiment index')+'</p></section>')
 out.append('</main></body></html>\n')
 dest=ROOT/'docs/reproduction/experiment-catalog.html';dest.write_bytes(''.join(out).encode('utf-8'))
 print(json.dumps({'status':'PASS','records':len(data['records']),'verified':sum(e['reproductionStatus']['verified'] for e in data['records']),'destination':dest.relative_to(ROOT).as_posix()}))
if __name__=='__main__':main()
