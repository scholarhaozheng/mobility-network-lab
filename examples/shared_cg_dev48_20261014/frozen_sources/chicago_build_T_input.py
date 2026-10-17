"""Input-only exact time expansion; streamed interval union avoids a tuple set.

The physical/time/capacity semantics follow the accepted corrected R1 builder.
No optimization kernel, LP state, or other-city path enters this input adapter.
"""
from pathlib import Path
import csv,datetime,hashlib,heapq,json,math,shutil,sys,time
import psutil
W=Path(__file__).resolve().parent
FIELDS=['arc_id','from_node_time_id','to_node_time_id','from_physical_node_id','to_physical_node_id','from_time','to_time','arc_type','physical_link_id','cost','capacity']
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8')
def distance(source,adj):
    d={source:0};heap=[(0,source)]
    while heap:
        du,u=heapq.heappop(heap)
        if du!=d[u]:continue
        for v,dt in adj.get(u,[]):
            alt=du+dt
            if alt<d.get(v,math.inf):d[v]=alt;heapq.heappush(heap,(alt,v))
    return d
def merge(intervals):
    result=[]
    for lo,hi in sorted(intervals):
        if hi<lo:continue
        if result and lo<=result[-1][1]+1:result[-1][1]=max(hi,result[-1][1])
        else:result.append([lo,hi])
    return result
def main():
    started=time.monotonic();ident=json.loads((W/'INPUT_IDENTITY.json').read_text());plan=json.loads((W/'EXPERIMENT_PLAN.json').read_text());pre=json.loads((W/'RESOURCE_PREFLIGHT.json').read_text())
    selected=ident['T_selected_od'];H=plan['T_policy']['H_steps'];dep=5;dt=30
    out=W/'runs/T_case';out.mkdir(parents=True,exist_ok=False)
    links=rows(W/'input/static/link.csv');physical=[];nodes=set();adj={};rev={}
    for r in links:
        u,v=r['from_node_id'],r['to_node_id'];tau=max(1,math.ceil(float(r['vdf_fftt'])*60/dt))
        physical.append((u,v,tau,r));nodes.update([u,v]);adj.setdefault(u,[]).append((v,tau));rev.setdefault(v,[]).append((u,tau))
    reach=[]
    for r in selected:
        o,d=r['origin_node'],r['destination_node'];do,dd=distance(o,adj),distance(d,rev)
        assert do[d]==r['rounded_shortest_steps'];reach.append((o,d,do,dd,do[d]))
    total=sum(r['volume_pce']/12 for r in selected);counts={k:0 for k in ['movement','waiting','source_connector','sink_connector']};nodebits={};physical_support=set();process=psutil.Process();peak=process.memory_info().rss
    def monitor():
        nonlocal peak
        peak=max(peak,process.memory_info().rss)
        if peak>plan['memory_ceiling_bytes']:raise MemoryError('input builder exceeded frozen memory ceiling')
    with (out/'dynamic_arc.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');writer.writeheader()
        def emit(a,ni,nj,u,v,t,t2,kind,lid,c,cap):
            writer.writerow(dict(zip(FIELDS,[a,ni,nj,u,v,t,t2,kind,lid,repr(c),repr(cap)])));counts[kind]+=1
            if kind not in ('source_connector','sink_connector'):
                nodebits[u]=nodebits.get(u,0)|(1<<t);nodebits[v]=nodebits.get(v,0)|(1<<t2)
            elif kind=='source_connector':nodebits[v]=nodebits.get(v,0)|(1<<t2)
            else:nodebits[u]=nodebits.get(u,0)|(1<<t)
        # Same order as sorted accepted ('m', physical-index, time) / ('w', node-index, time).
        for j,(u,v,tau,r) in enumerate(physical):
            intervals=merge([(dep+do[u],H-tau-dd[v]) for o,d,do,dd,s in reach if u in do and v in dd])
            if intervals:physical_support.add(r['link_id'])
            for lo,hi in intervals:
                for t in range(lo,hi+1):emit(f"arc_{r['link_id']}_t{t}",f'n{u}_t{t}',f'n{v}_t{t+tau}',u,v,t,t+tau,'movement',r['link_id'],float(r['vdf_fftt']),float(r['capacity'])*dt/3600)
            if j%1000==0:monitor()
        for j,u in enumerate(sorted(nodes)):
            intervals=merge([(dep+do[u],H-1-dd[u]) for o,d,do,dd,s in reach if u in do and u in dd])
            for lo,hi in intervals:
                for t in range(lo,hi+1):emit(f'wait_{u}_t{t}',f'n{u}_t{t}',f'n{u}_t{t+1}',u,u,t,t+1,'waiting','',.5,total)
            if j%1000==0:monitor()
        for k,(o,d,do,dd,s) in enumerate(reach):
            did=f'T{k+1:02d}';q=selected[k]['volume_pce']/12
            emit('source_'+did,f'source_{did}_t{dep}',f'n{o}_t{dep}',o,o,dep,dep,'source_connector','',0.,q)
            for t in range(dep+s,H+1):emit(f'sink_{did}_{d}_t{t}',f'n{d}_t{t}',f'sink_{did}_t{H}',d,d,t,H,'sink_connector','',0.,q)
    demands=[{'demand_id':f'T{i+1:02d}','origin_node_id':r['origin_node'],'destination_node_id':r['destination_node'],'departure_time':dep,'volume':repr(r['volume_pce']/12)} for i,r in enumerate(selected)]
    with (out/'dynamic_demand.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(demands[0]),lineterminator='\n');wr.writeheader();wr.writerows(demands)
    with (out/'dynamic_node.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.writer(f,lineterminator='\n');wr.writerow(['node_time_id','physical_node_id','time'])
        for u in sorted(nodebits):
            for t in range(H+1):
                if nodebits[u]&(1<<t):wr.writerow([f'n{u}_t{t}',u,t])
        for k,(o,d,*_) in enumerate(reach):
            did=f'T{k+1:02d}';wr.writerow([f'source_{did}_t{dep}',o,dep]);wr.writerow([f'sink_{did}_t{H}',d,H])
    shutil.copyfile(W/'input/static/link.csv',out/'physical_link.csv')
    arcsha=sha(out/'dynamic_arc.csv');demsha=sha(out/'dynamic_demand.csv');signature=hashlib.sha256((arcsha+'|'+demsha).encode()).hexdigest()
    manifest={'schema_version':'cross_city_lagrangian_case_v1','adapter':'finite_dynamic_csv_v1','case_id':'CHICAGO_JANE_BYRNE_R2_T4_dt30','city':'Chicago Jane Byrne / West Loop','arc_file':'dynamic_arc.csv','demand_file':'dynamic_demand.csv','arc_sha256':arcsha,'demand_sha256':demsha,'physical_link_file':'physical_link.csv','physical_link_sha256':sha(out/'physical_link.csv'),'physical_link_id_column':'link_id','objective_unit':'pce_minutes','capacity_unit':'pce_per_30sec_step','time_step_seconds':dt,'model_signature':signature}
    save(out/'case_manifest.json',manifest)
    exact=sum(counts.values());upper=pre['T4']['dynamic_arc_union_upper'];exact_connectors=sum(H-dep-r['rounded_shortest_steps']+2 for r in selected)
    assert exact==upper-len(selected)*(H+2)+exact_connectors
    receipt={'status':'BUILT_INPUT_ONLY','profile':'T4','model_signature':signature,'signature_rule':'sha256(sha256(ordered arc CSV)|sha256(ordered demand CSV))','H_steps':H,'H_minutes':H/2,'dt_seconds':dt,'departure_step':dep,'demand_q_pce':total,'arc_counts':counts,'arcs':exact,'dynamic_nodes':sum(n.bit_count() for n in nodebits.values())+2*len(selected),'physical_support_links':len(physical_support),'original_links':len(links),'original_nodes':len(nodes),'OD_rounded_shortest_steps':[r[-1] for r in reach],'peak_sampled_rss_bytes':peak,'input_build_seconds':time.monotonic()-started,'optimizer_calls':0,'semantics':plan['T_policy'],'exact_pruning':'exact union of forward/reverse rounded source-sink reachability intervals; all times in closed merged intervals; no finite path restriction','union_proof':'integer interval union is identical to set union of each commodity arc-time domain; adjacent intervals can be merged without adding a missing integer','node_order':'deterministic physical node then integer time; nodes do not change ordered arc/demand signature','core_loader_resource_gate_pending':True,'hashes':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
    save(out/'BUILD_RECEIPT.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()
