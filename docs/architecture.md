# Architecture

## City modelling is the organizing workflow

Mobility Computation Lab centres on **networks, zones, demand, evidence and network computation**. Data catalogs support this workflow; they do not replace a city model. The [city workflow](city-workflow.md) distinguishes currently executable components from extensions.

![Selective project module map from public source records](assets/project_structure_r3/project_structure.svg)

*Four source groups, model preparation, two independent mathematical contracts, outputs, three case instances and reusable software/documentation entry points.* [Clickable SVG](assets/project_structure_r3/project_structure.svg) · [PNG](assets/project_structure_r3/project_structure.png) · [Module model](assets/project_structure_r3/project_structure_model.json) · [Source and renderer hashes](assets/project_structure_r3/project_structure.source.json).

The figure is a **selective module map**, not a claim that one executable runs every row. It does not make the cases downstream of the outputs. Its observation card represents QC and matching/association with physical links or service records—not an automatic `GPS → observed OD → calibrated model` route. City demand stages 01–03 and already-declared vehicle OD are distinct entries to static stage 04; bounded finite time expansion has its own selected graph, OD, time and capacity contract. Static BPR/Beckmann and finite fixed-cost hard-capacity optimization are not sequential solver steps. The [capability table](capabilities.md) gives exact city and method scope.

The [earlier R2 diagram](assets/project_structure_r2/project_structure.svg) remains available as a historical presentation, but the selective R3 map above is the current architecture view.

### Retained earlier framework illustration

![Earlier city-neutral GMNS, demand, observation and computation framework illustration](assets/presentation_r3/framework_overview.png)

This earlier conceptual illustration remains available as a distinct historical presentation; it is not a substitute for the complete, source-grounded module map above.

## Network, zone-access and demand interface

- `app/src/gmns_dynamic/external_network_input.py` reads the current explicit model profile.
- `app/cases/` contains self-contained synthetic regression inputs, not new city datasets.
- `schemas/` and [data contract](data-contract.md) document IDs, field mappings, units and model conditions.

The generic engine starts with prepared network and demand tables. Boston and Hong Kong also have separately documented, case-specific source, zone, demand and observation workflows; their results do not turn registry names into model-ready cities or make those steps automatic in the generic CLI.

## Assignment and optimization

- `app/src/gmns_dynamic/explicit_network_workflow.py` prepares the explicit space–time problem.
- `app/src/gmns_dynamic/run_full_cg_v1.py` retains the Phase-I/Phase-II column-generation engine.
- `tools/mnl.py` is the network command entry point.
- `algorithms/static_fw/` is a separate static Beckmann / Frank–Wolfe implementation.

Do not compare these models as if a shared CSV vocabulary made their objectives, capacities or time definitions identical. Official `tap-b` Algorithm B integration and bounded Lagrangian/ADMM results have their own [documented method scopes](methods.md); native internal Policy Bush state inspection remains a research extension. The retained `tools/mnl.py` entry is the generic 0.3.0-rc5 engine, not an automatic reproduction route for later separately versioned Boston and Hong Kong CG cases.

## Supporting mobility data

`src/mobilitylab/omdv/` contains selected authorized city/catalog normalization and exact name/country matching functions. `src/mobilitylab/data/catalog_city_workflow.py` and `tools/mcl_data.py` call them on user-supplied local files. This is independent of the fixed aggregate evidence catalog.

`catalog/open-data-evidence.json`, `omdv-provenance.json`, `omdv-authorized-files.json` and `interoperability-sources.json` preserve summaries, sources and reuse scope. The OMDV study does not supply city OD or GPS observations to the solver automatically.

## Results and visible verification

`launcher/` verifies saved outputs. `catalog/datasets.json` and `benchmark-results.csv` identify bundled examples and historical benchmark records. The [visual gallery](visualizations.md) indexes the retained scientific figure families and their source records; data cards preserve interpretation limits. Original-space flow reconstruction, saved-result SQLite/CSV queries and model-specific independent checks are distinct output routes, not a single universal optimality certificate.

## Maintain the working implementation

The existing numerical and data-tool source layouts remain unchanged. The GitHub README and Pages homepage are different presentations of the same project; both must preserve the city-network focus and lead to real tools and figures. `tools/build_site.py` is the Pages generator, not a replacement for root `README.md`.

## Source-grounded module index

The linked table is generated from the [R3 module model](assets/project_structure_r3/project_structure_model.json) and its referenced [source ledger](assets/project_structure_r2/project_structure_model.json). It includes every drawn module, its actual public source/data entry, the documentation route, and the scope qualifier. A source path is evidence of an implementation or data record, not proof that every city uses it.

<!-- project-structure-node-map:start -->
| Diagram module | Actual source or data entry | Documentation and demonstrated scope |
|---|---|---|
| `roads` · Roads, boundaries, zones | [`catalog/`](../catalog/), [`examples/boston/`](../examples/boston/) | [Open evidence](data-contract.md). source-dependent |
| `people` · People and activity | [`docs/datasets/boston-population-households.md`](datasets/boston-population-households.md), [`docs/datasets/hong-kong-gmns.md`](datasets/hong-kong-gmns.md) | [Open evidence](datasets/boston-population-households.md). Boston/Hong Kong, distinct sources |
| `transit` · Transit and walking | [`docs/datasets/boston-four-step-sources.md`](datasets/boston-four-step-sources.md), [`docs/cases/hong-kong-four-stage.md`](cases/hong-kong-four-stage.md) | [Open evidence](city-workflow.md). case-specific |
| `observations` · Observation records | [`docs/datasets/boston-behavior-feedback.md`](datasets/boston-behavior-feedback.md), [`docs/methods/hong-kong-evidence-contract.md`](methods/hong-kong-evidence-contract.md) | [Open evidence](datasets/boston-behavior-feedback.md). different uses and access rights |
| `gmns` · GMNS representation | [`schemas/`](../schemas/), [`app/src/gmns_dynamic/external_network_input.py`](../app/src/gmns_dynamic/external_network_input.py), [`docs/datasets/boston-gmns-exchange.md`](datasets/boston-gmns-exchange.md) | [Open evidence](data-contract.md). portable contract plus documented extensions |
| `city_demand` · Demand stages 01–03 | [`docs/datasets/boston-population-households.md`](datasets/boston-population-households.md), [`docs/cases/hong-kong-four-stage.md`](cases/hong-kong-four-stage.md) | [Open evidence](city-workflow.md). bounded Boston/Hong Kong; not Sioux |
| `declared_od` · Already-declared OD | [`examples/scalable_vehicle_fixture/`](../examples/scalable_vehicle_fixture/), [`docs/RUN_YOUR_OWN_GMNS.md`](RUN_YOUR_OWN_GMNS.md) | [Open evidence](cases/sioux-falls.md). finite cases have separate selected OD/time |
| `association` · Observation association | [`docs/datasets/boston-behavior-feedback.md`](datasets/boston-behavior-feedback.md), [`docs/datasets/boston-gmns-exchange.md`](datasets/boston-gmns-exchange.md), [`docs/methods/hong-kong-evidence-contract.md`](methods/hong-kong-evidence-contract.md) | [Open evidence](city-workflow.md). case-specific evidence role |
| `static` · 04 / Static road assignment | [`algorithms/static_fw/`](../algorithms/static_fw/), [`algorithms/origin_based_algorithm_b/`](../algorithms/origin_based_algorithm_b/), [`algorithms/finite_path_reference/`](../algorithms/finite_path_reference/), [`algorithms/path_compression/diagnostic_l3/`](../algorithms/path_compression/diagnostic_l3/) | [Open evidence](methods.md). mode-specific or supplied OD; case/method acceptance varies |
| `finite` · Finite time-expanded optimization | [`app/src/gmns_dynamic/run_full_cg_v1.py`](../app/src/gmns_dynamic/run_full_cg_v1.py), [`algorithms/distributed_assignment/lagrangian_r2/`](../algorithms/distributed_assignment/lagrangian_r2/), [`algorithms/admm_r2/`](../algorithms/admm_r2/), [`docs/assets/hong_kong/full_stack_r5/`](assets/hong_kong/full_stack_r5/) | [Open evidence](methods/space-time-cg.md). not a downstream Frank–Wolfe step |
| `outputs` · Saved outputs and independent checks | [`launcher/`](../launcher/), [`tools/mcl_results.py`](../tools/mcl_results.py), [`examples/boston/run_saved_example.py`](../examples/boston/run_saved_example.py), [`docs/visualizations.md`](visualizations.md) | [Open evidence](capabilities.md). not one universal empirical-validation certificate |
| `boston` · Boston | [`examples/boston/`](../examples/boston/), [`docs/cases/boston.md`](cases/boston.md) | [Open evidence](cases/boston.md). city data and distinct computational scales |
| `sioux` · Sioux Falls | [`examples/sioux-falls/`](../examples/sioux-falls/), [`docs/cases/sioux-falls.md`](cases/sioux-falls.md) | [Open evidence](cases/sioux-falls.md). not a city demographic compiler |
| `hong_kong` · Hong Kong | [`examples/hong-kong/`](../examples/hong-kong/), [`docs/assets/hong_kong/full_stack_r5/`](assets/hong_kong/full_stack_r5/) | [Open evidence](cases/hong-kong.md). not all methods have accepted results |
| `data_tools` · Data and GMNS tools | [`src/mobilitylab/data/`](../src/mobilitylab/data/), [`catalog/`](../catalog/), [`tools/mcl_data.py`](../tools/mcl_data.py) | [Open evidence](data-tools.md). source/query support |
| `generic_engine` · Generic RC5 engine | [`app/src/gmns_dynamic/`](../app/src/gmns_dynamic/), [`tools/mnl.py`](../tools/mnl.py) | [Open evidence](getting-started.md). distinct from later case adapters |
| `method_code` · Versioned method code | [`algorithms/`](../algorithms/), [`docs/assets/hong_kong/full_stack_r5/`](assets/hong_kong/full_stack_r5/) | [Open evidence](source-layout.md). case-specific versions |
| `reproduce` · Examples and checks | [`tools/`](../tools/), [`tests/`](../tests/), [`launcher/`](../launcher/) | [Open evidence](getting-started.md). builds do not run solvers |
<!-- project-structure-node-map:end -->
