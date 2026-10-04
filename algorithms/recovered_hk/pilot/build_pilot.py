"""City-agnostic GMNS object construction from registered source adapters.

The Hong Kong source reads live here; graph, zone, relationship and demand
outputs use the shared GMNS-style object contract documented separately.
"""
import csv, io, json, math, zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'; OUT=ROOT/'instance'; OUT.mkdir(exist_ok=True)
BBOX=(114.164,22.295,114.181,22.312)
LON_SCALE=111320*math.cos(math.radians(22.3035));LAT_SCALE=111320

def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def write_json(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_csv(name,rows,fields):
 with (OUT/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def meters(a,b):return math.hypot((a[0]-b[0])*LON_SCALE,(a[1]-b[1])*LAT_SCALE)
def point_seg(p,a,b):
 ax,ay=a[0]*LON_SCALE,a[1]*LAT_SCALE;bx,by=b[0]*LON_SCALE,b[1]*LAT_SCALE;px,py=p[0]*LON_SCALE,p[1]*LAT_SCALE
 dx,dy=bx-ax,by-ay;u=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
 return math.hypot(px-(ax+u*dx),py-(ay+u*dy)),(dx,dy)
def point_line(p,coords):
 return min((point_seg(p,a,b) for a,b in zip(coords,coords[1:])),key=lambda x:x[0])
def wkt_line(coords):return 'LINESTRING('+','.join(f'{x:.9f} {y:.9f}' for x,y in coords)+')'
def wkt_poly(rings):return 'POLYGON('+','.join('('+','.join(f'{x:.9f} {y:.9f}' for x,y in ring)+')' for ring in rings)+')'
def ring_area_centroid(ring):
 area=cx=cy=0
 for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
  d=x1*y2-x2*y1;area+=d;cx+=(x1+x2)*d;cy+=(y1+y2)*d
 area/=2
 return area,(cx/(6*area),cy/(6*area)) if abs(area)>1e-15 else (sum(x for x,y in ring)/len(ring),sum(y for x,y in ring)/len(ring))
def clip_edge(poly,inside,intersect):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia,ib=inside(a),inside(b)
  if ia and ib:out.append(b)
  elif ia and not ib:out.append(intersect(a,b))
  elif not ia and ib:out.extend((intersect(a,b),b))
 return out
def clip_ring(ring):
 p=[tuple(x[:2]) for x in ring]
 if len(p)>1 and p[0]==p[-1]:p=p[:-1]
 w,s,e,n=BBOX
 for coord,side,is_min in [(0,w,True),(0,e,False),(1,s,True),(1,n,False)]:
  if not p:break
  inside=(lambda q:q[coord]>=side) if is_min else (lambda q:q[coord]<=side)
  def cross(a,b):
   t=(side-a[coord])/(b[coord]-a[coord]) if b[coord]!=a[coord] else 0
   return (a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
  p=clip_edge(p,inside,cross)
 if len(p)<3:return []
 if p[0]!=p[-1]:p.append(p[0])
 return p
def poly_area_centroid(rings):
 signed=[]
 for ring in rings:
  if len(ring)>=4:
   a,c=ring_area_centroid(ring)
   if abs(a)>1e-15:signed.append((a,c))
 total=sum(a for a,c in signed)
 if abs(total)<1e-15:return 0,None
 return abs(total),(sum(a*c[0] for a,c in signed)/total,sum(a*c[1] for a,c in signed)/total)
def in_ring(p,ring):
 x,y=p;hit=False
 for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:hit=not hit
 return hit
def in_poly(p,rings):return sum(in_ring(p,r) for r in rings)%2==1
def csv_zip(archive,name,encoding='utf-8-sig'):
 z=zipfile.ZipFile(archive)
 with z,z.open(name) as stream:
  yield from csv.DictReader(io.TextIOWrapper(stream,encoding=encoding,newline=''))

# Physical network. Exact official endpoint coordinates define graph nodes; only
# its largest weak component is routable in this bounded pilot.
roads=[json.loads(s) for s in (ROOT/'candidate_extract/TST_Jordan_roads.jsonl').open(encoding='utf-8')]
parent={}
def find(x):
 parent.setdefault(x,x)
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[b]=a
for r in roads:union(tuple(r['start']),tuple(r['end']))
sizes=Counter(find(k) for k in parent);main=max(sizes,key=sizes.get)
accepted=[r for r in roads if find(tuple(r['start']))==main and r['travel_direction'] in ('1','2','3') and r['route_id'] and float(r['length_source_m'] or 0)>0 and tuple(r['start'])!=tuple(r['end'])]
quarantined=[{'source_route_id':r['route_id'],'kml_id':r['kml_id'],
 'reason':'outside_largest_component' if find(tuple(r['start']))!=main else ('self_loop' if tuple(r['start'])==tuple(r['end']) else 'nonroutable_or_missing_length')} for r in roads if r not in accepted]
coords=sorted({tuple(r['start']) for r in accepted}|{tuple(r['end']) for r in accepted})
node_id={p:10000+i for i,p in enumerate(coords)}
nodes=[];node_cw=[]
for p,nid in node_id.items():
 source_key=f'endpoint:{p[0]:.13f},{p[1]:.13f}'
 nodes.append({'node_id':nid,'zone_id':'','x_coord':p[0],'y_coord':p[1], 'node_type':'physical_road','source_node_id':source_key,'source_h3_zone_id':'','mcl_source_taz_zone_id':''})
 node_cw.append({'source_node_key':source_key,'node_id':nid,'method':'exact KML endpoint coordinate','source_id':'TD_ROAD_CENTERLINE'})
links=[];link_cw=[];by_route=defaultdict(list)
for r in sorted(accepted,key=lambda x:int(x['route_id'])):
 rid=int(r['route_id']);a=node_id[tuple(r['start'])];b=node_id[tuple(r['end'])]
 if a==b:
  quarantined.append({'source_route_id':rid,'kml_id':r['kml_id'],'reason':'self_loop'});continue
 for suffix,start,end,path in [('F',a,b,r['geometry_simplified']),('R',b,a,list(reversed(r['geometry_simplified'])))]:
  if r['travel_direction']=='3' and suffix=='R':continue
  if r['travel_direction']=='2' and suffix=='F':continue
  lid=100000+rid*2+(0 if suffix=='F' else 1)
  link={'link_id':lid,'from_node_id':start,'to_node_id':end,'directed':1,'dir_flag':1 if suffix=='F' else -1,
   'length':r['length_source_m'],'free_speed':'','free_flow_time':'','capacity':'','lanes':'','link_type':1,
   'vdf_alpha':'','vdf_beta':'','vdf_plf':'','geometry':wkt_line(path),'mcl_link_class':'physical',
   'source_link_id':rid,'source_from_node_id':a,'source_to_node_id':b,'mcl_gps_match_allowed':'true',
   'source_kml_id':r['kml_id'],'source_travel_direction':r['travel_direction'],'street_name':r['name'],'street_code':r['street_code'],
   'geometry_sampling':'<=101 vertices; endpoints exact','length_unit':'m','capacity_unit':'unknown','free_speed_unit':'unknown'}
  links.append(link);by_route[str(rid)].append(link)
  link_cw.append({'source_id':'TD_ROAD_CENTERLINE','source_route_id':rid,'source_kml_id':r['kml_id'],'gmns_link_id':lid,
                  'direction':suffix,'source_travel_direction':r['travel_direction']})

# Official SSG fine zones, official STPUG parents, with clipped-area allocation.
ssg=read_json(RAW/'census_ssg_geometry.json')['features']
stpug=read_json(RAW/'census_stpug_geometry.json')['features']
parents=[]
for f in stpug:
 a=f['attributes'];rings=[clip_ring(r) for r in f['geometry']['rings']];rings=[r for r in rings if r]
 if rings:
  area,c=poly_area_centroid(rings)
  if area>0:parents.append({'source_stpug':str(a['stpug']),'rings':rings,'full_rings':f['geometry']['rings'],'name':str(a.get('stpug_eng') or a['stpug'])})
parents.sort(key=lambda x:x['source_stpug'])
parent_id={x['source_stpug']:1001+i for i,x in enumerate(parents)}
zones=[];zone_cw=[];population=[];exclusions=[];zone_geo=[];zone_map=[]
for f in sorted(ssg,key=lambda x:str(x['attributes']['ssbg'])):
 a=f['attributes'];full=f['geometry']['rings'];clipped=[clip_ring(r) for r in full];clipped=[r for r in clipped if r]
 area,c=poly_area_centroid(clipped);full_area,_=poly_area_centroid(full)
 if area<=1e-13 or not c or full_area<=0:continue
 weight=min(1,max(0,area/full_area));sid=str(a['ssbg']);zid=len(zones)+1
 if weight<.01:
  exclusions.append({'source_ssbg':sid,'outside_pilot_population_estimate':a['t_pop'],
    'outside_pilot_households_estimate':a['dh'],'reason':'intersecting sliver under 1% of source SSG; no model zone'})
  continue
 if not (BBOX[0]<=c[0]<=BBOX[2] and BBOX[1]<=c[1]<=BBOX[3]) or not in_poly(c,clipped):
  candidates=[]
  for ring in clipped:
   ra,rc=ring_area_centroid(ring)
   if in_poly(rc,clipped):candidates.append((abs(ra),rc))
  c=max(candidates)[1] if candidates else clipped[0][0]
 matches=[x for x in parents if in_poly(c,x['full_rings'])]
 parent_source=matches[0]['source_stpug'] if len(matches)==1 else next((x['source_stpug'] for x in parents if sid.startswith(x['source_stpug'][:3])),'')
 super_id=parent_id.get(parent_source,'')
 pop=float(a['t_pop'])*weight
 try:hh=float(a['dh'])*weight
 except (ValueError,TypeError):hh=None
 zone={'zone_id':zid,'name':sid,'boundary':wkt_poly(clipped),'super_zone':super_id,
       'mcl_original_h3_id':'','mcl_h3_resolution':'','mcl_clipped_geometry_wkt':wkt_poly(clipped),
       'mcl_boundary_status':'clipped_official_SSG','source_ssbg':sid,'source_stpug':parent_source,
       'centroid_lon':c[0],'centroid_lat':c[1]}
 zones.append(zone);zone_map.append((zid,c))
 zone_geo.append({'type':'Feature','properties':{'zone_id':zid,'ssbg':sid,'super_zone':super_id},'geometry':{'type':'Polygon','coordinates':clipped}})
 zone_cw.append({'zone_id':zid,'source_ssbg':sid,'source_stpug':parent_source,'source_population':a['t_pop'],
                 'source_households':a['dh'],'allocation_method':'clipped_polygon_area_ratio','allocation_weight':weight,
                 'source_year':2021,'spatial_parent_match_count':len(matches)})
 population.append({'zone_id':zid,'source_ssbg':sid,'source_year':2021,'allocation_weight':weight,
                    'source_population':a['t_pop'],'population_allocated':pop,'source_households':a['dh'],
                    'households_allocated':hh if hh is not None else '', 'status':'area_allocated_estimate'})
 exclusions.append({'source_ssbg':sid,'outside_pilot_population_estimate':float(a['t_pop'])*(1-weight),
                    'outside_pilot_households_estimate':float(a['dh'])*(1-weight) if hh is not None else '',
                    'reason':'outside_clipped_pilot_polygon; area allocation assumption'})
super_zones=[{'zone_id':parent_id[x['source_stpug']],'name':x['name'],'boundary':wkt_poly(x['rings']),
              'super_zone':'','source_stpug':x['source_stpug']} for x in parents]
zone_access=[];connectors=[]
for z in zones:
 zid=z['zone_id'];p=(float(z['centroid_lon']),float(z['centroid_lat']))
 nearest=min(coords,key=lambda q:meters(p,q));dist=meters(p,nearest);nid=node_id[nearest]
 zone_access.append({'zone_id':zid,'centroid_node_id':zid,'physical_access_node_id':nid,
                     'access_distance_m':round(dist,3),'access_status':'review_long_or_barrier' if dist>200 else 'straight_line_screen_only',
                     'access_method':'nearest physical road endpoint; no barrier confirmation'})
 nodes.append({'node_id':zid,'zone_id':zid,'x_coord':p[0],'y_coord':p[1], 'node_type':'model_centroid_nonphysical','source_node_id':'','source_h3_zone_id':'','mcl_source_taz_zone_id':''})
 for suffix,source,target in [('out',zid,nid),('in',nid,zid)]:
  lid=10_000_000+zid*2+(0 if suffix=='out' else 1)
  c={'link_id':lid,'from_node_id':source,'to_node_id':target,'directed':1,'dir_flag':1,'length':'','free_speed':'',
     'free_flow_time':'','capacity':'','lanes':'','link_type':0,'vdf_alpha':'','vdf_beta':'','vdf_plf':'',
     'geometry':wkt_line([p,nearest] if suffix=='out' else [nearest,p]),'mcl_link_class':'nonphysical_zone_access_'+suffix,
     'source_link_id':'','source_from_node_id':'','source_to_node_id':'','mcl_gps_match_allowed':'false',
     'source_kml_id':'','source_travel_direction':'','street_name':'','street_code':'','geometry_sampling':'straight display only',
     'length_unit':'not routable','capacity_unit':'not routable','free_speed_unit':'not routable'}
  connectors.append(c)
links_all=links+connectors

# Turns retain the source multi-edge relationship. Operational movement mapping
# is only accepted where consecutive directed links share the exact endpoint.
turns=[json.loads(s) for s in (ROOT/'candidate_extract/TST_Jordan_turns.jsonl').open(encoding='utf-8')]
movements=[];turn_limits=[]
for t in turns:
 p=t['properties'];tid=p.get('TURN_ID','');sequence=[p.get(f'Edge{i}FID','') for i in range(1,9)]
 sequence=[x for x in sequence if x and x not in ('<Null>','-1')]
 pairs=[]
 if len(sequence)>=2:
  for r1,r2 in zip(sequence,sequence[1:]):
   pairs.extend((x,y) for x in by_route.get(r1,[]) for y in by_route.get(r2,[]) if x['to_node_id']==y['from_node_id'])
 if pairs:
  for x,y in pairs:
   movements.append({'source_turn_id':tid,'source_edge_sequence':'|'.join(sequence),'from_link_id':x['link_id'],
     'to_link_id':y['link_id'],'via_node_id':x['to_node_id'],'no_turn':p.get('NO_TURN',''),
     'included_vehicle_types':p.get('INC_VEH_TYPE',''),'excluded_vehicle_types':p.get('EXC_VEH_TYPE',''),
     'part_time_restriction':p.get('PART_TIME_REST',''),'status':'mapped_source_restriction_not_solver_enforced'})
 else:turn_limits.append({'source_turn_id':tid,'source_edge_sequence':'|'.join(sequence),'reason':'edge_missing_or_no_exact_directed_adjacency'})

# Detector snapshot and explicit spatial/directional crosswalk.
with (RAW/'detector_info.csv').open(encoding='utf-8-sig',newline='') as f:all_det=list(csv.DictReader(f))
det=[d for d in all_det if BBOX[0]<=float(d['Longitude'])<=BBOX[2] and BBOX[1]<=float(d['Latitude'])<=BBOX[3]]
headings={'NORTH':(0,1),'SOUTH':(0,-1),'EAST':(1,0),'WEST':(-1,0),
          'NORTH EAST':(1,1),'NORTH WEST':(-1,1),'SOUTH EAST':(1,-1),'SOUTH WEST':(-1,-1)}
det_link=[];det_by_id={}
for d in det:
 p=(float(d['Longitude']),float(d['Latitude']));h=headings.get(d['Direction'].strip().upper())
 candidates=[]
 for link in links:
  if not (BBOX[0]-.002<=p[0]<=BBOX[2]+.002):continue
  route=next(r for r in accepted if str(r['route_id'])==str(link['source_link_id']))
  path=route['geometry_simplified'] if link['dir_flag']==1 else list(reversed(route['geometry_simplified']))
  distance,v=point_line(p,path)
  if h:
   norm=math.hypot(*v)*math.hypot(*h)
   cosine=(v[0]*h[0]+v[1]*h[1])/norm if norm else -1
  else:cosine=0
  if cosine>=.5:candidates.append((distance,link,cosine))
 candidates.sort(key=lambda q:q[0]);best=candidates[0] if candidates else None
 status='matched_direction_screened' if best and best[0]<=80 else 'unmatched'
 row={'detector_id':d['AID_ID_Number'],'source_direction':d['Direction'],'source_road':d['Road_EN'].strip(),
      'longitude':p[0],'latitude':p[1],'gmns_link_id':best[1]['link_id'] if status!='unmatched' else '',
      'source_route_id':best[1]['source_link_id'] if status!='unmatched' else '',
      'distance_m':round(best[0],3) if best else '', 'direction_cosine':round(best[2],4) if best else '',
      'second_candidate_distance_m':round(candidates[1][0],3) if len(candidates)>1 else '',
      'match_status':status,'grade_status':'unverified; flyover/underpass ambiguity remains'}
 det_link.append(row);det_by_id[row['detector_id']]=row
xml=ET.parse(RAW/'detector_raw.xml').getroot();date=xml.findtext('date');observations=[]
for period in xml.findall('./periods/period'):
 for detector in period.findall('./detectors/detector'):
  did=detector.findtext('detector_id')
  if did not in det_by_id:continue
  match=det_by_id[did]
  for lane in detector.findall('./lanes/lane'):
   observations.append({'detector_id':did,'date':date,'period_from':period.findtext('period_from'),
    'period_to':period.findtext('period_to'),'source_direction':detector.findtext('direction'),
    'lane_id':lane.findtext('lane_id'),'speed_kmh':lane.findtext('speed'),'volume_30s':lane.findtext('volume'),
    'occupancy_percent':lane.findtext('occupancy'),'source_valid':lane.findtext('valid'),
    'gmns_link_id':match['gmns_link_id'] if match['match_status']=='matched_direction_screened' else '',
    'mapping_status':match['match_status']})

# Scheduled transit relationships; no realized vehicle movement inferred.
stops=[x for x in csv_zip(RAW/'td_gtfs.zip','stops.txt') if x.get('stop_lon') and x.get('stop_lat') and BBOX[0]<=float(x['stop_lon'])<=BBOX[2] and BBOX[1]<=float(x['stop_lat'])<=BBOX[3]]
stop_ids={x['stop_id'] for x in stops};stop_zone=[];stop_net=[];transit_stops=[]
ped=[]
for i in range(4):ped.extend(read_json(RAW/f'pedestrian_{i}.json')['features'])
ped_segments=[]
for f in ped:
 a=f['attributes'];pid=a['PedestrianRouteID']
 for path in f['geometry']['paths']:
  if len(path)>1:ped_segments.append((pid,a,[tuple(q[:2]) for q in path]))
for stop in stops:
 p=(float(stop['stop_lon']),float(stop['stop_lat']));zid,zc=min(zone_map,key=lambda q:meters(p,q[1]));nearest=min(coords,key=lambda q:meters(p,q))
 ped_candidates=[]
 for pid,a,path in ped_segments:
  if any(abs(p[0]-q[0])<.0015 and abs(p[1]-q[1])<.0015 for q in (path[0],path[-1])):
   ped_candidates.append((point_line(p,path)[0],pid,a))
 best=min(ped_candidates,key=lambda q:q[0]) if ped_candidates else None
 stop_zone.append({'stop_id':stop['stop_id'],'zone_id':zid,'straight_distance_m':round(meters(p,zc),3),
                   'method':'nearest fine-zone centroid; boundary topology not certified'})
 stop_net.append({'stop_id':stop['stop_id'],'physical_node_id':node_id[nearest],
                  'straight_distance_m':round(meters(p,nearest),3),
                  'pedestrian_route_id':best[1] if best else '', 'pedestrian_straight_distance_m':round(best[0],3) if best else '',
                  'pedestrian_floor_id':best[2].get('FloorID') if best else '',
                  'pedestrian_access_time_id':best[2].get('AccessTimeID') if best else '',
                  'status':'pedestrian_proximity_only; vertical connectivity unknown' if best else 'pedestrian_unmatched'})
 transit_stops.append({'stop_id':stop['stop_id'],'stop_name':stop['stop_name'],'stop_lon':p[0],'stop_lat':p[1],
                      'location_type':stop.get('location_type',''),'source_zone_id':stop.get('zone_id','')})
selected_trips=set();stop_trip_pairs=set()
for x in csv_zip(RAW/'td_gtfs.zip','stop_times.txt'):
 if x['stop_id'] in stop_ids:
  selected_trips.add(x['trip_id']);stop_trip_pairs.add((x['stop_id'],x['trip_id']))
trips={x['trip_id']:x for x in csv_zip(RAW/'td_gtfs.zip','trips.txt') if x['trip_id'] in selected_trips}
routes={x['route_id']:x for x in csv_zip(RAW/'td_gtfs.zip','routes.txt')}
calendar={x['service_id']:x for x in csv_zip(RAW/'td_gtfs.zip','calendar.txt')}
freq=defaultdict(list)
for x in csv_zip(RAW/'td_gtfs.zip','frequencies.txt'):
 if x['trip_id'] in selected_trips:freq[x['trip_id']].append(x)
route_counts=Counter((x['route_id'],x['service_id']) for x in trips.values())
route_ids={k[0] for k in route_counts}
fare_ids=defaultdict(set)
for x in csv_zip(RAW/'td_gtfs.zip','fare_rules.txt'):
 if x.get('route_id') in route_ids:fare_ids[x['route_id']].add(x['fare_id'])
all_fares=set().union(*fare_ids.values()) if fare_ids else set();fare_attr={}
for x in csv_zip(RAW/'td_gtfs.zip','fare_attributes.txt'):
 if x['fare_id'] in all_fares:fare_attr[x['fare_id']]=x
route_summary=[];fare_summary=[]
for (rid,service),count in sorted(route_counts.items()):
 r=routes.get(rid,{});trip_set={tid for tid,x in trips.items() if x['route_id']==rid and x['service_id']==service}
 heads=[int(q['headway_secs']) for tid in trip_set for q in freq.get(tid,[]) if q.get('headway_secs')]
 cal=calendar.get(service,{})
 route_summary.append({'route_id':rid,'agency_id':r.get('agency_id',''),'route_short_name':r.get('route_short_name',''),
 'route_long_name':r.get('route_long_name',''),'route_type':r.get('route_type',''),'service_id':service,
 'pilot_intersecting_trip_patterns':count,'frequency_records':sum(len(freq.get(tid,[])) for tid in trip_set),
 'headway_min_s':min(heads) if heads else '', 'headway_max_s':max(heads) if heads else '',
 'calendar_start':cal.get('start_date',''),'calendar_end':cal.get('end_date',''),
 'schedule_type':'frequency/headway' if heads else 'specified schedule or no frequency record'})
for rid in sorted(fare_ids):
 for fid in sorted(fare_ids[rid]):
  a=fare_attr.get(fid,{})
  fare_summary.append({'route_id':rid,'fare_id':fid,'price_hkd':a.get('price',''),'currency':a.get('currency_type',''),
                       'status':'GTFS published fare; no fare collection observation'})
stop_routes=sorted({(sid,trips[tid]['route_id'],trips[tid]['service_id']) for sid,tid in stop_trip_pairs if tid in trips})

# Transparent, internal-only person-trip scenarios from area-allocated census.
zone_pop={int(x['zone_id']):float(x['population_allocated']) for x in population}
stop_counts=Counter(int(x['zone_id']) for x in stop_zone)
activity=[{'zone_id':zid,'population_2021_area_allocated':round(pop,6),'households_2021_area_allocated':next(x['households_allocated'] for x in population if x['zone_id']==zid),
           'gtfs_stop_count':stop_counts[zid],'employment':'unknown','activity_proxy':'population only; no jobs evidence'} for zid,pop in zone_pop.items()]
tiers={'smoke':0.002,'pilot':0.05};pa=[];person=[];vehicle=[]
for tier,rate in tiers.items():
 for zid,point in zone_map:
  production=zone_pop[zid]*rate
  candidates=[]
  for other,p in zone_map:
   if other==zid or zone_pop[other]<=0:continue
   distance=meters(point,p)
   weight=zone_pop[other]*math.exp(-distance/1200)
   candidates.append((weight,other,distance))
  selected=sorted(candidates,reverse=True)[:5];total=sum(x[0] for x in selected)
  pa.append({'tier':tier,'zone_id':zid,'person_trip_productions':production,
             'attraction_proxy':zone_pop[zid],'production_rate_per_resident':rate,
             'period':'abstract one-hour scenario','status':'scenario_seed_not_observed'})
  if not total:continue
  for weight,did,distance in selected:
   volume=production*weight/total
   person.append({'tier':tier,'o_zone_id':zid,'d_zone_id':did,'person_trips':volume,
                  'straight_distance_m':round(distance,3),'method':'top5 population-weighted exponential distance; 1200 m decay'})
   vehicle.append({'tier':tier,'o_zone_id':zid,'d_zone_id':did,'volume':volume*.2/1.5,
                   'vehicle_fraction_assumption':0.2,'persons_per_vehicle_assumption':1.5,
                   'status':'hypothetical vehicle scenario; not observed mode share'})

write_csv('node.csv',sorted(nodes,key=lambda x:int(x['node_id'])),list(nodes[0]))
write_csv('link.csv',sorted(links_all,key=lambda x:(int(x['from_node_id']),int(x['to_node_id']),int(x['link_id']))),list(links_all[0]))
write_csv('zone.csv',zones+super_zones,list(zones[0]))
write_csv('super_zone.csv',super_zones,list(super_zones[0]))
write_csv('zone_source_crosswalk.csv',zone_cw,list(zone_cw[0]))
write_csv('source_node_crosswalk.csv',node_cw,list(node_cw[0]))
write_csv('source_link_crosswalk.csv',link_cw,list(link_cw[0]))
write_csv('zone_access.csv',zone_access,list(zone_access[0]))
write_csv('connector_link.csv',connectors,list(connectors[0]))
write_csv('movement.csv',movements,list(movements[0]) if movements else ['source_turn_id','source_edge_sequence','from_link_id','to_link_id','via_node_id','no_turn','included_vehicle_types','excluded_vehicle_types','part_time_restriction','status'])
write_csv('zone_population_households.csv',population,list(population[0]))
write_csv('zone_activity.csv',activity,list(activity[0]))
write_csv('production_attraction.csv',pa,list(pa[0]))
write_csv('demand_seed_person.csv',person,list(person[0]))
write_csv('demand_seed_vehicle.csv',vehicle,list(vehicle[0]))
write_csv('demand_S1.csv',[x for x in vehicle if x['tier']=='smoke'],['o_zone_id','d_zone_id','volume'])
write_csv('excluded_or_unknown_demand.csv',exclusions,list(exclusions[0]))
write_csv('detector_to_link.csv',det_link,list(det_link[0]))
write_csv('detector_observations.csv',observations,list(observations[0]))
write_csv('transit_stops.csv',transit_stops,list(transit_stops[0]))
write_csv('stop_to_zone.csv',stop_zone,list(stop_zone[0]))
write_csv('stop_to_network.csv',stop_net,list(stop_net[0]))
write_csv('transit_route_service.csv',route_summary,list(route_summary[0]))
write_csv('transit_fares.csv',fare_summary,list(fare_summary[0]) if fare_summary else ['route_id','fare_id','price_hkd','currency','status'])
write_csv('transit_stop_route.csv',[{'stop_id':a,'route_id':b,'service_id':c} for a,b,c in stop_routes],['stop_id','route_id','service_id'])
write_csv('network_quarantine.csv',quarantined,['source_route_id','kml_id','reason'])
write_csv('turn_limitations.csv',turn_limits,['source_turn_id','source_edge_sequence','reason'])
write_json('zone_geometry.geojson',{'type':'FeatureCollection','features':zone_geo})
write_json('pilot_boundary.geojson',{'type':'FeatureCollection','features':[{'type':'Feature','properties':{'name':'TST–Jordan bounded engineering pilot','bbox':BBOX},'geometry':{'type':'Polygon','coordinates':[[[BBOX[0],BBOX[1]],[BBOX[2],BBOX[1]],[BBOX[2],BBOX[3]],[BBOX[0],BBOX[3]],[BBOX[0],BBOX[1]]]]}}]})
write_json('NETWORK_QUALITY_REPORT.json',{'source_road_features':len(roads),'physical_source_features':len(accepted),'physical_nodes':len(coords),
 'physical_directed_links':len(links),'weak_components_source':len(sizes),'largest_component_nodes':sizes[main],
 'quarantined_records':len(quarantined),'source_turn_features':len(turns),'mapped_movement_rows':len(movements),'unmapped_turns':len(turn_limits),
 'speed_capacity_lanes':'unknown in official centerline; assignment gate blocked','geometry':'KML paths simplified to <=101 display vertices; endpoints exact'})
write_json('ZONE_ACCESS_QUALITY_REPORT.json',{'fine_zones':len(zones),'super_zones':len(super_zones),'centroid_nodes':len(zones),
 'nonphysical_connectors':len(connectors),'long_access_over_200m':sum(float(x['access_distance_m'])>200 for x in zone_access),
 'max_access_distance_m':max(float(x['access_distance_m']) for x in zone_access),'barrier_validation':'not complete; nearest-node straight distance screening only'})
write_json('OBSERVATION_QUALITY_REPORT.json',{'detector_sites_in_boundary':len(det),'matched_to_physical_link':sum(x['match_status']=='matched_direction_screened' for x in det_link),
 'observation_lane_rows':len(observations),'observation_date':date,'GPS_TRAJECTORY_NOT_COMPLETED':True,
 'mapping_limit':'nearest sampled road geometry + direction within 60 degrees and 80 m; grade and lane not confirmed'})
write_json('TRANSIT_QUALITY_REPORT.json',{'stops_in_boundary':len(stops),'routes_with_intersecting_trips':len(route_ids),
 'route_service_rows':len(route_summary),'stop_route_service_rows':len(stop_routes),'fare_rows':len(fare_summary),
 'pedestrian_source_features_queried':len(ped),'stop_pedestrian_proximity_links':sum(x['pedestrian_route_id']!='' for x in stop_net),
 'meaning':'published GTFS headways/schedules/fares, not realized vehicle trajectories; pedestrian link proximity is not a walk path'})
write_json('DEMAND_ACCOUNTING.json',{'fine_zones':len(zones),'source_population_sum_intersecting':sum(float(x['source_population']) for x in population),
 'allocated_population':sum(zone_pop.values()),'allocated_households':sum(float(x['households_allocated']) for x in population if x['households_allocated']!=''),
 'tiers':{tier:{'person_od_rows':sum(x['tier']==tier for x in person),'person_trips':sum(x['person_trips'] for x in person if x['tier']==tier),
                 'vehicle_scenario_trips':sum(x['volume'] for x in vehicle if x['tier']==tier)} for tier in tiers},
 'allocation':'source SSG population/households times clipped area fraction; not observed within-SSG distribution',
 'production_conservation_error':{tier:sum(x['person_trip_productions'] for x in pa if x['tier']==tier)-sum(x['person_trips'] for x in person if x['tier']==tier) for tier in tiers}})
print(json.dumps({'physical_nodes':len(coords),'physical_links':len(links),'fine_zones':len(zones),'super_zones':len(super_zones),
                  'detector_matches':sum(x['match_status']=='matched_direction_screened' for x in det_link),
                  'GTFS_stops':len(stops),'person_OD_rows':len(person)},indent=2))
