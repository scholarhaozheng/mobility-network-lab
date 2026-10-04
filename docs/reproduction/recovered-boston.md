# Boston: recovered computation and evidence

These entry points add the recovered Boston workflows to the existing repository. They distinguish an actual computation from inspection of an earlier run. Data and source identities are in [the manifest](../../experiments/recovered/boston.json); every listed repository file has a SHA-256. Source transformations are recorded in [SOURCE_PROVENANCE.json](../../examples/boston/recovered-r14/SOURCE_PROVENANCE.json).

## Install and run

Use Python 3.11. The executed checks used Python 3.11.4, NumPy 1.24.3, SciPy 1.10.1, pandas 1.5.3, NetworkX 3.1 and Shapely 2.1.2. This delivery used an existing environment; it does not claim a new clean installation.

~~~sh
python -m venv .venv
# Activate .venv using the command for your operating system.
python -m pip install numpy==1.24.3 scipy==1.10.1 pandas==1.5.3 networkx==3.1 shapely==2.1.2
python tools/mcl_recovered.py list
python tools/mcl_recovered.py describe boston-finite-arc-flow-lp
python tools/mcl_recovered.py check boston-finite-arc-flow-lp
python tools/mcl_recovered.py run boston-finite-arc-flow-lp --output ../runs/boston-lp
python tools/mcl_recovered.py verify boston-finite-arc-flow-lp --run ../runs/boston-lp
~~~

Always use a new output directory. **run** executes the stated computation. **inspect** independently checks the retained evidence and makes zero optimizer calls. **verify** checks an existing output using its original execution receipt. Fresh runs must retain all declared result files; a missing file fails verification and never falls back to a historical result. Saved-evidence inspection is allowed only for an original inspect receipt. The LP objective is recomputed using the pinned graph costs, and inconsistent reported unit costs fail verification. The six executed light commands were GMNS structural validation, ACS allocation arithmetic, household-based production, prepared Srestore choice, finite graph construction and the finite LP. CG and ADMM saved states were inspected; their published run routes were not executed again in this delivery.

## boston-gmns-exchange-r1

The existing [exchange code](../../tools/gmns/boston_exchange.py) checks schemas, IDs, physical directions, effective capacities, nonphysical connectors and joins in the released exchange. The recovered command reports 3,029 export nodes, 5,445 export links, 177 fine-zone access rows and 26 OD rows per S1/S2. It neither reacquires GMNS nor solves assignment. The original export/roundtrip subcommands remain available in that source file.

## boston-acs-population-allocation-r1

Run recomputes area-weighted population and household totals from the released 174 block groups and 724 crosswalk rows; 177 zones sum to 171,049.52015979076 persons and 79,537.49255074753 households. Output is population_or_household_by_zone.csv. The independent original [allocation checker](../../tools/population/verify_saved_allocation.py) is reused. Frozen crosswalk arithmetic does not rerun the geographic overlay. The recovered [regional builder](../../algorithms/recovered_boston/preparation/build_regional_demand.py) contains original Census acquisition/overlay and CTPS production logic; raw reconstruction additionally requires dated ACS 2024/TIGER geometry, clipped zones and the documented activity prior.

## boston-regional-trip-generation-r1

Run computes 6 purpose rates times 177 zone household totals, yielding 1,062 zone-purpose rows and 816,054.67357067 modeled daily person-trip productions. The rates are regional transfers, not locally estimated coefficients. Attractions and OD distribution are separate. The recorded historical pre-semantic distribution must not be silently replaced by a later corrected branch.

## boston-massgis-activity-prior-r1

Inspect checks the released fine/coarse area totals and 50,000 production/attraction margins. Blank source areas remain unknown; they are not asserted to be measured zero. Individual assessment records are not included. The historical source was the [MassGIS property-tax parcel service](https://services1.arcgis.com/hGdibHYSPO59RG1h/ArcGIS/rest/services/Massachusetts_Property_Tax_Parcels/FeatureServer/0), dated 2026-09-17. The manifest records the exact local historical gzip hash so a source acquisition can be compared.

The executable [acquisition script](../../algorithms/recovered_boston/preparation/acquire_activity_sources.py) and [overlay/prior builder](../../algorithms/recovered_boston/preparation/build_activity_demand_prior.py) are included. Work in an external source workspace. Set MCL_BOSTON_SOURCE_ROOT to its absolute directory; these source commands write derived data inside that workspace. Copy the repository's preparation/city_config.json to config/city_config.yaml there. Acquire the official source only if its current terms permit your use. A current service response need not equal the historical snapshot.

~~~powershell
$env:MCL_BOSTON_SOURCE_ROOT = 'D:/my-boston-source-workspace'
python algorithms/recovered_boston/preparation/acquire_activity_sources.py
python algorithms/recovered_boston/preparation/build_activity_demand_prior.py
~~~

The builder requires database/zones/zone.csv, zone_hierarchy.csv, zones/access_runs/boston_quality_r1_20260922/zone_access_review.csv, and database/demand/skim.csv, productions_attractions.csv and od_person.csv in that source workspace. It uses NumPy, pandas, Shapely 2, pyproj and the included city_database._balance_gravity helper; the full source workspace also needs h3. These additional geospatial dependencies and raw reconstruction were not installed/run for this delivery.

**Scope correction:** boston-activity-informed-50000-am-r1 is an activity prior and AM **assignment-ready input**, not a completed assignment. Its original manifest says assignment_run:false. A new assignment would be a new computation.

## boston-transit-walk-semantic-preparation

Inspect checks the saved 36 OD × 3 departure panel, 1,296 skim rows, 87 available transit paths per scenario and the zero-mismatch restore check. The real [multimodal builder](../../algorithms/recovered_boston/preparation/build_multimodal_panel.py) and [fare/transfer adapter](../../algorithms/recovered_boston/preparation/semantic_transit.py) are included.

Raw reconstruction needs the exact historical GTFS SHA 94d12a7645402990f8e246759e5d97e5a65416baa3e201eacba132a1010c0c1e and OSM SHA 5b59c0c4dd1afeac1b3193b239e5953c1315f0484952d136b70aeea48f6fbf4e. The [Mobility Database feed](https://files.mobilitydatabase.org/mdb-437/latest.zip) and [MBTA publisher](https://cdn.mbta.com/MBTA_GTFS.zip) are acquisition routes, not guaranteed historical snapshots. The original snapshot's redistribution was unresolved, so the feed archive is not bundled. Preserve OSM attribution when acquiring its geometry.

In a source workspace provide raw/gtfs/mdb-437_20260918.zip, raw/osm/behavior_feedback_r1/central_boston_highways.osm, database/network/gmns/{node,link}.csv, database/zones/{zone,zone_access}.csv and the processed database/transit GTFS tables. The selected run directory must contain derived/regional_od_h3.csv, gps_service_observation.csv, service_overlay.csv and validation_panel.csv. Install h3, osmium, pyproj and the base numeric environment before invoking:

~~~sh
python algorithms/recovered_boston/preparation/build_multimodal_panel.py --root SOURCE_WORKSPACE --run-dir SOURCE_WORKSPACE/runs/semantic-fixed
~~~

Exact provider snapshot availability, optional dependency pinning and full raw reconstruction remain explicit requirements. The prepared Srestore command below is available without those raw sources.

## boston-gps-network-association

Inspect validates 581 retained path-link association rows against 5,091 physical links and exports the saved aggregate quality summary. Raw vehicle positions are excluded. The included [city database pipeline](../../algorithms/recovered_boston/preparation/city_database.py) implements acquisition, cleaning, segmentation and matching; [quality correction](../../algorithms/recovered_boston/preparation/correct_boston_quality.py) records accepted/rejected evidence separately.

Use the [official MBTA V3 bus-vehicle endpoint](https://api-v3.mbta.com/vehicles?filter%5Broute_type%5D=3). The historical collection used 12 snapshots 15 seconds apart. Repeating live queries now creates a different dated sample, not the original result. Provide an exact snapshot archive to replay that historical association; pin the mapmatching4gmns backend and its recorded configuration before claiming equivalence. That historical backend environment is not certified by this recovered entry.

~~~powershell
$env:MCL_BOSTON_SOURCE_ROOT = 'D:/my-boston-source-workspace'
python algorithms/recovered_boston/preparation/city_database.py --config D:/my-boston-source-workspace/config/city_config.yaml fetch-mbta-gps
python algorithms/recovered_boston/preparation/city_database.py --config D:/my-boston-source-workspace/config/city_config.yaml process-gps
~~~

The source workspace must also have the configured physical matcher network, provider feed and geometry dependencies. No raw observation record is included in the computational download.

## boston-semantic-fix-srestore

Run invokes the preserved [semantic-fixed choice code](../../algorithms/recovered_boston/preparation/run_mode_choice_feedback.py) with frozen skims, base shares, panel and zone access. It recomputes choice probabilities and person/vehicle demand, comparing 2,808 restore rows to the retained output. Prepared choice replay is distinct from rebuilding skims, absolute conditional choice, independent validation and a new FW solve. The original Srestore branch reused S1 assignment because its demand/model signatures matched; no separate Srestore FW solve is invented.

## boston-finite-construction

Run uses the recovered explicit-network builder with 90 physical nodes, 125 links, 10 demands, 3-second steps and 100 horizon steps. It generates 9,110 dynamic nodes and 22,217 arcs. Verification checks identity, endpoints, direction in time, costs, capacities and demand volumes against the frozen graph. The exact graph is shared by LP, CG and ADMM.

## boston-finite-arc-flow-lp

Run solves the 212,990 variable same-graph LP through SciPy HiGHS. The fresh objective 64.39686151152954 agrees with 64.3968615115296; verification independently accumulates commodity balance, shared capacity and objective from positive flows. A finite fixed-cost/hard-capacity benchmark is the claim boundary.

## boston-finite-cg-pilot-r2-r3

The exact R3 run_full_cg_v1.py source hash is ffeb757882dbde635bb3152daced08ac20e134c8e00f4d34dddf637834a6fe90. Its dependency closure and frozen input manifest are included. The runner sets portable input/output paths and retains 120 Phase I rounds, 25 Phase II rounds, 4 candidates per demand and 7,200 seconds maximum runtime. The saved objective 64.39686151152952 and feasibility were independently recomputed here with zero optimizer calls. R3 by itself did not pass the later independent full-DAG closure check.

~~~sh
python tools/mcl_recovered.py inspect boston-finite-cg-pilot-r2-r3 --output ../runs/boston-cg-saved
# To perform a new, potentially lengthy solve:
python tools/mcl_recovered.py run boston-finite-cg-pilot-r2-r3 --output ../runs/boston-cg-new
~~~

## boston-finite-cg-r4-pricing-closure

The run command continues from the preserved R3 pool through the recovered R4 RMP/independent-pricing routine. Inspect reruns only the independent evaluator on the retained final pool, dual and solution; it confirms 10 demand closure checks and objective 64.39686151152954. It does not call an optimizer. The original numerical policy remains 25 rounds, 100 added columns and 7,200 seconds; machine-specific directories alone were replaced by explicit runner paths.

## boston-admm-r2-s

The existing public ADMM solver is reused with newly included Boston graph, policy and compressed full state. Inspect recomputes conservation, capacity, KKT, consensus projection, dual update and objective from that state. Saved 253 iterations produce objective 64.3972916554108, capacity excess 9.2438249e-7 and maximum balance residual 7.6202239e-8. Run performs a new frozen R2_S solve, then the same independent checks; no new ADMM solve was performed for this delivery.

The separate Boston Lagrangian P07 result remains a failed 1% gap gate, and expanded finite-path/Native L3 attempts remain not run/resource gated. This release does not change those scientific conclusions.
