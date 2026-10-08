from pathlib import Path
import csv,json,hashlib,collections
import numpy as np
from shapely import wkt
from shapely.ops import transform,substring
from pyproj import Transformer
W=Path(__file__).resolve().parent;ROOT=W.parents[3]
RUN=ROOT/'work/urbana_champaign_algorithm_transfer_r1/runs/berkeley_c2a_transfer_r2'
CITY=ROOT/'work/six_city_preflight_r1/cities/urbana_champaign'
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:yield from csv.DictReader(f)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    paths={m:list(rows(RUN/f'T/{m}/positive_paths.csv')) for m in ['cg','lr']}
    byarc={m:collections.defaultdict(float) for m in paths}
    for m,pp in paths.items():
        for p in pp:
            for aid in json.loads(p.get('path_arc_ids_json',p.get('arc_ids_json'))):byarc[m][aid]+=float(p['flow'])
    ids=[]
    for p in paths['cg']:ids.extend(json.loads(p['path_arc_ids_json']))
    wanted=set(ids); details={}; totals={m:collections.defaultdict(float) for m in ['lp','cg','lr','admm']}
    with np.load(RUN/'T/admm_main/final_checkpoint/state.npz') as z:admm=z['x'].sum(axis=0)
    with np.load(RUN/'T/lp_dag/LP_SOLUTION.npz') as z:lp=np.bincount(z['var_a'],weights=z['x'],minlength=len(admm))
    ordered=hashlib.sha256(); arcf=RUN/'T/model/dynamic_arc.csv'; n=0
    for i,a in enumerate(rows(arcf)):
        n=i+1
        if a['arc_id'] in wanted:details[a['arc_id']]=a
        if a['arc_type']=='physical_road':
            gid=a['solver_link_id']; totals['admm'][gid]+=float(admm[i]); totals['lp'][gid]+=float(lp[i])
            for m in ['cg','lr']:totals[m][gid]+=byarc[m].get(a['arc_id'],0.0)
    assert n==len(admm)==1429496
    identity=json.loads((RUN/'T/admm_main/final_checkpoint/checkpoint_identity.json').read_text())
    assert sha(arcf)==identity['arc_sha256']
    plinks=list(rows(CITY/'four_stage/inputs/physical_link_map.csv'))
    gids=sorted(r['model_link_id'] for r in plinks); gs={r['gmns_link_id'] for r in plinks}
    tf=Transformer.from_crs(4326,26916,always_xy=True); sources={};geom={}
    for r in rows(CITY/'processed/gmns/link.csv'):
        if r['link_id'] in gs:
            sources[r['link_id']]=transform(tf.transform,wkt.loads(r['geometry']))
    assert set(sources)==gs
    for r in plinks:
        mid=r['model_link_id'];g=sources[r['gmns_link_id']];fraction=float(r['fraction_of_source_length'])
        if fraction<1:
            assert fraction==.5 and mid.endswith((':A',':B'))
            g=substring(g,0,.5,normalized=True) if mid.endswith(':A') else substring(g,.5,1,normalized=True)
        geom[mid]=[[x/1000,y/1000] for x,y in g.coords]
    xy=np.array([v for line in geom.values() for v in line]); origin=xy.min(axis=0)
    segments={k:(np.array(v)-origin).tolist() for k,v in geom.items()}
    static=collections.defaultdict(float); pmap={r['model_link_id']:r['gmns_link_id'] for r in plinks}
    for r in rows(RUN/'S/fw_fast_72_r2/link_flow.csv'):
        if r['link_id'] in pmap:static[r['link_id']]+=float(r['flow_pce_per_period'])
    data={'gids':gids,'source_gmns_ids':[pmap[k] for k in gids],'segments':[segments[k] for k in gids],'physical_solver_arcs':len(plinks),'unique_gmns_geometries':len(gs),'T_physical_solver_arcs':len(totals['lp']),
      'projection':'EPSG:4326 to EPSG:26916, local km from southwest model extent',
      'physical_projection':'Sum own saved physical traversal flow over time and commodities by solver_link_id. Split A/B physical arcs use their separate source-geometry halves; serial partial arcs are not summed into a full-road volume. Turns/waits/connectors excluded. Uninstantiated T arcs have storage-placeholder zeros with in_t=false and appear only as gray geographic context; they are not solved zero-flow arcs.',
      'in_t':[k in totals['lp'] for k in gids],'flows':{m:[totals[m].get(k,0.0) for k in gids] for m in totals},'static':[static.get(k,0.0) for k in gids],
      'cg_paths':[{**p,'arcs':[details[aid] for aid in json.loads(p['path_arc_ids_json'])]} for p in paths['cg']],
      'max_admm_lp_physical_difference':max(abs(totals['admm'].get(k,0)-totals['lp'].get(k,0)) for k in gids)}
    (W/'derived.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    sources=[arcf,RUN/'T/admm_main/final_checkpoint/state.npz',RUN/'T/lp_dag/LP_SOLUTION.npz',RUN/'T/cg/positive_paths.csv',RUN/'T/lr/positive_paths.csv',CITY/'processed/gmns/link.csv',CITY/'four_stage/inputs/physical_link_map.csv']
    (W/'DERIVATION.json').write_text(json.dumps({'status':'PASS','solver_calls':0,'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sources},'T_arc_count':n,'physical_solver_arcs':len(plinks),'physical_solver_geometries':len(gids),'unique_source_geometries':len(gs),'max_admm_lp_difference':data['max_admm_lp_physical_difference']},indent=2),encoding='utf8')
    print('Derived',n,'T arcs',len(gids),'physical geometries',data['max_admm_lp_physical_difference'])
if __name__=='__main__':main()
