"""Independent all-destination original-time Bellman audit of dev22 batch RMP dual prices.

Reads original CSV and saved dual; does not import rolling_price or any
producer pricing function. Positive-time arcs are relaxed in a separate
pass; zero-time arcs use a fresh topological order.
"""
from pathlib import Path
from hashlib import sha256
from collections import deque
import csv,json,math,time,numpy as np
from numba import njit
R=Path(__file__).resolve().parent
OUT=R/'runs/dev22_batch_rmp_dual_price_urbana_f'
RMP=R/'runs/dev22_batch_event_rmp_urbana_f'
CASE=R/'cases/urbana_F_Q__sparse_common_dev20_rolling_path_recovery.json'

@njit(cache=True)
def independent_values(n,H,T,dt,dest,origins,pu,pv,pc,pdur,pid,toll,
                       zero_ptr,zero_head,zero_cost,reverse):
    D=int(np.max(pdur));ring=np.full((D+1,n),np.inf,dtype=np.float64)
    answer=np.empty((len(origins),T),dtype=np.float64)
    slots=D+1
    for t in range(H,-1,-1):
        slot=t%slots
        for node in range(n):
            ring[slot,node]=0.0 if node==dest else (dt/60.0+ring[(t+1)%slots,node] if t<H else np.inf)
        for e in range(len(pu)):
            d=pdur[e]
            if t+d>H:continue
            value=pc[e]+ring[(t+d)%slots,pv[e]]
            p=pid[e]
            if p>=0:value+=toll[p,t]
            if value<ring[slot,pu[e]]:ring[slot,pu[e]]=value
        for k in range(n):
            node=reverse[k]
            for j in range(zero_ptr[node],zero_ptr[node+1]):
                value=zero_cost[j]+ring[slot,zero_head[j]]
                if value<ring[slot,node]:ring[slot,node]=value
        if t<T:
            for k in range(len(origins)):
                answer[k,t]=ring[slot,origins[k]]
    return answer

def sha(path):
    h=sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    tmp.replace(path)
def rows_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    result=json.loads((OUT/'RESULT.json').read_text(encoding='utf-8-sig'))
    cfg=json.loads(CASE.read_text(encoding='utf-8-sig'))
    source=Path(cfg['source_dir'])
    hashes={name:sha(source/name) for name in cfg['expected_source_hashes']}
    if hashes!=cfg['expected_source_hashes'] or hashes!=result['source_hashes']:
        raise ValueError('original Q source identity')
    if sha(RMP/'INDEPENDENT_CERT.json')!=result['RMP_cert_sha256']:
        raise ValueError('different RMP dual snapshot')
    with np.load(RMP/'NEW_RESTRICTED_RMP_ROWS_AND_DUAL.npz') as z:
        rows=z['original_resource_rows'];mu=z['capacity_dual']
    if np.any(mu>1e-8):raise ValueError('capacity dual sign')
    lam=np.maximum(-mu,0.0)
    H=int(cfg['horizon_steps']);T=int(cfg['release_steps']);dt=float(cfg['dt_seconds'])
    net=rows_csv(source/'network.csv');access=rows_csv(source/'access.csv');od=rows_csv(source/'assignment_od_pce.csv')
    nodes=sorted({r['from_node_id'] for r in net}|{r['to_node_id'] for r in net})
    ix={v:i for i,v in enumerate(nodes)}
    zone={r['zone_id']:ix[r['node_id']] for r in access}
    positive=[];zero=[[] for _ in nodes];indeg=np.zeros(len(nodes),dtype=np.int32)
    physical_edges=[]
    for e,arc in enumerate(net):
        u=ix[arc['from_node_id']];v=ix[arc['to_node_id']]
        cost=float(arc['vdf_fftt'])
        if arc[cfg['physical_field']]==cfg['physical_value']:
            dur=max(1,math.ceil(cost*60/dt-1e-12))
            positive.append((u,v,cost,dur,e))
            physical_edges.append(e)
        else:
            zero[u].append((v,cost));indeg[v]+=1
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
    pos_edge=np.array([e for u,v,c,d,e in positive],dtype=np.int32)
    priced_physical=np.unique(rows[lam>0]//H)
    priced_original=[physical_edges[int(p)] for p in priced_physical]
    toll=np.zeros((len(priced_original),H),dtype=np.float64)
    pmap={e:j for j,e in enumerate(priced_original)}
    physical_pos={e:p for p,e in enumerate(physical_edges)}
    for resource,value in zip(rows,lam):
        if value<=0:continue
        p=int(resource//H);t=int(resource%H);e=physical_edges[p]
        toll[pmap[e],t]=float(value)
    pid=np.array([pmap.get(int(e),-1) for e in pos_edge],dtype=np.int32)
    pu=np.array([u for u,v,c,d,e in positive],np.int32)
    pv=np.array([v for u,v,c,d,e in positive],np.int32)
    pc=np.array([c for u,v,c,d,e in positive],np.float64)
    pdur=np.array([d for u,v,c,d,e in positive],np.int32)
    destination_nodes=sorted({zone[r['d_zone_id']] for r in od})
    with np.load(OUT/'ALL_ORIGINAL_OD_RELEASE_PRICE_VALUES.npz') as z:
        producer=z['minimum_adjusted_price']
    if producer.shape!=(len(od),T):
        raise ValueError('producer hidden OD/release')
    full=np.empty_like(producer)
    hourly=np.array([float(r['volume_pce']) for r in od],dtype=np.float64)
    if len(od)*T!=result['original_commodity_events']:
        raise ValueError('original event coverage')
    began=time.monotonic();stages=[];maximum=0.0
    for number,dest in enumerate(destination_nodes):
        ids=np.array([i for i,r in enumerate(od) if zone[r['d_zone_id']]==dest],np.int32)
        origins=np.array([zone[od[i]['o_zone_id']] for i in ids],np.int32)
        t0=time.monotonic()
        values=independent_values(len(nodes),H,T,dt,int(dest),origins,
                                  pu,pv,pc,pdur,pid,toll,zp,zh,zc,
                                  np.asarray(topo[::-1],np.int32))
        if not np.all(np.isfinite(values)):
            raise ValueError('independent unreachable original event')
        full[ids]=values
        difference=float(np.max(np.abs(values-producer[ids])))
        maximum=max(maximum,difference)
        stages.append({'destination_node_index':int(dest),'original_OD_count':len(ids),
                       'original_event_count':len(ids)*T,'max_price_difference':difference,
                       'independent_value_sha256':sha256(values.tobytes()).hexdigest(),
                       'wall_seconds':time.monotonic()-t0})
        save(OUT/'INDEPENDENT_PRICE_STAGE_RECEIPT.json',
             {'schema':'SHARED_CG_DEV22_BATCH_RMP_INDEPENDENT_PRICE_STAGES_R1',
              'status':'IN_PROGRESS' if number+1<len(destination_nodes) else 'ALL_DESTINATIONS_INDEPENDENTLY_PRICED',
              'completed':stages,'producer_result_sha256':sha(OUT/'RESULT.json')})
        print(json.dumps({'independent_completed':number+1,'of':len(destination_nodes),
                          'dest':int(dest),'max_difference':difference}),flush=True)
    if maximum>1e-7:raise ValueError('producer and independent complete graph price differ')
    cap=np.array([float(a['capacity'])*dt/3600 for a in net])
    term=float(sum(cap[physical_edges[int(r//H)]]*v for r,v in zip(rows,lam)))
    weighted=float(np.dot(hourly/T,np.sum(full,axis=1)))
    lower=weighted-term
    if abs(lower-result['full_original_graph_dual_lower_bound'])>1e-5:
        raise ValueError('independent original dual lower mismatch')
    if lower>result['independent_same_build_feasible_upper']+1e-6:
        raise ValueError('invalid original lower bound')
    path=OUT/'INDEPENDENT_ALL_ORIGINAL_PRICE_VALUES.npz'
    np.savez_compressed(path,minimum_adjusted_price=full)
    cert={'schema':'SHARED_CG_DEV22_BATCH_RMP_INDEPENDENT_FULL_ORIGINAL_Q_DUAL_PRICE_CERT_R1',
          'status':'PASS_ALL_ORIGINAL_COMMODITY_PRICES_VALID_DUAL_OPEN_GAP',
          'case_id':cfg['case_id'],'source_hashes':hashes,
          'producer_result_sha256':sha(OUT/'RESULT.json'),
          'RMP_cert_sha256':sha(RMP/'INDEPENDENT_CERT.json'),
          'original_OD_count':len(od),'original_commodity_events':len(od)*T,
          'destinations_independently_priced':len(destination_nodes),
          'maximum_independent_price_difference':maximum,
          'demand_weighted_independent_full_graph_minimum':weighted,
          'original_capacity_price_term':term,
          'independent_full_original_graph_dual_lower_bound':lower,
          'independently_feasible_same_build_upper':result['independent_same_build_feasible_upper'],
          'relative_open_gap':(result['independent_same_build_feasible_upper']-lower)/result['independent_same_build_feasible_upper'],
          'independent_profile_file':str(path),'independent_profile_file_sha256':sha(path),
          'wall_seconds':time.monotonic()-began,
          'scope':'all original Q full graph release prices and valid lower bound; full CG gap open'}
    save(OUT/'INDEPENDENT_DUAL_CERT.json',cert)
    print(json.dumps({k:cert[k] for k in ('status','destinations_independently_priced',
          'maximum_independent_price_difference','independent_full_original_graph_dual_lower_bound',
          'relative_open_gap','wall_seconds')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()




