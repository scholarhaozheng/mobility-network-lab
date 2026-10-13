"""Identity-aware outer wrapper. Preparation/inspection never starts a solver."""
from pathlib import Path
import argparse,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[3]
EXP=ROOT/'experiments/shared-cg-20261013'
CAT=ROOT/'docs/assets/shared-cg-20261013/catalog.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def logical(s):return re.sub('/+','/',s.replace('\\','/')).split('/mobility_computation_lab_v2/')[-1]
def main():
 ap=argparse.ArgumentParser(description=__doc__);sp=ap.add_subparsers(dest='action',required=True)
 sp.add_parser('list');i=sp.add_parser('inspect');i.add_argument('--case',required=True)
 p=sp.add_parser('prepare');p.add_argument('--case',required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
 a=ap.parse_args();index=read(EXP/'case-index.json')
 if a.action=='list':
  for c in index:print(c['case_id'],':', 'Dev18 baseline' if c['dev18_baseline'] else 'historical Q evidence; producer-specific dependencies required')
  return
 rec=next((c for c in index if c['case_id']==a.case),None)
 if rec is None:ap.error('Unknown registered case')
 if a.action=='inspect':
  c=next(c for c in read(CAT)['cases'] if c['case_id']==a.case)
  print(json.dumps({k:c[k] for k in ['case_id','lineage','parent_note','classification']},indent=2,ensure_ascii=False));return
 if not rec['dev18_baseline']:ap.error('This Q record uses a historical producer chain; this baseline wrapper does not claim to reproduce it.')
 parent=EXP/'original-configs'/rec['original_config'];cfg=read(parent);data=a.data_root.resolve();out=a.output_root.resolve()
 if out.exists():ap.error('Output root must be new; existing results are never overwritten.')
 verified=[];derived=dict(cfg);derived['core_root']=str(Path(__file__).resolve().parent);derived['output_dir']=str(out/'run/solver')
 def validate(p,expected):
  if not p.is_file():ap.error('Missing frozen input: '+str(p))
  got=sha(p)
  if got!=expected:ap.error('Frozen input SHA mismatch: '+str(p))
  verified.append({'path':str(p),'sha256':got})
 manifest=None
 if cfg['graph_type']=='explicit':
  original_manifest=EXP/'original-configs'/Path(logical(cfg['input_manifest'])).name
  if not original_manifest.exists():ap.error('Missing explicit original manifest '+str(original_manifest))
  manifest=read(original_manifest)
  for key,name in [('dynamic_arc_file','dynamic_arc.csv'),('demand_file','dynamic_demand.csv')]:
   f=data/logical(manifest[key]);validate(f,cfg['expected_source_hashes'][name]);manifest[key]=str(f)
  derived['input_manifest']=str(out/'derived-input-manifest.json')
 else:
  src=data/logical(cfg['source_dir']);derived['source_dir']=str(src)
  for name,expected in cfg['expected_source_hashes'].items():validate(src/name,expected)
 if cfg.get('feasible_fifo_seed_npz'):
  seed=data/logical(cfg['feasible_fifo_seed_npz']);validate(seed,cfg['expected_seed_sha256']);derived['feasible_fifo_seed_npz']=str(seed)
 if cfg.get('resume_base_config'):ap.error('A warm continuation cannot be prepared as a cold-start baseline.')
 out.mkdir(parents=True)
 def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
 if manifest:write(out/'derived-input-manifest.json',manifest)
 cp=out/'derived-config.json';write(cp,derived)
 report={'action':'PREPARED_NOT_SOLVED','case_id':a.case,'parent_config_sha256':sha(parent),'derived_config_sha256':sha(cp),'verified_inputs':verified,'scientific_parameters_changed':False,'path_changes_only':True,'historical_certificates_resigned':False,'guard':'Future numerical execution must use the existing shared resource policy, never a bypass lock root.'};write(out/'PREPARATION.json',report)
 print(json.dumps(report,indent=2));print('Future command (NOT executed):')
 print('PYTHONPATH = '+str(Path(__file__).resolve().parent));print('python -B -m shared_cg.solve --config "'+str(cp)+'"')
if __name__=='__main__':main()
