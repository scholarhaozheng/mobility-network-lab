"""Common original-time FIFO path construction on exact source AON routes.

Every OD and original release is retained. Only physical time-entry capacity
rows determine waits; this produces a feasible upper if the independent replay
passes, not an unrestricted route optimum.
"""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,heapq,json,math,time
import numpy as np
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def rows(p):
 with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def save(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8");tmp.replace(p)
def stage_order(stage_set,routes):
 succ={e:set() for e in stage_set};indeg={e:0 for e in stage_set}
 for path in routes:
  seq=[e for e in path if e in stage_set]
  if len(seq)!=len(set(seq)):raise ValueError("repeated stage edge on source route")
  for a,b in zip(seq,seq[1:]):
   if b not in succ[a]:succ[a].add(b);indeg[b]+=1
 heap=[e for e in stage_set if indeg[e]==0];heapq.heapify(heap);order=[]
 while heap:
  e=heapq.heappop(heap);order.append(e)
  for f in sorted(succ[e]):
   indeg[f]-=1
   if indeg[f]==0:heapq.heappush(heap,f)
 if len(order)!=len(stage_set):raise ValueError("source route stage precedence cycle")
 return order
def source_overload(routes,entries,q,physical,cap_hour,T):
 events=defaultdict(list)
 for i,path in enumerate(routes):
  for e,t in zip(path,entries[i]):
   if physical[e]:events[e].append((t,q[i]));events[e].append((t+T,-q[i]))
 result=[]
 for e,ev in events.items():
  ev.sort();load=peak=0.;j=0
  while j<len(ev):
   at=ev[j][0];delta=0.
   while j<len(ev) and ev[j][0]==at:delta+=ev[j][1];j+=1
   load+=delta;peak=max(peak,load)
  if peak>cap_hour[e]*(1+1e-9):result.append(e)
 return sorted(result)
def service_one_edge(edge,od,release,mass,waits,routes,entries,cap_step,H):
 n=len(od);uses=np.zeros(len(routes),np.bool_);offset=np.full(len(routes),-1,np.int32)
 for i,path in enumerate(routes):
  if edge in path:
   p=path.index(edge);uses[i]=True;offset[i]=int(entries[i][p])
 active=np.flatnonzero(uses[od]);inactive=np.flatnonzero(~uses[od])
 if not len(active):return od,release,mass,waits,{"edge_index":edge,"input_fragments":0,"output_fragments":0,"max_service_load":0.}
 arrival=release[active].astype(np.int64)+offset[od[active]].astype(np.int64)+np.sum(waits[active],axis=1,dtype=np.int64)
 perm=np.lexsort((active,release[active],od[active],arrival));active=active[perm];arrival=arrival[perm]
 cap=float(cap_step[edge]);eps=max(1e-14,cap*1e-12);slot=-1;remain=0.;out_idx=[];out_mass=[];out_delay=[];served=defaultdict(float)
 for index,at in zip(active,arrival):
  at=int(at);left=float(mass[index])
  if at>=H:raise ValueError("stage arrival beyond horizon")
  while left>eps:
   if slot<at:slot=at;remain=cap
   if remain<=eps:slot+=1;remain=cap
   if slot>=H:raise ValueError("stage service beyond horizon")
   take=min(left,remain)
   if take<=eps:raise ValueError("numerical service failure")
   out_idx.append(int(index));out_mass.append(take);out_delay.append(slot-at)
   served[slot]+=take;left-=take;remain-=take
  if abs(left)>eps:raise ValueError("unserved fragment mass")
 idx=np.r_[inactive,np.asarray(out_idx,np.int64)]
 new_od=od[idx];new_release=release[idx];new_mass=np.r_[mass[inactive],np.asarray(out_mass,np.float64)]
 new_waits=np.zeros((len(idx),waits.shape[1]+1),np.int32);new_waits[:,:-1]=waits[idx];new_waits[len(inactive):,-1]=np.asarray(out_delay,np.int32)
 peak=max(served.values(),default=0.)
 if peak>cap+max(1e-9,cap*1e-8):raise ValueError("stage capacity")
 return new_od,new_release,new_mass,new_waits,{"edge_index":edge,"input_fragments":len(active),"output_fragments":len(out_idx),"max_service_load":peak,"step_capacity":cap,"last_service_step":max(served,default=-1)}
def audit(routes,entries,q,physical,cap_hour,dt,T,H,od,release,mass,waits,stage_ordered,route_duration):
 selected=set(map(int,np.unique(od)));stage_lookup={e:j for j,e in enumerate(stage_ordered)}
 if np.any(mass<0) or np.any(release<0) or np.any(release>=T):raise ValueError("negative or invalid fragment")
 by_od={i:np.flatnonzero(od==i) for i in selected}
 max_residual=0.
 for i,idx in by_od.items():
  got=np.bincount(release[idx],weights=mass[idx],minlength=T)
  max_residual=max(max_residual,float(np.max(np.abs(got-q[i]/T))))
  if np.any(release[idx]+route_duration[i]+np.sum(waits[idx],axis=1)>H):raise ValueError("terminal horizon")
 if max_residual>1e-8:raise ValueError("original per-release conservation")
 users=defaultdict(list)
 for i,path in enumerate(routes):
  before=[];seen=set()
  for e,t in zip(path,entries[i]):
   if e in stage_lookup:
    if e in seen:raise ValueError("repeated stage edge")
    before.append(stage_lookup[e]);seen.add(e)
   if physical[e]:users[e].append((i,int(t),tuple(before)))
 cap_step=cap_hour*dt/3600.;violated=[];max_excess=0.;max_ratio=0.;active_rows=0
 for e,items in users.items():
  diff=np.zeros(H+1,np.float64);dynamic=np.zeros(H,np.float64)
  for i,t,prefix in items:
   if i in selected:
    idx=by_od[i]
    delay=np.sum(waits[idx][:,prefix],axis=1,dtype=np.int64) if prefix else 0
    times=release[idx].astype(np.int64)+t+delay
    if np.any(times<0) or np.any(times>=H):raise ValueError("path entry horizon")
    dynamic+=np.bincount(times,weights=mass[idx],minlength=H)
   else:
    if t+T>H:raise ValueError("baseline interval horizon")
    diff[t]+=q[i]/T;diff[t+T]-=q[i]/T
  load=np.cumsum(diff[:-1])+dynamic;peak=float(np.max(load));ratio=peak/cap_step[e];excess=peak-cap_step[e]
  active_rows+=int(np.count_nonzero(load>1e-15));max_excess=max(max_excess,excess);max_ratio=max(max_ratio,ratio)
  if excess>max(1e-9,cap_step[e]*1e-7):violated.append((excess,e,int(np.argmax(load))))
 violated.sort(key=lambda x:(-x[0],x[1]))
 delay_cost=float(np.dot(mass,np.sum(waits,axis=1,dtype=np.int64)))*dt/60.
 return {"max_original_capacity_excess_pce":max(0.,max_excess),"max_original_capacity_ratio":max_ratio,"violated_physical_edges":len(violated),"violations":[{"edge_index":e,"peak_excess_pce":float(x),"peak_step":t} for x,e,t in violated],"max_original_release_mass_residual_pce":max_residual,"used_positive_original_capacity_rows":active_rows,"selected_OD":len(selected),"selected_fragment_paths":len(mass),"delay_cost_pce_minutes":delay_cost}
def main(config_path,aon_path,out_dir):
 start=time.monotonic();cp=Path(config_path);cfg=rd(cp);source=Path(cfg["source_dir"]);ap=Path(aon_path);out=Path(out_dir)
 case_id=cfg["case_id"]
 if {n:sha(source/n) for n in cfg["expected_source_hashes"]}!=cfg["expected_source_hashes"]:
  raise ValueError("original CSV source drift")
 if not ap.exists():raise FileNotFoundError(ap)
 net=rows(source/"network.csv");od_rows=rows(source/"assignment_od_pce.csv");T=int(cfg["release_steps"]);H=int(cfg["horizon_steps"]);dt=float(cfg["dt_seconds"])
 physical=np.asarray([a[cfg["physical_field"]]==cfg["physical_value"] for a in net],np.bool_);cap_hour=np.asarray([float(a["capacity"]) for a in net]);free=np.asarray([float(a["vdf_fftt"]) for a in net])
 duration=np.where(physical,np.maximum(1,np.ceil(free*60/dt-1e-12).astype(np.int32)),0)
 with np.load(ap,allow_pickle=False) as z:
  off=z["od_edge_offset"];flat=z["edge_index"];flat_entry=z["entry_offset_steps"];q=z["od_hourly_pce"];static=z["od_static_shortest_cost"]
 assert len(q)==len(od_rows) and len(q)*T==cfg["expected_commodity_events"]
 routes=[list(map(int,flat[int(off[i]):int(off[i+1])])) for i in range(len(q))]
 entries=[list(map(int,flat_entry[int(off[i]):int(off[i+1])])) for i in range(len(q))]
 for i,row in enumerate(od_rows):
  if abs(float(row["volume_pce"])*float(cfg["demand_factor"])-q[i])>1e-9:raise ValueError("original demand changed")
 route_duration=np.asarray([sum(int(duration[e]) for e in route) for route in routes],np.int32)
 initial=source_overload(routes,entries,q,physical,cap_hour,T)
 stage_set=set(initial)
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 out.mkdir(parents=True);progress=[]
 save(out/"INPUT_IDENTITY.json",{"schema":"Q_LOCAL_FIFO_R43_INPUT_IDENTITY","case_id":case_id,"seed_algorithm":"SOURCE_DRIVEN_ORIGINAL_FIFO_R43_GENERIC","config_sha256":sha(cp),"AON_sha256":sha(ap),"source_hashes":cfg["expected_source_hashes"],"original_positive_OD":len(q),"original_release_events":len(q)*T,"initial_AON_overloaded_physical_edges":initial,"full_original_horizon_steps":H,"dt_seconds":dt})
 for iteration in range(1,21):
  ordered=stage_order(stage_set,routes);selected=np.asarray(sorted({i for e in ordered for i,path in enumerate(routes) if e in path}),np.int32)
  frag_od=np.repeat(selected,T);frag_release=np.tile(np.arange(T,dtype=np.int32),len(selected));frag_mass=q[frag_od]/T;waits=np.zeros((len(frag_od),len(ordered)),np.int32);stage_records=[]
  for j,e in enumerate(ordered):
   frag_od,frag_release,frag_mass,subset_waits,record=service_one_edge(e,frag_od,frag_release,frag_mass,waits[:,:j],routes,entries,cap_hour*dt/3600.,H)
   waits=np.zeros((len(frag_od),len(ordered)),np.int32);waits[:,:j+1]=subset_waits
   stage_records.append(record)
   if len(frag_mass)>5_000_000:raise MemoryError("predeclared fragment resource gate")
  check=audit(routes,entries,q,physical,cap_hour,dt,T,H,frag_od,frag_release,frag_mass,waits,ordered,route_duration)
  candidate=float(np.dot(q,static))+check["delay_cost_pce_minutes"]
  row={"round":iteration,"stage_edges":ordered,"selected_OD":len(selected),"fragments":len(frag_mass),"candidate_objective":candidate,"audit":{k:v for k,v in check.items() if k!="violations"},"new_violated_edges":[x["edge_index"] for x in check["violations"] if x["edge_index"] not in stage_set],"wall_seconds":time.monotonic()-start}
  progress.append(row);save(out/"PROGRESS.json",progress);print(json.dumps(row),flush=True)
  if not check["violations"]:
   npz=out/"FRAGMENTS.npz";np.savez_compressed(npz,od_index=frag_od,release_step=frag_release,mass_pce=frag_mass,wait_steps=waits,stage_original_edge_index=np.asarray(ordered,np.int32),selected_od_index=selected)
   result={"schema":"Q_LOCAL_FIFO_FULL_ORIGINAL_TIME_RESULT_R43","case_id":case_id,"status":"CANDIDATE_FEASIBLE_PENDING_INDEPENDENT_ORIGINAL_REPLAY","seed_algorithm":"SOURCE_DRIVEN_ORIGINAL_FIFO_R43_GENERIC","config_sha256":sha(cp),"AON_sha256":sha(ap),"source_hashes":cfg["expected_source_hashes"],"positive_OD":len(q),"original_release_events":len(q)*T,"original_unconstrained_AON_cost":float(np.dot(q,static)),"candidate_primal_cost":candidate,"max_original_capacity_excess":check["max_original_capacity_excess_pce"],"max_original_release_mass_residual":check["max_original_release_mass_residual_pce"],"selected_OD":len(selected),"fragment_paths":len(frag_mass),"stage_count":len(ordered),"stage_records":stage_records,"rounds":iteration,"fragment_path":str(npz),"fragment_sha256":sha(npz),"wall_seconds":time.monotonic()-start,"scientific_limit":"Original route FIFO candidate only; independent original replay and unrestricted route pricing required."}
   save(out/"RESULT.json",result);print(json.dumps({"case_id":case_id,"status":result["status"],"objective":candidate,"wall_seconds":result["wall_seconds"]}),flush=True);return
  new=set(x["edge_index"] for x in check["violations"])-stage_set
  if not new:
   save(out/"RESULT.json",{"status":"STALLED_WITH_ORIGINAL_CAPACITY_VIOLATION","case_id":case_id,"last":row});return
  stage_set|=new
 save(out/"RESULT.json",{"status":"ROUND_LIMIT_OPEN","case_id":case_id,"last":progress[-1]})
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--config",required=True);p.add_argument("--aon",required=True);p.add_argument("--out",required=True)
 a=p.parse_args();main(a.config,a.aon,a.out)
