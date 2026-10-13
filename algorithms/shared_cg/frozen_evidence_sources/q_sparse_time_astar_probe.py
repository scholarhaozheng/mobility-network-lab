"""Exact on-demand full-time A* pricing probe for one original Q commodity.

Nonnegative sparse capacity tolls, original travel/turn/wait/sink arcs, and
frozen horizon are respected. A complete query certifies one OD-release path;
a sample is never a full-Q closure certificate.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import argparse,csv,hashlib,heapq,json,math,time
import numpy as np
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
class SparseTimeAStar:
 def __init__(self,n,u,v,cost,duration,physical,dt,H):
  self.n=int(n);self.u=np.asarray(u,dtype=np.int32);self.v=np.asarray(v,dtype=np.int32)
  self.cost=np.asarray(cost,dtype=np.float64);self.duration=np.asarray(duration,dtype=np.int32)
  self.physical=np.asarray(physical,dtype=bool);self.dt=float(dt);self.H=int(H)
  self.out=[[] for _ in range(self.n)];self.incoming=[[] for _ in range(self.n)]
  for e in range(len(self.u)):
   self.out[int(self.u[e])].append(e);self.incoming[int(self.v[e])].append(e)
  if np.any(self.cost<0) or np.any(self.duration<0):raise ValueError("negative base arc")
  self._heuristic={}
 def heuristic(self,dest):
  dest=int(dest)
  if dest in self._heuristic:return self._heuristic[dest]
  h=np.full(self.n,np.inf);h[dest]=0.;heap=[(0.,dest)]
  while heap:
   val,node=heapq.heappop(heap)
   if val>h[node]+1e-12:continue
   for e in self.incoming[node]:
    prev=int(self.u[e]);new=val+float(self.cost[e])
    if new<h[prev]-1e-12:h[prev]=new;heapq.heappush(heap,(new,prev))
  self._heuristic[dest]=h
  return h
 def price(self,origin,dest,release,toll=None,max_expansions=1000000):
  origin=int(origin);dest=int(dest);release=int(release)
  if release<0 or release>self.H:raise ValueError("release outside horizon")
  toll={} if toll is None else toll
  if any(v<0 or not math.isfinite(v) for v in toll.values()):raise ValueError("nonnegative finite toll required")
  h=self.heuristic(dest)
  if not math.isfinite(h[origin]):return {"status":"UNREACHABLE_SPATIAL"}
  start=release*self.n+origin
  best={start:0.};pred={}
  heap=[(float(h[origin]),0.,release,origin)]
  expansions=0;started=time.monotonic()
  while heap:
   f,g,t,node=heapq.heappop(heap)
   state=t*self.n+node
   if g>best.get(state,math.inf)+1e-12:continue
   expansions+=1
   if expansions>max_expansions:
    return {"status":"EXPANSION_BUDGET_OPEN","expansions":expansions,
            "states":len(best),"wall_seconds":time.monotonic()-started}
   if node==dest:
    path=[];s=state
    while s!=start:
     previous,edge=pred[s]
     path.append((int(edge),int(previous//self.n)))
     s=previous
    path.reverse()
    return {"status":"EXACT_ONE_COMMODITY_FULL_TIME_SHORTEST",
            "adjusted_cost":float(g),"unconstrained_static_lower":float(h[origin]),
            "release_step":release,"arrival_step":t,
            "expansions":expansions,"states":len(best),"path":path,
            "wall_seconds":time.monotonic()-started}
   if t<self.H:
    s=(t+1)*self.n+node
    new=g+self.dt/60
    if new<best.get(s,math.inf)-1e-12:
     best[s]=new;pred[s]=(state,-2)
     heapq.heappush(heap,(new+float(h[node]),new,t+1,node))
   for e in self.out[node]:
    new_t=t+int(self.duration[e])
    if new_t>self.H:continue
    nxt=int(self.v[e]);price=float(self.cost[e])
    if self.physical[e]:price+=float(toll.get((e,t),0.))
    new=g+price;s=new_t*self.n+nxt
    if new<best.get(s,math.inf)-1e-12:
     best[s]=new;pred[s]=(state,e)
     heapq.heappush(heap,(new+float(h[nxt]),new,new_t,nxt))
  return {"status":"UNREACHABLE_WITHIN_HORIZON","expansions":expansions,
          "states":len(best),"wall_seconds":time.monotonic()-started}
def toy():
 n=3;u=[0,1,0];v=[1,2,2];cost=[1.,1.,4.];duration=[1,1,2]
 g=SparseTimeAStar(n,u,v,cost,duration,[True]*3,60,4)
 toll={(0,1):10.,(1,1):10.}
 found=g.price(0,2,0,toll)
 if found["status"]!="EXACT_ONE_COMMODITY_FULL_TIME_SHORTEST" or abs(found["adjusted_cost"]-3.)>1e-9:
  raise ValueError("toy full time shortest failed")
 if (-2,1) not in found["path"]:raise ValueError("intermediate waiting path missed")
 return found
def real(case):
 cfgp=R/"cases"/f"{case}__sparse_common_dev9_delayed_zero_gc.json"
 cfg=json.loads(cfgp.read_text(encoding="utf-8-sig"));source=Path(cfg["source_dir"])
 hashes={n:sha(source/n) for n in ("network.csv","access.csv","assignment_od_pce.csv")}
 if hashes!=cfg["expected_source_hashes"]:raise ValueError("original Q source drift")
 net=read(source/"network.csv");acc=read(source/"access.csv");od=read(source/"assignment_od_pce.csv")
 nodes=sorted({r["from_node_id"] for r in net}|{r["to_node_id"] for r in net});ix={x:i for i,x in enumerate(nodes)}
 access={r["zone_id"]:ix[r["node_id"]] for r in acc}
 u=np.array([ix[r["from_node_id"]] for r in net],dtype=np.int32)
 v=np.array([ix[r["to_node_id"]] for r in net],dtype=np.int32)
 cost=np.array([float(r["vdf_fftt"]) for r in net])
 physical=np.array([r[cfg["physical_field"]]==cfg["physical_value"] for r in net])
 dt=float(cfg["dt_seconds"]);H=int(cfg["horizon_steps"]);T=int(cfg["release_steps"])
 duration=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 model=SparseTimeAStar(len(nodes),u,v,cost,duration,physical,dt,H)
 # Choose an original positive OD whose frozen AON path uses a priced capacity edge.
 data=np.load(R/f"STATIONARY_Q_ZERO_COST_DUAL_{case}.npz",allow_pickle=False)
 charged={int(np.flatnonzero(physical)[r]) for r in data["physical_row"]}
 aon=np.load(R/"runs"/"sparse_common_dev9_delayed_zero_gc"/case/"solver"/"UNIFORM_AON_FULL_ORIGINAL_PATHS.npz",allow_pickle=False)
 offsets=aon["od_edge_offset"];flat=aon["edge_index"]
 ids=[i for i in range(len(od)) if any(int(e) in charged for e in flat[int(offsets[i]):int(offsets[i+1])])]
 if not ids:raise ValueError("no OD uses diagnosed capacity edge")
 i=ids[0];origin=access[od[i]["o_zone_id"]];dest=access[od[i]["d_zone_id"]]
 releases=(0,T//2,T-1)
 outputs=[]
 for release in releases:
  out=model.price(origin,dest,release,{},max_expansions=200000)
  out["path_edge_count"]=sum(e>=0 for e,t in out.get("path",[]))
  out["wait_count"]=sum(e==-2 for e,t in out.get("path",[]))
  out.pop("path",None)
  outputs.append(out)
 report={"schema":"SHARED_CG_Q_SPARSE_TIME_ASTAR_PROBE_R1","case_id":case,
  "source_hashes":hashes,"original_positive_OD":len(od),"original_release_events":len(od)*T,
  "selected_original_OD_index":i,"selected_OD_original_hourly_pce":float(od[i]["volume_pce"])*float(cfg["demand_factor"]),
  "selection_rule":"first original positive OD using a diagnosed capacity edge; not chosen by solver success",
  "toy_intermediate_wait":toy(),"real_no_toll_queries":outputs,
  "scientific_limit":"Exact full-time pricing for three sampled original release commodities only. No full-demand RMP or full-Q optimality claim."}
 out=R/f"Q_SPARSE_TIME_ASTAR_PROBE_{case}.json"
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:report[k] for k in ("case_id","selected_original_OD_index","real_no_toll_queries")},ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--case",default="urbana_F_Q")
 a=p.parse_args();real(a.case)
