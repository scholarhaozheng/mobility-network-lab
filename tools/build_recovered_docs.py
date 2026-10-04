"""Attach recovered code/data recipes to the existing English experiment portal."""
from pathlib import Path
import argparse, hashlib, html, json, re
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/assets/reproduction'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_bytes((json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release-ref',default='reproduction-2026-10-04-r14')
    a=ap.parse_args(); repo='https://github.com/scholarhaozheng/mobility-network-lab'; raw=repo.replace('github.com','raw.githubusercontent.com')
    text=(DEST/'data.js').read_text(encoding='utf-8')
    data=json.loads(text[len('window.MCL_REPRODUCTION='):].strip().removesuffix(';'))
    updates={r['id']:r for r in read(ROOT/'experiments/recovered-status.json')['records']}
    recovered={}; manifests=[]
    for p in sorted((ROOT/'experiments/recovered').glob('*.json')):
        manifests.append(p.relative_to(ROOT).as_posix())
        for r in read(p).get('records',[]):
            if r['id'] in recovered:raise ValueError('Duplicate recovered ID: '+r['id'])
            r=dict(r);r['manifest']=p.relative_to(ROOT).as_posix();recovered[r['id']]=r
    for e in data['records']:
        note=updates.get(e['id'])
        if note:
            e['recovery']={'status':note['group'],'summary':note['label']}
            e['title']=note['title']
            if not e.get('recipe'):e['missing']=note['remainingRequirements']
            if e['id']=='boston-activity-informed-50000-am-r1':
                e['auditStatus']='input_preparation_only';e['auditLabel']='Input preparation only';e['scope']='The historical 50,000-trip activity-informed demand was prepared, but assignment_run is false in its source manifest. No historical assignment result is claimed.'
        r=recovered.get(e['id'])
        if not r:continue
        for f in r.get('files',[]):
            p=(ROOT/f['path']).resolve()
            if not p.is_relative_to(ROOT) or not p.is_file() or sha(p)!=f['sha256']:raise ValueError('Recovered file identity mismatch: '+f['path'])
        e['recoveredRecipe']={k:v for k,v in r.items() if k not in ('files','dataSources')}
        er=e['recoveredRecipe'];er['manifestUrl']=repo+'/blob/'+a.release_ref+'/'+r['manifest']
        er['codeUrl']=repo+'/blob/'+a.release_ref+'/'+r['entrypoint'] if r.get('entrypoint') else None
        er['entryLabel']='Scope / historical record' if r.get('state') in ('scope_only','historical_failure') else 'Recovered code and commands' if 'run' in r.get('supportedActions',[]) else 'Source code and evidence checks'
        e['recovery']={'status':'integrated','initialStatus':note['group'] if note else None,'summary':'Source and evidence integrated; the supported actions and remaining limits are stated below.'}
        er['commands']={}
        for action in r.get('supportedActions',[]):
            if action not in ('run','verify','inspect','acquire'):continue
            target_action=('run' if 'run' in r.get('supportedActions',[]) else 'inspect') if action=='verify' else action
            command='python -B tools/mcl_recovered.py '+action+' '+r['id']+(' --run ' if action=='verify' else ' --output ')+'../results/'+r['id']+'-'+target_action
            if r.get('state')=='requires_external_input' and action=='run':command+=' --input-root ../source-inputs/'+r['id']
            er['commands'][action]=command
        er['checkCommand']='python -B tools/mcl_recovered.py check '+r['id']
        citydoc={'boston':'boston','hong-kong':'hong-kong','sioux-falls':'sioux','shared':'shared'}.get(e['city'])
        guide='docs/reproduction/recovered-'+citydoc+'.md'
        er['guideUrl']=repo+'/blob/'+a.release_ref+'/'+guide if (ROOT/guide).is_file() else None
        receipt=r.get('evidenceReceipt')
        if receipt:
            p=ROOT/receipt
            if not p.is_file():raise ValueError('Missing recovered receipt: '+receipt)
            er['receiptUrl']=repo+'/blob/'+a.release_ref+'/'+receipt
        e['scope']=r.get('scope') or e['scope']
        if r.get('remainingRequirements') is not None:e['missing']=r['remainingRequirements']
        e['entryLabel']=er['entryLabel']
        known={c['path'] for c in e['code']}
        for f in r.get('files',[]):
            role=f.get('role','')
            url=repo+'/blob/'+a.release_ref+'/'+f['path']
            if f['path'].endswith('.py') or role in ('solver_code','build_code','environment'):
                if f['path'] not in known:e['code'].append({'path':f['path'],'url':url,'note':'Recovered, hash-pinned computation source or environment.'});known.add(f['path'])
            else:
                role='expected_result' if role in ('reference_only','saved_result','expected_result','saved_state') else 'display_evidence' if role in ('input_provenance','provenance','documentation','execution_receipt') else 'frozen_input' if role in ('solver_input','solver_config','input','configuration') else 'mixed_bundle'
                material={'path':f['path'],'title':f['path'],'role':role,'note':'Recovered recipe file; role is defined in its manifest.','browseUrl':url,'downloadUrl':raw+'/'+a.release_ref+'/'+f['path'],'sourceUrl':None,'sha256':f['sha256']}
                old=next((m for m in e['materials'] if m.get('path')==f['path']),None)
                if old:old.update(material)
                else:e['materials'].append(material)
        e['recoveredRecipe']['dataSources']=r.get('dataSources',[])
    data['releaseVersion']='20261004-r14';data['recoveredReleaseRef']=a.release_ref
    data['recoveredSummary']={'records':len(recovered),'executable':sum('run' in r.get('supportedActions',[]) for r in recovered.values()),'inspectable':sum('inspect' in r.get('supportedActions',[]) for r in recovered.values()),'manifestFiles':manifests,'note':'Recovered commands and inspected historical results are separate from the 41 previously verified command recipes.'}
    rendered=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    if re.search(r'[\u3400-\u9fff]',rendered):raise ValueError('Non-English text in reader data')
    (DEST/'data.js').write_text('window.MCL_REPRODUCTION='+rendered+';\n',encoding='utf-8')
    write(DEST/'recovered-recipes.json',{'releaseRef':a.release_ref,'summary':data['recoveredSummary'],'records':list(recovered.values())})
    for filename in ('experiments/reproduction-status.json','docs/assets/reproduction/reproduction-status.json'):
        status=read(ROOT/filename)
        for e in status['records']:
            if e['id'] in updates:
                e['recoveryStatus']=dict(updates[e['id']])
                if e['id'] in recovered:e['recoveryStatus'].update(initialGroup=updates[e['id']]['group'],group='integrated',label='Source and evidence integrated; check supported actions and scope limits.')
            if e['id'] in recovered:
                r=recovered[e['id']];e['recoveredRecipe']={'manifest':r['manifest'],'entrypoint':r.get('entrypoint'),'actions':r.get('supportedActions',[]),'state':r.get('state'),'evidenceBasis':r.get('evidenceBasis'),'evidenceReceipt':r.get('evidenceReceipt')}
                e['remainingRequirements']=r.get('remainingRequirements',updates.get(e['id'],{}).get('remainingRequirements',[]))
            if e['id']=='boston-activity-informed-50000-am-r1':
                e['title']=updates[e['id']]['title'];e['status']='input_preparation_only';e['statusLabel']='Input preparation only; historical assignment was not run'
        counts={}
        for e in status['records']:counts[e['status']]=counts.get(e['status'],0)+1
        status['counts']=counts;status['releaseVersion']='20261004-r14';status['recoveredRecipes']=data['recoveredSummary'];write(ROOT/filename,status)
    write(DEST/'recovered-build-report.json',data['recoveredSummary'])
    print(json.dumps(data['recoveredSummary'],indent=2))
if __name__=='__main__':main()
