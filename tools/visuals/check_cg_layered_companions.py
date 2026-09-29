#!/usr/bin/env python3
"""Check saved companion figures, exact edge tables and already-released path records.
No solver is imported. --source-root may point to REFERENCE_INPUTS in the handoff.
"""
from pathlib import Path
import argparse,csv,hashlib,json,xml.etree.ElementTree as ET

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    a.add_argument('--source-root',type=Path)
    args=a.parse_args();root=args.repo_root.resolve();src=(args.source_root or root).resolve()
    out=root/'docs/assets/cg_layered_companions_r1';m=json.loads((out/'DISPLAY_INPUTS.json').read_text(encoding='utf-8'))
    checks=[]
    for rel,h in m['input_hashes'].items():
        p=src/rel
        assert p.is_file(),f'Missing source {p}'
        assert digest(p)==h,f'Source identity mismatch: {rel}'
        checks.append('source:'+rel)
    for city,path in [('boston','docs/assets/boston/space_time_cg_r4/data/construction_path_arcs.csv'),('hong_kong','docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv')]:
        rp=rows(src/path);look={r['arc_id']:r for r in rp}
        if city=='boston':look.update({r['arc_id']:r for r in rows(src/'docs/assets/three_city_r2/data/boston_construction_edges.csv')})
        for e in rows(out/f'{city}_display_edges.csv'):
            q=look[e['arc_id']]
            for k in ['arc_id','arc_type','from_physical_node_id','to_physical_node_id','from_time','to_time','physical_link_id']:
                assert e[k]==q.get(k,''),(city,e['arc_id'],k)
            checks.append(city+':arc:'+e['arc_id'])
        stem=city+'_layered_space_time_construction';j=json.loads((out/(stem+'.source.json')).read_text(encoding='utf-8'))
        for suffix,key in [('.png','png_sha256'),('.svg','svg_sha256')]:
            assert digest(out/(stem+suffix))==j[key],f'Image hash mismatch: {stem+suffix}'
        assert digest(root/'tools/visuals/render_cg_layered_companions.py')==j['renderer_sha256']
        assert digest(out/'DISPLAY_INPUTS.json')==j['display_inputs_sha256']
        assert digest(out/f'{city}_display_states.csv')==j['display_states_sha256']
        assert digest(out/f'{city}_display_edges.csv')==j['display_edges_sha256']
        svg=ET.parse(out/(stem+'.svg'))
        plotted=[e.attrib['data-arc-id'] for e in svg.iter() if 'data-arc-id' in e.attrib]
        assert sorted(plotted)==sorted(j['displayed_arc_ids'])
        assert not list(svg.iter('{http://www.w3.org/2000/svg}image')),'SVG must not embed a generated raster'
        assert j['scientific_solver_calls']==0
        checks.append(city+':SVG/PNG/renderer/state checks')
    print(json.dumps({'status':'PASS','checks':len(checks),'details':checks,'optimizer_calls':0},indent=2))
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (AssertionError,KeyError,FileNotFoundError) as e:
        import sys
        print(f'VALIDATION FAILED: {e}',file=sys.stderr);raise SystemExit(1)
