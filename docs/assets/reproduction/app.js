(function () {
'use strict';
const D = window.MCL_REPRODUCTION;
if (!D || !Array.isArray(D.records) || !D.records.every(e => e.reproductionStatus)) {
  window.mclCatalogFailure?.();
  return;
}
const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const objectText = x => typeof x === 'string' ? x : JSON.stringify(x, null, 2);
const names = {boston:'Boston','sioux-falls':'Sioux Falls','hong-kong':'Hong Kong',shared:'Public tools / controls'};
const params = new URLSearchParams(location.search);
const hashId = () => { try { return decodeURIComponent(location.hash.slice(1)); } catch { return ''; } };
let figure = params.get('figure'), selected = hashId(), platform = 'windows';
const list = document.getElementById('experiment-list'), detail = document.getElementById('experiment');
const status = e => e.reproductionStatus.label;
const verified = e => e.reproductionStatus.verified === true;
const recordLink = id => '#'+encodeURIComponent(id);
const gitCommands = 'git clone -c core.autocrlf=false '+D.repository+'.git\ncd mobility-network-lab\ngit checkout reproduction-2026-10-04-r14\ngit rev-parse HEAD';
document.getElementById('setup-command').textContent = gitCommands;
document.getElementById('release-state').textContent = 'Website and documentation: r18.1 · Computational recipes and evidence: r14 · '+D.records.filter(verified).length+' verified-run records / '+D.records.length+' records';
if (figure && !D.figures[figure]) figure = null;
if (params.get('pilots') === '1' || params.get('ready') === '1') document.getElementById('ready').checked = true;
function context() {
  const f = D.figures[figure], el = document.getElementById('figure-context');
  if (!f) { el.innerHTML = ''; return; }
  el.innerHTML = '<section class="figure-context">'+(f.publishedAsset?'<a href="'+esc(f.publishedAsset)+'"><img src="'+esc(f.publishedAsset)+'" alt="'+esc(f.title)+'"></a>':'')+'<div><h2>'+esc(f.title)+'</h2><p>'+esc(f.reason)+'</p><p>'+f.experimentIds.length+' linked experiment or preparation records. Select the exact method, scale and version.</p>'+((f.referenceIds||[]).length?'<p>Comparison baseline: '+f.referenceIds.map(id=>'<a href="'+recordLink(id)+'">'+esc(D.records.find(e=>e.id===id)?.title||id)+'</a>').join(' · ')+'</p>':'')+'<button id="show-all" type="button">Browse all records</button></div></section>';
  document.getElementById('show-all').onclick = () => { figure=null; context(); renderList(); syncFilters(); };
}
function materialGroups(e){return[['frozen_input','Frozen computational inputs'],['upstream_source','Original sources and access'],['expected_result','Expected results and validation evidence'],['display_evidence','Display and provenance evidence'],['mixed_bundle','Mixed bundle: inspect input and output roles'],['unresolved','Material role not yet resolved']].map(([role,label])=>{const ms=e.materials.filter(m=>m.role===role);return ms.length?'<details class="material-group"'+''+'><summary>'+label+' · '+ms.length+'</summary><ul class="material-list">'+ms.map(m=>'<li><span class="path">'+esc(m.path||m.title)+'</span><span class="note">'+esc(m.note)+'</span><div class="material-actions">'+(m.browseUrl?'<a href="'+esc(m.browseUrl)+'" target="_blank" rel="noopener">Browse</a>':'')+(m.downloadUrl?'<a href="'+esc(m.downloadUrl)+'" target="_blank" rel="noopener">Download file</a>':'')+(m.localAddition?'<span class="note">Included in the computational checkout; verify the listed SHA-256.</span>':'')+(m.sourceUrl?'<a href="'+esc(m.sourceUrl)+'" target="_blank" rel="noopener">Source / access instructions</a>':'')+'</div>'+(m.sha256?'<details><summary>SHA-256</summary><code>'+esc(m.sha256)+'</code></details>':'')+'</li>').join('')+'</ul></details>':''}).join('')}
function recoveredData(r){const ds=r?.dataSources||[];return ds.length?'<details class="material-group"><summary>Data sources and retained evidence</summary><ul class="material-list">'+ds.map(s=>'<li><span class="path">'+esc(s.path||s.name||s.id||'Source snapshot')+'</span><p class="small">Role: '+esc((s.role||s.mode||'upstream source').replaceAll('_',' '))+'</p><p>'+esc(s.note||s.instructions||s.mode||'')+'</p>'+((s.url||s.sourceUrl)?'<a href="'+esc(s.url||s.sourceUrl)+'">Source / download</a>':'')+(s.sha256?'<details><summary>Required historical SHA-256</summary><code>'+esc(s.sha256)+'</code></details>':'')+'</li>').join('')+'</ul></details>':'';}
function commandBlock(title, command) {
  return '<div class="commands"><p class="command-label">'+esc(title)+'</p><button class="copy-command" type="button" aria-label="Copy '+esc(title.toLowerCase())+'">Copy</button><pre><code>'+esc(command)+'</code></pre></div>';
}
function pythonPath(venv) { return platform==='windows'?'.\\'+venv+'\\Scripts\\python.exe':venv+'/bin/python'; }
function venvSetup(version, venv, packages, requirements) {
  const python=pythonPath(venv), launcher=platform==='windows'?'py -'+version:'python'+version;
  return launcher+' -m venv '+venv+'\n'+python+' -m pip install '+(requirements?'-r '+requirements:packages)+'\n'+python+' --version';
}
function runtimeNote(r, recovered) {
  const env=r.environment||{};
  return '<p class="small">'+esc(recovered?(env.note||env.testedExecution||'Use the recorded environment and recipe-specific prerequisites. A clean installation of this environment was not certified by this delivery.'):'Run validation was performed on Windows. The POSIX command form is supplied where supported; macOS and Linux have not been independently validated for this recipe.')+'</p>'+(r.setupGuideUrl?'<p><a href="'+esc(r.setupGuideUrl)+'">Native environment installation guide</a></p>':'')+(r.setup?.note?'<p class="small">'+esc(r.setup.note)+'</p>':'')+(r.setupValidationReceiptUrl?'<p><a href="'+esc(r.setupValidationReceiptUrl)+'">Clean installation and rerun receipt</a></p>':'');
}
function workflow(e) {
  const recovered=!e.recipe && !!e.recoveredRecipe, r=e.recipe||e.recoveredRecipe;
  if (!r) return null;
  const env=r.environment||{}, result={r,recovered,canRun:e.reproductionStatus.runAvailable,blocked:false};
  if (!recovered) {
    const venv=env.venv||'.venv', version=env.setup_python||'3.12';
    result.python=pythonPath(venv);
    result.setup=venvSetup(version,venv,'',env.requirements||'requirements-tested.txt');
    result.environment='Python '+(env.tested_versions?.python||version)+' · '+(env.requirements||'requirements-tested.txt');
    if (r.supportedPlatforms && !r.supportedPlatforms.includes(platform)) { result.blocked=true; result.setup='# This recipe requires Windows. Select Windows PowerShell above.'; }
    else if(r.setup?.[platform]) result.setup+='\n\n'+r.setup[platform];
    const p=result.python+' tools/mcl_reproduce.py';
    result.check=result.python+' tools/mcl_reproduction_check.py --experiment '+r.id+' --environment\n'+p+' describe '+r.id;
    result.run=p+' run '+r.id+' --output ../results/'+r.id;
    result.verify=p+' verify '+r.id+' --run ../results/'+r.id;
    result.output='../results/'+r.id;
    return result;
  }
  let version='3.12',venv='.venv-recovered',requirements='requirements-tested.txt',packages='',extra='';
  if (e.city==='boston') {
    version='3.11';venv='.venv-boston-recovered';requirements='';
    packages='numpy==1.24.3 scipy==1.10.1 pandas==1.5.3 networkx==3.1 shapely==2.1.2 PyYAML==6.0.3';
  } else if (e.id==='TOOL-CITY-EVIDENCE-QUERY') {
    version='3.11';venv='.venv-public-controls';requirements='requirements-reproduction-public-controls.txt';
  } else if (e.id==='HK-H1-FINITE' || /^sioux-(native|cg)-/.test(e.id)) {
    version='3.11';venv='.venv-legacy-recovered';requirements='requirements-reproduction-public-controls.txt';
  } else if (e.id==='HK-H1-FW') {
    version='3.9';venv='.venv-hk-h1-fw';requirements='';packages='numpy==2.0.2';
  }
  result.python=pythonPath(venv);
  result.environment='Python '+version+' · '+(requirements||packages);
  result.setup=venvSetup(version,venv,packages,requirements);
  if(/^sioux-cg-/.test(e.id)) {
    result.setup+='\n'+result.python+' -m pip install PyYAML==6.0.3';
    result.environment+='; PyYAML 6.0.3';
  }
  const native=/^sioux-native-/.test(e.id)||/^HK-H1-L3-/.test(e.id);
  if(native) {
    if(platform!=='windows') { result.blocked=true; result.setup='# Fresh native computation uses the recorded Windows toolchain. Select Windows PowerShell.'; }
    else {
      const nativeRecipe=D.records.find(x=>x.recipe?.id==='boston-native-l3-ranks26-52')?.recipe;
      if(nativeRecipe?.setup?.windows) {
        extra=nativeRecipe.setup.windows.replaceAll('.\\.venv\\Scripts\\python.exe',result.python).replaceAll('native-boston','native-recovered').replace('Clean installation and both native ranks were verified.','The extended native environment was not freshly installed or solved for this record.');
        if(e.city==='sioux-falls') extra+='\n& (Join-Path $nativePrefix \'python.exe\') -m pip install -r algorithms/recovered_sioux/native-additions.txt';
        result.setup+='\n\n'+extra;
        result.environment+='; native child Python 3.9.25 / IPOPT 3.14.19';
        if(e.city==='hong-kong') result.python="& (Join-Path $nativePrefix 'python.exe')";
      }
    }
  }
  if(e.id==='sioux-taplab-official-parity') result.setup+='\n\n# Install '+(platform==='windows'?'Zig 0.15.1':'a C compiler')+' and put it on PATH.\n'+result.python+' tools/reproduction/build_tapb.py --compiler '+(platform==='windows'?'zig':'cc')+' --output .mcl-runtime/tap-b';
  const withPython=command=>String(command||'').replace(/^python\b/,result.python);
  result.check=withPython(r.checkCommand)+'\n'+result.python+' -B tools/mcl_recovered.py describe '+r.id;
  result.run=withPython(r.commands?.run);
  if(native && e.city==='hong-kong' && platform==='windows' && result.run) result.run+=' --ipopt "$env:MCL_IPOPT"';
  result.verify=withPython(r.commands?.verify);
  result.inspect=withPython(r.commands?.inspect);
  result.output=(r.commands?.run||r.commands?.inspect||'').match(/--output\s+(\S+)/)?.[1]||'';
  result.inspectionVerify=result.inspect?result.python+' -B tools/mcl_recovered.py verify '+r.id+' --run '+(r.commands.inspect.match(/--output\s+(\S+)/)?.[1]||''):'';
  return result;
}
function evidence(e,w) {
  const r=w?.r, s=e.reproductionStatus;
  let content='<p>'+esc(r?.verificationSummary||s.scope||e.scope)+'</p><p class="small">Evidence basis: '+esc(s.evidenceBasis||'No execution evidence registered')+'.</p>';
  const metrics=r?.metrics||r?.verificationMetrics;
  if (metrics) content+='<table class="metrics"><thead><tr><th>Check</th><th>'+ (s.verified?'Recorded verified result':'Retained-state check') +'</th></tr></thead><tbody>'+Object.entries(metrics).map(([k,v])=>'<tr><td>'+esc(k)+'</td><td>'+esc(objectText(v))+'</td></tr>').join('')+'</tbody></table>';
  if (r?.verificationChecks) content+='<details class="material-group"><summary>Independent verification checks</summary><ul class="result-list">'+Object.entries(r.verificationChecks).map(([name,passed])=>'<li>'+esc(name)+': '+(passed?'passed':'not passed')+'</li>').join('')+'</ul></details>';
  if (r?.tolerances) content+='<details class="material-group"><summary>Acceptance thresholds</summary><pre><code>'+esc(objectText(r.tolerances))+'</code></pre></details>';
  if(s.receiptUrl) content+='<p><a href="'+esc(s.receiptUrl)+'">'+(s.verified?'Execution and independent verification receipt':'Recorded evidence and checks')+'</a></p>';
  if(w?.recovered) content+='<p>The output directory contains execution metadata and <code>verification.json</code>. Check the verification result and its evidence basis: a saved-state inspection is not a fresh solve. <a href="'+esc(r.manifestUrl)+'">The exact recipe</a> and the linked receipt list the available numerical checks and result files.</p>';
  return content;
}
function openRecord(e) {
  const w=workflow(e), r=w?.r, s=e.reproductionStatus;
  detail.innerHTML='<p class="section-label">'+esc(names[e.city])+' / '+esc(e.id)+'</p><h2 id="record-title" tabindex="-1">'+esc(e.title)+'</h2><p class="instance">'+esc(objectText(e.instance))+'</p><span class="state '+(verified(e)?'ready':'gap')+'">'+esc(status(e))+'</span>'+(s.externalInputsRequired?'<span class="state gap">Additional source inputs required</span>':'')+'<p class="scope">'+esc(objectText(s.scope||e.scope))+'</p>'+
    '<nav class="record-jumps" aria-label="Reproduction steps"><button type="button" data-jump="data-step">Download &amp; data</button><button type="button" data-jump="environment-step">Environment</button><button type="button" data-jump="run-step">Run</button><button type="button" data-jump="verify-step">Verify</button><button type="button" data-jump="results-step">Expected result</button></nav>'+
    '<p class="run-notice">'+esc(s.verified?'This scoped computation has an execution receipt and passed independent checks. Follow its exact inputs and acceptance criteria below.':s.runAvailable?'A computation command is available. Its fresh result has not been independently verified in the recorded delivery; retained-state checks remain separate.':'No fresh computation command is registered for this record. The available source material and any saved-evidence inspection route are retained below.')+'</p>'+
    '<h3 id="data-step">1. Download and prepare data</h3><p><a href="downloads/computational-checkout.zip">Download the computational checkout</a>, extract it, and open a terminal in the folder containing <code>tools</code> and <code>experiments</code>. Included inputs and reference outputs are pinned by their file hashes. '+(s.externalInputsRequired?'This record also needs the exact external snapshots listed below; current provider downloads may not match the historical hashes.':'Use the included frozen inputs for this recipe.')+'</p><details class="material-group"><summary>Git alternative and computation version</summary><pre><code>'+esc(gitCommands)+'</code></pre><p>Computation release: <code>reproduction-2026-10-04-r14</code>. Record your checkout commit and retain the download manifest with your results.</p></details>'+materialGroups(e)+recoveredData(e.recoveredRecipe)+
    '<h3 id="environment-step">2. Set up this experiment’s environment</h3>'+(w?'<div class="platform-label"><label for="platform">Shell</label><select id="platform"><option value="windows"'+(platform==='windows'?' selected':'')+'>Windows PowerShell</option><option value="posix"'+(platform==='posix'?' selected':'')+'>macOS / Linux shell (not validated)</option></select></div><p>'+esc(w.environment)+'</p><p class="small">Run from the checkout root. These commands call the environment’s interpreter explicitly; activation is not required. Reuse this environment after setup.</p>'+commandBlock('Environment setup',w.setup)+runtimeNote(r,w.recovered)+(r.guideUrl?'<p><a href="'+esc(r.guideUrl)+'">Recipe-specific setup and data instructions</a> · <a href="'+esc(r.manifestUrl)+'">Pinned recipe and file hashes</a></p>':'')+(w.recovered&&r.environment?.freshRun?'<p class="small">'+esc(r.environment.freshRun)+'</p>':''):'<p>No executable environment is registered for this record. Consult the source evidence and remaining requirements below.</p>')+
    '<h3 id="run-step">3. Compute a new result</h3>'+(w?.canRun&&!w.blocked?'<p>Use a new or empty output directory. The preflight checks source and input identity; <code>run</code> executes this record’s computation.</p>'+commandBlock('Check inputs and inspect the recipe',w.check)+(s.externalInputsRequired?'<p class="run-notice">Obtain the exact inputs using the source instructions above before running. Keep the required directory layout and use the shown <code>--input-root</code>, or replace it with your prepared source directory.</p>':'')+commandBlock('Run computation',w.run):'<p>'+(w?.blocked?'Fresh execution requires the Windows environment documented above.':'No fresh run command is available for this record. Inspection, where available, is listed separately below.')+'</p>')+
    '<h3 id="verify-step">4. Verify the new result</h3>'+(w?.canRun&&!w.blocked?'<p>Verify the same output directory after the run. Verification does not start a new optimizer.</p>'+commandBlock('Verify computation',w.verify):'<p>No new computation is claimed by this record. Use the documented evidence checks below.</p>')+
    '<h3 id="results-step">5. Read the expected result and limits</h3>'+(w?.output?'<p>Result directory: <code>'+esc(w.output)+'</code>.</p>':'')+evidence(e,w)+
    ((e.missing||[]).length?'<details class="material-group"><summary>Remaining requirements and scope limits</summary><ul class="result-list">'+e.missing.map(m=>'<li>'+esc(typeof m==='string'?m:m.detail||m.note||objectText(m))+'</li>').join('')+'</ul></details>':'')+
    (w?.inspect?'<details class="material-group"><summary>Inspect historical evidence instead of computing</summary><p>This checks retained evidence and does not solve the experiment again. Use a separate inspection output directory.</p>'+commandBlock('Inspect saved evidence',w.inspect)+commandBlock('Verify saved inspection',w.inspectionVerify)+'</details>':'')+
    '<details class="material-group"><summary>Code, historical audit and source evidence</summary><p>Original audit: '+esc(e.historicalAudit?.auditLabel||e.auditLabel)+'. '+esc(e.recovery?.summary||'')+'</p><h4>Computation source</h4><ul class="result-list">'+(e.code||[]).map(c=>'<li>'+(c.url?'<a href="'+esc(c.url)+'">'+esc(c.path)+'</a>':esc(c.path))+(c.note?' — '+esc(c.note):'')+'</li>').join('')+'</ul>'+((e.relatedCode||[]).length?'<h4>Related historical code</h4><ul class="result-list">'+e.relatedCode.map(c=>'<li><a href="'+esc(c.url)+'">'+esc(c.path)+'</a> — '+esc(c.note)+'</li>').join('')+'</ul>':'')+((e.existingCommands||[]).length?'<details><summary>Earlier documented commands</summary>'+e.existingCommands.map(c=>'<pre><code>'+esc(objectText(c))+'</code></pre>').join('')+'</details>':'')+'<p class="small">Historical source baseline: <code>'+esc(D.baseline)+'</code>. <a href="assets/reproduction/command-source.html">Current command source and hashes</a>.</p><ul class="result-list">'+(e.evidence||[]).map(x=>'<li><a href="'+esc(x.url)+'">'+esc(x.path)+'</a>'+(x.note?' — '+esc(x.note):'')+'</li>').join('')+'</ul></details>'+
    ((e.related||[]).length?'<h3>Related records</h3><ul class="result-list">'+e.related.map(x=>'<li><a href="'+recordLink(x.id)+'">'+esc(x.title)+'</a> — '+esc(x.note)+'</li>').join('')+'</ul>':'');
  detail.querySelectorAll('[data-jump]').forEach(button=>button.onclick=()=>{const heading=document.getElementById(button.dataset.jump);heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});heading.scrollIntoView({block:'start',behavior:'smooth'});});
  detail.querySelectorAll('.copy-command').forEach(button=>button.onclick=async()=>{try { await navigator.clipboard.writeText(button.parentElement.querySelector('code').textContent);button.textContent='Copied';} catch {button.textContent='Select and copy';}});
  const shell=detail.querySelector('#platform');
  if(shell)shell.onchange=()=>{platform=shell.value;const top=shell.getBoundingClientRect().top;openRecord(e);const next=detail.querySelector('#platform');next.focus({preventScroll:true});window.scrollBy(0,next.getBoundingClientRect().top-top);};
}
function chooser(es) {
  detail.innerHTML='<h2 id="record-title" tabindex="-1">Select the exact instance</h2><p>This figure compares several records. Choose a method, input scale and version before running its code.</p><ul class="result-list">'+es.map(e=>'<li><a href="'+recordLink(e.id)+'">'+esc(e.title)+'</a><br><small>'+esc(e.id)+' · '+esc(status(e))+'</small></li>').join('')+'</ul>';
}
function renderList() {
  const city=document.getElementById('city').value,q=document.getElementById('search').value.trim().toLowerCase(),ready=document.getElementById('ready').checked;
  const es=D.records.filter(e=>(!figure||D.figures[figure]?.experimentIds.includes(e.id))&&(city==='all'||e.city===city)&&(!ready||verified(e))&&(!q||JSON.stringify([e.id,e.title,e.instance,e.city]).toLowerCase().includes(q)));
  let e=es.find(x=>x.id===selected);
  if(!e&&(!figure||es.length===1)&&es.length){e=es[0];selected=e.id;}
  list.innerHTML=es.map(x=>'<a href="'+recordLink(x.id)+'" aria-current="'+String(x.id===selected)+'"><span class="city-label">'+esc(names[x.city])+'</span><br>'+esc(x.title)+'<small>'+esc(x.id)+' · '+esc(status(x))+'</small></a>').join('');
  document.getElementById('catalog-count').textContent=es.length+' of '+D.records.length+' records';
  if(e)openRecord(e);else if(es.length>1)chooser(es);else detail.innerHTML='<h2 id="record-title" tabindex="-1">No matching records</h2><p>Try another city or search term, or turn off the verified-only filter.</p>';
}
function selectRecord(id, focus) {
  const e=D.records.find(x=>x.id===id);
  if(!e)return;
  selected=id;
  const cityControl=document.getElementById('city'),searchControl=document.getElementById('search');
  if(cityControl.value!=='all'&&cityControl.value!==e.city)cityControl.value='all';
  const query=searchControl.value.trim().toLowerCase();
  if(query&&!JSON.stringify([e.id,e.title,e.instance,e.city]).toLowerCase().includes(query))searchControl.value='';
  if(!verified(e))document.getElementById('ready').checked=false;
  if(figure&&!D.figures[figure]?.experimentIds.includes(id)){figure=null;context();}
  renderList();syncFilters();
  if(focus){const title=document.getElementById('record-title');title.focus({preventScroll:true});title.scrollIntoView({block:'start',behavior:'auto'});}
}
document.addEventListener('click',event=>{
  const anchor=event.target.closest('a[href^="#"]');
  if(!anchor||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  let id;try{id=decodeURIComponent(anchor.getAttribute('href').slice(1));}catch{return;}
  if(!D.records.some(e=>e.id===id))return;
  event.preventDefault();
  if(id!==hashId()){const url=new URL(location.href);url.hash=encodeURIComponent(id);history.pushState(null,'',url);}
  selectRecord(id,true);
});
window.addEventListener('hashchange',()=>selectRecord(hashId(),false));
function syncFilters(){const u=new URL(location.href),city=document.getElementById('city').value,q=document.getElementById('search').value.trim();city==='all'?u.searchParams.delete('city'):u.searchParams.set('city',city);q?u.searchParams.set('q',q):u.searchParams.delete('q');document.getElementById('ready').checked?u.searchParams.set('ready','1'):u.searchParams.delete('ready');if(!figure)u.searchParams.delete('figure');if(selected)u.hash=encodeURIComponent(selected);history.replaceState(null,'',u);}
function filterChanged(){renderList();syncFilters();}
for(const id of ['city','ready'])document.getElementById(id).addEventListener('change',filterChanged);
document.getElementById('search').addEventListener('input',filterChanged);
if(params.get('city')&&names[params.get('city')])document.getElementById('city').value=params.get('city');
if(params.get('q'))document.getElementById('search').value=params.get('q');
context();renderList();
document.getElementById('catalog-loading').hidden=true;
document.getElementById('catalog-interface').hidden=false;
})();
