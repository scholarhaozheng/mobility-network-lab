"""Materialize a new evidence sandbox or an 11-case dev18 cold-run sandbox.

Never runs a solver/verifier and never rewrites files in the handoff package.
The default check-only mode verifies input and entry availability.
"""
from pathlib import Path,PureWindowsPath
import argparse,hashlib,json,shutil,sys,os

OLD=PureWindowsPath(r'E:\mobility_computation_lab_v2')
CASES=['hong_kong_10_H','boston_10_H','sioux_200_H','sioux_250_H','berkeley_T4_H','chicago_T4_H','ithaca_F_Q','ann_arbor_F_Q','pittsburgh_F_Q','urbana_F_H','pittsburgh_F_H']
BUILD='sparse_common_dev18_demand_weighted_columns'
def io(p):
 p=Path(p).absolute()
 return Path('\\\\?\\'+str(p)) if sys.platform=='win32' and not str(p).startswith('\\\\?\\') else p
def files(root):
 for p in io(root).rglob('*'):
  if p.is_file():yield Path(str(p)[4:]) if str(p).startswith('\\\\?\\') else p
def relold(value):
 try:return Path(*PureWindowsPath(value).relative_to(OLD).parts)
 except (ValueError,TypeError):return None
def digest(p):
 h=hashlib.sha256()
 with io(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write_json(p,v):io(p.parent).mkdir(parents=True,exist_ok=True);io(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rebase(v,out):
 if isinstance(v,dict):return {k:rebase(x,out) for k,x in v.items()}
 if isinstance(v,list):return [rebase(x,out) for x in v]
 if isinstance(v,str):
  r=relold(v)
  if r is not None:return str(out/r)
 return v
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[1])
 ap.add_argument('--out',type=Path)
 ap.add_argument('--mode',choices=['baseline11','evidence'],default='baseline11')
 ap.add_argument('--restored-results-root',type=Path,help='Logical package root produced by restore_full_results.py --output-root; required original filenames must exist and match raw SHA')
 ap.add_argument('--materialize',action='store_true',help='Create --out; otherwise validate only')
 a=ap.parse_args();package=a.package.resolve();snapshot=package/'SOURCE_AND_REPRODUCTION/workspace_snapshot';r=snapshot/'work/shared_cg_cross_city_r1'
 errors=[];required=set();configs={};input_hash_checks=[]
 if a.mode=='baseline11':
  for name in CASES:
   cfgpath=r/'cases'/f'{name}__{BUILD}.json'
   if not io(cfgpath).is_file():errors.append('missing config '+str(cfgpath));continue
   c=json.loads(io(cfgpath).read_text(encoding='utf-8-sig'));configs[cfgpath]=c;required.add(cfgpath)
   required.add(cfgpath.with_name(cfgpath.stem+'_budget.json'))
   inputs={}
   if c['graph_type']=='explicit':
    mpath=snapshot/relold(c['input_manifest']);m=json.loads(io(mpath).read_text(encoding='utf-8-sig'));configs[mpath]=m;required.add(mpath)
    inputs={'dynamic_arc.csv':snapshot/relold(m['dynamic_arc_file']),'dynamic_demand.csv':snapshot/relold(m['demand_file'])}
   else:
    s=snapshot/relold(c['source_dir']);inputs={n:s/n for n in c['expected_source_hashes']}
   for n,p in inputs.items():
    required.add(p)
    got=digest(p) if io(p).is_file() else None
    match=got==c['expected_source_hashes'][n]
    input_hash_checks.append({'case':name,'file':str(p.relative_to(package)),'expected':c['expected_source_hashes'][n],'observed':got,'matches':match})
    if not match:errors.append('missing or altered full input '+str(p))
  for p in files(r/BUILD):
   if '__pycache__' not in p.parts:required.add(p)
  for n in ['run_dev18_case_and_verify.py','run_dev18_11_regression.py','run_sparse_case.py','run_case.py','verify_explicit.py','verify_implicit_recompute.py','verify_uniform_release.py','DEV18_ELEVEN_CASE_PRE_RUN.json']:
   required.add(r/n)
  required.add(snapshot/'work/six_city_preflight_r1/instructions/support/mcl_batch_guard.py')
  for p in required:
   if not io(p).is_file():errors.append('missing entry/dependency '+str(p))
 else:
  required=set(files(snapshot))
  resultsroot=(a.restored_results_root or package).resolve()
  mapfile=package/'RESULTS_AND_CERTIFICATES/FULL_STORAGE_MAP.json'
  if not io(mapfile).is_file():errors.append('full result storage map absent')
  else:
   storagemap=json.loads(io(mapfile).read_text(encoding='utf-8'))
   for row in storagemap['files']:
    raw=resultsroot/row['package_path']
    if not io(raw).is_file():errors.append('original result filename absent; restore_full_results.py --restore --output-root first: '+str(raw));continue
    if io(raw).stat().st_size!=row['bytes'] or digest(raw)!=row['sha256']:errors.append('restored original result SHA/size mismatch: '+str(raw))
 report={'mode':a.mode,'required_files':len(required),'input_hash_checks':input_hash_checks,'errors':errors,'no_solver_started':True,'historical_evidence_unchanged':True,'baseline_rebased_configs_are_unverified_derivatives':a.mode=='baseline11'}
 if errors:
  print(json.dumps(report,ensure_ascii=False,indent=2));return 2
 if not a.materialize:
  print(json.dumps(report,ensure_ascii=False,indent=2));return 0
 if a.out is None:ap.error('--materialize requires --out')
 out=a.out.resolve()
 if io(out).exists():raise FileExistsError('output must be a new directory: '+str(out))
 # Prevent accidental reconstruction into the source package or the live task.
 oldhost=Path(str(OLD)).resolve()
 if out==oldhost or oldhost in out.parents or package==out or package in out.parents:raise ValueError('choose a separate new sandbox outside the entire live workspace and handoff package')
 io(out).mkdir(parents=True)
 copied=[]
 for p in sorted(required):
  target=out/p.relative_to(snapshot);io(target.parent).mkdir(parents=True,exist_ok=True)
  if p in configs and a.mode=='baseline11':
   write_json(target,rebase(configs[p],out))
   copied.append({'original_package_file':str(p.relative_to(package)),'sandbox_file':str(target),'original_sha256':digest(p),'sandbox_sha256':digest(target),'modified':'absolute paths only; original frozen input SHA kept'})
  else:shutil.copyfile(io(p),io(target))
 if a.mode=='evidence':
  prefix='RESULTS_AND_CERTIFICATES/shared_cg_snapshot/'
  for row in storagemap['files']:
   if not row['package_path'].startswith(prefix):continue
   p=resultsroot/row['package_path']
   target=out/'work/shared_cg_cross_city_r1'/row['package_path'][len(prefix):];io(target.parent).mkdir(parents=True,exist_ok=True)
   if io(target).is_file() and digest(target)!=digest(p):raise ValueError('conflicting evidence overlay '+str(target))
   if not io(target).exists():shutil.copyfile(io(p),io(target))
 report['output']=str(out);report['config_derivatives']=copied
 if a.mode=='evidence':report['restored_results_root']=str(resultsroot)
 report['historical_paths_note']='Evidence mode preserves absolute E: paths and historical SHA. It is a browseable exact reconstruction. Historical frozen experiments run unchanged only on an isolated host whose workspace uses the original absolute root; no old hash evidence is silently reissued after rebasing.'
 write_json(out/'REPRODUCTION_PREPARATION_REPORT.json',report)
 print(json.dumps(report,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
