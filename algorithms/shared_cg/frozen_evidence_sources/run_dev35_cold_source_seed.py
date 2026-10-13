"""Fresh source-driven Urbana Q AON/FIFO seed, then independent original replay."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent
CORE=R/'sparse_common_dev35_joint_stabilized_cg'
sys.path.insert(0,str(CORE))
from shared_cg.solve import run as run_aon
from shared_cg.source_fifo import main as run_fifo
CFG=R/'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
BASE=R/'runs/dev35_cold_source_seed_urbana_f'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
 start=time.monotonic();cfg=rd(CFG)
 aon=Path(cfg['output_dir']);fifo=BASE/'fifo'
 if not (aon/'RESULT.json').exists():
  exitcode=run_aon(CFG)
  if exitcode!=2:raise ValueError('expected source AON overload screen, not closed solver')
 ar=rd(aon/'RESULT.json')
 if ar['status']!='AON_CAPACITY_OVERLOAD_NEEDS_GENERIC_CG' or ar['source_hashes']!=cfg['expected_source_hashes']:
  raise ValueError('fresh original AON source identity')
 path=aon/'UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 if ar['path_sha256']!=sha(path):raise ValueError('fresh AON path drift')
 if not (fifo/'RESULT.json').exists():
  run_fifo(CFG,path,fifo)
 fr=rd(fifo/'RESULT.json')
 if fr['status']!='CANDIDATE_FEASIBLE_PENDING_INDEPENDENT_ORIGINAL_REPLAY':
  raise ValueError('source-driven FIFO did not produce original feasible seed')
 if not (fifo/'INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json').exists():
  cmd=[sys.executable,'-B',str(R/'verify_dev35_cold_source_fifo.py'),'--config',str(CFG),'--aon',str(path),'--out',str(fifo)]
  subprocess.run(cmd,check=True,cwd=R.parents[1])
 cert=rd(fifo/'INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json')
 if cert['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or cert['producer_result_sha256']!=sha(fifo/'RESULT.json'):
  raise ValueError('fresh seed independent original replay')
 receipt={'schema':'DEV35_FRESH_SOURCE_Q_FIFO_SEED_RECEIPT','status':'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED',
  'case_id':cfg['case_id'],'source_hashes':cfg['expected_source_hashes'],
  'source_config_sha256':sha(CFG),'AON_result_sha256':sha(aon/'RESULT.json'),'AON_path_sha256':sha(path),
  'FIFO_result_sha256':sha(fifo/'RESULT.json'),'FIFO_fragment_sha256':sha(fifo/'FRAGMENTS.npz'),
  'independent_certificate_sha256':sha(fifo/'INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json'),
  'independent_feasible_upper':cert['independent_feasible_primal_upper'],
  'original_positive_OD':cert['original_positive_OD'],'original_release_events':cert['original_release_events'],
  'wall_seconds':time.monotonic()-start,'scope':'Fresh source-generated feasible seed only, unrestricted joint CG optimum still open.'}
 (BASE/'RECEIPT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
