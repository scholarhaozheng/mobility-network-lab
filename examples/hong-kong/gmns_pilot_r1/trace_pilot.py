"""Read-only source-to-GMNS relationship trace. Paths are relative by default."""
import argparse,csv,json
from pathlib import Path

def rows(root,name):
 with (root/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def one(items,key,value):
 matches=[x for x in items if x[key]==str(value)]
 if len(matches)!=1:raise ValueError(f'Expected one {key}={value}, got {len(matches)}')
 return matches[0]
def trace(root,zone_id=None,detector_id=None,stop_id=None,trajectory_point=None):
 result={};root=Path(root)
 links=rows(root,'link.csv');nodes=rows(root,'node.csv')
 if zone_id is not None:
  z=one(rows(root,'zone.csv'),'zone_id',zone_id)
  if not z['super_zone']:raise ValueError('fine zone required')
  parent=one(rows(root,'super_zone.csv'),'zone_id',z['super_zone'])
  cw=one(rows(root,'zone_source_crosswalk.csv'),'zone_id',zone_id)
  pop=one(rows(root,'zone_population_households.csv'),'zone_id',zone_id)
  access=one(rows(root,'zone_access.csv'),'zone_id',zone_id)
  centroid=one(nodes,'node_id',zone_id)
  connector=one([x for x in links if x['mcl_link_class']=='nonphysical_zone_access_out'],'from_node_id',zone_id)
  physical=one(nodes,'node_id',access['physical_access_node_id'])
  demand=next((x for x in rows(root,'demand_seed_person.csv') if x['tier']=='smoke' and x['o_zone_id']==str(zone_id)),None)
  result['zone_to_road_and_demand']={'fine_zone_id':z['zone_id'],'source_ssbg':cw['source_ssbg'],
   'source_stpug':cw['source_stpug'],'super_zone_id':parent['zone_id'],'source_population':pop['source_population'],
   'area_allocation_weight':pop['allocation_weight'],'allocated_population':pop['population_allocated'],
   'centroid_node_id':centroid['node_id'],'connector_link_id':connector['link_id'],
   'connector_class':connector['mcl_link_class'],'physical_access_node_id':physical['node_id'],
   'access_distance_m':access['access_distance_m'],'smoke_person_OD_example':demand}
 if detector_id is not None:
  x=one(rows(root,'detector_to_link.csv'),'detector_id',detector_id)
  linked=one(links,'link_id',x['gmns_link_id']) if x['gmns_link_id'] else None
  observations=[o for o in rows(root,'detector_observations.csv') if o['detector_id']==detector_id]
  result['detector_to_physical_link']={'detector_id':detector_id,'source_road':x['source_road'],
   'source_direction':x['source_direction'],'match_status':x['match_status'],'distance_m':x['distance_m'],
   'source_route_id':x['source_route_id'],'physical_gmns_link_id':x['gmns_link_id'],
   'physical_link_class':linked['mcl_link_class'] if linked else None,
   'observation_rows':len(observations),'observation_example':observations[0] if observations else None,
   'caution':'Detector lane data are observations, not GPS or calibrated link flow.'}
 if stop_id is not None:
  s=one(rows(root,'transit_stops.csv'),'stop_id',stop_id)
  z=one(rows(root,'stop_to_zone.csv'),'stop_id',stop_id)
  n=one(rows(root,'stop_to_network.csv'),'stop_id',stop_id)
  services=[x for x in rows(root,'transit_stop_route.csv') if x['stop_id']==str(stop_id)]
  result['transit_stop_access']={'stop_id':stop_id,'name':s['stop_name'],'zone_id':z['zone_id'],
   'stop_zone_straight_distance_m':z['straight_distance_m'],'physical_node_id':n['physical_node_id'],
   'stop_road_straight_distance_m':n['straight_distance_m'],'pedestrian_route_id':n['pedestrian_route_id'],
   'pedestrian_proximity_m':n['pedestrian_straight_distance_m'],'route_service_example':services[0] if services else None,
   'caution':'Published GTFS service and pedestrian proximity; no observed journey or validated walk path.'}
 if trajectory_point is not None:
  p=one(rows(root,'trajectory_points.csv'),'point_index',trajectory_point)
  link=one(links,'link_id',p['gmns_link_id']) if p['gmns_link_id'] else None
  result['reference_trajectory_to_physical_link']={'trace_id':p['trace_id'],'source_line':p['source_line'],
   'utc_iso':p['utc_iso'],'position_source':p['position_source'],'longitude':p['longitude'],'latitude':p['latitude'],
   'physical_gmns_link_id':p['gmns_link_id'],'source_route_id':p['source_route_id'],
   'link_class':link['mcl_link_class'] if link else None,'distance_m':p['link_distance_m'],
   'continuity':p['continuity'],'caution':'SPAN-CPT+IE reference vehicle, not raw GNSS or representative traffic demand.'}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path(__file__).resolve().parent/'instance')
 p.add_argument('--zone');p.add_argument('--detector');p.add_argument('--stop');p.add_argument('--trajectory-point');a=p.parse_args()
 print(json.dumps(trace(a.instance,a.zone,a.detector,a.stop,a.trajectory_point),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
