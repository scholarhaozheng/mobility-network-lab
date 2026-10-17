"""Promote the approved CG V1 cards into existing atlas components only.

The 19-row comparison and all non-CG content are kept byte/content protected.
No old-result catalog is imported; current run identity remains authoritative.
"""
from pathlib import Path
import json,re,html,hashlib,csv,shutil
from PIL import Image

R=Path(__file__).resolve().parents[2];D=R/'docs';A=D/'assets/shared-cg-dev48-20261014';V=D/'assets/cg-v1-20261017'
REV='20261017-cg-v1-source-inputs'
DEFAULTS={'hong-kong':'hong_kong_10_H','boston':'boston_10_H','sioux-falls':'sioux_200_H','berkeley':'berkeley_T4_H','chicago':'chicago_T4_H','ann-arbor':'ann_arbor_F_Q','ithaca':'ithaca_F_Q','pittsburgh':'pittsburgh_F_H','urbana-champaign':'urbana_F_H'}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def edit(p,s):
    b=p.read_bytes();s=s.replace('\r\n','\n');p.write_bytes(s.replace('\n','\r\n'if b'\r\n'in b else'\n').encode('utf8'))
def balanced(s,start,tag):
    depth=0
    for m in re.finditer(r'</?'+tag+r'\b[^>]*>',s[start:],re.I):
        depth+=-1 if m[0].startswith('</')else 1
        if not depth:return start+m.end()
    raise ValueError((start,tag))
def span(s,city):
    for m in re.finditer(r'<section\b[^>]*class="[^"]*\bcg-component\b[^>]*>',s):
        if 'data-cg-city="'+city+'"'in m[0]:return m.start(),balanced(s,m.start(),'section')
    raise ValueError(city)
esc=html.escape
def n(v):return 'not established'if v is None else f'{v:.10g}'
def status(c):
    if not c['accepted_at_frozen_gate']:return 'Verified feasible solution; full-graph optimality OPEN.'
    if c['actual_adapter']=='uniform_release shortcut':return 'Exact certified construction; no CG iterations were required.'
    if c['raw_pricing_status']=='MET':return 'Feasible solution and original pricing gate verified.'
    return 'Accepted at the frozen gap tolerance; the original raw pricing gate remains unmet.'

def caption(c,i,data):
    if i==0:
        if data.get('phase_i_executed'):
            return f"All {len(data['round'])} saved Phase I states: capacity-resource slack {n(data['capacity_slack'][0])} → {n(data['capacity_slack'][-1])} {data['unit']}; path pool {data['path_pool'][0]:,} → {data['path_pool'][-1]:,}. Slack is summed over capacity-resource rows, not unmet OD demand or unserved vehicles. Both panels use the same run."
        if data.get('branch')=='exact_uniform_release':
            return f"Exact construction: maximum physical entry-time load/capacity {n(data['maximum_entry_capacity_ratio'])}; all {data['release_events']:,} releases served; original OD residual zero. The left panel is an entry-time peak, not cumulative flow divided by capacity. Phase I was not executed."
        if 'feasible_seed_verification'in data:
            seed=data['feasible_seed_verification'];return f"A verified original-graph seed makes Phase I unnecessary: {seed['seed_path_columns']:,} initial paths cover {seed['original_release_events']:,} original releases. Maximum event-demand residual {n(seed['seed_max_event_demand_residual'])} PCE; capacity excess {n(seed['seed_max_capacity_excess'])} PCE. These are seed records, not artificial-flow iterations."
        return f"Full-demand construction for {c['OD']:,} positive OD pairs and {c['events']:,} original releases. The right panel shows the actual generated pool at three recorded CG rounds and the final solved RMP. No Phase I artificial-flow iteration was executed; final primal feasibility does not establish full-graph optimality."
    if i==1:
        prefix='Three recorded CG rounds plus the final solved RMP; the final point is not a fourth CG round. 'if c['solver_branch']=='new_joint_delta_cg'else'Exact construction, no Phase II CG loop. 'if c['actual_adapter']=='uniform_release shortcut'else'One solved Phase II state; the original pricing gate was met at the first check. 'if len(data['objective'])==1 else f"All {len(data['objective'])} saved Phase II states are retained. "
        if data['fixed_terminal_L'] is None:return prefix+'No verified same-run full-graph lower bound is available. The right panel remains unavailable; no other-run or historical bound is substituted. Optimality remains OPEN.'
        return prefix+f"Left: true objective in {data['unit']}. Right: signed 100(J − Lfinal)/|Lfinal|, with fixed same-run independently verified Lfinal={n(data['fixed_terminal_L'])}. This is not per-round pricing gap. The 0.01% guide is a display reference; acceptance uses 100(U−L)/|U|. Signed roundoff and all states remain in plot data."
    return 'Current and best saved full-graph lower bounds are distinguished. Per-round values are solver records, not independently checked certificates for every round. Signed gaps use 100(U−L)/|U|; the best-bound curve never replaces current raw data.'

cat=read(A/'catalog.json');design=read(V/'design-data.json');bydesign={c['case_id']:c for c in design['cases']}
previous=read(A/'site-catalog.json');parent_cases={c['case_id']:c for c in previous['cases']};trace=[]
for c in cat['cases']:
    approved=bydesign[c['case_id']];folder=V/'figures'/c['case_id'];oldmap=next(f for f in c['figures']if f['id'].endswith('physical-flow'))
    figs=[]
    exact=c['actual_adapter']=='uniform_release shortcut'
    titles=['Feasibility: capacity and demand conservation'if exact else'Phase I: capacity slack and path-pool growth'if approved['phase_i_states']else'Feasibility: the verified starting construction',
            'Optimality: feasible cost and verified bound'if exact else'Phase II: objective and final-bound reference']
    for i,stem in enumerate(['phase-i','phase-ii']):
        fid=f"cg-dev48-{c['case_id']}-"+['phase-i-combined','phase-ii-pair'][i];dp=folder/(stem+'.plot.json');data=read(dp);cap=caption(c,i,data)
        with Image.open(folder/(stem+'.png'))as im:w,h=im.size
        fig={'id':fid,'title':titles[i],'src':(folder/(stem+'.svg')).relative_to(D).as_posix(),'png':(folder/(stem+'.png')).relative_to(D).as_posix(),'data':dp.relative_to(D).as_posix(),'source':(folder/(stem+'.source.json')).relative_to(D).as_posix(),'caption':cap,'width':w,'height':h}
        source_path=folder/(stem+'.source.json');prior=read(source_path)
        source={'case_id':c['case_id'],'run_id':c['run_id'],'model_id':c['model_id'],'code_package':c['code_package'],'actual_solver_entry':c['actual_entry'],'source_record':c['source_dir']+'/run-provenance.json','input_result':{'path':c['source_dir']+'/result.json','sha256':sha(D/c['source_dir']/'result.json')},'renderer':'tools/visuals/render_cg_v1_20261017.py','renderer_sha256':sha(R/'tools/visuals/render_cg_v1_20261017.py'),'style_sha256':sha(R/'tools/visuals/berkeley_alignment_r2/atlas_style.py'),'approved_asset_renderer_sha256':prior.get('approved_asset_renderer_sha256',prior.get('renderer_sha256')),'caption':cap,'outputs':{ext:sha(folder/(stem+'.'+ext))for ext in ['svg','png','plot.json']},'new_solver_calls':0,'new_pricing_calls':0,'notice':'assets/shared-cg-dev48-20261014/NOTICE.txt','presentation':'V1 approved design, same-run saved evidence'}
        source['inputs']=[{'path':c['source_dir']+'/'+name,'sha256':sha(D/c['source_dir']/name)} for name in ['result.json','config.json','upper-certificate.json','lower-certificate.json','acceptance-receipt.json','phase-i-combined.plot.json','phase-ii-pair.plot.json'] if (D/c['source_dir']/name).exists()]
        write(source_path,source);(folder/(stem+'.caption.txt')).write_text(cap+'\n',encoding='utf8');figs.append(fig)
    # The current centered map uses the same saved movement vector. Source maps stay archived.
    if (folder/'physical-flow.png').exists():
        with Image.open(folder/'physical-flow.png')as im:w,h=im.size
        oldmap=dict(oldmap)
        oldmap.update({k:(folder/('physical-flow.'+ext)).relative_to(D).as_posix()for k,ext in [('src','svg'),('png','png'),('data','plot.json'),('source','source.json')]})
        oldmap.update(width=w,height=h)
        source_path=folder/'physical-flow.source.json';source=read(source_path)
        source.update(source_dir=c['source_dir'],renderer='tools/visuals/render_cg_v1_20261017.py',renderer_sha256=sha(R/'tools/visuals/render_cg_v1_20261017.py'),map_function='tools/visuals/render_cg_dev48_20261014.py::physical(centered=True)',case_id=c['case_id'],run_id=c['run_id'],model_id=c['model_id'],caption=oldmap['caption'],presentation=REV)
        if source.get('retained_map_renderer'):source['retained_map_renderer']['sha256']=sha(R/'tools/visuals/render_cg_dev48_20261014.py')
        for item in source.get('inputs',[]):
            path=Path(item['path'])
            if path.is_absolute():item['path']=path.relative_to(D).as_posix()
        write(source_path,source)
    figs.append(oldmap);c['figures']=figs;c['v1_saved_phase_i_states']=approved['phase_i_states'];c['v1_saved_phase_ii_states']=approved['phase_ii_states'];c['v1_presentation']=REV
    for key in ['online_template_revision','new_city_presentation_revision','phase_ii_right_panel']:c.pop(key,None)
    c['phase_ii_right_panel']='signed_difference_to_same_run_final_bound';c['diagnostic']=None
    diag=folder/'pricing-diagnostic.svg'
    if diag.exists():
        with Image.open(diag.with_suffix('.png'))as im:w,h=im.size
        c['diagnostic']={'id':f"cg-dev48-{c['case_id']}-pricing-diagnostic",'title':'Pricing diagnostics: current and best saved bounds','src':diag.relative_to(D).as_posix(),'png':diag.with_suffix('.png').relative_to(D).as_posix(),'data':diag.with_suffix('.plot.json').relative_to(D).as_posix(),'source':diag.with_suffix('.source.json').relative_to(D).as_posix(),'caption':caption(c,2,{}),'width':w,'height':h}
        source=read(diag.with_suffix('.source.json'));source.update(case_id=c['case_id'],run_id=c['run_id'],model_id=c['model_id'],actual_solver_entry=c['actual_entry'],current_renderer='tools/visuals/render_cg_v1_20261017.py',current_renderer_sha256=sha(R/'tools/visuals/render_cg_v1_20261017.py'));write(diag.with_suffix('.source.json'),source)
    for f in c['figures']+([c['diagnostic']]if c['diagnostic']else[]):trace.append({'case_id':c['case_id'],'run_id':c['run_id'],'figure_id':f['id'],'svg':f['src'],'svg_sha256':sha(D/f['src']),'plot_data':f['data'],'plot_data_sha256':sha(D/f['data']),'solver_entry_sha256':c['actual_entry']['sha256']})
write(A/'catalog.json',cat)

def card(c,f,volume=False,diagnostic=False,idx=0):
    pre='../'if volume else'';fid=f['id']if volume else'atlas-'+f['id'];eid='dev48-diagnostic'if diagnostic else'dev48'
    href=pre+f['src']if volume else'volumes/'+c['city']+'.html?cg-case='+c['case_id']+'&amp;cg-evidence='+eid+'#'+f['id']
    cap=('<figcaption class="atlas-final-caption"><strong>'+esc(f['title'])+'.</strong> '+esc(f['caption'])+'</figcaption>')if volume else'<p class="atlas-final-caption">'+esc(f['caption'])+'</p>'
    evidence=pre+'assets/shared-cg-dev48-20261014/REPRODUCTION.html#'+c['case_id']if volume else href
    links='<a href="'+evidence+'">Complete evidence</a> · <a href="'+pre+f['src']+'">Full figure</a> · <a href="'+pre+f['data']+'">Plot data</a>'
    sources=[f['data'],f['source'],c['source_dir']+'/run-provenance.json']
    if idx==2:sources.insert(1,c['source_dir']+'/physical-flow.csv')
    records='<details class="atlas-source-records"><summary>Source records</summary><ul>'+''.join('<li><a href="'+pre+path+'">docs/'+esc(path)+'</a></li>'for path in sources)+'</ul><p><a href="'+pre+f['png']+'">PNG</a> · <a href="'+pre+f['src']+'">SVG</a></p></details>'
    tag='figure'if volume else'div'
    heading=''if volume else'<h5>'+esc(f['title'])+'</h5>'
    return '<'+tag+' class="atlas-card conservative-card cg-figure'+(' cg-map-card'if idx==2 else'')+'" data-figure="'+f['id']+'" id="'+fid+'">'+heading+'<a class="atlas-image" href="'+href+'"><img src="'+pre+f['src']+'" alt="'+esc(f['title'])+'" width="'+str(f['width'])+'" height="'+str(f['height'])+'" loading="lazy"></a>'+cap+'<p class="atlas-final-links">'+links+'</p>'+records+'</'+tag+'>'

def panel(c,volume=False,diagnostic=False):
    pre='../'if volume else'';dt=c['dt_seconds'];time=f"Δt {dt:g} s · {c['horizon_steps']:,} steps ({dt*c['horizon_steps']/60:g} min)"if dt else f"{c['horizon_steps']:,} native steps; seconds not established"
    instance=f"{c['OD']:,} OD pairs · {c['events']:,} releases · demand ×{c['scale']:g} · {time}"
    desc=status(c)+f" U={n(c['U'])}; L={n(c['L'])}; certificate gap="+('not established.'if c['gap_raw']is None else n(c['gap_raw']*100)+'%.')
    figs=list(c['figures'])
    if diagnostic and c['diagnostic']:figs[1]=c['diagnostic']
    text='<h5 class="atlas-method-heading">Column generation framework · Dev48</h5><p class="atlas-method-instance">'+esc(instance)+'</p><p class="atlas-method-summary" data-cg-status="'+('accepted'if c['accepted_at_frozen_gate']else'open')+'">'+esc(desc)+'</p>'
    text+='<div class="atlas-gallery cg-gallery" data-columns="3">'+''.join(card(c,f,volume,diagnostic,i)for i,f in enumerate(figs))+'</div>'
    source=pre+c['source_dir'];code=pre+'assets/shared-cg-dev48-20261014/REPRODUCTION.html#'+c['case_id']
    details='<p>Actual run: '+esc(c['run_id'])+'. Code package: '+esc(c['code_package'])+'. Actual path: '+esc(c['actual_adapter'])+'.</p>'
    details+='<p>Model identity: '+esc(c['model_id'])+'. Original raw minimum reduced cost: '+n(c['raw_last_minimum_reduced_cost'])+'; original gate −1e−6; '+esc(c['raw_pricing_status'])+'. Gap acceptance and original pricing closure are separate.</p>'
    if c['case_id']=='pittsburgh_S2_H':details+='<p>This cold retry uses its final stage-60 primal and independently checked stage-57/60 dual mixture. The raw solver stopped at its round limit. The verified mixed bound is a terminal reference, not the last raw pricing bound.</p>'
    if c['solver_branch']=='new_joint_delta_cg':details+='<p>Three recorded CG rounds plus the final solved RMP are shown. Full-graph per-round lower bounds/gaps were not saved. A final independent bound, where present, is only a fixed reference; the joint Q problem remains OPEN.</p>'
    elif c['actual_adapter']=='uniform_release shortcut':details+='<p>The exact construction satisfies the original demand and entry-time capacities and matches its lower bound. It has zero Phase I/II CG iterations; no trajectory is fabricated.</p>'
    else:details+=f"<p>Saved Phase I states: {c['v1_saved_phase_i_states']}; saved Phase II states: {c['v1_saved_phase_ii_states']}. State counts include checks and are not automatically update counts. Capacity-resource slack is not unmet OD demand. The main objective reference is fixed to this run’s independently verified terminal lower bound.</p>"
    parent=parent_cases.get(c['case_id'],{}).get('parent_note')
    if parent:details+='<p>'+esc(parent)+'</p>'
    links=[('Configuration','config.json'),('Actual result and history','result.json'),('Independent primal','upper-certificate.json'),('Acceptance record','acceptance-receipt.json'),('Projection checks','projection-checks.json'),('Complete movement CSV','physical-flow.csv'),('Run/source hashes','run-provenance.json')]
    if c['L']is not None:links.insert(3,('Independent lower bound','lower-certificate.json'))
    details+='<p>'+' · '.join('<a href="'+source+'/'+f+'">'+label+'</a>'for label,f in links)+'</p>'
    text+='<details class="cg-supporting-records"><summary>Independent certificates, model scope and actual code</summary>'+details+'</details><p class="cg-evidence-links"><a href="'+code+'">This run’s code, inputs and reproduction</a> · <a href="'+pre+'assets/shared-cg-dev48-20261014/NOTICE.txt">Sources and reuse notice</a></p>'
    return text

site={'schema':'MCL_CG_CURRENT_V1','version':REV,'current_code_package':cat['code_package'],'defaults':DEFAULTS,'cities':{c['city']:c['city_name']for c in cat['cases']},'cases':[]}
for c in cat['cases']:
    item={k:c[k]for k in ['case_id','city','city_name','OD','events','scale','dt_seconds','horizon_steps','run_id','actual_adapter']};item.update(default_evidence='dev48',dev48_available=True,selected_three=True,evidence=[])
    for diag in ([False,True]if c['diagnostic']else[False]):
        e={'evidence_id':'dev48-diagnostic'if diag else'dev48','label':'Same-run pricing diagnostics'if diag else'V1 · objective and final-bound reference','run_id':c['run_id'],'code_package':c['code_package'],'figures':([c['figures'][0],c['diagnostic'],c['figures'][2]]if diag else c['figures'])}
        e['home_html']=panel(c,False,diag);e['volume_html']=panel(c,True,diag);item['evidence'].append(e)
    site['cases'].append(item)
write(A/'site-catalog.json',site);(A/'catalog.js').write_text('window.MCL_CG_CATALOG='+json.dumps(site,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')

def controls(city):
    return '<div class="cg-controls">'+''.join('<label>'+label+'<select '+attr+' aria-label="'+esc(site['cities'][city]+' '+label)+'"></select></label>'for label,attr in [('OD scope / demand factor','data-cg-od'),('Time model / experiment','data-cg-case'),('Evidence view','data-cg-evidence')])+'</div>'
def component(city,volume=False):
    c=next(c for c in cat['cases']if c['case_id']==DEFAULTS[city]);return '<section class="cg-component" id="shared-cg-'+city+'" data-cg-city="'+city+'" data-cg-volume="'+str(volume).lower()+'" data-cg-template="v1-20261017">'+controls(city)+'<div class="cg-body">'+panel(c,volume)+'</div></section>'
def scripts(s):
    for f in ['catalog.js','switch.js','style.css']:s=re.sub(r'shared-cg-dev48-20261014/'+re.escape(f)+r'(?:\?v=[^"<> ]+)?','shared-cg-dev48-20261014/'+f+'?v='+REV,s)
    s=re.sub(r'reading/atlas-data\.js(?:\?v=[^"<> ]+)?','reading/atlas-data.js?v='+REV,s)
    return s
for name in ['index.html','index-coverage-city.html','index-coverage-stage.html']:
    p=D/name;s=p.read_text(encoding='utf8')
    for city in DEFAULTS:
        a,b=span(s,city);s=s[:a]+component(city)+s[b:]
    edit(p,scripts(s))
mdnames={'boston':'02-boston','hong-kong':'04-hong-kong','sioux-falls':'03-sioux-falls'}
for city in DEFAULTS:
    p=D/'volumes'/(city+'.html');s=p.read_text(encoding='utf8');a,b=span(s,city);edit(p,scripts(s[:a]+component(city,True)+s[b:]))
    p=D/'volumes'/(mdnames.get(city,city)+'.md');s=p.read_text(encoding='utf8');s,count=re.subn(r'<!-- SHARED_CG_20261013_START -->.*?<!-- SHARED_CG_20261013_END -->','<!-- SHARED_CG_20261013_START -->\n'+component(city,True)+'\n<!-- SHARED_CG_20261013_END -->',s,flags=re.S);assert count==1;edit(p,s)
with(V/'FIGURE_TRACE.csv').open('w',encoding='utf-8-sig',newline='')as f:
    writer=csv.DictWriter(f,fieldnames=list(trace[0]));writer.writeheader();writer.writerows(trace)
write(V/'CURRENT_PRESENTATION.json',{'version':REV,'cases':len(cat['cases']),'main_cards':48,'scientific_code_package':cat['code_package'],'legacy_algorithm_choices':[],'diagnostics':'Same actual run, same code; separate display only','solver_calls':0,'pricing_calls':0,'renderer':'tools/visuals/render_cg_v1_20261017.py'})
design.update(purpose='Approved V1 integrated into the existing complete website',website_modified=True)
write(V/'design-data.json',design)
for filename in ['switch.js','style.css']:shutil.copyfile(Path(__file__).parent/'cg_v1_assets'/filename,A/filename)
atlas_data=D/'assets/reading/atlas-data.js'
old='Selected Dev48 runs: Phase I capacity slack and per-OD data scope; Phase II objective with each case’s declared progress metric; final physical-link movement flow. Boston, Hong Kong and Sioux Falls show actual per-round pricing lower bounds and signed gaps on the right. Other cases retain their stated fixed references; historical versions remain separate.'
new='Approved V1 / selected Dev48 runs: Phase I capacity-resource slack and path-pool growth, or the actual seed/exact feasibility certificate; Phase II real objective and signed difference to the fixed same-run terminal bound; final physical-link movement flow. Same-run per-round pricing diagnostics are a separate view. All recorded states and genuine missing bounds remain; no historical run is substituted.'
edit(atlas_data,atlas_data.read_text(encoding='utf8').replace(old,new))
print('V1 integrated into 3 home variants, 9 city volumes and their maintenance sources; 16 current cases.')
