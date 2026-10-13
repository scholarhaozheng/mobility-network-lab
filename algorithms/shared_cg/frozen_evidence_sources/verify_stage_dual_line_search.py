"""Independently certify lower bounds along zero-to-checkpoint capacity duals.

The saved RMP dual is not accepted at face value. Rebuild the complete original
time graph from source CSV; for each nonpositive scaled capacity multiplier,
recompute every destination/time potential and verify all legal arc inequalities.
Every sampled bound is valid even if the checkpoint is not globally optimal.
"""
from pathlib import Path
import argparse,csv,datetime,hashlib,heapq,json,math
import numpy as np
from verify_implicit_recompute import independent_reverse_distance,potential_residual
R=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 a=argparse.ArgumentParser();a.add_argument('--config',required=True);a.add_argument('--checkpoint',required=True)
 a.add_argument('--alphas',default='0,0.015625,0.03125,0.0625,0.125,0.25,0.5,1')
 a.add_argument('--output',required=True);args=a.parse_args()
 cfgp=Path(args.config);cfg=json.loads(cfgp.read_text(encoding='utf-8-sig'))
 if cfg['graph_type']!='implicit' or cfg['demand_factor']!=2.0 or cfg['case_id'] not in ('urbana_S2_H','pittsburgh_S2_H'):
  raise ValueError('registered H S2 only')
 rec=json.loads(Path(args.checkpoint).read_text(encoding='utf-8'))
 if rec['phase']!='II' or rec['config_sha256']!=sha(cfgp):raise ValueError('checkpoint config identity')
 rmp_path=Path(rec['rmp_path']);pool_path=Path(rec['pool_path'])
 if sha(rmp_path)!=rec['rmp_sha256'] or sha(pool_path)!=rec['pool_sha256']:raise ValueError('stage SHA drift')
 source=Path(cfg['source_dir']);names=('network.csv','access.csv','assignment_od_pce.csv')
 hashes={n:sha(source/n) for n in names}
 if hashes!=cfg['expected_source_hashes']:raise ValueError('original input SHA drift')
 net=read(source/'network.csv');acc=read(source/'access.csv');od=read(source/'assignment_od_pce.csv')
 zone={r['zone_id']:r['node_id'] for r in acc}
 if len(zone)!=len(acc):raise ValueError('duplicate zone mapping')
 node_ids=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={n:i for i,n in enumerate(node_ids)}
 u=np.array([ix[r['from_node_id']] for r in net],dtype=np.int32)
 v=np.array([ix[r['to_node_id']] for r in net],dtype=np.int32)
 cost=np.array([float(r['vdf_fftt']) for r in net],dtype=np.float64)
 physical=np.array([r['arc_kind']=='physical' for r in net],dtype=np.bool_)
 if np.any(~np.isfinite(cost)) or np.any(cost<0):raise ValueError('invalid original edge cost')
 dt=float(cfg['dt_seconds']);H=int(cfg['horizon_steps']);T=int(cfg['release_steps'])
 duration=np.array([max(1,math.ceil(cost[e]*60/dt-1e-12)) if physical[e] else 0 for e in range(len(net))],dtype=np.int32)
 pidx=np.full(len(net),-1,dtype=np.int32);phys=np.flatnonzero(physical);pidx[phys]=np.arange(len(phys),dtype=np.int32)
 cap=np.array([float(net[e]['capacity'])*dt/3600 for e in phys],dtype=np.float64)
 if np.any(cap<=0) or len(od)*T!=cfg['expected_commodity_events']:raise ValueError('capacity or full OD count')
 q=np.repeat(np.array([float(r['volume_pce'])*float(cfg['demand_factor'])/T for r in od],dtype=np.float64),T)
 origins=np.repeat(np.array([ix[zone[r['o_zone_id']]] for r in od],dtype=np.int32),T)
 dests=np.repeat(np.array([ix[zone[r['d_zone_id']]] for r in od],dtype=np.int32),T)
 release=np.tile(np.arange(T,dtype=np.int32),len(od))
 if np.any(q<=0):raise ValueError('nonpositive original demand')
 zero=[[] for _ in node_ids];indegree=np.zeros(len(node_ids),dtype=np.int32)
 for e in range(len(net)):
  if duration[e]==0:zero[int(u[e])].append(e);indegree[int(v[e])]+=1
 heap=[i for i in range(len(node_ids)) if indegree[i]==0];heapq.heapify(heap);topo=[]
 while heap:
  node=heapq.heappop(heap);topo.append(node)
  for e in zero[node]:
   nxt=int(v[e]);indegree[nxt]-=1
   if indegree[nxt]==0:heapq.heappush(heap,nxt)
 if len(topo)!=len(node_ids):raise ValueError('original zero-time cycle')
 ptr=np.zeros(len(node_ids)+1,dtype=np.int32);flat=[]
 for node,es in enumerate(zero):ptr[node]=len(flat);flat.extend(es)
 ptr[-1]=len(flat);flat=np.asarray(flat,dtype=np.int32);rev=np.asarray(topo[::-1],dtype=np.int32)
 with np.load(rmp_path,allow_pickle=False) as rmp:
  rows=rmp['capacity_rows'];mu=rmp['capacity_dual']
  if str(rmp['phase'][0])!='II':raise ValueError('wrong stage phase')
 if len(rows)!=len(mu) or len(np.unique(rows))!=len(rows) or np.any(rows<0) or np.any(rows>=len(phys)*H) or np.any(mu>1e-8):
  raise ValueError('invalid original capacity dual')
 alpha_list=[float(x) for x in args.alphas.split(',')]
 if not alpha_list or any(not math.isfinite(x) or x<0 or x>1 for x in alpha_list):raise ValueError('alpha range')
 sampled=[]
 for alpha in alpha_list:
  dense=np.zeros(len(phys)*H,dtype=np.float64);dense[rows]=alpha*mu
  lower=float(np.dot(cap[rows//H],alpha*mu));worst=0.0;bad_reach=0
  for dest in sorted(set(dests)):
   phi=independent_reverse_distance(len(node_ids),H,int(dest),u,v,duration,cost,pidx,ptr,flat,rev,dense,dt/60)
   violation,bad=potential_residual(phi,H,dt,u,v,duration,cost,pidx,dense)
   worst=max(worst,float(violation));bad_reach+=int(bad)
   ids=np.flatnonzero(dests==dest);start=phi[release[ids],origins[ids]]
   if np.any(~np.isfinite(start)):raise ValueError('hidden unreachable commodity')
   lower+=float(np.dot(q[ids],start))
  if worst>1e-7 or bad_reach:raise ValueError('full original graph dual invalid')
  sampled.append({'alpha':alpha,'certified_full_original_graph_lower_bound':lower,
                  'maximum_all_arc_inequality_violation':worst,'bad_reachability_arc_count':bad_reach})
  print(json.dumps(sampled[-1]),flush=True)
 best=max(sampled,key=lambda x:x['certified_full_original_graph_lower_bound'])
 primal_cert_path=Path(cfg['output_dir'])/'STAGE_CHECKPOINT_INDEPENDENT_PRIMAL_CERTIFICATE.json'
 primal_cert=json.loads(primal_cert_path.read_text(encoding='utf-8'))
 if primal_cert['status']!='PASS_ORIGINAL_PRIMAL_FEASIBLE_OPEN_DUAL' or primal_cert['checkpoint_round']!=rec['round'] or primal_cert['checkpoint_rmp_sha256']!=rec['rmp_sha256'] or primal_cert['checkpoint_pool_sha256']!=rec['pool_sha256']:
  raise ValueError('no matching independent original-graph primal certificate')
 upper=float(primal_cert['original_primal_objective'])
 cert={'schema':'SHARED_CG_S2_H_INDEPENDENT_DUAL_LINE_CERT_R1','status':'VALID_FULL_ORIGINAL_GRAPH_DUAL_LOWER_OPEN_OPTIMALITY',
  'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_id':cfg['case_id'],
  'original_source_hashes':hashes,'config_path':str(cfgp),'config_sha256':sha(cfgp),
  'stage_checkpoint':str(args.checkpoint),'stage_checkpoint_sha256':sha(args.checkpoint),
  'rmp_sha256':rec['rmp_sha256'],'pool_sha256':rec['pool_sha256'],'checkpoint_round':rec['round'],'independent_primal_certificate':str(primal_cert_path),'independent_primal_certificate_sha256':sha(primal_cert_path),
  'original_commodity_events':len(q),'full_original_physical_time_entry_rows':len(phys)*H,
  'sampled_dual_scalings':sampled,'best_certified_lower':best['certified_full_original_graph_lower_bound'],
  'best_alpha':best['alpha'],'separately_independently_certified_primal_upper':upper,
  'relative_open_gap':(upper-best['certified_full_original_graph_lower_bound'])/max(1,abs(upper)),
  'proof':'Each alpha scales nonpositive original-capacity dual; full time-DAG potentials independently recomputed from original source and all travel/turn/wait/sink inequalities checked. Each sampled Lagrangian bound is valid. Primal upper requires separate stage path audit.'}
 Path(args.output).write_text(json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'best_alpha':cert['best_alpha'],'lower':cert['best_certified_lower'],'upper':upper,'gap':cert['relative_open_gap']}),flush=True)
if __name__=='__main__':main()


