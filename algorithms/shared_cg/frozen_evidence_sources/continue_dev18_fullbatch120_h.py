"""Generic compatible H-stage continuation with a positive-flow-only final artifact.

The complete graph is repriced at the base stage to reconstruct pending columns.
This is a development continuation, never a final-build cold-start regression.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'sparse_common_dev18_demand_weighted_columns'))
from types import SimpleNamespace
import json,math,os,time
import numpy as np
from shared_cg.implicit_graph import ImplicitTimeGraph,PathColumn
from shared_cg.sparse_rmp import solve_master
from shared_cg.solve import sha,save_json,pack_columns,price_batch,primal_audit,write_stage_checkpoint

def _pool_columns(path):
 with np.load(path,allow_pickle=False) as p:
  commodity=p['commodity'];cost=p['cost'];roff=p['resource_offset'];resources=p['resource_flat'];poff=p['edge_time_offset'];edge_time=p['edge_time_flat'];identity=p['identity']
  if len(commodity)!=len(cost) or len(roff)!=len(commodity)+1 or len(poff)!=len(commodity)+1 or len(identity)!=len(commodity):raise ValueError('base pool shape')
  columns=[]
  for i in range(len(commodity)):
   columns.append(PathColumn(int(commodity[i]),float(cost[i]),resources[int(roff[i]):int(roff[i+1])].copy(),edge_time[int(poff[i]):int(poff[i+1])].copy(),float(cost[i]),str(identity[i])))
 return columns

def run_positive_resume(config_path,cfg):
 config_path=Path(config_path);output=Path(cfg['output_dir'])
 if output.exists() and any(output.iterdir()):raise FileExistsError('nonempty positive resume output')
 base_config_path=Path(cfg['resume_base_config']);base_cfg=json.loads(base_config_path.read_text(encoding='utf-8-sig'))
 keys=('case_id','graph_type','source_dir','expected_source_hashes','dt_seconds','horizon_steps','release_steps','demand_factor','expected_commodity_events','phase_I_tie_break_epsilon','phase_I_max_rounds','max_new_columns_per_round','phase_I_artificial_tolerance','relative_gap_tolerance','rmp_time_limit_seconds','solver_wall_seconds','release_relative_tolerance','feasible_fifo_seed_npz','expected_seed_sha256','checkpoint_every_rounds')
 for key in keys:
  if cfg.get(key)!=base_cfg.get(key):raise ValueError('incompatible scientific/resume field '+key)
 if cfg['graph_type']!='implicit' or cfg['phase_II_max_rounds']!=120 or base_cfg['phase_II_max_rounds']!=60:raise ValueError('implicit H 60-round stage only')
 bp=Path(cfg['resume_from']);base=json.loads(bp.read_text(encoding='utf-8'))
 if base['phase']!='II' or base['config_sha256']!=sha(base_config_path):raise ValueError('base checkpoint config')
 base_pool=Path(base['pool_path']);base_rmp=Path(base['rmp_path'])
 if sha(base_pool)!=base['pool_sha256'] or sha(base_rmp)!=base['rmp_sha256']:raise ValueError('base checkpoint SHA')
 base_result_path=Path(cfg['resume_base_result'])
 base_result=json.loads(base_result_path.read_text(encoding='utf-8'))
 prior=[r for r in base_result['history'] if r['phase']=='II' and r['round']==base['round']]
 if len(prior)!=1 or base['round']<1 or base['round']>=cfg['phase_II_max_rounds']:raise ValueError('base solved stage history')
 output.mkdir(parents=True)
 started=time.monotonic()
 model=ImplicitTimeGraph(cfg['source_dir'],cfg['dt_seconds'],cfg['horizon_steps'],cfg['release_steps'],cfg['demand_factor'])
 if model.source_hashes!=cfg['expected_source_hashes'] or model.K!=cfg['expected_commodity_events']:raise ValueError('source/model drift')
 save_json(output/'MODEL_IDENTITY.json',model.model_identity)
 columns=_pool_columns(base_pool)
 if len(columns)!=base['column_count']:raise ValueError('base pool count')
 seen=[set() for _ in range(model.K)]
 for col in columns:
  if col.commodity<0 or col.commodity>=model.K:raise ValueError('invalid base commodity')
  if col.identity in seen[col.commodity]:raise ValueError('duplicate base column')
  seen[col.commodity].add(col.identity)
 if any(not identities for identities in seen):raise ValueError('base hides original commodity')
 with np.load(base_rmp,allow_pickle=False) as r:
  if str(r['phase'][0])!='II' or len(r['x'])!=len(columns):raise ValueError('base RMP phase/shape')
  master=SimpleNamespace(capacity_rows=r['capacity_rows'],capacity_dual=r['capacity_dual'],equality_dual=r['equality_dual'])
 offers,base_price=price_batch(model,master,'II',seen,int(cfg['max_new_columns_per_round']),float(cfg['phase_I_tie_break_epsilon']))
 old=prior[0]
 for key,new in [('added_columns',len(offers)),('novel_negative_candidates',base_price['negative_novel_candidates'])]:
  if old[key]!=new:raise ValueError('pending base price differs: '+key)
 for key,new in [('minimum_reduced_cost',base_price['minimum_reduced_cost']),('full_graph_lower_bound',base_price['full_graph_lagrangian_lower_bound'])]:
  if abs(old[key]-new)>1e-7*max(1,abs(old[key])):raise ValueError('base price numeric drift: '+key)
 for _,k,col in offers:columns.append(col);seen[k].add(col.identity)
 resume={'schema':'SHARED_CG_GENERIC_H_POSITIVE_ONLY_RESUME_R1','base_config_path':str(base_config_path),'base_config_sha256':sha(base_config_path),'base_checkpoint':str(bp),'base_checkpoint_sha256':sha(bp),'base_pool_sha256':sha(base_pool),'base_rmp_sha256':sha(base_rmp),'base_result_path':str(base_result_path),'base_result_sha256':sha(base_result_path),'base_solved_round':base['round'],'reconstructed_pending_columns':len(offers),'zero_age_reset_conservative':True,'scientific_fields_compared':list(keys),'status':'BASE_PRICING_RECONSTRUCTED_FULL_GRAPH'}
 save_json(output/'RESUME_COMPATIBILITY.json',resume)
 summary={'schema':'SHARED_CG_POSITIVE_ONLY_RESUMED_IMPLICIT_H_R1','build_id':cfg['build_id'],'case_id':cfg['case_id'],'config_path':str(config_path),'config_sha256':sha(config_path),'source_hashes':model.source_hashes,'resume_compatibility':str(output/'RESUME_COMPATIBILITY.json'),'status':'RUNNING','history':[],'base_solved_round':base['round'],'base_pool_columns':base['column_count'],'base_pending_columns_added':len(offers),'phase_II_objective':None,'full_graph_lower_bound':None,'full_graph_potentials_mode':'INDEPENDENT_RECOMPUTE_FROM_SOURCE_AND_SAVED_DUAL'}
 save_json(output/'RESULT.json',summary)
 zero_age=[0]*len(columns);pending_gc=False;final=None
 epsilon=float(cfg['phase_I_tie_break_epsilon']);tol=float(cfg['relative_gap_tolerance'])
 for iteration in range(base['round']+1,int(cfg['phase_II_max_rounds'])+1):
  if time.monotonic()-started>float(cfg['solver_wall_seconds']):
   summary['status']='WALL_BUDGET_POSITIVE_STAGE_OPEN';break
  if pending_gc:
   count=np.bincount(np.fromiter((int(c.commodity) for c in columns),dtype=np.int32,count=len(columns)),minlength=model.K)
   survivors=[];ages=[];removed=0
   for col,age in zip(columns,zero_age):
    k=int(col.commodity)
    if age>=3 and count[k]>1:
     seen[k].discard(col.identity);count[k]-=1;removed+=1
    else:survivors.append(col);ages.append(age)
   if np.any(count==0):raise ValueError('GC hid original demand')
   columns=survivors;zero_age=ages;pending_gc=False
   summary['history'][-1]['zero_columns_released_next_round']=removed
  master=solve_master(model,columns,'II',epsilon,cfg['rmp_time_limit_seconds'])
  P=master.path_variable_count
  for i,x in enumerate(master.optimization.x[:P]):zero_age[i]=zero_age[i]+1 if x==0.0 else 0
  offered,price=price_batch(model,master,'II',seen,int(cfg['max_new_columns_per_round']),epsilon)
  audit=primal_audit(model,columns,master)
  upper=audit['objective_reconstructed'];lower=price['full_graph_lagrangian_lower_bound'];gap=(upper-lower)/max(abs(upper),1e-12)
  row={'phase':'II','round':iteration,'rmp_objective':float(master.optimization.fun),'true_primal_objective':upper,'full_graph_lower_bound':lower,'relative_gap_raw':gap,'column_count':len(columns),'solved_path_variables':P,'capacity_row_count':master.capacity_row_count,'fixed_commodity_count':master.fixed_commodity_count,'secondary_offers':price.get('sidetrack_novel_offers',0),'novel_negative_candidates':price['negative_novel_candidates'],'added_columns':0,'wall_seconds':time.monotonic()-started}
  summary['history'].append(row);summary['last_primal_audit']=audit;summary['last_pricing']=price
  final=(iteration,master,audit,price,gap,columns[:P])
  save_json(output/'RESULT.json',summary)
  if iteration%3==0:
   stage=write_stage_checkpoint(output,columns,master,iteration,sha(config_path),audit,price,gap,(iteration//3)%2)
   summary['latest_stage_checkpoint']=str(output/'LATEST_STAGE_CHECKPOINT.json')
   summary['latest_stage_checkpoint_round']=iteration
   save_json(output/'RESULT.json',summary)
  if audit['max_original_commodity_residual']<=1e-6 and audit['max_relative_original_commodity_residual']<=float(cfg['release_relative_tolerance']) and audit['max_original_capacity_excess']<=1e-6 and abs(gap)<=tol+1e-10:
   summary['status']='SOLVER_PRIMAL_DUAL_CLOSED';summary['phase_II_objective']=upper;summary['full_graph_lower_bound']=lower;summary['relative_gap_raw']=gap;break
  if not offered:summary['status']='PHASE_II_NO_NOVEL_NEGATIVE_COLUMN_WITH_OPEN_GAP';break
  for _,k,col in offered:columns.append(col);seen[k].add(col.identity);zero_age.append(0)
  if iteration>=21 and iteration%3==0 and len(columns)>150000:pending_gc=True
  row['added_columns']=len(offered);save_json(output/'RESULT.json',summary)
 if summary['status']=='RUNNING':summary['status']='PHASE_II_ROUND_LIMIT_OPEN'
 if final:
  iteration,master,audit,price,gap,solved_columns=final
  x=np.asarray(master.optimization.x[:master.path_variable_count],dtype=np.float64)
  positive=np.flatnonzero(x>0.0)
  if not len(positive):raise ValueError('no positive original flow')
  pcols=[solved_columns[int(i)] for i in positive]
  temp=output/'COLUMN_POOL.tmp.npz';pool=output/'COLUMN_POOL.npz'
  pack_columns(temp,pcols);os.replace(temp,pool)
  rmp=output/'LAST_RMP.npz'
  np.savez_compressed(rmp,x=x[positive],capacity_rows=master.capacity_rows,equality_dual=master.equality_dual,capacity_dual=master.capacity_dual,phase=np.array(['II']))
  checkpoint={'schema':'SHARED_CG_POSITIVE_FLOW_ONLY_STAGE_R1','phase':'II','round':iteration,'config_sha256':sha(config_path),'pool_path':str(pool),'pool_sha256':sha(pool),'rmp_path':str(rmp),'rmp_sha256':sha(rmp),'column_count':len(pcols),'full_restricted_master_columns_not_saved':master.path_variable_count,'status':'POSITIVE_FLOW_PRIMAL_AND_FULL_GRAPH_DUAL_ONLY','base_resume_compatibility_sha256':sha(output/'RESUME_COMPATIBILITY.json')}
  save_json(output/'LATEST_STAGE_CHECKPOINT.json',checkpoint)
  summary.update(last_solved_column_count=len(pcols),last_original_pool_columns=master.path_variable_count,last_capacity_rows=master.capacity_row_count,positive_only_primal_pool=True,latest_stage_checkpoint=str(output/'LATEST_STAGE_CHECKPOINT.json'))
 summary['wall_seconds']=time.monotonic()-started
 save_json(output/'RESULT.json',summary)
 print(json.dumps({'status':summary['status'],'base_round':base['round'],'final_round':final[0] if final else None,'upper':final[2]['objective_reconstructed'] if final else None,'raw_gap':final[4] if final else None,'positive_pool':summary.get('last_solved_column_count'),'wall_seconds':summary['wall_seconds']}),flush=True)
 return 0 if summary['status']=='SOLVER_PRIMAL_DUAL_CLOSED' else 2

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args()
 config_path=Path(args.config);config=json.loads(config_path.read_text(encoding='utf-8-sig'))
 raise SystemExit(run_positive_resume(config_path,config))

