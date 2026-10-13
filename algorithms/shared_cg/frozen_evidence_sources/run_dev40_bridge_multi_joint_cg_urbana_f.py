"""Fresh source-driven full-demand Urbana Q joint path-CG candidate.

The shared algorithm lives in shared_cg; this entry supplies only registered
source paths, time graph and exact original capacity-row mapping.
"""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,os,sys,time
import numpy as np
from scipy import sparse
R=Path(__file__).resolve().parent
CORE=R/'sparse_common_dev40_bridge_multi_cg'
sys.path.insert(0,str(CORE))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.rolling_price import RollingModel
from shared_cg.batch_rolling_paths import recover_many_paths
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.full_event_selection import StreamingEventSelector
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates
from shared_cg.joint_cg_loop import Candidate,JointState,run_joint_cg
DESIGN=R/'DEV40_BRIDGE_MULTI_JOINT_CG_DESIGN.json'
CFG=R/'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
SEED=R/'runs/dev35_cold_source_seed_urbana_f'
PROBE=R/'runs/dev40_bridge_source_probe/RESULT.json'
OUT=R/'runs/dev40_bridge_multi_joint_cg_urbana_f'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
 tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');os.replace(tmp,p)
def path_signature(f,edge,entry):
 h=hashlib.sha256();h.update(np.asarray([f],np.int64).tobytes())
 h.update(np.asarray(edge,np.int32).tobytes());h.update(np.asarray(entry,np.int32).tobytes())
 return h.hexdigest()
def save_pool(path,offers):
 offsets=[0];edge=[];entry=[];fragment=[];signatures=[]
 for col,ee,tt,f,sig in offers:
  edge.extend(map(int,ee));entry.extend(map(int,tt));offsets.append(len(edge))
  fragment.append(int(f));signatures.append(sig)
 tmp=path.with_suffix('.partial.npz')
 np.savez_compressed(tmp,edge_offset=np.asarray(offsets,np.int64),original_edge_index=np.asarray(edge,np.int32),
  original_entry_step=np.asarray(entry,np.int32),source_event_key=np.asarray(fragment,np.int64),
  signature=np.asarray(signatures,dtype='U64'))
 os.replace(tmp,path)
def main():
 begin=time.monotonic()
 design=rd(DESIGN);cfg=rd(CFG);seed=rd(SEED/'RECEIPT.json')
 if sha(CFG)!=design['source_config_sha256'] or sha(SEED/'RECEIPT.json')!=design['fresh_seed_receipt_sha256']:
  raise ValueError('frozen cold source/seed drift')
 for name,want in design['core_module_sha256'].items():
  if sha(CORE/'shared_cg'/name)!=want:raise ValueError('common candidate module drift '+name)
 if sha(Path(__file__))!=design['runner_sha256']:raise ValueError('cold solver entry drift')
 if seed['status']!='PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED':
  raise ValueError('fresh source seed not independently accepted')
 model=ImplicitTimeGraph(cfg['source_dir'],cfg['dt_seconds'],cfg['horizon_steps'],cfg['release_steps'],cfg['demand_factor'])
 if model.source_hashes!=cfg['expected_source_hashes'] or model.K!=design['original_release_events']:
  raise ValueError('original full-Q source identity')
 aon=SEED/'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz';fifo=SEED/'fifo/FRAGMENTS.npz'
 if sha(aon)!=seed['AON_path_sha256'] or sha(fifo)!=seed['FIFO_fragment_sha256']:
  raise ValueError('fresh base path identity')
 base=FullUniformQBase(model,aon,fifo);oracle=RollingModel.from_implicit(model)
 bridge=SourceBridgePrefixCandidates(model,base)
 probe=rd(PROBE)
 if sha(PROBE)!=design['source_probe_sha256'] or probe['status']!='PASS_SOURCE_ONLY_FULL_ORIGINAL_PATH_REPLAY' or probe['source_hashes']!=model.source_hashes or probe['bridge_edge_original_index']!=bridge.edge:
  raise ValueError('independent source bridge probe identity')
 if len(base.fod)<1 or np.max(abs(base.fm))<=0:raise ValueError('missing original source fragment base')
 policy=design['algorithm_policy']
 dest_by_od=np.array([x[3] for x in model.od],np.int32)
 origin_by_od=np.array([x[2] for x in model.od],np.int32)
 fifo_dest=dest_by_od[base.fod]
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'RESULT.json').exists():raise FileExistsError('completed cold candidate exists')
 checkpoint=OUT/'STAGE_CHECKPOINT.json'
 all_offers=[]
 if checkpoint.exists():
  cp=rd(checkpoint)
  if cp['design_sha256']!=sha(DESIGN) or cp['status']!='POOL_ADDED_PENDING_NEXT_RMP':
   raise ValueError('incompatible cold CG stage')
  with np.load(OUT/'STATE.npz') as z:
   rows=z['original_rows'];rhs=z['residual_capacity'];cost=z['delta_cost'];group=z['column_group']
   mass=z['group_mass'];keys=z['group_key'];signatures=z['column_signature']
  if cp['state_sha256']!=sha(OUT/'STATE.npz') or cp['matrix_sha256']!=sha(OUT/'STATE_MATRIX.npz'):
   raise ValueError('checkpoint array drift')
  state=JointState(sparse.load_npz(OUT/'STATE_MATRIX.npz'),rows,rhs,cost,group,mass,list(map(int,keys)),list(map(str,signatures)),base.residual_capacity)
  with np.load(OUT/'RECOVERED_PATH_POOL.npz') as z:pool={k:z[k].copy() for k in z.files}
  if cp['path_pool_sha256']!=sha(OUT/'RECOVERED_PATH_POOL.npz'):raise ValueError('checkpoint path pool drift')
  for j,f in enumerate(pool['source_event_key']):
   lo=int(pool['edge_offset'][j]);hi=int(pool['edge_offset'][j+1])
   all_offers.append((None,pool['original_edge_index'][lo:hi],pool['original_entry_step'][lo:hi],int(f),str(pool['signature'][j])))
  completed=int(cp['completed_rounds'])
 else:
  state=JointState(sparse.csr_matrix((0,0)),[],[],[],[],[],[],[],base.residual_capacity)
  completed=0
 price_receipts=[];exact_receipts=[]
 def price(lambda_by_row,nu_by_key,mode):
  active={int(r):float(v) for r,v in lambda_by_row.items() if v>1e-12}
  rows=np.fromiter(active,dtype=np.int64);lam=np.fromiter(active.values(),dtype=np.float64)
  t0=time.monotonic()
  if mode=='exact':
   weighted=0.
   for dest in model.destinations:
    ids=np.array([i for i,item in enumerate(model.od) if int(item[3])==int(dest)],np.int32)
    origins=origin_by_od[ids]
    release=np.tile(np.arange(model.release_steps,dtype=np.int32),len(ids))
    values=oracle.price(int(dest),release,np.repeat(origins,model.release_steps),rows,lam).reshape(len(ids),model.release_steps)
    weighted+=float(np.dot(base.hourly[ids]/model.release_steps,np.sum(values,axis=1)))
   lower=weighted-float(np.dot(model.capacity_for_rows(rows),lam))
   rec={'mode':'exact','original_events':model.K,'capacity_price_rows':len(rows),'full_original_lower':lower,'seconds':time.monotonic()-t0}
   exact_receipts.append(rec);print(json.dumps(rec),flush=True)
   return [],{'full_original_lower':lower,'minimum_reduced_cost':-np.inf}
  selector=StreamingEventSelector(model.release_steps,window_steps=2048,chosen_windows=4,
                                  per_window=80,per_od_window=4,total=320,epsilon=1e-6)
  calls=0
  freeflow_shortcut=(not active and not nu_by_key)
  for dest in model.destinations:
   fragments=np.flatnonzero(fifo_dest==dest).astype(np.int64)
   unsplit=base.unsplit_od[dest_by_od[base.unsplit_od]==dest]
   if freeflow_shortcut:unsplit=np.empty(0,dtype=np.int32)
   other=(base.n_fragments+np.repeat(unsplit,model.release_steps).astype(np.int64)*model.release_steps+
          np.tile(np.arange(model.release_steps,dtype=np.int64),len(unsplit)))
   keys=np.r_[fragments,other]
   if not len(keys):continue
   i,r,m,c=base.event_arrays(keys)
   adjusted=oracle.price(int(dest),r,origin_by_od[i],rows,lam)
   toll=base.base_toll_keys(keys,active)
   nu=np.fromiter((nu_by_key.get(int(k),0.) for k in keys),dtype=np.float64,count=len(keys))
   selector.add(keys,i,r,m,adjusted,c,toll,nu)
   calls+=1
  selected,selected_windows=selector.select()
  offers=[];sweeps=0
  for dest in model.destinations:
   chosen=[x for x in selected if dest_by_od[x.od]==dest]
   if not chosen:continue
   keys=np.asarray([x.key for x in chosen],np.int64)
   i,r,m,c=base.event_arrays(keys)
   recovered=recover_many_paths(oracle,int(dest),origin_by_od[i],r,rows,lam,
                                window_steps=2048,max_windows_per_path=28)
   sweeps+=recovered.full_horizon_sweeps
   for j,key in enumerate(keys):
    if abs(float(recovered.adjusted_cost[j])-chosen[j].adjusted_cost)>1e-6:
     raise ValueError('same-dual original path recovery')
    ee=recovered.original_edge_index[j];tt=recovered.original_entry_step[j]
    sig=path_signature(int(key),ee,tt)
    after=Counter(int(model.physical_pos[int(e)])*model.H+int(t) for e,t in zip(ee,tt) if model.physical_pos[int(e)]>=0)
    before=base.base_rows(int(key))
    delta={row:after.get(row,0)-before.get(row,0) for row in after.keys()|before.keys()}
    delta={row:value for row,value in delta.items() if value}
    delta_cost=float(recovered.raw_cost[j]-c[j])
    if not delta and abs(delta_cost)<=1e-14:continue
    w=int(r[j]//2048);diverse=(int(i[j]),w,int(min(delta)//model.H) if delta else -1)
    col=Candidate(int(key),float(m[j]),delta_cost,tuple(sorted(delta.items())),sig,diverse,'full_graph')
    offers.append(col);all_offers.append((col,ee.copy(),tt.copy(),int(key),sig))
  bridge_fragments,bridge_windows=bridge.select(
   max_events=int(policy['max_bridge_recovered_per_round']),
   per_od_window=4,window_steps=2048,chosen_windows=4)
  bridge_recovered=0
  for f in bridge_fragments:
   ee,tt,raw=bridge.recover(int(f))
   sig=path_signature(int(f),ee,tt)
   after=Counter(int(model.physical_pos[int(e)])*model.H+int(t)
                 for e,t in zip(ee,tt) if model.physical_pos[int(e)]>=0)
   before=base.base_rows(int(f))
   delta={row:after.get(row,0)-before.get(row,0) for row in after.keys()|before.keys()}
   delta={row:value for row,value in delta.items() if value}
   change=float(raw-base.donor_cost[int(f)])
   if not delta and abs(change)<=1e-14:continue
   i=int(base.fod[int(f)]);w=int(base.fr[int(f)]//2048)
   diverse=(i,w,int(min(delta)//model.H) if delta else -1)
   col=Candidate(int(f),float(base.fm[int(f)]),change,
                 tuple(sorted(delta.items())),sig,diverse,'bridge_prefix')
   offers.append(col);all_offers.append((col,ee.copy(),tt.copy(),int(f),sig))
   bridge_recovered+=1
  rec={'mode':'partial','original_events_total':model.K,'events_priced':selector.events_priced,
       'freeflow_unsplit_shortcut':freeflow_shortcut,'destination_calls':calls,
       'capacity_price_rows':len(rows),'negative_events':selector.negative_events,
       'selected_windows':selected_windows,'selected_events':len(selected),
       'recovered_paths':len(offers),'bridge_recovered_paths':bridge_recovered,'bridge_selected_windows':bridge_windows,'bridge_edge_original_index':bridge.edge,'full_horizon_recovery_sweeps':sweeps,
       'minimum_reduced_cost':selector.minimum_reduced_cost,'seconds':time.monotonic()-t0}
  price_receipts.append(rec);print(json.dumps(rec),flush=True)
  return offers,{'minimum_reduced_cost':selector.minimum_reduced_cost}
 def checkpoint_after_add(state,history):
  sparse.save_npz(OUT/'STATE_MATRIX.partial.npz',state.A)
  os.replace(OUT/'STATE_MATRIX.partial.npz',OUT/'STATE_MATRIX.npz')
  np.savez_compressed(OUT/'STATE.partial.npz',original_rows=np.asarray(state.rows,np.int64),
   residual_capacity=np.asarray(state.rhs),delta_cost=np.asarray(state.cost),
   column_group=np.asarray(state.group,np.int32),group_mass=np.asarray(state.mass),
   group_key=np.asarray(state.keys,np.int32),column_signature=np.asarray(state.column_signatures,dtype='U64'))
  os.replace(OUT/'STATE.partial.npz',OUT/'STATE.npz')
  save_pool(OUT/'RECOVERED_PATH_POOL.npz',all_offers)
  save(checkpoint,{'schema':'DEV40_BRIDGE_MULTI_CG_STAGE','status':'POOL_ADDED_PENDING_NEXT_RMP',
   'design_sha256':sha(DESIGN),'completed_rounds':completed+len(history),
   'column_count':state.A.shape[1],'original_rows':len(state.rows),
   'matrix_sha256':sha(OUT/'STATE_MATRIX.npz'),'state_sha256':sha(OUT/'STATE.npz'),
   'path_pool_sha256':sha(OUT/'RECOVERED_PATH_POOL.npz'),
   'history':history,'source_hashes':model.source_hashes})
 remaining=int(policy['max_rounds'])-completed
 if remaining>0:
  status,master,history=run_joint_cg(state,price,max_rounds=remaining,
   max_new_per_round=int(policy['max_new_columns_per_round']),max_per_group=2,
   epsilon=1e-7,rmp_seconds=float(design['resources']['RMP_seconds_each']),
   stabilization_alpha=float(policy['stabilization_alpha_initial']),
   lane_minimums={'bridge_prefix':int(policy['bridge_lane_minimum_new_columns'])},checkpoint=checkpoint_after_add)
 else:
  status='ROUND_LIMIT_OPEN';history=cp.get('history',[])
 final=state.solve(float(design['resources']['RMP_seconds_each']))
 if final.max_capacity_excess>1e-7 or final.max_group_excess>1e-8:
  raise ValueError('cold source joint RMP original rows')
 checkpoint_after_add(state,history)
 np.savez_compressed(OUT/'FINAL_RMP.npz',original_rows=np.asarray(state.rows,np.int64),
  residual_capacity=np.asarray(state.rhs),delta_cost=np.asarray(state.cost),
  column_group=np.asarray(state.group,np.int32),group_mass=np.asarray(state.mass),
  group_key=np.asarray(state.keys,np.int32),column_signature=np.asarray(state.column_signatures,dtype='U64'),
  flow=final.y,capacity_mu=final.capacity_mu,group_mu=final.group_mu)
 upper=float(seed['independent_feasible_upper']+final.objective_delta)
 result={'schema':'DEV40_BRIDGE_MULTI_ORIGINAL_Q_JOINT_CG','status':status,
  'case_id':cfg['case_id'],'build_id':design['core_build_id'],'source_hashes':model.source_hashes,
  'design_sha256':sha(DESIGN),'runner_sha256':sha(Path(__file__)),
  'original_positive_OD':len(model.od),'original_release_events':model.K,
  'fresh_seed_receipt_sha256':sha(SEED/'RECEIPT.json'),
  'initial_columns':0,'new_columns':state.A.shape[1],'represented_source_events_or_fragments':len(state.keys),
  'source_fragment_count':len(base.fod),'source_selected_bridge_edge':bridge.edge,'source_bridge_weighted_wait_steps_PCE':bridge.weighted_wait_steps,'source_bridge_eligible_fragments':len(bridge.eligible),'unsplit_original_OD':len(base.unsplit_od),'all_original_event_count':model.K,'round_history':history,
  'partial_price_receipts':price_receipts,'exact_price_receipts':exact_receipts,
  'fresh_source_base_upper':seed['independent_feasible_upper'],
  'candidate_upper_pending_independent_replay':upper,
  'historical_best_independent_upper_evaluation_only':design['historical_best_evaluation_only']['upper'],
  'final_RMP_iterations':final.iterations,
  'final_positive_columns':int(np.count_nonzero(final.y>1e-10)),
  'final_max_original_touched_capacity_excess':final.max_capacity_excess,
  'final_max_group_demand_excess':final.max_group_excess,
  'final_rmp_sha256':sha(OUT/'FINAL_RMP.npz'),
  'final_matrix_sha256':sha(OUT/'STATE_MATRIX.npz'),
  'path_pool_sha256':sha(OUT/'RECOVERED_PATH_POOL.npz'),
  'wall_seconds':time.monotonic()-begin,
  'scientific_limit':'Fresh source cold-start original Q candidate, partial pricing rounds; not full CG closure or final 16-case build.'}
 save(OUT/'RESULT.json',result)
 print(json.dumps({k:result[k] for k in ('status','new_columns','represented_source_events_or_fragments','candidate_upper_pending_independent_replay','historical_best_independent_upper_evaluation_only','wall_seconds')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
