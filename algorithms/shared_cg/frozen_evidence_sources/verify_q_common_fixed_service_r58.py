"""Independent original-CSV replay of the common R57 full-demand fixed-service flow."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,json,time
import numpy as np
from numba import njit
R=Path(__file__).resolve().parent
@njit(cache=False)
def wait_of(mask,wait):
 x=0
 for j in range(len(wait)):
  if mask&(1<<j):x+=int(wait[j])
 return x
@njit(cache=False)
def replay_block(indices,action,origin,frag,OD,release,delay,mass,service,old,candidate,swap,fw,static,baseoff,basee,baset,basemask,sufoff,sufe,suft,tailcost,bridge,bridge_internal,bridge_tail,offsets,sorted_u,head,dur,physical,original,cost,rowmap,load,H,S,dt):
 gain=0.;maxerror=0.;actions=0;physactions=0;count=0
 for z in range(len(indices)):
  j=int(indices[z]);amount=float(swap[j]);i=int(OD[j]);k=int(frag[j]);r=int(release[j]);delta=int(delay[j])
  if amount<=1e-11:continue
  if amount>float(mass[j])+1e-12 or amount<0:raise ValueError('original fragment mass')
  base=float(static[i])
  for h in range(fw.shape[1]):base+=float(fw[k,h])*dt/60.
  if abs(base-float(old[j]))>1e-7:raise ValueError('R43 source fragment cost')
  for p in range(int(baseoff[i]),int(baseoff[i+1])):
   e=int(basee[p]);t=r+int(baset[p])+wait_of(int(basemask[p]),fw[k]);row=int(rowmap[e])
   if row<0 or t<0 or t>=S:raise ValueError('original source row')
   load[row,t]-=amount
  node=int(origin[i]);remain=delta;t=r;pcost=0.;guard=0
  while remain>0 or node!=bridge_tail:
   choice=int(action[remain,node])
   if choice==254:t+=1;remain-=1;pcost+=dt/60.
   elif choice<254:
    e=int(offsets[node])+choice
    if e>=offsets[node+1] or e==bridge_internal or int(sorted_u[e])!=node:raise ValueError('invalid original prefix arc')
    oe=int(original[e]);pcost+=float(cost[oe])
    if physical[e]:
     row=int(rowmap[oe])
     if row<0 or t<0 or t>=S:raise ValueError('candidate original physical row')
     load[row,t]+=amount;physactions+=1
    node=int(head[e]);t+=int(dur[e]);remain-=int(dur[e]);actions+=1
   else:raise ValueError('premature original terminal')
   guard+=1
   if remain<0 or guard>100000:raise ValueError('invalid original time path')
  if t!=r+delta or t!=int(service[j]):raise ValueError('certified service time changed')
  brow=int(rowmap[bridge])
  if brow<0 or t>=S:raise ValueError('bridge capacity row')
  load[brow,t]+=amount;physactions+=1
  for p in range(int(sufoff[i]),int(sufoff[i+1])):
   e=int(sufe[p]);tt=t+int(suft[p]);row=int(rowmap[e])
   if row<0 or tt>=S:raise ValueError('suffix original capacity row')
   load[row,tt]+=amount;physactions+=1
  truecost=pcost+float(tailcost[i]);err=abs(truecost-float(candidate[j]));maxerror=max(maxerror,err)
  if err>1e-7:raise ValueError('original candidate true cost')
  gain+=amount*(base-truecost);count+=1
 return gain,maxerror,actions,physactions,count

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while True:
   b=f.read(8*1024*1024)
   if not b:break
   h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main(case):
 start=time.monotonic();dp=R/'Q_COMMON_FIXED_SERVICE_GREEDY_PRE_RUN_R57.json';d=rd(dp);d55p=R/'Q_COMMON_FIXED_SERVICE_PREFIX_PRE_RUN_R55.json';d56p=R/'Q_COMMON_FIXED_SERVICE_SUPPORT_PRE_RUN_R56.json';d55=rd(d55p);item=next(x for x in d55['cases'] if x['case_id']==case);di=next(x for x in d['cases'] if x['case_id']==case)
 if sha(d55p)!=d['R55_design_sha256'] or sha(d56p)!=d['R56_design_sha256'] or sha(di['R55_result_path'])!=di['R55_result_sha256'] or sha(di['R56_result_path'])!=di['R56_result_sha256']:raise ValueError('frozen design/evidence')
 cfg=rd(item['config_path']);src=Path(cfg['source_dir']);r43=rd(item['R43_result_path']);c43=rd(item['R43_independent_certificate_path']);r55=rd(di['R55_result_path']);r56=rd(di['R56_result_path']);rp=R/'runs/q_common_fixed_service_greedy_r57'/case/'RESULT.json';r57=rd(rp)
 if r57['design_sha256']!=sha(dp) or r57['R55_result_sha256']!=sha(di['R55_result_path']) or r57['R56_result_sha256']!=sha(di['R56_result_path']) or c43['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE':raise ValueError('producer/base identity')
 for k in ('config','R43_result','R43_independent_certificate','AON'):
  name={'config':'config_path','R43_result':'R43_result_path','R43_independent_certificate':'R43_independent_certificate_path','AON':'AON_path'}[k]
  if sha(item[name])!=item[k+'_sha256']:raise ValueError('source hash '+k)
 if {n:sha(src/n) for n in item['source_hashes']}!=item['source_hashes']:raise ValueError('original CSV')
 for path,ref in ((r43['fragment_path'],r43['fragment_sha256']),(r55['profile_path'],r55['profile_sha256']),(r56['edge_support_path'],r56['edge_support_sha256']),(r57['action_policy_path'],r57['action_policy_sha256']),(r57['variable_path'],r57['variable_sha256'])):
  if sha(path)!=ref:raise ValueError('array hash '+path)
 net=rows(src/'network.csv');odrows=rows(src/'assignment_od_pce.csv');acc={x['zone_id']:x['node_id'] for x in rows(src/'access.csv')};nodes=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(nodes)};u0=np.asarray([ix[x['from_node_id']] for x in net],np.int32);v0=np.asarray([ix[x['to_node_id']] for x in net],np.int32);cost=np.asarray([float(x['vdf_fftt']) for x in net]);physical0=np.asarray([x[cfg['physical_field']]==cfg['physical_value'] for x in net],bool);dt=float(cfg['dt_seconds']);H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);S=int(r56['compact_time_steps']);duration0=np.where(physical0,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0);capacity=np.asarray([float(x['capacity'])*dt/3600 for x in net])
 perm=np.argsort(u0,kind='stable');sorted_u=u0[perm];head=v0[perm];dur=duration0[perm];physical=physical0[perm];offsets=np.r_[0,np.cumsum(np.bincount(sorted_u,minlength=len(nodes)))].astype(np.int32);original=perm.astype(np.int32);bridge=int(item['bottleneck_original_edge_index']);bridge_internal=int(np.flatnonzero(perm==bridge)[0]);bridge_tail=int(u0[bridge]);action=np.load(r57['action_policy_path'],mmap_mode='r',allow_pickle=False)
 if action.shape!=(item['max_fixed_service_delay_steps']+1,len(nodes)) or action.dtype!=np.uint8:raise ValueError('saved original action policy dimensions')
 with np.load(item['AON_path'],allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 with np.load(r43['fragment_path'],allow_pickle=False) as z:fod=z['od_index'];fr=z['release_step'];fm=z['mass_pce'];fw=z['wait_steps'];stage=z['stage_original_edge_index']
 with np.load(r55['profile_path'],allow_pickle=False) as z:fi=z['fragment_index'];oi=z['original_OD_index'];release=z['original_release_step'];mass=z['fragment_mass_pce'];service=z['service_step'];delay=z['fixed_service_delay_steps'];old=z['R43_fragment_unit_cost'];candidate=z['exact_prefix_candidate_unit_cost'];gain=z['unit_saving_minutes']
 with np.load(r57['variable_path'],allow_pickle=False) as z:vfi=z['fragment_index'];vi=z['original_OD_index'];vr=z['original_release_step'];vm=z['fragment_mass_pce'];vd=z['fixed_service_delay_steps'];swap=z['swap_pce'];vo=z['R43_fragment_unit_cost'];vc=z['exact_prefix_candidate_unit_cost']
 with np.load(r56['edge_support_path'],allow_pickle=False) as z:changed=z['all_changed_original_physical_edge_index']
 if len(q)*T!=cfg['expected_commodity_events'] or len(fi)!=item['expected_selected_fragments'] or not np.array_equal(fi,vfi) or not np.array_equal(oi,vi) or not np.array_equal(release,vr) or not np.array_equal(delay,vd) or np.max(abs(vm-mass))>1e-12 or np.max(abs(vo-old))>1e-7 or np.max(abs(vc-candidate))>1e-7:raise ValueError('all original fragment variables')
 if np.max(abs(q-np.asarray([float(x['volume_pce'])*float(cfg['demand_factor']) for x in odrows])))>1e-9 or np.any(fod[fi]!=oi) or np.any(fr[fi]!=release) or np.any(swap<-1e-12) or np.any(swap-mass>1e-12):raise ValueError('original source OD/fragment conversion')
 stageix={int(e):j for j,e in enumerate(stage)};sj=stageix[bridge];selected=set(map(int,np.unique(oi)));origin=np.full(len(q),-1,np.int32);baseoff=[0];basee=[];baset=[];basemask=[];sufoff=[0];sufe=[];suft=[];tailcost=np.zeros(len(q));users=defaultdict(list);byod={i:np.flatnonzero(fod==i) for i in set(map(int,fod))};maxmassres=0.
 for i,row in enumerate(odrows):
  lo=int(off[i]);hi=int(off[i+1]);path=ae[lo:hi];times=at[lo:hi];node=ix[acc[row['o_zone_id']]];t=0;mask=0;prefix=[];costsum=0.;bk=np.flatnonzero(path==bridge);b=int(bk[0]) if len(bk)==1 else -1
  if i in selected:
   if len(bk)!=1:raise ValueError('selected source bottleneck')
   origin[i]=node;tailcost[i]=float(np.sum(cost[path[b:]]));idx=byod[i];release_mass=np.bincount(fr[idx],weights=fm[idx],minlength=T);maxmassres=max(maxmassres,float(np.max(abs(release_mass-q[i]/T))))
  for j,(e0,s0) in enumerate(zip(path,times)):
   e=int(e0);s=int(s0)
   if u0[e]!=node or s!=t:raise ValueError('AON original topology/time')
   if e in stageix:mask|=1<<stageix[e];prefix.append(stageix[e])
   if physical0[e]:
    users[e].append((i,s,tuple(prefix)))
    if i in selected:basee.append(e);baset.append(s);basemask.append(mask)
    if i in selected and j>b:sufe.append(e);suft.append(s-int(times[b]))
   costsum+=cost[e];node=int(v0[e]);t+=int(duration0[e])
  if node!=ix[acc[row['d_zone_id']]] or t+T-1>H or abs(costsum-static[i])>1e-7:raise ValueError('source AON terminal/shortest cost')
  baseoff.append(len(basee));sufoff.append(len(sufe))
 if maxmassres>1e-8 or np.any(fw[fi,sj+1:]!=0):raise ValueError('selected original release/wait semantics')
 baseoff=np.asarray(baseoff,np.int64);basee=np.asarray(basee,np.int32);baset=np.asarray(baset,np.int32);basemask=np.asarray(basemask,np.uint32);sufoff=np.asarray(sufoff,np.int64);sufe=np.asarray(sufe,np.int32);suft=np.asarray(suft,np.int32)
 rowmap=np.full(len(net),-1,np.int32);rowmap[changed]=np.arange(len(changed),dtype=np.int32);load=np.zeros((len(changed),S),np.float64);hist={}
 def hload(i,prefix):
  key=(i,prefix)
  if key not in hist:
   idx=byod[i];shifts=np.sum(fw[idx][:,prefix],axis=1,dtype=np.int64) if prefix else 0;hist[key]=np.bincount(fr[idx].astype(np.int64)+shifts,weights=fm[idx],minlength=S)
  return hist[key]
 for e in changed:
  a=load[int(rowmap[e])]
  for i,s,prefix in users.get(int(e),[]):
   if i in byod:
    h=hload(i,prefix)
    if s<S:a[s:]+=h[:S-s]
   elif s<S:a[s:min(s+T,S)]+=float(q[i])/T
  if np.max(a-capacity[e])>1e-8:raise ValueError('original R43 base capacity')
 positive=np.flatnonzero(swap>1e-11).astype(np.int32);totalgain=0.;maxerror=0.;actions=physicalactions=checked=0
 for lo in range(0,len(positive),25000):
  g,err,act,pact,num=replay_block(positive[lo:lo+25000],action,origin,fi,oi,release,delay,mass,service,old,candidate,swap,fw,static,baseoff,basee,baset,basemask,sufoff,sufe,suft,tailcost,bridge,bridge_internal,bridge_tail,offsets,sorted_u,head,dur,physical,original,cost,rowmap,load,H,S,dt)
  totalgain+=g;maxerror=max(maxerror,err);actions+=int(act);physicalactions+=int(pact);checked+=int(num)
  print(json.dumps({'case_id':case,'independent_checked_swaps':checked,'elapsed_seconds':time.monotonic()-start}),flush=True)
 maxexcess=0.;minflow=0.;usedrows=0
 for e in changed:
  a=load[int(rowmap[e])];maxexcess=max(maxexcess,float(np.max(a-capacity[e])));minflow=min(minflow,float(np.min(a)));usedrows+=int(np.count_nonzero(a>1e-15))
 if maxexcess>1e-8 or minflow<-1e-8 or checked!=r57['positive_fragment_swaps']:raise ValueError('final original physical capacity/flow count')
 prior=float(np.dot(q,static))+float(np.dot(fm,np.sum(fw,axis=1,dtype=np.int64)))*dt/60.;upper=prior-totalgain
 if abs(prior-c43['independent_feasible_primal_upper'])>1e-6 or abs(upper-r57['candidate_full_original_objective'])>1e-6 or abs(totalgain-r57['achieved_capacity_feasible_saving_PCE_minutes'])>1e-6:raise ValueError('independent original objective')
 cert={'schema':'Q_COMMON_FIXED_SERVICE_INDEPENDENT_FULL_ORIGINAL_CERTIFICATE_R58','status':'PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE','case_id':case,'design_sha256':sha(dp),'producer_result_sha256':sha(rp),'source_hashes':item['source_hashes'],'original_positive_OD':len(q),'original_release_events':len(q)*T,'selected_original_OD':len(selected),'selected_R43_fragments':len(fi),'positive_fragment_swaps_independently_replayed':checked,'original_prefix_arc_actions_independently_replayed':actions,'original_physical_actions_independently_replayed':physicalactions,'max_candidate_original_path_cost_error_minutes':maxerror,'max_selected_per_release_mass_residual_PCE':maxmassres,'all_changed_original_capacity_edges_checked':len(changed),'all_changed_original_capacity_rows_used':usedrows,'max_original_capacity_excess_PCE':max(0.,maxexcess),'min_original_row_flow_PCE':minflow,'R43_independent_full_original_feasible_upper':prior,'independent_full_original_feasible_upper':upper,'independent_improvement_PCE_minutes':totalgain,'wall_seconds':time.monotonic()-start,'scientific_limit':'Independent full-original-demand primal replay on one fixed bottleneck service schedule; unrestricted global CG/dual optimum still open.'}
 out=R/'runs/q_common_fixed_service_greedy_r57'/case/'INDEPENDENT_FULL_ORIGINAL_CERTIFICATE_R58.json'
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8');print(json.dumps({'case_id':case,'status':cert['status'],'upper':upper,'improvement':totalgain,'max_excess':cert['max_original_capacity_excess_PCE'],'wall_seconds':cert['wall_seconds']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('case_id',choices=['pittsburgh_S2_Q','urbana_S2_Q']);main(p.parse_args().case_id)
