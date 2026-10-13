"""Independent original-space certificate for explicit dynamic CSV path-CG.

This reader reconstructs every selected path and all shared original arc
capacities, then checks a complete saved node-potential inequality certificate.
It does not import the producer graph, pricing, or RMP implementation.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math
import numpy as np

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def rows(path):
 with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def verify(config_path):
 cfg=json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
 if cfg.get('graph_type')!='explicit':raise ValueError('not explicit config')
 out=Path(cfg['output_dir'])
 result=json.loads((out/'RESULT.json').read_text(encoding='utf-8'))
 identity=json.loads((out/'MODEL_IDENTITY.json').read_text(encoding='utf-8'))
 if result['status']!='SOLVER_PRIMAL_DUAL_CLOSED':raise ValueError('producer did not close')
 if result['config_sha256']!=sha(config_path):raise ValueError('config changed')
 manifest_path=Path(cfg['input_manifest'])
 manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
 arc_path=Path(manifest['dynamic_arc_file']);demand_path=Path(manifest['demand_file'])
 hashes={'dynamic_arc.csv':sha(arc_path),'dynamic_demand.csv':sha(demand_path)}
 if hashes!=cfg['expected_source_hashes'] or hashes!=identity['source_hashes']:
  raise ValueError('original explicit source hashes changed')
 arcs=rows(arc_path);demands=rows(demand_path)
 ids=[r['arc_id'] for r in arcs]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate original arc ID')
 nodes=sorted({r['from_node_time_id'] for r in arcs}|{r['to_node_time_id'] for r in arcs})
 nix={x:i for i,x in enumerate(nodes)}
 u=np.array([nix[r['from_node_time_id']] for r in arcs],dtype=np.int32)
 v=np.array([nix[r['to_node_time_id']] for r in arcs],dtype=np.int32)
 cost=np.array([float(r['cost']) for r in arcs],dtype=np.float64)
 cap=np.array([float(r['capacity']) for r in arcs],dtype=np.float64)
 from_time=np.array([int(r['from_time']) for r in arcs],dtype=np.int32)
 to_time=np.array([int(r['to_time']) for r in arcs],dtype=np.int32)
 if np.any(to_time<from_time):raise ValueError('source has backwards arc')
 byid={r['arc_id']:r for r in arcs}
 sources=[];targets=[];q=[]
 for d in demands:
  did=d['demand_id']
  s=byid.get('source_'+did)
  sinks={r['to_node_time_id'] for r in arcs if r['arc_type']=='sink_connector' and
         r['arc_id'].startswith('sink_'+did+'_')}
  if s is None or s['arc_type']!='source_connector' or len(sinks)!=1:
   raise ValueError('bad original demand connector '+did)
  sources.append(nix[s['from_node_time_id']])
  targets.append(nix[next(iter(sinks))])
  q.append(float(d['volume']))
 K=len(demands);M=len(arcs)
 if K!=cfg['expected_commodity_events'] or K!=identity['original_positive_demands']:
  raise ValueError('hidden explicit demand')
 q=np.array(q,dtype=np.float64)
 pool=np.load(out/'COLUMN_POOL.npz',allow_pickle=False)
 master=np.load(out/'LAST_RMP.npz',allow_pickle=False)
 commodity=pool['commodity'];col_cost=pool['cost'];roff=pool['resource_offset'];rflat=pool['resource_flat']
 poff=pool['edge_time_offset'];pflat=pool['edge_time_flat']
 x=master['x'];P=len(commodity)
 if str(master['phase'][0])!='II' or len(x)!=P:raise ValueError('not Phase II path primal')
 mu_rows=master['capacity_rows'];mu=master['capacity_dual']
 if (len(mu_rows)!=len(mu) or len(set(map(int,mu_rows)))!=len(mu_rows) or
     np.any(mu_rows<0) or np.any(mu_rows>=M) or np.any(mu>1e-8)):
  raise ValueError('bad full original capacity dual')
 dense=np.zeros(M,dtype=np.float64);dense[mu_rows]=mu
 flow=np.zeros(K,dtype=np.float64);loads=np.zeros(M,dtype=np.float64);objective=0.0
 max_path_cost_residual=0.0
 for j in range(P):
  k=int(commodity[j])
  if k<0 or k>=K:raise ValueError('unknown commodity')
  path=pflat[int(poff[j]):int(poff[j+1])]
  if len(path)%2 or not len(path):raise ValueError('bad path length')
  node=sources[k];value=0.0;resource=[]
  for edge,entry in zip(path[::2],path[1::2]):
   e=int(edge)
   if e<0 or e>=M or node!=int(u[e]) or int(entry)!=int(from_time[e]):
    raise ValueError('bad original arc mapping or path continuity')
   value+=float(cost[e]);resource.append(e);node=int(v[e])
  if node!=targets[k]:raise ValueError('path does not serve exact original demand')
  claimed=rflat[int(roff[j]):int(roff[j+1])]
  if not np.array_equal(claimed,np.array(resource,dtype=np.int32)):
   raise ValueError('path capacity resources omit/change an original arc')
  max_path_cost_residual=max(max_path_cost_residual,abs(value-float(col_cost[j])))
  f=float(x[j])
  if not math.isfinite(f) or f<-1e-8:raise ValueError('negative/nonfinite flow')
  flow[k]+=f;objective+=f*value
  if f>1e-11:
   for e in resource:loads[e]+=f
 residual=np.abs(flow-q)
 cap_excess=np.maximum(loads-cap,0.0)
 dual_lower=float(np.dot(cap[mu_rows],mu))
 potential_records=result.get('full_graph_potentials')
 if not potential_records or len(potential_records)!=len(set(targets)):
  raise ValueError('missing destination potential coverage')
 bydest={int(rec['destination_node_index']):rec for rec in potential_records}
 worst=0.0;bad_reachability=0
 for dest in sorted(set(targets)):
  rec=bydest.get(dest)
  if rec is None:raise ValueError('missing original sink potential')
  potpath=Path(rec['path'])
  if sha(potpath)!=rec['sha256']:raise ValueError('potential bytes changed')
  z=np.load(potpath,allow_pickle=False)
  phi=z['potential']
  if phi.shape!=(len(nodes),) or int(z['destination'][0])!=dest:
   raise ValueError('potential has wrong original graph identity')
  if phi[dest]>1e-8:raise ValueError('terminal sink dual exceeds zero')
  finite_u=np.isfinite(phi[u]);finite_v=np.isfinite(phi[v])
  bad_reachability+=int(np.count_nonzero(~finite_u&finite_v))
  mask=finite_u&finite_v
  if np.any(mask):
   worst=max(worst,float(np.max(phi[u[mask]]-(cost[mask]-dense[mask]+phi[v[mask]]))))
  served=np.array([k for k,t in enumerate(targets) if t==dest],dtype=np.int32)
  start=phi[np.array(sources,dtype=np.int32)[served]]
  if not np.all(np.isfinite(start)):raise ValueError('unreachable positive original demand')
  dual_lower+=float(np.dot(q[served],start))
 gap=(objective-dual_lower)/max(abs(objective),1e-12)
 cert={'schema':'SHARED_CG_EXPLICIT_INDEPENDENT_CERT_R1',
  'status':'PASS_FULL_GRAPH' if float(np.max(residual))<=1e-6 and
      float(np.max(residual/q))<=float(cfg.get('release_relative_tolerance',1e-4)) and
      float(np.max(cap_excess))<=1e-6 and max_path_cost_residual<=1e-7 and
      worst<=1e-7 and bad_reachability==0 and
      abs(gap)<=float(cfg['relative_gap_tolerance'])+1e-10 else 'OPEN_FULL_GRAPH',
  'source_hashes':hashes,'original_demands':K,'all_original_arcs':M,
  'all_shared_original_capacity_rows':M,'pool_columns':P,
  'max_original_demand_residual':float(np.max(residual)),
  'max_relative_demand_residual':float(np.max(residual/q)),
  'max_original_arc_capacity_excess':float(np.max(cap_excess)),
  'maximum_original_path_cost_residual':max_path_cost_residual,
  'maximum_full_graph_potential_inequality_violation':worst,
  'bad_finite_reachability_arc_count':bad_reachability,
  'original_objective':objective,'verified_full_graph_lower_bound':dual_lower,
  'relative_gap_raw':gap,'pricing_verifier':'every original dynamic arc plus every demand-specific source/sink mapping'}
 (out/'INDEPENDENT_CERTIFICATE.json').write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(cert,indent=2))
 return 0 if cert['status']=='PASS_FULL_GRAPH' else 2

def main():
 a=argparse.ArgumentParser();a.add_argument('--config',required=True);args=a.parse_args()
 return verify(args.config)
if __name__=='__main__':raise SystemExit(main())
