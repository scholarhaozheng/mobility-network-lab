"""Independent original CSV/full-release audit of R126 29-destination dual point."""
from pathlib import Path
from collections import deque
import json,time
import numpy as np
from verify_pit_q_second_physical_cycle_toll_r83 import reverse_static
from verify_pit_q_r88_top_unpriced_cycle_monotone_r90 import independent_profile_flat
from verify_pit_q_r117_selected_factor_full_reprice_r120 import R,sha,rd,rows

def main():
 started=time.monotonic();dp=R/'PIT_Q_R125_SELECTED_REPEATED_PAIR_FULL_REPRICE_PRE_RUN_R126.json';d=rd(dp)
 rp=R/'runs/pit_q_r125_selected_repeated_pair_full_reprice_r126/RESULT.json';rec=rd(rp);ap=Path(rec['array_path'])
 r119p=R/'runs/pit_q_r117_selected_factor_full_reprice_r119/RESULT.json';base=rd(r119p)
 c120p=R/'runs/pit_q_r117_selected_factor_full_reprice_r119/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R120.json';c120=rd(c120p)
 r124p=R/'runs/pit_q_r123_repeated_pair_monotone_r124/RESULT.json';r124=rd(r124p)
 c125p=R/'runs/pit_q_r123_repeated_pair_monotone_r124/INDEPENDENT_COMPLETE_GRID_CERT_R125.json';c125=rd(c125p)
 cp=R/'cases/pittsburgh_S2_Q__sparse_common_dev9_delayed_zero_gc.json';cfg=rd(cp);source=Path(cfg['source_dir'])
 aonp=R/'runs/sparse_common_dev9_delayed_zero_gc/pittsburgh_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 for key,p in [('R119_result_sha256',r119p),('R120_independent_certificate_sha256',c120p),('R124_result_sha256',r124p),('R125_independent_complete_grid_certificate_sha256',c125p),('generic_price_core_sha256',R/'q_original_dual_price_profile_common_r89.py'),('source_config_sha256',cp),('original_AON_array_sha256',aonp)]:
  if sha(p)!=d[key]:raise ValueError(key+' drift')
 hashes={n:sha(source/n) for n in ('network.csv','access.csv','assignment_od_pce.csv')}
 if hashes!=d['original_source_hashes'] or hashes!=cfg['expected_source_hashes'] or hashes!=c120['original_source_hashes'] or rec['design_sha256']!=sha(dp):raise ValueError('original source/frozen design')
 if c125['status']!='PASS_COMPLETE_GRID_CONSERVATIVE_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY' or c125['selected_candidate_flat_toll_minutes']!=d['selected_candidate_flat_toll_minutes'] or c125['best_independent_conservative_full_original_graph_lower']<=c120['independent_exact_full_original_graph_lower']+1e-6:raise ValueError('independent gate')
 net=rows(source/'network.csv');acc=rows(source/'access.csv');od=rows(source/'assignment_od_pce.csv');nodes=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(nodes)};zone={x['zone_id']:ix[x['node_id']] for x in acc}
 if len(zone)!=len(acc) or len(od)!=d['original_positive_OD']:raise ValueError('original access/OD')
 u=np.array([ix[x['from_node_id']] for x in net],np.int32);v=np.array([ix[x['to_node_id']] for x in net],np.int32);cost=np.array([float(x['vdf_fftt']) for x in net]);phys=np.array([x[cfg['physical_field']]==cfg['physical_value'] for x in net]);dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dur=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 if len(od)*T!=d['original_release_events'] or abs(T*dt-3600)>1e-8:raise ValueError('original release')
 pe=np.flatnonzero(phys);ze=np.flatnonzero(~phys);zu=u[ze];zv=v[ze];zc=cost[ze];sort=np.argsort(zu,kind='stable');zu=zu[sort];zv=zv[sort];zc=zc[sort];zo=np.r_[0,np.cumsum(np.bincount(zu,minlength=len(nodes)))].astype(np.int32);indeg=np.bincount(zv,minlength=len(nodes)).astype(np.int32);queue=deque(np.flatnonzero(indeg==0).tolist());topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for j in range(zo[node],zo[node+1]):
   nxt=int(zv[j]);indeg[nxt]-=1
   if indeg[nxt]==0:queue.append(nxt)
 if len(topo)!=len(nodes):raise ValueError('original zero-time cycle')
 reverse=np.asarray(topo[::-1],np.int32);incoming=[[] for _ in nodes]
 for e in range(len(net)):incoming[v[e]].append((int(u[e]),float(cost[e]),int(dur[e])))
 bridge=int(d['bridge_original_edge']);first=int(d['bridge_first_step']);end=int(d['price_end_exclusive']);oldprices={int(k):float(x) for k,x in d['base_flat_original_physical_edge_prices_minutes'].items()};prices={int(k):float(x) for k,x in d['new_flat_original_physical_edge_prices_minutes'].items()};candidate=list(map(int,d['candidate_original_physical_edges']));bp=np.flatnonzero(pe==bridge)
 if len(bp)!=1 or bridge!=6410 or first!=185 or end!=26799 or candidate!=[16684,16682] or set(prices)!=set(oldprices) or base['flat_original_physical_edge_prices_minutes']!=d['base_flat_original_physical_edge_prices_minutes'] or rec['flat_original_physical_edge_prices_minutes']!=d['new_flat_original_physical_edge_prices_minutes']:raise ValueError('original price resources')
 for e in prices:
  if prices[e]!=(d['selected_candidate_flat_toll_minutes'] if e in candidate else oldprices[e]):raise ValueError('candidate price change only')
 basearr=Path(base['array_path'])
 if sha(basearr)!=d['R119_array_sha256'] or sha(basearr)!=c120['producer_array_sha256']:raise ValueError('R119 accepted event array')
 with np.load(basearr,allow_pickle=False) as z:ids0=z['original_OD_index'];release0=z['original_release_step'];basevalues=z['adjusted_shortest_cost'];baselam=z['bridge_price_per_step']
 with np.load(aonp,allow_pickle=False) as z:ao=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 origins=np.array([zone[x['o_zone_id']] for x in od],np.int32);dests=np.array([zone[x['d_zone_id']] for x in od],np.int32);trees={};bounds={};flag=np.zeros((len(od),T),np.bool_);target=set(prices)|{bridge};baseline=0.;maxarrival=0
 for i,row in enumerate(od):
  mass=float(row['volume_pce'])*float(cfg['demand_factor'])
  if abs(mass-q[i])>1e-9:raise ValueError('original OD mass')
  z=int(dests[i]);node=int(origins[i])
  if z not in trees:trees[z],bounds[z]=reverse_static(len(nodes),incoming,z)
  h=trees[z];t=0;value=0.
  for j in range(int(ao[i]),int(ao[i+1])):
   e=int(ae[j]);offset=int(at[j])
   if u[e]!=node or offset!=t:raise ValueError('original AON topology/time')
   if e in target:
    lo=max(0,(first if e==bridge else 0)-offset);hi=min(T,end-offset)
    if lo<hi:flag[i,lo:hi]=True
   value+=cost[e];t+=int(dur[e]);node=int(v[e])
  if node!=z or t+T-1>H or abs(value-static[i])>1e-7 or abs(value-h[origins[i]])>1e-7:raise ValueError('original AON static/terminal')
  baseline+=mass*h[origins[i]];maxarrival=max(maxarrival,t+T-1)
 ids,release=np.nonzero(flag);ids=ids.astype(np.int32);release=release.astype(np.int32)
 if not np.array_equal(ids,ids0) or not np.array_equal(release,release0) or len(ids)!=d['R119_exact_affected_original_events'] or len(np.unique(dests[ids]))!=d['original_affected_destinations']:raise ValueError('all original affected events')
 if abs(baseline-c120['independent_baseline_original_lower'])>1e-6:raise ValueError('original static baseline')
 lam=np.array([float(d['bridge_factor'])*dt/60*(end-t) for t in range(first,end)],np.float64)
 if np.max(abs(lam-baselam))>1e-12:raise ValueError('same bridge price')
 flat=np.zeros(len(pe),np.float64);capacity_price_constant=float(net[bridge]['capacity'])*dt/3600.*float(np.sum(lam));increment=0.
 for e,price in prices.items():
  atp=np.flatnonzero(pe==e)
  if len(atp)!=1 or float(net[e]['capacity'])<=0:raise ValueError('original physical capacity mapping')
  flat[atp[0]]=price;capacity_price_constant+=float(net[e]['capacity'])*dt/3600.*end*price
  if e in candidate:increment+=float(net[e]['capacity'])*dt/3600.*end*(price-oldprices[e])
 if abs(capacity_price_constant-c120['independent_original_capacity_price_constant']-increment)>1e-6:raise ValueError('independent capacity price constant')
 values=np.empty(len(ids),np.float64)
 for z in np.unique(dests[ids]):
  z=int(z);h=trees[z]
  if end+int(np.max(dur))+bounds[z]>H:raise ValueError('original terminal bound')
  pos=np.flatnonzero(dests[ids]==z);pos=pos[np.argsort(-release[pos],kind='stable')]
  values[pos]=independent_profile_flat(len(nodes),H,end,dt,u[pe],v[pe],cost[pe],dur[pe],int(bp[0]),first,lam,flat,zo,zv,zc,reverse,z,h,release[pos],origins[ids[pos]])
  print(json.dumps({'independent_destination':z,'events':len(pos),'elapsed_seconds':time.monotonic()-started}),flush=True)
 lower=baseline+float(np.dot(q[ids]/T,values-static[ids]))-capacity_price_constant
 lower_from_base=float(c120['independent_exact_full_original_graph_lower'])+float(np.dot(q[ids]/T,values-basevalues))-increment
 if abs(lower-lower_from_base)>1e-6 or lower+1e-6<c125['best_independent_conservative_full_original_graph_lower'] or lower>c120['original_feasible_upper']+1e-6:raise ValueError('independent full dual/gate')
 if sha(ap)!=rec['array_sha256']:raise ValueError('producer selected array SHA')
 with np.load(ap,allow_pickle=False) as z:
  if not np.array_equal(z['original_OD_index'],ids) or not np.array_equal(z['original_release_step'],release) or not np.array_equal(z['flat_original_physical_edges'],np.array(list(prices),np.int32)) or np.max(abs(z['flat_toll_minutes_per_edge']-np.array(list(prices.values()))))>1e-12:raise ValueError('producer original events/physical map')
  err=float(np.max(abs(z['adjusted_shortest_cost']-values)));lamerr=float(np.max(abs(z['bridge_price_per_step']-lam)))
 if err>1e-7 or lamerr>1e-10 or abs(lower-rec['producer_exact_full_original_graph_lower'])>1e-6 or abs(increment-rec['incremental_candidate_capacity_price_constant'])>1e-6:raise ValueError('independent producer dual identity')
 cert={'schema':'PIT_Q_R125_SELECTED_REPEATED_PAIR_FULL_REPRICE_INDEPENDENT_CERT_R127','status':'PASS_EXACT_FULL_ORIGINAL_GRAPH_DUAL_LOWER_OPEN_OPTIMALITY','original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_events':len(od)*T,'original_horizon_steps':H,'original_physical_arc_count':len(pe),'all_original_physical_capacity_rows':len(pe)*H,'priced_original_capacity_rows':(end-first)+len(prices)*end,'affected_original_release_events_independently_repriced':len(ids),'unaffected_original_release_events_proven':len(od)*T-len(ids),'priced_destinations':len(np.unique(dests[ids])),'max_original_AON_arrival_step':maxarrival,'bridge_factor':d['bridge_factor'],'independent_baseline_original_lower':baseline,'independent_original_capacity_price_constant':capacity_price_constant,'independent_incremental_candidate_capacity_price_constant':increment,'independent_exact_full_original_graph_lower':lower,'R125_independent_conservative_lower':c125['best_independent_conservative_full_original_graph_lower'],'original_feasible_upper':c120['original_feasible_upper'],'relative_open_gap':(c120['original_feasible_upper']-lower)/c120['original_feasible_upper'],'max_producer_event_price_error':err,'max_producer_bridge_price_error':lamerr,'producer_result_sha256':sha(rp),'producer_array_sha256':sha(ap),'frozen_design_sha256':sha(dp),'R120_certificate_sha256':sha(c120p),'R125_independent_certificate_sha256':sha(c125p),'wall_seconds':time.monotonic()-started,'scientific_limit':'Exact full-original-graph dual point and separate feasible primal; global optimum/open three Q remain.'}
 out=R/'runs/pit_q_r125_selected_repeated_pair_full_reprice_r126/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R127.json';out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':cert['status'],'lower':lower,'gap':cert['relative_open_gap'],'error':err,'seconds':cert['wall_seconds']}),flush=True)
if __name__=='__main__':main()
