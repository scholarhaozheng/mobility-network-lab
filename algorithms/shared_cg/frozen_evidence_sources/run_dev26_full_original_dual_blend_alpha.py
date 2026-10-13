"""One checkpointable alpha of a frozen full-original Q cross-method dual blend."""
from pathlib import Path
from hashlib import sha256
import argparse,json,os,sys,time,numpy as np
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'sparse_common_dev20_rolling_path_recovery'))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.rolling_price import RollingModel
D=R/'DEV26_FULL_ORIGINAL_DUAL_BLEND_GRID_DESIGN.json';SUP=R/'runs/dev26_dual_blend_support_urbana_f';OUT=R/'runs/dev26_full_original_dual_blend_grid_urbana_f'
CFG=R/'cases/urbana_F_Q__sparse_common_dev20_rolling_path_recovery.json';SEED=R/'runs/sparse_common_dev20_rolling_path_recovery/urbana_F_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
def sha(p):
 h=sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,record):
 tmp=p.with_suffix('.partial.json');tmp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');os.replace(tmp,p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--alpha-index',type=int,required=True);args=ap.parse_args()
 d=json.loads(D.read_text(encoding='utf-8-sig'));cfg=json.loads(CFG.read_text(encoding='utf-8-sig'))
 if not 0<=args.alpha_index<len(d['alpha_grid']):raise ValueError('alpha outside frozen grid')
 for key,path in [('support_result_sha256',SUP/'RESULT.json'),('support_npz_sha256',SUP/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz'),('base_independent_cert_sha256',R/'runs/dev25_two_subgradient_bundle_grid_urbana_f/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT.json'),('RMP_independent_cert_sha256',R/'runs/dev22_batch_event_rmp_urbana_f/INDEPENDENT_CERT.json')]:
  if sha(path)!=d[key]:raise ValueError('frozen source-certified blend input drift '+key)
 support=json.loads((SUP/'RESULT.json').read_text(encoding='utf-8-sig'))
 with np.load(SUP/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz') as z:
  allrows=z['original_resource_rows'];base=z['base_capacity_lambda'];other=z['RMP_capacity_lambda'];ids=z['affected_original_OD_index'];release=z['affected_release_step'];destinations=z['affected_destination_node_index'];static=z['affected_static_cost']
 alpha=float(d['alpha_grid'][args.alpha_index]);full_lambda=(1-alpha)*base+alpha*other;positive=full_lambda>0;rows=allrows[positive];lam=full_lambda[positive]
 model=ImplicitTimeGraph(cfg['source_dir'],cfg['dt_seconds'],cfg['horizon_steps'],cfg['release_steps'],cfg['demand_factor'])
 if model.source_hashes!=cfg['expected_source_hashes'] or model.K!=cfg['expected_commodity_events'] or len(ids)!=support['affected_original_events']:raise ValueError('complete original Q identity/affected event set')
 if any(int(model.od[int(i)][3])!=int(dest) for i,dest in zip(ids,destinations)):raise ValueError('affected source destination mapping')
 oracle=RollingModel.from_implicit(model)
 alpha_dir=OUT/f'ALPHA_{args.alpha_index:03d}';alpha_dir.mkdir(parents=True,exist_ok=True)
 if (alpha_dir/'RESULT.json').exists():raise FileExistsError('alpha already complete')
 stage=alpha_dir/'DESTINATION_STAGE_RECEIPT.json';receipts=json.loads(stage.read_text(encoding='utf-8-sig'))['completed_destinations'] if stage.exists() else []
 unique=np.unique(destinations)
 if not np.array_equal(unique,np.array(d['affected_destination_node_indices'],dtype=np.int32)):raise ValueError('predeclared original destination scope')
 if len(receipts)>len(unique):raise ValueError('bad prior destination count')
 if receipts:
  prior=json.loads(stage.read_text(encoding='utf-8-sig'))
  if prior['design_sha256']!=sha(D) or prior['support_npz_sha256']!=sha(SUP/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz') or prior['alpha_index']!=args.alpha_index:raise ValueError('stage identity drift')
 values=np.empty(len(ids),np.float64)
 for j,item in enumerate(receipts):
  dest=int(unique[j]);positions=np.flatnonzero(destinations==dest).astype(np.int32);path=alpha_dir/f'DESTINATION_{dest:05d}_PRICE.npz'
  if item['destination_node_index']!=dest or item['sha256']!=sha(path):raise ValueError('saved destination hash/order drift')
  with np.load(path) as z:oldpos=z['selection_position'];price=z['minimum_adjusted_price']
  if not np.array_equal(positions,oldpos) or len(price)!=len(positions) or not np.all(np.isfinite(price)):raise ValueError('saved original affected events')
  values[positions]=price
 began=time.monotonic()
 for j in range(len(receipts),len(unique)):
  dest=int(unique[j]);positions=np.flatnonzero(destinations==dest).astype(np.int32)
  origins=np.array([int(model.od[int(i)][2]) for i in ids[positions]],np.int32)
  t0=time.monotonic();price=oracle.price(dest,release[positions],origins,rows,lam)
  if not np.all(np.isfinite(price)):raise ValueError('unreachable original event')
  values[positions]=price;path=alpha_dir/f'DESTINATION_{dest:05d}_PRICE.npz';tmp=alpha_dir/f'DESTINATION_{dest:05d}_PRICE.partial.npz'
  np.savez_compressed(tmp,selection_position=positions,minimum_adjusted_price=price);os.replace(tmp,path)
  receipts.append({'destination_node_index':dest,'affected_original_events':len(positions),'sha256':sha(path),'seconds':time.monotonic()-t0})
  save(stage,{'schema':'SHARED_CG_DEV26_ORIGINAL_Q_DUAL_BLEND_PRICE_STAGES_R1','alpha_index':args.alpha_index,'alpha':alpha,'status':'ALL_AFFECTED_DESTINATIONS_PRICED' if len(receipts)==len(unique) else 'IN_PROGRESS','completed_destinations':receipts,'design_sha256':sha(D),'support_npz_sha256':sha(SUP/'DUAL_ROW_AND_AFFECTED_EVENT_SUPPORT.npz')})
  print(json.dumps({'alpha_index':args.alpha_index,'alpha':alpha,'completed_destinations':len(receipts),'of':len(unique),'destination':dest,'events':len(positions),'seconds':receipts[-1]['seconds']}),flush=True)
 with np.load(SEED) as z:hourly=z['od_hourly_pce'];short=z['od_static_shortest_cost']
 if np.max(np.abs(static-short[ids]))>1e-10:raise ValueError('original static base path mismatch')
 weighted=float(np.dot(hourly,short)+np.dot(hourly[ids]/model.release_steps,values-static))
 capterm=float(np.dot(model.capacity_for_rows(rows),lam));lower=weighted-capterm;upper=float(d['accepted_feasible_upper'])
 if lower>upper+1e-6:raise ValueError('full original weak duality')
 profile=alpha_dir/'ALL_AFFECTED_ORIGINAL_PRICE_VALUES.npz';np.savez_compressed(profile,minimum_adjusted_price=values)
 result={'schema':'SHARED_CG_DEV26_ONE_ALPHA_FULL_ORIGINAL_Q_DUAL_BLEND_R1','status':'FULL_ORIGINAL_AFFECTED_EVENT_PRICE_PENDING_INDEPENDENT_CSV_AUDIT','alpha_index':args.alpha_index,'alpha':alpha,'design_sha256':sha(D),'source_hashes':model.source_hashes,'original_OD_count':len(model.od),'original_commodity_events':model.K,'source_proven_unaffected_events':model.K-len(ids),'individually_priced_affected_events':len(ids),'priced_destinations':len(unique),'positive_original_capacity_rows':len(rows),'demand_weighted_original_adjusted_minimum':weighted,'original_capacity_price_term':capterm,'exact_full_original_graph_dual_lower':lower,'accepted_source_feasible_upper':upper,'relative_open_gap':(upper-lower)/upper,'profile_sha256':sha(profile),'stage_receipt_sha256':sha(stage),'seconds':time.monotonic()-began,'scope':'one frozen blend weight; nonnegative original capacity prices and source-AON unaffected-event proof; no CG optimum claim'}
 save(alpha_dir/'RESULT.json',result);print(json.dumps({k:result[k] for k in ('alpha','exact_full_original_graph_dual_lower','relative_open_gap','seconds')}),flush=True)
if __name__=='__main__':main()
