#!/usr/bin/env python3
"""Check the public source tree, local documentation links and catalog paths."""
from __future__ import annotations
import argparse
import ast
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publication',action='store_true',help='Also require a confirmed repository URL and root license')
    args=parser.parse_args()
    errors=[];warnings=[];checks=0
    paths=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ('.git','.venv','results','outputs'))]
    for p in paths:
        relative=p.relative_to(ROOT).as_posix()
        if p.suffix.lower() in ('.zip','.pyc','.exe','.dll','.7z') or '__pycache__' in p.parts:
            errors.append(f'Unexpected public payload: {relative}')
        if p.suffix=='.py':
            try:ast.parse(p.read_text(encoding='utf-8-sig'));checks+=1
            except SyntaxError as exc:errors.append(f'{relative}: {exc}')
        if p.suffix in ('.md','.html','.json','.txt','.py','.cff'):
            text=p.read_text(encoding='utf-8-sig')
            if p.name not in ('check_repository.py',) and any(x in text for x in ('SuperDoctorCat','/mnt/data/','C:\\Users\\')):
                errors.append(f'Private machine path in {relative}')
        if p.suffix in ('.md','.html'):
            text=p.read_text(encoding='utf-8-sig')
            prose_text=re.sub(r'<script type="application/json"[^>]*>.*?</script>','',text,flags=re.DOTALL)
            if re.search(r'[\u4e00-\u9fff]',prose_text):errors.append(f'Non-English public page: {relative}')
            # The README and documentation use plain relative links without spaces.
            refs=re.findall(r'(?:href|src)=["\']([^"\']+)',text) if p.suffix=='.html' else re.findall(r'\]\(([^)]+)\)',text)+re.findall(r'(?:href|src)=["\']([^"\']+)',text)
            for raw in refs:
                raw=html.unescape(raw)
                if raw.startswith(('http:','https:','mailto:','#','data:')):continue
                target=unquote(raw.split('#',1)[0])
                if not target:continue
                resolved=(p.parent/target).resolve()
                if not resolved.exists():errors.append(f'Broken local link: {relative} -> {raw}')
                checks+=1
    source=json.loads((ROOT/'catalog/source-files.json').read_text())
    for row in source['files']:
        p=ROOT/row['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            errors.append(f'Retained source changed without provenance update: {row["path"]}')
        checks+=1
    catalog=json.loads((ROOT/'catalog/datasets.json').read_text())
    seen=set()
    for row in catalog['datasets']:
        if row['id'] in seen:errors.append(f'Duplicate dataset ID: {row["id"]}')
        seen.add(row['id'])
        if not (ROOT/row['data_page']).is_file():errors.append(f'Missing data card: {row["id"]}')
        if row['access']=='bundled-input':
            for key in ('input','config'):
                if not (ROOT/row[key]).exists():errors.append(f'Missing {key}: {row["id"]}')
        checks+=1
    project=json.loads((ROOT/'catalog/project.json').read_text())
    if not project.get('repository_url'):
        (errors if args.publication else warnings).append('Repository URL has not been set; local rendering is available.')
    if not any((ROOT/name).is_file() for name in ('LICENSE','LICENSE.md','LICENSE.txt')):
        (errors if args.publication else warnings).append('The maintainer must select and authorize a root code license before public release.')
    if args.publication:
        for name in ('THIRD_PARTY_NOTICES.md','DATA_LICENSES.md','requirements-data-tools.txt','requirements-data-tools-tested.txt','catalog/open-data-evidence.json','catalog/open-data-products.json','catalog/omdv-provenance.json','catalog/omdv-authorized-files.json','schemas/catalog-city-quality-report.schema.json','docs/open-data.md','docs/open-data-explorer.md','docs/open-data-sources.md','docs/gtfs-zip-tool.md','docs/data-tools.md','docs/architecture.md','docs/data/open-mobility/city_evidence.csv','docs/data/open-mobility/city_evidence_schema.json','docs/data/open-mobility/content_city.csv','docs/data/open-mobility/content_city_schema.json','docs/data/open-mobility/source_content_city.csv','docs/data/open-mobility/source_content_city_schema.json','examples/data-tools/feeds_sample.csv','examples/data-tools/external_city_universe_sample.csv'):
            if not (ROOT/name).is_file():errors.append(f'Missing publication rights notice: {name}')
        try:
            products=json.loads((ROOT/'catalog/open-data-products.json').read_text(encoding='utf-8'))
            for product in products['products']:
                target=ROOT/product['path']
                if not target.is_file():errors.append(f'Missing open-data product: {product["path"]}')
                elif hashlib.sha256(target.read_bytes()).hexdigest()!=product['sha256']:
                    errors.append(f'Open-data product hash mismatch: {product["path"]}')
                checks+=1
            if products['checks'].get('city_rows')!=11422:
                errors.append('Open-data product catalog does not retain 11,422 city rows.')
        except Exception as exc:
            errors.append(f'Open-data product catalog failed validation: {exc}')
        try:
            from mobilitylab.data.evidence import load_evidence_catalog
            load_evidence_catalog()
            checks+=1
        except Exception as exc:
            errors.append(f'Open-data evidence catalog failed validation: {exc}')
        if project.get('title')!='Mobility Computation Lab':
            errors.append('Public product title is not Mobility Computation Lab.')
    result={'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors,'warnings':warnings,'publication_checks':args.publication}
    print(json.dumps(result,indent=2))
    return 0 if not errors else 1

if __name__=='__main__':raise SystemExit(main())
