"""Independent complete-original-graph verifier for shared uniform Q exact shortcut.

Reads original source CSV anew, runs forward Dijkstra by origin (producer uses
reverse trees by destination), checks every saved original edge/time path, and
sweeps exact release intervals over all used physical entry resources. A
nonnegative wait cost proves the static shortest lower bound for the full time
graph; a capacity-feasible shortest construction attains it.
"""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,heapq,json,math,numpy as np

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def verify(config_path):
 cp=Path(config_path);cfg=json.loads(cp.read_text(encoding='utf-8-sig'))
 if cfg['graph_type']!='uniform_release_implicit':raise ValueError('wrong Q graph type')
 output=Path(cfg['output_dir']);result=json.loads((output/'RESULT.json').read_text());identity=json.loads((output/'MODEL_IDENTITY.json').read_text())
 if result['status']!='SOLVER_PRIMAL_DUAL_CLOSED' or result['config_sha256']!=sha(cp):raise ValueError('Q producer not closed/identity')
 source=Path(cfg['source_dir']);names=('network.csv','access.csv','assignment_od_pce.csv')
 hashes={n:sha(source/n) for n in names}
 if hashes!=cfg['expected_source_hashes'] or hashes!=result['source_hashes'] or hashes!=identity['source_hashes']:
  raise ValueError('original Q source hash')
 net=read(source/'network.csv');acc=read(source/'access.csv');od=read(source/'assignment_od_pce.csv')
 zone={r['zone_id']:r['node_id'] for r in acc}
 if len(zone)!=len(acc):raise ValueError('duplicate Q access')
 nodes=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={n:i for i,n in enumerate(nodes)}
 u=np.array([ix[r['from_node_id']] for r in net],dtype=np.int32);v=np.array([ix[r['to_node_id']] for r in net],dtype=np.int32)
 cost=np.array([float(r['vdf_fftt']) for r in net]);cap=np.array([float(r['capacity']) for r in net]);
 physical=np.array([r[cfg['physical_field']]==cfg['physical_value'] for r in net],dtype=np.bool_)
 if np.any(cost<0) or np.any(cap<=0):raise ValueError('invalid original Q source edge')
 dt=float(cfg['dt_seconds']);T=int(cfg['release_steps']);H=int(cfg['horizon_steps']);factor=float(cfg['demand_factor'])
 if len(od)*T!=cfg['expected_commodity_events'] or abs(dt*T-3600)>1e-8:raise ValueError('Q release count')
 dur=np.where(physical,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(np.int32)),0)
 outgoing=[[] for _ in nodes]
 for e in range(len(net)):outgoing[int(u[e])].append(e)
 for es in outgoing:es.sort(key=lambda e:(float(cost[e]),net[e]['link_id']))
 origins=sorted({ix[zone[r['o_zone_id']]] for r in od});trees={}
 for origin in origins:
  dist=np.full(len(nodes),np.inf);dist[origin]=0.0;heap=[(0.0,origin)]
  while heap:
   d,n=heapq.heappop(heap)
   if d>dist[n]+1e-12:continue
   for e in outgoing[n]:
    nxt=int(v[e]);cand=d+float(cost[e])
    if cand<dist[nxt]-1e-12:dist[nxt]=cand;heapq.heappush(heap,(cand,nxt))
  trees[origin]=dist
 path=Path(result['path_file'])
 if sha(path)!=result['path_sha256']:raise ValueError('Q saved path SHA drift')
 a=np.load(path,allow_pickle=False);off=a['od_edge_offset'];edge=a['edge_index'];entry=a['entry_offset_steps'];pq=a['od_hourly_pce'];ps=a['od_static_shortest_cost']
 if len(off)!=len(od)+1 or len(pq)!=len(od) or len(edge)!=len(entry) or int(off[-1])!=len(edge):
  raise ValueError('Q saved path shape')
 events=defaultdict(list);totalq=0.0;primal=0.0;lower=0.0;maxarrival=0;max_q_residual=0.0
 for i,row in enumerate(od):
  original_q=float(row['volume_pce'])*factor
  max_q_residual=max(max_q_residual,abs(original_q-float(pq[i])))
  if original_q<=0 or max_q_residual>1e-9:raise ValueError('Q original OD q mismatch')
  origin=ix[zone[row['o_zone_id']]];dest=ix[zone[row['d_zone_id']]];node=origin;t=0;value=0.0
  if int(off[i])<0 or int(off[i+1])<int(off[i]) or int(off[i+1])>len(edge):raise ValueError('Q path offsets')
  for j in range(int(off[i]),int(off[i+1])):
   e=int(edge[j])
   if e<0 or e>=len(net) or int(u[e])!=node or int(entry[j])!=t:raise ValueError('Q original edge/time mapping')
   value+=float(cost[e]);node=int(v[e])
   if physical[e]:
    amount=original_q/T;events[e].append((t,amount));events[e].append((t+T,-amount))
   t+=int(dur[e])
  if node!=dest or t+T-1>H:raise ValueError('Q hidden late/unserved release')
  shortest=float(trees[origin][dest])
  if not math.isfinite(shortest) or abs(shortest-value)>1e-7 or abs(shortest-float(ps[i]))>1e-7:
   raise ValueError('Q complete original graph shortest path')
  totalq+=original_q;primal+=original_q*value;lower+=original_q*shortest;maxarrival=max(maxarrival,t+T-1)
 worst=0.0;worste=None;worstt=None;worstload=0.0;over=0
 for e,ev in events.items():
  ev.sort(key=lambda z:z[0]);at=0;load=0.0;top=0.0;top_t=0
  while at<len(ev):
   now=ev[at][0];delta=0.0
   while at<len(ev) and ev[at][0]==now:delta+=ev[at][1];at+=1
   load+=delta
   if load>top:top=load;top_t=now
  ratio=top/(cap[e]*dt/3600)
  if ratio>1+1e-9:over+=1
  if ratio>worst:worst=ratio;worste=net[e]['link_id'];worstt=top_t;worstload=top
 gap=(primal-lower)/max(1,abs(primal))
 if abs(primal-result['phase_II_objective'])>1e-6 or abs(lower-result['full_graph_lower_bound'])>1e-6:
  raise ValueError('Q producer objective mismatch')
 status='PASS_FULL_GRAPH' if over==0 and gap<=float(cfg['relative_gap_tolerance']) and max_q_residual<=1e-9 and maxarrival<=H else 'OPEN_FULL_GRAPH'
 cert={'schema':'SHARED_CG_Q_UNIFORM_INDEPENDENT_FULL_GRAPH_CERT_R1','status':status,'case_id':cfg['case_id'],'build_id':cfg['build_id'],
  'original_source_hashes':hashes,'original_positive_OD':len(od),'original_release_commodity_events':len(od)*T,
  'all_original_edges':len(net),'all_original_physical_arcs':int(np.count_nonzero(physical)),
  'all_original_physical_entry_rows':int(np.count_nonzero(physical))*H,
  'original_hourly_pce':totalq,'original_primal_objective':primal,'independent_full_graph_lower_bound':lower,
  'relative_gap_raw':gap,'maximum_original_capacity_ratio':worst,'overcapacity_original_physical_edges':over,
  'worst_original_physical_edge_id':worste,'worst_entry_step':worstt,'worst_step_load_pce':worstload,
  'max_original_OD_hourly_demand_residual':max_q_residual,'all_original_release_events_served':True,
  'max_release_plus_path_arrival_step':maxarrival,'path_sha256':result['path_sha256'],
  'proof_method':'independent original-source forward Dijkstra lower bound; every original edge/time path and all exact uniform release intervals checked; wait cost nonnegative; full physical time-entry capacity feasible'}
 out=output/'INDEPENDENT_CERTIFICATE.json';out.write_text(json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:cert[k] for k in ('case_id','status','original_release_commodity_events','original_primal_objective','relative_gap_raw','maximum_original_capacity_ratio')},ensure_ascii=False))
 return 0 if status=='PASS_FULL_GRAPH' else 2
def main():
 a=argparse.ArgumentParser();a.add_argument('--config',required=True);args=a.parse_args()
 return verify(args.config)
if __name__=='__main__':raise SystemExit(main())
