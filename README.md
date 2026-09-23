<p align="center"><img src="docs/assets/boston/visual_release_r1/mcl_boston_hero.png" width="100%" alt="Dark navy Mobility Computation Lab cover with real Central Boston street and zone geometry on the right."></p>
<p align="center"><small>Central Boston road geometry: GMNS Plus 21_Boston (Apache-2.0), commit 116447ab641cca1ed34797d019c8e704063393c3; H3 zones and cover composition: Mobility Computation Lab. Geography only—not measured or modeled traffic.</small></p>


<p align="center">
  <a href="#four-step-workflow">Four-step workflow</a> ·
  <a href="#how-gps-changes-the-result">GPS → model response</a> ·
  <a href="docs/datasets/boston-behavior-feedback.md">Boston results</a> ·
  <a href="#quick-start">Run the saved example</a> ·
  <a href="#mobility-data-support">Open data</a> ·
  <a href="docs/visualizations.md">Visual results</a>
</p>

# Mobility Computation Lab

**From city activity to travel demand, mode choice and road flows.**

Mobility Computation Lab connects city data and transportation calculations through a common **GMNS road network, spatial zones and explicit data relationships**. The Central Boston example makes the four-step workflow visible: **trip generation → trip distribution → mode choice → traffic assignment**. Transit observations form a separate input that changes service costs and propagates to mode demand and road flows.

The project also provides reusable space–time column generation, a separate static Frank–Wolfe baseline, historical Sioux Falls results, and Open Mobility Data Visibility tools. **Boston demonstrates the connected workflow; it does not replace the broader network-computation project.**

## City network workflow

The common foundation is a real city network: **2,852 physical nodes, 5,091 directed links, 177 H3 r9 zones and nine r7 parents**. Zone-access mappings attach demand to roads; ordered link membership defines a corridor; transit and GPS records retain their own identities and connect to the same network. Model access lines are not automatically verified physical routes.

[GMNS-compatible input contract](docs/data-contract.md) · [City and hierarchy guide](docs/city-workflow.md) · [Boston network and data layers](docs/datasets/boston-central.md)

<p align="center"><a href="docs/datasets/boston-central.md#boston-visual-gallery"><img src="docs/assets/boston/visual_release_r1/boston_network_zones.png" width="780" alt="Shared Central Boston foundation: physical roads, H3 zones, study boundary and one ordered 23-link corridor."></a></p>

*This is the spatial foundation, not one of the four demand-model stages. Parcel outlines provide geographic context, not building footprints. [Sources, units and original map gallery](docs/datasets/boston-visual-sources.md).*

## Four-step workflow

**Four questions. Four calculations. Four inspectable outputs.** The numbered sections below describe the saved Boston implementation—not four generic software components.

| Stage | Question and actual calculation | What you can inspect |
|---|---|---|
| **01 · Trip generation** | How many trips start and end in each zone? Area-allocated ACS household estimates are multiplied by transferred regional rates by purpose; MassGIS activity supplies attraction weights. | [Zonal productions and six purpose totals](docs/datasets/boston-behavior-feedback.md#step-1-trip-generation): **816,054.67 modeled workday person trips**, not observed trips. |
| **02 · Trip distribution** | Where do those trips go? Gravity/IPF and purpose/time-specific PA-to-OD conversion create directed demand. | [The saved 177 × 177 HBW midday matrix](docs/datasets/boston-behavior-feedback.md#step-2-trip-distribution), totaling **22,807.22 modeled person trips**. |
| **03 · Mode choice** | Which travel alternatives are selected? Scheduled and observation-adjusted journey costs drive a nested response around regional baseline shares. | [Saved S1/S2 costs and probability changes](docs/datasets/boston-behavior-feedback.md#step-3-mode-choice). S1 is still a shared regional baseline, not an OD-specific absolute-cost model. |
| **04 · Traffic assignment** | Which roads carry the resulting vehicles? The selected private/occupied-vehicle demand is loaded through the same static FW model. | [S1 road flows and S2−S1 differences](docs/datasets/boston-behavior-feedback.md#step-4-traffic-assignment), with input and result tables. |

**The scope narrows deliberately:** regional generation → saved HBW demand → **36 fixed OD pairs × three midday departures** → **78 eligible OD–time cases** → about **202 assigned vehicle trips**. These are different populations and units, not one mass-conserving funnel. The remaining 30 cases retain their exclusion and person-demand records; the full regional demand is not assigned by this panel.

<table>
<tr><th>01 · Actual generation output</th><th>02 · Actual distribution output</th></tr>
<tr>
<td width="50%"><a href="docs/datasets/boston-behavior-feedback.md#step-1-trip-generation"><img src="docs/assets/boston/four_step_results_r1/step1_generation.png" width="100%" alt="Trip generation: saved modeled workday productions summed by the six source purpose codes."></a></td>
<td width="50%"><a href="docs/datasets/boston-behavior-feedback.md#step-2-trip-distribution"><img src="docs/assets/boston/four_step_results_r1/step2_distribution.png" width="100%" alt="Trip distribution: saved HBW midday origin-destination matrix in stable H3 ID order, with a declared log color scale."></a></td>
</tr>
<tr><td>Households and regional effective mean rates generate the modeled total. This is a result chart—not the residential-area input map.</td><td>Rows are origins and columns are destinations. These are modeled OD values, not GPS-inferred trips or mapped routes.</td></tr>
<tr><th>03 · Actual mode response</th><th>04 · Actual assignment output</th></tr>
<tr>
<td><a href="docs/datasets/boston-behavior-feedback.md#step-3-mode-choice"><img src="docs/assets/boston/four_step_results_r1/step3_mode_response.png" width="100%" alt="Mode choice: saved S2 minus S1 percentage-point changes for all nine model leaves in panel_od_019 at 12:30."></a></td>
<td><a href="docs/datasets/boston-behavior-feedback.md#step-4-traffic-assignment"><img src="docs/assets/boston/visual_release_r1/boston_panel_flow_s1.png" width="100%" alt="Traffic assignment: modeled S1 fixed-panel vehicle trips on the actual Boston road network."></a></td>
</tr>
<tr><td>The illustrated response depends on this OD's changed service costs. The common S1 shares are not newly estimated local baseline probabilities.</td><td>Static FW loads the selected vehicle panel. No regional background flow is included; this is not measured citywide congestion.</td></tr>
</table>

[**Read the four stages with their inputs, operations and outputs →**](docs/datasets/boston-behavior-feedback.md) · [Download the display data and check the source mapping](docs/datasets/boston-four-step-sources.md)

## How GPS changes the result

**GPS is not an unused map layer, and it is not a fifth stage.** MBTA vehicle positions are matched to the network and related to transit service intervals. In this example, a saved interval observation changes the transit service input; stages 03 and 04 then recompute the dependent response. GPS does **not** determine the regional trip total or the gravity-model OD in this release.

```text
Vehicle positions → road/service linkage → interval-time adjustment
                                               ↓
                 transit itinerary and travel cost
                                               ↓
                03  mode-share response → vehicle demand
                                               ↓
                04  FW road assignment → link-flow response
```

One saved trace uses route **749**, direction **1**, stop pair **1788 → 5093**: **86 s sample-derived elapsed time versus 180 s planned**. Applying the declared exploratory interval adjustment gives the following result for **panel_od_019 at 12:30**:

| Quantity in the same OD–departure case | S1 · planned service | S2 · exploratory adjustment |
|---|---:|---:|
| Transit journey time | 29.052 min | 27.486 min |
| Selected-itinerary fare | USD 1.70 | USD 1.70 |
| Walk-access-transit probability, μ_transit = 1 | 4.0990% | 4.2246% |
| Private/occupied ride-service demand | 2.164631 vehicle trips | 2.161796 vehicle trips |

Across the **whole eligible panel**, S1/S2 vehicle inputs are **202.078384 / 202.070733**. Seventy-eight links differ by more than `1e-10`; the maximum absolute link difference is **0.006603 modeled vehicle trips**. A link difference aggregates contributing OD cases and is not attributable solely to the one trace above.

**Srestore** switches the service overlay off and independently recomputes the affected costs, probabilities and demand, returning them to S1. This demonstrates an executable dependency, not independent prediction accuracy. The 13 interval adjustments each have one supporting event and are disabled by default.

[**Follow the exact observation → parameter → itinerary → probability → vehicle → road records →**](examples/boston/behavior_feedback_r1_semantic_fix_r1/FEEDBACK_TRACE.md) · [See the saved S2−S1 road map](docs/datasets/boston-behavior-feedback.md#step-4-traffic-assignment) · [Inspect the separate GPS-to-road projection illustration](docs/datasets/boston-central.md#one-saved-transit-position-projection)

*The projection map illustrates a different recorded segment; it is not presented as the same event as this feedback trace. The released calculation is a bounded technical example: no independently validated AM forecast, complete TDM23 reproduction or full-city multimodal assignment is claimed. [Scope and assumptions](docs/datasets/boston-behavior-feedback.md#scope-and-assumptions).*

## Sioux Falls benchmark series

Explore the actual saved results before running an example. The two panels below are **different selected-OD benchmark instances**, not a comparison of algorithms on the same demand.

<table>
<tr>
<th>Sioux Falls · 200 OD</th><th>Sioux Falls · 250 OD</th>
</tr>
<tr>
<td width="50%"><a href="docs/datasets/sioux-200od.md"><img src="docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="100%" alt="200-OD selected subset: final physical-link movement flow"></a></td>
<td width="50%"><a href="docs/datasets/sioux-250od.md"><img src="docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png" width="100%" alt="250-OD selected subset: final physical-link movement flow"></a></td>
</tr>
<tr>
<td>24 nodes · 64 selected links · 446 final columns<br><a href="docs/datasets/sioux-200od.md">Open 200-OD results →</a></td>
<td>24 nodes · 69 selected links · 567 final columns<br><a href="docs/datasets/sioux-250od.md">Open 250-OD results →</a></td>
</tr>
<tr>
<td><a href="docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png"><img src="docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png" width="100%" alt="200-OD Phase-II objective trace from saved successful results"></a></td>
<td><a href="docs/assets/benchmarks/sioux_250od_phase2_objective_trace.png"><img src="docs/assets/benchmarks/sioux_250od_phase2_objective_trace.png" width="100%" alt="250-OD Phase-II objective trace from saved successful results"></a></td>
</tr>
</table>

*Map line width represents final movement flow accumulated over the modelled time horizon. These are schematic physical-link views, not observed traffic, static V/C or a full 528-OD assignment. Opposite directions can overlap in the existing map rendering; use the data cards for numerical interpretation.*

| Road benchmark | Physical nodes | Selected links | OD pairs | Final columns | Objective | Access |
|---|---:|---:|---:|---:|---:|---|
| [Sioux Falls · 200 OD](docs/datasets/sioux-200od.md) | 24 | 64 | 200 | 446 | 943,155.589771 | Historical result record |
| [Sioux Falls · 250 OD](docs/datasets/sioux-250od.md) | 24 | 69 | 250 | 567 | 1,521,090.836620 | Historical result record |
| [Sioux Falls · static FW](docs/datasets/sioux-static-fw.md) | 24 | 76 | 528 | — | 4,236,715.140438 | Approximate static baseline |

[**All six benchmark figures**](docs/visualizations.md) · [Network and example catalog](docs/datasets.md) · [Verification scope](docs/outputs.md)

Historical road records include checked results and approved figures, **not redistributed raw inputs**. Self-contained [synthetic reference inputs](docs/examples.md) are bundled separately for installation and regression testing. Static FW and space–time CG solve different model formulations; their objective values are not directly comparable.

## Mobility data support

### Open mobility evidence

**Explore the data behind a city model, then prepare the records you need.** Selected Open Mobility Data Visibility (OMDV) results now include a downloadable, non-geometric 11,422-city evidence table and actual source-record → content-SHA → city relationships. The executable tools query those records, organize local catalogs and inspect a user-supplied GTFS ZIP.

<!-- open-evidence-overview:start -->
<table>
<tr>
<td width="50%" data-evidence-layer="global_city_frame"><b>11,422 urban centres</b><br><a href="docs/open-data.md#global-city-frame">City frame &amp; catalog visibility</a><br>A common GHSL study frame with explicitly defined catalog-matching scenarios.</td>
<td width="50%" data-evidence-layer="gtfs_static"><b>2,959 cities with GTFS stop evidence</b><br><a href="docs/open-data.md#gtfs-static">Scheduled-transit evidence</a><br>4,425 unique parseable content hashes in the all-retained view; city evidence uses inside-polygon stops.</td>
</tr>
<tr>
<td data-evidence-layer="gtfs_realtime"><b>2,465 endpoint representatives</b><br><a href="docs/open-data.md#gtfs-realtime">GTFS-Realtime source context</a><br>Metadata accounting and bounded snapshot classifications, not a live health monitor.</td>
<td data-evidence-layer="osm_map_features"><b>29 regional extracts</b><br><a href="docs/open-data.md#osm">OSM map-feature evidence</a><br>791 of 916 sampled urban-centre rows have bbox-joined point-feature evidence.</td>
</tr>
<tr>
<td data-evidence-layer="gbfs_shared_mobility"><b>1,516 shared-mobility registry rows</b><br><a href="docs/open-data.md#gbfs-and-shared-mobility">GBFS source context</a><br>48 countries represented; location strings are not reviewed city matches.</td>
<td data-evidence-layer="model_interoperability"><b>13 standards and tools</b><br><a href="docs/interoperability.md">Model-interface crosswalk</a><br>GMNS, TNTP, GTFS and related formats: references and reuse pathways, not thirteen bundled converters.</td>
</tr>
</table>
<!-- open-evidence-overview:end -->

These evidence layers are not additive. Each value is tied to its own unit, source frame and retained research snapshot. They do not measure live service coverage or the number of runnable city models. The public release includes a **selected result projection**, provenance and executable tools—not raw feeds, provider URLs, geometry or live endpoint checks. [Browse/download 11,422 city rows](docs/open-data-explorer.md) · [Sources and reproduction scope](docs/open-data-sources.md) · [Trace each metric](docs/omdv-provenance.md)

### Query evidence and prepare your own records

The authorized OMDV workflow normalizes a user-supplied feed catalog and city table, performs exact city/country **named-entity matching**, and writes standardized records, unmatched/ambiguous statuses and quality checks.

```bash
python -m pip install -r requirements-data-tools.txt
python -B tools/mcl_data.py catalog-city-match --catalog examples/data-tools/feeds_sample.csv --cities examples/data-tools/external_city_universe_sample.csv --output results/data-tools-demo
python -B tools/mcl_data.py query-city --name "Hong Kong" --country CHN --include-relations
python -B tools/mcl_data.py process-gtfs --zip path/to/feed.zip --output results/gtfs-content-report
```

`query-city` prefers the stable city ID and explicitly rejects duplicate name/country keys unless `--all-matches` is requested. `process-gtfs` reuses the authorized OMDV content parser with a streamed stop-times pass; it makes no network request and does not extract or modify the ZIP. These are evidence/content tools, not GPS-to-road matching, traffic-zone creation, OD estimation or an automatic connection to the solver.

[**Browse city evidence**](docs/open-data-explorer.md) · [**Use the data tools**](docs/data-tools.md) · [**Explore all six evidence layers**](docs/open-data.md) · [**Connect data to the city workflow**](docs/city-workflow.md)

## Quick start

Use a compatible Python environment and install the network-workflow dependencies. The source has been exercised with Python 3.12 and 3.13; see the [tested profiles and installation guide](docs/getting-started.md).

```bash
python -m pip install -r requirements.txt
python tools/mnl.py catalog
```

Run the self-contained capacity regression from network and demand tables:

```bash
python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode auto --seed-k 1 --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo
```

Open `results/capacity-demo/report.html`. The reference example allocates 3 units to one route and 7 to the alternative, with objective **27**. This is a labelled regression example, not a city dataset. Use a new output directory for each run.

To inspect the **saved** Central Boston feedback results without rerunning a model, use the included compact component and a new output directory:

```bash
python -B examples/boston/run_saved_example.py --data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1" --output "results/boston_saved_example"
```

The command rebuilds a query database from the released CSVs and exports five saved-result queries; it does not acquire sources, fit parameters, run FW/CG or validate predictions. The [saved-result guide](examples/boston/SAVED_EXAMPLE.md) also explains how to point `--data-dir` at `public_component` after extracting the separate full data asset. The trusted code stays beside the wrapper in this checkout.

## Use your own network

Declare node/link/demand fields, units and zone-access rules in `case.json`, then use the same numerical entry point:

```bash
python tools/mnl.py validate --input /path/to/network/input --config /path/to/network/case.json
python tools/mnl.py run --input /path/to/network/input --config /path/to/network/case.json --seed-mode auto --seed-k 5 --output results/network-run
python tools/mnl.py verify --run results/network-run
```

The current CG profile uses one-minute steps, positive integer travel times, a common departure time, fixed costs, continuous path flows and shared hard arc capacities. [Read the exact contract](docs/data-contract.md) before adapting a dataset; this is not a general static user-equilibrium or unrestricted city-scale DTA interface.

**Network + demand → route initialization → explicit space–time network → reference LP + Phase-I/II → final pool, flows and duals → independent checks.**

The allowed network is independent of the initial route pool. Every column in the last successfully solved pool is exported, including zero-flow columns. Reference agreement and independently established pricing closure are distinct statements.

## Tools, methods and extensions

[GMNS](https://github.com/zephyr-data-specs/GMNS) supplies the common network vocabulary. [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset), [OSM2GMNS](https://github.com/asu-trans-ai-lab/OSM2GMNS), [grid2demand](https://github.com/asu-trans-ai-lab/grid2demand) and [TAPLab](https://github.com/asu-trans-ai-lab/TAPLab) are upstream data/tools with their own implementations and licenses. A reference link is not evidence of a bundled executable integration.

The computational release includes **space–time CG** and a separate **static Frank–Wolfe** implementation. Central Boston exercises hierarchical zones, engineering OD generation and real bus GPS matching through the existing static FW core. Generalized raw-city automation, broader GPS traces and map matching, and origin-based / Policy Bush methods with forward-flow and backward-value computations remain research extensions. Coupled primal–dual, Lagrangian and ADMM methods also remain research extensions, not shipped solvers. [Methods](docs/methods.md) · [City workflow](docs/city-workflow.md) · [Roadmap](docs/roadmap.md)

## Project layout

```text
app/src/gmns_dynamic/   Existing network input and space–time CG engine
app/cases/             Self-contained, labelled regression examples
algorithms/static_fw/  Separate static traffic-assignment baseline
launcher/              Saved-output verification
src/mobilitylab/        Authorized metadata tools and supporting adapters
catalog/               Network records, evidence summaries and provenance
schemas/               Explicit input and output contracts
docs/                  City workflow, visual results and project website
tools/                 User commands, documentation build and checks
```

## Contributing, citation and licenses

Contribute a traceable city/network instance, a focused adapter, a verification improvement or a documented method. Keep observed, estimated and synthetic inputs distinct. [Contribution guide](CONTRIBUTING.md) · [Add a network](docs/add-a-network.md) · [Citation](docs/citation.md)

Original code in the public tree is distributed under [MIT](LICENSE) within the stated authorization scope. Datasets and third-party tools retain their own terms. See [data licenses](DATA_LICENSES.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [data access](docs/data-access.md).
