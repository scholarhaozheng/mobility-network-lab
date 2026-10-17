"""Independently replay one frozen recovered path batch from original CSVs."""
from pathlib import Path
from hashlib import sha256
import argparse,csv,json,math,os,numpy as np
R=Path(__file__).resolve().parent
OUT=R/'runs/dev22_batch_original_paths_urbana_f'
CFG=R/'cases/urbana_F_Q__sparse_common_dev20_rolling_path_recovery.json'
SEL=R/'runs/dev22_batch_negative_selection_urbana_f/SELECTED_ORIGINAL_EVENTS.npz'
DUAL=R/'runs/dev21_third_real_rmp_urbana_f/NEW_RESTRICTED_RMP_ROWS_AND_DUAL.npz'
PRICE=R/'runs/dev21_third_rmp_dual_price_urbana_f/INDEPENDENT_ALL_ORIGINAL_PRICE_VALUES.npz'

def sha(p):
 h=sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def csvrows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def replay(net,physical,origin,destination,release,edges,entries,H,dt,tolls,declared_rows=None):
 node=origin;t=int(release);raw=adjusted=0.;waits=0;rows=[];seen=set()
 for edge,entry in zip(edges,entries):
  edge=int(edge);entry=int(entry)
  if edge<0 or edge>=len(net):raise ValueError('invalid original edge')
  if entry<t or entry>H:raise ValueError('wrong original entry time')
  if node==destination:raise ValueError('hidden travel after destination')
  waits+=entry-t
  raw+=(entry-t)*dt/60.;adjusted+=(entry-t)*dt/60.;t=entry
  if (t,node) in seen:raise ValueError('zero duration cycle')
  seen.add((t,node))
  arc=net[edge]
  if arc['from_node_id']!=node:raise ValueError('bad original node mapping')
  c=float(arc['vdf_fftt'])
  duration=max(1,math.ceil(c*60/dt-1e-12)) if arc['arc_kind']=='physical' else 0
  if t+duration>H:raise ValueError('original horizon exceeded')
  raw+=c;adjusted+=c
  p=physical.get(edge)
  if p is not None:
   row=p*H+t;rows.append(row);adjusted+=tolls.get(row,0.)
  node=arc['to_node_id'];t+=duration
 if node!=destination:raise ValueError('unserved original commodity')
 if declared_rows is not None and list(map(int,declared_rows))!=rows:raise ValueError('hidden or bad capacity mapping')
 return raw,adjusted,t,waits,rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--destination',type=int,required=True);args=ap.parse_args()
 cfg=json.loads(CFG.read_text(encoding='utf-8-sig'));source=Path(cfg['source_dir'])
 hashes={name:sha(source/name) for name in cfg['expected_source_hashes']}
 if hashes!=cfg['expected_source_hashes']:raise ValueError('original CSV identity')
 net=csvrows(source/'network.csv');access=csvrows(source/'access.csv');od=csvrows(source/'assignment_od_pce.csv')
 zones={r['zone_id']:r['node_id'] for r in access}
 physical={i:j for j,i in enumerate(i for i,r in enumerate(net) if r['arc_kind']=='physical')}
 H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
 with np.load(DUAL) as z:
  rows=z['original_resource_rows'];mu=z['capacity_dual']
 tolls={int(r):float(-v) for r,v in zip(rows,mu) if v<-1e-12}
 with np.load(PRICE) as z: independent=z['minimum_adjusted_price']
 with np.load(SEL) as z:
  all_ids=z['original_OD_index'];all_rel=z['release_step'];all_q=z['original_event_q_pce'];all_dest=z['destination_node_index']
 p=OUT/f'DEST_{args.destination}_ORIGINAL_PATHS.npz';meta=OUT/f'DEST_{args.destination}_RESULT.json';cert=OUT/f'DEST_{args.destination}_INDEPENDENT_CERT.json';rowfile=OUT/f'DEST_{args.destination}_INDEPENDENT_CAPACITY_ROWS.npz'
 if cert.exists() or rowfile.exists():raise FileExistsError('independent destination certificate exists')
 record=json.loads(meta.read_text(encoding='utf-8-sig'))
 if record['paths_npz_sha256']!=sha(p) or record['source_hashes']!=hashes:raise ValueError('producer path/source drift')
 with np.load(p) as z: arrays={k:z[k].copy() for k in z.files}
 positions=arrays['selection_position'];ids=arrays['original_OD_index'];releases=arrays['release_step'];q=arrays['original_event_q_pce'];off=arrays['edge_offset'];edge=arrays['original_edge_index'];entry=arrays['original_entry_step']
 if not np.array_equal(positions,np.flatnonzero(all_dest==args.destination)) or not np.array_equal(ids,all_ids[positions]) or not np.array_equal(releases,all_rel[positions]) or not np.array_equal(q,all_q[positions]):raise ValueError('selected event mapping drift')
 if len(off)!=len(ids)+1 or off[0]!=0 or off[-1]!=len(edge) or len(edge)!=len(entry) or np.any(np.diff(off)<0):raise ValueError('edge offset mapping')
 resource_rows=[];resource_offsets=[0];maxraw=maxadj=maxprice=0.;total_q=0.
 for j,i in enumerate(ids):
  i=int(i);release=int(releases[j]);orig=zones[od[i]['o_zone_id']];dest=zones[od[i]['d_zone_id']]
  if abs(float(od[i]['volume_pce'])/T-float(q[j]))>1e-12:raise ValueError('source original event demand')
  a=int(off[j]);b=int(off[j+1]);raw,adj,arrival,wait,rr=replay(net,physical,orig,dest,release,edge[a:b],entry[a:b],H,dt,tolls)
  if abs(raw-float(arrays['raw_cost'][j]))>1e-7 or abs(adj-float(arrays['adjusted_cost'][j]))>1e-7 or arrival!=int(arrays['arrival_step'][j]) or wait!=int(arrays['wait_count'][j]):raise ValueError('producer path replay mismatch')
  priced=float(independent[i,release]);err=abs(adj-priced)
  if err>1e-7:raise ValueError('not original full graph adjusted minimum')
  maxraw=max(maxraw,abs(raw-float(arrays['raw_cost'][j])));maxadj=max(maxadj,abs(adj-float(arrays['adjusted_cost'][j])));maxprice=max(maxprice,err);total_q+=float(q[j])
  resource_rows.extend(rr);resource_offsets.append(len(resource_rows))
 if len(resource_rows)==0:raise ValueError('no original physical resources')
 # Semantic negatives use the same original CSV replay: illegal time, edge, and hidden row must fail.
 j=0;i=int(ids[j]);a=int(off[j]);b=int(off[j+1]);orig=zones[od[i]['o_zone_id']];dest=zones[od[i]['d_zone_id']]
 tests={};base_edges=edge[a:b].copy();base_entry=entry[a:b].copy();base_rows=resource_rows[resource_offsets[j]:resource_offsets[j+1]]
 for name,ee,tt,rr in [('bad_original_edge',np.r_[len(net)+1,base_edges[1:]],base_entry,base_rows),('bad_time_mapping',base_edges,np.r_[base_entry[0]-1,base_entry[1:]],base_rows),('hidden_capacity_resource',base_edges,base_entry,base_rows[:-1])]:
  try:replay(net,physical,orig,dest,int(releases[j]),ee,tt,H,dt,tolls,rr)
  except ValueError:tests[name]='REJECTED'
  else:raise AssertionError('negative test accepted '+name)
 tmp=rowfile.with_suffix('.partial.npz')
 np.savez_compressed(tmp,selection_position=positions,original_capacity_offset=np.array(resource_offsets,np.int64),original_capacity_resource_rows=np.array(resource_rows,np.int64))
 os.replace(tmp,rowfile)
 result={'schema':'SHARED_CG_DEV22_INDEPENDENT_BATCH_ORIGINAL_CSV_REPLAY_R1','status':'PASS_EVERY_ORIGINAL_PATH_DEMAND_CAPACITY_PRICE_AND_NEGATIVES','destination_node_index':args.destination,'original_event_count':len(ids),'original_commodity_events':len(od)*T,'sum_selected_q_pce':total_q,'original_physical_resource_entries':len(resource_rows),'maximum_raw_cost_error':maxraw,'maximum_adjusted_cost_error':maxadj,'maximum_independent_price_error':maxprice,'semantic_negative_tests':tests,'source_hashes':hashes,'producer_result_sha256':sha(meta),'producer_path_npz_sha256':sha(p),'independent_price_profile_sha256':sha(PRICE),'capacity_rows_npz_sha256':sha(rowfile),'scope':'all selected paths separately replayed from original source CSV; no convergence claim'}
 tmpj=cert.with_suffix('.partial.json');tmpj.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');os.replace(tmpj,cert)
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
