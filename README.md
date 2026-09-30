# Mobility Computation Lab

**City networks, travel demand and reproducible network computation.** Project author: [Hao Zheng](CITATION.cff). This open-source research environment connects explicit city representations to documented demand and network calculations while keeping each result tied to its own instance, units and evidence. [Full technical walkthrough](docs/full-walkthrough.md) · [Start with a saved example](docs/getting-started.md) · [Source and citation](docs/citation.md).

<a id="what-this-project-adds"></a>
## 01 / What this project adds

### City-to-model representations

The project links roads, hierarchical zones, population and activity inputs, transit services, and supported observations to explicit demand and network models. Its adapters preserve identifiers, units, access semantics, and physical-link mappings across the documented city cases. [Implementation and source map](docs/contributions.md#city-to-model-representations).

### Computational implementations and diagnostics

The repository brings together path-based and compressed static-assignment experiments with finite time-expanded CG, Lagrangian, and ADMM implementations. Project-specific work includes feasibility restoration, pricing and degeneracy handling, local-subproblem scaling, and reconstruction in the original flow space. [Methods and evidence](docs/contributions.md#computational-implementations-and-diagnostics).

### Reusable cross-city computational tools

The project packages shared data interfaces, case configurations, and analysis tools into an open-source environment for Boston, Sioux Falls, and Hong Kong. Documented examples connect zonal demand, generated paths, and physical-link results, allowing researchers to reuse the supported workflows and compare demand scales, network representations, and solution methods. [Tools, attribution and demonstrated scope](docs/contributions.md#reusable-cross-city-computational-tools).

<a id="framework"></a>
## 02 / Complete project structure

![Complete project structure: public inputs, GMNS representation, population and four-stage demand, observation association, separate static and finite time-expanded computation, outputs, three city instances, and software/documentation entries](docs/assets/project_structure_r2/project_structure.svg)

*A conceptual map of supported modules and case-specific connections, not a single command that runs every lane.* [Full-size editable SVG](docs/assets/project_structure_r2/project_structure.svg) · [PNG](docs/assets/project_structure_r2/project_structure.png) · [Accessible module and source table](docs/architecture.md).

<a id="gmns-in-action"></a><a id="four-step-workflow"></a>
GMNS keeps directed physical roads, hierarchical zones, centroids, nonphysical access and source IDs distinct. Population, household and activity preparation precedes **01 trip generation → 02 trip distribution → 03 mode choice → 04 traffic assignment** where those stages are supported; declared vehicle OD can instead enter assignment directly. GPS traces and map matching, service records and detector context require explicit quality and network-association rules, not an automatic observed-OD or calibrated-demand pipeline. [GMNS exchange](docs/datasets/boston-gmns-exchange.md) · [Four-stage city workflow](docs/city-workflow.md) · [Observation example](docs/datasets/boston-behavior-feedback.md).

Static **BPR/Beckmann** assignment and finite **fixed-cost, hard-capacity time-expanded** optimization are separate mathematical branches. The latter is not an automatically calibrated dynamic version of the former. [Architecture](docs/architecture.md) · [Data contract](docs/data-contract.md).

<a id="coverage"></a>
## 03 / Case coverage and selected evidence

Cells describe the **saved instance and route actually documented**, not citywide validation or universal method availability. [Complete city/GMNS, static and finite-instance statistics](docs/capabilities.md#comparable-statistics) retain separate cohorts, units and objectives.

| Model or evidence | Boston | Sioux Falls | Hong Kong |
|---|---|---|---|
| GMNS, demand and observations | [City network, ACS/H3, four-stage and exploratory GPS/service linkage](docs/cases/boston.md) | [Supplied network and vehicle OD; no demographic city compiler](docs/cases/sioux-falls.md) | [Turn-aware GMNS and bounded four-stage engineering scenario](docs/cases/hong-kong.md) |
| Static Frank–Wolfe | [Expanded tiers, up to 17,522 loaded node ODs](docs/cases/boston-assignment.md) | [Classic benchmark, with retained input-identity scope](docs/datasets/sioux-static-fw.md) | [One-hour, 723.191 PCE modeled scenario](docs/cases/hong-kong-static-assignment.md) |
| `tap-b` Algorithm B | [B0/B1 via task-local lossless TAPLab-compatible adapter](docs/cases/boston-algorithm-b.md) | [Official TAPLab registered-adapter parity](docs/cases/sioux-algorithm-b.md) | [Task-local lossless adapter](docs/cases/hong-kong-static-assignment.md) |
| Finite-path / native Diagnostic L3 | [Solved 26-OD/130-path control; rank-26/52 controls](docs/cases/boston-assignment.md) | [Rank-50 numerical candidates](docs/cases/sioux-falls.md) | Not demonstrated in this static study |
| Finite arc-flow LP and two-phase CG | [Bounded 10-OD LP agreement; independent pricing closure 10/10](docs/cases/boston-space-time.md) | [Historical 200/250-OD own-LP agreement](docs/cases/sioux-space-time.md) | [R5 bounded 10-OD LP agreement; closure 10/10](docs/cases/hong-kong-space-time.md) |
| Lagrangian capacity pricing | [Bounded transfer record](docs/methods/distributed-assignment.md) | [Accepted selected-OD R2](docs/methods/distributed-assignment.md) | [Accepted bounded transfer](docs/cases/hong-kong-space-time.md) |
| Finite space–time ADMM R2 | [Accepted 10-OD R2_S](docs/cases/boston-admm.md) | [Accepted 200/250-OD R2_S](docs/cases/sioux-admm.md) | [Frozen transfer diagnostic; no accepted objective](docs/cases/hong-kong-space-time.md) |

<a id="cg-experiments"></a><a id="admm-r2"></a><a id="algorithm-b"></a><a id="distributed-assignment"></a>
The [executed cross-case CG comparison](docs/methods/space-time-cg.md#cg-experiments), [ADMM method and figure families](docs/methods/admm-space-time.md), [Algorithm B method](docs/methods/origin-based-algorithm-b.md) and [adapter distinction](docs/integrations/taplab-tapb.md), and [Lagrangian results](docs/methods/distributed-assignment.md) are one click away. Boston and Hong Kong CG establish independent pricing closure on **different** ten-demand graphs; that certificate is not imputed to the retained Sioux runs.

## 04 / Explore the three cases

The previews below are navigation to full-size, source-qualified evidence, not interchangeable plots or a claim that all three cities have the same input layers.

| Boston | Sioux Falls | Hong Kong |
|---|---|---|
| <a href="docs/cases/boston.md"><img src="docs/assets/boston/visual_release_r1/boston_network_zones.png" width="100%" alt="Central Boston directed road network, H3 zone hierarchy and bounded corridor"></a> | <a href="docs/cases/sioux-falls.md"><img src="docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="100%" alt="Sioux Falls selected 200-OD final physical-link movement flow on the classic benchmark network"></a> | <a href="docs/cases/hong-kong.md"><img src="docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png" width="100%" alt="Hong Kong finite time-expanded construction using the approved model-generated HK10 path excerpt"></a> |
| Real-city GMNS and observation/demand workflow; scalable static assignment and bounded numerical studies. [Case](docs/cases/boston.md) · [CG](docs/cases/boston-space-time.md) · [ADMM](docs/cases/boston-admm.md) | Controlled static 528-OD benchmark and distinct historical 200/250-OD finite instances. [Case](docs/cases/sioux-falls.md) · [CG](docs/cases/sioux-space-time.md) · [ADMM](docs/cases/sioux-admm.md) | Turn-aware real-city engineering scenario and bounded static/finite studies. The pictured HK10 path is **model-generated**, not an observed trajectory. [Case](docs/cases/hong-kong.md) · [R5 CG](docs/cases/hong-kong-space-time.md) · [Four stages](docs/cases/hong-kong-four-stage.md) |

<a id="boston"></a><a id="sioux-falls"></a><a id="hong-kong"></a><a id="hong-kong-cg-r5"></a>
[Boston network preview at full size](docs/assets/boston/visual_release_r1/boston_network_zones.png) · [Sioux Falls flow preview](docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png) · [Hong Kong approved HK10 layered preview](docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.svg) · [All scientific figure families](docs/visualizations.md).

<a id="run-your-input"></a>
## 05 / Run and inspect

**Inspect saved evidence:** [result queries and source records](docs/visualizations.md). **Run a documented example:** in a compatible Python environment at the repository root, use:

```bash
python -B examples/boston/run_saved_example.py --data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1" --output "results/boston_saved_example"
```

This rebuilds a local SQLite query database from released CSV tables and exports five saved-result queries; it does **not** run demand estimation, FW, CG or matching. Use a new output directory. [Installation and dependencies](docs/getting-started.md) · [Saved-result guide](examples/boston/SAVED_EXAMPLE.md).

**Use your own inputs:** [vehicle-OD preparation and static FW](docs/RUN_YOUR_OWN_GMNS.md), or the separately documented [generic space–time network command](docs/getting-started.md#run-from-raw-input). **Version scope:** `tools/mnl.py` retains the 0.3.0-rc5 generic engine; later Boston and Hong Kong CG cases use separately versioned implementations and saved-result checks, so that command does not reproduce those case runs unchanged.

<a id="mobility-data-support"></a>
## 06 / Attribution, scope and further reading

GMNS, `tap-b`/TAPLab and source datasets retain their upstream attribution; this project documents its own adapters, computations and bounded results separately. [Contribution/source attribution](docs/contributions.md) · [Third-party notices](THIRD_PARTY_NOTICES.md) · [Data licenses](DATA_LICENSES.md) · [Citation](docs/citation.md). Results distinguish source-derived city inputs, engineering scenarios, supplied benchmarks and observed evidence; no shown case is a calibrated citywide forecast.

The [open-data explorer](docs/open-data-explorer.md) and data tools, including `mcl_data.py catalog-city-match` for named-entity matching of user-supplied catalogs, support source inspection rather than automatic OD creation. **These evidence layers are not additive.** [Data-tools instructions](docs/data-tools.md) · [Source and access scope](docs/open-data.md). Future directions such as Policy Bush remain outside the current demonstrated modules.

[Full technical walkthrough — every retained experiment, table and figure in reading order](docs/full-walkthrough.md) · [Architecture and project-map sources](docs/architecture.md) · [Complete case/method coverage](docs/capabilities.md) · [Roadmap](docs/roadmap.md).
