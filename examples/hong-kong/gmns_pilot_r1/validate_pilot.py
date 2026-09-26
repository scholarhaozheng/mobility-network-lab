"""Portable GMNS-style schema and relationship checks for saved pilot objects."""
import argparse,csv,json,math,sys
from collections import Counter,defaultdict
from pathlib import Path

def table(root,name):
 with (root/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def unique(rows,key):return len(rows)==len({r[key] for r in rows})
def run(root,fixture=None):
 root=Path(root)
 nodes=table(root,'node.csv');links=table(root,'link.csv');zones=table(root,'zone.csv')
 zone_cw=table(root,'zone_source_crosswalk.csv');access=table(root,'zone_access.csv')
 link_cw=table(root,'source_link_crosswalk.csv');det=table(root,'detector_to_link.csv')
 obs=table(root,'detector_observations.csv');stops=table(root,'transit_stops.csv')
 stop_zone=table(root,'stop_to_zone.csv');stop_net=table(root,'stop_to_network.csv')
 route_service=table(root,'transit_route_service.csv');stop_route=table(root,'transit_stop_route.csv')
 pop=table(root,'zone_population_households.csv');pa=table(root,'production_attraction.csv')
 person=table(root,'demand_seed_person.csv');vehicle=table(root,'demand_seed_vehicle.csv')
 movements=table(root,'movement.csv')
 if fixture=='duplicate_link':links.append(dict(links[0]))
 if fixture=='bad_connector':
  next(x for x in links if x['mcl_link_class'].startswith('nonphysical'))['mcl_gps_match_allowed']='true'
 if fixture=='bad_demand':person[0]['d_zone_id']='99999999'
 nid={x['node_id'] for x in nodes};lid={x['link_id'] for x in links};zid={x['zone_id'] for x in zones}
 physical={x['link_id'] for x in links if x['mcl_link_class']=='physical'}
 fine={x['zone_id'] for x in zones if x['super_zone']};parent={x['zone_id'] for x in zones if not x['super_zone']}
 centroids={x['node_id'] for x in nodes if x['node_type']=='model_centroid_nonphysical'}
 connectors=[x for x in links if x['mcl_link_class'].startswith('nonphysical_zone_access_')]
 checks={}
 checks['node_ids_unique']=unique(nodes,'node_id')
 checks['link_ids_unique']=unique(links,'link_id')
 checks['zone_ids_unique']=unique(zones,'zone_id')
 checks['source_link_to_arc_unique']=unique(link_cw,'gmns_link_id')
 checks['link_endpoints_exist']=all(x['from_node_id'] in nid and x['to_node_id'] in nid for x in links)
 checks['fine_parent_fk']=all(x['super_zone'] in parent for x in zones if x['super_zone'])
 checks['centroid_zone_id_equality']=centroids==fine and all(x['node_id']==x['zone_id'] for x in nodes if x['node_type']=='model_centroid_nonphysical')
 checks['one_access_per_fine_zone']={x['zone_id'] for x in access}==fine and unique(access,'zone_id')
 checks['access_node_fks']=all(x['centroid_node_id'] in centroids and x['physical_access_node_id'] in nid for x in access)
 checks['two_nonphysical_arcs_per_access']=len(connectors)==2*len(access) and all(sum(x['from_node_id']==a['centroid_node_id'] and x['to_node_id']==a['physical_access_node_id'] for x in connectors)==1 and sum(x['to_node_id']==a['centroid_node_id'] and x['from_node_id']==a['physical_access_node_id'] for x in connectors)==1 for a in access)
 checks['no_physical_centroid_endpoint']=all(x['from_node_id'] not in centroids and x['to_node_id'] not in centroids for x in links if x['mcl_link_class']=='physical')
 checks['connectors_nonroutable_nonmatchable']=all(x['mcl_gps_match_allowed']=='false' and not x['capacity'] and not x['free_speed'] for x in connectors)
 checks['physical_source_crosswalk_complete']={x['gmns_link_id'] for x in link_cw}==physical
 checks['physical_length_m_positive']=all(float(x['length'])>0 and x['length_unit']=='m' for x in links if x['mcl_link_class']=='physical')
 checks['source_direction_codes']=all(x['source_travel_direction'] in ('1','2','3') for x in links if x['mcl_link_class']=='physical')
 checks['zone_source_crosswalk_complete']={x['zone_id'] for x in zone_cw}==fine and all(0<=float(x['allocation_weight'])<=1 and x['spatial_parent_match_count']=='1' for x in zone_cw)
 checks['population_zone_fk']={x['zone_id'] for x in pop}==fine
 checks['population_area_conservation']=all(abs(float(x['source_population'])*float(x['allocation_weight'])-float(x['population_allocated']))<1e-7 for x in pop)
 checks['person_demand_fine_fk']=all(x['o_zone_id'] in fine and x['d_zone_id'] in fine and x['o_zone_id']!=x['d_zone_id'] for x in person)
 checks['vehicle_demand_fine_fk']=all(x['o_zone_id'] in fine and x['d_zone_id'] in fine for x in vehicle)
 checks['person_demand_nonnegative']=all(float(x['person_trips'])>=0 for x in person)
 checks['vehicle_demand_nonnegative']=all(float(x['volume'])>=0 for x in vehicle)
 checks['production_balance']=all(abs(sum(float(x['person_trip_productions']) for x in pa if x['tier']==tier)-sum(float(x['person_trips']) for x in person if x['tier']==tier))<1e-6 for tier in ('smoke','pilot'))
 checks['detector_link_physical']=all(not x['gmns_link_id'] or x['gmns_link_id'] in physical for x in det)
 checks['observation_link_physical']=all(not x['gmns_link_id'] or x['gmns_link_id'] in physical for x in obs)
 checks['observation_detector_fk']={x['detector_id'] for x in obs}<={x['detector_id'] for x in det}
 stop_ids={x['stop_id'] for x in stops};service_keys={(x['route_id'],x['service_id']) for x in route_service}
 checks['stop_zone_fk']=all(x['stop_id'] in stop_ids and x['zone_id'] in fine for x in stop_zone)
 checks['stop_network_fk']=all(x['stop_id'] in stop_ids and x['physical_node_id'] in nid and x['physical_node_id'] not in centroids for x in stop_net)
 checks['stop_route_service_fk']=all(x['stop_id'] in stop_ids and (x['route_id'],x['service_id']) in service_keys for x in stop_route)
 checks['movement_physical_fks']=all(x['from_link_id'] in physical and x['to_link_id'] in physical and x['via_node_id'] in nid for x in movements)
 if (root/'trajectory_points.csv').exists():
  trajectory=table(root,'trajectory_points.csv')
  checks['trajectory_reference_link_physical']=all(not x['gmns_link_id'] or x['gmns_link_id'] in physical for x in trajectory)
  checks['trajectory_source_distinction']=all(x['position_source']=='SPAN-CPT+IE_ground_truth_reference_not_raw_GNSS' for x in trajectory)
  checks['trajectory_time_monotone']=all(float(b['utc_seconds'])>float(a['utc_seconds']) for a,b in zip(trajectory,trajectory[1:]))
 # Independent edge-list reconstruction from physical GMNS rows.
 arcs={(x['link_id'],x['from_node_id'],x['to_node_id'],x['source_link_id']) for x in links if x['mcl_link_class']=='physical'}
 reconstructed={(x['link_id'],x['from_node_id'],x['to_node_id'],x['source_link_id']) for x in links if x['link_id'] in {c['gmns_link_id'] for c in link_cw}}
 checks['roundtrip_physical_arcs_preserved']=arcs==reconstructed
 passed=all(checks.values())
 summary={'status':'PASS' if passed else 'FAIL','checks':checks,'counts':{'nodes':len(nodes),'physical_nodes':len(nid-centroids),
 'centroids':len(centroids),'physical_links':len(physical),'connectors':len(connectors),'fine_zones':len(fine),
 'super_zones':len(parent),'detector_sites':len(det),'observation_rows':len(obs),'transit_stops':len(stops),
 'person_demand_rows':len(person),'vehicle_demand_rows':len(vehicle),
 'trajectory_reference_points':len(table(root,'trajectory_points.csv')) if (root/'trajectory_points.csv').exists() else 0},
 'scope':'schema and saved-object relationships; not calibration, routability under turn restrictions, or assignment readiness'}
 roundtrip={'status':'PASS' if checks['roundtrip_physical_arcs_preserved'] else 'FAIL','physical_arc_count':len(arcs),
  'crosswalk_arc_count':len(link_cw),'physical_endpoint_count':len({x['from_node_id'] for x in links if x['mcl_link_class']=='physical'}|{x['to_node_id'] for x in links if x['mcl_link_class']=='physical'}),
  'solver_ready':False,'reason':'free speed, lanes and capacity unknown; turn restrictions not enforced'}
 return summary,roundtrip

def main():
 p=argparse.ArgumentParser();p.add_argument('--instance',type=Path,default=Path(__file__).resolve().parent/'instance');p.add_argument('--fixture',choices=['duplicate_link','bad_connector','bad_demand']);p.add_argument('--write-reports',action='store_true');a=p.parse_args()
 summary,roundtrip=run(a.instance,a.fixture)
 if a.write_reports and not a.fixture:
  (a.instance/'GMNS_VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
  (a.instance/'ROUNDTRIP_REPORT.json').write_text(json.dumps(roundtrip,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,indent=2))
 return 0 if summary['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
