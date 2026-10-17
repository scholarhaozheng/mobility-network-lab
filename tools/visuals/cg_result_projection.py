"""Project actual saved CG path flows; never solve or substitute historical flows.

These numerical decoders retain the prior publication's original-path replay,
with input paths supplied explicitly by the current run's workspace index.
"""
from pathlib import Path
from collections import defaultdict,Counter
import json,csv,hashlib
import numpy as np
from numba import njit
from scipy import sparse

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def csvrows(p):
 with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))

@njit(cache=False)
def paths(commodity,x,poff,pflat,roff,rflat,colcost,u,v,cost,duration,pidx,H,dt,orig,dest,release,explicit,fromtime,q,nrows):
 loads=np.zeros(nrows);edgeflow=np.zeros(len(cost));served=np.zeros(len(q));objective=0.;maxerr=0.;maxarrival=0
 for j in range(len(x)):
  f=x[j]
  assert np.isfinite(f) and f>=-1e-8
  if f==0:continue
  k=commodity[j];node=orig[k];t=release[k];val=0.;ri=roff[j]
  for z in range(poff[j],poff[j+1],2):
   e=pflat[z];entry=pflat[z+1]
   if e==-2:
    assert not explicit and entry==t and t<H
    t+=1;val+=dt/60
   else:
    assert e>=0 and e<len(cost) and u[e]==node
    if explicit:
     assert entry==fromtime[e]
     resource=e;t=fromtime[e]+duration[e]
    else:
     assert entry==t and t+duration[e]<=H
     resource=pidx[e]*H+t if pidx[e]>=0 else -1;t+=duration[e]
    if resource>=0:
     assert ri<roff[j+1] and rflat[ri]==resource
     loads[resource]+=f;ri+=1
    val+=cost[e];edgeflow[e]+=f;node=v[e]
  assert node==dest[k] and ri==roff[j+1]
  if not explicit:assert t<=H
  maxarrival=max(maxarrival,t);maxerr=max(maxerr,abs(val-colcost[j]));objective+=f*val;served[k]+=f
 return edgeflow,loads,served,objective,maxerr,maxarrival

def arrays(p):
 with np.load(p,allow_pickle=False)as z:return {k:z[k]for k in z.files}
def binding(p):return {'path':str(p),'sha256':sha(p)}
def graph(cfg):
 net=csvrows(Path(cfg['source_dir'])/'network.csv');od=csvrows(Path(cfg['source_dir'])/'assignment_od_pce.csv')
 access={r['zone_id']:r['node_id']for r in csvrows(Path(cfg['source_dir'])/'access.csv')}
 ids=sorted({r['from_node_id']for r in net}|{r['to_node_id']for r in net});ix={k:i for i,k in enumerate(ids)}
 u=np.array([ix[r['from_node_id']]for r in net]);v=np.array([ix[r['to_node_id']]for r in net]);cost=np.array([float(r['vdf_fftt'])for r in net])
 phys=np.array([r[cfg.get('physical_field','arc_kind')]==cfg.get('physical_value','physical')for r in net]);pe=np.flatnonzero(phys);pidx=np.full(len(net),-1);pidx[pe]=np.arange(len(pe))
 dt=cfg['dt_seconds'];dur=np.where(phys,np.maximum(1,np.ceil(cost*60/dt-1e-12).astype(int)),0)
 origins=np.array([ix[access[r['o_zone_id']]]for r in od]);dests=np.array([ix[access[r['d_zone_id']]]for r in od]);hourly=np.array([float(r['volume_pce'])*cfg['demand_factor']for r in od])
 return net,od,access,u,v,cost,phys,pe,pidx,dur,origins,dests,hourly

def regular(c,cfg):
 paths_index=c['paths'];out=Path(paths_index['result']).parent
 poolp=Path(paths_index.get('column_pool',out/'COLUMN_POOL.npz'));rmpp=Path(paths_index.get('rmp',out/'LAST_RMP.npz'))
 checkpoint=paths_index.get('latest_checkpoint')
 if checkpoint and Path(checkpoint).is_file():
  cp=read(checkpoint);poolp=Path(cp['pool_path']);rmpp=Path(cp['rmp_path'])
  assert sha(poolp)==cp['pool_sha256'] and sha(rmpp)==cp['rmp_sha256']
  cert=read(paths_index['independent_certificate'])
  assert sha(poolp)==cert['checkpoint_pool_sha256'] and sha(rmpp)==cert['checkpoint_rmp_sha256']
 pool=arrays(poolp);rmp=arrays(rmpp);x=rmp['x'];K=cfg['expected_commodity_events']
 assert str(rmp['phase'][0])=='II' and len(x)==len(pool['commodity'])==len(pool['cost'])
 explicit=cfg['graph_type']=='explicit'
 if explicit:
  m=read(cfg['input_manifest']);net=csvrows(m['dynamic_arc_file']);od=csvrows(m['demand_file']);nodes=sorted({r['from_node_time_id']for r in net}|{r['to_node_time_id']for r in net});ix={k:i for i,k in enumerate(nodes)}
  u=np.array([ix[r['from_node_time_id']]for r in net]);v=np.array([ix[r['to_node_time_id']]for r in net]);cost=np.array([float(r['cost'])for r in net]);fromtime=np.array([int(r['from_time'])for r in net]);dur=np.array([int(r['to_time'])-int(r['from_time'])for r in net]);cap=np.array([float(r['capacity'])for r in net])
  byid={r['arc_id']:i for i,r in enumerate(net)};sinks=defaultdict(set)
  for r in net:
   if r['arc_type']=='sink_connector':
    for d in od:
     if r['arc_id'].startswith('sink_'+d['demand_id']+'_'):sinks[d['demand_id']].add(r['to_node_time_id']);break
  assert all(len(sinks[d['demand_id']])==1 for d in od)
  orig=np.array([u[byid['source_'+d['demand_id']]]for d in od]);dest=np.array([ix[next(iter(sinks[d['demand_id']]))]for d in od]);q=np.array([float(d['volume'])for d in od]);release=np.zeros(K,dtype=int);H=int(max(int(r['to_time'])for r in net));dt=float(c['dt_seconds']or 1);pidx=np.arange(len(net));nr=len(net)
 else:
  net,od,access,u,v,cost,phys,pe,pidx,dur,oo,dd,hourly=graph(cfg);H=cfg['horizon_steps'];T=cfg['release_steps'];dt=cfg['dt_seconds'];orig=np.repeat(oo,T);dest=np.repeat(dd,T);q=np.repeat(hourly/T,T);release=np.tile(np.arange(T),len(od));fromtime=np.zeros(len(net),dtype=int);cap=np.repeat(np.array([float(net[e]['capacity'])*dt/3600 for e in pe]),H);nr=len(cap)
 assert len(q)==K
 ef,loads,served,U,err,arrival=paths(pool['commodity'],x,pool['edge_time_offset'],pool['edge_time_flat'],pool['resource_offset'],pool['resource_flat'],pool['cost'],u,v,cost,dur,pidx,H,dt,orig,dest,release,explicit,fromtime,q,nr)
 residual=float(np.max(abs(served-q)));relative=float(np.max(abs(served-q)/q));excess=float(np.max(loads-cap,initial=0))
 assert err<=1e-7 and residual<=1e-6 and relative<=cfg.get('release_relative_tolerance',1e-4)+1e-10 and excess<=1e-6,(c['case_id'],err,residual,relative,excess)
 sums=defaultdict(float)
 for e,r in enumerate(net):
  if (r.get('arc_type')=='movement')if explicit else(r[cfg.get('physical_field','arc_kind')]==cfg.get('physical_value','physical')):
   ident=r['physical_link_id']if explicit else r['link_id'];assert ident;sums[ident]+=float(ef[e])
 return dict(sums),U,{'total_demand':float(q.sum()),'served_demand':float(served.sum()),'max_demand_residual':residual,'max_relative_demand_residual':relative,'max_original_entry_capacity_excess':excess,'max_path_cost_error':err,'positive_path_columns':int(np.count_nonzero(x>0)),'solved_columns':len(x),'horizon_steps':H,'max_arrival_step':int(arrival),'pool':binding(poolp),'rmp':binding(rmpp)},[poolp,rmpp]

def replay(u,v,cost,dur,pidx,origin,destination,release,edge,entry,H,dt):
 node=int(origin);t=int(release);value=0.;wait=0;rows=[]
 for ee,tt in zip(edge,entry):
  e=int(ee);tt=int(tt);assert 0<=e<len(cost) and tt>=t and u[e]==node and tt+dur[e]<=H
  wait+=tt-t;value+=(tt-t)*dt/60+cost[e]
  if pidx[e]>=0:rows.append(int(pidx[e]*H+tt))
  t=tt+int(dur[e]);node=int(v[e])
 assert node==destination
 return value,t,wait,rows

def base_paths(c,cfg,a,net,u,v,cost,pe,pidx,dur,oo,dd,hourly):
 assert len(a['od_hourly_pce'])==len(hourly)and np.max(abs(a['od_hourly_pce']-hourly))<1e-9
 ef=np.zeros(len(net));vals=[];events=defaultdict(list);T=cfg['release_steps'];H=cfg['horizon_steps'];dt=cfg['dt_seconds'];arrival=0
 for i,q in enumerate(hourly):
  lo,hi=a['od_edge_offset'][i:i+2];ee=a['edge_index'][lo:hi];tt=a['entry_offset_steps'][lo:hi]
  value,arr,w,rr=replay(u,v,cost,dur,pidx,oo[i],dd[i],0,ee,tt,H,dt)
  assert w==0 and abs(value-a['od_static_shortest_cost'][i])<1e-7 and arr+T-1<=H
  vals.append(value);arrival=max(arrival,arr+T-1);np.add.at(ef,ee,q)
  for e,t in zip(ee,tt):
   if pidx[e]>=0:events[int(e)].extend([(int(t),q/T),(int(t)+T,-q/T)])
 return ef,np.asarray(vals),events,arrival

def uniform(c,cfg):
 net,od,access,u,v,cost,phys,pe,pidx,dur,oo,dd,hourly=graph(cfg);p=Path(c['paths']['uniform_paths']);a=arrays(p)
 ef,values,events,arrival=base_paths(c,cfg,a,net,u,v,cost,pe,pidx,dur,oo,dd,hourly);maximum=0.;excess=0.
 for e,ev in events.items():
  merged=defaultdict(float)
  for t,q in ev:merged[t]+=q
  cap=float(net[e]['capacity'])*cfg['dt_seconds']/3600;load=0.
  for t,delta in sorted(merged.items()):load+=delta;maximum=max(maximum,load/cap);excess=max(excess,load-cap)
 assert excess<=1e-8
 U=float(np.dot(hourly,values));return {net[e]['link_id']:float(ef[e])for e in pe},U,{'total_demand':float(hourly.sum()),'served_demand':float(hourly.sum()),'max_demand_residual':float(np.max(abs(hourly-a['od_hourly_pce']))),'max_original_entry_capacity_excess':excess,'maximum_entry_capacity_ratio':maximum,'max_arrival_step':int(arrival),'horizon_steps':cfg['horizon_steps'],'release_events':len(od)*cfg['release_steps'],'trajectory_status':'NOT_APPLICABLE_UNIFORM_RELEASE_SHORTCUT'},[p]

def joint(c,cfg):
 net,od,access,u,v,cost,phys,pe,pidx,dur,oo,dd,hourly=graph(cfg);out=Path(c['paths']['result']).parent
 ap=Path(c['paths']['uniform_paths']);fp=Path(c['paths']['fifo_fragments']);initial=Path(c['paths']['initial_path_pool']).parent;seed=ap.parent.parent
 a=arrays(ap);f=arrays(fp);save=arrays(c['paths']['rmp']);ip=arrays(c['paths']['initial_path_pool']);new=arrays(c['paths']['new_path_pool'])
 H=cfg['horizon_steps'];T=cfg['release_steps'];dt=cfg['dt_seconds'];ef,values,events,arrival=base_paths(c,cfg,a,net,u,v,cost,pe,pidx,dur,oo,dd,hourly)
 # Waiting changes source timing/cost, never source route traversal totals.
 fod=f['od_index'];fr=f['release_step'];fm=f['mass_pce'];fw=f['wait_steps'];stages={int(e):i for i,e in enumerate(f['stage_original_edge_index'])};selected=set(map(int,f['selected_od_index']));nfrag=len(fod)
 for i in selected:
  mask=fod==i;mass=np.bincount(fr[mask],weights=fm[mask],minlength=T);assert len(mass)==T and np.max(abs(mass-hourly[i]/T))<=1e-9
 seedU=float(np.dot(hourly,values)+np.dot(fm,fw.sum(axis=1))*dt/60);seedcert=read(seed/'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json')
 assert abs(seedU-seedcert['independent_feasible_primal_upper'])<=1e-6
 y=save['flow'];group=save['column_group'];keys=save['group_key'];mass=save['group_mass'];signatures=save['column_signature'];used=np.bincount(group,weights=y,minlength=len(keys));remaining=mass-used
 assert len(y)==len(signatures)==len(save['delta_cost'])and np.min(y)>=-1e-8 and np.min(remaining)>=-1e-8
 assert len(set(map(int,keys)))==len(keys)and len(set(map(str,signatures)))==len(signatures)
 pos={str(s):(ip,j)for j,s in enumerate(ip['signature'])}
 for j,s in enumerate(new['signature']):pos.setdefault(str(s),(new,j))
 A=sparse.load_npz(c['paths']['state_matrix']).tocsc();rows=save['original_rows'];assert A.shape==(len(rows),len(y))
 deltas=np.zeros(len(y));maxerror=0.;positive=0;firstwait=0;maxarrival=arrival
 for j,sig in enumerate(signatures):
  pool,p=pos[str(sig)];key=int(keys[group[j]]);assert key==pool['source_event_key'][p]
  if key<nfrag:i=int(fod[key]);release=int(fr[key]);waitrow=fw[key];q=fm[key]
  else:i,release=divmod(key-nfrag,T);assert i not in selected;waitrow=None;q=hourly[i]/T
  assert abs(mass[group[j]]-q)<1e-12
  lo,hi=pool['edge_offset'][p:p+2];ee=pool['original_edge_index'][lo:hi];tt=pool['original_entry_step'][lo:hi]
  value,arr,wait,rr=replay(u,v,cost,dur,pidx,oo[i],dd[i],release,ee,tt,H,dt);maxarrival=max(maxarrival,arr);firstwait+=int(len(tt)>0 and tt[0]>release)
  lo,hi=a['od_edge_offset'][i:i+2];donor=a['edge_index'][lo:hi];oldrows=[];delay=0
  for e,t in zip(donor,a['entry_offset_steps'][lo:hi]):
   if waitrow is not None and e in stages:delay+=int(waitrow[stages[e]])
   if pidx[e]>=0:
    when=release+int(t)+delay;assert 0<=when<H;oldrows.append(int(pidx[e]*H+when))
  oldcost=values[i]+(0 if waitrow is None else waitrow.sum()*dt/60);deltas[j]=value-oldcost;maxerror=max(maxerror,abs(deltas[j]-save['delta_cost'][j]));assert maxerror<=1e-7
  delta=Counter(rr);delta.subtract(Counter(oldrows));delta={k:v for k,v in delta.items()if v}
  aa,bb=A.indptr[j:j+2];actual={int(rows[r]):float(vv)for r,vv in zip(A.indices[aa:bb],A.data[aa:bb])};assert actual==delta
  if y[j]!=0:np.add.at(ef,ee,y[j]);np.add.at(ef,donor,-y[j])
  positive+=int(y[j]>0)
 # Rebuild source entry flow at all changed rows; untouched rows retain the
 # exact independently certified full source flow, not zero.
 byedge=defaultdict(list)
 for j,row in enumerate(rows):p,t=divmod(int(row),H);byedge[int(pe[p])].append((t,j))
 base=np.zeros(len(rows));byod={i:np.flatnonzero(fod==i)for i in selected}
 for i in range(len(od)):
  prior=[];lo,hi=a['od_edge_offset'][i:i+2]
  for e,t in zip(a['edge_index'][lo:hi],a['entry_offset_steps'][lo:hi]):
   if e in stages:prior.append(stages[e])
   if e not in byedge:continue
   items=byedge[e];times=np.fromiter((x[0]for x in items),int);positions=np.fromiter((x[1]for x in items),int)
   if i in byod:
    ids=byod[i];delay=fw[ids][:,prior].sum(axis=1)if prior else 0;when=fr[ids]+int(t)+delay;assert np.min(when)>=0 and np.max(when)<H;base[positions]+=np.bincount(when,weights=fm[ids],minlength=H)[times]
   else:base[positions]+=(hourly[i]/T)*((times>=t)&(times<t+T))
 cap=np.array([float(net[e]['capacity'])*dt/3600 for e in pe]);caprows=cap[rows//H];assert np.max(abs(save['residual_capacity']-(caprows-base)),initial=0)<=1e-8
 loads=base+A@y;excess=float(np.max(loads-caprows,initial=0));assert excess<=1e-8 and np.min(loads,initial=0)>=-1e-8
 U=float(seedU+np.dot(deltas,y));assert np.min(ef[pe])>=-1e-8
 metric={'total_demand':float(hourly.sum()),'served_demand':float(hourly.sum()),'release_events':len(od)*T,'max_demand_residual':float(np.max(np.maximum(used-mass,0),initial=0)),'minimum_remaining_base_group_mass':float(remaining.min()),'minimum_replacement_mass':float(y.min()),'max_original_entry_capacity_excess':max(0.,excess),'max_path_cost_error':maxerror,'projected_base_objective':seedU,'recomputed_delta_objective':float(np.dot(deltas,y)),'solved_columns':len(y),'initial_columns':len(ip['signature']),'new_pool_offers':len(new['signature']),'selected_new_columns':len(y)-len(ip['signature']),'positive_replacement_columns':positive,'signature_join':'FINAL_RMP.column_signature -> INITIAL/NEW.signature; exact group and resource coefficients checked','unchanged_resource_proof':'Same-run full AON/FIFO independent source certificate; all changed original rows replayed here','max_arrival_step':int(maxarrival),'horizon_steps':H,'first_action_wait_paths':firstwait,'complete_flow':'Full source routes minus transferred donor mass plus selected replacement routes; repeated traversals preserved'}
 return {net[e]['link_id']:float(ef[e])for e in pe},U,metric,[ap,fp,seed/'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json',initial/'INITIAL_PATH_POOL.npz',out/'NEW_PATH_POOL.npz',out/'FINAL_RMP.npz',out/'STATE_MATRIX.npz']

