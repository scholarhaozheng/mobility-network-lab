"""QC and bounded physical-link association for one UrbanNav TST reference run."""
import csv,json,math,statistics
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'instance';raw=root/'raw/UrbanNav_TST_GT_raw.txt'
LON=111320*math.cos(math.radians(22.3035));LAT=111320
def dist(a,b):return math.hypot((a[0]-b[0])*LON,(a[1]-b[1])*LAT)
def segdist(p,a,b):
 ax,ay=a[0]*LON,a[1]*LAT;bx,by=b[0]*LON,b[1]*LAT;px,py=p[0]*LON,p[1]*LAT
 dx,dy=bx-ax,by-ay;u=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
 return math.hypot(px-ax-u*dx,py-ay-u*dy),(dx,dy)
def linedist(p,path):return min((segdist(p,a,b) for a,b in zip(path,path[1:])),key=lambda x:x[0])
def table(name):
 with (out/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,rows,fields):
 with (out/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def parse_wkt(s):return [tuple(map(float,q.split())) for q in s[11:-1].split(',')]
links=[x for x in table('link.csv') if x['mcl_link_class']=='physical']
for x in links:x['coords']=parse_wkt(x['geometry'])
cell=.001;grid=defaultdict(set)
for i,x in enumerate(links):
 xs=[q[0] for q in x['coords']];ys=[q[1] for q in x['coords']]
 for gx in range(math.floor((min(xs)-.0007)/cell),math.floor((max(xs)+.0007)/cell)+1):
  for gy in range(math.floor((min(ys)-.0007)/cell),math.floor((max(ys)+.0007)/cell)+1):grid[(gx,gy)].add(i)
records=[];bad_lines=[]
for lineno,line in enumerate(raw.read_text(encoding='utf-8').splitlines()[2:],start=3):
 parts=line.split()
 if len(parts)!=20:
  bad_lines.append(lineno);continue
 try:
  utc=float(parts[0]);lat=float(parts[3])+float(parts[4])/60+float(parts[5])/3600
  lon=float(parts[6])+float(parts[7])/60+float(parts[8])/3600
  quality=parts[19]
  records.append({'source_line':lineno,'utc_seconds':utc,'utc_iso':datetime.fromtimestamp(utc,timezone.utc).isoformat(),
                  'lat':lat,'lon':lon,'height_m':float(parts[9]),'quality_code_uninterpreted':quality,
                  'heading_deg':float(parts[18])})
 except (ValueError,OverflowError):bad_lines.append(lineno)
inside=[p for p in records if 114.164<=p['lon']<=114.181 and 22.295<=p['lat']<=22.312]
results=[];prev_link=None;prev_point=None;unmatched=0;speed_fail=0;time_fail=0;continuity_breaks=0
for index,p in enumerate(inside):
 point=(p['lon'],p['lat']);q=inside[index+1] if index+1<len(inside) else None
 move=( (q['lon']-p['lon'])*LON,(q['lat']-p['lat'])*LAT ) if q and q['utc_seconds']-p['utc_seconds']<=2 else (0,0)
 speed=dist(point,(prev_point['lon'],prev_point['lat']))/(p['utc_seconds']-prev_point['utc_seconds']) if prev_point and p['utc_seconds']>prev_point['utc_seconds'] else 0
 gap=p['utc_seconds']-prev_point['utc_seconds'] if prev_point else 0
 if gap>2:time_fail+=1
 if speed>40:speed_fail+=1
 key=(math.floor(point[0]/cell),math.floor(point[1]/cell));cand=[]
 for j in grid.get(key,()):
  x=links[j];d,v=linedist(point,x['coords'])
  if d>60:continue
  norm=math.hypot(*v)*math.hypot(*move)
  cosine=(v[0]*move[0]+v[1]*move[1])/norm if norm and math.hypot(*move)>2 else 0
  heading_penalty=8*(1-cosine) if math.hypot(*move)>2 else 0
  transition=0 if prev_link is None or x['link_id']==prev_link['link_id'] or prev_link['to_node_id']==x['from_node_id'] else 20
  cand.append((d+heading_penalty+transition,d,x,cosine))
 cand.sort(key=lambda v:v[0]);best=cand[0] if cand else None
 x=best[2] if best else None
 continuity='start' if prev_link is None else ('same_link' if x and x['link_id']==prev_link['link_id'] else ('adjacent_directed' if x and prev_link['to_node_id']==x['from_node_id'] else 'discontinuity'))
 if x is None:unmatched+=1
 if continuity=='discontinuity':continuity_breaks+=1
 results.append({'trace_id':'UrbanNav_TST_GT_raw','point_index':index,'source_line':p['source_line'],'utc_iso':p['utc_iso'],
   'utc_seconds':p['utc_seconds'],'latitude':p['lat'],'longitude':p['lon'],'height_m':p['height_m'],
   'quality_code_uninterpreted':p['quality_code_uninterpreted'],'position_source':'SPAN-CPT+IE_ground_truth_reference_not_raw_GNSS',
   'interpoint_speed_mps':round(speed,3),'time_gap_s':gap,'speed_plausible':speed<=40,
   'gmns_link_id':x['link_id'] if x else '', 'source_route_id':x['source_link_id'] if x else '',
   'link_distance_m':round(best[1],3) if best else '', 'direction_cosine':round(best[3],4) if best else '',
   'candidate_link_count':len(cand),'continuity':continuity,'match_method':'local distance+motion+one-link transition heuristic' if x else 'unmatched'})
 prev_link=x;prev_point=p
paths=[];current=[]
for p in results:
 if p['continuity'] in ('start','discontinuity') and current:
  paths.append(current);current=[]
 current.append(p)
if current:paths.append(current)
path_rows=[]
for i,path in enumerate(paths,1):
 path_rows.append({'path_segment_id':i,'trace_id':'UrbanNav_TST_GT_raw','start_utc':path[0]['utc_iso'],
                   'end_utc':path[-1]['utc_iso'],'point_count':len(path),
                   'matched_point_count':sum(bool(x['gmns_link_id']) for x in path),
                   'physical_link_sequence':'|'.join(dict.fromkeys(x['gmns_link_id'] for x in path if x['gmns_link_id'])),
                   'status':'heuristic_link_association; breaks explicit'})
write('trajectory_points.csv',results,list(results[0]))
write('trajectory_paths.csv',path_rows,list(path_rows[0]))
matched_dist=[float(x['link_distance_m']) for x in results if x['gmns_link_id']]
report={'source':'UrbanNav-HK-Medium-Urban-1 TST ground truth text, PolyU IPNL','position_type':'SPAN-CPT+IE reference; not raw receiver GNSS',
 'raw_rows':len(records),'rows_inside_pilot_bbox':len(inside),'parse_failures':len(bad_lines),'parse_failure_lines':bad_lines[:20],
 'matched_points':len(matched_dist),'unmatched_points':unmatched,'median_link_distance_m':statistics.median(matched_dist) if matched_dist else None,
 'p95_link_distance_m':sorted(matched_dist)[int(.95*(len(matched_dist)-1))] if matched_dist else None,
 'time_gaps_over_2s':time_fail,'interpoint_speeds_over_40mps':speed_fail,'continuity_breaks':continuity_breaks,
 'path_segments':len(path_rows),'method':'greedy local distance+motion+one-link continuity heuristic; no lane/grade validation',
 'general_traffic_demand_inference':False,'raw_GNSS_included':False,'raw_file_publication':'private pending exact-file rights review'}
(out/'TRAJECTORY_QUALITY_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
obs=json.loads((out/'OBSERVATION_QUALITY_REPORT.json').read_text(encoding='utf-8'))
obs['GPS_TRAJECTORY_NOT_COMPLETED']=False;obs['reference_trajectory_included']=True;obs['raw_GNSS_included']=False;obs['reference_trajectory_matched_points']=len(matched_dist)
(out/'OBSERVATION_QUALITY_REPORT.json').write_text(json.dumps(obs,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
