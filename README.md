<p align="center"><img src="docs/assets/presentation_r3/framework_overview.png" width="100%" alt="City-neutral framework: GMNS objects and separate population-household/activity preparation feed four stages; observation linkage, static methods and finite space-time CG remain distinct."></p>

# Mobility Computation Lab

**An open-source computational framework for GMNS networks, demand, observation linkage and traffic assignment.**

The reusable objects come first; cities are instances. Networks, zones and explicit units enter shared interfaces. Users can start with supplied vehicle OD, or prepare vehicle demand from a supported person-demand and choice specification. Static assignment and finite space–time column generation are **different model branches**, not interchangeable algorithms for one universal problem.

<p align="center"><a href="#framework">Framework</a> · <a href="#coverage">Case coverage</a> · <a href="#boston">Case 01 · Boston</a> · <a href="#sioux-falls">Case 02 · Sioux Falls</a> · <a href="#run-your-input">Run new inputs</a> · <a href="#mobility-data-support">Open data & tools</a></p>

<a id="framework"></a>
## 01 / The shared framework

### GMNS is the common object contract

`zone / super_zone → centroid / access → physical node / directed link` keeps the different objects distinct. Source-ID mappings connect supplied demand, matched observations and saved outputs without merging their identities. The exchange profile records directions, units, capacities and supported extensions. A nonphysical connector is not a road; a shared link reference does not make two datasets the same trip or observation.

The **framework diagram above is conceptual**. It contains no city geography or empirical values. Actual source-backed objects and record-level demonstrations appear inside each labeled case below. [Data contract](docs/data-contract.md) · [City and hierarchy workflow](docs/city-workflow.md).

### Population, Households & Activity Preparation

Before any optional demand estimation, source statistics and activity evidence need **version, field, unit and geography checks**. Statistical polygons and model zones are different objects: a declared spatial allocation can create zonal population and household attributes with source IDs, coverage and uncertainty limits retained. Activity evidence can supply a separate attraction attribute. A generation model must then declare which attribute it uses; households are one possible input, not a universal rate base. This preparation is **upstream of stage 01**, not a fifth numbered stage or an automatic adapter for every city.

Boston below demonstrates an actual aggregate ACS-to-H3 allocation and transferred household-rate example. Sioux Falls begins with supplied benchmark vehicle OD and has **no estimated demographic stage**. A user with valid vehicle OD may bypass population preparation and stages 01–03. [Boston's exact source fields, allocation and saved-table check](docs/datasets/boston-population-households.md).

<a id="four-step-workflow"></a>
### Four stages, with explicit inputs and outputs

| Stage | Question | Computational object |
|---|---|---|
| **01 · Trip generation** | How much travel is produced and attracted? | Activity/household evidence and a declared model → purpose-specific productions and attractions |
| **02 · Trip distribution** | Where does that travel go? | Margins, impedance and boundary treatment → directed person OD |
| **03 · Mode choice** | Which available alternatives are used? | Absolute costs or a declared pivot model → probabilities and mode demand; occupancy → vehicles |
| **04 · Traffic assignment** | Which paths and roads carry the demand? | A declared network, vehicle demand, period and objective → path/link flows and independent checks |

A four-stage label is not a guarantee of a calibrated regional model. Input support, modeling assumptions and empirical status are recorded per case. **Users who already have vehicle OD can enter directly at stage 04.** No GPS, census or transit feed is required by the generic direct-vehicle entry.

### GPS and service evidence enter through explicit relationships

```text
positions + timestamps → quality checks → road/service matching
                                            ↓
                          a supported interval/cost/parameter input
                                            ↓
                           mode demand and/or network calculation
```

Map matching is a computation, not a property supplied automatically by the GMNS file format. A position sample is not a traffic count, and matched vehicle paths do not automatically reveal all passenger OD. Each application must define what an observation supports. Boston below separates spatial linkage from an exploratory transit-time feedback experiment.

### Methods: choose the mathematical problem before the solver

| Model family | Existing implementations | What the method returns |
|---|---|---|
| **Static, fixed-demand user-equilibrium approximation** | Frank–Wolfe; solved finite-path reference; native Diagnostic L3 with declared reconstruction and constraints | BPR/Beckmann path and link flow under the declared period and units |
| **Finite space–time, fixed-cost capacitated flow** | Arc-flow reference LP; Phase-I feasibility restoration; Phase-II restricted master and pricing / column generation | Time-indexed path columns and capacity use; physical-link back-projection |

Compression changes a representation and requires a checked reconstruction. It is **not** the same operation as time expansion. Diagnostic **L3** is an algorithm profile name, not GMNS Level 3 or stage 03 of the demand model. No unimplemented Bush/ADMM variant is listed as an available solver. [Actual method sources and supported scopes](docs/methods.md).

### Why a space–time network is built before CG

A physical node is replicated as `(node, time)`. A movement connects departure to a later arrival state; waiting stays at the same physical node while advancing time; demand-specific source/sink connections attach departure and arrival support. A path through that network becomes a column in the restricted master. Phase I reduces artificial demand; Phase II optimizes real path cost, with candidate paths supplied by pricing. The same-instance arc-flow LP is a reference, not another city or the static FW objective.

[Construction and master/pricing guide](docs/methods/space-time-cg.md). The detailed **Sioux Falls** section shows an actual local time-network slice, selected column and shared-capacity event. Boston has no supplied case-specific CG run; this is visible in the matrix rather than hidden or filled with invented results.

<a id="coverage"></a>
## 02 / What each case demonstrates

The entries distinguish **available code**, **executed case evidence**, and **the scale at which a method was actually accepted**. A missing result is not a claim that the method can never run on that city. A tiny generic fixture does not certify a large Boston solve.

| Capability / evidence | Boston | Sioux Falls |
|---|---|---|
| GMNS network, zones and access | **Demonstrated:** H3 hierarchy, centroid/access and source-ID round-trip | **Benchmark network:** supplied topology and demand; not a present-day H3 city dataset |
| Population, households and activity preparation | **Demonstrated, limited:** source-backed ACS block-group → H3 aggregate allocation; separate MassGIS attraction proxy | **Not estimated:** classic benchmark supplies vehicle OD without a demographic build |
| Trip generation | **Demonstrated, limited:** ACS households + transferred purpose rates; activity attraction prior | **Not modeled:** benchmark demand is supplied |
| Trip distribution | **Demonstrated, limited:** saved gravity/IPF and PA-to-OD | **Not estimated:** given OD and selected subsets |
| Mode choice | **Demonstrated, conditional:** regional-share feedback and absolute DA/S2/S3/TW research branch | **Not modeled:** fixed vehicle demand |
| GPS / service evidence | **Demonstrated, exploratory:** network linkage and default-off interval feedback; no independent AM validation | **Not included** in the classic benchmark |
| Static Frank–Wolfe | **Demonstrated:** small controls and three expanded tiers, up to 17,522 loaded node ODs | **Demonstrated:** historical static benchmark; input-identity caveat retained |
| Finite full-path reference | **Solved:** 26-OD / 130-path control; **resource-gated** at expanded tiers | Used within the method/source framework; no equivalent solved full-path reference claimed by these supplied records |
| Native Diagnostic L3 / compression | **Accepted numerical controls:** ranks 26/52; new-input fixture; **not solved at expanded tiers** | **Executed numerical candidates:** rank 50; full-network gaps remain 8.17% / 4.38%, not exact UE |
| Space–time network construction | **No Boston run supplied**; reusable code availability is not case execution | **Demonstrated:** finite time-expanded selected-OD instances |
| Phase I / Phase II / pricing | **No Boston CG result supplied** | **Historical runs:** 200 / 250 OD, objective-level arc-LP agreement |
| New-input preparation and solving | **Generic vehicle/person routes implemented**, with declared profiles and optional dependencies | Existing benchmark and external-network interfaces; case-specific scope is explicit |
| Saved checks and visualization | Tables, GMNS tracing, figures, original-space checks | Static checks, space–time traces, phase and capacity evidence |

[Capability definitions and evidence pointers](docs/capabilities.md). Both cases include assignment research; Boston is not only a data/GPS example and Sioux Falls is not the exclusive home of compression.

<a id="boston"></a>
## 03 / Case study — Boston

**What this case demonstrates.** Real-city GMNS object relationships; household/activity-based generation; modeled OD distribution; limited mode-choice branches; exploratory GPS/service linkage; new-input static computation; and FW at increasing demand coverage. It also retains a small **FW / full-path / native L3** control. **Not demonstrated here:** a Boston space–time CG run, full-city empirically calibrated demand, or independent AM accuracy.

| Boston branch | Scope and purpose | Keep it distinct from |
|---|---|---|
| **Semantic service-feedback baseline** | 36 selected zone ODs × three departures; regional baseline shares; about 202.078 / 202.071 assigned vehicle trips | An absolute-cost baseline-choice model or the expanded all-OD run |
| **Conditional ABS_PLANNED control** | 26 road-node ODs, 203.660479 vehicles, frozen 130-path comparison; FW and accepted native ranks 26/52 | Expanded L3 performance |
| **Scalable conditional planned service** | 500 / 2,000 / all 30,790 interzonal source ODs; new absolute attributes and eligible demand | All real Boston traffic or independent behavioral validation |

[Complete Boston case](docs/cases/boston.md) · [Assignment branches and original result files](docs/cases/boston-assignment.md).

<p align="center"><img src="docs/assets/boston/visual_release_r1/mcl_boston_hero.png" width="100%" alt="Dark navy Mobility Computation Lab cover with real Central Boston street and zone geometry on the right."></p>
<p align="center"><small>Central Boston road geometry: GMNS Plus 21_Boston (Apache-2.0), commit 116447ab641cca1ed34797d019c8e704063393c3; H3 zones and cover composition: Mobility Computation Lab. Geography only—not measured or modeled traffic.</small></p>



<a id="gmns-in-action"></a>
### Boston / GMNS in Action

**One network reference for zones, demand, observations, and results.** The actual Boston exchange keeps H3 zone 35, its centroid, nonphysical access connector and physical road node distinct. A documented crosswalk maps zone identities to road access; zonal S1 demand remains modeled panel vehicle trips. A separate saved GPS path occurrence can reference a physical link and its saved S1 road result without claiming it is the same OD or observed journey.

<p align="center"><a href="docs/datasets/boston-gmns-exchange.md#one-network-multiple-connected-data-layers"><img src="docs/assets/boston/gmns_in_action_r1/gmns_connected_layers.png" width="100%" alt="Actual Boston H3 zones 35 and 71, centroid 35, dashed nonphysical access to road node 14285, an OD relation, and a separate GPS-to-link result branch."></a></p>

*Separate objects, explicit relationships. Model access connectors are not physical roads. Shared link references do not imply a shared observed trip.* [Figure records, field mappings and provenance](docs/datasets/boston-gmns-exchange.md) · [Versioned exchange and GMNS Plus profile](examples/boston/gmns_exchange_r1/README.md) · [Read-only relationship lookup](tools/gmns/trace_gmns_figure.py).

From the repository root, inspect the generic relationships with `python -B tools/gmns/boston_exchange.py trace --exchange examples/boston/gmns_exchange_r1/data`; the [exact figure segment query](docs/datasets/boston-gmns-exchange.md#reproduce-the-relationships) is separate. GMNS is the data/exchange contract, not the matching algorithm or evidence of improved prediction. The pinned GMNS Plus Level 2 reader accepted S1/S2 node/link/demand; a separate zone-schema check and the declared `mcl_solver_*` fields support the existing solver round-trip.

### City network workflow

The common foundation is a real city network: **2,852 physical nodes, 5,091 directed links, 177 H3 r9 zones and nine r7 parents**. Zone-access mappings attach demand to roads; ordered link membership defines a corridor; transit and GPS records retain their own identities and connect to the same network. Model access lines are not automatically verified physical routes.

[GMNS-compatible input contract](docs/data-contract.md) · [City and hierarchy guide](docs/city-workflow.md) · [Boston network and data layers](docs/datasets/boston-central.md)

#### GMNS Foundation and Toolchain Alignment

The [versioned Boston exchange](examples/boston/gmns_exchange_r1/README.md) now exposes the actual [GMNS nodes](examples/boston/gmns_exchange_r1/data/node.csv), [directed links](examples/boston/gmns_exchange_r1/data/link.csv), [H3 zones and hierarchy](examples/boston/gmns_exchange_r1/data/zone.csv), and separate [S1](examples/boston/gmns_exchange_r1/data/demand_S1.csv)/[S2](examples/boston/gmns_exchange_r1/data/demand_S2.csv) zonal demand. A [reversible ID/access crosswalk](examples/boston/gmns_exchange_r1/data/id_crosswalk.csv) connects 177 distinct zones to 139 physical access nodes. The pinned GMNS Plus structural reader opened both exports; the adapter reconstructed the accepted physical solver inputs without rerunning the model. [Open/query/rebuild commands and precise scope](docs/datasets/boston-gmns-exchange.md) distinguish core GMNS fields, GMNS Plus conventions, and MCL GPS/service/result extensions. Source-hourly and solver-period capacities remain separate; nonphysical connectors have no invented routing costs. Grid2demand2/competition approval and empirical calibration are not claimed.

<p align="center"><a href="docs/datasets/boston-central.md#boston-visual-gallery"><img src="docs/assets/boston/visual_release_r1/boston_network_zones.png" width="780" alt="Shared Central Boston foundation: physical roads, H3 zones, study boundary and one ordered 23-link corridor."></a></p>

*This is the spatial foundation, not one of the four demand-model stages. Parcel outlines provide geographic context, not building footprints. [Sources, units and original map gallery](docs/datasets/boston-visual-sources.md).*

### Boston / Population and Household Preparation

The **U.S. Census Bureau's ACS 2024 five-year (2020–2024)** block-group estimates were accessed through the **Census Reporter `acs2024_5yr` mirror** for Massachusetts Suffolk `025`, Middlesex `017` and Norfolk `021`; recorded source boundaries came from its `tiger2024` GeoJSON. The fixed core intersects **174 source block groups**. Those statistical polygons do not coincide with the **177 clipped H3 r9 model zones**. In EPSG:32619, each source estimate is assigned by `area(source ∩ clipped zone) / area(full source polygon)`; the outside-core share remains a spatial remainder, **not** an observed external-trip matrix. The allocation assumes uniform persons/households within each source polygon.

| Prepared quantity | Saved core value | Role and source |
|---|---:|---|
| Population, ACS [`B01003`](https://api.census.gov/data/2024/acs/acs5/groups/B01003.html) | **171,049.520 persons** | Retained H3 demographic attribute, not the household-rate multiplier; acquired via [Census Reporter `acs2024_5yr`](https://github.com/censusreporter/census-api/blob/master/API.md) |
| Households, ACS [`B11001`](https://api.census.gov/data/2024/acs/acs5/groups/B11001.html) | **79,537.493 households** | `P_i,p = H_i × r_p` with six transferred [CTPS TDM23.2.0 Table 74 rates](https://ctps.org/pub/tdm23_sc/tdm23.2.0/TDM23.2.0_Structures%20and%20Performance.pdf#page=148) |
| Activity attraction | Separate [MassGIS Property Tax Parcels](https://www.mass.gov/info-details/massgis-data-property-tax-parcels) nonresidential/mixed building-area weights | Proxy attraction margins, **not measured employment** or ACS allocation weights |

<p align="center"><a href="docs/datasets/boston-population-households.md"><img src="docs/assets/boston/population_r1/population_allocation.png" width="100%" alt="Actual saved Suffolk block-group and clipped H3 geometry; the selected area share allocates population and households separately before household-based generation."></a></p>

The [ACS source statistics](examples/boston/population_r1/data/acs_block_group_stats.csv), [source-to-H3 contributions](examples/boston/population_r1/data/acs_block_group_h3_crosswalk.csv), [H3 attributes](examples/boston/population_r1/data/population_or_household_by_zone.csv), [outside-core ledger](examples/boston/behavior_feedback_r1_semantic_fix_r1/data/external_flow_ledger.csv) and [generation rows](examples/boston/behavior_feedback_r1_semantic_fix_r1/data/trip_generation_by_purpose.csv) are directly openable. [Source versions, provider/download links, exact fields, assumptions and no-solver reproduction command →](docs/datasets/boston-population-households.md). Source margins of error were retained; the H3 estimates do not have a validated propagated MOE. All 177 saved zones have source coverage; in general, missing is not zero.

### Boston / The retained semantic four-stage chain

**This retained branch is a fixed-panel service-feedback example. The expanded computation follows in the next section.** The numbered sections below describe the saved Boston implementation—not four generic software components.

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

<a id="how-gps-changes-the-result"></a>
### Boston / How GPS changes the result

**GPS is not an unused map layer, and it is not a fifth stage.** MBTA vehicle positions are matched to the network and related to transit service intervals. In this example, a saved interval observation changes the transit service input; stages 03 and 04 then recompute the dependent response. GPS does **not** determine the regional trip total or the gravity-model OD in this release.

<p align="center"><a href="docs/datasets/boston-gmns-exchange.md#from-gps-coordinates-to-gmns-linked-evidence"><img src="docs/assets/boston/gmns_in_action_r1/gps_to_gmns_evidence.png" width="100%" alt="The same twelve saved route-60 GPS positions before and after saved path association on identical Boston map bounds; ordered matched links join a separate modeled S1 road result."></a></p>

*Source observations → algorithm-derived matching → physical road attributes → separately modeled assignment results.* This **qualified route-60 segment** is a spatial-reference illustration, not the route-749 service-feedback event below or a matching-accuracy test. Its 26 ordered path occurrences and projected positions are saved outputs, not newly matched here. [Shared network reference—not the same observed trip; inspect exact records →](docs/datasets/boston-gmns-exchange.md#from-gps-coordinates-to-gmns-linked-evidence)

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

### Boston / Scalable assignment is now the primary road-flow result

The same 5,091-link clipped network is now evaluated on progressively larger source-zone demand sets using the **new-input generic FW entry**, not a renamed copy of the 26-OD solution. Planned-service costs were computed for new OD records, and the fixed conditional four-mode specification uses their absolute attributes. Unknown four-mode input remains unknown.

| Source-zone OD tier | Selected person trips | Evaluated person trips | Loaded vehicle/PCE trips | Loaded node ODs | Positive physical links | Accepted signed FW gap |
|---|---:|---:|---:|---:|---:|---:|
| **500** | 2,643.767 | 2,413.603 | 1,936.238 | 453 | 1,653 | −4.59×10⁻¹⁶ |
| **2,000** | 8,415.295 | 7,248.674 | 5,815.569 | 1,684 | 1,784 | 5.60×10⁻⁶ |
| **All 30,790 interzonal** | 22,633.470 | 20,231.449 | 16,259.122 | **17,522** | **2,147** | **6.81×10⁻⁶** |

The largest accepted FW result has **133 physical endpoints**, Beckmann objective **73,552.277556 PCE-minutes**, zero maximum OD residual and `2.84×10⁻¹⁴` link reconstruction error. These are checked numerical approximations for a **conditional HBW-midday research cohort**. They do not include all modes, all travelers, external/background traffic or empirical calibration.

<table class="figure-grid"><tr><th>Source zones: selected demand coverage</th><th>Physical roads: accepted all-tier FW</th></tr><tr><td width="50%"><a href="docs/BOSTON_SCALE_RESULTS.md"><img src="docs/assets/boston/scalable_tool_r1/source_zone_all_coverage.png" width="100%" alt="Saved all-interzonal selected source-zone production and attraction coverage."></a></td><td width="50%"><a href="docs/BOSTON_SCALE_RESULTS.md"><img src="docs/assets/boston/scalable_tool_r1/fw_all_flow.png" width="100%" alt="All-tier accepted FW: 17,522 loaded node ODs and 2,147 positive links on the clipped physical network."></a></td></tr><tr><td>30,790 source pairs are not 30,790 loaded physical OD keys. Zone access, input support and same-node accounting remain explicit.</td><td>Model PCE flow, not observed counts. The three tier maps use tier-specific legend maxima; equal colors across tiers do not imply equal values.</td></tr></table>

[500-tier map](docs/assets/boston/scalable_tool_r1/fw_500_flow.png) · [2,000-tier map](docs/assets/boston/scalable_tool_r1/fw_2000_flow.png) · [All-tier endpoint coverage](docs/assets/boston/scalable_tool_r1/endpoint_all_coverage.png) · [Complete scale, runtime and resource records](docs/BOSTON_SCALE_RESULTS.md).

| Expanded method status | 500 tier | 2,000 tier | All interzonal |
|---|---|---|---|
| **FW** | Accepted | Accepted | Accepted |
| **Finite full-path** | Resource gate before solve; 2,261-path pool exists | Valid 8,412-path K5 pool; solve resource-gated | Path-pool preparation gate; not built |
| **Native L3, requested 25% / 50% fractions** | Basis/solve resource-gated | Basis/solve resource-gated | Pool/basis resource-gated |

A separate **new-input two-OD fixture** actually ran finite full path and native L3 with IPOPT. That demonstrates changed-input method execution, not success at the large tiers. Accepted FW points have one positive saved path per loaded OD; larger coverage alone is not proof of a hard route-splitting or compression speedup experiment. No expanded L3 map is fabricated or substituted with FW.


<a id="boston-case--saved-assignment-methods"></a>
### Boston / Small controlled assignment-method comparison

The real-city [Boston case](docs/cases/boston.md) includes **both** the GMNS/four-stage/GPS workflow above **and** executed static assignment methods. The earlier semantic S1/S2 service-feedback example used about **202.078384 / 202.070733** modeled vehicle trips. A separate conditional absolute-attribute choice sensitivity evaluates DA/S2/S3/TW for sufficient-vehicle households: 87 of 108 fixed OD-time objects had known four-mode inputs, 21 remained unknown, and only 78 common objects were road-loaded. Its [saved probabilities and specification](examples/boston/conditional_choice_r1/README.md) are a reduced transfer sensitivity, not calibrated all-mode TDM23 or an independent AM validation.

For the **fixed ABS_PLANNED** algorithm comparison, FW, the solved uncompressed path reference and two native Diagnostic L3 representations all use the same 5,091 physical links, 26 endpoint OD pairs, 203.6604786350987 modeled vehicle trips, heterogeneous BPR costs and frozen 130-path pool. ABS_OBS_EXPLORATORY FW is a separate service scenario, not another compression method or the old S1 export. [Read full method/instance details and the full-size gallery](docs/cases/boston-assignment.md).

| Boston saved method / run | Original Beckmann F (vehicle-minutes) | Original-space result and scope |
|---|---:|---|
| [FW · ABS_PLANNED](examples/boston/assignment_methods_r1/reference/fw_solution.csv) | 707.0579230712884 | Same-network static FW; [actual source](algorithms/static_fw/tap_frank_wolfe.py) |
| [Uncompressed 130-path SLSQP](examples/boston/assignment_methods_r1/reference/full_path_flow.csv) | 707.0579230712882 | Exact saved OD equalities on this finite pool; [solver/config](algorithms/finite_path_reference/README.md) |
| [Native L3 · rank 26 · outer 02](examples/boston/assignment_methods_r1/runs/rank26/outer_02_check.json) | 707.0578811137339 | Max OD residual 8.255328278750085e-7; signed full-network relative gap **−5.933966773022305e-8**; 52 path coordinates + 5,091 links = 5,143 variables |
| [Native L3 · rank 52 · outer 02](examples/boston/assignment_methods_r1/runs/rank52/outer_02_check.json) | 707.0578811562873 | Max OD residual 8.254705861077127e-7; signed full-network relative gap **−5.927948547394401e-8**; 78 path coordinates + 5,091 links = 5,169 variables |
| [FW · ABS_OBS_EXPLORATORY](examples/boston/conditional_choice_r1/fw_abs_obs_exploratory_solution.csv) | 707.043586277782 | **Different demand:** 203.6573680559407 vehicle trips; not a same-instance rank comparison |

The two native points passed declared numerical checks, but their **negative gaps reflect tolerated OD deficits**, not exact feasible equilibria, improved traffic, or roundoff. Their initialization reused the full-path reference. No cold-start acceleration, peak IPOPT memory or independent performance validation is claimed.

<p align="center"><a href="docs/cases/boston-assignment.md#comparison-board"><img src="docs/assets/presentation_r3/boston_method_comparison.png" width="100%" alt="Comparison board: FW and native L3 rank 26/rank 52 on the same small ABS_PLANNED input; below are the two signed micro-scale differences and interpretation."></a></p>

**Read across methods, then down to the signed difference.** The first row compares three absolute-flow maps; the second row gives their differences and interpretation. This is the **small 26-node-OD control**, not the expanded 17,522-node-OD FW run.

Original full-resolution panels remain available: [FW](docs/assets/boston/assignment_methods_r1/boston_abs_planned_fw_flow.png) · [rank 26](docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_flow.png) · [rank 52](docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank52_flow.png) · [rank 26 − FW](docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_minus_fw.png) · [rank 52 − FW](docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank52_minus_fw.png).

*All three absolute maps share one scale; the two signed maps share a zero-centred scale. They can look almost identical because the maximum native–FW link differences are only about **5.89 × 10⁻⁶ modeled vehicle trips**. These are saved model results, not GPS counts. [Inspect all 5,091 full-precision physical-link rows](docs/assets/boston/assignment_methods_r1/boston_abs_planned_assignment_links.csv) · [Source/field/scale manifest](docs/assets/boston/assignment_methods_r1/BOSTON_ASSIGNMENT_FIGURE_SOURCES.json) · [no-solve renderer](tools/visuals/render_boston_assignment.py). GMNS physical link identities and the documented export crosswalk let method outputs attach to the same road network without changing the older S1 demand exchange.*

```bash
python -B tools/mcl_results.py list --case boston
python -B tools/mcl_results.py verify-saved --run boston-abs-planned-full-path
python -B tools/mcl_results.py verify-saved --run boston-abs-planned-l3-rank26-outer02
```

These commands inspect saved points; they do not solve, build paths, refit demand or match new GPS data.

<a id="sioux-falls"></a>
## 04 / Case study — Sioux Falls

**What this case demonstrates.** A classic supplied-demand benchmark with static FW and native L3 research, plus distinct 200/250-OD finite space–time CG instances. **Not modeled here:** real-city trip generation, destination/mode estimation or GPS service feedback. The benchmark does not become a modern city dataset because it shares the framework.

<a id="sioux-falls-benchmark-series"></a>
### Sioux Falls / Static methods and retained benchmarks

The [Sioux Falls case](docs/cases/sioux-falls.md) also has actual static assignment work. Its historical [FW result](docs/datasets/sioux-static-fw.md) has Beckmann F **4,236,715.140437842**, but the retained runtime OD identity is insufficient to declare it a same-input reference for the native profile. The corrected [native Diagnostic L3 implementation](algorithms/path_compression/diagnostic_l3/README.md) has accepted **outer-04** points on the frozen 76-link, 528-positive-OD, 2,218-path static instance (rank 50; 585 reduced path coordinates; 661 total native variables):

| Sioux native configuration | Original Beckmann component F | Max OD residual | Full-network relative cost gap |
|---|---:|---:|---:|
| [A_REG001 · gamma=0.01](examples/sioux-falls/native_l3_r1/runs/SiouxFalls/A_REG001/outer_04_check.json) | 4,325,864.946597109 | 5.548833712509804e-7 | **8.167461%** |
| [B_BECKMANN · gamma=0](examples/sioux-falls/native_l3_r1/runs/SiouxFalls/B_BECKMANN/outer_04_check.json) | 4,289,674.484214505 | 6.957361051718181e-7 | **4.381867%** |

Both pass recorded numerical feasibility, but neither has a full-network UE certificate or new empirical validation. A is regularized and B is not. The separate 200OD/250OD figures below are **historical finite time-expanded CG**, not native-L3 runs or present-day city observations. Sioux demand is exogenous; no real-city GPS/GTFS or Boston-style four-stage estimation was added.

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

### Sioux Falls / From the physical network to time-indexed columns

**The CG examples solve a finite space–time linear flow model with fixed arc costs and explicit capacities.** They are not the same objective as static BPR/Beckmann FW or native L3. Source and sink connectors attach each demand to the time network, movement arcs advance to arrival times, and waiting arcs permit modeled delay.

<p align="center"><a href="docs/cases/sioux-space-time.md"><img src="docs/assets/presentation_r3/sioux_space_time_construction.png" width="100%" alt="Source-grounded exploded local time-network slice with nodes at times zero through six, waiting and movement arcs, the actual selected XS170 path and the master/pricing loop."></a></p>

**This is an explanatory local cutaway—not a plot of every node and arc.** Diagram positions are schematic; the selected IDs and times come from saved records. The highlighted column is `source_XS170 → xs_link19_t0 → xs_link15_t2 → sink_XS170_5_t6`, corresponding to physical nodes `8 → 6 → 5` at times `0 → 2 → 6`. The rest of the horizon and demand-specific connectors are not drawn. [Construction, exact fields and source mappings](docs/cases/sioux-space-time.md).

### Sioux Falls / Phase I restores feasibility, Phase II improves cost

<table class="figure-grid"><tr><th>200 OD · artificial mass clears in round 51</th><th>250 OD · artificial mass clears in round 62</th></tr><tr><td width="50%"><a href="docs/assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png"><img src="docs/assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png" width="100%" alt="Supplied 200-OD artificial-flow trace, starting at 749.807 and clearing in round 51."></a></td><td width="50%"><a href="docs/assets/sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png"><img src="docs/assets/sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png" width="100%" alt="Supplied 250-OD artificial-flow trace, starting at 4082.888 and clearing in round 62."></a></td></tr></table>

| Saved observation | 200 OD | 250 OD |
|---|---:|---:|
| Initial artificial mass | 749.806844 | 4,082.887577 |
| Demands initially carrying artificial mass | 2 | 5 |
| Round when artificial mass becomes zero | 51 | 62 |
| Added Phase-I / Phase-II columns | 51 / 195 | 62 / 255 |
| Final real-column pool | 446 | 567 |
| Final objective / same-instance arc-LP reference | 943,155.589771 | 1,521,090.836620 |
| Absolute objective difference | 2.33×10⁻¹⁰ | 0 |
| Maximum final demand residual / capacity violations | 0 / 0 | 0 / 0 |

The 200-OD selection is contained in the 250-OD selection. There is one recorded run per size, with different iteration/candidate caps. These are **descriptive historical runs**, not repeated runtime trials, a scaling law or a global pricing-closure certificate. The original run summaries explicitly leave `optimality_claimed` and `full_cg_global_convergence_claimed` false.

### Sioux Falls / A new path can help a different OD

At round 34 (200 OD) and round 39 (250 OD), pricing selected a new path for **XS170**, but **XS169** lost 500 units of artificial mass after master reoptimization. XS170's 500 real units moved away from `xs_link21_t1`; XS169's real flow on that binding shared arc grew from 150.193 to 650.193. The total arc load stayed at its 5,050.193 capacity.

<p align="center"><a href="docs/cases/sioux-space-time.md#shared-capacity-event"><img src="docs/assets/presentation_r3/sioux_capacity_exchange.png" width="100%" alt="Before/after shared-capacity accounting: XS170 frees 500 units on a binding arc and XS169 uses them; total capacity use remains constant."></a></p>

This is a recorded coupled-master mechanism, not a proof that this one path was uniquely necessary. The raw capacity dual stays approximately −1 under the saved solver convention. [OD-level supplementary figure](docs/assets/sioux/phase_i_r1/od_level_phase_i_clearance.png) · [Saved trace CSVs](docs/assets/sioux/phase_i_r1/data/200_phase_i_trace.csv) · [Full Sioux CG explanation](docs/cases/sioux-space-time.md).


<a id="run-your-input"></a>
## 05 / Run new inputs, or inspect saved results

**These are two different operations.** The new generic preparation/solve entry computes a fresh result from supplied inputs. The saved-result entries below inspect frozen experiments. A documentation build never silently invokes a solver.

### New vehicle OD → preparation → FW → verification → map

```bash
python -B tools/mcl_assignment.py prepare --input examples/scalable_vehicle_fixture/network --demand examples/scalable_vehicle_fixture/vehicle.csv --config examples/scalable_vehicle_fixture/config.json --output "my results/instance"
python -B tools/mcl_assignment.py solve --instance "my results/instance" --method fw --output "my results/fw"
python -B tools/mcl_assignment.py verify --run "my results/fw"
python -B tools/mcl_assignment.py plot --run "my results/fw" --output "my results/figures"
```

The supported direct-vehicle profile is single-class, fixed-demand and static. It retains text IDs and parallel physical links; units, capacity basis, period and PCE factor are explicit. Unsupported turn-state or class/time inputs are rejected rather than ignored. `prepare`, FW and `verify` use the standard library; plotting and optional native methods have separate dependencies.

A second entry accepts person OD, supported absolute skims, the fixed conditional choice specification and occupancy configuration. It feeds the same vehicle-assignment interface; it is not an arbitrary calibrated choice-model library. [Full new-input contract and commands](docs/RUN_YOUR_OWN_GMNS.md) · [Boston scale profile](examples/boston/scalable_tool_r1/README.md) · [Data and dependency terms](docs/SCALABLE_TOOL_DATA_NOTICE.md).


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

The computational release includes **space–time CG**, **static Frank–Wolfe**, the solved **finite-path Boston reference**, and the corrected **native Diagnostic L3** source/profiles with selected saved Boston and Sioux records. [The method table](docs/methods.md) states their distinct objectives, instances and accuracy scopes; `python -B tools/mcl_results.py list` and `verify-saved --run <run-id>` inspect the released points without solving. Generalized raw-city automation, broader GPS traces and map matching, and origin-based / Policy Bush methods remain research extensions. Coupled primal–dual, Lagrangian and ADMM methods are not newly shipped or validated by this integration. [City workflow](docs/city-workflow.md) · [Roadmap](docs/roadmap.md)

## Project layout

```text
app/src/gmns_dynamic/   Existing network input and space–time CG engine
app/cases/             Self-contained, labelled regression examples
algorithms/static_fw/  Separate static traffic-assignment baseline
algorithms/finite_path_reference/  Boston 130-path SLSQP source/config
algorithms/path_compression/diagnostic_l3/  Corrected native builder and profiles
algorithms/mode_choice_conditional/  Reduced absolute-attribute choice evaluator
examples/boston/assignment_methods_r1/  Saved FW/full-path/native results
examples/sioux-falls/native_l3_r1/  Selected Sioux native results
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
