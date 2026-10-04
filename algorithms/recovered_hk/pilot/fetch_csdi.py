"""Fetch only selected TST–Jordan CSDI geometry in WGS84."""
import csv,hashlib,json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parent;raw=root/'raw'
base='https://portal.csdi.gov.hk/server/rest/services/common/'
tasks=[('CENSUS_SSG_GEOMETRY','censtatd_rcd_1635933365202_19171',0,3000),
       ('LANDSD_PEDESTRIAN','landsd_rcd_1637222018065_52265',0,3000),
       ('LANDSD_PEDESTRIAN','landsd_rcd_1637222018065_52265',3000,3000),
       ('LANDSD_PEDESTRIAN','landsd_rcd_1637222018065_52265',6000,3000),
       ('LANDSD_PEDESTRIAN','landsd_rcd_1637222018065_52265',9000,3000)]
records=[]
for sid,dataset,offset,limit in tasks:
 params={'f':'json','geometry':'114.164,22.295,114.181,22.312','geometryType':'esriGeometryEnvelope',
  'inSR':'4326','spatialRel':'esriSpatialRelIntersects','where':'1=1','outFields':'*',
  'outSR':'4326','returnGeometry':'true','resultOffset':offset,'resultRecordCount':limit}
 url=base+dataset+'/FeatureServer/0/query?'+urllib.parse.urlencode(params)
 dest=raw/(('census_ssg_geometry' if sid=='CENSUS_SSG_GEOMETRY' else f'pedestrian_{offset//3000}')+'.json')
 t=time.monotonic();stamp=datetime.now(timezone.utc).isoformat();status='ok';error=''
 try:
  with urllib.request.urlopen(url,timeout=120) as resp:
   data=resp.read(200_000_001)
  if len(data)>200_000_000:raise ValueError('200 MB page cap')
  obj=json.loads(data)
  if 'error' in obj:raise ValueError(str(obj['error']))
  dest.write_bytes(data)
  count=len(obj.get('features',[]))
 except Exception as exc:status='failed';error=repr(exc);count=0
 size=dest.stat().st_size if dest.exists() else 0
 sha=hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else ''
 records.append((sid,url,stamp,status,size,round(time.monotonic()-t,3),error,str(dest.relative_to(root)),sha,count))
 print(sid,offset,status,count,size,error,flush=True)
with (root/'DOWNLOAD_LOG.csv').open('a',newline='',encoding='utf-8') as f:
 w=csv.writer(f);[w.writerow(r[:7]) for r in records]
with (root/'RAW_FILE_MANIFEST.csv').open('a',newline='',encoding='utf-8') as f:
 w=csv.writer(f);[w.writerow((r[0],r[7],r[4],r[8],r[2])) for r in records if r[3]=='ok']
with (root/'SOURCE_REGISTER.csv').open(encoding='utf-8',newline='') as f:
 reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
for row in rows:
 if row['source_id']=='LANDSD_PEDESTRIAN':
  row['exact_data_resource_url']=base+'landsd_rcd_1637222018065_52265/FeatureServer/0/query'
  row['local_raw_file_path']='raw/pedestrian_0.json ... raw/pedestrian_3.json'
  row['retrieval_timestamp_utc']=records[-1][2]
 if row['source_id']=='CENSUS_SSG':
  row['notes']='CSV statistics plus separate official CSDI geometry; see CENSUS_SSG_GEOMETRY entry'
rows.append(dict(source_id='CENSUS_SSG_GEOMETRY',provider='Census and Statistics Department',
 official_landing_page='https://portal.csdi.gov.hk/csdi-webpage/dataset/censtatd_rcd_1635933365202_19171',
 exact_data_resource_url=base+'censtatd_rcd_1635933365202_19171/FeatureServer/0/query',
 retrieval_timestamp_utc=records[0][2],version_or_last_update='2021 census; service queried 2026-09-26',
 coverage='TST–Jordan selected envelope only',format='ArcGIS JSON',
 relevant_fields='ssbg,t_pop,dh,polygon rings',license_terms_redistribution='CSDI terms to review',
 local_raw_file_path='raw/census_ssg_geometry.json',sha256=records[0][8],
 publication_decision='derived-only pending rights review',notes='98 intersecting polygons expected'))
with (root/'SOURCE_REGISTER.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
