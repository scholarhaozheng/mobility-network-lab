"""Check a reproduction checkout without downloading data or invoking an optimizer."""
from __future__ import annotations
import argparse, hashlib, importlib.metadata, json, platform, sys
from pathlib import Path

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--experiment',help='Limit checks to one catalog command ID')
    parser.add_argument('--environment',action='store_true',help='Also require the selected command packages to be installed; differing tested versions are reported')
    parser.add_argument('--report',type=Path,help='Optional JSON report path')
    args=parser.parse_args(); root=args.repo_root.resolve(); cat=read(root/'experiments/catalog.json')
    entries=[e for e in cat['experiments'] if not args.experiment or e['id']==args.experiment]
    if not entries: parser.error('Unknown command ID; use tools/mcl_reproduce.py list')
    problems=[]; warnings=[]; rows=[]; files={}; runtime=read(root/'experiments/runtime-setup.json').get('entries',{})
    for entry in entries:
        issues=[]
        for f in entry['files']+runtime.get(entry['id'],{}).get('files',[]):
            rel=f['path']; p=(root/rel).resolve()
            if not p.is_relative_to(root): issues.append('Unsafe file path: '+rel); continue
            result=files.get(rel)
            if result is None:
                result={'path':rel,'exists':p.is_file(),'sha256':digest(p) if p.is_file() else None};files[rel]=result
            if result['sha256']!=f['sha256']: issues.append('Missing or changed pinned file: '+rel)
        receipt_path=root/'experiments/verification'/(entry['id']+'.json')
        if not receipt_path.is_file(): issues.append('Missing archived run receipt')
        else:
            receipt=read(receipt_path); v=receipt.get('verification',{}); checks=v.get('checks',{})
            expected=hashlib.sha256(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if receipt.get('experiment_id')!=entry['id'] or v.get('experiment_id')!=entry['id'] or receipt.get('catalog_entry_sha256')!=expected: issues.append('Receipt/catalog identity mismatch')
            if v.get('status')!='PASS' or not checks or any(value is not True for value in checks.values()) or v.get('errors') or v.get('optimizer_calls')!=0: issues.append('Archived independent verification does not pass')
            if v.get('verifier_cli_sha256')!=digest(root/'tools/mcl_reproduce.py') or receipt.get('cli_sha256')!=v.get('run_cli_sha256'): issues.append('Wrapper/verifier identity mismatch')
        env={}
        if args.environment:
            minimum=tuple(int(x) for x in entry['environment'].get('python_minimum','3.10').split('.'))
            if sys.version_info[:len(minimum)]<minimum: issues.append('Python is below the minimum version')
            for name in entry['environment'].get('packages',[]):
                try: env[name]=importlib.metadata.version(name)
                except importlib.metadata.PackageNotFoundError: issues.append('Missing Python package: '+name)
            for name,expected in entry['environment'].get('tested_versions',{}).items():
                actual=platform.python_version() if name=='python' else env.get(name)
                if actual and actual!=expected: warnings.append(entry['id']+': tested '+name+' '+expected+'; current '+actual)
        rows.append({'id':entry['id'],'status':'PASS' if not issues else 'FAIL','archived_receipt':'experiments/verification/'+entry['id']+'.json','environment':env,'problems':issues})
        problems.extend(entry['id']+': '+x for x in issues)
    mapped=set()
    for ids in cat['audit_entries'].values(): mapped.update([ids] if isinstance(ids,str) else ids)
    recovered_checks=[]; recovered_files={}
    if not args.experiment and (root/'experiments/recovered').is_dir():
        from mcl_recovered import records as recovered_records, check as check_recovered
        for entry in recovered_records(root).values():
            result=check_recovered(root,entry)
            recovered_checks.append({'id':entry['id'],'status':result['status'],'checked_files':len(result['files']),'errors':result['errors']})
            for item in result['files']: recovered_files[item['path']]=item
            problems.extend(entry['id']+': '+issue for issue in result['errors'])
    report={'schema':'mcl_reproduction_checkout_check_v1','status':'PASS' if not problems else 'FAIL','optimizer_calls':0,'network_calls':0,'fresh_computation_performed':False,'scope':'Pinned file and archived receipt integrity only. Execute run and verify to reproduce a result. Runtime binaries must be built or installed separately.','baseline':cat['baseline_commit'],'commands_checked':len(rows),'mapped_inventory_records':len(mapped),'unique_files_checked':len(files),'python':platform.python_version(),'commands':rows,'warnings':warnings,'errors':problems}
    report.update(recovered_records_checked=len(recovered_checks), recovered_unique_files_checked=len(recovered_files), recovered_checks=recovered_checks)
    if args.report: args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));return 0 if not problems else 2
if __name__=='__main__': raise SystemExit(main())
