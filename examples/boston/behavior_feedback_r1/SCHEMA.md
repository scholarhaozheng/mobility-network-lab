# Behavior-feedback schema

All identifiers—including H3, GTFS, source geography and `use_code`-like fields—are loaded as SQLite `TEXT`; empty scientific values become `NULL`, never zero.

| Table | Primary/unique key | Main foreign-key relationships | Scope |
|---|---|---|---|
| `source_registry` | `source_id` | referenced by parameter/source fields | provenance and redistribution status |
| `parameter_registry` | `parameter_id` | `source_id → source_registry` | values, units, page/table/row and transfer status |
| `zonal_population_households` | `zone_id` | H3 zone used throughout | ACS estimate area-weighted to H3 |
| `trip_generation_by_purpose` | `(zone_id,purpose)` | zone | average-weekday person trips |
| `validation_panel` | `od_id` | origin/destination H3 | 36 frozen HBW pilot OD pairs |
| `od_multimodal_skims` | `(od_id,departure_time,scenario_id,mode)` | panel OD | physical time components, fare and availability |
| `itinerary_legs` | `(path_id,leg_sequence)` | skim `path_id` | access/transfer/ride/egress time account |
| `transit_observations` | `observation_id` | quality-run segment/trip/stops | 13 exploratory exact-trip stop pairs |
| `service_overlay` | `parameter_id` | route/direction/stops and observations | disabled by default |
| `od_mode_probabilities` | `(od_id,departure_time,scenario_id,mu_transit_sensitivity,mode)` | skims/model | nested-pivot sensitivity; not full TDM23 |
| `person_to_vehicle_crosswalk` | composite model key | probabilities/panel/access nodes | occupancy conversion and unresolved TA road legs |
| `assignment_result_by_scenario` | `link_id` | GMNS link | S1/S2 panel-only FW delta |
| `feedback_trace` | `trace_id` | observation/overlay/OD/link | one complete technical dependency chain |
| `feedback_scenario_registry` | `scenario_id` | parent scenario | S0/S1/S2/Srestore execution and validation identity |
| `readiness` | `readiness_area` | source/execution/validation fields | technical versus empirical status by area |

Views `scenario_transit_response` and `end_to_end_feedback_trace` expose the central comparisons. The manifest gives row counts and SHA-256 for every packaged CSV.
