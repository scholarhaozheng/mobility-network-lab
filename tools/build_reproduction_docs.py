"""Build English reproduction metadata without running a solver or changing existing pages."""
from pathlib import Path
import argparse, hashlib, html, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/assets/reproduction'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj): p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_receipt(entry, receipt):
    verification=receipt.get('verification',{})
    expected=hashlib.sha256(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if receipt.get('experiment_id')!=entry['id'] or verification.get('experiment_id')!=entry['id']:
        raise ValueError('Receipt experiment identity mismatch: '+entry['id'])
    if receipt.get('catalog_entry_sha256')!=expected:
        raise ValueError('Stale receipt for changed catalog: '+entry['id'])
    if verification.get('verifier_cli_sha256')!=digest(ROOT/'tools/mcl_reproduce.py') or receipt.get('cli_sha256')!=verification.get('run_cli_sha256'):
        raise ValueError('Receipt wrapper/verifier identity mismatch: '+entry['id'])
    checks=verification.get('checks',{})
    if verification.get('status')!='PASS' or not checks or not all(checks.values()) or verification.get('errors') or verification.get('optimizer_calls')!=0:
        raise ValueError('Receipt does not independently pass: '+entry['id'])
    for item in entry['files']:
        p=ROOT/item['path']
        if not p.is_file() or digest(p)!=item['sha256']:
            raise ValueError('Changed pinned source/input: '+item['path'])


def file_url(item, published, repository, baseline):
    if published or item.get('download_url'):
        return repository+'/blob/'+(published or item.get('version') or baseline)+'/'+item['path']
    if item['role'] in ('solver_code','build_code','environment'):
        return 'assets/reproduction/command-source.html#file-'+hashlib.sha256(item['path'].encode()).hexdigest()[:16]
    return None


STATUS_LABELS = {
    'verified_run': 'Run and verification passed',
    'runnable': 'Run available; not freshly verified',
    'external_inputs': 'External inputs required',
    'inspection_only': 'Historical evidence / inspection only',
    'no_accepted_experiment': 'No accepted computational experiment',
}


def reproduction_status(record, recovered=None, fresh=None):
    """Resolve one current reader status; historical evidence is never fresh by implication."""
    recipe = record.get('recipe')
    actions = recovered.get('supportedActions', []) if recovered else []
    external = bool(recovered and recovered.get('state') == 'requires_external_input')
    runnable = bool(recipe or 'run' in actions)
    verified = bool(recipe and recipe.get('verified') or fresh)
    historical = record.get('historicalAudit', {})
    old_status = historical.get('auditStatus', record.get('auditStatus'))
    no_accepted = (recovered and recovered.get('state') in ('scope_only', 'historical_failure')) or old_status in ('no_experiment', 'not_run', 'failure_boundary_reobserved')
    if no_accepted:
        key, verified = 'no_accepted_experiment', False
    elif verified:
        key = 'verified_run'
    elif external:
        key = 'external_inputs'
    elif runnable:
        key = 'runnable'
    else:
        key = 'inspection_only'
    if fresh:
        basis = fresh['basis']
    elif recipe:
        basis = 'prepared_input_replay_independently_verified' if old_status == 'prepared_input_reproduced' else 'fresh_computation_independently_verified'
    elif recovered:
        basis = recovered.get('evidenceBasis', 'historical_record')
    else:
        basis = old_status or 'historical_record'
    return {
        'key': key, 'label': STATUS_LABELS[key], 'verified': verified,
        'runAvailable': runnable, 'evidenceBasis': basis,
        'receiptUrl': recipe.get('receiptUrl') if recipe else record.get('recoveredRecipe', {}).get('receiptUrl'),
        'scope': record.get('scope', ''), 'externalInputsRequired': external,
        'commandId': recipe['id'] if recipe else recovered['id'] if recovered else None,
        'commandFamily': 'registered' if recipe else 'recovered' if recovered else None,
    }


def set_reader_status(record, status):
    # Keep original audit language available as history, not a competing current status.
    record.setdefault('historicalAudit', {key: record[key] for key in ('auditStatus', 'auditLabel', 'entryLabel', 'missing') if key in record})
    record['reproductionStatus'] = status
    record['auditStatus'] = status['key']
    record['auditLabel'] = status['label']
    record['entryLabel'] = status['label']


def status_summary(records):
    counts, cities, commands = {}, {}, set()
    for record in records:
        status = record['reproductionStatus']
        key = status['key']
        counts[key] = counts.get(key, 0) + 1
        city = cities.setdefault(record['city'], {'records': 0, 'verifiedRecords': 0, 'verifiedCommands': set()})
        city['records'] += 1
        if status['verified']:
            city['verifiedRecords'] += 1
            command = (status['commandFamily'], status['commandId'])
            city['verifiedCommands'].add(command)
            commands.add(command)
    for city in cities.values():
        city['verifiedCommands'] = len(city['verifiedCommands'])
    return {'records': len(records), 'verifiedRecords': sum(r['reproductionStatus']['verified'] for r in records),
            'verifiedCommands': len(commands), 'counts': counts, 'byCity': cities,
            'scope': 'Recorded execution and independent verification apply only to each stated workflow and its declared inputs; they do not imply raw-source acquisition, a fresh solve in this website revision, or clean-environment certification.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--published-revision',help='Public repository ref used for navigation; exact numerical identities remain pinned by file hashes')
    args=parser.parse_args()
    inv=read(ROOT/'experiments/inventory.json'); cat=read(ROOT/'experiments/catalog.json')
    runtime_path=ROOT/'experiments/runtime-setup.json'
    runtime_setups=read(runtime_path).get('entries',{}) if runtime_path.is_file() else {}
    baseline=cat['baseline_commit']; repo=cat['repository']; DEST.mkdir(parents=True,exist_ok=True)
    materials={m['id']:m for m in inv['materials']}; codes={c['id']:c for c in inv['code']}
    entries={e["id"]:e for e in cat["experiments"]}
    audit_to_entry={}
    for command_id, audit_ids in cat["audit_entries"].items():
        for audit_id in ([audit_ids] if isinstance(audit_ids,str) else audit_ids):
            if audit_id in audit_to_entry: raise ValueError("Ambiguous primary command for "+audit_id)
            audit_to_entry[audit_id]=entries[command_id]
    states={'saved_validation_only':'Saved evidence checked','blocked':'Blocked by missing requirements','prepared_input_reproduced':'Prepared inputs reproduced','fresh_reproduced':'Fresh solve checked','not_run':'Not run','input_preparation_only':'Input preparation only','no_experiment':'No accepted computational experiment','failure_boundary_reobserved':'Failure boundary reobserved'}
    data={'repository':repo,'baseline':baseline,'published':bool(args.published_revision),'publishedRevision':args.published_revision,'records':[],'figures':{},'releaseVersion':'20261004-r14','sourceIdentityManifest':'experiments/publication.json'}
    for e in inv['experiments']:
        ms=[]
        for ref in e['materialRefs']:
            m=materials[ref['id']]; role=ref.get('role') or m['role']
            ms.append({'path':m.get('path'),'title':m.get('title'),'role':'upstream_source' if role=='raw_upstream_source' else role,'note':m.get('note',''),'browseUrl':m.get('repositoryBrowseUrl'),'downloadUrl':m.get('downloadButton',{}).get('url') if m.get('downloadButton',{}).get('enabled') else None,'sourceUrl':m.get('sourceProviderUrl') or m.get('sourceLandingUrl'),'sha256':m.get('contentSha256')})
        cs=[{'path':codes[i]['path'],'url':codes[i].get('repositoryBrowseUrl') or codes[i].get('upstreamUrl'),'note':codes[i].get('note','')} for i in e['codeRefs']]
        record={'id':e['id'],'city':e['city'],'title':e['title'],'instance':e['instance'],'scope':e['auditScope'],'auditStatus':e['auditStatus'],'auditLabel':states.get(e['auditStatus'],e['auditStatus']),'entryLabel':'No accepted computational experiment' if e['auditStatus']=='no_experiment' else 'Run entry not ready','materials':ms,'code':cs,'existingCommands':e.get('existingPublicCommand',{}).get('documentedCommands',[]),'missing':e.get('missing',[]),'related':[],'evidence':[]}
        for ev in e.get('evidence',[]):
            p=ev.get('path','')
            if p and not re.match(r'^[A-Za-z]:',p) and not Path(p).is_absolute() and (ROOT/p).is_file():
                record['evidence'].append({'path':p,'url':repo+'/blob/'+baseline+'/'+p+('#L'+str(ev['line']) if ev.get('line') else ''),'note':ev.get('note','')})
        entry=audit_to_entry.get(e['id'])
        if entry:
            receipt_path=ROOT/'experiments/verification'/(entry['id']+'.json')
            receipt=read(receipt_path) if receipt_path.is_file() else None
            if receipt:
                validate_receipt(entry,receipt)
                v=receipt['verification']
                record['auditStatus']='prepared_input_reproduced' if e['auditStatus']=='prepared_input_reproduced' else 'fresh_reproduced'
                record['auditLabel']='Prepared-input replay checked' if record['auditStatus']=='prepared_input_reproduced' else 'Fresh computation checked'
                record['scope']=entry['contract']
                record['missing']=entry.get('remaining_requirements',[])+e.get('publicationReviewRequirements',[])
                primary_paths={f['path'] for f in entry['files'] if f['role'] in ('solver_code','build_code','environment')}
                record['relatedCode']=[{'path':c['path'],'url':c['url'],'note':'Related historical implementation; not called by this registered command.'} for c in cs if c['path'] not in primary_paths]
                cs[:]=[c for c in cs if c['path'] in primary_paths]
                for c in cs:
                    c['note']='Pinned implementation called by this registered command.'
                    exact_source=next(f for f in entry['files'] if f['path']==c['path'])
                    c['url']=file_url(exact_source,args.published_revision,repo,baseline)
                for f in entry['files']:
                    if f['role'] in ('solver_code','build_code','environment'):
                        if not any(c['path']==f['path'] for c in cs): cs.append({'path':f['path'],'url':file_url(f, args.published_revision, repo, baseline),'note':('Pinned environment requirements; install during setup.' if f['role']=='environment' else 'Pinned source-build helper; run separately during setup.' if f['role']=='build_code' or f['path'].endswith('/build_tapb.py') else 'Pinned implementation used by this command.')})
                        continue
                    role={'solver_input':'frozen_input','solver_config':'frozen_input','reference_only':'expected_result','input_provenance':'display_evidence'}[f['role']]
                    exact={'path':f['path'],'role':role,'note':'Exact file in the computational manifest.','browseUrl':file_url(f,args.published_revision,repo,baseline),'downloadUrl':('https://raw.githubusercontent.com/'+repo.split('github.com/')[-1]+'/'+args.published_revision+'/'+f['path']) if args.published_revision else f.get('download_url'),'sha256':f['sha256'],'localAddition':not bool(args.published_revision or f.get('download_url'))}
                    old=next((m for m in ms if m.get('path')==f['path']),None)
                    if old: old.update(exact)
                    else: ms.append(exact)
                cs.append({'path':'tools/mcl_reproduce.py','url':repo+'/blob/'+(args.published_revision or baseline)+'/tools/mcl_reproduce.py','note':'Unified entry point; current wrapper source and hashes.'})
                record['recipe']={'id':entry['id'],'verified':True,'verificationSummary':entry['claim_boundary'],'metrics':{k:v for k,v in v['metrics'].items() if not isinstance(v,(dict,list)) and 'signature' not in k and 'seconds' not in k},'tolerances':v['tolerances'],'receiptUrl':'assets/reproduction/verification/'+entry['id']+'.json','environment':entry['environment'],'setup':entry.get('setup',{})}
                if entry['id'] in runtime_setups:
                    runtime=runtime_setups[entry['id']]
                    for item in runtime['files']:
                        if digest(ROOT/item['path'])!=item['sha256']: raise ValueError('Runtime setup file changed: '+item['path'])
                    record['recipe']['setup']=runtime['setup']
                    if runtime.get('remainingRequirement'): record['missing'].append(runtime['remainingRequirement'])
                    if runtime.get('validationReceipt'):
                        validation_name=Path(runtime['validationReceipt']).name
                        (DEST/'environment-verification').mkdir(parents=True,exist_ok=True)
                        write(DEST/'environment-verification'/validation_name,read(ROOT/runtime['validationReceipt']))
                        record['recipe']['setupValidationReceiptUrl']='assets/reproduction/environment-verification/'+validation_name
                    record['recipe']['setupGuideUrl']='assets/reproduction/command-source.html#file-'+hashlib.sha256(runtime['setup']['documentation'].encode()).hexdigest()[:16]
                if entry['id']=='boston-native-l3-ranks26-52':
                    record['recipe']['supportedPlatforms']=['windows']
                    for rank in ('26','52'):
                        for key,value in v['metrics'].get(rank,{}).items(): record['recipe']['metrics']['rank'+rank+'_'+key]=value
                if e['id']=='HK10-ARC-LP': record['missing']=[m for m in record['missing'] if not isinstance(m,str) or 'one-line command' not in m.lower()]
                (DEST/'verification').mkdir(exist_ok=True)
                write(DEST/'verification'/(entry['id']+'.json'),receipt)
        if args.published_revision and record.get('recipe'):
            record['recipe']['verificationSummary']=record['recipe']['verificationSummary'].replace('Inputs are included in the local review bundle, not yet GitHub main.','Inputs are included in this tagged repository release and its computational checkout.').replace('local review bundle','tagged computational checkout')
        record['recovery']=e.get('recovery')
        set_reader_status(record, reproduction_status(record))
        data['records'].append(record)
    byid={e['id']:e for e in data['records']}
    for f in inv['figures']:
        data['figures'][f['figureId']]={'title':f['title'],'experimentIds':f['entryExperimentIds'],'referenceIds':f['referenceExperimentIds'],'relatedIds':f['relatedExperimentIds'],'reason':f['mappingReason'],'purpose':f['entryPurpose'],'previewAsset':f.get('previewAsset'),'publishedAsset':f.get('publishedAsset')}
        for current in f['entryExperimentIds']:
            for ids,note in [(f['referenceExperimentIds'],'Comparison baseline'),(f['relatedExperimentIds'],'Related context or instance; not the main result in this figure')]:
                for related in ids:
                    if related!=current and not any(x['id']==related for x in byid[current]['related']): byid[current]['related'].append({'id':related,'title':byid[related]['title'],'note':note})
    byid['sioux-historical-fw-100']['related'].append({'id':'sioux-public-fw-frozen-528','title':byid['sioux-public-fw-frozen-528']['title'],'note':'A separate verified new experiment; it does not reproduce the historical 100-iteration figure.'})
    rendered=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\u003c')
    if re.search(r'[\u3400-\u9fff]',rendered): raise ValueError('Non-English CJK text in reader data')
    (DEST/'data.js').write_text('window.MCL_REPRODUCTION='+rendered+';\n',encoding='utf-8')
    write(DEST/'inventory.json',inv)
    source_files=['tools/mcl_reproduce.py','tools/mcl_reproduction_check.py','tools/mcl_recovered.py','experiments/catalog.json','experiments/README.md']
    source_files+=sorted({f['path'] for e in cat['experiments'] for f in e['files'] if not f.get('download_url') and f['role'] in ('solver_code','build_code','environment')})
    if runtime_setups:
        source_files+=['experiments/runtime-setup.json']+sorted({f['path'] for runtime in runtime_setups.values() for f in runtime['files']})
    chunks=[]
    for rel in source_files:
        p=ROOT/rel
        chunks.append('<details id="file-'+hashlib.sha256(rel.encode()).hexdigest()[:16]+'"><summary>'+html.escape(rel)+'</summary><p>SHA-256: <code>'+digest(p)+'</code></p><pre><code>'+html.escape(p.read_text(encoding='utf-8')).replace('[','&#91;').replace(']','&#93;')+'</code></pre></details>')
    (DEST/'command-source.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Command source · Mobility Computation Lab</title><link rel="stylesheet" href="../presentation-r3.css"></head><body><main class="mcl-page"><p><a href="../../reproduce.html">Experiment catalog</a></p><h1>Unified command source</h1><p>These files wrap the existing computational implementations. Input and solver hashes are fixed in the catalog. Publication status is shown on the reproduction page.</p>'+''.join(chunks)+'</main></body></html>\n',encoding='utf-8')
    write(DEST/'build-report.json',{'records':len(data['records']),'figures':len(data['figures']),'verifiedCommands':sorted({e['recipe']['id'] for e in data['records'] if e.get('recipe')}),'verifiedRecords':sum(bool(e.get('recipe')) for e in data['records']),'publishedRevision':args.published_revision,'files':{p:digest(ROOT/p) for p in source_files}})
    recovered_summary=None
    if (ROOT/'experiments/recovered').is_dir():
        recovered_build=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_recovered_docs.py'),'--release-ref',args.published_revision or 'reproduction-2026-10-04-r14'],cwd=ROOT,capture_output=True,text=True,check=True)
        recovered_summary=json.loads(recovered_build.stdout)
    final_data=json.loads((DEST/'data.js').read_text(encoding='utf-8').removeprefix('window.MCL_REPRODUCTION=').strip().removesuffix(';'))
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_reproduction_fallback.py')],cwd=ROOT,capture_output=True,text=True,check=True)
    print(json.dumps({'records':len(data['records']),'originalCatalogVerifiedRecords':sum(bool(e.get('recipe')) for e in data['records']),'currentStatus':final_data.get('statusSummary',status_summary(data['records'])),'recovered':recovered_summary}))
if __name__=='__main__': main()
