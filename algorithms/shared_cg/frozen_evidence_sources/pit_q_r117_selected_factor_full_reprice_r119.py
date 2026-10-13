"""Full original-graph 29-destination exact reprice of independently selected R117 factor."""
from pathlib import Path
import csv,hashlib,json,time
import numpy as np
from q_profile_dp_probe_v2 import setup,static_h
from q_original_dual_price_profile_common_r89 import price_profile
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def rows(p):
 with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def save(p,x):
 p=Path(p);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(json.dumps(x,indent=2)+"\n",encoding="utf-8");tmp.replace(p)
def main():
 started=time.monotonic();dp=R/"PIT_Q_R117_SELECTED_FACTOR_FULL_REPRICE_PRE_RUN_R119.json";d=rd(dp)
 r103p=R/"runs/pit_q_r101_selected_cycle_expanded_full_reprice_r103/RESULT.json";r103=rd(r103p)
 c104p=R/"runs/pit_q_r101_selected_cycle_expanded_full_reprice_r103/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R104.json";c104=rd(c104p)
 r117p=R/"runs/pit_q_r103_eight_price_bridge_factor_grid_r117/RESULT.json";r117=rd(r117p)
 c118p=R/"runs/pit_q_r103_eight_price_bridge_factor_grid_r117/INDEPENDENT_COMPLETE_GRID_CERT_R118.json";c118=rd(c118p)
 cp=R/"cases/pittsburgh_S2_Q__sparse_common_dev9_delayed_zero_gc.json";cfg=rd(cp);source=Path(cfg["source_dir"])
 aonp=R/"runs/sparse_common_dev9_delayed_zero_gc/pittsburgh_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz"
 for key,p in [("R103_result_sha256",r103p),("R104_independent_certificate_sha256",c104p),("R117_result_sha256",r117p),("R118_independent_complete_grid_certificate_sha256",c118p),("generic_price_core_sha256",R/"q_original_dual_price_profile_common_r89.py"),("source_config_sha256",cp),("original_AON_array_sha256",aonp)]:
  if sha(p)!=d[key]:raise ValueError(key+" drift")
 if c118["status"]!="PASS_COMPLETE_GRID_CONSERVATIVE_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY" or r117["selected_bridge_factor"]!=d["selected_bridge_factor"] or c118["selected_bridge_factor"]!=d["selected_bridge_factor"]:raise ValueError("independent improvement gate")
 hashes={n:sha(source/n) for n in ("network.csv","access.csv","assignment_od_pce.csv")}
 if hashes!=d["original_source_hashes"] or hashes!=cfg["expected_source_hashes"]:raise ValueError("original source")
 net=rows(source/"network.csv");T=int(cfg["release_steps"]);H=int(cfg["horizon_steps"]);dt=float(cfg["dt_seconds"]);bridge=int(d["bridge_original_edge"]);first=int(d["bridge_first_step"]);end=int(d["price_end_exclusive"])
 cfg2,net2,od,nodes,access,u,v,cost,dur,phys,off,order,inc,pid,starts,ends,weights,inverse=setup("pittsburgh_S2_Q",[(bridge,first,end,1.)],1.)
 if cfg2!=cfg or len(od)!=d["original_positive_OD"] or len(od)*T!=d["original_release_events"]:raise ValueError("full original OD/time")
 basearr=Path(r103["array_path"])
 if sha(basearr)!=d["R103_array_sha256"] or sha(basearr)!=c104["producer_array_sha256"]:raise ValueError("accepted base array")
 with np.load(basearr,allow_pickle=False) as z:ids=z["original_OD_index"];release=z["original_release_step"];basevalues=z["adjusted_shortest_cost"];baselam=z["bridge_price_per_step"]
 with np.load(aonp,allow_pickle=False) as z:ao=z["od_edge_offset"];ae=z["edge_index"];at=z["entry_offset_steps"];q=z["od_hourly_pce"];static=z["od_static_shortest_cost"]
 prices={int(k):float(v) for k,v in d["fixed_original_physical_edge_price_map_minutes"].items()}
 if r103["flat_original_physical_edge_prices_minutes"]!=d["fixed_original_physical_edge_price_map_minutes"] or len(ids)!=d["exact_affected_original_release_events"] or len(baselam)!=end-first:raise ValueError("accepted base vector/events")
 flag=np.zeros((len(od),T),np.bool_);target=set(prices)|{bridge}
 for i in range(len(od)):
  for j in range(int(ao[i]),int(ao[i+1])):
   e=int(ae[j])
   if e not in target:continue
   offset=int(at[j]);lo=max(0,(first if e==bridge else 0)-offset);hi=min(T,end-offset)
   if lo<hi:flag[i,lo:hi]=True
 checkids,checkrelease=np.nonzero(flag)
 if not np.array_equal(ids,checkids) or not np.array_equal(release,checkrelease):raise ValueError("all affected original AON releases")
 origin=np.array([access[x["o_zone_id"]] for x in od],np.int32);dest=np.array([access[x["d_zone_id"]] for x in od],np.int32);qsource=np.array([float(x["volume_pce"])*float(cfg["demand_factor"]) for x in od])
 if np.max(abs(q-qsource))>1e-9 or len(np.unique(dest[ids]))!=d["exact_affected_destinations"]:raise ValueError("original OD mass/destinations")
 lam=np.array([float(d["selected_bridge_factor"])*dt/60*(end-t) for t in range(first,end)],np.float64)
 if np.min(lam-baselam)<-1e-12:raise ValueError("nonmonotone factor")
 flat=np.zeros(len(cost),np.float64)
 for e,price in prices.items():
  if net[e][cfg["physical_field"]]!=cfg["physical_value"] or float(net[e]["capacity"])<=0:raise ValueError("original physical price row")
  flat[inverse[e]]=price
 out=R/"runs/pit_q_r117_selected_factor_full_reprice_r119"
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 out.mkdir(parents=True);values=basevalues.copy();terminal={}
 for z in np.unique(dest[ids]):
  z=int(z);h,bound=static_h(len(nodes),inc,z);pos=np.flatnonzero(dest[ids]==z);pos=pos[np.argsort(-release[pos],kind="stable")]
  if end+int(np.max(dur))+bound>H or np.max(abs(h[origin[np.unique(ids[pos])]]-static[np.unique(ids[pos])]))>1e-7:raise ValueError("original static/terminal")
  values[pos]=price_profile(len(nodes),H,end,dt,off,order,v,cost,dur,int(inverse[bridge]),first,lam,flat,z,h,release[pos],origin[ids[pos]])
  terminal[str(z)]=bound;print(json.dumps({"destination":z,"events":len(pos),"completed_destinations":len(terminal),"total_destinations":d["exact_affected_destinations"],"elapsed_seconds":time.monotonic()-started}),flush=True)
 bridgecap=float(net[bridge]["capacity"])*dt/3600.;delta=float(np.dot(q[ids]/T,values-basevalues));increment=bridgecap*float(np.sum(lam-baselam));lower=float(c104["independent_exact_full_original_graph_lower"])+delta-increment
 if lower+1e-6<c118["independent_conservative_full_original_graph_lower"] or lower>c104["original_feasible_upper"]+1e-6:raise ValueError("conservative gate/weak duality")
 arr=out/"BEST_PRICE_PROFILE.npz";np.savez_compressed(arr,original_OD_index=ids,original_release_step=release,adjusted_shortest_cost=values,bridge_price_per_step=lam,flat_original_physical_edges=np.array(list(prices),np.int32),flat_toll_minutes_per_edge=np.array(list(prices.values())))
 rec={"schema":"PIT_Q_R117_SELECTED_FACTOR_FULL_REPRICE_RESULT_R119","status":"PRODUCER_EXACT_FULL_ORIGINAL_DUAL_PENDING_INDEPENDENT","case_id":"pittsburgh_S2_Q","design_sha256":sha(dp),"original_source_hashes":hashes,"R118_independent_certificate_sha256":sha(c118p),"original_positive_OD":len(od),"original_release_events":len(od)*T,"affected_original_release_events":len(ids),"unaffected_original_release_events_static_proven":len(od)*T-len(ids),"affected_original_positive_OD":len(np.unique(ids)),"priced_destinations":len(terminal),"terminal_bounds":terminal,"selected_bridge_factor":d["selected_bridge_factor"],"flat_original_physical_edge_prices_minutes":d["fixed_original_physical_edge_price_map_minutes"],"R104_independent_exact_lower":c104["independent_exact_full_original_graph_lower"],"all_affected_event_cost_increment":delta,"incremental_bridge_capacity_price_constant":increment,"producer_exact_full_original_graph_lower":lower,"R118_conservative_lower":c118["independent_conservative_full_original_graph_lower"],"original_feasible_upper":c104["original_feasible_upper"],"relative_open_gap":(c104["original_feasible_upper"]-lower)/c104["original_feasible_upper"],"array_path":str(arr),"array_sha256":sha(arr),"wall_seconds":time.monotonic()-started,"scientific_limit":"Exact full-original-graph dual price point; independently feasible primal separate, global optimum open."}
 save(out/"RESULT.json",rec);print(json.dumps({"status":rec["status"],"lower":lower,"gap":rec["relative_open_gap"],"events":len(ids),"destinations":len(terminal),"seconds":rec["wall_seconds"]}),flush=True)
if __name__=="__main__":main()
