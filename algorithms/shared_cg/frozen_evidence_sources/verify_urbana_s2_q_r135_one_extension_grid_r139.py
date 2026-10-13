"""Independent original CSV full-demand audit of frozen Urbana S2 one-time extension."""
from pathlib import Path
from collections import deque
import json,time
import numpy as np
from verify_q_s2_two_bridge_plus_cycle_r72 import R,sha,rd,rows,reverse_static,independent_profile

def main():
 started=time.monotonic();dp=R/'URBANA_S2_Q_R135_ONE_EXTENSION_GRID_PRE_RUN_R137.json';d=rd(dp);rp=R/'runs/urbana_s2_q_r135_one_extension_grid_r138/RESULT.json';rec=rd(rp)
 paths={'R71_result_sha256':R/'runs/q_s2_two_bridge_plus_cycle_toll_r71/RESULT.json','R135_independent_certificate_sha256':R/'runs/urbana_s2_q_fixed_cycle_two_bridge_coord_grid_r134/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R135.json','R134_result_sha256':R/'runs/urbana_s2_q_fixed_cycle_two_bridge_coord_grid_r134/RESULT.json','R136_conditional_rule_sha256':R/'URBANA_S2_Q_CONDITIONAL_R135_ONE_EXTENSION_RULE_R136.json','R28_result_sha256':R/'Q_S2_TWO_BRIDGE_FINE_RESULT_R28.json','source_config_sha256':R/'cases/urbana_S2_Q__sparse_common_dev9_delayed_zero_gc.json','original_AON_array_sha256':R/'runs/sparse_common_dev9_delayed_zero_gc/urbana_S2_Q/solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'}
 for key,p in paths.items():
  if sha(p)!=d[key]:raise ValueError(key+' drift')
 r71=rd(paths['R71_result_sha256']);c135=rd(paths['R135_independent_certificate_sha256']);r28=rd(paths['R28_result_sha256']);r134=rd(paths['R134_result_sha256']);rule=rd(paths['R136_conditional_rule_sha256'])
 grid=d['factor_pair_grid']
 if rec['design_sha256']!=sha(dp) or [x['factor_pair'] for x in rec['history']]!=grid or grid!=[[.9,.9],[.91,.9],[.9,.91],[.91,.91],[.92,.92]] or grid!=rule['one_extension_factor_pair_grid'] or c135['status']!='PASS_EXACT_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY' or c135['selected_bridge_factor_pair']!=[.9,.9] or r134['selected_bridge_factor_pair']!=[.9,.9]:raise ValueError('complete frozen grid/accepted base')
 cfg=rd(paths['source_config_sha256']);source=Path(cfg['source_dir']);hashes={n:sha(source/n) for n in ('network.csv','access.csv','assignment_od_pce.csv')}
 if hashes!=d['original_source_hashes'] or hashes!=cfg['expected_source_hashes'] or hashes!=c135['original_source_hashes']:raise ValueError('original source')
 net=rows(source/'network.csv');acc=rows(source/'access.csv');od=rows(source/'assignment_od_pce.csv');nodes=sorted({x['from_node_id'] for x in net}|{x['to_node_id'] for x in net});ix={x:i for i,x in enumerate(nodes)};access={x['zone_id']:ix[x['node_id']] for x in acc}
 if len(access)!=len(acc) or len(od)!=d['original_positive_OD']:raise ValueError('original access/OD')
 u=np.array([ix[x['from_node_id']] for x in net],np.int32);v=np.array([ix[x['to_node_id']] for x in net],np.int32);cost=np.array([float(x['vdf_fftt']) for x in net]);phys=np.array([x[cfg['physical_field']]==cfg['physical_value'] for x in net]);dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);dur=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 if len(od)*T!=d['original_release_events'] or abs(T*dt-3600)>1e-8:raise ValueError('original release')
 pe=np.flatnonzero(phys);ze=np.flatnonzero(~phys);zu=u[ze];zv=v[ze];zc=cost[ze];order=np.argsort(zu,kind='stable');zu=zu[order];zv=zv[order];zc=zc[order];zo=np.r_[0,np.cumsum(np.bincount(zu,minlength=len(nodes)))].astype(np.int32);indeg=np.bincount(zv,minlength=len(nodes)).astype(np.int32);queue=deque(np.flatnonzero(indeg==0).tolist());topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for e in range(zo[node],zo[node+1]):
   nxt=int(zv[e]);indeg[nxt]-=1
   if indeg[nxt]==0:queue.append(nxt)
 if len(topo)!=len(nodes):raise ValueError('original zero-time cycle')
 reverse=np.asarray(topo[::-1],np.int32);incoming=[[] for _ in nodes]
 for e in range(len(net)):incoming[v[e]].append((int(u[e]),float(cost[e]),int(dur[e])))
 intervals=[(int(x['original_edge_index']),int(x['first_entry_step']),int(x['end_exclusive_entry_step'])) for x in d['bridge_intervals']];terminal=int(d['price_end_exclusive']);loops=list(map(int,d['fixed_cycle_original_physical_edges']));flat=float(d['fixed_cycle_flat_toll_minutes']);basef=np.array(d['base_bridge_factor_pair'],np.float64)
 if intervals!=[(447,557,35491),(2876,606,29548)] or terminal!=35491 or loops!=r71['cycle_original_edges'] or flat!=r71['best_cycle_flat_toll_minutes'] or r134['selected_bridge_factor_pair']!=d['base_bridge_factor_pair']:raise ValueError('accepted price resources')
 priceid=np.full(len(pe),-1,np.int32)
 for j,(e,first,stop) in enumerate(intervals):
  atp=np.flatnonzero(pe==e)
  if len(atp)!=1 or float(net[e]['capacity'])<=0:raise ValueError('original physical bridge')
  priceid[atp[0]]=j
 pstart=np.array([x[1] for x in intervals],np.int32);pend=np.array([x[2] for x in intervals],np.int32);loopmask=np.isin(pe,loops)
 with np.load(paths['original_AON_array_sha256'],allow_pickle=False) as z:ao=z['od_edge_offset'];ae=z['edge_index'];at=z['entry_offset_steps'];q=z['od_hourly_pce'];static=z['od_static_shortest_cost']
 basearr=Path(r134['array_path'])
 if sha(basearr)!=d['R134_array_sha256'] or sha(basearr)!=c135['producer_array_sha256']:raise ValueError('accepted R72 array')
 with np.load(basearr,allow_pickle=False) as z:ids0=z['original_OD_index'];release0=z['original_release_step'];basevalues=z['adjusted_shortest_cost']
 origins=np.array([access[x['o_zone_id']] for x in od],np.int32);dests=np.array([access[x['d_zone_id']] for x in od],np.int32);trees={};bounds={};flag=np.zeros((len(od),T),np.bool_);lookup={e:(first,stop) for e,first,stop in intervals};target=set(loops)|set(lookup);baseline=0.;maxarrival=0
 for i,row in enumerate(od):
  mass=float(row['volume_pce'])*float(cfg['demand_factor'])
  if abs(mass-q[i])>1e-9:raise ValueError('original OD mass')
  z=int(dests[i]);node=int(origins[i])
  if z not in trees:trees[z],bounds[z]=reverse_static(len(nodes),incoming,z)
  h=trees[z];t=0;value=0.
  for j in range(int(ao[i]),int(ao[i+1])):
   e=int(ae[j]);offset=int(at[j])
   if e<0 or e>=len(net) or u[e]!=node or offset!=t:raise ValueError('AON original node/time mapping')
   if e in target:
    first,stop=lookup[e] if e in lookup else (0,terminal);lo=max(0,first-offset);hi=min(T,stop-offset)
    if lo<hi:flag[i,lo:hi]=True
   value+=cost[e];t+=int(dur[e]);node=int(v[e])
  if node!=z or t+T-1>H or abs(value-static[i])>1e-7 or abs(value-h[origins[i]])>1e-7:raise ValueError('original AON shortest/terminal')
  baseline+=mass*h[origins[i]];maxarrival=max(maxarrival,t+T-1)
 ids,release=np.nonzero(flag);ids=ids.astype(np.int32);release=release.astype(np.int32)
 if not np.array_equal(ids,ids0) or not np.array_equal(release,release0) or len(ids)!=d['R135_affected_original_events'] or len(np.unique(dests[ids]))!=d['R135_affected_destinations'] or abs(baseline-c135['independent_baseline_original_lower'])>1e-6:raise ValueError('all original affected releases/static lower')
 capunit=np.array([float(net[e]['capacity'])*dt/3600.*(dt/60.)*(stop-first)*(stop-first+1)/2 for e,first,stop in intervals],np.float64);values=np.empty(len(ids),np.float64);history=[];selected_values=None;selected_err=0.
 for pair,claim in zip(grid,rec['history']):
  factors=np.array(pair,np.float64);pweight=factors*dt/60.
  for z in np.unique(dests[ids]):
   z=int(z);h=trees[z]
   if terminal+int(np.max(dur))+bounds[z]>H:raise ValueError('static terminal bound')
   pos=np.flatnonzero(dests[ids]==z);pos=pos[np.argsort(-release[pos],kind='stable')]
   values[pos]=independent_profile(len(nodes),H,terminal,dt,u[pe],v[pe],cost[pe],dur[pe],priceid,pstart,pend,pweight,loopmask,flat,zo,zv,zc,reverse,z,h,release[pos],origins[ids[pos]])
  if pair==grid[0] and np.max(abs(values-basevalues))>1e-7:raise ValueError('R135 control')
  delta=float(np.dot(q[ids]/T,values-basevalues));penalty=float(np.dot(factors-basef,capunit));lower=float(c135['independent_exact_full_original_graph_dual_lower'])+delta-penalty
  err=max(abs(lower-claim['exact_full_original_graph_dual_lower']),abs(delta-claim['all_affected_event_cost_change']),abs(penalty-claim['incremental_original_capacity_price_constant']))
  if err>1e-6 or lower>c135['R58_independent_feasible_upper']+1e-6:raise ValueError('independent full original dual grid')
  history.append({'factor_pair':pair,'independent_exact_full_original_graph_dual_lower':lower,'all_affected_event_cost_change':delta,'incremental_original_capacity_price_constant':penalty,'max_producer_accounting_error':err})
  if pair==rec['selected_bridge_factor_pair']:
   selected_values=values.copy();selected_err=err
  print(json.dumps(history[-1]),flush=True)
 best=max(history,key=lambda x:x['independent_exact_full_original_graph_dual_lower'])
 if best['factor_pair']!=rec['selected_bridge_factor_pair'] or abs(best['independent_exact_full_original_graph_dual_lower']-rec['producer_exact_full_original_graph_dual_lower'])>1e-6:raise ValueError('complete grid selection')
 ap=Path(rec['array_path'])
 if sha(ap)!=rec['array_sha256'] or selected_values is None:raise ValueError('producer selected array')
 with np.load(ap,allow_pickle=False) as z:
  if not np.array_equal(z['original_OD_index'],ids) or not np.array_equal(z['original_release_step'],release) or np.max(abs(z['bridge_factor_pair']-np.array(best['factor_pair'])))>1e-12 or abs(float(z['fixed_cycle_flat_toll_minutes'][0])-flat)>1e-12 or not np.array_equal(z['fixed_cycle_original_physical_edges'],np.array(loops,np.int32)):raise ValueError('selected event/price identity')
  maxpriceerr=float(np.max(abs(z['adjusted_shortest_cost']-selected_values)))
 if maxpriceerr>1e-7:raise ValueError('independent selected event prices')
 status='PASS_EXACT_FULL_ORIGINAL_GRAPH_DUAL_IMPROVED_OPEN_OPTIMALITY' if best['independent_exact_full_original_graph_dual_lower']>c135['independent_exact_full_original_graph_dual_lower']+1e-6 else 'PASS_EXACT_VALID_BUT_NO_IMPROVEMENT_RETAIN_R135'
 cert={'schema':'URBANA_S2_Q_R135_ONE_EXTENSION_GRID_INDEPENDENT_CERT_R139','status':status,'original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_events':len(od)*T,'original_horizon_steps':H,'original_physical_arc_count':len(pe),'all_original_physical_capacity_rows':len(pe)*H,'affected_original_release_events_independently_repriced_per_point':len(ids),'unaffected_original_release_events_proven':len(od)*T-len(ids),'priced_destinations_per_point':len(np.unique(dests[ids])),'max_original_AON_arrival_step':maxarrival,'independent_baseline_original_lower':baseline,'complete_grid':history,'selected_bridge_factor_pair':best['factor_pair'],'R135_independent_lower':c135['independent_exact_full_original_graph_dual_lower'],'independent_exact_full_original_graph_dual_lower':best['independent_exact_full_original_graph_dual_lower'],'R58_independent_feasible_upper':c135['R58_independent_feasible_upper'],'relative_open_gap':(c135['R58_independent_feasible_upper']-best['independent_exact_full_original_graph_dual_lower'])/c135['R58_independent_feasible_upper'],'max_producer_selected_event_price_error':maxpriceerr,'max_selected_producer_accounting_error':selected_err,'producer_result_sha256':sha(rp),'producer_array_sha256':sha(ap),'frozen_design_sha256':sha(dp),'R135_certificate_sha256':sha(paths['R135_independent_certificate_sha256']),'R136_conditional_rule_sha256':sha(paths['R136_conditional_rule_sha256']),'wall_seconds':time.monotonic()-started,'scientific_limit':'Exact full-original-graph dual grid and separate feasible primal; global optimum and same-build CG closure remain open.'}
 out=R/'runs/urbana_s2_q_r135_one_extension_grid_r138/INDEPENDENT_FULL_ORIGINAL_DUAL_CERT_R139.json';out.write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':status,'pair':best['factor_pair'],'lower':cert['independent_exact_full_original_graph_dual_lower'],'gap':cert['relative_open_gap'],'price_error':maxpriceerr,'seconds':cert['wall_seconds']}),flush=True)
if __name__=='__main__':main()
