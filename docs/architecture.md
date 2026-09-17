# Architecture

## City modelling is the organizing workflow

Mobility Computation Lab centres on **networks, zones, demand, evidence and network computation**. Data catalogs support this workflow; they do not replace a city model. The [city workflow](city-workflow.md) distinguishes currently executable components from extensions.

## Network, zone-access and demand interface

- `app/src/gmns_dynamic/external_network_input.py` reads the current explicit model profile.
- `app/cases/` contains self-contained synthetic regression inputs, not new city datasets.
- `schemas/` and [data contract](data-contract.md) document IDs, field mappings, units and model conditions.

The supported route starts with prepared network and demand tables. Road acquisition, hierarchical-zone generation, OD estimation and GPS matching require separate actual implementations; a name in a registry is not a model-ready city.

## Assignment and optimization

- `app/src/gmns_dynamic/explicit_network_workflow.py` prepares the explicit space–time problem.
- `app/src/gmns_dynamic/run_full_cg_v1.py` retains the Phase-I/Phase-II column-generation engine.
- `tools/mnl.py` is the network command entry point.
- `algorithms/static_fw/` is a separate static Beckmann / Frank–Wolfe implementation.

Do not compare these models as if a shared CSV vocabulary made their objectives, capacities or time definitions identical. New origin-based / Policy Bush and coupled methods are research extensions; existing CG remains a usable baseline.

## Supporting mobility data

`src/mobilitylab/omdv/` contains selected authorized city/catalog normalization and exact name/country matching functions. `src/mobilitylab/data/catalog_city_workflow.py` and `tools/mcl_data.py` call them on user-supplied local files. This is independent of the fixed aggregate evidence catalog.

`catalog/open-data-evidence.json`, `omdv-provenance.json`, `omdv-authorized-files.json` and `interoperability-sources.json` preserve summaries, sources and reuse scope. The OMDV study does not supply city OD or GPS observations to the solver automatically.

## Results and visible verification

`launcher/` verifies saved outputs. `catalog/datasets.json` and `benchmark-results.csv` identify the bundled examples and historical benchmark records. The [visual gallery](visualizations.md) exposes the retained six figures; data cards preserve their interpretation limits.

## Maintain the working implementation

The existing numerical and data-tool source layouts remain unchanged. The GitHub README and Pages homepage are different presentations of the same project; both must preserve the city-network focus and lead to real tools and figures. `tools/build_site.py` is the Pages generator, not a replacement for root `README.md`.
