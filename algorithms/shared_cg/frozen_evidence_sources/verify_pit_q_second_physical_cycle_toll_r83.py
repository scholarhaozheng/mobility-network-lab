"""Separate original-CSV full-DAG dual audit for R35 frozen bridge grid with R27 fixed cycle toll."""
from pathlib import Path
from collections import deque
import csv,hashlib,heapq,json,time
import numpy as np
from numba import njit
R=Path(__file__).resolve().parent
@njit(cache=False)
def independent_profile(n,H,end,dt,pu,pv,pc,pdur,bridge,first,bridge_price,loopmask,loopfirst,flat,newmask,newflat,zo,zh,zc,reverse,dest,h,release,origin):
 D=int(np.max(pdur));ring=np.empty((D+1,n),np.float64);answer=np.empty(len(release),np.float64);cursor=0
 for k in range(D+1):
  for node in range(n):ring[k,node]=h[node]
 for t in range(end-1,-1,-1):
  slot=t%(D+1);future=(t+1)%(D+1)
  for node in range(n):ring[slot,node]=0. if node==dest else ring[future,node]+dt/60.
  for e in range(len(pu)):
   d=pdur[e]
   if t+d>H:continue
   cand=pc[e]+ring[(t+d)%(D+1),pv[e]]
   if e==bridge and t>=first:cand+=bridge_price[t-first]
   if loopmask[e] and t>=loopfirst:cand+=flat
   if newmask[e]:cand+=newflat
   if cand<ring[slot,pu[e]]:ring[slot,pu[e]]=cand
  for k in range(n):
   node=reverse[k]
   for e in range(zo[node],zo[node+1]):
    cand=zc[e]+ring[slot,zh[e]]
    if cand<ring[slot,node]:ring[slot,node]=cand
  while cursor<len(release) and release[cursor]==t:
   answer[cursor]=ring[slot,origin[cursor]];cursor+=1
 if cursor!=len(release):raise ValueError('missing original release')
 return answer

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def csvrows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def reverse_static(n,inc,dest):
 h=np.full(n,np.inf);length=np.full(n,10**9,np.int32);h[dest]=0.;length[dest]=0;heap=[(0.,0,dest)]
 while heap:
  val,t,node=heapq.heappop(heap)
  if val>h[node]+1e-10 or (abs(val-h[node])<=1e-10 and t>length[node]):continue
  for prev,c,d in inc[node]:
   v=val+c;steps=t+d
   if v<h[prev]-1e-10 or (abs(v-h[prev])<=1e-10 and steps<length[prev]):h[prev]=v;length[prev]=steps;heapq.heappush(heap,(v,steps,prev))
 return h,int(np.max(length[np.isfinite(h)]))
def main():
 started=time.monotonic();dp=R/'PIT_Q_SECOND_PHYSICAL_CYCLE_TOLL_GRID_PRE_RUN_R82.json';design=rd(dp)
 rp=R/'runs/pit_q_second_physical_cycle_toll_r82/RESULT.json';result=rd(rp);arr=R/'runs/pit_q_second_physical_cycle_toll_r82/BEST_PRICE_PROFILE.npz'
 r31p=R/'PIT_Q_LOCAL_BRIDGE_PRICE_RESULT_R31.json';r31=rd(r31p)
 r74p=R/'runs/pit_q_late_cycle_fixed_bridge_factor_r74/RESULT.json';c75p=R/'runs/pit_q_late_cycle_fixed_bridge_factor_r74/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R75.json';c68p=R/'runs/pit_q_bridge_plus_observed_cycle_toll_r65/INDEPENDENT_COMPLETED_POINT_DUAL_CERT_R68.json';c77p=R/'runs/pit_q_wide_cycle_bridge_factor_r76/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R77.json';tr81p=R/'PIT_Q_R76_ALL_BRIDGE_OD_SAMPLE_TRACE_R81.json';r60p=R/'runs/q_common_fixed_service_greedy_r57/pittsburgh_S2_Q/CAPACITY_DIAGNOSTIC_R60.json'
 if sha(rp)!=design.get('producer_result_sha256_for_verify',sha(rp)) or sha(arr)!=result['array_sha256'] or result['design_sha256']!=sha(dp):raise ValueError('producer identity')
 if sha(r31p)!=design['R31_result_sha256'] or sha(r74p)!=design['R74_result_sha256'] or sha(c75p)!=design['R75_independent_certificate_sha256'] or sha(c68p)!=design['R68_independent_wide_control_certificate_sha256'] or sha(c77p)!=design['R77_independent_certificate_sha256'] or sha(tr81p)!=design['R81_original_policy_trace_sha256'] or sha(r60p)!=design['R60_original_capacity_diagnostic_sha256']:raise ValueError('frozen predecessor drift')
 if design['flat_loop_toll_grid_minutes']!=[.0005] or design['new_cycle_flat_toll_grid_minutes']!=[.0005,.001,.002] or [x['new_cycle_flat_toll_minutes'] for x in result['history']]!=design['new_cycle_flat_toll_grid_minutes'] or result['best_new_cycle_flat_toll_minutes'] not in design['new_cycle_flat_toll_grid_minutes'] or result['producer_valid_full_original_graph_lower']!=max(x['valid_full_original_graph_lower'] for x in result['history']) or design['bridge_factor_fixed']!=.12:raise ValueError('complete frozen prospective grid')
 flat=.0005;newflat=float(result['best_new_cycle_flat_toll_minutes'])
 cp=R/'cases/pittsburgh_S2_Q__sparse_common_dev9_delayed_zero_gc.json';cfg=rd(cp);source=Path(cfg['source_dir']);hashes={x:sha(source/x) for x in ('network.csv','access.csv','assignment_od_pce.csv')}
 if hashes!=cfg['expected_source_hashes'] or hashes!=design['original_source_hashes'] or sha(cp)!=design['config_sha256']:raise ValueError('source identity drift')
 net=csvrows(source/'network.csv');acc=csvrows(source/'access.csv');od=csvrows(source/'assignment_od_pce.csv');nodes=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(nodes)};zone={x['zone_id']:ix[x['node_id']] for x in acc}
 if len(zone)!=len(acc):raise ValueError('duplicate access')
 u=np.array([ix[x['from_node_id']] for x in net],np.int32);v=np.array([ix[x['to_node_id']] for x in net],np.int32);cost=np.array([float(x['vdf_fftt']) for x in net]);phys=np.array([x[cfg['physical_field']]==cfg['physical_value'] for x in net]);dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dur=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 if len(od)!=1406 or len(od)*T!=cfg['expected_commodity_events']:raise ValueError('original OD release count')
 pe=np.flatnonzero(phys);ze=np.flatnonzero(~phys);zu=u[ze];zv=v[ze];zc=cost[ze];sort=np.argsort(zu,kind='stable');zu=zu[sort];zv=zv[sort];zc=zc[sort];zo=np.r_[0,np.cumsum(np.bincount(zu,minlength=len(nodes)))].astype(np.int32);indeg=np.bincount(zv,minlength=len(nodes)).astype(np.int32);queue=deque(np.flatnonzero(indeg==0).tolist());topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for e in range(zo[node],zo[node+1]):
   nxt=int(zv[e]);indeg[nxt]-=1
   if indeg[nxt]==0:queue.append(nxt)
 if len(topo)!=len(nodes):raise ValueError('original zero-time cycle')
 reverse=np.asarray(topo[::-1],np.int32);incoming=[[] for _ in nodes]
 for e in range(len(net)):incoming[v[e]].append((int(u[e]),float(cost[e]),int(dur[e])))
 bridge=int(design['original_bridge_edge_index']);loops=list(map(int,design['cycle_original_physical_edges']));newloops=list(map(int,design['new_cycle_original_physical_edges']));first=int(design['bridge_price_first_step']);end=int(design['bridge_price_end_exclusive_step']);loopfirst=int(0)
 if bridge!=6410 or loops!=[5564,5572] or newloops!=[16682,16684] or first!=185 or end!=26799 or loopfirst!=0 or design['bridge_factor_fixed']!=0.12:raise ValueError('frozen original physical price support')
 bridge_price=np.array([design['bridge_factor_fixed']*dt/60.*(end-t) for t in range(first,end)])
 aonp=R/'runs/sparse_common_dev9_delayed_zero_gc/pittsburgh_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 if sha(aonp)!=r31['original_AON_sha256']:raise ValueError('AON drift')
 with np.load(aonp,allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 origins=np.array([zone[x['o_zone_id']] for x in od],np.int32);dests=np.array([zone[x['d_zone_id']] for x in od],np.int32);trees={};bounds={};flag=np.zeros((len(od),T),np.bool_);target=set(loops)|set(newloops)|{bridge};baseline=0.;maxarrival=0
 for i,row in enumerate(od):
  mass=float(row['volume_pce'])*float(cfg['demand_factor'])
  if abs(mass-q[i])>1e-9:raise ValueError('original demand changed')
  dest=int(dests[i]);origin=int(origins[i])
  if dest not in trees:trees[dest],bounds[dest]=reverse_static(len(nodes),incoming,dest)
  h=trees[dest];node=origin;t=0;value=0.
  for j in range(int(off[i]),int(off[i+1])):
   e=int(ae[j]);offset=int(at[j])
   if u[e]!=node or offset!=t:raise ValueError('original AON topology/time mapping')
   if e in target:
    lo=max(0,(first if e==bridge else 0)-offset);hi=min(T,end-offset)
    if lo<hi:flag[i,lo:hi]=True
   value+=cost[e];t+=int(dur[e]);node=int(v[e])
  if node!=dest or t+T-1>H or abs(value-static[i])>1e-7 or abs(value-h[origin])>1e-7:raise ValueError('original all-OD AON shortest/horizon')
  baseline+=mass*h[origin];maxarrival=max(maxarrival,t+T-1)
 ids,release=np.nonzero(flag);ids=ids.astype(np.int32);release=release.astype(np.int32)
 if len(ids)!=result['affected_original_release_events']:raise ValueError('affected original event set differs')
 values=np.empty(len(ids),np.float64);physical_loopmask=np.isin(pe,loops);physical_newmask=np.isin(pe,newloops);bp=np.flatnonzero(pe==bridge)
 if len(bp)!=1:raise ValueError('original physical bridge map')
 for dest in np.unique(dests[ids]):
  dest=int(dest);h=trees[dest]
  if end+int(np.max(dur))+bounds[dest]>H:raise ValueError('terminal exact boundary')
  positions=np.flatnonzero(dests[ids]==dest);positions=positions[np.argsort(-release[positions],kind='stable')]
  values[positions]=independent_profile(len(nodes),H,end,dt,u[pe],v[pe],cost[pe],dur[pe],int(bp[0]),first,bridge_price,physical_loopmask,loopfirst,flat,physical_newmask,newflat,zo,zv,zc,reverse,dest,h,release[positions],origins[ids[positions]])
 bridge_cap=float(net[bridge]['capacity'])*dt/3600.;loopcap=sum(float(net[e]['capacity'])*dt/3600. for e in loops);newcap=sum(float(net[e]['capacity'])*dt/3600. for e in newloops);penalty=bridge_cap*float(np.sum(bridge_price))+loopcap*(end-loopfirst)*flat+newcap*end*newflat
 lower=baseline+float(np.dot(q[ids]/T,values-static[ids]))-penalty
 if abs(lower-result['producer_valid_full_original_graph_lower'])>1e-6 or abs(penalty-result['capacity_price_constant'])>1e-6:raise ValueError('independent dual accounting differs')
 with np.load(arr,allow_pickle=False) as z:
  if not np.array_equal(z['original_OD_index'],ids) or not np.array_equal(z['original_release_step'],release) or abs(float(z['loop_flat_toll_minutes'][0])-flat)>1e-12 or abs(float(z['new_cycle_flat_toll_minutes'][0])-newflat)>1e-12:raise ValueError('producer event identity')
  maxerr=float(np.max(np.abs(z['adjusted_shortest_cost']-values)))
  if maxerr>1e-7 or np.max(np.abs(z['bridge_price_per_step']-bridge_price))>1e-12:raise ValueError('independent shortest path mismatch')
 cert={'schema':'PIT_Q_SECOND_PHYSICAL_CYCLE_TOLL_INDEPENDENT_CERT_R83','status':'PASS_VALID_FULL_ORIGINAL_GRAPH_DUAL_LOWER_OPEN_OPTIMALITY','original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_events':len(od)*T,'original_horizon_steps':H,'original_physical_arc_count':len(pe),'all_original_physical_time_rows':len(pe)*H,'priced_original_capacity_rows':(end-first)+len(loops)*(end-loopfirst)+len(newloops)*end,'affected_release_events_independently_priced':len(ids),'unaffected_original_release_events_proven':len(od)*T-len(ids),'profile_destinations':len(np.unique(dests[ids])),'max_original_AON_arrival_step':maxarrival,'independent_baseline_lower':baseline,'independent_capacity_price_constant':penalty,'independent_full_original_graph_lower':lower,'original_feasible_upper':50976.33449678995,'relative_open_gap':(50976.33449678995-lower)/50976.33449678995,'max_producer_event_price_error':maxerr,'producer_result_sha256':sha(rp),'producer_array_sha256':sha(arr),'frozen_design_sha256':sha(dp),'R77_independent_control_sha256':sha(c77p),'R81_original_policy_trace_sha256':sha(tr81p),'selected_new_cycle_flat_toll_minutes':newflat,'method':'Original CSV and all-OD AON audit; independent physical-time and zero-turn Bellman; all affected releases repriced; unaffected releases proven static','wall_seconds':time.monotonic()-started,'scientific_limit':'One prospective original full graph dual point; primal upper and dual lower remain separate; global optimum open.'}
 out=R/'runs/pit_q_second_physical_cycle_toll_r82/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R83.json';out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:cert[k] for k in ('status','independent_full_original_graph_lower','relative_open_gap','max_producer_event_price_error','wall_seconds')}),flush=True)
if __name__=='__main__':main()
