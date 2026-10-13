"""One common sparse path-CG loop over a full finite-time model adapter.

Numerical update follows the accepted compact two-phase path CG: RMP,
full-network pricing, real column addition, and re-solve. No historical
solution/dual/pool is read. The implicit adapter avoids explicit arc dicts.
"""
from pathlib import Path
import argparse,hashlib,json,math,os,time,traceback
import numpy as np
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.explicit_graph import ExplicitTimeGraph
from shared_cg.sparse_rmp import solve_master
from shared_cg.fifo_seed import load_fifo_seed
from shared_cg.uniform_release import run_uniform_release

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()

def save_json(path,x):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix(path.suffix+".tmp")
 temp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 os.replace(temp,path)

def pack_columns(out,columns):
 commodity=np.array([x.commodity for x in columns],dtype=np.int32)
 cost=np.array([x.objective_cost for x in columns],dtype=np.float64)
 rlen=np.array([len(x.resources) for x in columns],dtype=np.int64)
 plen=np.array([len(x.edge_time) for x in columns],dtype=np.int64)
 roff=np.r_[0,np.cumsum(rlen)]
 poff=np.r_[0,np.cumsum(plen)]
 resources=np.concatenate([x.resources for x in columns]) if roff[-1] else np.empty(0,dtype=np.int32)
 paths=np.concatenate([x.edge_time for x in columns]) if poff[-1] else np.empty(0,dtype=np.int32)
 identity=np.array([x.identity for x in columns],dtype="U32")
 np.savez_compressed(out,commodity=commodity,cost=cost,
                     resource_offset=roff,resource_flat=resources,
                     edge_time_offset=poff,edge_time_flat=paths,identity=identity)

def write_stage_checkpoint(output,columns,master,round_number,config_sha,audit,price,gap,slot):
 """Two alternating atomic slots preserve one complete solved RMP at a stage boundary.

 The receipt is written last. A terminated future round cannot erase both
 earlier complete slots. This is an operational snapshot, not a stop rule.
 """
 directory=Path(output)/"STAGE_CHECKPOINTS"/("slot_a" if slot==0 else "slot_b")
 directory.mkdir(parents=True,exist_ok=True)
 pool=directory/"COLUMN_POOL.npz";pool_tmp=directory/"COLUMN_POOL.tmp.npz"
 rmp=directory/"RMP.npz";rmp_tmp=directory/"RMP.tmp.npz"
 pack_columns(pool_tmp,columns[:master.path_variable_count])
 np.savez_compressed(rmp_tmp,x=master.optimization.x,
                     capacity_rows=master.capacity_rows,
                     equality_dual=master.equality_dual,
                     capacity_dual=master.capacity_dual,
                     phase=np.array(["II"]))
 os.replace(pool_tmp,pool);os.replace(rmp_tmp,rmp)
 rec={"schema":"SHARED_CG_STAGE_CHECKPOINT_R1","phase":"II",
      "round":round_number,"config_sha256":config_sha,
      "pool_path":str(pool),"pool_sha256":sha(pool),
      "rmp_path":str(rmp),"rmp_sha256":sha(rmp),
      "column_count":master.path_variable_count,
      "internal_original_primal_audit":audit,
      "internal_full_graph_lower_bound":price["full_graph_lagrangian_lower_bound"],
      "internal_relative_gap_raw":gap,
      "status":"PENDING_INDEPENDENT_ORIGINAL_GRAPH_PRIMAL_AUDIT"}
 save_json(directory/"CHECKPOINT_RECEIPT.json",rec)
 save_json(Path(output)/"LATEST_STAGE_CHECKPOINT.json",rec)
 return rec

def price_batch(model,master,phase,seen,max_new,epsilon):
 dual=np.zeros(model.resource_count,dtype=np.float64)
 dual[master.capacity_rows]=master.capacity_dual
 offers=[]
 min_adjusted=np.empty(model.K,dtype=np.float64)
 min_rc=math.inf
 calls=0
 for dest in model.destinations:
  dist,choice=model.price_destination(dest,dual,phase,epsilon)
  calls+=1
  ids=np.flatnonzero(model.destination==dest)
  for k in ids:
   k=int(k)
   distance=float(dist[int(model.release[k]),int(model.origin[k])]) if model.graph_kind=="implicit" else float(dist[int(model.origin[k])])
   if not math.isfinite(distance):raise ValueError(f"unreachable full-graph commodity {k}")
   min_adjusted[k]=distance
   rc=distance-float(master.equality_dual[k])
   min_rc=min(min_rc,rc)
   if rc<-1e-6:
    col=model.path_from_choice(k,dist,choice)
    if col.identity not in seen[k]:
     offers.append((rc,k,col))
 offers.sort(key=lambda x:(x[0]*float(model.q[x[1]]),x[0],x[1],x[2].identity))
 lower=float(np.dot(model.q,min_adjusted)+
             np.dot(model.capacity_for_rows(master.capacity_rows),master.capacity_dual))
 return offers[:max_new],{"minimum_reduced_cost":min_rc,
                          "full_graph_lagrangian_lower_bound":lower,
                          "negative_novel_candidates":len(offers),
                          "destination_pricing_calls":calls}

def export_full_graph_potentials(model,master,output):
 directory=Path(output)/"FULL_GRAPH_POTENTIALS"
 directory.mkdir(parents=True,exist_ok=True)
 dual=np.zeros(model.resource_count,dtype=np.float64)
 dual[master.capacity_rows]=master.capacity_dual
 records=[]
 for dest in model.destinations:
  dist,_=model.price_destination(dest,dual,"II")
  path=directory/("destination_"+str(int(dest))+".npz")
  np.savez_compressed(path,potential=dist,destination=np.array([dest],dtype=np.int32))
  records.append({"destination_node_index":int(dest),"path":str(path),"sha256":sha(path),
                  "finite_states":int(np.count_nonzero(np.isfinite(dist)))})
 return records

def primal_audit(model,columns,master):
 P=len(columns)
 x=np.asarray(master.optimization.x[:P],dtype=np.float64)
 qgot=np.bincount(np.array([c.commodity for c in columns],dtype=np.int32),
                  weights=x,minlength=model.K)
 residual=np.abs(qgot-model.q)
 max_od=float(np.max(residual))
 max_relative_od=float(np.max(residual/model.q))
 loads={}
 for c,flow in zip(columns,x):
  if flow<=1e-11:continue
  for row in c.resources:
   r=int(row);loads[r]=loads.get(r,0.0)+float(flow)
 max_cap=max((max(0.0,load-model.capacity_for_rows(np.array([row],dtype=np.int64))[0])
              for row,load in loads.items()),default=0.0)
 objective=float(sum(float(flow)*c.objective_cost for c,flow in zip(columns,x)))
 return {"max_original_commodity_residual":max_od,
         "max_relative_original_commodity_residual":max_relative_od,
         "max_original_capacity_excess":max_cap,
         "positive_columns":int(np.count_nonzero(x>1e-10)),
         "used_capacity_rows":len(loads),"objective_reconstructed":objective}

def run(config_path):
 path=Path(config_path)
 cfg=json.loads(path.read_text(encoding="utf-8-sig"))
 output=Path(cfg["output_dir"])
 if output.exists() and any(output.iterdir()):
  raise FileExistsError("nonempty output: "+str(output))
 output.mkdir(parents=True,exist_ok=True)
 if cfg.get("graph_type")=="uniform_release_implicit":
  return run_uniform_release(path,cfg,output)
 started=time.monotonic()
 if cfg.get("graph_type","implicit")=="implicit":
  model=ImplicitTimeGraph(cfg["source_dir"],cfg["dt_seconds"],
                          cfg["horizon_steps"],cfg["release_steps"],
                          cfg["demand_factor"])
 elif cfg["graph_type"]=="explicit":
  model=ExplicitTimeGraph(cfg["input_manifest"])
 else:raise ValueError("unknown graph type")
 if cfg["expected_source_hashes"]!=model.source_hashes:
  raise ValueError("source input hash changed")
 if model.K!=cfg["expected_commodity_events"]:
  raise ValueError("full demand release count changed")
 save_json(output/"MODEL_IDENTITY.json",model.model_identity)
 summary={"schema":"SHARED_CG_IMPLICIT_SOLVE_R1","build_id":cfg["build_id"],
          "config_path":str(path),"config_sha256":sha(path),
          "source_files":{str(Path(__file__).resolve()):sha(__file__),
                          str(Path(__file__).with_name("implicit_graph.py")):sha(Path(__file__).with_name("implicit_graph.py")),
                          str(Path(__file__).with_name("sparse_rmp.py")):sha(Path(__file__).with_name("sparse_rmp.py")),
                          str(Path(__file__).with_name("explicit_graph.py")):sha(Path(__file__).with_name("explicit_graph.py")),
                          str(Path(__file__).with_name("fifo_seed.py")):sha(Path(__file__).with_name("fifo_seed.py"))},
          "status":"RUNNING","model":model.model_identity,
          "phase_I_artificial_mass":None,"phase_II_objective":None,
          "full_graph_lower_bound":None,"history":[]}
 save_json(output/"RESULT.json",summary)
 epsilon=float(cfg["phase_I_tie_break_epsilon"])
 tolerance=float(cfg["relative_gap_tolerance"])
 max_new=int(cfg["max_new_columns_per_round"])
 wall=float(cfg["solver_wall_seconds"])
 columns=[];seen=[set() for _ in range(model.K)]
 initial_price_calls=0
 if cfg.get("feasible_fifo_seed_npz"):
  if model.graph_kind!="implicit":raise ValueError("FIFO seed requires implicit original graph")
  columns,seed_weights,seed_receipt=load_fifo_seed(model,cfg["feasible_fifo_seed_npz"],cfg["expected_seed_sha256"])
  for col in columns:seen[int(col.commodity)].add(col.identity)
  summary["feasible_seed_verification"]=seed_receipt
  summary["phase_I_artificial_mass"]=0.0
  summary["phase_I_status"]="FEASIBLE_SEED_ORIGINAL_GRAPH_VERIFIED"
  phase_sequence=("II",)
 else:
  zeros=np.zeros(model.resource_count,dtype=np.float64)
  for dest in model.destinations:
   dist,choice=model.price_destination(dest,zeros,"II",epsilon)
   initial_price_calls+=1
   ids=np.flatnonzero(model.destination==dest)
   for k in ids:
    col=model.path_from_choice(int(k),dist,choice)
    columns.append(col);seen[int(k)].add(col.identity)
  columns.sort(key=lambda c:c.commodity)
  phase_sequence=("I","II")
 zero_age=[0]*len(columns)
 pending_gc=False
 summary["input_seed_columns"]=len(columns)
 summary["initial_destination_pricing_calls"]=initial_price_calls
 save_json(output/"RESULT.json",summary)
 rmp_calls=0;pricing_calls=initial_price_calls;added=0
 final=None
 for phase in phase_sequence:
  rounds=int(cfg["phase_I_max_rounds"] if phase=="I" else cfg["phase_II_max_rounds"])
  for iteration in range(1,rounds+1):
   if time.monotonic()-started>wall:
    summary["status"]="WALL_BUDGET_CHECKPOINT";break
   if phase=="II" and pending_gc:
    count=np.bincount(np.fromiter((int(c.commodity) for c in columns),dtype=np.int32,count=len(columns)),minlength=model.K)
    survivors=[];surviving_age=[];removed=0
    for col,age in zip(columns,zero_age):
     k=int(col.commodity)
     if age>=3 and count[k]>1:
      seen[k].discard(col.identity);count[k]-=1;removed+=1
     else:
      survivors.append(col);surviving_age.append(age)
    if np.any(count==0):raise ValueError("zero-column GC hid a commodity")
    columns=survivors;zero_age=surviving_age;pending_gc=False
    summary["history"][-1]["zero_columns_released_next_round"]=removed
    summary["history"][-1]["pool_after_exact_zero_gc"]=len(columns)
    save_json(output/"RESULT.json",summary)
   master=solve_master(model,columns,phase,epsilon,cfg["rmp_time_limit_seconds"])
   rmp_calls+=1
   if phase=="II":
    for i,x in enumerate(master.optimization.x[:master.path_variable_count]):
     zero_age[i]=zero_age[i]+1 if x==0.0 else 0
   offered,price=price_batch(model,master,phase,seen,max_new,epsilon)
   pricing_calls+=price["destination_pricing_calls"]
   audit=primal_audit(model,columns,master)
   upper=audit["objective_reconstructed"]
   lower=price["full_graph_lagrangian_lower_bound"]
   gap=(upper-lower)/max(abs(upper),1e-12) if phase=="II" else None
   row={"phase":phase,"round":iteration,"rmp_objective":float(master.optimization.fun),
        "true_primal_objective":upper if phase=="II" else None,
        "artificial_mass":master.artificial_total,"column_count":len(columns),
        "capacity_row_count":master.capacity_row_count,
        "used_capacity_rows_before_exact_reduction":master.used_capacity_rows_before_exact_reduction,
        "exactly_redundant_capacity_rows":master.exactly_redundant_capacity_rows,
        "fixed_commodity_count":master.fixed_commodity_count,
        "reduced_master_path_variables":master.reduced_master_path_variables,
        "reduced_master_equality_rows":master.reduced_master_equality_rows,
        "minimum_reduced_cost":price["minimum_reduced_cost"],
        "full_graph_lower_bound":lower,"relative_gap_raw":gap,
        "novel_negative_candidates":price["negative_novel_candidates"],
        "added_columns":0,"wall_seconds":time.monotonic()-started}
   summary["history"].append(row)
   summary["rmp_calls"]=rmp_calls
   summary["destination_pricing_calls"]=pricing_calls
   summary["columns_added"]=added
   save_json(output/"RESULT.json",summary)
   final=(phase,master,audit,price,gap)
   checkpoint_every=int(cfg.get("checkpoint_every_rounds",0))
   if phase=="II" and checkpoint_every>0 and iteration%checkpoint_every==0:
    checkpoint=write_stage_checkpoint(output,columns,master,iteration,sha(path),audit,price,gap,
                                      (iteration//checkpoint_every)%2)
    summary["latest_stage_checkpoint"]=str(output/"LATEST_STAGE_CHECKPOINT.json")
    summary["latest_stage_checkpoint_round"]=iteration
    save_json(output/"RESULT.json",summary)
   if phase=="I" and master.artificial_total<=float(cfg["phase_I_artificial_tolerance"]):
    summary["phase_I_artificial_mass"]=master.artificial_total
    summary["phase_I_status"]="FEASIBLE_ARTIFICIAL_ZERO"
    break
   if phase=="II" and audit["max_original_commodity_residual"]<=1e-6 and audit["max_relative_original_commodity_residual"]<=float(cfg["release_relative_tolerance"]) and audit["max_original_capacity_excess"]<=1e-6 and abs(gap)<=tolerance+1e-10:
    summary["status"]="SOLVER_PRIMAL_DUAL_CLOSED"
    summary["phase_II_objective"]=upper
    summary["full_graph_lower_bound"]=lower
    summary["relative_gap_raw"]=gap
    break
   if not offered:
    summary["status"]="PHASE_"+phase+"_NO_NOVEL_NEGATIVE_COLUMN_WITH_OPEN_GAP"
    break
   for _,k,col in offered:
    columns.append(col);seen[k].add(col.identity);zero_age.append(0);added+=1
   if phase=="II" and iteration>=21 and iteration%3==0 and len(columns)>150000:pending_gc=True
   row["added_columns"]=len(offered)
   save_json(output/"RESULT.json",summary)
  if summary["status"]=="RUNNING" and not (phase=="I" and summary.get("phase_I_status")=="FEASIBLE_ARTIFICIAL_ZERO"):
   summary["status"]="PHASE_"+phase+"_ROUND_LIMIT_OPEN"
  if phase=="I" and summary.get("phase_I_status")!="FEASIBLE_ARTIFICIAL_ZERO":
   break
  if phase=="II":break
 if final:
  phase,master,audit,price,gap=final
  summary["last_phase"]=phase
  summary["last_primal_audit"]=audit
  summary["last_pricing"]=price
  summary["last_solved_column_count"]=master.path_variable_count
  summary["last_capacity_rows"]=master.capacity_row_count
  pack_columns(output/"COLUMN_POOL.npz",columns[:master.path_variable_count])
  np.savez_compressed(output/"LAST_RMP.npz",x=master.optimization.x,
                      capacity_rows=master.capacity_rows,
                      equality_dual=master.equality_dual,
                      capacity_dual=master.capacity_dual,
                      phase=np.array([phase]))
 if summary["status"]=="SOLVER_PRIMAL_DUAL_CLOSED":
  if model.graph_kind=="implicit":
   summary["full_graph_potentials_mode"]="INDEPENDENT_RECOMPUTE_FROM_SOURCE_AND_SAVED_DUAL"
   summary["full_graph_potentials_saved_count"]=0
  else:
   summary["full_graph_potentials"]=export_full_graph_potentials(model,master,output)
 summary["wall_seconds"]=time.monotonic()-started
 save_json(output/"RESULT.json",summary)
 print(json.dumps({k:summary.get(k) for k in ("status","phase_I_artificial_mass",
       "phase_II_objective","full_graph_lower_bound","rmp_calls","columns_added","wall_seconds")}))
 return 0 if summary["status"]=="SOLVER_PRIMAL_DUAL_CLOSED" else 2

def main():
 a=argparse.ArgumentParser()
 a.add_argument("--config",required=True)
 args=a.parse_args()
 try:return run(args.config)
 except Exception:
  print(traceback.format_exc(),flush=True)
  raise
if __name__=="__main__":raise SystemExit(main())

