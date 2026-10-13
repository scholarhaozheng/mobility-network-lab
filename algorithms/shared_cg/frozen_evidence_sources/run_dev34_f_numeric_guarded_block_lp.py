"""Original-demand fixed-path block-coordinate LP with exact shared capacities."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(p,x):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ordering-index',type=int,required=True);args=ap.parse_args()
 devp=R/'DEV34_F_BLOCK_LP_NUMERIC_REVISION_PRE_RUN.json';dev=rd(devp)
 if not 0<=args.ordering_index<len(dev['ordering_grid']):raise ValueError('ordering outside frozen grid')
 if sha(R/dev['parent_design'])!=dev['parent_design_sha256'] or sha(R/dev['measured_failure_receipt'])!=dev['measured_failure_sha256'] or sha(R/dev['independently_valid_partial_certificate'])!=dev['partial_certificate_sha256']:raise ValueError('measured numeric-revision evidence drift')
 for name,item in dev['frozen_inputs'].items():
  if sha(R/item['relative_path'])!=item['sha256']:raise ValueError('frozen accepted source drift '+name)
 start=time.monotonic();dp=R/'Q_F_ALL_BRIDGE_FRAGMENTS_EXACT_PREFIX_PRE_RUN_R51.json';d=rd(dp);cfg=rd(d['source_config']);source=Path(cfg['source_dir'])
 for k in ('source_config','R43_result','R43_independent_certificate','original_AON'):
  if sha(d[k])!=d[k+'_sha256']:raise ValueError('frozen source '+k)
 if {n:sha(source/n) for n in d['source_hashes']}!=d['source_hashes']:raise ValueError('original CSV drift')
 r43=rd(d['R43_result']);c43=rd(d['R43_independent_certificate']);p51=R/'runs/q_f_all_bridge_exact_prefix_r51/PROFILE_RESULT.json';r51=rd(p51);p52=R/'runs/q_f_all_bridge_exact_prefix_r52/RESULT.json';r52=rd(p52)
 if c43['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or r51['design_sha256']!=sha(dp) or r52['design_sha256']!=sha(dp) or r52['profile_result_sha256']!=sha(p51):raise ValueError('source results')
 if sha(r51['profile_array_path'])!=r51['profile_array_sha256'] or sha(r52['pattern_array_path'])!=r52['pattern_array_sha256'] or sha(r43['fragment_path'])!=r43['fragment_sha256']:raise ValueError('arrays')
 net=rows(source/'network.csv');odrows=rows(source/'assignment_od_pce.csv');H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
 phys=np.asarray([x[cfg['physical_field']]==cfg['physical_value'] for x in net],bool);cap=np.asarray([float(x['capacity'])*dt/3600 for x in net]);free=np.asarray([float(x['vdf_fftt']) for x in net]);duration=np.where(phys,np.maximum(1,np.ceil(free*60/dt-1e-12).astype(np.int32)),0)
 with np.load(d['original_AON'],allow_pickle=False) as z:off=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 with np.load(r43['fragment_path'],allow_pickle=False) as z:fod=z['od_index'];fr=z['release_step'];fm=z['mass_pce'];fw=z['wait_steps'];stage=z['stage_original_edge_index']
 with np.load(r51['profile_array_path'],allow_pickle=False) as z:fi=z['fragment_index'];oi=z['original_OD_index'];release=z['original_release_step'];mass=z['fragment_mass_pce'];service=z['bridge_service_step'];delt=z['fixed_bridge_delay_steps'];old=z['R43_fragment_unit_cost'];candidate=z['exact_prefix_candidate_unit_cost'];gain=z['unit_saving_minutes']
 with np.load(r52['pattern_array_path'],allow_pickle=False) as z:pi=z['original_OD_index'];pd=z['fixed_bridge_delay_steps'];pof=z['physical_edge_offset'];pe=z['physical_original_edge_index'];pt=z['physical_entry_offset_steps'];punit=z['candidate_unit_cost']
 if len(q)!=418 or len(q)*T!=6019200 or len(fi)!=d['expected_selected_fragments'] or len(pi)!=r52['unique_patterns']:raise ValueError('full source demand')
 if np.any(fod[fi]!=oi) or np.any(fr[fi]!=release) or np.max(abs(fm[fi]-mass))>1e-12:raise ValueError('fragment profile identity')
 # The candidate is cheaper by old-candidate; the preceding algebra is deliberately checked below.
 if np.max(abs(old-candidate-gain))>1e-7:raise ValueError('unit gain')
 bridge=int(d['bridge_original_edge_index']);sj=list(stage).index(bridge);selected_od=set(map(int,np.unique(oi)))
 base_edge={};base_offset={};base_after={};users=defaultdict(list)
 for i in range(len(q)):
  epath=ae[int(off[i]):int(off[i+1])];times=at[int(off[i]):int(off[i+1])];prefix=[];bedge=[];boffset=[];bafter=[]
  for e0,s0 in zip(epath,times):
   e=int(e0);s=int(s0)
   if e in set(map(int,stage)):prefix.append(list(stage).index(e))
   if phys[e]:
    users[e].append((i,s,tuple(prefix)))
    if i in selected_od:bedge.append(e);boffset.append(s);bafter.append(int(sj in prefix))
  if i in selected_od:base_edge[i]=np.asarray(bedge,np.int32);base_offset[i]=np.asarray(boffset,np.int32);base_after[i]=np.asarray(bafter,np.int8)
 if len(base_edge)!=d['expected_selected_OD']:raise ValueError('selected base OD')
 maxbase=0
 for i in selected_od:
  idx=np.flatnonzero(fod==i);b=int(np.max(fr[idx]+int(np.max(base_offset[i]))+fw[idx,sj]));maxbase=max(maxbase,b)
 S=max(int(r52['maximum_candidate_original_entry_step']),maxbase)+1
 if S>H:raise ValueError('original horizon')
 all_edges=np.unique(np.concatenate((pe,np.concatenate([base_edge[i] for i in sorted(selected_od)]))))
 if np.any(~phys[all_edges]):raise ValueError('nonphysical pattern row')
 expected_bytes=int(len(all_edges))*S*8
 if expected_bytes>int(dev['compact_capacity_array_gate_bytes']):raise MemoryError('exact full source compact capacity array exceeds 2GiB memory gate: '+str(expected_bytes))
 rowmap=np.full(len(net),-1,np.int32);rowmap[all_edges]=np.arange(len(all_edges),dtype=np.int32);load=np.zeros((len(all_edges),S),np.float64);initialized=np.zeros(len(all_edges),bool)
 byod={i:np.flatnonzero(fod==i) for i in set(map(int,fod))};histcache={}
 def history(i,prefix):
  key=(int(i),prefix)
  if key not in histcache:
   ix=byod[i];delay=np.sum(fw[ix][:,prefix],axis=1,dtype=np.int64) if prefix else 0;when=fr[ix].astype(np.int64)+delay
   if np.any(when>=S):raise ValueError('R43 event before edge offset outside compact horizon')
   histcache[key]=np.bincount(when,weights=fm[ix],minlength=S)
  return histcache[key]
 def init_edges(original_edges):
  for raw in np.unique(original_edges):
   e=int(raw);row=int(rowmap[e])
   if row<0:raise ValueError('missing compact capacity row')
   if initialized[row]:continue
   a=load[row]
   for i,s,prefix in users.get(e,[]):
    if i in byod:
     h=history(i,prefix)
     if s<S:a[s:]+=h[:S-s]
    else:
     if s<S:a[s:min(s+T,S)]+=float(q[i])/T
   if np.max(a-cap[e])>1e-8:raise ValueError('R43 source capacity mismatch '+str(e))
   initialized[row]=True
 maxkey=int(d['maximum_fixed_bridge_delay_steps'])+1;lookup=np.full(len(q)*maxkey,-1,np.int32);lookup[pi*maxkey+pd]=np.arange(len(pi),dtype=np.int32)
 eligible=np.flatnonzero(gain>1e-9)
 if len(fi)!=int(dev['restricted_candidate_fragments']) or len(q)!=int(dev['original_positive_OD']) or len(q)*T!=int(dev['original_release_events']):
  raise ValueError('frozen full original demand/fragment count')
 for key in ('incumbent_certificate','incumbent_result','incumbent_swap_array'):
  if sha(R/dev[key])!=dev[key+'_sha256']:raise ValueError('frozen incumbent drift '+key)
 inc=rd(R/dev['incumbent_result']);ic=rd(R/dev['incumbent_certificate'])
 if ic['status']!='PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE' or abs(float(ic['independent_full_original_feasible_upper'])-float(dev['incumbent_independent_feasible_upper_PCE_minutes']))>1e-7:
  raise ValueError('incumbent independent feasible upper')
 with np.load(R/dev['incumbent_swap_array'],allow_pickle=False) as z:
  y=z['swap_pce'].astype(np.float64,copy=True)
  incfi=z['fragment_index'];incod=z['original_OD_index'];incr=z['original_release_step']
  incmass=z['fragment_mass_pce'];incold=z['R43_fragment_unit_cost'];incnew=z['exact_candidate_unit_cost']
 if len(y)!=len(fi) or not np.array_equal(incfi,fi) or not np.array_equal(incod,oi) or not np.array_equal(incr,release):
  raise ValueError('incumbent fragment identity')
 if np.max(abs(incmass-mass))>1e-12 or np.max(abs(incold-old))>1e-7 or np.max(abs(incnew-candidate))>1e-7 or np.any(y<-1e-12) or np.any(y-mass>1e-12):
  raise ValueError('incumbent source mass/cost/box')
 if np.any(y[gain<=1e-9]>1e-11) or abs(float(c43['independent_feasible_primal_upper'])-float(np.dot(y,gain))-float(dev['incumbent_independent_feasible_upper_PCE_minutes']))>1e-6:
  raise ValueError('incumbent independent objective/profile')
 pattern_id=np.full(len(fi),-1,np.int32)
 idx=oi.astype(np.int64)*maxkey+delt.astype(np.int64)
 pattern_id[eligible]=lookup[idx[eligible]]
 if np.any(pattern_id[eligible]<0) or np.max(abs(punit[pattern_id[eligible]]-candidate[eligible]))>1e-7:raise ValueError('candidate pattern identity')
 out=R/'runs/dev34_f_block_lp_numeric_revision/ORDER_00'
 out.mkdir(parents=True,exist_ok=True)
 if (out/'RESULT.json').exists():raise FileExistsError('final endpoint already completed')
 check=out/'CHECKPOINT.npz'
 width=int(dev['release_block_steps'])
 block_ids=list(range((T+width-1)//width-1,-1,-1))
 history_rows=[]
 nextpos=0
 if check.exists():
  with np.load(check,allow_pickle=False) as z:
   resumed=z['swap_pce'];nextpos=int(z['next_block_position']);dhash=str(z['design_sha256']);saved_history=str(z['history_json'])
  if dhash!=sha(devp) or len(resumed)!=len(y) or not 0<=nextpos<=len(block_ids):raise ValueError('checkpoint identity')
  y=resumed.astype(np.float64,copy=True)
  if np.any(y<-1e-12) or np.any(y-mass>1e-12):raise ValueError('checkpoint box')
  history_rows=json.loads(saved_history)
  if len(history_rows)!=nextpos:raise ValueError('checkpoint history identity')
 init_edges(all_edges)
 if not np.all(initialized):raise ValueError('not all candidate capacity edges initialized')
 def action(j):
  i=int(oi[j]);r=int(release[j]);k=int(fi[j]);p=int(pattern_id[j])
  if p<0:raise ValueError('missing original candidate path')
  lo=int(pof[p]);hi=int(pof[p+1]);ce=pe[lo:hi];ct=r+pt[lo:hi]
  if np.any(ct<0) or np.any(ct>=S):raise ValueError('candidate entry outside original horizon')
  wait=int(fw[k,sj]);be=base_edge[i];bt=r+base_offset[i]+base_after[i]*wait
  if np.any(bt<0) or np.any(bt>=S):raise ValueError('original incumbent entry outside horizon')
  candkey=ce.astype(np.int64)*H+ct.astype(np.int64)
  basekey=be.astype(np.int64)*H+bt.astype(np.int64)
  pos=np.setdiff1d(candkey,basekey,assume_unique=True)
  neg=np.setdiff1d(basekey,candkey,assume_unique=True)
  pe0=(pos//H).astype(np.int32);pt0=(pos%H).astype(np.int32)
  ne0=(neg//H).astype(np.int32);nt0=(neg%H).astype(np.int32)
  return rowmap[pe0].astype(np.int64)*S+pt0, rowmap[ne0].astype(np.int64)*S+nt0
 flat=load.reshape(-1)
 for j in np.flatnonzero(y>1e-11):
  pos,neg=action(int(j));amount=float(y[j])
  if len(pos):np.add.at(flat,pos,amount)
  if len(neg):np.add.at(flat,neg,-amount)

 initial_excess=max(float(np.max(load[int(rowmap[e])]-cap[e])) for e in all_edges)
 initial_min=float(np.min(flat))
 if initial_excess>float(dev['post_block_capacity_target_PCE'])+1e-12 or initial_min<-1e-8:raise ValueError('incumbent reconstructed capacity '+str((initial_excess,initial_min)))
 opts={'primal_feasibility_tolerance':float(dev['lp_options']['primal_feasibility_tolerance']),
       'dual_feasibility_tolerance':float(dev['lp_options']['dual_feasibility_tolerance']),
       'time_limit':float(dev['lp_options']['time_limit_seconds_per_block'])}
 for posn in range(nextpos,len(block_ids)):
  bid=block_ids[posn];t0=time.monotonic()
  members=eligible[(release[eligible]//width)==bid]
  if len(members):
   key_parts=[];col_parts=[];sgn_parts=[]
   for col,j in enumerate(members):
    pp,nn=action(int(j))
    if len(pp):
     key_parts.append(pp);col_parts.append(np.full(len(pp),col,np.int32));sgn_parts.append(np.ones(len(pp),np.float64))
    if len(nn):
     key_parts.append(nn);col_parts.append(np.full(len(nn),col,np.int32));sgn_parts.append(-np.ones(len(nn),np.float64))
   if key_parts:
    keys=np.concatenate(key_parts);cols=np.concatenate(col_parts);sign=np.concatenate(sgn_parts)
    unique,inv=np.unique(keys,return_inverse=True)
    A=coo_matrix((sign,(inv,cols)),shape=(len(unique),len(members))).tocsr()
    A.sum_duplicates()
    current=flat[unique].copy();oldx=y[members].copy()
    row_cap=cap[all_edges[unique//S]]
    rhs=row_cap-(current-A@oldx)
    bounds=np.column_stack((np.zeros(len(members)),mass[members]))
    result=linprog(-gain[members],A_ub=A,b_ub=rhs,bounds=bounds,method='highs',options=opts)
    if not result.success:
     save(out/'BLOCK_FAILURE.json',{'status':'LP_BLOCK_FAILED_CHECKPOINT_PRESERVED','block_position':posn,'block_id':bid,'solver_status':int(result.status),'solver_message':str(result.message),'variables':len(members),'rows':len(unique),'nnz':int(A.nnz),'incumbent_max_capacity_residual_PCE':float(np.max(A@oldx-rhs)),'incumbent_min_rhs_PCE':float(np.min(rhs)),'incumbent_max_original_capacity_excess_PCE':float(np.max(current-row_cap)),'design_sha256':sha(devp)})
     raise RuntimeError('block LP stopped at '+str(bid)+' '+str(result.message))
    x=np.clip(np.asarray(result.x,dtype=np.float64),0.,mass[members])
    delta=x-oldx;change=A@delta
    target=float(dev['post_block_capacity_target_PCE'])
    increasing=change>0
    fraction=1.
    if np.any(increasing):
     allowed=(row_cap[increasing]-current[increasing]+target)/change[increasing]
     fraction=max(0.,min(1.,float(np.min(allowed))))
     if fraction<1.:fraction=max(0.,fraction*(1.-1e-10))
    if fraction<1.:
     x=oldx+fraction*delta;delta=x-oldx;change=A@delta
    new=current+change
    if np.max(new-row_cap)>target+1e-12 or np.min(new)<-1e-8:raise ValueError('guarded block LP original resource residual')
    improvement=float(np.dot(gain[members],delta))
    if improvement>1e-9:
     flat[unique]=new;y[members]=x
    else:
     improvement=0.
    row={'block_position':posn,'release_block_id':bid,'variables':len(members),'touched_original_capacity_rows':len(unique),'matrix_nnz':int(A.nnz),'solver_iterations':int(result.nit),'line_search_fraction':fraction,'objective_improvement_PCE_minutes':improvement,'elapsed_seconds':time.monotonic()-t0}
   else:
    row={'block_position':posn,'release_block_id':bid,'variables':len(members),'touched_original_capacity_rows':0,'matrix_nnz':0,'solver_iterations':0,'objective_improvement_PCE_minutes':0.,'elapsed_seconds':time.monotonic()-t0}
  else:
   row={'block_position':posn,'release_block_id':bid,'variables':0,'touched_original_capacity_rows':0,'matrix_nnz':0,'solver_iterations':0,'objective_improvement_PCE_minutes':0.,'elapsed_seconds':time.monotonic()-t0}
  history_rows.append(row)
  cp=out/'CHECKPOINT.partial.npz'
  np.savez_compressed(cp,swap_pce=y,next_block_position=np.array(posn+1,np.int32),design_sha256=np.array(sha(devp)),history_json=np.array(json.dumps(history_rows)))
  cp.replace(check)
  save(out/'PROGRESS.json',{'status':'RUNNING' if posn+1<len(block_ids) else 'COMPLETE_BLOCK_SWEEP_PENDING_FINAL_REPLAY','design_sha256':sha(devp),'blocks':history_rows,'checkpoint_sha256':sha(check)})
  if (posn+1)%10==0 or row['objective_improvement_PCE_minutes']>0.01:
   print(json.dumps({'completed_blocks':posn+1,'total_blocks':len(block_ids),'block':bid,'LP_variables':row['variables'],'rows':row['touched_original_capacity_rows'],'gain':row['objective_improvement_PCE_minutes'],'cumulative_gain_vs_R43':float(np.dot(y,gain)),'elapsed_seconds':time.monotonic()-start}),flush=True)
 final_excess=max(float(np.max(load[int(rowmap[e])]-cap[e])) for e in all_edges);final_min=float(np.min(flat))
 if final_excess>float(dev['post_block_capacity_target_PCE'])+1e-12 or final_min<-1e-8:raise ValueError('final exact capacity')
 prior=float(c43['independent_feasible_primal_upper']);saving=float(np.dot(y,gain));new=prior-saving
 initial=dev['incumbent_independent_feasible_upper_PCE_minutes']
 if new>initial+1e-7:raise ValueError('restricted LP worsened incumbent')
 var=out/'SWAP_VARIABLES.npz'
 np.savez_compressed(var,profile_position=np.arange(len(fi),dtype=np.int32),fragment_index=fi,original_OD_index=oi,original_release_step=release,pattern_id=pattern_id,swap_pce=y,fragment_mass_pce=mass,R43_fragment_unit_cost=old,exact_candidate_unit_cost=candidate)
 result={'schema':'SHARED_CG_DEV34_F_NUMERIC_GUARDED_BLOCK_LP_RESULT_R1','dev34_design_sha256':sha(devp),'ordering_index':0,'ordering':dev['ordering_grid'][0],
         'status':'CANDIDATE_FULL_ORIGINAL_FLOW_PENDING_INDEPENDENT_REPLAY','design_sha256':sha(dp),'R51_profile_result_sha256':sha(p51),'R52_pattern_result_sha256':sha(p52),
         'R43_independent_certificate_sha256':sha(d['R43_independent_certificate']),'incumbent_independent_certificate_sha256':dev['incumbent_certificate_sha256'],
         'source_hashes':d['source_hashes'],'original_positive_OD':len(q),'original_release_events':len(q)*T,
         'selected_original_bridge_OD':len(selected_od),'selected_source_fragments':len(fi),'positive_gain_fragments':len(eligible),
         'positive_fragment_swaps':int(np.count_nonzero(y>1e-11)),'achieved_capacity_feasible_saving_PCE_minutes':saving,'prior_R43_independent_feasible_upper':prior,
         'candidate_full_original_objective':new,'incumbent_independent_feasible_upper':initial,'improvement_over_incumbent_PCE_minutes':initial-new,
         'block_width_release_steps':width,'completed_blocks':len(history_rows),'total_lp_iterations':sum(int(a['solver_iterations']) for a in history_rows),
         'total_touched_rows_across_blocks':sum(int(a['touched_original_capacity_rows']) for a in history_rows),'total_matrix_nnz_across_blocks':sum(int(a['matrix_nnz']) for a in history_rows),
         'original_capacity_edges_initialized':int(np.count_nonzero(initialized)),'compact_capacity_time_steps':S,'compact_capacity_array_bytes':expected_bytes,
         'internal_post_block_capacity_target_PCE':float(dev['post_block_capacity_target_PCE']),'max_original_capacity_excess_PCE':max(0.,final_excess),'min_original_row_flow_PCE':final_min,'variable_path':str(var),'variable_sha256':sha(var),
         'checkpoint_sha256':sha(check),'history_path':str(out/'PROGRESS.json'),'wall_seconds':time.monotonic()-start,
         'scientific_limit':'One feasible block-coordinate sweep on fixed R51/R52 paths; not a global restricted LP or unrestricted CG optimum.'}
 save(out/'RESULT.json',result)
 print(json.dumps({'status':result['status'],'new_upper':new,'gain_over_incumbent':initial-new,'blocks':len(history_rows),'lp_iterations':result['total_lp_iterations'],'max_excess':result['max_original_capacity_excess_PCE'],'wall_seconds':result['wall_seconds']}),flush=True)
if __name__=='__main__':main()





