"""Independent original-source and all-changed-resource replay of R53 all-fragment flow."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,json,time
import numpy as np
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ordering-index',type=int,required=True);args=ap.parse_args()
 devp=R/'DEV34_F_BLOCK_LP_NUMERIC_REVISION_PRE_RUN.json';dev=rd(devp)
 if not 0<=args.ordering_index<len(dev['ordering_grid']):raise ValueError('ordering outside frozen grid')
 if sha(R/dev['incumbent_certificate'])!=dev['incumbent_certificate_sha256'] or sha(R/dev['incumbent_result'])!=dev['incumbent_result_sha256'] or sha(R/dev['incumbent_swap_array'])!=dev['incumbent_swap_array_sha256']:raise ValueError('frozen incumbent drift')
 if sha(R/dev['parent_design'])!=dev['parent_design_sha256'] or sha(R/dev['measured_failure_receipt'])!=dev['measured_failure_sha256'] or sha(R/dev['independently_valid_partial_certificate'])!=dev['partial_certificate_sha256']:raise ValueError('numeric revision source drift')
 for name,item in dev['frozen_inputs'].items():
  if sha(R/item['relative_path'])!=item['sha256']:raise ValueError('frozen accepted source drift '+name)
 start=time.monotonic();dp=R/'Q_F_ALL_BRIDGE_FRAGMENTS_EXACT_PREFIX_PRE_RUN_R51.json';d=rd(dp)
 for k in ('source_config','R43_result','R43_independent_certificate','original_AON'):
  if sha(d[k])!=d[k+'_sha256']:raise ValueError('frozen evidence '+k)
 cfg=rd(d['source_config']);src=Path(cfg['source_dir'])
 if {n:sha(src/n) for n in d['source_hashes']}!=d['source_hashes']:raise ValueError('original CSV hash')
 r43=rd(d['R43_result']);c43=rd(d['R43_independent_certificate']);p51=R/'runs/q_f_all_bridge_exact_prefix_r51/PROFILE_RESULT.json';r51=rd(p51);p52=R/'runs/q_f_all_bridge_exact_prefix_r52/RESULT.json';r52=rd(p52);rp=R/f'runs/dev34_f_block_lp_numeric_revision/ORDER_{args.ordering_index:02d}/RESULT.json';r53=rd(rp)
 if c43['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or r51['design_sha256']!=sha(dp) or r52['design_sha256']!=sha(dp) or r53['design_sha256']!=sha(dp) or r53['dev34_design_sha256']!=sha(devp) or r53['ordering_index']!=args.ordering_index or r53['ordering']!=dev['ordering_grid'][args.ordering_index] or r53['R51_profile_result_sha256']!=sha(p51) or r53['R52_pattern_result_sha256']!=sha(p52):raise ValueError('result chain')
 for path,expected in ((r43['fragment_path'],r43['fragment_sha256']),(r51['profile_array_path'],r51['profile_array_sha256']),(r52['pattern_array_path'],r52['pattern_array_sha256']),(r53['variable_path'],r53['variable_sha256'])):
  if sha(path)!=expected:raise ValueError('array hash '+path)
 net=rows(src/'network.csv');odrows=rows(src/'assignment_od_pce.csv');acc={x['zone_id']:x['node_id'] for x in rows(src/'access.csv')};H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds']);S=int(r53['compact_capacity_time_steps'])
 node_names=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});nodeid={x:i for i,x in enumerate(node_names)};u=np.asarray([nodeid[x['from_node_id']] for x in net],np.int32);v=np.asarray([nodeid[x['to_node_id']] for x in net],np.int32)
 phys=np.asarray([x[cfg['physical_field']]==cfg['physical_value'] for x in net],bool);cost=np.asarray([float(x['vdf_fftt']) for x in net]);duration=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0);cap=np.asarray([float(x['capacity'])*dt/3600 for x in net])
 with np.load(d['original_AON'],allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 with np.load(r43['fragment_path'],allow_pickle=False) as z:fod=z['od_index'];fr=z['release_step'];fm=z['mass_pce'];fw=z['wait_steps'];stage=z['stage_original_edge_index']
 with np.load(r51['profile_array_path'],allow_pickle=False) as z:fi=z['fragment_index'];oi=z['original_OD_index'];release=z['original_release_step'];mass=z['fragment_mass_pce'];service=z['bridge_service_step'];delt=z['fixed_bridge_delay_steps'];old=z['R43_fragment_unit_cost'];candidate=z['exact_prefix_candidate_unit_cost'];gain=z['unit_saving_minutes']
 with np.load(r52['pattern_array_path'],allow_pickle=False) as z:pi=z['original_OD_index'];pd=z['fixed_bridge_delay_steps'];eoff=z['original_edge_offset'];ee=z['original_edge_index'];et=z['original_entry_offset_steps'];poff=z['physical_edge_offset'];pe=z['physical_original_edge_index'];pt=z['physical_entry_offset_steps'];punit=z['candidate_unit_cost'];maxrelease=z['maximum_original_release_step']
 with np.load(r53['variable_path'],allow_pickle=False) as z:vfi=z['fragment_index'];vi=z['original_OD_index'];vr=z['original_release_step'];pattern=z['pattern_id'];y=z['swap_pce'];vm=z['fragment_mass_pce'];vo=z['R43_fragment_unit_cost'];vn=z['exact_candidate_unit_cost']
 if len(q)!=418 or len(q)*T!=6019200 or len(fi)!=305053 or len(pi)!=57390 or not np.array_equal(fi,vfi) or not np.array_equal(oi,vi) or not np.array_equal(release,vr):raise ValueError('full original demand/fragment identity')
 if np.max(abs(q-np.asarray([float(x['volume_pce']) for x in odrows])))>1e-9 or np.max(abs(fm[fi]-mass))>1e-12 or np.max(abs(vm-mass))>1e-12 or np.max(abs(vo-old))>1e-7 or np.max(abs(vn-candidate))>1e-7 or np.max(abs(old-candidate-gain))>1e-7:raise ValueError('mass/cost profile')
 if np.any(fod[fi]!=oi) or np.any(fr[fi]!=release) or np.any(y<-1e-12) or np.any(y-mass>1e-12):raise ValueError('fragment unit mapping')
 selected=set(map(int,np.unique(oi)));bridge=int(d['bridge_original_edge_index']);stageindex={int(e):j for j,e in enumerate(stage)};sj=stageindex[bridge]
 if len(selected)!=20 or np.any(fw[fi,sj+1:]!=0):raise ValueError('selected bridge component')
 # Rebuild every original AON path from the source CSV and independently verify selected per-release mass.
 users=defaultdict(list);basephysical={};byod={i:np.flatnonzero(fod==i) for i in set(map(int,fod))};maxmassres=0.
 for i,row in enumerate(odrows):
  lo=int(off[i]);hi=int(off[i+1]);path=ae[lo:hi];times=at[lo:hi];node=nodeid[acc[row['o_zone_id']]];t=0;prefix=[];costsum=0.;base_e=[];base_t=[];after=[]
  for e0,s0 in zip(path,times):
   e=int(e0);s=int(s0)
   if s!=t or u[e]!=node:raise ValueError('original AON source mapping')
   if e in stageindex:prefix.append(stageindex[e])
   if phys[e]:
    users[e].append((i,s,tuple(prefix)))
    if i in selected:base_e.append(e);base_t.append(s);after.append(int(sj in prefix))
   costsum+=cost[e];node=int(v[e]);t+=int(duration[e])
  if node!=nodeid[acc[row['d_zone_id']]] or T-1+t>H or abs(costsum-static[i])>1e-7:raise ValueError('original AON destination/cost')
  if i in selected:
   basephysical[i]=(np.asarray(base_e,np.int32),np.asarray(base_t,np.int32),np.asarray(after,np.int8));ix=byod[i];total=np.bincount(fr[ix],weights=fm[ix],minlength=T);maxmassres=max(maxmassres,float(np.max(abs(total-q[i]/T))))
 if maxmassres>1e-8:raise ValueError('original release conservation')
 # Independently replay all canonical original paths, including zero-time connectors and cycles.
 maxpatherror=0.;totalarc=0;totalphysical=0
 for k in range(len(pi)):
  lo=int(eoff[k]);hi=int(eoff[k+1]);path=ee[lo:hi];times=et[lo:hi];plo=int(poff[k]);phi=int(poff[k+1]);pedge=pe[plo:phi];ptime=pt[plo:phi];i=int(pi[k]);delta=int(pd[k])
  if not len(path) or not np.array_equal(pedge,path[phys[path]]) or not np.array_equal(ptime,times[phys[path]]):raise ValueError('physical pattern mapping')
  if u[int(path[0])]!=nodeid[acc[odrows[i]['o_zone_id']]] or v[int(path[-1])]!=nodeid[acc[odrows[i]['d_zone_id']]] or np.any(u[path[1:]]!=v[path[:-1]]):raise ValueError('pattern original node continuity')
  waits=np.empty(len(path),np.int64);waits[0]=int(times[0]);waits[1:]=times[1:].astype(np.int64)-times[:-1].astype(np.int64)-duration[path[:-1]].astype(np.int64)
  if np.any(waits<0) or int(times[-1])+int(duration[int(path[-1])])+int(maxrelease[k])>H:raise ValueError('pattern original time/horizon')
  hits=np.flatnonzero(path==bridge)
  if len(hits)!=1 or int(times[hits[0]])!=delta:raise ValueError('pattern bridge service')
  c=float(np.sum(cost[path]))+float(np.sum(waits))*dt/60.;err=abs(c-float(punit[k]));maxpatherror=max(maxpatherror,err)
  if err>1e-7:raise ValueError('pattern true original path cost')
  totalarc+=len(path);totalphysical+=len(pedge)
 if totalarc!=r52['all_original_arc_actions'] or totalphysical!=r52['all_original_physical_arc_actions']:raise ValueError('pattern action count')
 positive=np.flatnonzero(y>1e-11);pospattern=pattern[positive]
 if len(positive)!=r53['positive_fragment_swaps'] or np.any(pospattern<0) or np.any(pi[pospattern]!=oi[positive]) or np.any(pd[pospattern]!=delt[positive]) or np.max(abs(punit[pospattern]-candidate[positive]))>1e-7 or np.any(service[positive]!=release[positive]+delt[positive]):raise ValueError('swap pattern identity')
 # Rebuild original R43 load independently for all candidate or source rows that any swap can change.
 all_edges=np.unique(np.concatenate((pe,np.concatenate([x[0] for x in basephysical.values()]))));rowmap=np.full(len(net),-1,np.int32);rowmap[all_edges]=np.arange(len(all_edges),dtype=np.int32)
 if np.any(~phys[all_edges]):raise ValueError('connector in capacity support')
 load=np.zeros((len(all_edges),S),np.float64);hist={}
 def source_hist(i,prefix):
  key=(i,prefix)
  if key not in hist:
   ix=byod[i];delay=np.sum(fw[ix][:,prefix],axis=1,dtype=np.int64) if prefix else 0;when=fr[ix].astype(np.int64)+delay
   if np.any(when>=S):raise ValueError('source event outside compact horizon')
   hist[key]=np.bincount(when,weights=fm[ix],minlength=S)
  return hist[key]
 for e in all_edges:
  a=load[int(rowmap[e])]
  for i,s,prefix in users.get(int(e),[]):
   if i in byod:
    h=source_hist(i,prefix)
    if s<S:a[s:]+=h[:S-s]
   elif s<S:a[s:min(s+T,S)]+=float(q[i])/T
  if np.max(a-cap[e])>1e-8:raise ValueError('R43 source load exceeds capacity')
 for j in positive:
  amount=float(y[j]);i=int(oi[j]);r=int(release[j]);k=int(fi[j]);p=int(pattern[j]);plo=int(poff[p]);phi=int(poff[p+1]);ce=pe[plo:phi];ct=r+pt[plo:phi]
  be,bt0,after=basephysical[i];bt=r+bt0+after*int(fw[k,sj])
  if np.any(ct>=S) or np.any(bt>=S):raise ValueError('changed physical row outside compact support')
  np.add.at(load,(rowmap[ce],ct),amount);np.add.at(load,(rowmap[be],bt),-amount)
 maxexcess=0.;minload=0.;usedrows=0;worst=None
 for e in all_edges:
  a=load[int(rowmap[e])];ex=float(np.max(a-cap[e]));mn=float(np.min(a));usedrows+=int(np.count_nonzero(a>1e-15))
  if ex>maxexcess:maxexcess=ex;worst=[int(e),int(np.argmax(a-cap[e]))]
  minload=min(minload,mn)
 if maxexcess>1e-8 or minload<-1e-8:raise ValueError('original physical capacity/nonnegativity '+str(worst))
 prior=float(np.dot(q,static))+float(np.dot(fm,np.sum(fw,axis=1,dtype=np.int64)))*dt/60.;improve=float(np.dot(y,old-candidate));full=prior-improve
 if abs(prior-c43['independent_feasible_primal_upper'])>1e-6 or abs(full-r53['candidate_full_original_objective'])>1e-6:raise ValueError('independent full objective')
 cert={'schema':'SHARED_CG_DEV34_F_INDEPENDENT_NUMERIC_GUARDED_BLOCK_LP_CERT_R1','dev34_design_sha256':sha(devp),'ordering_index':args.ordering_index,'ordering':dev['ordering_grid'][args.ordering_index],'status':'PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE','design_sha256':sha(dp),'producer_result_sha256':sha(rp),'R43_independent_certificate_sha256':sha(d['R43_independent_certificate']),'original_source_hashes':d['source_hashes'],'original_positive_OD':len(q),'original_release_events':len(q)*T,'selected_bridge_OD':len(selected),'all_selected_R43_fragments':len(fi),'all_canonical_original_paths_independently_checked':len(pi),'all_pattern_original_arc_actions_checked':totalarc,'positive_original_fragment_swaps':len(positive),'max_selected_per_release_mass_residual_PCE':maxmassres,'max_original_pattern_cost_error_minutes':maxpatherror,'all_changed_original_capacity_edges_checked':len(all_edges),'all_changed_original_capacity_rows_used':usedrows,'max_original_capacity_excess_PCE':max(0.,maxexcess),'min_original_row_flow_PCE':minload,'R43_independent_feasible_upper':prior,'independent_full_original_feasible_upper':full,'independent_improvement_PCE_minutes':improve,'wall_seconds':time.monotonic()-start,'scientific_limit':'All-original-release primal flow with exact original physical entry rows, fixed bridge service schedule; no full-graph dual closure or 16/16 optimum claim.'}
 out=R/f'runs/dev34_f_block_lp_numeric_revision/ORDER_{args.ordering_index:02d}/INDEPENDENT_CERT.json'
 if out.exists():raise FileExistsError(out)
 out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':cert['status'],'upper':full,'improvement':improve,'capacity_excess':cert['max_original_capacity_excess_PCE'],'wall_seconds':cert['wall_seconds']}),flush=True)
if __name__=='__main__':main()


