<p align="center"><img src="docs/assets/presentation_r3/framework_overview.png" width="100%" alt="City-neutral framework: GMNS objects and separate population-household/activity preparation feed four stages; observation linkage, static methods and finite space-time CG remain distinct."></p>

# Mobility Computation Lab

**An open-source computational framework for GMNS city models, four-stage demand, static assignment, and finite space–time optimization.** City networks, travel demand and reproducible network computation.

The reusable objects come first; cities are instances. Networks, zones and explicit units enter shared interfaces. Users can start with supplied vehicle OD, or prepare vehicle demand from a supported person-demand and choice specification. Static assignment and finite space–time capacitated flow are **different model branches**, not interchangeable algorithms for one universal problem.

> **Executed CG evidence is part of the public release—not only a roadmap.** Boston and Hong Kong each have a distinct accepted bounded ten-demand pilot with same-graph arc-flow LP agreement and independent pricing closure for 10/10 demands. Sioux Falls retains separate 200-OD and 250-OD historical selected-OD runs with reference-objective agreement; independent pricing closure is not established for those retained runs. These are three different instances, not one interchangeable citywide result.

<p align="center"><a href="#framework">Framework</a> · <a href="#cg-experiments">Executed CG experiments</a> · <a href="#admm-r2">ADMM R2</a> · <a href="#distributed-assignment">Distributed assignment</a> · <a href="#algorithm-b">Algorithm B</a> · <a href="#coverage">Case coverage</a> · <a href="#boston">Case 01 · Boston</a> · <a href="#sioux-falls">Case 02 · Sioux Falls</a> · <a href="#hong-kong">Case 03 · Hong Kong</a> · <a href="#run-your-input">Run new inputs</a> · <a href="#mobility-data-support">Open data & tools</a></p>

<a id="framework"></a>
## 01 / Shared computational architecture

`network + declared demand → [static BPR/Beckmann: FW / Algorithm B / finite-path / L3]`

`network + selected finite demand + time horizon → [fixed-cost hard-capacity arc-flow LP / CG / Lagrangian / ADMM]`

Population, household, activity, transit and observation preparation may inform a declared demand branch; a supplied vehicle OD can bypass preparation. The static result is **not** a prerequisite for time expansion, and their objectives are not compared numerically.

The **physical network** contains directed physical links. A **finite time-expanded graph** copies its states in time and adds movement, waiting, source and sink arcs. A **generated column** is one feasible source-to-sink time-indexed path. Final time-expanded movement-arc flow is aggregated back to **final physical-link movement flow**. Static BPR/Beckmann and finite fixed-cost hard-capacity problems have different objectives and units.

The same vocabulary and figure order are used below, while each city's scale, evidence and gates remain distinct. [CG method](docs/methods/space-time-cg.md) · [Data contract](docs/data-contract.md) · [Figure source table](docs/data/three_city_r1/THREE_CITY_FINITE_TIME_EXPANDED_STATISTICS.csv).

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
| **Static, fixed-demand user-equilibrium approximation** | Frank–Wolfe; solved finite-path reference; native Diagnostic L3; official `tap-b` Algorithm B with an explicitly named adapter route | BPR/Beckmann path and link flow under the declared period and units |
| **Finite space–time, fixed-cost capacitated flow** | Arc-flow reference LP; Phase-I/II column generation; bounded Sioux/Hong Kong Lagrangian; Sioux/Boston ADMM R2_S | Time-indexed flows and shared-capacity checks; algorithm-specific certificates and physical-link back-projection |

Compression changes a representation and requires a checked reconstruction. It is **not** the same operation as time expansion. Diagnostic **L3** is an algorithm profile name, not GMNS Level 3 or stage 03 of the demand model. [Official `tap-b` Algorithm B results](docs/methods/origin-based-algorithm-b.md) are a separate static assignment branch. [ADMM R2](docs/methods/admm-space-time.md) has selected Sioux and bounded Boston evidence under the finite time-expanded LP contract. [Actual method sources and supported scopes](docs/methods.md).

### Why a space–time network is built before CG

A physical node is replicated as `(node, time)`. A movement connects departure to a later arrival state; waiting stays at the same physical node while advancing time; demand-specific source/sink connections attach departure and arrival support. A path through that network becomes a generated column in the restricted master. **Phase I restores feasibility by clearing artificial flow. Phase II improves the real-path objective.** The arc-flow LP on the same finite time-expanded graph is a reference, not another city or the static FW objective.

[Construction and master/pricing guide](docs/methods/space-time-cg.md). The established Boston/Sioux parallel figures retain their shared vocabulary and reading order; [Hong Kong's separate bounded 10-OD R5 case](docs/cases/hong-kong-space-time.md) now adds its own accepted current-CG and closure evidence. Boston and Hong Kong each have independent pricing closure; neither certificate is imputed to Sioux Falls.

<a id="coverage"></a>
## 02 / Cross-city coverage matrix

| Capability | Boston | Sioux Falls | Hong Kong |
|---|---|---|---|
| GMNS physical network | [Verified](docs/cases/boston.md) | [Verified](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |
| hierarchical zones / parent zones | [Verified bounded case](docs/cases/boston.md) | [Not part of this benchmark](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |
| population / households / activity | [Verified bounded case](docs/cases/boston.md) | [Not part of this benchmark](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |
| transit / pedestrian layer | [Verified bounded case](docs/cases/boston.md) | [Not part of this benchmark](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |
| GPS / detector / trajectory evidence | [Verified bounded case](docs/cases/boston.md) | [Not part of this benchmark](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |
| four-stage demand | [Verified bounded case](docs/cases/boston.md) | [Not part of this benchmark](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |
| static Frank–Wolfe | [Verified bounded case](docs/cases/boston-assignment.md) | [Verified](docs/datasets/sioux-static-fw.md) | [Verified bounded case](docs/cases/hong-kong-static-assignment.md) |
| origin-based / Algorithm B | [Verified bounded case](docs/cases/boston-algorithm-b.md) | [Verified](docs/cases/sioux-algorithm-b.md) | [Verified bounded case](docs/cases/hong-kong-static-assignment.md) |
| full-path / Diagnostic L3 numerical evidence | [Verified bounded case](docs/cases/boston.md) | [Verified bounded case](docs/cases/sioux-falls.md) | [Not demonstrated](docs/cases/hong-kong.md) |
| finite arc-flow LP | [Verified bounded case](docs/cases/boston-space-time.md) | [Verified bounded case](docs/cases/sioux-space-time.md) | [Verified bounded case](docs/cases/hong-kong-space-time.md) |
| column generation | [Verified bounded case](docs/cases/boston-space-time.md) | [Verified bounded case](docs/cases/sioux-space-time.md) | [Verified bounded case](docs/cases/hong-kong-space-time.md) |
| Lagrangian decomposition | [Gated](docs/methods/distributed-assignment.md) | [Verified bounded case](docs/methods/distributed-assignment.md) | [Verified bounded case](docs/cases/hong-kong-space-time.md) |
| ADMM | [Verified bounded case](docs/cases/boston-admm.md) | [Verified bounded case](docs/cases/sioux-admm.md) | [Gated](docs/cases/hong-kong-space-time.md) |
| CG reference-objective agreement | [Reference-objective agreement](docs/cases/boston-space-time.md) | [Reference-objective agreement](docs/cases/sioux-space-time.md) | [Reference-objective agreement](docs/cases/hong-kong-space-time.md) |
| CG independent pricing closure | [Independent pricing closure established](docs/cases/boston-space-time.md) | [Not established](docs/cases/sioux-space-time.md) | [Independent pricing closure established](docs/cases/hong-kong-space-time.md) |
| clean-room / independent evaluator | [Verified bounded case](docs/cases/boston.md) | [Verified bounded case](docs/cases/sioux-falls.md) | [Verified bounded case](docs/cases/hong-kong.md) |

*Status refers to each linked bounded or historical case, not a universal method guarantee. Sioux Falls has no demographic/transit/GPS city-data build; Hong Kong ADMM remains gated.* [Source record](docs/data/three_city_r1/THREE_CITY_CAPABILITY_MATRIX.source.json).

<a id="admm-r2"></a>
![Accepted finite ADMM R2 saved-result overview](docs/assets/admm_r2/figures/admm_results_overview.png)

*Selected Sioux 200/250 OD and Boston ten-OD finite LP comparisons; Hong Kong ADMM is gated.* [Method-specific figures and gates](docs/methods/admm-space-time.md).

### Capability scope and method-specific boundaries

The entries distinguish **available code**, **executed case evidence**, and **the scale at which a method was actually accepted**. A missing result is not a claim that the method can never run on that city. A tiny generic fixture does not certify a large Boston solve.

| Capability / evidence | Boston | Sioux Falls | Hong Kong bounded case |
|---|---|---|---|
| GMNS network, zones and access | **Demonstrated:** H3 hierarchy, centroid/access and source-ID round-trip | **Benchmark network:** supplied topology and demand; not a present-day H3 city dataset | **Demonstrated, bounded:** 780 physical nodes, 1,239 links, 95 SSG/10 STPUG zones and 190 nonphysical connectors |
| Population, households and activity preparation | **Demonstrated, limited:** source-backed ACS block-group → H3 aggregate allocation; separate MassGIS attraction proxy | **Not estimated:** classic benchmark supplies vehicle OD without a demographic build | **Demonstrated, limited:** 2021 census SSG area allocation; building activity proxy separate from households |
| Trip generation / distribution | **Demonstrated, limited:** transferred household rates, activity prior, gravity/IPF and PA-to-OD | **Not estimated:** given benchmark OD | **Engineering scenario:** transferred TCS rates, local-capture sensitivity and gravity/IPF over 8,930 directed interzonal ODs |
| Mode choice | **Demonstrated, conditional:** regional-share feedback and absolute DA/S2/S3/TW research branch | **Not modeled:** fixed vehicle demand | **Engineering scenario:** GTFS/fare/walk generalized costs and sensitivity logit, not locally calibrated |
| GPS / service evidence | **Demonstrated, exploratory:** network linkage and default-off interval feedback; no independent AM validation | **Not included** in the classic benchmark | **Linked layers:** 183 GTFS stops, 294 routes and 50 detector lane observations; UrbanNav points private |
| Static Frank–Wolfe | **Demonstrated:** small controls and three expanded tiers, up to 17,522 loaded node ODs | **Demonstrated:** historical static benchmark; input-identity caveat retained | **Accepted turn-aware one-hour scenario:** 723.191 PCE modeled load |
| Finite full-path reference | **Solved:** 26-OD / 130-path control; **resource-gated** at expanded tiers | No equivalent solved full-path reference claimed by these supplied records | **Not demonstrated** for static assignment |
| Native Diagnostic L3 / compression | **Accepted numerical controls:** ranks 26/52; not solved at expanded tiers | **Executed numerical candidates:** rank 50; full-network gaps 8.17% / 4.38%, not exact UE | **Not demonstrated** |
| Space–time CG | **Accepted bounded pilot:** 90 nodes / 125 links / 10 ODs; same-graph LP match and independent 10/10 pricing closure | **Historical 200 / 250 OD:** feasible and own-LP matched; independent pricing closure not established | **Accepted R5 bounded 10-OD case:** same-graph LP match, Phase I zero in 12 rounds, independent 10/10 pricing closure |
| Lagrangian capacity pricing | **Gated transfer:** feasible recovery but 1.1002% gap missed frozen 1% gate | **Accepted R2:** 200/250 OD separately feasible; duality gaps 0.0746% / 0.3177% | **Accepted bounded transfer:** separate feasible recovery and 0.7444% certified gap |
| ADMM shared-capacity decomposition | **Accepted R2_S bounded holdout:** 10 ODs, 253 iterations, 6.68e-6 own-LP relative gap | **Accepted R2_S selected subsets:** 200/250 OD, 85/101 iterations, 6.30e-6 / 7.16e-6 own-LP gaps | **Gated R2 transfer:** first local conservation test failed; no accepted objective |
| Official `tap-b` Algorithm B static UE | **Accepted B0/B1 through task-local lossless adapter; official converter blocked before solve** | **Accepted classic benchmark; official TAPLab adapter parity and verification pass** | **Accepted static result through task-local lossless TAPLab-compatible adapter** |
| Saved checks and visualization | GMNS tracing, static original-space checks, full bounded CG figure family | Static/CG records plus accepted bounded Lagrangian/ADMM views | Source/rights register, full-stack static/four-stage figures and R5 CG traces, closure and physical-flow projection |

[Capability definitions and evidence pointers](docs/capabilities.md). The earlier [Hong Kong R1 data pilot](docs/cases/hong-kong-gmns-pilot.md) remains a historical checkpoint; the current [R2–R5 bounded technical case](docs/cases/hong-kong.md) has accepted static and CG evidence under its explicit engineering assumptions.

## 03 / Comparable statistics

These are *instance-level* descriptions, not a cross-city objective leaderboard. The stable machine-readable CSV retains schema fields; the tables here present metric rows for reading.

### A. City-data and GMNS statistics

| Metric | Boston · city-data case | Sioux Falls · benchmark | Hong Kong · bounded city case |
|---|---|---|---|
| Directed physical roads | 2852 nodes / 5091 links | 24 nodes / 76 links | 780 nodes / 1239 links |
| Fine / parent zones | 177 / 9 | Not part of this benchmark / Not part of this benchmark | 95 / 10 |
| Centroids / nonphysical access | 177 / 354 | Not part of this benchmark / Not part of this benchmark | 95 / 190 |
| Transit service layer | 3,553 referenced stops / 112 routes (dated GTFS slice) | Not part of this benchmark | 183 stops / 294 routes (pilot service layer) |
| Observation evidence | 581 GPS path-link associations; 56 planned-shape links | Not part of this benchmark | 50 detector lane snapshot records; UrbanNav point data private |
| Evidence grade | Verified bounded case; not a calibrated citywide forecast | Verified static topology; historical selected-OD finite cases are separate | Verified bounded case; activity and demand use graded assumptions |

Observation counts have different meanings and are not pooled. Sioux is a supplied-demand benchmark, not a demographic or GPS build.

[Machine-readable CSV](docs/data/three_city_r1/THREE_CITY_GMNS_STATISTICS.csv) · [Readable-table source record](docs/data/three_city_r2/GMNS_READABLE.source.json).


### B. Static-assignment statistics

| Metric | Boston B1 · conditional 2 h | Sioux Falls · classic 528 OD | Hong Kong · bounded 1 h |
|---|---|---|---|
| Physical-node / positive OD pairs | 453 | 528 | 8930 |
| Assigned demand and period | 1936.238475 PCE / 2 h | 360600 vehicles | 723.191228 PCE / 1 h |
| Mathematical problem | static BPR / Beckmann | static BPR / Beckmann | turn-aware static BPR / Beckmann |
| FW evidence | Verified bounded case | Verified historical run; input-identity caveat | Verified bounded case |
| Algorithm B route | Verified bounded case; task-local TAPLab-compatible lossless adapter | Verified; official TAPLab registered-adapter parity | Verified bounded case; task-local lossless adapter |
| Objective and independent gap | Beckmann 7922.083942188 PCE-min; independent relative gap -2.3e-16 | Beckmann 4231335.287110682 vehicle-min; independent relative gap 4.5e-09 | Beckmann 1676.012131329 PCE-min; independent relative gap 4.21e-15 |
| Path-to-link reconstruction | Verified; max path/link mismatch 5.68e-14 PCE | Verified; max path/link mismatch 5.46e-11 vehicles | Verified; max path/link mismatch 1.42e-13 PCE |

Boston B1 is a matched-method holdout, not Boston's largest accepted FW tier. Objectives and demands are not comparable across cities or with finite fixed-cost models.

[Machine-readable CSV](docs/data/three_city_r1/THREE_CITY_STATIC_ASSIGNMENT_STATISTICS.csv) · [Readable-table source record](docs/data/three_city_r2/STATIC_READABLE.source.json).


### C. Finite time-expanded statistics

| Metric | Boston · 10 OD | Sioux · 200 OD | Sioux · 250 OD | Hong Kong · 10 OD |
|---|---|---|---|---|
| Selected physical subnetwork | 90 nodes / 125 links | 24 nodes / 64 links | 24 nodes / 69 links | 100 nodes / 111 links |
| Selected OD demands | 10 | 200 | 250 | 10 |
| One model time step | 3 s | seconds not reported | seconds not reported | 30 s |
| Number of model steps | 100 | not reported in public summary | not reported in public summary | 50 |
| Elapsed model horizon | 300 s | not derivable from released summary | not derivable from released summary | 1,500 s |
| Dynamic graph | 9,110 nodes / 22,217 arcs | 1,192 nodes / 9,406 arcs | 1,292 nodes / 11,254 arcs | 11,954 nodes / 24,910 arcs |
| Same-graph reference LP objective | 64.396861511530 | 943,155.589771 | 1,521,090.83662 | 75.036329857948 |
| CG Phase-I zero round | 90 | 51 | 62 | 12 |
| Final CG column pool | 167 | 446 | 567 | 25 |
| CG independent full-DAG pricing | Independent pricing closure established; 10/10 | Not established | Not established | Independent pricing closure established; 10/10 |
| Lagrangian status / gap | Gated; 1.1002% exceeds frozen 1% gate | Accepted; 0.0746% duality gap | Accepted; 0.3177% duality gap | Verified bounded case; 0.7444% duality gap |
| ADMM status / own-LP difference | Verified bounded case; R2_S own-LP gap 6.68e−6 | Accepted R2_S; 6.30e−6 | Accepted R2_S; 7.16e−6 | Gated; first local conservation residual 0.082467622 PCE |

Fixed-cost, hard-capacity finite problems; each column is a separate graph. Objective values are vehicle-minutes, but no cross-city ranking is implied. CG pricing closure does not transfer to Lagrangian or ADMM.

[Machine-readable CSV](docs/data/three_city_r1/THREE_CITY_FINITE_TIME_EXPANDED_STATISTICS.csv) · [Readable-table source record](docs/data/three_city_r2/FINITE_READABLE.source.json).


<a id="boston"></a>
## 04 / Case study — Boston

### Role in the repository

Real-city GMNS/four-stage/GPS and scalable static assignment case, with separate bounded finite algorithms.

**What this case demonstrates.** Real-city GMNS object relationships; household/activity-based generation; modeled OD distribution; limited mode-choice branches; exploratory GPS/service linkage; new-input static computation; and FW at increasing demand coverage. It also retains a small **FW / full-path / native L3** control, an accepted **task-local-adapter Algorithm B B0/B1** static branch, and separate bounded finite space–time **CG and ADMM R2_S** pilots. **Not demonstrated here:** citywide CG/ADMM, full-city empirically calibrated demand, or independent AM accuracy.

| Boston branch | Scope and purpose | Keep it distinct from |
|---|---|---|
| **Semantic service-feedback baseline** | 36 selected zone ODs × three departures; regional baseline shares; about 202.078 / 202.071 assigned vehicle trips | An absolute-cost baseline-choice model or the expanded all-OD run |
| **Conditional ABS_PLANNED control** | 26 road-node ODs, 203.660479 vehicles, frozen 130-path comparison; FW and accepted native ranks 26/52 | Expanded L3 performance |
| **Algorithm B B0/B1 static controls** | B0 26-OD interface; B1 453 physical-node ODs, 1,936.23847491 PCE in two hours; official tap-b through task-local lossless adapter | Official TAPLab Boston adapter parity or observed/citywide demand |
| **Scalable conditional planned service** | 500 / 2,000 / all 30,790 interzonal source ODs; new absolute attributes and eligible demand | All real Boston traffic or independent behavioral validation |
| **Bounded finite space–time CG pilot** | 90 nodes / 125 links / 10 ODs; Phase I + Phase II + independent full-DAG pricing closure | Citywide Boston CG, static BPR/Beckmann assignment, or a second Boston scale |
| **Bounded finite space–time ADMM R2_S holdout** | Same bounded 90-node / 125-link / 10-OD finite graph; 253 iterations, 6.68e-6 own-LP relative objective gap and independent gates | Citywide Boston ADMM, static UE, or observed traffic |

[Complete Boston case](docs/cases/boston.md) · [Static assignment branches](docs/cases/boston-assignment.md) · [Algorithm B B0/B1](docs/cases/boston-algorithm-b.md) · [Bounded space–time CG result](docs/cases/boston-space-time.md).
[Bounded space–time ADMM R2 holdout](docs/cases/boston-admm.md).

<p align="center"><img src="docs/assets/boston/visual_release_r1/mcl_boston_hero.png" width="100%" alt="Dark navy Mobility Computation Lab cover with real Central Boston street and zone geometry on the right."></p>
<p align="center"><small>Central Boston road geometry: GMNS Plus 21_Boston (Apache-2.0), commit 116447ab641cca1ed34797d019c8e704063393c3; H3 zones and cover composition: Mobility Computation Lab. Geography only—not measured or modeled traffic.</small></p>

### Scope and statistics

2,852 physical nodes, 5,091 directed physical links; 177 H3 r9 zones and nine r7 parents. Its finite CG/ADMM holdout is a different 90-node/125-link, 10-OD instance.

| Metric | Accepted scope |
|---|---|
| City physical network | 2,852 nodes; 5,091 directed links |
| Static B1 comparison | 453 physical-node ODs; 1,936.238475 PCE / 2 h |
| Finite CG/ADMM holdout | 90 nodes; 125 links; 10 ODs |

### GMNS, zones, and source evidence

[GMNS exchange and source-ID tracing](docs/datasets/boston-gmns-exchange.md) preserve centroids, 354 nonphysical access arcs and physical link identity.

<a id="gmns-in-action"></a>
#### Boston / GMNS in Action

**One network reference for zones, demand, observations, and results.** The actual Boston exchange keeps H3 zone 35, its centroid, nonphysical access connector and physical road node distinct. A documented crosswalk maps zone identities to road access; zonal S1 demand remains modeled panel vehicle trips. A separate saved GPS path occurrence can reference a physical link and its saved S1 road result without claiming it is the same OD or observed journey.

<p align="center"><a href="docs/datasets/boston-gmns-exchange.md#one-network-multiple-connected-data-layers"><img src="docs/assets/boston/gmns_in_action_r1/gmns_connected_layers.png" width="100%" alt="Actual Boston H3 zones 35 and 71, centroid 35, dashed nonphysical access to road node 14285, an OD relation, and a separate GPS-to-link result branch."></a></p>

*Separate objects, explicit relationships. Model access connectors are not physical roads. Shared link references do not imply a shared observed trip.* [Figure records, field mappings and provenance](docs/datasets/boston-gmns-exchange.md) · [Versioned exchange and GMNS Plus profile](examples/boston/gmns_exchange_r1/README.md) · [Read-only relationship lookup](tools/gmns/trace_gmns_figure.py).

From the repository root, inspect the generic relationships with `python -B tools/gmns/boston_exchange.py trace --exchange examples/boston/gmns_exchange_r1/data`; the [exact figure segment query](docs/datasets/boston-gmns-exchange.md#reproduce-the-relationships) is separate. GMNS is the data/exchange contract, not the matching algorithm or evidence of improved prediction. The pinned GMNS Plus Level 2 reader accepted S1/S2 node/link/demand; a separate zone-schema check and the declared `mcl_solver_*` fields support the existing solver round-trip.

#### City network workflow

The common foundation is a real city network: **2,852 physical nodes, 5,091 directed links, 177 H3 r9 zones and nine r7 parents**. Zone-access mappings attach demand to roads; ordered link membership defines a corridor; transit and GPS records retain their own identities and connect to the same network. Model access lines are not automatically verified physical routes.

[GMNS-compatible input contract](docs/data-contract.md) · [City and hierarchy guide](docs/city-workflow.md) · [Boston network and data layers](docs/datasets/boston-central.md)

#### GMNS Foundation and Toolchain Alignment

The [versioned Boston exchange](examples/boston/gmns_exchange_r1/README.md) now exposes the actual [GMNS nodes](examples/boston/gmns_exchange_r1/data/node.csv), [directed links](examples/boston/gmns_exchange_r1/data/link.csv), [H3 zones and hierarchy](examples/boston/gmns_exchange_r1/data/zone.csv), and separate [S1](examples/boston/gmns_exchange_r1/data/demand_S1.csv)/[S2](examples/boston/gmns_exchange_r1/data/demand_S2.csv) zonal demand. A [reversible ID/access crosswalk](examples/boston/gmns_exchange_r1/data/id_crosswalk.csv) connects 177 distinct zones to 139 physical access nodes. The pinned GMNS Plus structural reader opened both exports; the adapter reconstructed the accepted physical solver inputs without rerunning the model. [Open/query/rebuild commands and precise scope](docs/datasets/boston-gmns-exchange.md) distinguish core GMNS fields, GMNS Plus conventions, and MCL GPS/service/result extensions. Source-hourly and solver-period capacities remain separate; nonphysical connectors have no invented routing costs. Grid2demand2/competition approval and empirical calibration are not claimed.

<p align="center"><a href="docs/datasets/boston-central.md#boston-visual-gallery"><img src="docs/assets/boston/visual_release_r1/boston_network_zones.png" width="780" alt="Shared Central Boston foundation: physical roads, H3 zones, study boundary and one ordered 23-link corridor."></a></p>

*This is the spatial foundation, not one of the four demand-model stages. Parcel outlines provide geographic context, not building footprints. [Sources, units and original map gallery](docs/datasets/boston-visual-sources.md).*

### Demand, transit, and observations

[ACS household/population allocation](docs/datasets/boston-population-households.md), MassGIS activity priors, MBTA service and exploratory GPS linkage have separate evidence grades.

#### Boston / Population and Household Preparation

The **U.S. Census Bureau's ACS 2024 five-year (2020–2024)** block-group estimates were accessed through the **Census Reporter `acs2024_5yr` mirror** for Massachusetts Suffolk `025`, Middlesex `017` and Norfolk `021`; recorded source boundaries came from its `tiger2024` GeoJSON. The fixed core intersects **174 source block groups**. Those statistical polygons do not coincide with the **177 clipped H3 r9 model zones**. In EPSG:32619, each source estimate is assigned by `area(source ∩ clipped zone) / area(full source polygon)`; the outside-core share remains a spatial remainder, **not** an observed external-trip matrix. The allocation assumes uniform persons/households within each source polygon.

| Prepared quantity | Saved core value | Role and source |
|---|---:|---|
| Population, ACS [`B01003`](https://api.census.gov/data/2024/acs/acs5/groups/B01003.html) | **171,049.520 persons** | Retained H3 demographic attribute, not the household-rate multiplier; acquired via [Census Reporter `acs2024_5yr`](https://github.com/censusreporter/census-api/blob/master/API.md) |
| Households, ACS [`B11001`](https://api.census.gov/data/2024/acs/acs5/groups/B11001.html) | **79,537.493 households** | `P_i,p = H_i × r_p` with six transferred [CTPS TDM23.2.0 Table 74 rates](https://ctps.org/pub/tdm23_sc/tdm23.2.0/TDM23.2.0_Structures%20and%20Performance.pdf#page=148) |
| Activity attraction | Separate [MassGIS Property Tax Parcels](https://www.mass.gov/info-details/massgis-data-property-tax-parcels) nonresidential/mixed building-area weights | Proxy attraction margins, **not measured employment** or ACS allocation weights |

<p align="center"><a href="docs/datasets/boston-population-households.md"><img src="docs/assets/boston/population_r1/population_allocation.png" width="100%" alt="Actual saved Suffolk block-group and clipped H3 geometry; the selected area share allocates population and households separately before household-based generation."></a></p>

The [ACS source statistics](examples/boston/population_r1/data/acs_block_group_stats.csv), [source-to-H3 contributions](examples/boston/population_r1/data/acs_block_group_h3_crosswalk.csv), [H3 attributes](examples/boston/population_r1/data/population_or_household_by_zone.csv), [outside-core ledger](examples/boston/behavior_feedback_r1_semantic_fix_r1/data/external_flow_ledger.csv) and [generation rows](examples/boston/behavior_feedback_r1_semantic_fix_r1/data/trip_generation_by_purpose.csv) are directly openable. [Source versions, provider/download links, exact fields, assumptions and no-solver reproduction command →](docs/datasets/boston-population-households.md). Source margins of error were retained; the H3 estimates do not have a validated propagated MOE. All 177 saved zones have source coverage; in general, missing is not zero.

#### Boston / The retained semantic four-stage chain

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
#### Boston / How GPS changes the result

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

### Static assignment

[FW scale tiers](docs/BOSTON_SCALE_RESULTS.md), the [controlled FW/full-path/L3 comparison](docs/cases/boston-assignment.md), and [task-local Algorithm B B0/B1](docs/cases/boston-algorithm-b.md) solve declared static instances.

#### Accepted Boston FW scale ladder — source OD ≠ physical-node OD

| Selected source-zone OD | Loaded physical-node OD after choice | Modeled road PCE | FW Beckmann objective (PCE-min) | Execution status |
|---:|---:|---:|---:|---|
| 500 | 453 | 1,936.238 | 7,922.083942 | Accepted; same B1 static comparison instance |
| 2,000 | 1,684 | 5,815.569 | 24,238.470872 | Accepted FW; full-path/L3 resource-gated |
| All 30,790 interzonal source OD | 17,522 | 16,259.122 | 73,552.277556 | Accepted FW; full-path/L3 resource-gated |

The numbers count different objects: selected H3 source-zone OD before choice, then eligible physical-node vehicle OD after choice. The 30,790 label is **not** 30,790 loaded physical-node OD or citywide observed traffic. [Exact selection, units, checks and resource gates](docs/BOSTON_SCALE_RESULTS.md).

#### Boston / Scalable assignment is now the primary road-flow result

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
#### Boston / Small controlled assignment-method comparison

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

<a id="algorithm-b"></a>
#### Boston B1 · official tap-b executable via task-local lossless adapter

![Boston B1 Algorithm B convergence](docs/assets/algorithm_b_r21/source_panels/boston_b1_convergence.svg)

![Boston B1 physical-link flow against same-problem FW](docs/assets/algorithm_b_r21/presentation/boston_b1_fw_flow_compact.svg)

![Boston B1 selected-origin reconstructed flow](docs/assets/algorithm_b_r21/source_panels/boston_b1_origin_flow.svg)

![Boston B1 independent static verification](docs/assets/algorithm_b_r21/source_panels/boston_b1_verification.svg)

The stock TAPLab Boston converter was blocked before solving; this is **task-local TAPLab-compatible lossless adapter** evidence, not official registered-adapter parity. [Exact result and limitations](docs/cases/boston-algorithm-b.md).

### Finite time-expanded algorithms

[Accepted bounded CG](docs/cases/boston-space-time.md) reaches its same-graph LP objective; [ADMM R2_S](docs/cases/boston-admm.md) passes its separate 10-OD holdout. Lagrangian remains gated at the frozen gap criterion. [Full representation-level figures and ordered evidence](docs/cases/boston-space-time.md).

<p align="center"><a href="docs/cases/boston-space-time.md"><img src="docs/assets/three_city_r2/boston_finite_space_time_case_sequence.png" width="100%" alt="Boston bounded finite CG sequence: saved graph arcs, generated column, Phase I, shared-capacity change, Phase II and final projection."></a></p>

[Historical R1 six-panel layout](docs/assets/three_city_r1/boston_finite_space_time_case_sequence.png) remains available; the R2 image above is the current view.

![Boston saved physical-to-finite graph construction](docs/assets/three_city_r2/boston_physical_to_time_expanded_graph.png)

*Saved-record R2 view.* [SVG](docs/assets/three_city_r2/boston_physical_to_time_expanded_graph.svg) · [Source](docs/assets/three_city_r2/boston_physical_to_time_expanded_graph.source.json).

![Boston accepted B07 generated column with ordered dynamic arcs](docs/assets/three_city_r2/boston_generated_column_time_indexed_path.png)

*One positive-flow time-indexed path; the terminal t19→H100 connector is bookkeeping, not physical waiting.* [SVG](docs/assets/three_city_r2/boston_generated_column_time_indexed_path.svg) · [Source](docs/assets/three_city_r2/boston_generated_column_time_indexed_path.source.json).

![Boston movement-only physical-link projection](docs/assets/three_city_r2/boston_time_expanded_to_physical_link_flow.png)

*Saved-record R2 view.* [SVG](docs/assets/three_city_r2/boston_time_expanded_to_physical_link_flow.svg) · [Source](docs/assets/three_city_r2/boston_time_expanded_to_physical_link_flow.source.json).

#### Boston / Bounded finite space–time CG pilot

This is **one** accepted 90-physical-node, 125-directed-link, 10-OD finite time-expanded instance (3-second steps; 100-step horizon), not the 5,091-link static Boston assignment or a second Boston scale. The fixed-cost hard-capacity objective is distinct from FW/Beckmann.

The six accepted evidence stages are displayed below. Final physical-link flow and independent pricing closure share one row; the preceding stages remain full width. The former [six-panel PNG](docs/assets/presentation_r5/boston_cg_case_sequence.png), [editable SVG](docs/assets/presentation_r5/boston_cg_case_sequence.svg), and [source hashes/display crops](docs/assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json) remain available; no scientific model was rerun.

<a id="boston--from-the-physical-network-to-time-indexed-columns"></a>
#### Boston / A generated column as a time-indexed path

![Recorded Boston B07 physical path and time-indexed column](docs/assets/boston/space_time_cg_r4/boston_space_time_construction.png)

*The recorded B07 column maps physical movements into actual node-time arcs; this is a local view of the bounded finite graph.*

#### Phase I restores feasibility

![Boston Phase-I total artificial-flow clearance](docs/assets/boston/space_time_cg_r4/boston_phase_i_artificial_flow.png)

*Artificial flow reaches zero in round 90.*

#### A new path can help a different OD

![Boston B07 B09 B10 shared-capacity reallocation](docs/assets/boston/space_time_cg_r4/boston_shared_capacity_event.png)

*The saved B07/B09/B10 event demonstrates reallocation after restricted-master reoptimization.*

#### Phase II improves the real-path objective

![Boston Phase-II objective against the same-graph arc-flow LP reference](docs/assets/boston/space_time_cg_r4/boston_phase_ii_objective.png)

*The real-path objective reaches the reference level on this finite graph.*

<a id="final-physical-link-movement-flow-and-validation"></a>
<a id="independent-pricing-closure"></a>
#### Final physical-link movement flow and independent pricing closure

<table class="figure-grid"><tr><td width="50%"><strong>Final physical-link movement flow and validation</strong><img src="docs/assets/boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png" width="100%" alt="Boston CG final time-aggregated physical-link movement flow"><small>52 of 125 directed physical links carry positive modeled movement flow; not observed traffic.</small></td><td width="50%"><strong>Independent pricing closure</strong><img src="docs/assets/boston/space_time_cg_r4/boston_pricing_closure_by_demand.png" width="100%" alt="Boston independent pricing closure by demand"><small>Full-DAG pricing closure passes all 10 demands at <code>1e-6</code>.</small></td></tr></table>

[Full uncropped figures, numeric checks and limitations](docs/cases/boston-space-time.md) · [Matching Sioux Falls case below](#sioux-falls) · [Earlier four-panel summary](docs/assets/boston/space_time_cg_r4/boston_cg_summary_panel.png).

| Shared CG stage | Boston result |
|---|---|
| **A generated column as a time-indexed path** | Actual B07 column on the accepted 90-node/125-link pilot |
| **Phase I restores feasibility** | Artificial flow **20.5536128974 → 0** in round **90** |
| **A new path can help a different OD** | Recorded B07/B09/B10 shared-capacity reallocation |
| **Phase II improves the real-path objective** | **64.39686151152952** after 15 rounds; reference-objective agreement on the same finite time-expanded graph |
| **Final physical-link movement flow and validation** | 52 positive-flow physical links; demand, capacity, path and back-projection checks pass |
| **Independent pricing closure** | Five continuation rounds, final column pool **152 → 167**; B01–B10 pass at `1e-6` |

The [detailed Boston CG page](docs/cases/boston-space-time.md) retains the full figure family, exact plot inputs, editable SVGs and hashed provenance. The 15 R4 certificate columns have zero final flow; they complete the dual/pricing certificate rather than create additional physical traffic. Final physical-link movement flows remain unchanged from R3 within numerical precision. The second-machine receiver check remains pending. These are saved-result visualizations only; no model was rerun for this public update.

<a id="boston-admm-readme"></a>
#### Boston / Bounded finite space–time ADMM R2_S

This is the accepted **10-OD holdout on the 90-node/125-link finite graph**, evaluated with the R2_S policy frozen before Boston. It is not the static Boston assignment, measured traffic, or a citywide ADMM run. The same four evidence stages appear in the Sioux Falls section below; each ADMM run is compared only with its **own same-graph arc-flow LP**. [Full Boston ADMM case and independent checks](docs/cases/boston-admm.md).

#### Convergence and original-unit feasibility

![Boston 10-OD ADMM R2 convergence, original-unit local balance and capacity, objective and fixed rho](docs/assets/admm_r2/figures/convergence_Boston_10OD.png)

#### Commodity conservation

![Boston 10-OD commodity-level original-unit conservation heatmap](docs/assets/admm_r2/figures/admm_boston_10od_local_conservation_heatmap.png)

#### Final physical-link movement flow

![Boston 10-OD final physical-link ADMM and same-graph LP movement flow](docs/assets/admm_r2/figures/admm_boston_10od_final_physical_link_flow.png)

#### Signed ADMM−LP physical-link difference

![Boston 10-OD signed ADMM-minus-LP physical-link movement-flow difference](docs/assets/admm_r2/figures/admm_boston_10od_minus_lp.png)

*These are accepted saved-result figures, not newly solved flows. The signed map retains its actual ±`4.24e-4`-vehicle maximum. [Editable figures, source records and the 125-link derived table](docs/cases/boston-admm.md) document the bounded scope and GMNS Plus attribution.*

### Independent verification

CG independent full-DAG pricing closure passes 10/10 demands; static and finite original-space checks remain separate.

### City-specific evidence and limits

No citywide calibrated CG/ADMM or independent AM validation is claimed. All earlier maps, GMNS records, GPS evidence and figures are retained below.

### Reproduction

[Use saved result checks and case entry points](docs/cases/boston.md#experiments--reproduction).

<a id="sioux-falls"></a>
## 05 / Case study — Sioux Falls

### Role in the repository

Classical supplied-vehicle-OD road benchmark and historical selected-OD finite algorithm case, not a new demographic or GPS city-data model.

**What this case demonstrates.** A classic supplied-demand benchmark with static FW, accepted official TAPLab/`tap-b` Algorithm B parity and native L3 research, plus distinct 200/250-OD finite space–time **CG and ADMM R2_S** results. **Not modeled here:** real-city trip generation, destination/mode estimation or GPS service feedback. The benchmark does not become a modern city dataset because it shares the framework.

### Scope and statistics

24-node/76-link static topology with 528 positive OD records; distinct finite selected subgraphs have 64/69 links and 200/250 OD demands.

| Metric | Accepted scope |
|---|---|
| Static benchmark | 24 nodes; 76 links; 528 supplied OD records |
| Historical finite 200-OD case | 24 nodes; 64 selected links; 200 ODs |
| Historical finite 250-OD case | 24 nodes; 69 selected links; 250 ODs |

### GMNS, zones, and source evidence

[Frozen static topology and source identity](examples/sioux-falls/native_l3_r1/README.md) remain separate from the selected finite subgraphs.

### Demand, transit, and observations

Population, household, transit and GPS preparation are **Not part of this benchmark**; vehicle OD is supplied.

No population, household, activity, transit or GPS preparation was executed for this supplied-demand benchmark.

### Static assignment

Historical FW, numerical native L3 candidates and [official TAPLab registered-adapter Algorithm B parity](docs/cases/sioux-algorithm-b.md) are distinct static results.

<a id="sioux-falls-benchmark-series"></a>
#### Sioux Falls / Static methods and retained numerical candidates

The [Sioux Falls case](docs/cases/sioux-falls.md) also has actual static assignment work. Its historical [FW result](docs/datasets/sioux-static-fw.md) has Beckmann F **4,236,715.140437842**, but the retained runtime OD identity is insufficient to declare it a same-input reference for the native profile. The corrected [native Diagnostic L3 implementation](algorithms/path_compression/diagnostic_l3/README.md) has accepted **outer-04** points on the frozen 76-link, 528-positive-OD, 2,218-path static instance (rank 50; 585 reduced path coordinates; 661 total native variables):

| Sioux native configuration | Original Beckmann component F | Max OD residual | Full-network relative cost gap |
|---|---:|---:|---:|
| [A_REG001 · gamma=0.01](examples/sioux-falls/native_l3_r1/runs/SiouxFalls/A_REG001/outer_04_check.json) | 4,325,864.946597109 | 5.548833712509804e-7 | **8.167461%** |
| [B_BECKMANN · gamma=0](examples/sioux-falls/native_l3_r1/runs/SiouxFalls/B_BECKMANN/outer_04_check.json) | 4,289,674.484214505 | 6.957361051718181e-7 | **4.381867%** |

Both pass recorded numerical feasibility, but neither has a full-network UE certificate or new empirical validation. A is regularized and B is not. Sioux demand is exogenous; no real-city GPS/GTFS or Boston-style four-stage estimation was added.

The separate [official TAPLab-adapter Algorithm B classic result](docs/cases/sioux-algorithm-b.md) has Beckmann **4,231,335.287110682 vehicle-min**, independent relative gap **4.4984e-9**, exact physical-link-flow parity through the registered CLI/direct callable, and a certified `taplab verify` output. It is the static 528-OD case, not either selected-OD space–time CG experiment.

#### Sioux Falls · official TAPLab registered-adapter parity for tap-b Algorithm B

![Sioux Falls Algorithm B convergence](docs/assets/algorithm_b_r21/source_panels/sioux_convergence.svg)

![Sioux Falls physical-link flow against same-problem FW](docs/assets/algorithm_b_r21/presentation/sioux_fw_flow_compact.svg)

![Sioux Falls selected-origin reconstructed flow](docs/assets/algorithm_b_r21/source_panels/sioux_origin_flow.svg)

![Sioux Falls independent static verification](docs/assets/algorithm_b_r21/source_panels/sioux_verification.svg)

Saved Beckmann objective 4,231,335.287110682 vehicle-min; independent relative gap 4.4984e-9. The registered CLI and direct callable have exact accepted physical-link-flow parity. [Exact static case](docs/cases/sioux-algorithm-b.md).

### Finite time-expanded algorithms

Historical [200/250-OD CG](docs/cases/sioux-space-time.md), accepted [Lagrangian R2](docs/methods/distributed-assignment.md) and [ADMM R2_S](docs/cases/sioux-admm.md) use selected finite graphs. [Full representation-level figures and ordered evidence](docs/cases/sioux-space-time.md).

<p align="center"><a href="docs/cases/sioux-space-time.md"><img src="docs/assets/three_city_r2/sioux_finite_space_time_case_sequence.png" width="100%" alt="Sioux Falls finite CG sequence: saved graph arcs and column, 200-OD Phase-I/II traces, recorded shared-capacity change and 200/250-OD final summary."></a></p>

[Historical R1 six-panel layout](docs/assets/three_city_r1/sioux_finite_space_time_case_sequence.png) remains available; the R2 image above is the current view.

![Sioux saved physical-to-finite graph construction](docs/assets/three_city_r2/sioux_physical_to_time_expanded_graph.png)

*Saved-record R2 view.* [SVG](docs/assets/three_city_r2/sioux_physical_to_time_expanded_graph.svg) · [Source](docs/assets/three_city_r2/sioux_physical_to_time_expanded_graph.source.json).

![Sioux Falls accepted XS170 generated column with ordered dynamic arcs](docs/assets/three_city_r2/sioux_generated_column_time_indexed_path.png)

*One saved selected-OD path; the model-step duration in seconds is not published.* [SVG](docs/assets/three_city_r2/sioux_generated_column_time_indexed_path.svg) · [Source](docs/assets/three_city_r2/sioux_generated_column_time_indexed_path.source.json).

![Sioux movement-only physical-link projection](docs/assets/three_city_r2/sioux_time_expanded_to_physical_link_flow.png)

*Saved-record R2 view.* [SVG](docs/assets/three_city_r2/sioux_time_expanded_to_physical_link_flow.svg) · [Source](docs/assets/three_city_r2/sioux_time_expanded_to_physical_link_flow.source.json).

#### Sioux Falls / Historical 200/250-OD finite space–time CG

The figures below are **historical finite time-expanded CG**, not native-L3 runs or present-day city observations. Explore the actual saved results before running an example. The 200- and 250-OD views represent **different selected-OD benchmark instances**, not a comparison of algorithms on the same demand.

The accepted construction, Phase-I, capacity, Phase-II and final-flow figures appear at their matching subsections below. The paired 200/250-OD Phase-I, Phase-II and final-flow views are side by side; other figures remain one per row. The former [six-panel PNG](docs/assets/presentation_r5/sioux_cg_case_sequence.png), [editable SVG](docs/assets/presentation_r5/sioux_cg_case_sequence.svg), and [source hashes/display crops](docs/assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json) remain available. The former last panel was a status label, not an established Sioux pricing certificate. The two OD selections are distinct benchmark instances, not repeated trials. [Full numeric checks and limitations](docs/cases/sioux-space-time.md) · [Matching Boston case above](#boston). No scientific model was rerun.

| Road benchmark | Physical nodes | Selected links | OD pairs | Final columns | Objective | Access |
|---|---:|---:|---:|---:|---:|---|
| [Sioux Falls · 200 OD](docs/datasets/sioux-200od.md) | 24 | 64 | 200 | 446 | 943,155.589771 | Historical result record |
| [Sioux Falls · 250 OD](docs/datasets/sioux-250od.md) | 24 | 69 | 250 | 567 | 1,521,090.836620 | Historical result record |
| [Sioux Falls · static FW](docs/datasets/sioux-static-fw.md) | 24 | 76 | 528 | — | 4,236,715.140438 | Approximate static baseline |

[**All six benchmark figures**](docs/visualizations.md) · [Network and example catalog](docs/datasets.md) · [Verification scope](docs/outputs.md)

Historical road records include checked results and approved figures, **not redistributed raw inputs**. Self-contained [synthetic reference inputs](docs/examples.md) are bundled separately for installation and regression testing. Static FW and space–time CG solve different model formulations; their objective values are not directly comparable.

<a id="sioux-falls--from-the-physical-network-to-time-indexed-columns"></a>
#### Sioux Falls / From the physical network to the finite time-expanded graph

**The CG examples solve a finite space–time linear flow model with fixed arc costs and explicit capacities.** They are not the same objective as static BPR/Beckmann FW or native L3. Source and sink connectors attach each demand to the time network, movement arcs advance to arrival times, and waiting arcs permit modeled delay.

![Sioux Falls recorded XS170 local physical-to-time network cutaway](docs/assets/presentation_r3/sioux_space_time_construction.png)

**This is an explanatory local cutaway—not a plot of every node and arc.** Positions are schematic; selected IDs and times come from saved records. The highlighted column is `source_XS170 → xs_link19_t0 → xs_link15_t2 → sink_XS170_5_t6`, corresponding to physical nodes `8 → 6 → 5` at times `0 → 2 → 6`. The rest of the horizon and demand-specific connectors are not drawn. [Construction fields and mappings](docs/cases/sioux-space-time.md).

#### Sioux Falls / Phase I restores feasibility

<table class="figure-grid"><tr><td width="50%"><img src="docs/assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png" width="100%" alt="Sioux Falls 200-OD saved Phase-I artificial-flow trace"><small>200 OD · artificial flow clears in round 51.</small></td><td width="50%"><img src="docs/assets/sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png" width="100%" alt="Sioux Falls 250-OD saved Phase-I artificial-flow trace"><small>250 OD · artificial flow clears in round 62.</small></td></tr></table>

| Saved observation | 200 OD | 250 OD |
|---|---:|---:|
| Initial artificial flow | 749.806844 | 4,082.887577 |
| Demands initially carrying artificial flow | 2 | 5 |
| Phase-I zero round | 51 | 62 |
| Added Phase-I / Phase-II columns | 51 / 195 | 62 / 255 |
| Final column pool | 446 | 567 |
| Objective / arc-flow LP reference on the same selected-OD finite time-expanded graph | 943,155.589771 | 1,521,090.836620 |
| Absolute objective difference | 2.33×10⁻¹⁰ | 0 |
| Maximum final demand residual / capacity violations | 0 / 0 | 0 / 0 |

The 200-OD selection is contained in the 250-OD selection. There is one recorded run per size, with different iteration/candidate caps. These are **descriptive historical runs**, not repeated runtime trials, a scaling law or a global pricing-closure certificate. The original run summaries explicitly leave `optimality_claimed` and `full_cg_global_convergence_claimed` false.

#### Sioux Falls / A new path can help a different OD

At round 34 (200 OD) and round 39 (250 OD), pricing selected a new path for **XS170**, but **XS169** lost 500 units of artificial flow after restricted-master reoptimization. XS170's 500 real units moved away from `xs_link21_t1`; XS169's real flow on that binding shared arc grew from 150.193 to 650.193. The total arc load stayed at its 5,050.193 capacity.

![Sioux Falls XS170 XS169 saved shared-capacity reallocation](docs/assets/presentation_r5/sioux_shared_capacity_canonical.png)

*This recorded coupled-master mechanism does not prove that one path was uniquely necessary.* The raw capacity dual stays approximately −1 under the saved solver convention. [Editable SVG](docs/assets/presentation_r5/sioux_shared_capacity_canonical.svg) · [OD-level supplementary figure](docs/assets/sioux/phase_i_r1/od_level_phase_i_clearance.png) · [Earlier accepted capacity diagram](docs/assets/presentation_r3/sioux_capacity_exchange.png) · [Saved plot input and hashes](docs/assets/presentation_r5/SIOUX_CAPACITY_CANONICAL_SOURCES.json) · [Saved trace CSVs](docs/assets/sioux/phase_i_r1/data/200_phase_i_trace.csv) · [Full Sioux CG explanation](docs/cases/sioux-space-time.md).


#### Sioux Falls / Phase II improves the real-path objective

<table class="figure-grid"><tr><td width="50%"><img src="docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png" width="100%" alt="Sioux Falls 200-OD saved Phase-II objective against its arc-flow LP"><small>200 OD · objective on its own selected-OD finite graph.</small></td><td width="50%"><img src="docs/assets/benchmarks/sioux_250od_phase2_objective_trace.png" width="100%" alt="Sioux Falls 250-OD saved Phase-II objective against its arc-flow LP"><small>250 OD · objective on its own selected-OD finite graph.</small></td></tr></table>

Each objective is compared with the arc-flow LP on the **same selected-OD finite time-expanded graph**. The two benchmark objective values must not be compared as if they were alternative algorithms on one demand set.

#### Sioux Falls / Final physical-link movement flow and validation

<table class="figure-grid"><tr><td width="50%"><img src="docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="100%" alt="Sioux Falls 200-OD final time-aggregated physical-link movement flow"><small>200 OD · 24 nodes, 64 selected links and 446 final columns. <a href="docs/datasets/sioux-200od.md">Open results</a>.</small></td><td width="50%"><img src="docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png" width="100%" alt="Sioux Falls 250-OD final time-aggregated physical-link movement flow"><small>250 OD · 24 nodes, 69 selected links and 567 final columns. <a href="docs/datasets/sioux-250od.md">Open results</a>.</small></td></tr></table>

The two saved views aggregate final time-indexed movement flow back to physical links. Both retained runs have zero final demand residual and zero capacity violations, and both have reference-objective agreement. Map line width represents final movement flow accumulated over the modeled time horizon. These are schematic benchmark views, not observed traffic, static V/C or a full 528-OD assignment. Opposite directions can overlap in the rendering; use the data cards for numerical interpretation.

#### Sioux Falls / Independent pricing closure

**Not established for the retained 200-OD and 250-OD runs.** Reference-objective agreement remains valid, but Boston's independent pricing-closure certificate is not transferred to Sioux Falls. [Exact status and reproduction limits](docs/cases/sioux-space-time.md#6-independent-pricing-closure).

<a id="sioux-admm-readme"></a>
#### Sioux Falls / Selected-OD finite space–time ADMM R2_S

The accepted **200-OD and 250-OD selected subsets are different finite graphs and demand sets**. The Sioux-selected R2_S policy passed independent conservation, capacity, KKT and physical-flow projection checks in 85 and 101 iterations, with own-LP relative objective gaps of 6.30e-6 and 7.16e-6. The four evidence stages below match the Boston ADMM section above; the two Sioux results are not one same-demand algorithm race. [Full Sioux ADMM case and independent checks](docs/cases/sioux-admm.md).

#### Convergence and original-unit feasibility

![Sioux Falls 200-OD ADMM R2 convergence, original-unit local balance and capacity, objective and fixed rho](docs/assets/admm_r2/figures/convergence_Sioux_200OD.png)

![Sioux Falls 250-OD ADMM R2 convergence, original-unit local balance and capacity, objective and fixed rho](docs/assets/admm_r2/figures/convergence_Sioux_250OD.png)

#### Commodity conservation

![Sioux Falls 200-OD commodity-level original-unit conservation heatmap](docs/assets/admm_r2/figures/admm_sioux_200_local_conservation_heatmap.png)

*The 250-OD accepted convergence figure above contains its original-unit local-balance and capacity traces; no separate 250-OD commodity heatmap was released.*

#### Final physical-link movement flow

![Sioux Falls 200-OD final physical-link ADMM and own-graph LP movement flow](docs/assets/admm_r2/figures/admm_sioux_200_final_physical_link_flow.png)

![Sioux Falls 250-OD final physical-link ADMM and own-graph LP movement flow](docs/assets/admm_r2/figures/admm_sioux_250_final_physical_link_flow.png)

#### Signed ADMM−LP physical-link difference

![Sioux Falls 200-OD signed ADMM-minus-LP physical-link movement-flow difference](docs/assets/admm_r2/figures/admm_sioux_200_minus_lp.png)

![Sioux Falls 250-OD signed ADMM-minus-LP physical-link movement-flow difference](docs/assets/admm_r2/figures/admm_sioux_250_minus_lp.png)

*These are accepted saved-result figures. Physical-link views use a deterministic schematic layout, not geographic coordinates or observed traffic. [Editable figures and source records](docs/cases/sioux-admm.md) retain the distinct 200/250-OD scopes.*

<a id="distributed-assignment"></a>
### Distributed assignment algorithms / bounded accepted results

The Sioux 200/250-OD **finite time-expanded shared-capacity** instances also have accepted, method-specific saved results. These are not static user equilibrium or full 528-OD network solutions. Their mathematical contract is separate from static FW; no cross-contract objective comparison is implied.

| Method | Accepted Sioux 200 OD | Accepted Sioux 250 OD | Necessary distinction |
|---|---|---|---|
| **Lagrangian R2** | Dual lower bound **942,452.403471**; separately recovered feasible primal **943,155.589771** vehicle-min; **0.0746%** certified gap | Dual **1,516,258.347432**; feasible primal **1,521,090.836620** vehicle-min; **0.3177%** gap, below frozen 1% gate | Capacity-price dual generates paths; a separate restricted-path LP recovers the primal. Both primals match their own same-graph arc-flow LP objectives. |
| **ADMM R2_S** | Objective **943,161.533307** vehicle-min; **6.30e-6** relative gap to own LP | Objective **1,521,101.731718** vehicle-min; **7.16e-6** relative gap to own LP | Frozen Sioux-selected policy also passes a separate bounded Boston 10-OD holdout; independent conservation/capacity/KKT/projection checks pass. [Full cross-city ADMM evidence](docs/methods/admm-space-time.md). |

<table><tr><td width="50%"><a href="docs/methods/distributed-assignment.md#lagrangian-capacity-pricing-with-separate-primal-recovery"><img src="docs/assets/sioux/distributed_r1/Sioux_200OD_P07.svg" width="100%" alt="Sioux 200-OD Lagrangian saved lower-bound and feasible-recovery evidence"></a></td><td width="50%"><a href="docs/methods/distributed-assignment.md#lagrangian-capacity-pricing-with-separate-primal-recovery"><img src="docs/assets/sioux/distributed_r1/Sioux_250OD_P07.svg" width="100%" alt="Sioux 250-OD Lagrangian saved lower-bound and feasible-recovery evidence"></a></td></tr></table>

*Saved Lagrangian R2 histories, in matching 200/250-OD layouts. The lower and upper bounds are different mathematical outputs; a dual lower bound alone is not a feasible assignment.*

<table><tr><td width="50%"><a href="docs/methods/distributed-assignment.md#admm-localconsensus-shared-capacity-decomposition"><img src="docs/assets/sioux/distributed_r1/sioux_200od_objective_difference.svg" width="100%" alt="200-OD ADMM result is 0.000434 percent above its own LP objective"></a></td><td width="50%"><a href="docs/methods/distributed-assignment.md#admm-localconsensus-shared-capacity-decomposition"><img src="docs/assets/sioux/distributed_r1/sioux_250od_objective_difference.svg" width="100%" alt="250-OD ADMM result is 0.000607 percent above its own LP objective"></a></td></tr></table>

*Earlier R1 paired scalar figures are retained as historical evidence; they are not the new R2_S histories. The R1 250-OD iteration history was not supplied, so none was created.* [R1 source and limits](docs/methods/distributed-assignment.md) · [R2 matched figures](docs/cases/sioux-admm.md).

The table describes accepted Sioux selected-OD results; [Hong Kong has a separate accepted bounded Lagrangian recovery and 0.7444% certificate](docs/cases/hong-kong-space-time.md). Boston's Lagrangian transfer remains gated by the frozen 1% duality-gap criterion. ADMM R2_S passes a separate bounded Boston 10-OD holdout, while Hong Kong's frozen ADMM R2 transfer remains gated. None changes previously accepted Boston FW or CG results.

### Independent verification

Both CG runs agree with their own arc-flow LP objectives; independent full-DAG pricing closure is **Not established** for either retained run.

### City-specific evidence and limits

The XS170/XS169 capacity mechanism and both scales remain visible; no full 528-OD finite assignment or current traffic validation is claimed.

### Reproduction

[Inspect saved benchmark inputs and checks](docs/cases/sioux-falls.md#experiments--reproduction).

<a id="hong-kong"></a>
## 06 / Case study — Hong Kong

### Role in the repository

Bounded turn-aware real-city engineering case with source-qualified four-stage/static and a frozen 10-OD finite case.

### Scope and statistics

780 physical nodes, 1,239 directed physical links, 95 SSG fine zones and ten STPUG parents. The finite case selects 100 physical nodes and 111 links.

| Metric | Accepted bounded instance |
|---|---|
| City network | 780 physical nodes; 1,239 directed links |
| Static scenario | 8,930 OD pairs; 723.191 PCE / 1 h |
| Finite R5 case | 100 selected nodes; 111 links; 10 ODs |

### GMNS, zones, and source evidence

[GMNS network, zone hierarchy, turn and grade checks](docs/datasets/hong-kong-gmns.md) preserve physical and nonphysical identities.

### Demand, transit, and observations

[Building/activity proxies and four-stage scenario](docs/cases/hong-kong-four-stage.md) use graded assumptions; detector and private UrbanNav evidence are not held-out validation.

### Static assignment

[Turn-aware FW and task-local Algorithm B](docs/cases/hong-kong-static-assignment.md) agree on the same static scenario; official TAPLab adapter parity is not claimed.

### Finite time-expanded algorithms

The specifically approved HK10 / `ORACLE_R1_HK10_K1` example is a **model-generated path**, verified against the frozen R5 final pool and positive-flow solution. Approval covers its 77-arc excerpt and matching figures/captions/provenance only; it does not cover the full pool, dual/state arrays or raw observations. [Exact disclosure scope and file hashes](docs/assets/three_city_r2/HK10_DISCLOSURE_APPROVAL_CURRENT.json).

[Accepted R5 CG](docs/cases/hong-kong-space-time.md) matches its same-graph arc-flow LP, with separately recovered Lagrangian feasibility. Frozen ADMM R2 remains **Gated**. [Full representation-level figures and ordered evidence](docs/cases/hong-kong-space-time.md).

<p align="center"><a href="docs/cases/hong-kong-space-time.md"><img src="docs/assets/three_city_r2/hong_kong_finite_space_time_case_sequence.png" width="100%" alt="Hong Kong bounded finite CG sequence: saved graph arcs, approved model-generated HK10 column, Phase I, no accepted shared-capacity event, Phase II and final projection."></a></p>

[Historical R1 six-panel layout](docs/assets/three_city_r1/hong_kong_finite_space_time_case_sequence.png) remains available alongside the current R2 image above.

![Hong Kong saved physical-to-finite graph construction](docs/assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.png)

*Saved-record R2 view.* [SVG](docs/assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.svg) · [Source](docs/assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.source.json).

The following approved, model-generated HK10 excerpt was verified against the frozen R5 final pool and **0.8352150831808043 PCE** positive flow. It is not an UrbanNav/GPS observation or approval for any other path data.

![Hong Kong approved model-generated HK10 column with ordered dynamic arcs](docs/assets/three_city_r2/hong_kong_generated_column_time_indexed_path.png)

*One model-generated path, not UrbanNav/GPS observation; original physical roads and turn-expanded routing states are distinct.* [SVG](docs/assets/three_city_r2/hong_kong_generated_column_time_indexed_path.svg) · [Source](docs/assets/three_city_r2/hong_kong_generated_column_time_indexed_path.source.json).

![Hong Kong movement-only physical-link projection](docs/assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.png)

*Saved-record R2 view.* [SVG](docs/assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.svg) · [Source](docs/assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.source.json).

The frozen 10-OD finite case has **11,954 dynamic nodes and 24,910 arcs**. Current CG R5 clears Phase I artificial flow **4.3502187198 → 0 in 12 rounds**, then reaches **75.03632985794835 vehicle-minutes**, agreeing with its same-graph arc-flow LP. An independent full-DAG check establishes **pricing closure for 10/10 demands at 1e-6**. Separate Lagrangian feasible-primal recovery has a **0.7444%** certified gap. Hong Kong ADMM R2 remains **gated before accepted outer iterations** and has no accepted objective. [Full finite case, individual scientific figures and redacted closure evidence](docs/cases/hong-kong-space-time.md).

<a id="hong-kong-cg-r5"></a>
#### Hong Kong / Bounded finite space–time CG R5

These are the accepted saved results for the **same unchanged 10-OD finite graph**. Phase-I total/by-demand evidence and Phase-II/independent-closure evidence form two paired rows; the construction, final flow and separate LP/Lagrangian comparison remain full width. The comparison is supporting context, not an additional CG run. The case page retains the full records, editable SVGs and reproduction limits.

<a id="from-physical-links-to-time-indexed-movement"></a>
#### Hong Kong / From the physical network to the finite time-expanded graph

![Hong Kong source-grounded local physical-link to time-indexed-arc cutaway](docs/assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.png)

*A source-grounded local cutaway: two connected Austin Road physical links become actual movement arcs joined by a zero-time turn connector; pale arcs include saved waiting and other allowed movements. Positions are schematic, and the highlighted chain is permitted by the frozen graph—not an exported CG column or observed trajectory. The full graph has 111 selected physical links, 30-second steps and a 50-step horizon.* [Editable SVG](docs/assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.svg) · [Source record and exact IDs](docs/assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.source.json) · [Earlier aggregate construction graphic](docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_physical_to_time_expanded.png).

<a id="phase-i-restores-real-path-feasibility"></a>
<a id="phase-i-clearance-by-demand"></a>
#### Phase I restores real-path feasibility and clears demand-level deficits

<table class="figure-grid"><tr><td width="50%"><strong>Phase I restores real-path feasibility</strong><img src="docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.png" width="100%" alt="Hong Kong R5 Phase-I total artificial-flow clearance"><small>4.3502187198 artificial PCE clears by round 12; modeled feasibility, not observation.</small></td><td width="50%"><strong>Phase I clearance by demand</strong><img src="docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_by_demand.png" width="100%" alt="Hong Kong R5 initial and final Phase-I artificial flow for ten demands"><small>Initial deficit in HK03, HK05 and HK07; all ten have zero final artificial flow.</small></td></tr></table>

[Total-flow SVG](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.svg) · [Total-flow source record](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.source.json) · [By-demand SVG](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_by_demand.svg) · [Saved Phase-I trace](docs/assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_i_artificial_flow_trace.csv).

<a id="phase-ii-improves-the-real-path-objective"></a>
<a id="independent-pricing-closure-and-original-space-checks"></a>
#### Phase II objective and independent pricing closure

<table class="figure-grid"><tr><td width="50%"><strong>Phase II improves the real-path objective</strong><img src="docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.png" width="100%" alt="Hong Kong R5 Phase-II objective against its same-graph arc-flow LP"><small>The real-only master falls from 75.075236 to 75.036330 vehicle-minutes after three added columns; reference LP is on the same graph.</small></td><td width="50%"><strong>Independent pricing closure and original-space checks</strong><img src="docs/assets/hong_kong/full_stack_r5/figures/hk_cg_pricing_closure.png" width="100%" alt="Hong Kong R5 independent full-DAG pricing closure for all ten demands"><small>10/10 full-DAG closure is separate from objective agreement; solver-free checks cover demand, capacity and link projection.</small></td></tr></table>

[Objective SVG](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.svg) · [Objective source record](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.source.json) · [Closure SVG](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_pricing_closure.svg) · [Redacted closure certificate](docs/assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json) · [Solver-free public verifier](docs/assets/hong_kong/full_stack_r5/verify_receiver_r5.py).

#### Final physical-link movement flow

![Hong Kong R5 final time-aggregated physical-link movement flow](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png)

*Time-indexed movement is aggregated onto the original 111 physical-link IDs; 69 carry positive modeled flow. This is not a traffic count map.* [SVG](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.svg) · [Source record](docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.source.json).

#### Same-graph reference and feasible-primal comparison

![Hong Kong accepted same-graph LP, CG and Lagrangian feasible-primal objective comparison](docs/assets/hong_kong/full_stack_r5/figures/hk_same_graph_method_comparison.png)

*The LP, current CG and separately recovered Lagrangian feasible primal agree at the reference objective. This does not establish identical link, path or time flows; ADMM has no accepted objective in this comparison.* [SVG](docs/assets/hong_kong/full_stack_r5/figures/hk_same_graph_method_comparison.svg) · [Lagrangian evaluation](docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/lagrangian_evaluation.json).

### Independent verification

CG Phase I reaches zero in 12 rounds, and independent full-DAG pricing closure passes 10/10 demands. The single newly displayed generated column is a bounded derived disclosure, not a full pool release.

### City-specific evidence and limits

Neither citywide DTA nor empirical calibration is established; original provider archives, raw point-level observations, full pool and duals stay excluded.

#### Retained R1 data checkpoint

<p align="center"><a href="docs/cases/hong-kong-gmns-pilot.md"><img src="docs/assets/hong_kong/gmns_pilot_r1/02_roads_zones.svg" width="100%" alt="Historical Hong Kong R1 bounded pilot roads and zones before assignment readiness"></a></p>

*This earlier source-backed road/zone view is not assignment flow.* Its saved `assignment_ready=false` gate describes **R1 only**, not the later accepted R2–R5 case. Centroid access remains nonphysical. Its deterministic demand seed was not observed OD, and private UrbanNav point-level derivatives were not published. [R1 case and five original views](docs/cases/hong-kong-gmns-pilot.md) · [R1 instance](examples/hong-kong/gmns_pilot_r1/README.md) · [Current evidence/rights contract](docs/methods/hong-kong-evidence-contract.md).

### Reproduction

[Run public saved-result checks](docs/methods/hong-kong-evidence-contract.md).

## 07 / Methods, reproduction, evidence, and limits

[Methods](docs/methods.md) · [Visual evidence](docs/visualizations.md) · [Run your own GMNS](docs/RUN_YOUR_OWN_GMNS.md) · [Licenses and source policies](docs/integrations.md).

<a id="cg-experiments"></a>
### Executed finite space–time CG experiments

The repository contains **three distinct executed CG case families**. Boston is one bounded real-city pilot on an accepted GMNS subnetwork; Sioux Falls contains two historical selected-OD benchmark instances; Hong Kong R5 is a separately frozen ten-demand Tsim Sha Tsui–Jordan finite case. They share a method family, not a graph, demand, objective value or universal certificate.

<p align="center"><a href="docs/methods/space-time-cg.md"><img src="docs/assets/presentation_r5/boston_sioux_cg_parallel_overview.png" width="100%" alt="Six-stage comparison of executed finite space–time CG evidence: one bounded Boston pilot and two historical Sioux Falls selected-OD runs. Both have saved Phase-I, Phase-II, final-flow and reference evidence; independent pricing closure is established only for Boston."></a></p>

| Executed evidence | Boston | Sioux Falls | Hong Kong |
|---|---|---|---|
| **Instance** | 90 physical nodes, 125 links, 10 ODs, 3-second steps, 100-step horizon | Historical 200/250-OD selected subsets | 111 selected physical links, 10 ODs, 30-second steps, 50-step horizon; 24,910 dynamic arcs |
| **Phase I** | Artificial flow **20.5536128974 → 0** in round **90** | Artificial flow reaches zero in rounds **51 / 62** | Artificial flow **4.3502187198 → 0** in **12** rounds |
| **Phase II** | **64.39686151152954** vehicle-min; own-LP agreement | **943,155.589771 / 1,521,090.836620**; each own-LP agreement | **75.03632985794835** vehicle-min; own-LP agreement after three added columns |
| **Pricing certificate** | Independent full-DAG closure **10/10** at `1e-6` | **Not established** for retained historical runs | Independent full-DAG closure **10/10** at `1e-6` |
| **Open the evidence** | [Boston case](docs/cases/boston-space-time.md) | [Sioux case](docs/cases/sioux-space-time.md) | [Hong Kong R5 case](docs/cases/hong-kong-space-time.md) |

*The Boston/Sioux image is an earlier two-city saved overview, retained without being relabeled as a three-city figure. Hong Kong's separate R5 figures appear [above on this homepage](#hong-kong-cg-r5) and in its case page. None is a citywide CG or a calibrated forecast. Fixed-cost hard-capacity CG objectives are not numerically comparable with static BPR/Beckmann FW.* [Boston/Sioux overview SVG](docs/assets/presentation_r5/boston_sioux_cg_parallel_overview.svg) · [Source hashes](docs/assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json) · [Earlier saved overview](docs/assets/presentation_r4/cg_experiments_overview.png).



<a id="run-your-input"></a>
### Run new inputs, or inspect saved results

**These are two different operations.** The new generic preparation/solve entry computes a fresh result from supplied inputs. The saved-result entries below inspect frozen experiments. A documentation build never silently invokes a solver.

For repeatable presentation-only builds and source-hash boundaries, see the [three-city saved-data build contract](docs/assets/three_city_r2/BUILD_AND_SOURCE_CONTRACT.md). The older one-off R1 composition helpers are not required.

#### New vehicle OD → preparation → FW → verification → map

```bash
python -B tools/mcl_assignment.py prepare --input examples/scalable_vehicle_fixture/network --demand examples/scalable_vehicle_fixture/vehicle.csv --config examples/scalable_vehicle_fixture/config.json --output "my results/instance"
python -B tools/mcl_assignment.py solve --instance "my results/instance" --method fw --output "my results/fw"
python -B tools/mcl_assignment.py verify --run "my results/fw"
python -B tools/mcl_assignment.py plot --run "my results/fw" --output "my results/figures"
```

The supported direct-vehicle profile is single-class, fixed-demand and static. It retains text IDs and parallel physical links; units, capacity basis, period and PCE factor are explicit. Unsupported turn-state or class/time inputs are rejected rather than ignored. `prepare`, FW and `verify` use the standard library; plotting and optional native methods have separate dependencies.

A second entry accepts person OD, supported absolute skims, the fixed conditional choice specification and occupancy configuration. It feeds the same vehicle-assignment interface; it is not an arbitrary calibrated choice-model library. [Full new-input contract and commands](docs/RUN_YOUR_OWN_GMNS.md) · [Boston scale profile](examples/boston/scalable_tool_r1/README.md) · [Data and dependency terms](docs/SCALABLE_TOOL_DATA_NOTICE.md).


<a id="mobility-data-support"></a>
### Mobility data support

Supporting mobility data remain distinct from runnable city models and from both the historical Hong Kong R1 data pilot and the later bounded R2–R5 technical case.

#### Open mobility evidence

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

#### Executable data tools: query evidence and prepare your own records

The authorized OMDV workflow normalizes a user-supplied feed catalog and city table, performs exact city/country **named-entity matching**, and writes standardized records, unmatched/ambiguous statuses and quality checks.

```bash
python -m pip install -r requirements-data-tools.txt
python -B tools/mcl_data.py catalog-city-match --catalog examples/data-tools/feeds_sample.csv --cities examples/data-tools/external_city_universe_sample.csv --output results/data-tools-demo
python -B tools/mcl_data.py query-city --name "Hong Kong" --country CHN --include-relations
python -B tools/mcl_data.py process-gtfs --zip path/to/feed.zip --output results/gtfs-content-report
```

`query-city` prefers the stable city ID and explicitly rejects duplicate name/country keys unless `--all-matches` is requested. `process-gtfs` reuses the authorized OMDV content parser with a streamed stop-times pass; it makes no network request and does not extract or modify the ZIP. These are evidence/content tools, not GPS-to-road matching, traffic-zone creation, OD estimation or an automatic connection to the solver.

[**Browse city evidence**](docs/open-data-explorer.md) · [**Use the data tools**](docs/data-tools.md) · [**Explore all six evidence layers**](docs/open-data.md) · [**Connect data to the city workflow**](docs/city-workflow.md)

#### Quick start

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

#### Use your own network

Declare node/link/demand fields, units and zone-access rules in `case.json`, then use the same numerical entry point:

```bash
python tools/mnl.py validate --input /path/to/network/input --config /path/to/network/case.json
python tools/mnl.py run --input /path/to/network/input --config /path/to/network/case.json --seed-mode auto --seed-k 5 --output results/network-run
python tools/mnl.py verify --run results/network-run
```

The current CG profile uses one-minute steps, positive integer travel times, a common departure time, fixed costs, continuous path flows and shared hard arc capacities. [Read the exact contract](docs/data-contract.md) before adapting a dataset; this is not a general static user-equilibrium or unrestricted city-scale DTA interface.

**Network + demand → route initialization → explicit space–time network → reference LP + Phase-I/II → final pool, flows and duals → independent checks.**

The allowed network is independent of the initial route pool. Every column in the last successfully solved pool is exported, including zero-flow columns. Reference agreement and independently established pricing closure are distinct statements.

#### Tools, methods and extensions

[GMNS](https://github.com/zephyr-data-specs/GMNS) supplies the common network vocabulary. [GMNS Plus Dataset](https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset), [OSM2GMNS](https://github.com/asu-trans-ai-lab/OSM2GMNS), [grid2demand](https://github.com/asu-trans-ai-lab/grid2demand) and [TAPLab](https://github.com/asu-trans-ai-lab/TAPLab) are upstream data/tools with their own implementations and licenses. A reference link is not evidence of a bundled executable integration.

The computational release includes **space–time CG**, **static Frank–Wolfe**, the solved **finite-path Boston reference**, corrected **native Diagnostic L3**, accepted **official `tap-b` Algorithm B** case evidence, bounded **Sioux Lagrangian R2**, and cross-city bounded **ADMM R2_S** source/evidence. [The method table](docs/methods.md) states their distinct objectives, instances and accuracy scopes; `python -B tools/mcl_results.py list` and `verify-saved --run <run-id>` inspect previously released points without solving. Generalized raw-city automation, broader GPS traces and map matching, coupled primal–dual work and native internal Policy Bush state inspection remain research extensions. [City workflow](docs/city-workflow.md) · [Algorithm B method](docs/methods/origin-based-algorithm-b.md) · [ADMM R2](docs/methods/admm-space-time.md) · [Roadmap](docs/roadmap.md)

#### Project layout

```text
app/src/gmns_dynamic/   Existing network input and space–time CG engine
app/cases/             Self-contained, labelled regression examples
algorithms/static_fw/  Separate static traffic-assignment baseline
algorithms/origin_based_algorithm_b/  Selected Algorithm B adapter, evaluator and saved evidence
algorithms/finite_path_reference/  Boston 130-path SLSQP source/config
algorithms/path_compression/diagnostic_l3/  Corrected native builder and profiles
algorithms/distributed_assignment/  Earlier bounded Lagrangian R2 and ADMM R1 source/evidence
algorithms/admm_r2/                  Frozen cross-city bounded R2_S source
algorithms/mode_choice_conditional/  Reduced absolute-attribute choice evaluator
examples/boston/assignment_methods_r1/  Saved FW/full-path/native results
examples/sioux-falls/native_l3_r1/  Selected Sioux native results
examples/hong-kong/gmns_pilot_r1/  Bounded public GMNS/data instance and offline checks
docs/assets/hong_kong/full_stack_r5/  Public R2–R4 full-stack and R5 CG saved-result bundle with solver-free checks
launcher/              Saved-output verification
src/mobilitylab/        Authorized metadata tools and supporting adapters
catalog/               Network records, evidence summaries and provenance
schemas/               Explicit input and output contracts
docs/                  City workflow, visual results and project website
tools/                 User commands, documentation build and checks
```

#### Contributing, citation and licenses

Contribute a traceable city/network instance, a focused adapter, a verification improvement or a documented method. Keep observed, estimated and synthetic inputs distinct. [Contribution guide](CONTRIBUTING.md) · [Add a network](docs/add-a-network.md) · [Citation](docs/citation.md)

Original code in the public tree is distributed under [MIT](LICENSE) within the stated authorization scope. Datasets and third-party tools retain their own terms. See [data licenses](DATA_LICENSES.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [data access](docs/data-access.md).
