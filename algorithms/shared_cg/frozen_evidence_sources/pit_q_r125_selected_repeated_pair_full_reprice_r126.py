"""Full 29-destination exact original-graph dual reprice at frozen R125 point."""
from pathlib import Path
import json,time
import numpy as np
from q_profile_dp_probe_v2 import setup,static_h
from q_original_dual_price_profile_common_r89 import price_profile
from pit_q_r117_selected_factor_full_reprice_r119 import R,sha,rd,rows,save

def main():
 started=time.monotonic();dp=R/'PIT_Q_R125_SELECTED_REPEATED_PAIR_FULL_REPRICE_PRE_RUN_R126.json';d=rd(dp)
 paths={'R119_result_sha256':R/'runs/pit_q_r117_selected_factor_full_reprice_r119/RESULT.json','R120_independent_certificate_sha256':R/'runs/pit_q_r117_selected_factor_full_reprice_r119/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R120.json','R124_result_sha256':R/'runs/pit_q_r123_repeated_pair_monotone_r124/RESULT.json','R125_independent_complete_grid_certificate_sha256':R/'runs/pit_q_r123_repeated_pair_monotone_r124/INDEPENDENT_COMPLETE_GRID_CERT_R125.json','generic_price_core_sha256':R/'q_original_dual_price_profile_common_r89.py','source_config_sha256':R/'cases/pittsburgh_S2_Q__sparse_common_dev9_delayed_zero_gc.json','original_AON_array_sha256':R/'runs/sparse_common_dev9_delayed_zero_gc/pittsburgh_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'}
 for key,p in paths.items():
  if sha(p)!=d[key]:raise ValueError(key+' drift')
 base=rd(paths['R119_result_sha256']);cert=rd(paths['R120_independent_certificate_sha256']);screen=rd(paths['R124_result_sha256']);screen_cert=rd(paths['R125_independent_complete_grid_certificate_sha256'])
 if cert['status']!='PASS_EXACT_FULL_ORIGINAL_GRAPH_DUAL_LOWER_OPEN_OPTIMALITY' or screen_cert['status']!='PASS_COMPLETE_GRID_CONSERVATIVE_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY' or screen_cert['selected_candidate_flat_toll_minutes']!=d['selected_candidate_flat_toll_minutes'] or screen_cert['best_independent_conservative_full_original_graph_lower']<=cert['independent_exact_full_original_graph_lower']+1e-6:raise ValueError('independent gate')
 cp=paths['source_config_sha256'];cfg=rd(cp);source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in ('network.csv','access.csv','assignment_od_pce.csv')}
 if hashes!=d['original_source_hashes'] or hashes!=cfg['expected_source_hashes']:raise ValueError('original source')
 net=rows(source/'network.csv');T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dt=float(cfg['dt_seconds']);bridge=int(d['bridge_original_edge']);first=int(d['bridge_first_step']);end=int(d['price_end_exclusive']);candidate=list(map(int,d['candidate_original_physical_edges']))
 cfg2,_,od,nodes,access,u,v,cost,dur,phys,off,order,inc,pid,starts,ends,weights,inverse=setup('pittsburgh_S2_Q',[(bridge,first,end,1.)],1.)
 if cfg2!=cfg or len(od)!=d['original_positive_OD'] or len(od)*T!=d['original_release_events']:raise ValueError('full original OD/time')
 basearr=Path(base['array_path'])
 if sha(basearr)!=d['R119_array_sha256'] or sha(basearr)!=cert['producer_array_sha256']:raise ValueError('accepted base array')
 with np.load(basearr,allow_pickle=False) as z:ids=z['original_OD_index'];release=z['original_release_step'];basevalues=z['adjusted_shortest_cost'];baselam=z['bridge_price_per_step']
 with np.load(paths['original_AON_array_sha256'],allow_pickle=False) as z:ao=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 if len(ids)!=d['R119_exact_affected_original_events']:raise ValueError('affected event count')
 oldprices={int(k):float(v) for k,v in d['base_flat_original_physical_edge_prices_minutes'].items()};prices={int(k):float(v) for k,v in d['new_flat_original_physical_edge_prices_minutes'].items()}
 if base['flat_original_physical_edge_prices_minutes']!=d['base_flat_original_physical_edge_prices_minutes'] or candidate!=[16684,16682] or set(oldprices)!=set(prices) or any((prices[e]!=d['selected_candidate_flat_toll_minutes'] if e in candidate else prices[e]!=oldprices[e]) for e in prices):raise ValueError('fixed physical price vector')
 flag=np.zeros((len(od),T),np.bool_);target=set(prices)|{bridge}
 for i in range(len(od)):
  for j in range(int(ao[i]),int(ao[i+1])):
   e=int(ae[j])
   if e not in target:continue
   offset=int(at[j]);lo=max(0,(first if e==bridge else 0)-offset);hi=min(T,end-offset)
   if lo<hi:flag[i,lo:hi]=True
 checkids,checkrelease=np.nonzero(flag)
 if not np.array_equal(ids,checkids) or not np.array_equal(release,checkrelease):raise ValueError('complete original AON affected support')
 origin=np.array([access[x['o_zone_id']] for x in od],np.int32);dest=np.array([access[x['d_zone_id']] for x in od],np.int32);qsource=np.array([float(x['volume_pce'])*float(cfg['demand_factor']) for x in od])
 if np.max(abs(q-qsource))>1e-9 or len(np.unique(dest[ids]))!=d['original_affected_destinations']:raise ValueError('source demand/destinations')
 lam=np.array([float(d['bridge_factor'])*dt/60*(end-t) for t in range(first,end)],np.float64)
 if np.max(abs(lam-baselam))>1e-12:raise ValueError('bridge price drift')
 flat=np.zeros(len(cost),np.float64)
 for e,price in prices.items():
  if net[e][cfg['physical_field']]!=cfg['physical_value'] or float(net[e]['capacity'])<=0:raise ValueError('original physical price row')
  flat[inverse[e]]=price
 out=R/'runs/pit_q_r125_selected_repeated_pair_full_reprice_r126'
 if out.exists() and any(out.iterdir()):raise FileExistsError(out)
 out.mkdir(parents=True);values=basevalues.copy();terminal={}
 for z in np.unique(dest[ids]):
  z=int(z);h,bound=static_h(len(nodes),inc,z);pos=np.flatnonzero(dest[ids]==z);pos=pos[np.argsort(-release[pos],kind='stable')]
  if end+int(np.max(dur))+bound>H or np.max(abs(h[origin[np.unique(ids[pos])]]-static[np.unique(ids[pos])]))>1e-7:raise ValueError('original static/terminal')
  values[pos]=price_profile(len(nodes),H,end,dt,off,order,v,cost,dur,int(inverse[bridge]),first,lam,flat,z,h,release[pos],origin[ids[pos]])
  terminal[str(z)]=bound;print(json.dumps({'destination':z,'events':len(pos),'completed_destinations':len(terminal),'total_destinations':d['original_affected_destinations'],'elapsed_seconds':time.monotonic()-started}),flush=True)
 capdelta=sum(float(net[e]['capacity'])*dt/3600.*end*(prices[e]-oldprices[e]) for e in candidate)
 delta=float(np.dot(q[ids]/T,values-basevalues));lower=float(cert['independent_exact_full_original_graph_lower'])+delta-capdelta
 if lower+1e-6<screen_cert['best_independent_conservative_full_original_graph_lower'] or lower>cert['original_feasible_upper']+1e-6:raise ValueError('conservative gate/weak duality')
 arr=out/'BEST_PRICE_PROFILE.npz';np.savez_compressed(arr,original_OD_index=ids,original_release_step=release,adjusted_shortest_cost=values,bridge_price_per_step=lam,flat_original_physical_edges=np.array(list(prices),np.int32),flat_toll_minutes_per_edge=np.array(list(prices.values())))
 rec={'schema':'PIT_Q_R125_SELECTED_REPEATED_PAIR_FULL_REPRICE_RESULT_R126','status':'PRODUCER_EXACT_FULL_ORIGINAL_DUAL_PENDING_INDEPENDENT','case_id':'pittsburgh_S2_Q','design_sha256':sha(dp),'original_source_hashes':hashes,'R125_independent_certificate_sha256':sha(paths['R125_independent_complete_grid_certificate_sha256']),'original_positive_OD':len(od),'original_release_events':len(od)*T,'affected_original_release_events':len(ids),'unaffected_original_release_events_static_proven':len(od)*T-len(ids),'affected_original_positive_OD':len(np.unique(ids)),'priced_destinations':len(terminal),'terminal_bounds':terminal,'bridge_factor':d['bridge_factor'],'flat_original_physical_edge_prices_minutes':d['new_flat_original_physical_edge_prices_minutes'],'R120_independent_exact_lower':cert['independent_exact_full_original_graph_lower'],'all_affected_event_cost_increment':delta,'incremental_candidate_capacity_price_constant':capdelta,'producer_exact_full_original_graph_lower':lower,'R125_conservative_lower':screen_cert['best_independent_conservative_full_original_graph_lower'],'original_feasible_upper':cert['original_feasible_upper'],'relative_open_gap':(cert['original_feasible_upper']-lower)/cert['original_feasible_upper'],'array_path':str(arr),'array_sha256':sha(arr),'wall_seconds':time.monotonic()-started,'scientific_limit':'Exact full-original-graph dual price point; separately certified feasible primal, global optimum open.'}
 save(out/'RESULT.json',rec);print(json.dumps({'status':rec['status'],'lower':lower,'gap':rec['relative_open_gap'],'events':len(ids),'destinations':len(terminal),'seconds':rec['wall_seconds']}),flush=True)
if __name__=='__main__':main()
