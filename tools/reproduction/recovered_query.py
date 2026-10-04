"""Reproduce a bounded query of the already published city-evidence tables."""
import argparse, csv, json, subprocess, sys
from pathlib import Path

def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream: return list(csv.DictReader(stream))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['run','verify','inspect'])
    ap.add_argument('--repo-root',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--run',type=Path)
    ap.add_argument('--record',default='TOOL-CITY-EVIDENCE-QUERY')
    a=ap.parse_args(); root=a.repo_root.resolve(); out=a.run if a.action=='verify' else a.output
    if a.record!='TOOL-CITY-EVIDENCE-QUERY' or out is None: ap.error('Unknown record or missing output')
    if a.action!='verify':
        if out.exists() and any(out.iterdir()): raise ValueError('Output must be new or empty')
        out.mkdir(parents=True,exist_ok=True)
        p=subprocess.run([sys.executable,'-B',str(root/'tools/mcl_data.py'),'query-city','--name','Hong Kong','--country','CHN','--include-relations'],cwd=root,capture_output=True,text=True,check=True)
        value=json.loads(p.stdout)
        (out/'query.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    value=json.loads((out/'query.json').read_text(encoding='utf-8'))
    cities=rows(root/'docs/data/open-mobility/city_evidence.csv')
    relations=rows(root/'docs/data/open-mobility/source_content_city.csv')
    expected=[r for r in cities if r['city_name']=='Hong Kong' and r['country_iso3']=='CHN']
    expected_relations=[r for r in relations if r['city_id']==expected[0]['city_id']]
    canonical=lambda values: sorted(json.dumps(r,sort_keys=True) for r in values)
    checks={'query_identity':value['query']=={'city_name':'Hong Kong','country':'CHN'},
            'unique_match':value['status']=='matched_unique' and value['match_count']==len(expected)==1,
            'exact_city_row':value['matches']==expected,
            'exact_relations':canonical(value['relationships'])==canonical(expected_relations),
            'relation_counts':value['relationship_count']==value['relationships_returned']==len(expected_relations)==2,
            'not_truncated':value['relationships_truncated'] is False}
    report={'success':all(checks.values()),'optimizer_calls':0,'checks':checks,
            'metrics':{'city_rows':len(cities),'relation_rows':len(relations),'matching_cities':len(expected),'matching_relations':len(expected_relations)},
            'scope':'Queries existing public evidence tables. Does not reacquire GTFS or rebuild the global collection.'}
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2)); return 0 if report['success'] else 2

if __name__=='__main__':raise SystemExit(main())
