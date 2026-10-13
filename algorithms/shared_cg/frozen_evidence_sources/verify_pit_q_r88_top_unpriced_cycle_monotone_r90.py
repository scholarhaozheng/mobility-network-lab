"""Independent original CSV physical/zero-time Bellman and monotonicity audit for R89."""
from pathlib import Path
from collections import deque
import csv,hashlib,json,heapq,time
import numpy as np
from numba import njit
from verify_pit_q_second_physical_cycle_toll_r83 import reverse_static
R=Path(__file__).resolve().parent
@njit(cache=False)
def independent_profile_flat(n,H,end,dt,pu,pv,pc,pdur,bridge,first,bridge_price,flat_toll,zo,zh,zc,reverse,dest,h,release,origin):
 D=int(np.max(pdur));ring=np.empty((D+1,n),np.float64);out=np.empty(len(release),np.float64);cursor=0
 for j in range(D+1):
  for node in range(n):ring[j,node]=h[node]
 for t in range(end-1,-1,-1):
  slot=t%(D+1);future=(t+1)%(D+1)
  for node in range(n):ring[slot,node]=0. if node==dest else ring[future,node]+dt/60.
  for e in range(len(pu)):
   d=pdur[e]
   if t+d>H:continue
   cand=pc[e]+flat_toll[e]+ring[(t+d)%(D+1),pv[e]]
   if e==bridge and t>=first:cand+=bridge_price[t-first]
   if cand<ring[slot,pu[e]]:ring[slot,pu[e]]=cand
  for k in range(n):
   node=reverse[k]
   for e in range(zo[node],zo[node+1]):
    cand=zc[e]+ring[slot,zh[e]]
    if cand<ring[slot,node]:ring[slot,node]=cand
  while cursor<len(release) and release[cursor]==t:out[cursor]=ring[slot,origin[cursor]];cursor+=1
 if cursor!=len(release):raise ValueError('unpriced original release')
 return out

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 start=time.monotonic();dp=R/'PIT_Q_R88_TOP_UNPRICED_CYCLE_MONOTONE_PRE_RUN_R89.json';d=rd(dp);rp=R/'runs/pit_q_r88_top_unpriced_cycle_monotone_r89/RESULT.json';rec=rd(rp);r86p=R/'runs/pit_q_r84_selected_factor_full_reprice_r86/RESULT.json';r86=rd(r86p);c87p=R/'runs/pit_q_r84_selected_factor_full_reprice_r86/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R87.json';c87=rd(c87p);tr88p=R/'PIT_Q_R86_ALL_BRIDGE_OD_SAMPLE_TRACE_R88.json'
 if sha(c87p)!=d['R87_independent_full_graph_certificate_sha256'] or sha(tr88p)!=d['R88_original_path_sample_sha256'] or rec['design_sha256']!=sha(dp) or rec['generic_price_core_sha256']!=sha(R/'q_original_dual_price_profile_common_r89.py'):raise ValueError('frozen predecessor and producer identity')
 if [x['candidate_flat_toll_minutes'] for x in rec['history']]!=d['candidate_flat_toll_grid_minutes'] or rec['selected_flat_toll_minutes'] not in d['candidate_flat_toll_grid_minutes'] or rec['best_conservative_full_original_graph_lower']!=max(x['conservative_full_original_graph_lower'] for x in rec['history']):raise ValueError('complete frozen candidate grid')
 cp=R/'cases/pittsburgh_S2_Q__sparse_common_dev9_delayed_zero_gc.json';cfg=rd(cp);source=Path(cfg['source_dir']);hashes={x:sha(source/x) for x in ('network.csv','access.csv','assignment_od_pce.csv')}
 if sha(cp)!=d['config_sha256'] or hashes!=d['original_source_hashes']==cfg['expected_source_hashes']:raise ValueError('original source drift')
 net=rows(source/'network.csv');acc=rows(source/'access.csv');od=rows(source/'assignment_od_pce.csv');nodes=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(nodes)};zone={x['zone_id']:ix[x['node_id']] for x in acc}
 if len(zone)!=len(acc) or len(od)!=1406:raise ValueError('original access OD count')
 u=np.array([ix[x['from_node_id']] for x in net],np.int32);v=np.array([ix[x['to_node_id']] for x in net],np.int32);cost=np.array([float(x['vdf_fftt']) for x in net]);phys=np.array([x[cfg['physical_field']]==cfg['physical_value'] for x in net]);dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dur=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 if len(od)*T!=cfg['expected_commodity_events'] or abs(T*dt-3600)>1e-8:raise ValueError('original release identity')
 pe=np.flatnonzero(phys);ze=np.flatnonzero(~phys);zu=u[ze];zv=v[ze];zc=cost[ze];sort=np.argsort(zu,kind='stable');zu=zu[sort];zv=zv[sort];zc=zc[sort];zo=np.r_[0,np.cumsum(np.bincount(zu,minlength=len(nodes)))].astype(np.int32);indeg=np.bincount(zv,minlength=len(nodes)).astype(np.int32);queue=deque(np.flatnonzero(indeg==0).tolist());topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for e in range(zo[node],zo[node+1]):
   nxt=int(zv[e]);indeg[nxt]-=1
   if indeg[nxt]==0:queue.append(nxt)
 if len(topo)!=len(nodes):raise ValueError('original zero-time cycle')
 reverse=np.asarray(topo[::-1],np.int32);incoming=[[] for _ in nodes]
 for e in range(len(net)):incoming[v[e]].append((int(u[e]),float(cost[e]),int(dur[e])))
 aonp=R/'runs/sparse_common_dev9_delayed_zero_gc/pittsburgh_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz';candidate=list(map(int,d['candidate_new_original_physical_edges']))
 with np.load(aonp,allow_pickle=False) as z:
  if np.any(np.isin(z['edge_index'],candidate)):raise ValueError('candidate original AON use invalidates unaffected set')
 basearr=Path(r86['array_path']);newarr=Path(rec['array_path'])
 if sha(basearr)!=r86['array_sha256'] or sha(basearr)!=c87['producer_array_sha256'] or sha(newarr)!=rec['array_sha256']:raise ValueError('base/new event arrays')
 with np.load(basearr,allow_pickle=False) as z:ids=z['original_OD_index'];release=z['original_release_step'];base_values=z['adjusted_shortest_cost']
 if len(ids)!=d['expected_base_affected_events']:raise ValueError('all original base affected events')
 dests=np.array([zone[x['d_zone_id']] for x in od],np.int32);origins=np.array([zone[x['o_zone_id']] for x in od],np.int32);q=np.array([float(x['volume_pce'])*float(cfg['demand_factor']) for x in od]);target=int(d['bridge_destination_node_index']);pos=np.flatnonzero(dests[ids]==target);pos=pos[np.argsort(-release[pos],kind='stable')]
 if len(pos)!=d['expected_exact_bridge_destination_events'] or target!=33925:raise ValueError('bridge destination original event set')
 with np.load(newarr,allow_pickle=False) as z:
  if not np.array_equal(z['original_OD_index'],ids[pos]) or not np.array_equal(z['original_release_step'],release[pos]) or np.max(abs(z['base_adjusted_shortest_cost']-base_values[pos]))>1e-12 or abs(float(z['candidate_flat_toll_minutes'][0])-rec['selected_flat_toll_minutes'])>1e-12:raise ValueError('producer selected event identity')
  claimed=z['new_adjusted_shortest_cost']
 h,bound=reverse_static(len(nodes),incoming,target);end=26799;first=185;bridge=6410
 if end+int(np.max(dur))+bound>H or d['base_bridge_factor']!=.2:raise ValueError('terminal/bridge support')
 flat=np.zeros(len(pe),np.float64)
 for e in d['base_old_cycle_original_edges']:
  at=np.flatnonzero(pe==e)
  if len(at)!=1:raise ValueError('original old cycle physical row')
  flat[at[0]]=float(d['base_old_cycle_flat_toll_minutes'])
 for e in d['base_second_cycle_original_edges']:
  at=np.flatnonzero(pe==e)
  if len(at)!=1:raise ValueError('original second cycle physical row')
  flat[at[0]]=float(d['base_second_cycle_flat_toll_minutes'])
 for e in candidate:
  at=np.flatnonzero(pe==e)
  if len(at)!=1:raise ValueError('candidate original physical row')
  flat[at[0]]=float(rec['selected_flat_toll_minutes'])
 bp=np.flatnonzero(pe==bridge)
 if len(bp)!=1:raise ValueError('original bridge physical row')
 lam=np.array([float(d['base_bridge_factor'])*dt/60*(end-t) for t in range(first,end)])
 values=independent_profile_flat(len(nodes),H,end,dt,u[pe],v[pe],cost[pe],dur[pe],int(bp[0]),first,lam,flat,zo,zv,zc,reverse,target,h,release[pos],origins[ids[pos]])
 err=float(np.max(abs(values-claimed)))
 if err>1e-7 or np.min(values-base_values[pos])<-1e-7:raise ValueError('independent priced shortest or monotonicity')
 delta=float(np.dot(q[ids[pos]]/T,values-base_values[pos]));penalty=sum(float(net[e]['capacity'])*dt/3600. for e in candidate)*end*float(rec['selected_flat_toll_minutes']);lower=float(c87['independent_full_original_graph_lower'])+delta-penalty
 if abs(lower-rec['best_conservative_full_original_graph_lower'])>1e-6 or abs(delta-rec['exact_bridge_dest_cost_increment'])>1e-6 or abs(penalty-rec['candidate_original_capacity_price_increment'])>1e-6 or lower>c87['original_feasible_upper']+1e-6:raise ValueError('independent original full demand dual accounting')
 cert={'schema':'PIT_Q_R88_TOP_UNPRICED_CYCLE_MONOTONE_INDEPENDENT_CERT_R90','status':'PASS_CONSERVATIVE_FULL_ORIGINAL_GRAPH_DUAL_LOWER_OPEN_OPTIMALITY','original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_events':len(od)*T,'base_affected_events':len(ids),'exact_bridge_destination_events':len(pos),'other_destination_events_reused_from_R87':len(ids)-len(pos),'candidate_original_physical_edges':candidate,'selected_flat_toll_minutes':rec['selected_flat_toll_minutes'],'prior_R87_independent_lower':c87['independent_full_original_graph_lower'],'independent_exact_bridge_dest_cost_increment':delta,'independent_original_capacity_price_increment':penalty,'independent_conservative_full_original_graph_lower':lower,'original_feasible_upper':c87['original_feasible_upper'],'relative_open_gap':(c87['original_feasible_upper']-lower)/c87['original_feasible_upper'],'max_producer_event_price_error':err,'R87_independent_certificate_sha256':sha(c87p),'R88_source_path_trace_sha256':sha(tr88p),'R86_base_array_sha256':sha(basearr),'producer_result_sha256':sha(rp),'producer_selected_array_sha256':sha(newarr),'method':'Original CSV physical/zero Bellman for all original bridge destination affected releases; candidate edges absent from all original AON routes; every other destination retains independently certified R87 shortest costs as monotone lower bound under nonnegative new physical prices.','wall_seconds':time.monotonic()-start,'scientific_limit':'Conservative full original graph dual lower only, no new primal or global CG optimum.'}
 out=R/'runs/pit_q_r88_top_unpriced_cycle_monotone_r89/INDEPENDENT_CONSERVATIVE_DUAL_CERT_R90.json';out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':cert['status'],'lower':lower,'gap':cert['relative_open_gap'],'err':err,'seconds':cert['wall_seconds']}),flush=True)
if __name__=='__main__':main()
