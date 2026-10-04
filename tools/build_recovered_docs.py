"""Attach recovered code/data recipes to the existing English experiment portal."""
from pathlib import Path
import argparse, hashlib, html, json, re
from build_reproduction_docs import reproduction_status, set_reader_status, status_summary, validate_receipt
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/assets/reproduction'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):
    if p.is_file() and read(p)==o:return
    p.write_bytes((json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def passed_checks(result, record_id, require_identity=False):
    identity = result.get('record', result.get('id'))
    return (result.get('success') is True and bool(result.get('checks'))
            and all(value is True for value in result['checks'].values())
            and result.get('optimizer_calls') == 0
            and (identity == record_id if require_identity else identity in (None, record_id)))


def validate_fresh_evidence(record, execution, receipt):
    """Require execution evidence as well as independent checks, never a ready flag."""
    record_id = record['id']
    if execution.get('id') != record_id or execution.get('status') != 'PASS' or execution.get('receipt') != record.get('evidenceReceipt'):
        raise ValueError('Fresh execution index does not match recipe: ' + record_id)
    if 'run' not in record.get('supportedActions', []) or record.get('state') in ('scope_only', 'historical_failure'):
        raise ValueError('Fresh execution is not a supported accepted workflow: ' + record_id)
    identity = receipt.get('record', receipt.get('id'))
    if identity != record_id:
        raise ValueError('Fresh receipt identity mismatch: ' + record_id)
    # Receipts predate the unified portal and use four documented schemas.
    # Check each schema explicitly, rather than treating PASS/inspect as a solve.
    if receipt.get('schema') == 'mcl_recovered_hk_evidence_v1':
        execution_passed = receipt.get('freshComputation') is True and receipt.get('action') == 'run_and_verify'
        independently_verified = passed_checks(receipt.get('verification', {}), record_id, True)
    elif receipt.get('schema') == 'mcl_recovered_evidence_v1':
        command = receipt.get('command', [])
        execution_passed = receipt.get('exitCode') == 0 and receipt.get('evidenceBasis') == 'fresh_query' and 'run' in command and record_id in command
        independently_verified = passed_checks(receipt.get('verification', {}), record_id)
    elif 'verifierUpdate' in receipt or 'independentReverification' in receipt:
        execution_passed = receipt.get('success') is True and str(receipt.get('evidenceBasis', '')).startswith('fresh_')
        independent = receipt.get('verifierUpdate', {}).get('result') or receipt.get('independentReverification', {})
        independently_verified = passed_checks(independent, record_id, True)
    else:
        execution_passed = (receipt.get('success') is True and receipt.get('evidence_basis') == 'fresh_computation'
                            and receipt.get('source_input_hashes_verified') is True
                            and bool(receipt.get('execution_adapter_sha256')) and bool(receipt.get('verification_adapter_sha256')))
        independently_verified = passed_checks(receipt, record_id, True) and receipt.get('verification_optimizer_calls') == 0
    if not execution_passed or not independently_verified:
        raise ValueError('Fresh execution and independent verification are not both supported: ' + record_id)
    return execution


def load_fresh_evidence(recovered):
    validation = read(ROOT / 'docs/reproduction/recovered-validation.json')
    if validation.get('status') != 'PASS':
        raise ValueError('Recovered execution validation did not pass')
    result = {}
    for execution in validation.get('freshExecutions', []):
        record_id = execution['id']
        if record_id in result or record_id not in recovered:
            raise ValueError('Duplicate or unknown fresh execution: ' + record_id)
        receipt_path = (ROOT / execution['receipt']).resolve()
        if not receipt_path.is_relative_to(ROOT) or not receipt_path.is_file():
            raise ValueError('Missing repository receipt: ' + execution['receipt'])
        result[record_id] = validate_fresh_evidence(recovered[record_id], execution, read(receipt_path))
    if len(result) != validation.get('freshDistinctWorkflows'):
        raise ValueError('Fresh workflow count disagrees with receipt index')
    return result

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
    fresh = load_fresh_evidence(recovered)
    registered = {entry['id']: entry for entry in read(ROOT/'experiments/catalog.json')['experiments']}
    validated_commands = set()
    for e in data['records']:
        if e.get('recipe') and e['recipe']['id'] not in validated_commands:
            command_id = e['recipe']['id']
            validate_receipt(registered[command_id], read(ROOT/'experiments/verification'/(command_id+'.json')))
            validated_commands.add(command_id)
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
            checked = read(p)
            verified_result = checked.get('verifierUpdate', {}).get('result') or checked.get('independentReverification') or checked.get('verification') or checked
            er['verificationMetrics'] = {key:value for key,value in verified_result.get('metrics', {}).items() if isinstance(value, (str, int, float, bool)) and 'seconds' not in key and 'signature' not in key}
            er['verificationChecks'] = {key:value for key,value in verified_result.get('checks', {}).items() if isinstance(value, bool)}
        e['scope']=r.get('scope') or e['scope']
        e['missing']=r.get('remainingRequirements', [])
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
    for e in data['records']:
        set_reader_status(e, reproduction_status(e, recovered.get(e['id']), fresh.get(e['id'])))
    data['statusSchema']='mcl_reader_reproduction_status_v1'
    data['statusSummary']=status_summary(data['records'])
    data['releaseVersion']='20261004-r14';data['recoveredReleaseRef']=a.release_ref
    data['recoveredSummary']={'records':len(recovered),'executable':sum('run' in r.get('supportedActions',[]) for r in recovered.values()),'inspectable':sum('inspect' in r.get('supportedActions',[]) for r in recovered.values()),'manifestFiles':manifests,'note':'Recovered commands and inspected historical results are separate from the 41 previously verified command recipes.'}
    rendered=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    if re.search(r'[\u3400-\u9fff]',rendered):raise ValueError('Non-English text in reader data')
    (DEST/'data.js').write_text('window.MCL_REPRODUCTION='+rendered+';\n',encoding='utf-8')
    write(DEST/'recovered-recipes.json',{'releaseRef':a.release_ref,'summary':data['recoveredSummary'],'records':list(recovered.values())})
    by_id = {e['id']: e for e in data['records']}
    for filename in ('experiments/reproduction-status.json','docs/assets/reproduction/reproduction-status.json'):
        status=read(ROOT/filename)
        status.setdefault('historicalAuditSummary', {key: status[key] for key in ('counts', 'byCity', 'verifiedCommands', 'verifiedRecords', 'scope') if key in status})
        for e in status['records']:
            current = by_id[e['id']]
            resolved = current['reproductionStatus']
            e.setdefault('historicalAudit', {key: e[key] for key in ('status', 'statusLabel', 'scope', 'claimBoundary', 'remainingRequirements', 'verifiedCommandId', 'receiptUrl', 'commands', 'recoveryStatus') if key in e})
            e['reproductionStatus'] = resolved
            e['status'], e['statusLabel'] = resolved['key'], resolved['label']
            e['title'], e['scope'] = current['title'], current['scope']
            e['remainingRequirements'] = current.get('missing', [])
            e['receiptUrl'] = resolved['receiptUrl']
            e['verifiedCommandId'] = resolved['commandId'] if resolved['verified'] else None
            e['commandFamily'] = resolved['commandFamily']
            if current.get('recoveredRecipe'):
                r=recovered[e['id']]
                e['recoveredRecipe']={'manifest':r['manifest'],'entrypoint':r.get('entrypoint'),'actions':r.get('supportedActions',[]),'state':r.get('state'),'evidenceBasis':r.get('evidenceBasis'),'evidenceReceipt':r.get('evidenceReceipt')}
                e['commands'] = current['recoveredRecipe']['commands']
                e['commands']['check'] = current['recoveredRecipe']['checkCommand']
                e['claimBoundary'] = current['scope']
                e['recoveryStatus'] = {'group':'integrated', 'label':resolved['label'], 'remainingRequirements':current.get('missing', []), 'historicalAssessment':updates.get(e['id'])}
            if e.get('availability'):
                e['availability']['registeredCommandPublished'] = resolved['runAvailable']
                e['availability']['dataAcquisition'] = 'Download the computational checkout, follow the selected recipe environment and declared input requirements, run its command, and verify its output. External inputs are identified per record.'
        summary = data['statusSummary']
        status.update(counts=summary['counts'], byCity=summary['byCity'], verifiedCommands=summary['verifiedCommands'], verifiedRecords=summary['verifiedRecords'], scope=summary['scope'], readerStatusSchema=data['statusSchema'])
        status['releaseVersion']='20261004-r14';status['recoveredRecipes']=data['recoveredSummary'];write(ROOT/filename,status)
    write(DEST/'recovered-build-report.json',data['recoveredSummary'])
    print(json.dumps(data['recoveredSummary'],indent=2))
if __name__=='__main__':main()
