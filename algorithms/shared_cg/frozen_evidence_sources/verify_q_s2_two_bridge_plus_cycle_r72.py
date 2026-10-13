"""Independent original CSV physical/zero-layer Bellman replay of S2 R71 dual."""
from pathlib import Path
from collections import deque
import csv,hashlib,heapq,json,time
import numpy as np
from numba import njit
R=Path(__file__).resolve().parent
@njit(cache=False)
def independent_profile(n,H,terminal,dt,pu,pv,pc,pdur,priceid,pstart,pend,pweight,loopmask,flat,zo,zh,zc,reverse,dest,h,release,origin):
 D=int(np.max(pdur));ring=np.empty((D+1,n),np.float64);out=np.empty(len(release),np.float64);cursor=0
 for j in range(D+1):
  for node in range(n):ring[j,node]=h[node]
 for t in range(terminal-1,-1,-1):
  slot=t%(D+1);future=(t+1)%(D+1)
  for node in range(n):ring[slot,node]=0. if node==dest else ring[future,node]+dt/60.
  for e in range(len(pu)):
   d=pdur[e]
   if t+d>H:continue
   value=pc[e]+ring[(t+d)%(D+1),pv[e]];j=priceid[e]
   if j>=0 and pstart[j]<=t<pend[j]:value+=pweight[j]*(pend[j]-t)
   if loopmask[e]:value+=flat
   if value<ring[slot,pu[e]]:ring[slot,pu[e]]=value
  for k in range(n):
   node=reverse[k]
   for e in range(zo[node],zo[node+1]):
    value=zc[e]+ring[slot,zh[e]]
    if value<ring[slot,node]:ring[slot,node]=value
  while cursor<len(release) and release[cursor]==t:out[cursor]=ring[slot,origin[cursor]];cursor+=1
 if cursor!=len(release):raise ValueError('unpriced original release')
 return out

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def reverse_static(n,inc,dest):
 h=np.full(n,np.inf);steps=np.full(n,10**9,np.int32);h[dest]=0.;steps[dest]=0;heap=[(0.,0,dest)]
 while heap:
  value,t,node=heapq.heappop(heap)
  if value>h[node]+1e-10 or (abs(value-h[node])<=1e-10 and t>steps[node]):continue
  for prev,c,d in inc[node]:
   a=value+c;b=t+d
   if a<h[prev]-1e-10 or (abs(a-h[prev])<=1e-10 and b<steps[prev]):h[prev]=a;steps[prev]=b;heapq.heappush(heap,(a,b,prev))
 return h,int(np.max(steps[np.isfinite(h)]))
def main():
 start=time.monotonic();dp=R/'Q_S2_TWO_BRIDGE_PLUS_CYCLE_CAPACITY_TOLL_PRE_RUN_R71.json';d=rd(dp);rp=R/'runs/q_s2_two_bridge_plus_cycle_toll_r71/RESULT.json';rec=rd(rp);r28p=R/'Q_S2_TWO_BRIDGE_FINE_RESULT_R28.json';c28p=R/'Q_S2_TWO_BRIDGE_FINE_INDEPENDENT_CERT_R28.json';r60p=R/'runs/q_common_fixed_service_greedy_r57/urbana_S2_Q/CAPACITY_DIAGNOSTIC_R60.json';f35p=R/'Q_F_BRIDGE_WITH_FIXED_LOOP_GRID_RESULT_R35.json';r28=rd(r28p)
 if sha(r28p)!=d['R28_result_sha256'] or sha(c28p)!=d['R28_independent_certificate_sha256'] or sha(r60p)!=d['R60_original_capacity_diagnostic_sha256'] or sha(f35p)!=d['F_R35_source_cycle_result_sha256']:raise ValueError('prior frozen evidence drift')
 if rec['design_sha256']!=sha(dp) or [x['flat_cycle_toll_minutes'] for x in rec['history']]!=d['flat_cycle_toll_grid_minutes'] or max(x['producer_full_original_lower'] for x in rec['history'])!=rec['producer_full_original_lower'] or rec['best_cycle_flat_toll_minutes'] not in d['flat_cycle_toll_grid_minutes']:raise ValueError('complete frozen grid')
 cfgp=R/'cases/urbana_S2_Q__sparse_common_dev9_delayed_zero_gc.json';cfg=rd(cfgp);source=Path(cfg['source_dir']);hashes={x:sha(source/x) for x in ('network.csv','access.csv','assignment_od_pce.csv')}
 if sha(cfgp)!=d['config_sha256'] or hashes!=cfg['expected_source_hashes'] or hashes!=d['original_source_hashes'] or hashes!=rec['source_hashes']:raise ValueError('original source identity')
 net=rows(source/'network.csv');od=rows(source/'assignment_od_pce.csv');acc=rows(source/'access.csv');names=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(names)};access={x['zone_id']:ix[x['node_id']] for x in acc};n=len(names);dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps'])
 if len(od)*T!=cfg['expected_commodity_events'] or len(od)!=418 or len(access)!=len(acc) or abs(T*dt-3600)>1e-8:raise ValueError('complete original OD/time/access')
 u=np.asarray([ix[x['from_node_id']] for x in net],np.int32);v=np.asarray([ix[x['to_node_id']] for x in net],np.int32);cost=np.asarray([float(x['vdf_fftt']) for x in net]);physical=np.asarray([x[cfg['physical_field']]==cfg['physical_value'] for x in net]);dur=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 pe=np.flatnonzero(physical);ze=np.flatnonzero(~physical);zu=u[ze];zv=v[ze];zc=cost[ze];order=np.argsort(zu,kind='stable');zu=zu[order];zv=zv[order];zc=zc[order];zo=np.r_[0,np.cumsum(np.bincount(zu,minlength=n))].astype(np.int32);indeg=np.bincount(zv,minlength=n).astype(np.int32);queue=deque(np.flatnonzero(indeg==0).tolist());topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for e in range(zo[node],zo[node+1]):
   nxt=int(zv[e]);indeg[nxt]-=1
   if indeg[nxt]==0:queue.append(nxt)
 if len(topo)!=n:raise ValueError('zero-time cycle')
 reverse=np.asarray(topo[::-1],np.int32);incoming=[[] for _ in names]
 for e in range(len(net)):incoming[v[e]].append((int(u[e]),float(cost[e]),int(dur[e])))
 intervals=[(int(x['original_edge_index']),int(x['first_entry_step']),int(x['end_exclusive_entry_step'])) for x in r28['price_intervals']]
 if [x[0] for x in intervals]!=d['fixed_R28_original_edges'] or [x[0] for x in intervals]!=rec['bridge_original_edges'] or d['fixed_R28_factor_pair']!=r28['selected_factor_pair']:raise ValueError('accepted bridge prices')
 loops=list(map(int,d['cycle_original_physical_edges']));top={x['original_edge_index'] for x in rd(r60p)['top_binding_resources']}
 if loops!=rec['cycle_original_edges'] or loops!=rd(f35p)['cycle_original_edge_indices'] or not set(loops)<=top:raise ValueError('original binding cycle evidence')
 terminal=int(d['cycle_toll_end_exclusive_step']);flat=float(rec['best_cycle_flat_toll_minutes']);factors=np.asarray(d['fixed_R28_factor_pair'],np.float64)
 if terminal!=max(x[2] for x in intervals) or d['cycle_toll_start_step']!=0:raise ValueError('cycle time price support')
 priceid=np.full(len(pe),-1,np.int32)
 for j,(e,first,end) in enumerate(intervals):
  at=np.flatnonzero(pe==e)
  if len(at)!=1:raise ValueError('priced original physical edge')
  priceid[at[0]]=j
 pstart=np.asarray([x[1] for x in intervals],np.int32);pend=np.asarray([x[2] for x in intervals],np.int32);pweight=factors*dt/60.;loopmask=np.isin(pe,loops)
 aonp=R/'runs/sparse_common_dev9_delayed_zero_gc/urbana_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 if sha(aonp)!=d['AON_sha256']:raise ValueError('source AON hash')
 with np.load(aonp,allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 arrp=Path(rec['array_path'])
 if sha(arrp)!=rec['array_sha256']:raise ValueError('producer priced array')
 with np.load(arrp,allow_pickle=False) as z:ids0=z['original_OD_index'];release0=z['original_release_step'];claimed=z['adjusted_shortest_cost']
 origins=np.asarray([access[x['o_zone_id']] for x in od],np.int32);dests=np.asarray([access[x['d_zone_id']] for x in od],np.int32);trees={};bounds={};flag=np.zeros((len(od),T),np.bool_);lookup={e:(first,end) for e,first,end in intervals};target=set(loops)|set(lookup);baseline=0.;maxarrival=0
 for i,row in enumerate(od):
  demand=float(row['volume_pce'])*float(cfg['demand_factor'])
  if abs(demand-q[i])>1e-9:raise ValueError('original source demand')
  dest=int(dests[i]);origin=int(origins[i])
  if dest not in trees:trees[dest],bounds[dest]=reverse_static(n,incoming,dest)
  h=trees[dest];node=origin;t=0;value=0.
  for j in range(int(off[i]),int(off[i+1])):
   e=int(ae[j]);offset=int(at[j])
   if e<0 or e>=len(net) or u[e]!=node or offset!=t:raise ValueError('AON original node/time mapping')
   if e in target:
    first,end=lookup[e] if e in lookup else (0,terminal);lo=max(0,first-offset);hi=min(T,end-offset)
    if lo<hi:flag[i,lo:hi]=True
   value+=cost[e];t+=int(dur[e]);node=int(v[e])
  if node!=dest or t+T-1>H or abs(value-static[i])>1e-7 or abs(value-h[origin])>1e-7:raise ValueError('AON original shortest/horizon')
  baseline+=demand*h[origin];maxarrival=max(maxarrival,t+T-1)
 ids,release=np.nonzero(flag);ids=ids.astype(np.int32);release=release.astype(np.int32)
 if not np.array_equal(ids,ids0) or not np.array_equal(release,release0) or len(ids)!=rec['affected_original_release_events']:raise ValueError('all original affected releases')
 values=np.empty(len(ids),np.float64);D=int(np.max(dur));profiles={}
 for dest in np.unique(dests[ids]):
  dest=int(dest);h=trees[dest]
  if terminal+D+bounds[dest]>H:raise ValueError('exact static terminal')
  pos=np.flatnonzero(dests[ids]==dest);pos=pos[np.argsort(-release[pos],kind='stable')]
  values[pos]=independent_profile(n,H,terminal,dt,u[pe],v[pe],cost[pe],dur[pe],priceid,pstart,pend,pweight,loopmask,flat,zo,zv,zc,reverse,dest,h,release[pos],origins[ids[pos]])
  profiles[str(dest)]=bounds[dest]
 err=float(np.max(abs(values-claimed)))
 if err>1e-7:raise ValueError('independent priced shortest paths differ')
 bridge_constant=sum(float(net[e]['capacity'])*dt/3600.*float(factors[j])*dt/60.*(end-first)*(end-first+1)/2 for j,(e,first,end) in enumerate(intervals));cycle_constant=sum(float(net[e]['capacity'])*dt/3600.*terminal*flat for e in loops);penalty=bridge_constant+cycle_constant;lower=baseline+float(np.dot(q[ids]/T,values-static[ids]))-penalty
 if abs(lower-rec['producer_full_original_lower'])>1e-6 or abs(penalty-rec['capacity_price_constant'])>1e-6:raise ValueError('independent original full dual accounting')
 cert={'schema':'Q_S2_TWO_BRIDGE_PLUS_CYCLE_INDEPENDENT_ORIGINAL_GRAPH_R72','status':'PASS_VALID_FULL_ORIGINAL_GRAPH_DUAL_LOWER_OPEN_OPTIMALITY','case_id':'urbana_S2_Q','original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_events':len(od)*T,'original_horizon_steps':H,'original_physical_arc_count':len(pe),'all_original_physical_capacity_rows':len(pe)*H,'priced_original_capacity_rows':sum(end-first for e,first,end in intervals)+len(loops)*terminal,'affected_release_events_independently_priced':len(ids),'unaffected_original_release_events_proven':len(od)*T-len(ids),'profile_destinations':len(profiles),'max_original_AON_arrival_step':maxarrival,'static_terminal_duration_bounds':profiles,'independent_baseline_lower':baseline,'independent_capacity_price_constant':penalty,'independent_full_original_graph_lower':lower,'R58_independent_feasible_upper':rec['R58_independent_feasible_upper'],'relative_open_gap':(rec['R58_independent_feasible_upper']-lower)/rec['R58_independent_feasible_upper'],'max_producer_event_price_error':err,'producer_result_sha256':sha(rp),'producer_array_sha256':sha(arrp),'method':'independent original CSV all OD and release audit, physical row Bellman then zero-time DAG, all capacity price constants','wall_seconds':time.monotonic()-start,'scientific_limit':'Valid original time-graph dual lower only; no complete shared CG optimality.'}
 out=R/'runs/q_s2_two_bridge_plus_cycle_toll_r71/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R72.json';out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':cert['status'],'lower':lower,'gap':cert['relative_open_gap'],'err':err,'seconds':cert['wall_seconds']}),flush=True)
if __name__=='__main__':main()
