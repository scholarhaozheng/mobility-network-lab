"""Independent original-input certificate for sparse implicit finite-time CG.

Reconstructs every path and capacity row from original CSV. Full-graph lower
bound uses saved node-time potentials, but verifies every legal travel, turn,
wait, and sink inequality with a separate kernel; it never calls producer
pricing or the producer RMP.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math,heapq
import numpy as np
from numba import njit

def rows(path):
 with Path(path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
@njit(cache=True)
def potential_residual(phi,H,dt,u,v,duration,cost,physical_pos,dual):
 worst=0.0;bad_reachability=0
 n=phi.shape[1]
 for t in range(H+1):
  if t<H:
   for node in range(n):
    a=phi[t,node];b=phi[t+1,node]
    if np.isfinite(a) and np.isfinite(b):
     z=a-(dt/60+b)
     if z>worst:worst=z
    elif not np.isfinite(a) and np.isfinite(b):
     bad_reachability+=1
  for e in range(len(u)):
   step=duration[e]
   if t+step>H:continue
   a=phi[t,u[e]];b=phi[t+step,v[e]]
   if np.isfinite(a) and np.isfinite(b):
    weight=cost[e]
    p=physical_pos[e]
    if p>=0:weight-=dual[p*H+t]
    z=a-(weight+b)
    if z>worst:worst=z
   elif not np.isfinite(a) and np.isfinite(b):
    bad_reachability+=1
 return worst,bad_reachability

@njit(cache=True)
def independent_reverse_distance(n,H,dest,u,v,duration,cost,physical_pos,
                                 zero_ptr,zero_edge,reverse_topo,dual,wait_cost):
 # Original-input time-DAG recurrence, separately implemented from producer.
 phi=np.full((H+1,n),np.inf,dtype=np.float64)
 for t in range(H,-1,-1):
  phi[t,dest]=0.0
  if t<H:
   for node in range(n):
    z=wait_cost+phi[t+1,node]
    if z<phi[t,node]:phi[t,node]=z
  for e in range(len(u)):
   step=duration[e]
   if step<=0 or t+step>H:continue
   z=cost[e]+phi[t+step,v[e]]
   p=physical_pos[e]
   if p>=0:z-=dual[p*H+t]
   if z<phi[t,u[e]]:phi[t,u[e]]=z
  for j in range(len(reverse_topo)):
   node=reverse_topo[j]
   for z in range(zero_ptr[node],zero_ptr[node+1]):
    e=zero_edge[z]
    cand=cost[e]+phi[t,v[e]]
    if cand<phi[t,node]:phi[t,node]=cand
 return phi

def verify(config_path):
 cfg=json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
 output=Path(cfg["output_dir"])
 result=json.loads((output/"RESULT.json").read_text(encoding="utf-8"))
 model_identity=json.loads((output/"MODEL_IDENTITY.json").read_text(encoding="utf-8"))
 if result["status"] not in ("SOLVER_PRIMAL_DUAL_CLOSED","PHASE_II_ROUND_LIMIT_OPEN"):raise ValueError("producer has no solved Phase II stage")
 if result["config_sha256"]!=sha(config_path):raise ValueError("config changed")
 source=Path(cfg["source_dir"])
 names=("network.csv","access.csv","assignment_od_pce.csv")
 hashes={n:sha(source/n) for n in names}
 if hashes!=cfg["expected_source_hashes"] or hashes!=model_identity["source_hashes"]:
  raise ValueError("original source hash changed")
 net=rows(source/"network.csv")
 access={r["zone_id"]:r["node_id"] for r in rows(source/"access.csv")}
 od=rows(source/"assignment_od_pce.csv")
 node_ids=sorted({r["from_node_id"] for r in net}|{r["to_node_id"] for r in net})
 node_ix={x:i for i,x in enumerate(node_ids)}
 u=np.array([node_ix[r["from_node_id"]] for r in net],dtype=np.int32)
 v=np.array([node_ix[r["to_node_id"]] for r in net],dtype=np.int32)
 cost=np.array([float(r["vdf_fftt"]) for r in net],dtype=np.float64)
 physical=np.array([r["arc_kind"]=="physical" for r in net],dtype=bool)
 dt=float(cfg["dt_seconds"]);H=int(cfg["horizon_steps"]);releases=int(cfg["release_steps"])
 duration=np.array([max(1,math.ceil(cost[e]*60/dt-1e-12)) if physical[e] else 0
                    for e in range(len(net))],dtype=np.int32)
 pidx=np.full(len(net),-1,dtype=np.int32)
 physical_edges=np.flatnonzero(physical)
 pidx[physical_edges]=np.arange(len(physical_edges),dtype=np.int32)
 cap=np.array([float(net[e]["capacity"])*dt/3600 for e in physical_edges],dtype=np.float64)
 K=len(od)*releases
 if K!=cfg["expected_commodity_events"]:raise ValueError("hidden or extra original demand")
 q=np.repeat(np.array([float(r["volume_pce"])*float(cfg["demand_factor"])/releases for r in od]),
             releases)
 origins=np.repeat(np.array([node_ix[access[r["o_zone_id"]]] for r in od],dtype=np.int32),releases)
 destinations=np.repeat(np.array([node_ix[access[r["d_zone_id"]]] for r in od],dtype=np.int32),releases)
 release=np.tile(np.arange(releases,dtype=np.int32),len(od))
 pool=np.load(output/"COLUMN_POOL.npz",allow_pickle=False)
 rmp=np.load(output/"LAST_RMP.npz",allow_pickle=False)
 commodity=pool["commodity"];cost_list=pool["cost"]
 roff=pool["resource_offset"];rflat=pool["resource_flat"]
 poff=pool["edge_time_offset"];pflat=pool["edge_time_flat"]
 P=len(commodity)
 x=rmp["x"]
 if str(rmp["phase"][0])!="II" or len(x)!=P:raise ValueError("not a final Phase II primal")
 cap_rows=rmp["capacity_rows"];mu=rmp["capacity_dual"]
 if len(cap_rows)!=len(mu) or len(np.unique(cap_rows))!=len(cap_rows) or np.any(mu>1e-8):
  raise ValueError("bad capacity dual")
 if np.any(cap_rows<0) or np.any(cap_rows>=len(physical_edges)*H):
  raise ValueError("capacity dual resource outside original graph")
 dense=np.zeros(len(physical_edges)*H,dtype=np.float64)
 dense[cap_rows]=mu
 demand_flow=np.zeros(K,dtype=np.float64)
 loads={}
 objective=0.0
 bad_mapping=0
 for j in range(P):
  k=int(commodity[j])
  if k<0 or k>=K:raise ValueError("unknown original commodity")
  path=pflat[int(poff[j]):int(poff[j+1])]
  if len(path)%2:raise ValueError("odd edge-time array")
  node=int(origins[k]);t=int(release[k]);value=0.0;resources=[]
  for edge,entry in zip(path[::2],path[1::2]):
   edge=int(edge);entry=int(entry)
   if entry!=t:raise ValueError("wrong departure/turn/wait time")
   if edge==-2:
    if t>=H:raise ValueError("wait past horizon")
    t+=1;value+=dt/60
   else:
    if edge<0 or edge>=len(net) or int(u[edge])!=node:
     raise ValueError("bad original edge or node continuity")
    if t+int(duration[edge])>H:raise ValueError("arrival outside frozen horizon")
    p=int(pidx[edge])
    if p>=0:resources.append(p*H+t)
    value+=float(cost[edge])
    node=int(v[edge]);t+=int(duration[edge])
  if node!=int(destinations[k]) or t>H:
   raise ValueError("hidden unserved OD or bad terminal mapping")
  claimed=rflat[int(roff[j]):int(roff[j+1])]
  if not np.array_equal(claimed,np.array(resources,dtype=np.int32)):
   raise ValueError("wrong original capacity mapping")
  if abs(value-float(cost_list[j]))>1e-7:
   raise ValueError("wrong original path cost")
  flow=float(x[j])
  if not math.isfinite(flow) or flow<-1e-8:raise ValueError("negative/nonfinite path flow")
  demand_flow[k]+=flow
  objective+=flow*value
  if flow>1e-11:
   for row in resources:loads[row]=loads.get(row,0.0)+flow
 residual=np.abs(demand_flow-q)
 max_demand=float(np.max(residual))
 max_relative_demand=float(np.max(residual/q))
 max_capacity=max((max(0.0,flow-cap[row//H]) for row,flow in loads.items()),default=0.0)
 if result["status"]=="SOLVER_PRIMAL_DUAL_CLOSED" and result.get("full_graph_potentials_mode")!="INDEPENDENT_RECOMPUTE_FROM_SOURCE_AND_SAVED_DUAL":
  raise ValueError("producer did not declare source-and-dual recomputation mode")
 zero=[[] for _ in node_ids];indegree=np.zeros(len(node_ids),dtype=np.int32)
 for e in range(len(net)):
  if int(duration[e])==0:
   zero[int(u[e])].append(e);indegree[int(v[e])]+=1
 queue=[i for i in range(len(node_ids)) if indegree[i]==0]
 heapq.heapify(queue);topo=[]
 while queue:
  node=heapq.heappop(queue);topo.append(node)
  for e in zero[node]:
   nxt=int(v[e]);indegree[nxt]-=1
   if indegree[nxt]==0:heapq.heappush(queue,nxt)
 if len(topo)!=len(node_ids):raise ValueError("original zero-time arcs cycle")
 ptr=np.zeros(len(node_ids)+1,dtype=np.int32);flat=[]
 for node,edges in enumerate(zero):
  ptr[node]=len(flat);flat.extend(edges)
 ptr[len(node_ids)]=len(flat)
 zero_edge=np.asarray(flat,dtype=np.int32)
 reverse_topo=np.asarray(topo[::-1],dtype=np.int32)
 dual_lower=float(np.dot(cap[cap_rows//H],mu))
 worst_inequality=0.0;bad_reachability=0
 for dest in sorted(set(destinations)):
  phi=independent_reverse_distance(len(node_ids),H,int(dest),u,v,duration,cost,pidx,
                                   ptr,zero_edge,reverse_topo,dense,dt/60)
  if phi.shape!=(H+1,len(node_ids)) or np.any(phi[:,int(dest)]>1e-8):
   raise ValueError("independent potential terminal condition")
  worst,bad=potential_residual(phi,H,dt,u,v,duration,cost,pidx,dense)
  worst_inequality=max(worst_inequality,float(worst));bad_reachability+=int(bad)
  ids=np.flatnonzero(destinations==dest)
  start=phi[release[ids],origins[ids]]
  if not np.all(np.isfinite(start)):raise ValueError("unreachable positive original demand")
  dual_lower+=float(np.dot(q[ids],start))
  del phi
 gap=(objective-dual_lower)/max(abs(objective),1e-12)
 certificate={"schema":"SHARED_CG_IMPLICIT_INDEPENDENT_CERT_R1",
  "status":"PASS_INDEPENDENT_PRIMAL_DUAL_OPEN_GAP" if max_demand<=1e-6 and max_relative_demand<=float(cfg["release_relative_tolerance"]) and max_capacity<=1e-6 and
    worst_inequality<=1e-7 and bad_reachability==0
    else "FAIL_INDEPENDENT_PRIMAL_DUAL_AUDIT",
  "original_source_hashes":hashes,"positive_original_commodity_events":K,
  "full_allowed_physical_arc_time_rows":len(physical_edges)*H,
  "pool_columns":P,"positive_columns":int(np.count_nonzero(x>1e-10)),
  "original_objective":objective,"verified_full_graph_dual_lower_bound":dual_lower,
  "relative_gap_raw":gap,"max_original_demand_residual":max_demand,
  "max_relative_release_demand_residual":max_relative_demand,
  "max_original_capacity_excess":max_capacity,
  "maximum_full_graph_potential_inequality_violation":worst_inequality,
  "bad_finite_reachability_arc_count":bad_reachability,
  "original_capacity_rows_used":len(loads),
  "pricing_verifier":"all original physical/turn/time/wait/sink inequalities, separate numba kernel",
  "producer_pricing_calls":result.get("destination_pricing_calls"),
  "independent_potential_method":"recomputed from original arcs, all waits, original H and saved sparse capacity dual; no producer potential files"}
 out=output/"INDEPENDENT_OPEN_DUAL_CERTIFICATE.json"
 out.write_text(json.dumps(certificate,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(certificate,indent=2))
 return 0 if certificate["status"]=="PASS_INDEPENDENT_PRIMAL_DUAL_OPEN_GAP" else 2

def main():
 a=argparse.ArgumentParser();a.add_argument("--config",required=True);args=a.parse_args()
 return verify(args.config)
if __name__=="__main__":raise SystemExit(main())
