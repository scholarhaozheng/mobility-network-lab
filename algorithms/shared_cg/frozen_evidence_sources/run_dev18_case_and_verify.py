"""Run and independently verify one registered case from the same dev8 source.

Call this only inside the original mcl_batch_guard heavy lock. The per-case
runner enforces the existing measured resource policy; the verifier reads
original inputs and does not call the CG producer.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent;BUILD='sparse_common_dev18_demand_weighted_columns'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('case_id');args=a.parse_args()
 case=args.case_id
 allowed={'hong_kong_10_H','boston_10_H','sioux_200_H','sioux_250_H','berkeley_T4_H','chicago_T4_H','urbana_F_H','pittsburgh_F_H','urbana_S2_H','pittsburgh_S2_H','urbana_F_Q','urbana_S2_Q','pittsburgh_F_Q','pittsburgh_S2_Q','ithaca_F_Q','ann_arbor_F_Q'}
 if case not in allowed:raise ValueError('unregistered case')
 cfgp=R/'cases'/f'{case}__{BUILD}.json';budget=R/'cases'/f'{case}__{BUILD}_budget.json';cfg=json.loads(cfgp.read_text(encoding='utf-8'))
 out=Path(cfg['output_dir']);root=out.parent
 started=time.monotonic()
 run=subprocess.run([sys.executable,'-B',str(R/'run_sparse_case.py'),'--config',str(cfgp),'--budget',str(budget)],cwd=R)
 record={'schema':'SHARED_CG_DEV18_FRESH_REGRESSION_R1','case_id':case,'build_id':BUILD,
         'config':str(cfgp),'config_sha256':sha(cfgp),'solver_exit_code':run.returncode,
         'source_identity':str(R/BUILD/'SOURCE_IDENTITY.json'),
         'source_identity_sha256':sha(R/BUILD/'SOURCE_IDENTITY.json')}
 if run.returncode==0:
  verifier=R/('verify_explicit.py' if cfg['graph_type']=='explicit' else ('verify_uniform_release.py' if cfg['graph_type']=='uniform_release_implicit' else 'verify_implicit_recompute.py'))
  log=root/'independent_verifier_stdout.log'
  with log.open('w',encoding='utf-8') as f:
   verified=subprocess.run([sys.executable,'-B',str(verifier),'--config',str(cfgp)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  record['verifier_exit_code']=verified.returncode;record['verifier_source']=str(verifier);record['verifier_source_sha256']=sha(verifier)
  cert=out/'INDEPENDENT_CERTIFICATE.json'
  if cert.exists():
   c=json.loads(cert.read_text(encoding='utf-8'));record['independent_status']=c['status'];record['independent_objective']=c.get('original_objective',c.get('original_primal_objective'));record['independent_gap']=c.get('relative_gap_raw');record['certificate']=str(cert);record['certificate_sha256']=sha(cert)
 else:record['independent_status']='NO_CLOSED_SOLVER_ENDPOINT'
 record['total_wall_seconds']=time.monotonic()-started
 (root/'DEV18_REGRESSION_RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:record.get(k) for k in ('case_id','solver_exit_code','verifier_exit_code','independent_status','independent_objective','independent_gap','total_wall_seconds')},ensure_ascii=False),flush=True)
 return 0 if record.get('independent_status')=='PASS_FULL_GRAPH' else 2
if __name__=='__main__':raise SystemExit(main())


