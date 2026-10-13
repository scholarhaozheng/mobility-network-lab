"""Two accepted S2 bridge prices plus independently binding source-cycle capacity tolls."""
from pathlib import Path
import csv,hashlib,json,time
import numpy as np
from numba import njit
from q_profile_dp_probe_v2 import setup,static_h
R=Path(__file__).resolve().parent;CASE='urbana_S2_Q'
@njit(cache=False)
def price_profile(n,H,end,dt,off,order,head,cost,duration,priceid,starts,ends,slopes,loopmask,flat,dest,h,release,origin):
 D=int(np.max(duration));ring=np.empty((D+1,n),np.float64);out=np.empty(len(release),np.float64);cursor=0
 for j in range(D+1):
  for node in range(n):ring[j,node]=h[node]
 for t in range(end-1,-1,-1):
  slot=t%(D+1);future=(t+1)%(D+1)
  for k in range(n):
   node=order[k];best=0. if node==dest else ring[future,node]+dt/60.
   for e in range(off[node],off[node+1]):
    d=duration[e]
    if t+d>H:continue
    nxt=head[e];cand=cost[e]+(ring[slot,nxt] if d==0 else ring[(t+d)%(D+1),nxt]);z=priceid[e]
    if z>=0 and starts[z]<=t<ends[z]:cand+=slopes[z]*(ends[z]-t)
    if loopmask[e]:cand+=flat
    if cand<best:best=cand
   ring[slot,node]=best
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
def save(p,x):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def main():
 start=time.monotonic();dp=R/'Q_S2_TWO_BRIDGE_PLUS_CYCLE_CAPACITY_TOLL_PRE_RUN_R71.json';d=rd(dp);r28p=R/'Q_S2_TWO_BRIDGE_FINE_RESULT_R28.json';c28p=R/'Q_S2_TWO_BRIDGE_FINE_INDEPENDENT_CERT_R28.json';r60p=R/'runs/q_common_fixed_service_greedy_r57/urbana_S2_Q/CAPACITY_DIAGNOSTIC_R60.json';f35p=R/'Q_F_BRIDGE_WITH_FIXED_LOOP_GRID_RESULT_R35.json';r28=rd(r28p);r60=rd(r60p);f35=rd(f35p)
 if sha(r28p)!=d['R28_result_sha256'] or sha(c28p)!=d['R28_independent_certificate_sha256'] or sha(r60p)!=d['R60_original_capacity_diagnostic_sha256'] or sha(f35p)!=d['F_R35_source_cycle_result_sha256']:raise ValueError('frozen accepted evidence')
 cp=R/'cases'/f'{CASE}__sparse_common_dev9_delayed_zero_gc.json';cfg=rd(cp);source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in ('network.csv','access.csv','assignment_od_pce.csv')}
 if sha(cp)!=d['config_sha256'] or hashes!=cfg['expected_source_hashes'] or hashes!=d['original_source_hashes']:raise ValueError('original source drift')
 loops=np.asarray(d['cycle_original_physical_edges'],np.int32);top={x['original_edge_index'] for x in r60['top_binding_resources']}
 if list(loops)!=f35['cycle_original_edge_indices'] or not set(map(int,loops))<=top:raise ValueError('source cycle physical binding support')
 aonp=R/'runs/sparse_common_dev9_delayed_zero_gc'/CASE/'solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
 if sha(aonp)!=d['AON_sha256']:raise ValueError('AON drift')
 with np.load(aonp,allow_pickle=False) as z:ao=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 net=rows(source/'network.csv');T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dt=float(cfg['dt_seconds']);price=[(int(x['original_edge_index']),int(x['first_entry_step']),int(x['end_exclusive_entry_step']),1.) for x in r28['price_intervals']]
 if [x[0] for x in price]!=d['fixed_R28_original_edges'] or r28['selected_factor_pair']!=d['fixed_R28_factor_pair'] or max(x[2] for x in price)!=d['cycle_toll_end_exclusive_step']:raise ValueError('R28 dual price identity')
 for e in loops:
  if net[int(e)][cfg['physical_field']]!=cfg['physical_value']:raise ValueError('original physical cycle resource')
 cfg2,net2,od,nodes,access,u,v,cost,dur,physical,off,order,inc,pid,starts,ends,weights,inverse=setup(CASE,price,1.)
 if cfg2!=cfg or len(q)!=len(od) or len(q)*T!=cfg['expected_commodity_events'] or np.max(abs(q-np.asarray([float(x['volume_pce'])*float(cfg['demand_factor']) for x in od])))>1e-9:raise ValueError('full original demand')
 loopmask=np.zeros(len(cost),np.bool_);loopmask[inverse[loops]]=True;target=set(map(int,loops))|{x[0] for x in price};flag=np.zeros((len(od),T),np.bool_);lookup={e:(f,en) for e,f,en,_ in price}
 for i in range(len(od)):
  for j in range(int(ao[i]),int(ao[i+1])):
   e=int(ae[j])
   if e not in target:continue
   first,end=lookup[e] if e in lookup else (0,d['cycle_toll_end_exclusive_step']);offset=int(at[j]);lo=max(0,first-offset);hi=min(T,end-offset)
   if lo<hi:flag[i,lo:hi]=True
 ids,release=np.nonzero(flag);ids=ids.astype(np.int32);release=release.astype(np.int32);origin=np.asarray([access[x['o_zone_id']] for x in od],np.int32);dest=np.asarray([access[x['d_zone_id']] for x in od],np.int32);terminal=d['cycle_toll_end_exclusive_step'];D=int(np.max(dur));profiles={}
 for z in np.unique(dest[ids]):
  h,maxsteps=static_h(len(nodes),inc,int(z));pos=np.flatnonzero(dest[ids]==z);pos=pos[np.argsort(-release[pos],kind='stable')]
  if terminal+D+maxsteps>H:raise ValueError('exact terminal boundary')
  if np.max(abs(h[origin[np.unique(ids[pos])]]-static[np.unique(ids[pos])]))>1e-7:raise ValueError('static original AON')
  profiles[int(z)]=(h,pos,maxsteps)
 factors=np.asarray(d['fixed_R28_factor_pair'],np.float64);slopes=factors*dt/60.;capunit=np.asarray([float(net[e]['capacity'])*dt/3600.*(dt/60.)*(en-f)*(en-f+1)/2 for e,f,en,_ in price]);loopcap=sum(float(net[int(e)]['capacity'])*dt/3600. for e in loops);base=float(np.dot(q,static));history=[];best=None
 out=R/'runs/q_s2_two_bridge_plus_cycle_toll_r71'
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 out.mkdir(parents=True)
 for flat in d['flat_cycle_toll_grid_minutes']:
  values=static[ids].astype(np.float64).copy()
  for z,(h,pos,maxsteps) in profiles.items():values[pos]=price_profile(len(nodes),H,terminal,dt,off,order,v,cost,dur,pid,starts,ends,slopes,loopmask,float(flat),z,h,release[pos],origin[ids[pos]])
  penalty=float(np.dot(factors,capunit))+loopcap*terminal*float(flat);lower=base+float(np.dot(q[ids]/T,values-static[ids]))-penalty
  if flat==0 and abs(lower-r28['valid_full_original_graph_lower'])>1e-5:raise ValueError('R28 zero-loop control')
  if lower>87820.38242178303+1e-6:raise ValueError('weak duality')
  row={'flat_cycle_toll_minutes':flat,'producer_full_original_lower':lower,'capacity_price_constant':penalty,'relative_open_gap_to_R58_upper':(87820.38242178303-lower)/87820.38242178303,'affected_original_release_events':len(ids),'priced_destinations':len(profiles),'elapsed_seconds':time.monotonic()-start};history.append(row);save(out/'PROGRESS.json',{'status':'RUNNING','design_sha256':sha(dp),'history':history});print(json.dumps(row),flush=True)
  if best is None or lower>best[0]:best=(lower,float(flat),values.copy(),penalty)
 lower,flat,values,penalty=best;arr=out/'BEST_PRICE_PROFILE.npz';np.savez_compressed(arr,original_OD_index=ids,original_release_step=release,adjusted_shortest_cost=values)
 rec={'schema':'Q_S2_TWO_BRIDGE_PLUS_CYCLE_TOLL_RESULT_R71','status':'PRODUCER_FULL_ORIGINAL_LOWER_PENDING_INDEPENDENT_REPRICE','case_id':CASE,'design_sha256':sha(dp),'source_hashes':hashes,'R28_independent_certificate_sha256':sha(c28p),'R60_original_capacity_diagnostic_sha256':sha(r60p),'original_positive_OD':len(q),'original_release_events':len(q)*T,'affected_original_release_events':len(ids),'unaffected_original_release_events_static_proven':len(q)*T-len(ids),'profile_destinations':len(profiles),'static_terminal_duration_bounds':{str(z):ms for z,(h,p,ms) in profiles.items()},'bridge_original_edges':[x[0] for x in price],'cycle_original_edges':list(map(int,loops)),'fixed_R28_factor_pair':d['fixed_R28_factor_pair'],'best_cycle_flat_toll_minutes':flat,'baseline_unconstrained_original_lower':base,'producer_full_original_lower':lower,'R58_independent_feasible_upper':87820.38242178303,'relative_open_gap':(87820.38242178303-lower)/87820.38242178303,'capacity_price_constant':penalty,'history':history,'array_path':str(arr),'array_sha256':sha(arr),'wall_seconds':time.monotonic()-start,'scientific_limit':'Original full graph S2 dual price family, no new feasible primal or global optimum assertion.'}
 save(out/'RESULT.json',rec);print(json.dumps({'status':rec['status'],'lower':lower,'flat':flat,'upper':rec['R58_independent_feasible_upper'],'gap':rec['relative_open_gap'],'seconds':rec['wall_seconds']}),flush=True)
if __name__=='__main__':main()
