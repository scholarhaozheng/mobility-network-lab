# Run your own static GMNS assignment

This candidate adds an input-driven **single-class, fixed-demand static user equilibrium** workflow. It computes a new result from supplied files. The saved Boston and Sioux Falls pages remain separate inspection examples.

## The two preparation routes

### A. Direct vehicle OD

Provide a directed physical `link.csv`, `vehicle.csv`, and JSON configuration. An optional GMNS `node.csv` is validated for unique IDs and link endpoint membership. This route needs no Boston GPS, ACS, H3, GTFS or old result. The small fixture at `examples/scalable_vehicle_fixture/` includes string IDs, a leading-zero node ID and parallel directed links.

`link.csv` requires unique text `link_id`, text `from_node_id`/`to_node_id`, positive `vdf_fftt` in minutes, nonnegative `vdf_alpha`, positive `vdf_beta`, and positive `capacity`. Optional `geometry` is WKT `LINESTRING`; maps report missing geometry. `is_physical=false` rows are excluded. The solver retains parallel edges by `link_id`. `turn.csv`/`turn_restrictions.csv` and unsupported mode permissions are rejected because this single-class profile cannot model them.

`vehicle.csv` requires `o_node_id,d_node_id,volume` or, with an explicit access crosswalk, `o_zone_id,d_zone_id,volume`. IDs are strings. A crosswalk has `zone_id,access_node_id`; it may map several zones to one physical node. Intrazonal and same-access mass is accounted but not loaded. Structural unreachability fails by default; `exclude_and_account` is explicit in configuration. Demand rows with unmodeled class/time columns are rejected.

Configuration must explicitly declare `scenario`, `period`, `demand_unit`, `period_hours`, `capacity_basis`, and `pce_factor`. Supported demand units: `vehicle_trips_per_period`, `vehicles_per_hour`, `pce_per_hour`. Supported capacity bases: `effective_period_pce` and `hourly_pce_per_lane`. The hourly form multiplies source per-lane capacity by `lanes × period_hours × vdf_plf` exactly once. Vehicle demand is converted to PCE using the declared factor exactly once. For already effective capacity, the input `capacity` is used unchanged. Neither departure sample spacing nor a folder name determines the assignment period.

From the candidate repository root on Windows (replace `python` with the chosen interpreter):

```powershell
python -B tools/mcl_assignment.py prepare --input examples/scalable_vehicle_fixture/network --demand examples/scalable_vehicle_fixture/vehicle.csv --config examples/scalable_vehicle_fixture/config.json --output "my results/instance"
python -B tools/mcl_assignment.py solve --instance "my results/instance" --method fw --output "my results/fw"
python -B tools/mcl_assignment.py verify --run "my results/fw"
python -B tools/mcl_assignment.py plot --run "my results/fw" --output "my results/figures"
```

On POSIX, the same arguments work with `python3` and forward-slash paths:

```sh
python3 -B tools/mcl_assignment.py prepare --input examples/scalable_vehicle_fixture/network --demand examples/scalable_vehicle_fixture/vehicle.csv --config examples/scalable_vehicle_fixture/config.json --output 'my results/instance'
python3 -B tools/mcl_assignment.py solve --instance 'my results/instance' --method fw --output 'my results/fw'
python3 -B tools/mcl_assignment.py verify --run 'my results/fw'
python3 -B tools/mcl_assignment.py plot --run 'my results/fw' --output 'my results/figures'
```

`prepare`, `solve fw`, and `verify` use the Python standard library. `plot` needs Matplotlib. No NLP backend is imported for `--help`, preparation, FW or verification. Each completed directory is immutable; a changed input requires a fresh output directory and produces a new signature.

### B. Supplied person OD plus supported skims and choice specification

Provide person OD with text `od_id,o_zone_id,d_zone_id,o_node_id,d_node_id` and an explicit person mass field named in choice configuration. Provide a skim CSV with `od_id,departure_time,scenario_id,mode` plus the absolute drive time/distance and scheduled transit ride/walk/wait/fare/boarding fields consumed by the accepted four-mode source function. Provide `choice_spec.json` and a choice configuration declaring departure weights, the source skim scenario, output scenario, nest scale and DA/S2/S3 occupancies. Example config is under `examples/boston/scalable_tool_r1/`.

```sh
python3 -B tools/mcl_person_choice.py --person-od selected_person_od.csv --skims supported_skims.csv --spec choice_spec.json --config choice_config.json --output choice_result
python3 -B tools/mcl_assignment.py prepare --input physical_gmns_dir --demand choice_result/vehicle_demand.csv --config assignment_config.json --output instance
python3 -B tools/mcl_assignment.py solve --instance instance --method fw --output fw
python3 -B tools/mcl_assignment.py verify --run fw
```

The source model is `REDUCED_TRANSFER_SENSITIVITY_HBW_AUTO_TW_SV_R1`, conditional on sufficient vehicles and four known DA/S2/S3/TW alternatives. Its fixed transferred constants, zero parking/toll/terminal context, 2026-to-2010 fare conversion and research nest scales remain explicit assumptions. Unknown fare, route or permissions leave the entire OD/departure conditional scope unknown; they do not silently renormalize auto choices. A route confirmed unavailable **within the declared search limits** receives a separate non-evaluated scope status, also without car-only renormalization. TW passengers add no road vehicle flow. The conversion is an engineering cohort calculation, not a population estimate or new empirical calibration.

Boston's optional `boston_planned_costs.py` generates *new* supported drive and transit-walk skims from its local accepted road, walk and GTFS inputs. It requires pandas, NumPy, SciPy, NetworkX and pyosmium in the routing interpreter, plus the exact local source files listed in the scale profile. It uses service date 2026-09-21, departures 12:30/12:40/12:50 and no GPS overlay by default. These engineering departure samples each carry one third of each selected saved HBW-midday person OD. It caches completed origin chunks with source hashes. Within one origin/departure, its batch helper shares the destination-independent scheduled-label scan while preserving the original terminal itinerary/fare code. The choice adapter spools intermediate output rows to bound memory. A fully independent city may supply compatible skims instead; the tool does not infer fares, choice parameters or access from a city name.

## Optional finite-path and native Diagnostic L3 methods

The same `solve` entry accepts `--method full-path` and `--method diagnostic-l3` with a method JSON file. It builds an instance-specific loopless path pool (bounded K=1..5) and validates ordered link identities and sparse incidence against the supplied network. The finite-path reference uses SciPy SLSQP and exact OD equalities. A finite path pool may have a small pool gap but a larger full-network gap; both are reported.

Diagnostic L3 requires NumPy, SciPy, Pyomo and a configured IPOPT executable. Its configuration declares a rank fraction, executable path and task-local temporary directory; the runner measures a half-free-physical-RAM ceiling before each method. The adapter uses the accepted isolated Diagnostic L3 mathematical builder, heterogeneous per-link BPR potential, gamma=0, legal zero link flow and hard reconstructed minor-path nonnegativity. It builds a new weighted path-by-link SVD basis for each changed instance, not the frozen 26/52 arrays. The seed is demand on each minimum-free-flow path. An exact feasible seed is assigned to the Pyomo variables at each source-convention outer rebuild. A missing native backend fails explicitly; it never returns an FW result under an L3 label.

## Verification, interpretation and limits

`verify` re-reads the particular prepared instance and raw returned flow. It checks physical-link identity, per-OD demand, original link reconstruction, negative raw values, BPR potential, and a signed full-network shortest-path gap. Declared default gates are maximum OD error `1e-6 + 1e-8 max(1,q)`, relative total OD L1 `1e-8`, full relative gap magnitude `1e-5`, separate negative-flow and link-reconstruction gates. A result within these is a **checked numerical approximation**. A finite path optimum alone is not a global user-equilibrium certificate. Negative signed gaps with demand deficits are reported, not treated as superior objectives.

For a Boston selected source-zone panel, `python -B tools/boston_zone_coverage.py --panel selected_500.csv --zones zone.csv --tier-label 500 --output source-zone-figure` draws source production and attraction separately from the generic prepared-instance endpoint/road maps. Its output CSV retains the H3 zone IDs and person mass; source zones are never recast as physical road nodes.

The result is only the supplied demand on the supplied physical road network. It excludes unmodeled background traffic, endogenous mode/departure response, class interactions, turn-state routing and transit vehicle traffic. Boston HBW midday conditional choice is a scoped research sensitivity. This tool has not been independently calibrated or validated for citywide empirical use.

GMNS core node/link IDs remain text. Boston's GMNS Plus H3 zone, centroid and nonphysical access connector objects remain separate from its physical solver roads. The `mcl_solver_*` extension and reversible crosswalk connect source physical IDs to solver IDs; access arcs do not acquire invented zero-cost routing semantics. New flow tables join the *same physical `link_id` objects* used in the accepted exchange. Code is under the existing MIT notice; GMNS Plus road data, MBTA GTFS and other inputs retain their own terms and are not bundled merely because the code is open source.
