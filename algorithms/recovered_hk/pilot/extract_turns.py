import html,json,re,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent; tag='{http://www.opengis.net/kml/2.2}'
bbox=(114.164,22.295,114.181,22.312)
kv=re.compile(r'<td>\s*([^<>]+?)\s*</td>\s*<td>\s*([^<>]*?)\s*</td>',re.I)
out=root/'candidate_extract/TST_Jordan_turns.jsonl'
alln=kept=0
with zipfile.ZipFile(root/'raw/road_turn.kmz') as z,z.open('doc.kml') as f,out.open('w',encoding='utf-8') as dst:
 ctx=ET.iterparse(f,events=('start','end'));_,base=next(ctx)
 for event,elem in ctx:
  if event!='end' or elem.tag!=tag+'Placemark':continue
  alln+=1
  coords=[]
  for item in (x.text or '' for x in elem.iter(tag+'coordinates')):
   for q in item.split():
    p=q.split(',')
    if len(p)>=2:
     try:coords.append((float(p[0]),float(p[1])))
     except ValueError:pass
  if not any(bbox[0]<=x<=bbox[2] and bbox[1]<=y<=bbox[3] for x,y in coords):
   base.clear();continue
  props={html.unescape(k).strip():html.unescape(v).strip() for k,v in kv.findall(elem.findtext(tag+'description') or '')}
  dst.write(json.dumps({'kml_id':elem.attrib.get('id'),'properties':props,'coordinates':coords},ensure_ascii=False,separators=(',',':'))+'\n')
  kept+=1;base.clear()
print({'all_turn_features':alln,'selected_turn_features':kept})
