# Central Boston GMNS exchange r1

This is a **data-interface view of the accepted Boston result**, not a new model run. Open [zone.csv](data/zone.csv), [node.csv](data/node.csv), [link.csv](data/link.csv), [S1 zonal demand](data/demand_S1.csv), [S2 zonal demand](data/demand_S2.csv), [ID crosswalk](data/id_crosswalk.csv) or the [machine manifest](data/manifest.json) directly. The selected GMNS Plus reader consumed node/link/demand for both scenarios at structural Level 2 with zero errors and zero warnings; its Level 2 path does not parse `zone.csv`, which our separate pinned-schema runner checks. These results do not establish ODME, routed-centroid costs, empirical calibration or a teacher/competition approval.

The community schema is [GMNS](https://github.com/zephyr-data-specs/GMNS) `0.96` at commit `4e51f4c7893f5df2c8c69ab21c5dc0abd9b69f48`; exact [schema snapshots](schema/) and [profile identity](TARGET_PROFILE.json) are retained. The consumer is [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset) at commit `116447ab641cca1ed34797d019c8e704063393c3`. Its unmodified structural reader is bundled [here](../../../tools/gmns/vendor/GMNS_Plus_Readiness_Validator.py), with a wrapper that blocks its unused DTALite assignment path.

The active 177 H3 r9 zones are mapped reversibly to integers 1–177. Nine r7 parents are aggregation metadata, not extra demand origins. Each fine zone has its own centroid even where multiple zones share one of 139 physical access nodes. Physical node IDs are `10000 + original node ID`; physical link IDs remain original link IDs. The 354 zone-access arcs are nonphysical and cannot be GPS matched. `node.zone_id` no longer ambiguously carries source TAZ values. All original source TAZs and connectors remain intact in the `source_inputs/source_gmns_plus_21_boston/` asset member ([source identity](SOURCE_LINEAGE.json)), but are inactive in this H3 graph.

The `link.capacity` core field is source PCE/hour/lane; `mcl_solver_capacity_effective` is the accepted two-hour physical solver value. The exporter preserves the entire frozen S1/S2 link row in explicitly prefixed MCL columns so the physical solver input is exactly reconstructible. The original `dir_flag` describes WKT orientation; `directed=true` describes travel. Blank connector speed/capacity/length is intentional: a structural reader can parse this graph, but generic routing through its centroids has **not** been certified. The supported solver adapter collapses zonal OD onto the accepted physical access-node injection without rerunning assignment.

The per-scenario demand CSVs have exactly `o_zone_id,d_zone_id,volume`, in vehicle trips for the fixed midday panel. The saved crosswalk selects S1 `mu=0.25` and S2's accepted FW boundary variant `mu=1.0` before aggregating modes and departures. [selected_demand_ledger.csv](data/selected_demand_ledger.csv) retains the included/excluded row semantics. The full regional 177×177 purpose/time OD is **not** replaced by these 26-row panel tables; it remains in `derived/regional_od_h3.csv` in the separate immutable `BOSTON_BEHAVIOR_FEEDBACK_PUBLIC_DATA_EN.zip` release asset.

The [GPS path relation](data/gps_path_links.csv), [planned GTFS shape-to-link relation](data/transit_shape_conflation.csv), [stop-to-physical-node access candidates](data/transit_stop_route_relation.csv), [ordered corridor membership](data/corridor_link.csv), and [saved road result](data/assignment_result_by_scenario.csv) are MCL evidence/result extensions, not universal GMNS schema tables. The 2,906 stop-route rows without a known access node stay blank, not zero. GPS observations were MBTA V3 JSON positions, not GTFS-Realtime protobuf. Native GTFS feed/route/stop IDs remain distinct from H3 and road IDs. No incomplete GMNS `location` rows have been fabricated.

## Rebuild and inspect (no optimization)

Download/extract the companion `BOSTON_GMNS_SOURCE_INPUTS_R1.zip` data asset to obtain `source_inputs/`. With Python 3.12 and Shapely 2.1, pandas 2.3 and scikit-learn 1.5 for the optional upstream reader (the exporter itself uses the standard library), run from the repository root:

```powershell
python -B tools/gmns/boston_exchange.py export --inputs "path with spaces/input/source_inputs" --output "path with spaces/new export"
python -B tools/gmns/boston_exchange.py validate --exchange "path with spaces/new export" --schema examples/boston/gmns_exchange_r1/schema
python -B tools/gmns/boston_exchange.py roundtrip --exchange "path with spaces/new export" --expected "path with spaces/input/source_inputs" --output "path with spaces/readback"
python -B tools/gmns/boston_exchange.py trace --exchange "path with spaces/new export"
python -B tools/gmns/run_gmns_plus_reader.py --upstream-file tools/gmns/vendor/GMNS_Plus_Readiness_Validator.py --exchange "path with spaces/new export" --level 2 --demand S1
python -B tools/gmns/run_gmns_plus_reader.py --upstream-file tools/gmns/vendor/GMNS_Plus_Readiness_Validator.py --exchange "path with spaces/new export" --level 2 --demand S2
```

The accepted physical files reappear at `readback/S1` and `readback/S2`. [Full mapping, exact status and evidence](../../../docs/datasets/boston-gmns-exchange.md) explain each claim. Road data: GMNS Plus 21_Boston, Apache-2.0. Zone indexing and derived exchange: Mobility Computation Lab. MBTA/MassGIS evidence retains its source-specific rights; this repository's code license is not a blanket data sublicense.
