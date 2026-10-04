"""Stream the official KMZ once; retain only the two bounded candidate envelopes."""
import csv, html, json, re, zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
AREAS={"TST_Jordan":(114.164,22.295,114.181,22.312),
       "WanChai_Causeway":(114.169,22.269,114.193,22.285)}
out=ROOT/"candidate_extract"; out.mkdir(exist_ok=True)
writers={n:(out/f"{n}_roads.jsonl").open("w",encoding="utf-8") for n in AREAS}
counts=Counter(); directions={n:Counter() for n in AREAS}; ids={n:Counter() for n in AREAS}
tag='{http://www.opengis.net/kml/2.2}'
kv=re.compile(r'<td>\s*([^<>]+?)\s*</td>\s*<td>\s*([^<>]*?)\s*</td>',re.I)
with zipfile.ZipFile(ROOT/'raw/road_centerline.kmz') as z, z.open('doc.kml') as f:
 context=ET.iterparse(f,events=('start','end'))
 _,root=next(context)
 for event,elem in context:
  if event!='end' or elem.tag!=tag+'Placemark': continue
  counts['total']+=1
  coord_texts=[x.text or '' for x in elem.iter(tag+'coordinates')]
  if not coord_texts:
   root.clear(); continue
  # Dense KML geometry makes vertex-in-envelope inclusion reliable for this screen.
  coords=[]
  for chunk in coord_texts:
   for item in chunk.split():
    vals=item.split(',')
    if len(vals)>=2:
     try: coords.append((float(vals[0]),float(vals[1])))
     except ValueError: pass
  if len(coords)<2:
   root.clear(); continue
  minx,maxx=min(x for x,y in coords),max(x for x,y in coords)
  miny,maxy=min(y for x,y in coords),max(y for x,y in coords)
  desc=elem.findtext(tag+'description') or ''
  props={html.unescape(k).strip():html.unescape(v).strip() for k,v in kv.findall(desc)}
  feature_id=elem.attrib.get('id','')
  for name,(w,s,e,n) in AREAS.items():
   if maxx<w or minx>e or maxy<s or miny>n: continue
   # Keep candidates with a vertex inside. Boundary-crossing links remain whole for topology.
   if not any(w<=x<=e and s<=y<=n for x,y in coords): continue
   sampled=coords[::max(1,len(coords)//100)]
   if sampled[-1]!=coords[-1]: sampled.append(coords[-1])
   row={'kml_id':feature_id,'route_id':props.get('ROUTE_ID',''),
        'street_code':props.get('ST_CODE',''),'name':props.get('STREET_ENAME',''),
        'travel_direction':props.get('TRAVEL_DIRECTION',''),
        'length_source_m':props.get('SHAPE_Length',''),
        'elevation':props.get('ELEVATION',''),
        'start':coords[0],'end':coords[-1], 'bbox':[minx,miny,maxx,maxy],
        'geometry_simplified':sampled,'vertex_count':len(coords)}
   writers[name].write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
   counts[name]+=1;directions[name][row['travel_direction']]+=1;ids[name][row['route_id']]+=1
  root.clear()
  if counts['total']%10000==0: print('parsed',counts['total'],flush=True)
for f in writers.values():f.close()
report={'features_parsed':counts['total'],'candidate_features':{n:counts[n] for n in AREAS},
        'direction_counts':{n:dict(directions[n]) for n in AREAS},
        'duplicate_route_ids':{n:sum(v-1 for v in ids[n].values() if v>1) for n in AREAS},
        'method':'KML stream; vertex-in-envelope screen; full feature endpoints retained; geometry sampled for maps'}
(out/'road_screen.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
