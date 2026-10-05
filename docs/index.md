<!-- Interactive homepage: index.html. Repository overview mirrored from README.md. -->
# Mobility Computation Lab

**Mobility Computation Lab connects city networks, travel demand, and reproducible network computation.**

This open-source research and learning project is developed by [Hao Zheng](https://scholarhaozheng.github.io/), a recent M.S. graduate from Tsinghua University, under the guidance of **[Professor Xuesong Zhou](https://search.asu.edu/profile/2182101)**. It brings together documented examples in Boston, Sioux Falls, and Hong Kong to study how city data, demand models, and network algorithms work together.

The repository uses the [General Modeling Network Specification (GMNS)](https://github.com/zephyr-data-specs/GMNS) as its portable network and data contract. Selected static traffic-assignment experiments build on [TAPLab: An Open Laboratory for Reproducible Traffic Assignment Experiments](https://github.com/asu-trans-ai-lab/TAPLab) and the official [tap-b Algorithm B](https://github.com/spartalab/tap-b), with upstream software, methods, and datasets attributed explicitly.

Project-specific work includes assembling and adapting the Boston, Sioux Falls, and Hong Kong cases; connecting city data and four-stage demand models to documented network computations; implementing and evaluating project-specific adapters, workflows, and experiments; and making each result traceable to its actual instance, units, assumptions, and evidence.

**Learning companion.** This site includes the [Traffic Assignment Lab](traffic-assignment-lab.html), an interactive demo of assignment, decomposition, spatial hierarchy, and coordinated computation on one teaching network. The demo was developed collaboratively by **[Professor Xuesong Zhou](https://search.asu.edu/profile/2182101)** and Hao Zheng, with Hao Zheng working under Professor Zhou's guidance and maintaining the web version.

[My contributions and upstream foundations](volumes/01-overview.md#src-docs-contributions-document) · [Full technical walkthrough](volumes/01-overview.md) · [Start with a saved example](volumes/01-overview.md#src-docs-getting-started-document) · [Source and citation](volumes/01-overview.md#src-docs-citation-document)

**Read the project:** [Website](https://scholarhaozheng.github.io/mobility-network-lab/) · [Complete overview](volumes/01-overview.md) · [Boston](volumes/02-boston.md) · [Sioux Falls](volumes/03-sioux-falls.md) · [Hong Kong](volumes/04-hong-kong.md)

**Run the computations:** [Code, data and environment guide](../REPRODUCTION_QUICKSTART.md) · [Experiment registry](../experiments/README.md) · [Online reproduction portal](https://scholarhaozheng.github.io/mobility-network-lab/reproduce.html)

<a id="what-this-project-adds"></a>
## 01 / What this project adds

### City-to-model representations

The project links roads, hierarchical zones, population and activity inputs, transit services, and supported observations to explicit demand and network models. Its adapters preserve identifiers, units, access semantics, and physical-link mappings across the documented city cases. [Implementation and source map](volumes/01-overview.md#src-docs-contributions-document-city-to-model-representations).

### Computational implementations and diagnostics

The repository brings together path-based and compressed static-assignment experiments with finite time-expanded CG, Lagrangian, and ADMM implementations. Project-specific work includes feasibility restoration, pricing and degeneracy handling, local-subproblem scaling, and reconstruction in the original flow space. [Methods and evidence](volumes/01-overview.md#src-docs-contributions-document-computational-implementations-and-diagnostics).

### Reusable cross-city computational tools

The project packages shared data interfaces, case configurations, and analysis tools into an open-source environment for Boston, Sioux Falls, and Hong Kong. Documented examples connect zonal demand, generated paths, and physical-link results, allowing researchers to reuse the supported workflows and compare demand scales, network representations, and solution methods. [Tools, attribution and demonstrated scope](volumes/01-overview.md#src-docs-contributions-document-reusable-cross-city-computational-tools).

<a id="framework"></a>
## 02 / Complete project structure

[![Project module map: source evidence; GMNS, demand and observation preparation; independent static and finite computation contracts; outputs; city cases; code and documentation](assets/atlas/project-map.svg)](https://scholarhaozheng.github.io/mobility-network-lab/assets/atlas/project-map.svg)

Open the [clickable SVG](https://scholarhaozheng.github.io/mobility-network-lab/assets/atlas/project-map.svg) to follow each card to its documentation. [PNG](assets/atlas/figures/g-f001.png) · [Accessible module and source table](volumes/01-overview.md#src-docs-architecture-document).

<a id="gmns-in-action"></a><a id="four-step-workflow"></a>
GMNS keeps directed physical roads, hierarchical zones, centroids, nonphysical access and source IDs distinct. Population, household and activity preparation precedes **01 trip generation → 02 trip distribution → 03 mode choice → 04 traffic assignment** where those stages are supported; declared vehicle OD can instead enter assignment directly. GPS traces and map matching, service records and detector context require explicit quality and network-association rules. [GMNS exchange](volumes/02-boston.md#src-docs-datasets-boston-gmns-exchange-document) · [Four-stage city workflow](volumes/01-overview.md#src-docs-city-workflow-document) · [Observation example](volumes/02-boston.md#src-docs-datasets-boston-behavior-feedback-document).

Static **BPR/Beckmann** assignment and finite **fixed-cost, hard-capacity time-expanded** optimization use separate mathematical models. [Architecture](volumes/01-overview.md#src-docs-architecture-document) · [Data contract](volumes/01-overview.md#src-docs-data-contract-document).

<a id="two-axes"></a><a id="02a-two-axes-of-mobility-computation-lab"></a>
### Two axes of Mobility Computation Lab

**Horizontal axis — documented city cases:**  
Boston · Sioux Falls · Hong Kong

**Vertical axis — computational depth within network assignment:**

- **A · Native assignment** — Frank–Wolfe, official tap-b Algorithm B, finite-path controls, and native L3 reconstruction.
- **B · Decomposition and distributed computation** — column generation, Lagrangian decomposition, and ADMM local or coupled computations.
- **C · Spatial hierarchy and representation** — fine and parent zones, access relationships, turn/time states, and projection back to physical network objects.
- **D · Coordination and verification** — shared capacities, residuals, pricing closure, independent evaluators, and declared result contracts.

**How to read the two axes.**  
The horizontal axis compares how the documented framework is instantiated in Boston, Sioux Falls, and Hong Kong. The vertical axis organizes increasing computational depth inside the network-assignment branch. Source data, GMNS, population and activity preparation, transit and observations, and the four-stage demand workflow remain the common city-model foundation outside A–D.

<a id="coverage"></a>
## 03 / Case coverage and selected evidence

This text-only matrix records the available stages, methods and limits. The website atlas presents the figures; each city volume contains the complete evidence.

| Stage | Boston | Sioux Falls | Hong Kong |
|---|---|---|---|
| **I City data and model foundations** | | | |
| 01 Source data and preparation | GMNS Plus, ACS/GTFS and registered source preparation. [Read evidence ↗](volumes/02-boston.md#coverage-row-01) | Frozen classic 24-node/76-link source graph and supplied vehicle OD. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-01) | Official-derived bounded network and source layers. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-01) |
| 02 GMNS network, zones and access | 5,091 physical links; 177 H3 fine zones, nine parents; connectors separate. [Read evidence ↗](volumes/02-boston.md#coverage-row-02) | 24-node, 76-link supplied directed benchmark. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-02) | 780 physical nodes, 1,239 links; 95 fine zones, ten parents and turn-aware access. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-02) |
| 03 Population, households and activity | ACS 2024 five-year block groups allocated to 177 clipped H3 zones. [Read evidence ↗](volumes/02-boston.md#coverage-row-03) | Supplied OD; no demographic city compiler. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-03) | 2021 census households/population and explicitly modeled building activity proxies. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-03) |
| **II Transit and observation evidence** | | | |
| 04 Transit and pedestrian inputs | MBTA service and pedestrian access support the bounded demand/feedback example. [Read evidence ↗](volumes/02-boston.md#coverage-row-04) | No GTFS or pedestrian city-input lane. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-04) | GTFS same-trip rides, fares, headways and pedestrian access enter generalized costs. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-04) |
| 05 GPS, trajectory and detector evidence | Exploratory map matching and service feedback. [Read evidence ↗](volumes/02-boston.md#coverage-row-05) | No modern GPS or detector observations. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-05) | Detector and private trajectory association; no held-out validation claim. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-05) |
| **III Four-stage travel-demand workflow** | | | |
| 06 01 / Trip generation — productions / attractions | Purpose-level productions and attractions in the bounded Boston example. [Read evidence ↗](volumes/02-boston.md#coverage-row-06) | Vehicle OD supplied; no trip-generation run. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-06) | Transferred rate and declared capture sensitivity. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-06) |
| 07 02 / Trip distribution — zonal OD demand | Zonal OD construction for the bounded semantic scenario. [Read evidence ↗](volumes/02-boston.md#coverage-row-07) | Supplied OD is input. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-07) | Turn-aware gravity/IPF balances 8,930 reachable directed OD pairs. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-07) |
| 08 03 / Mode choice — mode-specific demand | S1/S2 service response and conditional absolute choice remain separate. [Read evidence ↗](volumes/02-boston.md#coverage-row-08) | Vehicle OD supplied; no mode-choice run. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-08) | GTFS/pedestrian generalized cost and declared sensitivity logit. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-08) |
| 09 04 / Traffic assignment — assigned network flows | Static road flow from the bounded demand scenario; methods below. [Read evidence ↗](volumes/02-boston.md#coverage-row-09) | Static network flow from supplied vehicle OD; no upstream four-stage compiler. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-09) | Modeled one-hour static PCE road flow. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-09) |
| **IV Static assignment · BPR / Beckmann** | | | |
| 10 Frank–Wolfe | Expanded Boston FW, up to 17,522 loaded node ODs; separate from 26-OD controls. [Read evidence ↗](volumes/02-boston.md#coverage-row-10) | Classic 528-OD static FW, with ID-matched link-flow comparison against Algorithm B. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-10) | Turn-aware one-hour 723.191 PCE static engineering scenario. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-10) |
| 11 Official tap-b Algorithm B | B0/B1 numerical transfer via task-local lossless TAPLab-compatible adapter. [Read evidence ↗](volumes/02-boston.md#coverage-row-11) | Official TAPLab registered-adapter parity passes on Sioux Falls. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-11) | Accepted task-local lossless adapter; official-adapter parity remains unverified. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-11) |
| 12 Finite-path reference | 26 OD, 130-path uncompressed SLSQP reference on ABS_PLANNED. [Read evidence ↗](volumes/02-boston.md#coverage-row-12) | Frozen 2,218-path B_BECKMANN native candidate; full-network UE remains uncertified. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-12) | Accepted bounded H1: 26 ODs / 126 legal paths; matches H1 FW with full-graph relative gap approximately zero. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-12) |
| 13 Native Diagnostic L3 / compression | Rank-26/52 native controls on the same 26-OD ABS_PLANNED instance. [Read evidence ↗](volumes/02-boston.md#coverage-row-13) | Rank-50 classic static benchmark candidates. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-13) | Accepted H1 ranks 26 and 52; full-graph relative gap approximately 2.31×10⁻¹¹; evaluated under low congestion. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-13) |
| **V Finite time-expanded computation** | | | |
| 14 Network construction and generated columns | 90-node/125-link/10-OD finite graph; saved time-indexed column. [Read evidence ↗](volumes/02-boston.md#coverage-row-14) | Selected 200/250-OD finite graphs; saved time-indexed columns. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-14) | 100-node / 111-link / ten-OD finite graph, with saved time-layer construction and generated-column evidence. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-14) |
| 15 Arc-flow LP reference | Own-graph LP reference for the bounded ten-OD fixed-cost instance. [Read evidence ↗](volumes/02-boston.md#coverage-row-15) | Own selected-graph LP references for historical 200/250 ODs. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-15) | Own-graph LP reference for R5 ten-OD finite case. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-15) |
| 16 Two-phase column generation | Phase I/II and independent 10/10 pricing closure. [Read evidence ↗](volumes/02-boston.md#coverage-row-16) | Separate historical 200 / 250-OD CG results; independent full-DAG pricing closure is not established. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-16) | Phase I/II, same-graph LP agreement and independent 10/10 closure. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-16) |
| 17 Lagrangian | Saved Boston R2 10-OD best-bound iteration trace; feasible primal, 1.1002% gap misses the frozen 1% gate. [Read evidence ↗](volumes/02-boston.md#coverage-row-17) | Saved P07 best-dual and recovered feasible-primal traces for separate 200-OD and 250-OD instances; final certified gaps are 0.0746% and 0.3177%. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-17) | Ten-OD feasible recovery with 0.7444% certified gap. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-17) |
| 18 ADMM | Ten-OD original-space checks; own-LP gap 6.68e-6. [Read evidence ↗](volumes/02-boston.md#coverage-row-18) | Selected 200/250-OD original-space checks on finite graphs; the static 528-OD benchmark is a separate case. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-18) | Accepted bounded ADMM R3 transfer Fresh preregistered 4-OD holdout · 165 iterations · LP-relative difference 6.83×10⁻⁶ Finite 30-s × 50-step shared-capacity case with modeled OD demand in a bounded study area; empirical traffic validation remains open. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-18) |
| **VI Reusable outputs and tools** | | | |
| 19 Reusable outputs, queries and checks | Released source tables, GMNS and saved-result queries; separate static and finite runners. A saved-result check is distinct from a fresh solve. [Read evidence ↗](volumes/02-boston.md#coverage-row-19) | Given-input benchmark exports, static implementations and selected-OD finite checks. Historical CG pricing closure remains a separate limitation. [Read evidence ↗](volumes/03-sioux-falls.md#coverage-row-19) | GMNS and demand tables, static/H1 and finite case packages; accepted four-OD ADMM R3 is separate from ten-OD R2. Source-to-result reproduction has distinct requirements. [Read evidence ↗](volumes/04-hong-kong.md#coverage-row-19) |

<a id="boston"></a><a id="sioux-falls"></a><a id="hong-kong"></a><a id="cg-experiments"></a>
## 04 / Explore the three cases

Use the [interactive atlas](https://scholarhaozheng.github.io/mobility-network-lab/#04-explore-the-three-cases) in **Full atlas**, **By city**, or **By stage** view. Every stage remains visible in By stage; its selection bar jumps to a stage. Sioux Falls has a synchronized **200 / 250 OD** switch for the finite time-expanded experiments.

| Complete reading volume | Contents | Downloadable Markdown |
|---|---|---|
| [Overview](https://scholarhaozheng.github.io/mobility-network-lab/volumes/overview.html) | Project structure, cross-city coverage and statistics, methods, data access and scope | [01 — Overview](volumes/01-overview.md) |
| [Boston](https://scholarhaozheng.github.io/mobility-network-lab/volumes/boston.html) | City inputs, demand and observations, static assignment, finite time-expanded experiments | [02 — Boston](volumes/02-boston.md) |
| [Sioux Falls](https://scholarhaozheng.github.io/mobility-network-lab/volumes/sioux-falls.html) | Supplied vehicle OD, static methods, 200 / 250 OD CG, Lagrangian and ADMM evidence | [03 — Sioux Falls](volumes/03-sioux-falls.md) |
| [Hong Kong](https://scholarhaozheng.github.io/mobility-network-lab/volumes/hong-kong.html) | Source-qualified GMNS, four-stage models, H1 static methods, bounded time-expanded experiments | [04 — Hong Kong](volumes/04-hong-kong.md) |

The figures, source tables and model limits are retained in these volumes. The [cross-city CG method](methods/space-time-cg.md#cg-experiments) retains its original compatibility entry. The Hong Kong saved 77-arc column is a model-generated, bounded-network example. The original topic pages and historical walkthrough remain available for existing links.

## 05 / Run and inspect

Start with the [computational quickstart](../REPRODUCTION_QUICKSTART.md), then choose a registered experiment in the [Experiment catalog](https://scholarhaozheng.github.io/mobility-network-lab/reproduce.html). The [Reproduction guide](https://scholarhaozheng.github.io/mobility-network-lab/reproduction.html) links code downloads, data acquisition, exact environments, configuration, commands and verification receipts.

~~~bash
python tools/mcl_reproduce.py list
~~~

The [unified runner](../tools/mcl_reproduce.py) and [experiment registry](../experiments/README.md) separate running a computation from verifying its saved result. Follow each experiment's environment and input instructions before running it; external native tools have pinned setup requirements.

Saved-output checks verify released files; prepared-input reruns cover their declared stages. Boston S1/S2 recipes rerun the assignment stage only; Sioux Falls starts from supplied vehicle OD; population synthesis and mode choice are outside that benchmark. Independent full-DAG pricing closure remains open for the historical Sioux CG result. Each portal record states the available claim, remaining inputs and applicable limits.

The original generic GMNS engine remains versioned as **0.3.0-rc5**. Later city experiments are separately versioned and must use their own registered configuration and verification standard.

## 06 / Attribution, scope and further reading

GMNS, `tap-b`/TAPLab and source datasets retain their upstream attribution; this project documents its own adapters, computations and bounded results separately. [Contribution/source attribution](volumes/01-overview.md#src-docs-contributions-document) · [Third-party notices](../THIRD_PARTY_NOTICES.md) · [Data licenses](../DATA_LICENSES.md) · [Citation](volumes/01-overview.md#src-docs-citation-document). Results distinguish source-derived city inputs, engineering scenarios, supplied benchmarks and observed evidence; no shown case is a calibrated citywide forecast.

The [open-data explorer](volumes/01-overview.md#src-docs-open-data-explorer-document) and data tools, including `mcl_data.py catalog-city-match` for named-entity matching of user-supplied catalogs, support source inspection. **These evidence layers are not additive.** [Data-tools instructions](volumes/01-overview.md#src-docs-data-tools-document) · [Source and access scope](volumes/01-overview.md#src-docs-open-data-document). Future directions such as Policy Bush remain outside the current demonstrated modules.

[Complete current overview](volumes/01-overview.md) · [Historical technical walkthrough](volumes/01-overview.md) · [Architecture and project-map sources](volumes/01-overview.md#src-docs-architecture-document) · [Complete case/method coverage](volumes/01-overview.md#reading-section-3) · [Roadmap](volumes/01-overview.md#src-docs-roadmap-document).
