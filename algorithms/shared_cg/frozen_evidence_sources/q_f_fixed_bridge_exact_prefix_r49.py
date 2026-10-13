"""Exact original-network minimum-cost prefixes at fixed certified bridge entry times."""
from pathlib import Path
import csv,hashlib,json,time
import numpy as np
from numba import njit
from q_profile_dp_probe_v2 import setup
from original_time_path_column_core_r41 import replay_column
R=Path(__file__).resolve().parent
@njit(cache=False)
def exact_prefix_policy(n,maxdelta,dt,offsets,order,head,cost,duration,bridge,dest,origins):
 D=int(np.max(duration));ring=np.empty((D+1,n),np.float64);action=np.empty((maxdelta+1,n),np.uint8);values=np.empty((maxdelta+1,len(origins)),np.float64)
 for slot in range(D+1):
  for node in range(n):ring[slot,node]=np.inf
 for delta in range(maxdelta+1):
  slot=delta%(D+1);prev=(delta-1)%(D+1)
  for kk in range(n):
   node=order[kk]
   if delta==0:
    best=0. if node==dest else np.inf;chosen=255
   else:
    best=ring[prev,node]+dt/60.;chosen=254
   for e in range(offsets[node],offsets[node+1]):
    if e==bridge:continue
    duration_e=int(duration[e])
    if duration_e>delta:continue
    nextslot=(delta-duration_e)%(D+1)
    cand=cost[e]+ring[nextslot,head[e]]
    if cand<best-1e-12:best=cand;chosen=e-offsets[node]
   ring[slot,node]=best;action[delta,node]=chosen
  for k in range(len(origins)):values[delta,k]=ring[slot,origins[k]]
 return action,values

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
 started=time.monotonic();dp=R/'Q_F_FIXED_BRIDGE_TIME_EXACT_PREFIX_PRE_RUN_R49.json';d=rd(dp)
 for k in ('source_config','R43_result','R43_independent_certificate','R44_array','original_AON'):
  if sha(d[k])!=d[k+'_sha256']:raise ValueError('frozen hash drift '+k)
 cfg=rd(d['source_config']);src=Path(cfg['source_dir'])
 if {n:sha(src/n) for n in d['original_source_hashes']}!=d['original_source_hashes']:raise ValueError('source drift')
 r43=rd(d['R43_result']);c43=rd(d['R43_independent_certificate'])
 if c43['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or sha(r43['fragment_path'])!=r43['fragment_sha256']:raise ValueError('base drift')
 cfg2,net,od,nodes,access,u,v,cost,dur,physical,offsets,order,inc,pid,starts,ends,weights,inverse=setup('urbana_F_Q',[(447,0,1,1.)],1.)
 if cfg2!=cfg:raise ValueError('graph/config drift')
 bridge=int(d['bridge_original_edge_index']);be=int(inverse[bridge]);target=int(u[be]);dt=float(cfg['dt_seconds']);H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);maxdelta=int(d['max_fixed_bridge_delay_steps'])
 orig_edge=np.empty(len(inverse),np.int32);orig_edge[inverse]=np.arange(len(inverse),dtype=np.int32)
 if np.max(np.diff(offsets))>=254:raise ValueError('policy ordinal cannot fit uint8')
 with np.load(d['R44_array'],allow_pickle=False) as z:sel_i=z['original_OD_index'];sel_r=z['original_release_step']
 with np.load(d['original_AON'],allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 with np.load(r43['fragment_path'],allow_pickle=False) as z:fod=z['od_index'];fr=z['release_step'];fm=z['mass_pce'];fw=z['wait_steps'];stage=z['stage_original_edge_index']
 if len(sel_i)!=100 or len(q)!=418 or len(q)*T!=6019200:raise ValueError('original event identity')
 sj=list(stage).index(bridge);unique_i=np.asarray(sorted(set(map(int,sel_i))),np.int32);origin_nodes=np.asarray([access[od[int(i)]['o_zone_id']] for i in unique_i],np.int32);omap={int(i):j for j,i in enumerate(unique_i)}
 fragments=[];paths=[];aft=[];observed_delta=[]
 for i0,r0 in zip(sel_i,sel_r):
  i=int(i0);r=int(r0);idx=np.flatnonzero((fod==i)&(fr==r));path=ae[int(off[i]):int(off[i+1])];entry=at[int(off[i]):int(off[i+1])];bk=np.flatnonzero(path==bridge)
  if len(bk)!=1 or len(idx)==0:raise ValueError('selected bridge event')
  b=int(bk[0]);basebridge=int(entry[b]);suffix=path[b+1:];suffixoffset=entry[b+1:]-basebridge
  if np.any(fw[idx,sj+1:]!=0):raise ValueError('selected downstream waits')
  if abs(np.sum(fm[idx])-q[i]/T)>1e-10:raise ValueError('event mass')
  for k in idx:
   service=r+basebridge+int(np.sum(fw[k,:sj+1]));delta=service-r;observed_delta.append(delta)
   fragments.append((int(k),i,r,float(fm[k]),service,delta,b,suffix,suffixoffset))
 if len(fragments)!=int(d['selected_fragment_count']) or max(observed_delta)!=maxdelta:raise ValueError('frozen fragment count/delay')
 action,profile=exact_prefix_policy(len(nodes),maxdelta,dt,offsets,order,v,cost,dur,be,target,origin_nodes)
 flat_e=[];flat_t=[];flat_off=[0];basecost=[];oldcost=[];records=[];maxerr=0.;cheaper=0;positive_saving=0.
 for frag_index,i,r,mass,service,delta,b,suffix,suffixoffset in fragments:
  if not np.isfinite(profile[delta,omap[i]]):raise ValueError('prefix unreachable')
  node=int(origin_nodes[omap[i]]);remain=int(delta);t=int(r);edges=[];entry=[];guard=0
  while remain>0 or node!=target:
   choice=int(action[remain,node])
   if choice==254:
    t+=1;remain-=1
   elif choice<254:
    e=int(offsets[node])+choice
    if e>=offsets[node+1] or e==be:raise ValueError('invalid prefix action')
    edges.append(int(orig_edge[e]));entry.append(t);t+=int(dur[e]);remain-=int(dur[e]);node=int(v[e])
   else:raise ValueError('premature prefix terminal')
   guard+=1
   if guard>100000 or remain<0:raise ValueError('prefix path cycle/underflow')
  if t!=service:raise ValueError('bridge time')
  edges.append(bridge);entry.append(service)
  for e0,off0 in zip(suffix,suffixoffset):edges.append(int(e0));entry.append(service+int(off0))
  col=replay_column(net,edges,entry,nodes[int(origin_nodes[omap[i]])],nodes[int(access[od[i]['d_zone_id']])],r,dt,H,physical_field=cfg['physical_field'],physical_value=cfg['physical_value'])
  val=float(profile[delta,omap[i]])+float(cost[be])+sum(float(net[int(e)]['vdf_fftt']) for e in suffix)
  err=abs(col['base_cost_minutes']-val)
  if err>1e-7:raise ValueError('DP/path true cost mismatch')
  maxerr=max(maxerr,err);baseline=float(static[i])+float(np.sum(fw[frag_index]))*dt/60.;gain=baseline-col['base_cost_minutes']
  if gain>1e-9:cheaper+=1;positive_saving+=gain*mass
  flat_e.extend(edges);flat_t.extend(entry);flat_off.append(len(flat_e));basecost.append(col['base_cost_minutes']);oldcost.append(baseline)
  records.append({'fragment_index':frag_index,'original_OD_index':i,'release_step':r,'fragment_mass_pce':mass,'bridge_entry_step':service,'fixed_prefix_duration_steps':delta,'original_AON_fragment_cost':baseline,'exact_prefix_candidate_cost':col['base_cost_minutes'],'unit_saving_minutes':gain,'path_arcs':len(edges),'arrival_step':col['arrival_step'],'DP_path_cost_error_minutes':err})
 out=R/'runs/q_f_fixed_bridge_exact_prefix_r49';out.mkdir(parents=True,exist_ok=True)
 if (out/'RESULT.json').exists():raise FileExistsError(out/'RESULT.json')
 arr=out/'PATH_ARRAYS.npz';np.savez_compressed(arr,fragment_index=np.asarray([x[0] for x in fragments],np.int64),original_OD_index=np.asarray([x[1] for x in fragments],np.int32),original_release_step=np.asarray([x[2] for x in fragments],np.int32),fragment_mass_pce=np.asarray([x[3] for x in fragments]),bridge_entry_step=np.asarray([x[4] for x in fragments],np.int32),edge_offset=np.asarray(flat_off,np.int64),original_edge_index=np.asarray(flat_e,np.int32),original_entry_step=np.asarray(flat_t,np.int32),R43_fragment_unit_cost=np.asarray(oldcost),candidate_base_cost=np.asarray(basecost))
 result={'schema':'Q_F_FIXED_BRIDGE_TIME_EXACT_PREFIX_RESULT_R49','status':'PASS_103_FULL_ORIGINAL_FIXED_BRIDGE_PATHS_PENDING_JOINT_CAPACITY','design_sha256':sha(dp),'source_hashes':d['original_source_hashes'],'R43_independent_certificate_sha256':sha(d['R43_independent_certificate']),'original_positive_OD':len(q),'original_release_events':len(q)*T,'selected_fragments':len(fragments),'max_fixed_bridge_delay_steps':maxdelta,'candidate_paths_cheaper_than_R43_fragment':cheaper,'unconstrained_positive_saving_PCE_minutes':positive_saving,'maximum_DP_path_cost_error_minutes':maxerr,'total_original_arc_actions':len(flat_e),'array_path':str(arr),'array_sha256':sha(arr),'records':records,'wall_seconds':time.monotonic()-started,'scientific_limit':'Exact shortest prebridge path at each selected certified service step; individual paths, not joint capacity or full CG optimum.'}
 (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'cheaper':cheaper,'unconstrained_gain':positive_saving,'arcs':len(flat_e),'wall_seconds':result['wall_seconds']}),flush=True)
if __name__=='__main__':main()
