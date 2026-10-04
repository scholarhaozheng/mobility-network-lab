import csv,hashlib,json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parent;sid='CENSUS_STPUG_GEOMETRY'
endpoint='https://portal.csdi.gov.hk/server/rest/services/common/censtatd_rcd_1635933193720_58660/FeatureServer/0/query'
params={'f':'json','geometry':'114.164,22.295,114.181,22.312','geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects','where':'1=1','outFields':'*','outSR':'4326','returnGeometry':'true'}
url=endpoint+'?'+urllib.parse.urlencode(params);stamp=datetime.now(timezone.utc).isoformat();start=time.monotonic()
with urllib.request.urlopen(url,timeout=120) as f:data=f.read(20_000_001)
obj=json.loads(data)
if 'error' in obj:raise ValueError(obj['error'])
path=root/'raw/census_stpug_geometry.json';path.write_bytes(data)
sha=hashlib.sha256(data).hexdigest();size=len(data)
with (root/'DOWNLOAD_LOG.csv').open('a',encoding='utf-8',newline='') as f:csv.writer(f).writerow([sid,url,stamp,'ok',size,round(time.monotonic()-start,3),''])
with (root/'RAW_FILE_MANIFEST.csv').open('a',encoding='utf-8',newline='') as f:csv.writer(f).writerow([sid,str(path.relative_to(root)),size,sha,stamp])
with (root/'SOURCE_REGISTER.csv').open(encoding='utf-8',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
rows.append(dict(source_id=sid,provider='Census and Statistics Department',official_landing_page='https://data.gov.hk/en-data/dataset/hk-censtatd-census_geo-2021-population-census-by-stpu',exact_data_resource_url=endpoint,retrieval_timestamp_utc=stamp,version_or_last_update='2021 census',coverage='TST–Jordan selected envelope only',format='ArcGIS JSON',relevant_fields='official STPUG polygon and ID',license_terms_redistribution='CSDI terms to review',local_raw_file_path=str(path.relative_to(root)),sha256=sha,publication_decision='derived-only pending rights review',notes='Official parent geography'))
with (root/'SOURCE_REGISTER.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print('STPUG features',len(obj.get('features',[])),'fields',[x['name'] for x in obj.get('fields',[])])
