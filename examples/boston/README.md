# Central Boston corrected public research component

This is a bounded, source-backed Central Boston example. It is not an official forecast, a calibrated demand model, or evidence of observed congestion.

The separately packaged [behavior-feedback pilot](behavior_feedback_r1/README.md) adds ACS-linked demand evidence, real-network multimodal skims, a nested-choice sensitivity and an auditable GPS-to-FW trace without relabelling the existing AM baseline.

## Current correction and activity-prior runs

- Run: `boston_quality_r1_20260922`; all selected derived outputs carry the same configuration signature.
- Activity run: `boston_activity_prior_r1_20260922`; it preserves the corrected network, GPS evidence, 177 r9 zones, nine r7 parents, and the legacy network-proxy scenario.
- The activity run uses an official MassGIS parcel-assessment slice with 54,411 assessment records and 13,585 unique parcel geometries. Boston FY2023 and Cambridge FY2026 are both present; personal owner, mailing, contact, site-address, and registry fields were not requested.
- Parcel polygons were intersected with the existing clipped r9 zones in EPSG:32619. Every assessment feature retains an explicit outside-core weight, and r7 values are sums of r9 results rather than a second overlay.
- Raw GMNS files, the retained MBTA GTFS archive, and 12 raw vehicle-position snapshots remain local and byte-unchanged; they are not redistributed here.
- Of 235 GPS segments, 205 were not selected, 2 selected attempts returned no route, and 28 returned a route. Only 9 of those 28 pass the joint spatial, temporal, along-route, detour, and topology rules. Route return is not a quality pass.
- The saved GPS capture is 2026-09-21 12:28:57–12:55:19 Boston local time. It does not overlap the 2026-09-22 07:00–09:00 engineering assignment window and is not used to calibrate that assignment.
- Demand is vehicle trips over two hours. The existing capacity adapter interprets GMNS source capacity as PCE/hour/lane; assignment capacity is `source_capacity × lanes × 2 hours × vdf_plf`. The schema supports that convention, but no Boston-snapshot configuration proving the authored unit was found, so this remains an explicit engineering interpretation. Stress divides that effective capacity by 1.2.
- Full engineering demand relations are included. `demand_top_1000` is no longer presented as a rebuild input.
- The new activity-informed prior scales official residential area to the production margin and official nonresidential/mixed building area to the attraction margin. The 50,000 daily total, gravity beta, mode shares, AM share, and vehicle occupancy remain assumptions; this is not calibrated or observed travel.

## Build and query in this directory

Only Python's standard library is required by the public database builder and query helper.

```bash
python build_public_database.py --output rebuilt.sqlite
python query_boston.py --database rebuilt.sqlite --list
python query_boston.py --database rebuilt.sqlite road --limit 5
python query_boston.py --database rebuilt.sqlite gps-quality --limit 10
python query_boston.py --database rebuilt.sqlite capacity --limit 10
python query_boston.py --database rebuilt.sqlite demand --limit 5
python query_boston.py --database rebuilt.sqlite activity-zone --limit 5
python query_boston.py --database rebuilt.sqlite activity-sources
python query_boston.py --database rebuilt.sqlite activity-accounting
```

`queries/public_acceptance_queries.sql` covers the corrected baseline. `queries/activity_prior_queries.sql` adds seven executed activity/prior checks, including a source-record allocation and a full OD-chain example. The CSV files beside them are query outputs, not hand-written examples.

## Contents and boundaries

- `data/`: physical GMNS road slice, the preserved network-proxy scenario, corrected assignment tables, GPS relations, and `activity_prior_r1/` with actual assessment activity, crosswalks, an independent demand prior, comparisons, and assignment-ready input.
- `sources/activity_prior_r1/`: the privacy-minimised official source slice, metadata, selected-field dictionary, coverage, hashes, LODES acquisition status, and quality reports.
- `map/`: the corrected 18-layer network/GPS map plus a self-contained four-layer H3 activity-prior map. Neither loads an external basemap.
- `CAPACITY_BASIS.md`: unit evidence and conversion formula.
- `DATA_SOURCES.md`: source, license, and redistribution boundaries.

The legacy activity basis remains a labelled road-accessibility proxy. The independent new prior is no longer network-derived at its production and attraction inputs, but it is still an uncalibrated engineering scenario after those inputs. LODES was not acquired because the official host timed out after bounded retries, so no residence–workplace employment association is claimed. The corrected bus time-scale fit remains a development diagnostic and does not enter either demand scenario.
