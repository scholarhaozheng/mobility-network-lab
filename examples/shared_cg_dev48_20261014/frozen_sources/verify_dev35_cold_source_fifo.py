"""Independent original-CSV replay of R43 FIFO fragment paths, without producer imports."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,json,math,time
import numpy as np
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def csvrows(p):
 with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def run(config_path,aon_path,out_path):
 start=time.monotonic();cfgp=Path(config_path);cfg=rd(cfgp);source=Path(cfg["source_dir"]);aonp=Path(aon_path);out=Path(out_path);case_id=cfg["case_id"]
 assert {n:sha(source/n) for n in cfg["expected_source_hashes"]}==cfg["expected_source_hashes"]
 rp=out/"RESULT.json";result=rd(rp)
 assert result["status"]=="CANDIDATE_FEASIBLE_PENDING_INDEPENDENT_ORIGINAL_REPLAY"
 assert result["seed_algorithm"]=="SOURCE_DRIVEN_ORIGINAL_FIFO_R43_GENERIC"
 assert result["config_sha256"]==sha(cfgp) and result["AON_sha256"]==sha(aonp)
 fragp=Path(result["fragment_path"]);assert sha(fragp)==result["fragment_sha256"]
 net=csvrows(source/"network.csv");odrows=csvrows(source/"assignment_od_pce.csv");acc=csvrows(source/"access.csv")
 zones={x["zone_id"]:x["node_id"] for x in acc};assert len(zones)==len(acc)
 H=int(cfg["horizon_steps"]);T=int(cfg["release_steps"]);dt=float(cfg["dt_seconds"]);assert abs(T*dt-3600)<1e-8
 phys=np.asarray([x[cfg["physical_field"]]==cfg["physical_value"] for x in net],np.bool_)
 cap_hour=np.asarray([float(x["capacity"]) for x in net],np.float64);cost=np.asarray([float(x["vdf_fftt"]) for x in net],np.float64)
 assert np.all(cap_hour>0) and np.all(cost>=0)
 duration=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 with np.load(aonp,allow_pickle=False) as z:
  off=z["od_edge_offset"];edge=z["edge_index"];entry=z["entry_offset_steps"];q=z["od_hourly_pce"];static=z["od_static_shortest_cost"]
 assert len(q)==len(odrows) and len(q)*T==cfg["expected_commodity_events"]
 with np.load(fragp,allow_pickle=False) as z:
  fod=z["od_index"];release=z["release_step"];mass=z["mass_pce"];wait=z["wait_steps"];stages=z["stage_original_edge_index"];selected=z["selected_od_index"]
 assert len(fod)==len(release)==len(mass)==len(wait)==result["fragment_paths"]
 assert wait.shape==(len(mass),len(stages)) and len(selected)==result["selected_OD"]
 assert np.array_equal(selected,np.unique(fod)) and np.all(mass>=0) and np.all(wait>=0)
 assert np.all(release>=0) and np.all(release<T) and len(set(map(int,stages)))==len(stages)
 stage_index={int(e):j for j,e in enumerate(stages)}
 route_data=[];edge_users=defaultdict(list);max_path_cost_error=0.;max_mass_residual=0.;total_mass=0.
 selected_set=set(map(int,selected));stage_user=set()
 for i,row in enumerate(odrows):
  assert abs(float(row["volume_pce"])*float(cfg["demand_factor"])-float(q[i]))<1e-9
  lo=int(off[i]);hi=int(off[i+1]);node=zones[row["o_zone_id"]];dest=zones[row["d_zone_id"]];t=0;base=0.;used_stages=[];physical_count=0
  for j in range(lo,hi):
   e=int(edge[j]);s=int(entry[j]);assert 0<=e<len(net) and s==t and net[e]["from_node_id"]==node
   if e in stage_index:
    used_stages.append(stage_index[e]);stage_user.add(i)
   if phys[e]:physical_count+=1;edge_users[e].append((i,s,tuple(used_stages)))
   base+=float(cost[e]);t+=int(duration[e]);node=net[e]["to_node_id"]
  assert node==dest and T-1+t<=H and len(used_stages)==len(set(used_stages)) and used_stages==sorted(used_stages)
  max_path_cost_error=max(max_path_cost_error,abs(base-float(static[i])))
  route_data.append((t,tuple(used_stages),physical_count))
 assert selected_set==stage_user and max_path_cost_error<1e-7
 byod={i:np.flatnonzero(fod==i) for i in selected_set}
 for i in range(len(q)):
  total_mass+=float(q[i])
  if i in selected_set:
   idx=byod[i];got=np.bincount(release[idx],weights=mass[idx],minlength=T);max_mass_residual=max(max_mass_residual,float(np.max(np.abs(got-q[i]/T))))
   tt,used,_=route_data[i]
   unused=[j for j in range(len(stages)) if j not in used]
   if unused:assert not np.any(wait[idx][:,unused])
   assert np.all(release[idx]+tt+np.sum(wait[idx],axis=1,dtype=np.int64)<=H)
 assert max_mass_residual<1e-8
 cap_step=cap_hour*dt/3600.;max_excess=0.;max_ratio=0.;used_rows=0;worst_edge=None;worst_step=None;physical_actions=0
 for e,users in edge_users.items():
  baseline_change=np.zeros(H+1,np.float64);dynamic=np.zeros(H,np.float64)
  for i,offset,prefix in users:
   if i in selected_set:
    idx=byod[i];delay=np.sum(wait[idx][:,prefix],axis=1,dtype=np.int64) if prefix else 0
    when=release[idx].astype(np.int64)+offset+delay
    assert np.all(when>=0) and np.all(when<H)
    dynamic+=np.bincount(when,weights=mass[idx],minlength=H)
    physical_actions+=len(idx)
   else:
    assert 0<=offset and offset+T<=H
    baseline_change[offset]+=float(q[i])/T;baseline_change[offset+T]-=float(q[i])/T
    physical_actions+=T
  load=np.cumsum(baseline_change[:-1])+dynamic
  peak=float(np.max(load));excess=peak-float(cap_step[e]);ratio=peak/float(cap_step[e]);used_rows+=int(np.count_nonzero(load>1e-15))
  if excess>max_excess:
   max_excess=excess;worst_edge=int(e);worst_step=int(np.argmax(load))
  max_ratio=max(max_ratio,ratio)
 assert max_excess<=max(1e-8,float(np.max(cap_step))*1e-7)
 baseline=float(np.dot(q,static));wait_cost=float(np.dot(mass,np.sum(wait,axis=1,dtype=np.int64)))*dt/60.;objective=baseline+wait_cost
 assert abs(baseline-result["original_unconstrained_AON_cost"])<1e-6 and abs(objective-result["candidate_primal_cost"])<1e-6
 assert used_rows==rd(out/"PROGRESS.json")[-1]["audit"]["used_positive_original_capacity_rows"]
 cert={"schema":"Q_LOCAL_FIFO_FULL_ORIGINAL_TIME_INDEPENDENT_CERTIFICATE_R43","case_id":case_id,"status":"PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE","seed_algorithm":"SOURCE_DRIVEN_ORIGINAL_FIFO_R43_GENERIC","producer_result_sha256":sha(rp),"fragment_sha256":sha(fragp),"original_source_hashes":cfg["expected_source_hashes"],"original_positive_OD":len(q),"original_release_events":len(q)*T,"selected_OD":len(selected),"selected_fragment_paths":len(mass),"unselected_OD_implicitly_verified":len(q)-len(selected),"stage_original_physical_edges":list(map(int,stages)),"stage_count":len(stages),"max_original_AON_path_cost_error_minutes":max_path_cost_error,"max_per_release_mass_residual_PCE":max_mass_residual,"used_positive_original_capacity_rows":used_rows,"max_original_capacity_excess_PCE":max(0.,max_excess),"max_original_capacity_ratio":max_ratio,"worst_original_edge_index":worst_edge,"worst_original_entry_step":worst_step,"original_physical_arc_actions_checked":physical_actions,"baseline_shortest_cost_PCE_minutes":baseline,"queue_wait_cost_PCE_minutes":wait_cost,"independent_feasible_primal_upper":objective,"wall_seconds":time.monotonic()-start,"scientific_limit":"Feasible upper for all original release events on frozen source AON routes. No unrestricted full-graph pricing, Q optimum, or 16/16 claim."}
 target=out/"INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json"
 if target.exists():raise FileExistsError(target)
 target.write_text(json.dumps(cert,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"case_id":case_id,"status":cert["status"],"upper":objective,"wall_seconds":cert["wall_seconds"]}),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--config",required=True);p.add_argument("--aon",required=True);p.add_argument("--out",required=True)
 a=p.parse_args();run(a.config,a.aon,a.out)
