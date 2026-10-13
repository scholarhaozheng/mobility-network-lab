"""One common exact original-time fixed-service greedy capacity kernel for two Q cases."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,gc,hashlib,json,time
import numpy as np
from numba import njit
from q_profile_dp_probe_v2 import setup
from q_f_fixed_bridge_exact_prefix_r49 import exact_prefix_policy
R=Path(__file__).resolve().parent
@njit(cache=False)
def delay_from_mask(mask,wait):
 value=0
 for j in range(len(wait)):
  if mask&(1<<j):value+=int(wait[j])
 return value
@njit(cache=False)
def greedy_chunk(indices,action,origin_by_od,fragment_index,OD,release,service_delay,mass,gain,waits,base_offset,base_edge,base_time,base_mask,suffix_offset,suffix_edge,suffix_time,bridge,bridge_internal,bridge_tail,offsets,head,duration,physical,original_edge,rowmap,capacity,load,marker,H,S,safety,swap):
 accepted=0;limited=0;total_mass=0.;saving=0.;max_actions=0
 for z in range(len(indices)):
  j=int(indices[z]);i=int(OD[j]);f=int(fragment_index[j]);r=int(release[j]);delta=int(service_delay[j]);stamp=j+1;w=waits[f]
  for p in range(int(base_offset[i]),int(base_offset[i+1])):
   e=int(base_edge[p]);t=r+int(base_time[p])+delay_from_mask(int(base_mask[p]),w);row=int(rowmap[e])
   if row<0 or t<0 or t>=S:raise ValueError('base row outside exact support')
   marker[row,t]=stamp
  node=int(origin_by_od[i]);remain=delta;t=r;guard=0;slack=np.inf;steps=0
  while remain>0 or node!=bridge_tail:
   choice=int(action[remain,node])
   if choice==254:t+=1;remain-=1
   elif choice<254:
    e=int(offsets[node])+choice
    if e>=offsets[node+1] or e==bridge_internal:raise ValueError('bad original policy arc')
    if physical[e]:
     oe=int(original_edge[e]);row=int(rowmap[oe])
     if row<0 or t<0 or t>=S:raise ValueError('candidate row outside exact support')
     if marker[row,t]!=stamp:
      residual=capacity[oe]-load[row,t]-safety
      if residual<slack:slack=residual
    node=int(head[e]);t+=int(duration[e]);remain-=int(duration[e]);steps+=1
   else:raise ValueError('premature original prefix terminal')
   guard+=1
   if remain<0 or guard>100000:raise ValueError('original prefix action cycle')
  if t!=r+delta:raise ValueError('service time mismatch')
  if steps>max_actions:max_actions=steps
  brow=int(rowmap[bridge])
  if brow<0:raise ValueError('bridge row missing')
  if marker[brow,t]!=stamp:
   residual=capacity[bridge]-load[brow,t]-safety
   if residual<slack:slack=residual
  for p in range(int(suffix_offset[i]),int(suffix_offset[i+1])):
   e=int(suffix_edge[p]);tt=t+int(suffix_time[p]);row=int(rowmap[e])
   if row<0 or tt<0 or tt>=S:raise ValueError('suffix row outside support')
   if marker[row,tt]!=stamp:
    residual=capacity[e]-load[row,tt]-safety
    if residual<slack:slack=residual
  amount=float(mass[j])
  if slack<amount:amount=max(0.,slack)
  if amount<=1e-11:continue
  if amount<float(mass[j])-1e-9:limited+=1
  for p in range(int(base_offset[i]),int(base_offset[i+1])):
   e=int(base_edge[p]);tt=r+int(base_time[p])+delay_from_mask(int(base_mask[p]),w);load[int(rowmap[e]),tt]-=amount
  node=int(origin_by_od[i]);remain=delta;t=r;guard=0
  while remain>0 or node!=bridge_tail:
   choice=int(action[remain,node])
   if choice==254:t+=1;remain-=1
   else:
    e=int(offsets[node])+choice
    if physical[e]:load[int(rowmap[int(original_edge[e])]),t]+=amount
    node=int(head[e]);t+=int(duration[e]);remain-=int(duration[e])
   guard+=1
   if remain<0 or guard>100000:raise ValueError('original update path cycle')
  load[brow,t]+=amount
  for p in range(int(suffix_offset[i]),int(suffix_offset[i+1])):load[int(rowmap[int(suffix_edge[p])]),t+int(suffix_time[p])]+=amount
  swap[j]=amount;accepted+=1;total_mass+=amount;saving+=amount*float(gain[j])
 return accepted,limited,total_mass,saving,max_actions

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(p,x):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def main(case):
 start=time.monotonic();dp=R/'Q_COMMON_FIXED_SERVICE_GREEDY_PRE_RUN_R57.json';d=rd(dp);frozen55p=R/'Q_COMMON_FIXED_SERVICE_PREFIX_PRE_RUN_R55.json';frozen56p=R/'Q_COMMON_FIXED_SERVICE_SUPPORT_PRE_RUN_R56.json';f55=rd(frozen55p);item=next(x for x in f55['cases'] if x['case_id']==case);caseitem=next(x for x in d['cases'] if x['case_id']==case)
 if sha(frozen55p)!=d['R55_design_sha256'] or sha(frozen56p)!=d['R56_design_sha256'] or sha(caseitem['R55_result_path'])!=caseitem['R55_result_sha256'] or sha(caseitem['R56_result_path'])!=caseitem['R56_result_sha256']:raise ValueError('frozen source chain')
 cfg=rd(item['config_path']);source=Path(cfg['source_dir']);r43=rd(item['R43_result_path']);c43=rd(item['R43_independent_certificate_path']);r55=rd(caseitem['R55_result_path']);r56=rd(caseitem['R56_result_path'])
 for k in ('config','R43_result','R43_independent_certificate','AON'):
  pathkey={'config':'config_path','R43_result':'R43_result_path','R43_independent_certificate':'R43_independent_certificate_path','AON':'AON_path'}[k]
  if sha(item[pathkey])!=item[k+'_sha256']:raise ValueError('frozen input '+k)
 if {n:sha(source/n) for n in item['source_hashes']}!=item['source_hashes'] or c43['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or sha(r43['fragment_path'])!=r43['fragment_sha256'] or sha(r55['profile_path'])!=r55['profile_sha256'] or sha(r56['edge_support_path'])!=r56['edge_support_sha256']:raise ValueError('source arrays/certificates')
 net=rows(source/'network.csv');odrows=rows(source/'assignment_od_pce.csv');H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds']);S=int(r56['compact_time_steps']);bridge=int(item['bottleneck_original_edge_index'])
 cfg2,net2,od,nodes,access,u,v,cost,dur,physical,offsets,order,inc,pid,starts,ends,weights,inverse=setup(case,[(bridge,0,1,1.)],1.)
 if cfg2!=cfg or np.max(np.diff(offsets))>=254:raise ValueError('original network/action')
 original=np.empty(len(inverse),np.int32);original[inverse]=np.arange(len(inverse),dtype=np.int32);be=int(inverse[bridge]);tail=int(u[be]);hour=np.asarray([float(x['capacity']) for x in net]);capacity=hour*dt/3600.
 with np.load(item['AON_path'],allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 with np.load(r43['fragment_path'],allow_pickle=False) as z:fod=z['od_index'];fr=z['release_step'];fm=z['mass_pce'];fw=z['wait_steps'];stage=z['stage_original_edge_index']
 with np.load(r55['profile_path'],allow_pickle=False) as z:fi=z['fragment_index'];oi=z['original_OD_index'];release=z['original_release_step'];mass=z['fragment_mass_pce'];service=z['service_step'];delta=z['fixed_service_delay_steps'];base=z['R43_fragment_unit_cost'];candidate=z['exact_prefix_candidate_unit_cost'];gain=z['unit_saving_minutes']
 with np.load(r56['edge_support_path'],allow_pickle=False) as z:all_edges=z['all_changed_original_physical_edge_index']
 if len(q)*T!=cfg['expected_commodity_events'] or len(fi)!=item['expected_selected_fragments'] or np.any(fod[fi]!=oi) or np.any(fr[fi]!=release) or np.max(abs(fm[fi]-mass))>1e-12 or np.max(abs(base-candidate-gain))>1e-7:raise ValueError('full original OD/fragment identity')
 if np.max(abs(q-np.asarray([float(x['volume_pce'])*float(cfg['demand_factor']) for x in odrows])))>1e-9:raise ValueError('source OD conversion')
 sj=list(stage).index(bridge);selected=set(map(int,np.unique(oi)));origin_by_od=np.full(len(q),-1,np.int32)
 for i in selected:origin_by_od[i]=int(access[od[i]['o_zone_id']])
 # Source AON routes and stage masks are rebuilt, with every original OD retained in baseline load.
 users=defaultdict(list);base_off=[0];base_e=[];base_t=[];base_m=[];suffix_off=[0];suffix_e=[];suffix_t=[]
 for i in range(len(q)):
  path=ae[int(off[i]):int(off[i+1])];times=at[int(off[i]):int(off[i+1])];mask=0;prefix=[];bpos=np.flatnonzero(path==bridge);b=int(bpos[0]) if len(bpos)==1 else -1
  if i in selected and len(bpos)!=1:raise ValueError('selected bottleneck route')
  for j,(e0,s0) in enumerate(zip(path,times)):
   e=int(e0);s=int(s0)
   if e in stage:mask|=1<<list(stage).index(e);prefix.append(list(stage).index(e))
   if physical[int(inverse[e])]:
    users[e].append((i,s,tuple(prefix)))
    if i in selected:base_e.append(e);base_t.append(s);base_m.append(mask)
   if i in selected and j>b and physical[int(inverse[e])]:suffix_e.append(e);suffix_t.append(s-int(times[b]))
  base_off.append(len(base_e));suffix_off.append(len(suffix_e))
 base_off=np.asarray(base_off,np.int64);base_e=np.asarray(base_e,np.int32);base_t=np.asarray(base_t,np.int32);base_m=np.asarray(base_m,np.uint32);suffix_off=np.asarray(suffix_off,np.int64);suffix_e=np.asarray(suffix_e,np.int32);suffix_t=np.asarray(suffix_t,np.int32)
 if len(selected)!=item['expected_selected_OD'] or np.any(fw[fi,sj+1:]!=0) or np.any(service!=release+delta):raise ValueError('selected source semantics')
 rowmap=np.full(len(net),-1,np.int32);rowmap[all_edges]=np.arange(len(all_edges),dtype=np.int32)
 if int(len(all_edges))*S*12>2_500_000_000:raise MemoryError('load plus stamp arrays exceed fixed 2.5GiB gate')
 load=np.zeros((len(all_edges),S),np.float64);marker=np.zeros((len(all_edges),S),np.int32);byod={i:np.flatnonzero(fod==i) for i in set(map(int,fod))};hist={}
 def source_hist(i,prefix):
  key=(i,prefix)
  if key not in hist:
   ix=byod[i];delays=np.sum(fw[ix][:,prefix],axis=1,dtype=np.int64) if prefix else 0;when=fr[ix].astype(np.int64)+delays;hist[key]=np.bincount(when,weights=fm[ix],minlength=S)
  return hist[key]
 for e in all_edges:
  a=load[int(rowmap[e])]
  for i,s,prefix in users.get(int(e),[]):
   if i in byod:
    h=source_hist(i,prefix)
    if s<S:a[s:]+=h[:S-s]
   elif s<S:a[s:min(s+T,S)]+=float(q[i])/T
  if np.max(a-capacity[e])>1e-8:raise ValueError('certified original baseline capacity mismatch '+str(int(e)))
 del hist;gc.collect()
 origin_unique=np.asarray([origin_by_od[i] for i in sorted(selected)],np.int32);action,values=exact_prefix_policy(len(nodes),int(item['max_fixed_service_delay_steps']),dt,offsets,order,v,cost,dur,be,tail,origin_unique)
 eligible=np.flatnonzero(gain>1e-9);sequence=eligible[np.lexsort((fi[eligible],release[eligible],oi[eligible],-gain[eligible]))].astype(np.int32);swap=np.zeros(len(fi),np.float64)
 out=R/'runs/q_common_fixed_service_greedy_r57'/case;out.mkdir(parents=True,exist_ok=True)
 if (out/'RESULT.json').exists():raise FileExistsError(out/'RESULT.json')
 accepted=limited=processed=0;totalmass=saving=0.;maxactions=0;history=[]
 for lo in range(0,len(sequence),25000):
  block=sequence[lo:lo+25000];a,b,m,g,mx=greedy_chunk(block,action,origin_by_od,fi,oi,release,delta,mass,gain,fw,base_off,base_e,base_t,base_m,suffix_off,suffix_e,suffix_t,bridge,be,tail,offsets,v,dur,physical,original,rowmap,capacity,load,marker,H,S,float(d['capacity_safety_slack_PCE']),swap)
  processed+=len(block);accepted+=int(a);limited+=int(b);totalmass+=float(m);saving+=float(g);maxactions=max(maxactions,int(mx))
  row={'processed_positive_gain_fragments':processed,'accepted_fragment_swaps':accepted,'achieved_saving_PCE_minutes':saving,'elapsed_seconds':time.monotonic()-start};history.append(row);save(out/'PROGRESS.json',{'status':'RUNNING','design_sha256':sha(dp),'history':history});print(json.dumps({'case_id':case,**row}),flush=True)
 maxexcess=0.;minload=0.
 for e in all_edges:
  a=load[int(rowmap[e])];maxexcess=max(maxexcess,float(np.max(a-capacity[e])));minload=min(minload,float(np.min(a)))
 if maxexcess>1e-8 or minload<-1e-8:raise ValueError('original physical capacity/nonnegativity')
 ap=out/'ACTION_POLICY.npy';np.save(ap,action,allow_pickle=False);vp=out/'SWAP_VARIABLES.npz';np.savez_compressed(vp,fragment_index=fi,original_OD_index=oi,original_release_step=release,fragment_mass_pce=mass,fixed_service_delay_steps=delta,swap_pce=swap,R43_fragment_unit_cost=base,exact_prefix_candidate_unit_cost=candidate)
 upper=float(c43['independent_feasible_primal_upper'])-saving
 result={'schema':'Q_COMMON_FIXED_SERVICE_GREEDY_FULL_ORIGINAL_RESULT_R57','status':'CANDIDATE_FULL_ORIGINAL_FLOW_PENDING_INDEPENDENT_REPLAY','case_id':case,'design_sha256':sha(dp),'R55_result_sha256':sha(caseitem['R55_result_path']),'R56_result_sha256':sha(caseitem['R56_result_path']),'source_hashes':item['source_hashes'],'original_positive_OD':len(q),'original_release_events':len(q)*T,'selected_original_OD':len(selected),'selected_R43_fragments':len(fi),'positive_gain_fragments':len(eligible),'processed_positive_gain_fragments':processed,'positive_fragment_swaps':accepted,'capacity_limited_swaps':limited,'swapped_total_PCE':totalmass,'unconstrained_positive_saving_PCE_minutes':float(r55['unconstrained_positive_saving_PCE_minutes']),'achieved_capacity_feasible_saving_PCE_minutes':saving,'prior_R43_independent_feasible_upper':float(c43['independent_feasible_primal_upper']),'candidate_full_original_objective':upper,'all_changed_original_physical_edges':len(all_edges),'compact_time_steps':S,'load_and_marker_bytes':int(load.nbytes+marker.nbytes),'max_original_capacity_excess_PCE':max(0.,maxexcess),'min_original_row_flow_PCE':minload,'max_selected_prefix_original_actions':maxactions,'action_policy_path':str(ap),'action_policy_sha256':sha(ap),'variable_path':str(vp),'variable_sha256':sha(vp),'wall_seconds':time.monotonic()-start,'scientific_limit':'Same full-original-time greedy kernel for both Q cities; unrestricted global CG pricing/optimality remains open.'}
 (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');save(out/'PROGRESS.json',{'status':'COMPLETE','design_sha256':sha(dp),'history':history,'result_sha256':sha(out/'RESULT.json')})
 print(json.dumps({'case_id':case,'status':result['status'],'accepted':accepted,'gain':saving,'upper':upper,'max_excess':result['max_original_capacity_excess_PCE'],'wall_seconds':result['wall_seconds']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('case_id',choices=['pittsburgh_S2_Q','urbana_S2_Q']);main(p.parse_args().case_id)
