"""One frozen conditional full original Urbana S2 Q dual extension with fixed cycle toll."""
from pathlib import Path
import json,time
import numpy as np
from q_profile_dp_probe_v2 import setup,static_h
from q_s2_two_bridge_plus_cycle_toll_r71 import price_profile,R,sha,rd,rows,save

def main():
 started=time.monotonic();dp=R/'URBANA_S2_Q_R135_ONE_EXTENSION_GRID_PRE_RUN_R137.json';d=rd(dp)
 paths={'R71_result_sha256':R/'runs/q_s2_two_bridge_plus_cycle_toll_r71/RESULT.json','R135_independent_certificate_sha256':R/'runs/urbana_s2_q_fixed_cycle_two_bridge_coord_grid_r134/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R135.json','R134_result_sha256':R/'runs/urbana_s2_q_fixed_cycle_two_bridge_coord_grid_r134/RESULT.json','R136_conditional_rule_sha256':R/'URBANA_S2_Q_CONDITIONAL_R135_ONE_EXTENSION_RULE_R136.json','R28_result_sha256':R/'Q_S2_TWO_BRIDGE_FINE_RESULT_R28.json','source_config_sha256':R/'cases/urbana_S2_Q__sparse_common_dev9_delayed_zero_gc.json','original_AON_array_sha256':R/'runs/sparse_common_dev9_delayed_zero_gc/urbana_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'}
 for key,p in paths.items():
  if sha(p)!=d[key]:raise ValueError(key+' drift')
 r71=rd(paths['R71_result_sha256']);c135=rd(paths['R135_independent_certificate_sha256']);r28=rd(paths['R28_result_sha256']);r134=rd(paths['R134_result_sha256']);rule=rd(paths['R136_conditional_rule_sha256'])
 grid=d['factor_pair_grid'];basef=np.asarray(d['base_bridge_factor_pair'],np.float64)
 if c135['status']!='PASS_EXACT_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY' or c135['selected_bridge_factor_pair']!=[.9,.9] or r134['selected_bridge_factor_pair']!=d['base_bridge_factor_pair'] or grid!=rule['one_extension_factor_pair_grid'] or grid!=[[.9,.9],[.91,.9],[.9,.91],[.91,.91],[.92,.92]] or r71['best_cycle_flat_toll_minutes']!=d['fixed_cycle_flat_toll_minutes'] or r71['cycle_original_edges']!=d['fixed_cycle_original_physical_edges']:raise ValueError('accepted fixed price family')
 cfg=rd(paths['source_config_sha256']);source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in ('network.csv','access.csv','assignment_od_pce.csv')}
 if hashes!=d['original_source_hashes'] or hashes!=cfg['expected_source_hashes']:raise ValueError('original source')
 net=rows(source/'network.csv');T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dt=float(cfg['dt_seconds']);terminal=int(d['price_end_exclusive']);intervals=[(int(x['original_edge_index']),int(x['first_entry_step']),int(x['end_exclusive_entry_step']),1.) for x in d['bridge_intervals']]
 if intervals!=[(447,557,35491,1.),(2876,606,29548,1.)] or terminal!=35491:raise ValueError('original bridge interval identity')
 cfg2,_,od,nodes,access,u,v,cost,dur,phys,off,order,inc,pid,starts,ends,weights,inverse=setup('urbana_S2_Q',intervals,1.)
 if cfg2!=cfg or len(od)!=d['original_positive_OD'] or len(od)*T!=d['original_release_events']:raise ValueError('original OD/time')
 basearr=Path(r134['array_path'])
 if sha(basearr)!=d['R134_array_sha256'] or sha(basearr)!=c135['producer_array_sha256']:raise ValueError('accepted R72 array')
 with np.load(basearr,allow_pickle=False) as z:ids=z['original_OD_index'];release=z['original_release_step'];basevalues=z['adjusted_shortest_cost']
 with np.load(paths['original_AON_array_sha256'],allow_pickle=False) as z:ao=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 if len(ids)!=d['R135_affected_original_events']:raise ValueError('R72 affected count')
 lookup={e:(f,en) for e,f,en,_ in intervals};target=set(lookup)|set(map(int,d['fixed_cycle_original_physical_edges']));flag=np.zeros((len(od),T),np.bool_)
 for i in range(len(od)):
  for j in range(int(ao[i]),int(ao[i+1])):
   e=int(ae[j])
   if e not in target:continue
   first,end=lookup[e] if e in lookup else (0,terminal);offset=int(at[j]);lo=max(0,first-offset);hi=min(T,end-offset)
   if lo<hi:flag[i,lo:hi]=True
 checkids,checkrelease=np.nonzero(flag)
 if not np.array_equal(ids,checkids) or not np.array_equal(release,checkrelease):raise ValueError('complete original AON affected releases')
 origin=np.array([access[x['o_zone_id']] for x in od],np.int32);dest=np.array([access[x['d_zone_id']] for x in od],np.int32);qsource=np.array([float(x['volume_pce'])*float(cfg['demand_factor']) for x in od])
 if np.max(abs(q-qsource))>1e-9:raise ValueError('original hourly OD mass')
 profiles={}
 for z in np.unique(dest[ids]):
  z=int(z);h,bound=static_h(len(nodes),inc,z);pos=np.flatnonzero(dest[ids]==z);pos=pos[np.argsort(-release[pos],kind='stable')]
  if terminal+int(np.max(dur))+bound>H or np.max(abs(h[origin[np.unique(ids[pos])]]-static[np.unique(ids[pos])]))>1e-7:raise ValueError('original terminal/static')
  profiles[z]=(h,pos)
 if len(profiles)!=d['R135_affected_destinations']:raise ValueError('destination count')
 loops=np.asarray(d['fixed_cycle_original_physical_edges'],np.int32);loopmask=np.zeros(len(cost),np.bool_);loopmask[inverse[loops]]=True;flat=float(d['fixed_cycle_flat_toll_minutes'])
 capunit=np.asarray([float(net[e]['capacity'])*dt/3600.*(dt/60.)*(en-f)*(en-f+1)/2 for e,f,en,_ in intervals],np.float64)
 out=R/'runs/urbana_s2_q_r135_one_extension_grid_r138'
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 out.mkdir(parents=True);history=[];best=None
 for pair in grid:
  factors=np.asarray(pair,np.float64);slopes=factors*dt/60.;values=static[ids].astype(np.float64).copy()
  for z,(h,pos) in profiles.items():values[pos]=price_profile(len(nodes),H,terminal,dt,off,order,v,cost,dur,pid,starts,ends,slopes,loopmask,flat,z,h,release[pos],origin[ids[pos]])
  if pair==grid[0] and np.max(abs(values-basevalues))>1e-7:raise ValueError('R135 control point')
  delta=float(np.dot(q[ids]/T,values-basevalues));penalty=float(np.dot(factors-basef,capunit));lower=float(c135['independent_exact_full_original_graph_dual_lower'])+delta-penalty
  if lower>c135['R58_independent_feasible_upper']+1e-6:raise ValueError('weak duality')
  row={'factor_pair':pair,'exact_full_original_graph_dual_lower':lower,'all_affected_event_cost_change':delta,'incremental_original_capacity_price_constant':penalty,'original_affected_events_repriced':len(ids),'elapsed_seconds':time.monotonic()-started};history.append(row)
  if best is None or lower>best[0]+1e-9:best=(lower,pair,values.copy(),delta,penalty)
  save(out/'PROGRESS.json',{'status':'RUNNING','design_sha256':sha(dp),'history':history,'best_lower':best[0],'best_pair':best[1]});print(json.dumps(row),flush=True)
 lower,pair,values,delta,penalty=best;arr=out/'BEST_PRICE_PROFILE.npz';np.savez_compressed(arr,original_OD_index=ids,original_release_step=release,adjusted_shortest_cost=values,bridge_factor_pair=np.asarray(pair,np.float64),fixed_cycle_flat_toll_minutes=np.array([flat]),fixed_cycle_original_physical_edges=loops)
 rec={'schema':'URBANA_S2_Q_R135_ONE_EXTENSION_GRID_RESULT_R138','status':'PRODUCER_EXACT_FULL_ORIGINAL_GRAPH_GRID_PENDING_INDEPENDENT','case_id':'urbana_S2_Q','design_sha256':sha(dp),'original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_events':len(od)*T,'affected_original_release_events':len(ids),'unaffected_original_release_events_static_proven':len(od)*T-len(ids),'affected_destinations':len(profiles),'selected_bridge_factor_pair':pair,'fixed_cycle_flat_toll_minutes':flat,'producer_exact_full_original_graph_dual_lower':lower,'R135_independent_lower':c135['independent_exact_full_original_graph_dual_lower'],'R58_independent_feasible_upper':c135['R58_independent_feasible_upper'],'relative_open_gap':(c135['R58_independent_feasible_upper']-lower)/c135['R58_independent_feasible_upper'],'history':history,'array_path':str(arr),'array_sha256':sha(arr),'wall_seconds':time.monotonic()-started,'scientific_limit':'Exact original graph finite dual grid pending independent original CSV Bellman audit; global optimum open.'}
 save(out/'RESULT.json',rec);print(json.dumps({'status':rec['status'],'pair':pair,'lower':lower,'gap':rec['relative_open_gap'],'seconds':rec['wall_seconds']}),flush=True)
if __name__=='__main__':main()
