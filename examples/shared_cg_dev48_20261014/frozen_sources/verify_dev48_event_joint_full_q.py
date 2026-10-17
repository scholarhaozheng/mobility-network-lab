"""Independent original CSV Bellman audit of the dev48 cold-source full-Q price profile."""
from pathlib import Path
from collections import deque
import csv,hashlib,json,math,time
import numpy as np
from verify_dev22_batch_rmp_dual_price import independent_values
R=Path(__file__).resolve().parent
ROOT=R/'runs/dev48_event_joint_cg_urbana_f';OUT=ROOT/'FULL_PRICE'
CASE=R/'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,obj):
 t=p.with_suffix('.partial.json');t.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');t.replace(p)
def csvrows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 began=time.monotonic();result=json.loads((OUT/'RESULT.json').read_text(encoding='utf-8'))
 cfg=json.loads(CASE.read_text(encoding='utf-8-sig'));source=Path(cfg['source_dir'])
 hashes={name:sha(source/name) for name in cfg['expected_source_hashes']}
 if hashes!=cfg['expected_source_hashes'] or hashes!=result['source_hashes']:
  raise ValueError('original source drift')
 if result['RMP_independent_cert_sha256']!=sha(ROOT/'INDEPENDENT_CERT.json'):
  raise ValueError('different independently accepted RMP')
 with np.load(ROOT/'FINAL_RMP.npz') as z:rows=z['original_rows'];mu=z['capacity_mu']
 if len(rows)!=len(mu) or np.any(mu>1e-8):raise ValueError('dual row/sign')
 lam=np.maximum(-mu,0.)
 H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
 net=csvrows(source/'network.csv');access=csvrows(source/'access.csv');od=csvrows(source/'assignment_od_pce.csv')
 nodes=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net});ix={v:i for i,v in enumerate(nodes)}
 zone={r['zone_id']:ix[r['node_id']] for r in access}
 positive=[];zero=[[] for _ in nodes];indeg=np.zeros(len(nodes),dtype=np.int32);physical_edges=[]
 for e,arc in enumerate(net):
  u=ix[arc['from_node_id']];v=ix[arc['to_node_id']];cost=float(arc['vdf_fftt'])
  if arc[cfg['physical_field']]==cfg['physical_value']:
   dur=max(1,math.ceil(cost*60/dt-1e-12));positive.append((u,v,cost,dur,e));physical_edges.append(e)
  else:zero[u].append((v,cost));indeg[v]+=1
 queue=deque(int(j) for j in np.flatnonzero(indeg==0));topo=[]
 while queue:
  node=queue.popleft();topo.append(node)
  for v,c in zero[node]:
   indeg[v]-=1
   if indeg[v]==0:queue.append(v)
 if len(topo)!=len(nodes):raise ValueError('original zero-time cycle')
 zp=np.r_[0,np.cumsum([len(v) for v in zero])].astype(np.int32)
 zh=np.array([v for group in zero for v,c in group],dtype=np.int32)
 zc=np.array([c for group in zero for v,c in group],dtype=np.float64)
 posedge=np.array([e for u,v,c,d,e in positive],dtype=np.int32)
 priced=np.unique(rows[lam>0]//H);priced_original=[physical_edges[int(p)] for p in priced]
 toll=np.zeros((len(priced_original),H),dtype=np.float64);pmap={e:j for j,e in enumerate(priced_original)}
 for resource,value in zip(rows,lam):
  if value>0:
   e=physical_edges[int(resource//H)];t=int(resource%H);toll[pmap[e],t]=float(value)
 pid=np.array([pmap.get(int(e),-1) for e in posedge],dtype=np.int32)
 pu=np.array([u for u,v,c,d,e in positive],np.int32)
 pv=np.array([v for u,v,c,d,e in positive],np.int32)
 pc=np.array([c for u,v,c,d,e in positive],np.float64)
 pdur=np.array([d for u,v,c,d,e in positive],np.int32)
 destinations=sorted({zone[r['d_zone_id']] for r in od})
 hourly=np.array([float(r['volume_pce'])*float(cfg['demand_factor']) for r in od])
 if len(od)*T!=result['original_release_events']:raise ValueError('original commodity count')
 weighted=0.;maximum=0.;stages=[]
 for number,dest in enumerate(destinations):
  ids=np.array([i for i,r in enumerate(od) if zone[r['d_zone_id']]==dest],np.int32)
  origins=np.array([zone[od[i]['o_zone_id']] for i in ids],np.int32)
  t0=time.monotonic()
  values=independent_values(len(nodes),H,T,dt,int(dest),origins,pu,pv,pc,pdur,pid,toll,zp,zh,zc,np.asarray(topo[::-1],np.int32))
  p=OUT/f'DEST_{dest:05d}.npz'
  with np.load(p) as z:producer=z['price_by_release'];producer_ids=z['od_indices']
  if not np.array_equal(ids,producer_ids) or producer.shape!=values.shape or not np.all(np.isfinite(values)):
   raise ValueError('producer omitted original event')
  difference=float(np.max(abs(values-producer)));maximum=max(maximum,difference)
  if difference>1e-7:raise ValueError('original full-graph price mismatch')
  weighted+=float(np.dot(hourly[ids]/T,np.sum(values,axis=1)))
  stages.append({'destination':int(dest),'OD':len(ids),'events':len(ids)*T,'max_price_difference':difference,'seconds':time.monotonic()-t0})
  save(OUT/'INDEPENDENT_STAGE.json',{'status':'IN_PROGRESS' if number+1<len(destinations) else 'ALL_DESTINATIONS_VERIFIED','producer_result_sha256':sha(OUT/'RESULT.json'),'completed':stages})
  print(json.dumps({'independent_complete':number+1,'of':len(destinations),'dest':int(dest),'difference':difference}),flush=True)
 cap=np.array([float(a['capacity'])*dt/3600 for a in net])
 term=float(sum(cap[physical_edges[int(r//H)]]*value for r,value in zip(rows,lam)))
 lower=weighted-term
 if abs(lower-result['valid_full_original_lower'])>1e-5 or lower>result['independently_feasible_RMP_upper']+1e-6:
  raise ValueError('original dual lower mismatch')
 cert={'schema':'DEV48_INDEPENDENT_FULL_ORIGINAL_Q_PRICE_CERT','status':'PASS_FULL_ORIGINAL_DUAL_OPEN_CG_GAP',
  'case_id':cfg['case_id'],'source_hashes':hashes,'producer_result_sha256':sha(OUT/'RESULT.json'),
  'RMP_independent_cert_sha256':sha(ROOT/'INDEPENDENT_CERT.json'),
  'original_OD':len(od),'original_release_events':len(od)*T,'destinations_verified':len(destinations),
  'max_independent_price_difference':maximum,'independent_full_original_lower':lower,
  'independent_feasible_upper':result['independently_feasible_RMP_upper'],
  'relative_open_gap':(result['independently_feasible_RMP_upper']-lower)/result['independently_feasible_RMP_upper'],
  'wall_seconds':time.monotonic()-began,'scope':'One exact original Q dual snapshot, not CG closure.'}
 save(OUT/'INDEPENDENT_DUAL_CERT.json',cert)
 print(json.dumps({k:cert[k] for k in ('status','independent_full_original_lower','independent_feasible_upper','relative_open_gap','wall_seconds')}),flush=True)
if __name__=='__main__':main()


