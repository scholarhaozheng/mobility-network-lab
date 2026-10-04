"""Build the preregistered cohort on the accepted 30-second corridor contract."""
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from space_time_capacity_problem_contract import load,shortest_path

def rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(path,data):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

policy=json.loads((R/'HK_ADMM_R3_HOLDOUT_SELECTION_POLICY.json').read_text())
assert policy['status']=='FROZEN_INPUT_ONLY_BEFORE_ANY_FRESH_LP_OR_ADMM_SOLVE'
assert policy['selected_canonical_sha256']==hashlib.sha256(json.dumps(policy['selected'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
old=R/'inputs/old_hk10'
arcs=rows(old/'dynamic_arc.csv')
base=[a for a in arcs if a['arc_type'] not in ('source_connector','sink_connector')]
old_demand=rows(old/'dynamic_demand.csv')
old_keys={(x['origin_node_id'],x['destination_node_id'],int(float(x['departure_time']))) for x in old_demand}
assert all((x['origin'],x['destination'],x['departure_step']) not in old_keys for x in policy['selected'])
old_total=sum(float(x['volume']) for x in old_demand)
new_total=sum(x['declared_demand'] for x in policy['selected'])
assert new_total<old_total
large=old_total+1.0
horizon=50
out=R/'inputs/fresh_hk_holdout'
out.mkdir(parents=True,exist_ok=True)
demands=[]
for i,x in enumerate(policy['selected'],1):
    did=f'R3H{i:02d}'
    o,d=x['origin'],x['destination']
    t=int(x['departure_step'])
    assert t==0
    q=x['declared_demand']
    demands.append({'demand_id':did,'origin_node_id':o,'destination_node_id':d,
                    'departure_time':t,'volume':q})
    source=arcs[0].copy()
    source.update({'arc_id':f'source_{did}','from_node_time_id':f'source_{did}_t{t}',
                   'to_node_time_id':f'n{o}_t{t}',
                   'from_physical_node_id':f'source_{did}', 'to_physical_node_id':o,
                   'from_time':t,'to_time':t,'arc_type':'source_connector',
                   'physical_link_id':'','cost':0.0,'capacity':q})
    base.append(source)
    for step in range(horizon+1):
        sink=arcs[0].copy()
        sink.update({'arc_id':f'sink_{did}_{d}_t{step}',
                     'from_node_time_id':f'n{d}_t{step}',
                     'to_node_time_id':f'sink_{did}_t{horizon}',
                     'from_physical_node_id':d,'to_physical_node_id':f'sink_{did}',
                     'from_time':step,'to_time':horizon,'arc_type':'sink_connector',
                     'physical_link_id':'','cost':0.0,'capacity':large})
        base.append(sink)
write(out/'dynamic_arc.csv',base)
write(out/'dynamic_demand.csv',demands)
shutil.copyfile(old/'selected_physical_links.csv',out/'selected_physical_links.csv')
p=load(out/'dynamic_arc.csv',out/'dynamic_demand.csv')
reach=[]
for k in range(len(demands)):
    distance,path=shortest_path(p,k,p['cost'])
    reach.append({'demand_id':demands[k]['demand_id'],'shortest_path_cost':distance,'path_arc_count':len(path)})
signature=hashlib.sha256((out/'dynamic_arc.csv').read_bytes()+b'\0'+(out/'dynamic_demand.csv').read_bytes()).hexdigest()
identity={'status':'FROZEN_INPUT_INSTANCE','case_id':'HK_R3_FRESH_4OD_30S_50STEPS',
          'model_signature':signature,'arc_sha256':sha(out/'dynamic_arc.csv'),
          'demand_sha256':sha(out/'dynamic_demand.csv'),
          'physical_link_sha256':sha(out/'selected_physical_links.csv'),
          'selected_canonical_sha256':policy['selected_canonical_sha256'],
          'dynamic_nodes':len(p['nodes']),'dynamic_arcs':len(p['ids']),
          'od_count':len(demands),'demand_total_pce':new_total,
          'time_step_seconds':30,'horizon_steps':50,
          'cost_unit':'vehicle_minutes','capacity_unit':'PCE_per_30s_movement_departure',
          'source_graph':'accepted Hong Kong R2-R4 corridor; unchanged movement/turn/zone/wait arc rows; only commodity connectors replaced',
          'reachability':reach}
(R/'HK_ADMM_R3_FRESH_INSTANCE_IDENTITY.json').write_text(json.dumps(identity,indent=2)+'\n')
print(json.dumps({k:v for k,v in identity.items() if k!='reachability'}))
