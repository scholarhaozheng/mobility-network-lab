"""Exact full-original-Q price values under the dev48 joint RMP capacity dual.

This stage computes a valid L for the 418 x 14,400 original commodities.
The saved price profile is not a CG closure until current-dual negative
columns have been recovered, added and reoptimized.
"""
from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'sparse_common_dev48_balanced_selection'))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.rolling_price import RollingModel
OUT=R/'runs/dev48_event_joint_cg_urbana_f/FULL_PRICE'
ROOT=R/'runs/dev48_event_joint_cg_urbana_f'
CFG=R/'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,obj):
 t=p.with_suffix('.partial.json');t.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');os.replace(t,p)
def main():
 start=time.monotonic();run=json.loads((ROOT/'RESULT.json').read_text(encoding='utf-8'))
 cert=json.loads((ROOT/'INDEPENDENT_CERT.json').read_text(encoding='utf-8'))
 if cert['producer_result_sha256']!=sha(ROOT/'RESULT.json') or cert['status']!='PASS_FULL_ORIGINAL_PRIMAL_RESTRICTED_DUAL_OPEN_FULL_GRAPH':
  raise ValueError('cold source RMP not independently accepted')
 with np.load(ROOT/'FINAL_RMP.npz') as z:
  allrows=z['original_rows'];mu=z['capacity_mu']
 if len(allrows)!=len(mu) or np.any(mu>1e-8):raise ValueError('RMP price row/sign')
 active=mu<-1e-12;rows=allrows[active];lam=-mu[active]
 cfg=json.loads(CFG.read_text(encoding='utf-8-sig'))
 model=ImplicitTimeGraph(cfg['source_dir'],cfg['dt_seconds'],cfg['horizon_steps'],cfg['release_steps'],cfg['demand_factor'])
 if model.source_hashes!=cfg['expected_source_hashes'] or model.K!=cfg['expected_commodity_events']:
  raise ValueError('original source/model drift')
 oracle=RollingModel.from_implicit(model);T=model.release_steps
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'RESULT.json').exists():raise FileExistsError('full original price complete')
 stage=OUT/'STAGE.json';record=json.loads(stage.read_text(encoding='utf-8')) if stage.exists() else {
  'schema':'DEV48_FULL_ORIGINAL_Q_PRICE_STAGE','rmp_flow_sha256':sha(ROOT/'FINAL_RMP.npz'),
  'source_config_sha256':sha(CFG),'completed_destinations':[]}
 if record['rmp_flow_sha256']!=sha(ROOT/'FINAL_RMP.npz') or record['source_config_sha256']!=sha(CFG):
  raise ValueError('stale price stage')
 done=record['completed_destinations']
 for k,item in enumerate(done):
  dest=int(model.destinations[k]);p=OUT/f'DEST_{dest:05d}.npz'
  if item['destination']!=dest or item['sha256']!=sha(p):raise ValueError('stage destination identity')
 for k in range(len(done),len(model.destinations)):
  dest=int(model.destinations[k]);ids=np.asarray([i for i,od in enumerate(model.od) if int(od[3])==dest],np.int32)
  origins=np.asarray([int(model.od[i][2]) for i in ids],np.int32)
  release=np.tile(np.arange(T,dtype=np.int32),len(ids));query_origin=np.repeat(origins,T)
  t=time.monotonic();values=oracle.price(dest,release,query_origin,rows,lam).reshape(len(ids),T)
  if not np.all(np.isfinite(values)):raise ValueError('unreachable original Q release')
  p=OUT/f'DEST_{dest:05d}.npz';tmp=OUT/f'DEST_{dest:05d}.partial.npz'
  np.savez_compressed(tmp,od_indices=ids,price_by_release=values);os.replace(tmp,p)
  done.append({'destination':dest,'positive_OD':len(ids),'events':len(ids)*T,'sha256':sha(p),'seconds':time.monotonic()-t})
  save(stage,record)
  print(json.dumps({'complete':len(done),'of':len(model.destinations),'dest':dest,'events':len(ids)*T,'seconds':done[-1]['seconds']}),flush=True)
 weighted=0.
 for item in done:
  p=OUT/f"DEST_{item['destination']:05d}.npz"
  with np.load(p) as z:ids=z['od_indices'];values=z['price_by_release']
  hourly=np.asarray([float(model.od[int(i)][4]) for i in ids])
  weighted+=float(np.dot(hourly/T,np.sum(values,axis=1)))
 capterm=float(np.dot(model.capacity_for_rows(rows),lam))
 lower=weighted-capterm
 if lower>cert['independent_full_original_feasible_upper']+1e-6:raise ValueError('valid dual exceeds feasible U')
 result={'schema':'DEV48_COLD_SOURCE_FULL_ORIGINAL_Q_PRICE_CURRENT_RMP_DUAL','status':'COLD_SOURCE_JOINT_RMP_FULL_ORIGINAL_DUAL_OPEN_CG',
  'case_id':'urbana_F_Q','source_hashes':model.source_hashes,'original_positive_OD':len(model.od),'original_release_events':model.K,
  'destination_count':len(done),'positive_capacity_prices':len(rows),'capacity_price_sum':float(np.sum(lam)),
  'demand_weighted_minimum_adjusted_cost':weighted,'original_capacity_price_term':capterm,
  'valid_full_original_lower':lower,'independently_feasible_RMP_upper':cert['independent_full_original_feasible_upper'],
  'current_pair_gap':(cert['independent_full_original_feasible_upper']-lower)/cert['independent_full_original_feasible_upper'],
  'historical_best_lower':10335.278655330989,'historical_best_upper':11333.921650746439,
  'RMP_independent_cert_sha256':sha(ROOT/'INDEPENDENT_CERT.json'),'source_config_sha256':sha(CFG),
  'price_module_sha256':sha(R/'sparse_common_dev48_balanced_selection/shared_cg/rolling_price.py'),
  'stage_sha256':sha(stage),'wall_seconds_final_stage':time.monotonic()-start,
  'limitation':'Cold-source final-RMP dual bound requires independent full-source Bellman audit; priced negative routes must enter common RMP before CG closure.'}
 save(OUT/'RESULT.json',result)
 print(json.dumps({k:result[k] for k in ('status','valid_full_original_lower','independently_feasible_RMP_upper','current_pair_gap','positive_capacity_prices')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()



