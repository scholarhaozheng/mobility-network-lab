# Network and data catalog

Browse **network computations and their visual results** first. Supporting data tools and OMDV evidence summaries are separate resources, not a count of runnable city models. Machine-readable records remain in [catalog/datasets.json](../catalog/datasets.json); use `python tools/mnl.py catalog` to list them.

## Road benchmark results

| Record | Network | Model | Access |
|---|---|---|---|
| [Sioux Falls · 200 OD](datasets/sioux-200od.md) | 24 physical nodes, 64 selected links | Historical finite space–time CG | Result record and figures |
| [Sioux Falls · 250 OD](datasets/sioux-250od.md) | 24 physical nodes, 69 selected links | Historical finite space–time CG | Result record and figures |
| [Sioux Falls · static FW](datasets/sioux-static-fw.md) | 24 physical nodes, 76 links, 528 OD records | Approximate static Beckmann assignment | Result record |

[Open the six-figure gallery](visualizations.md). These are benchmark experiments, not newly collected city networks. Historical raw inputs are not bundled; consult each record for access and verification scope. The static and space–time objectives are not the same model.

## Runnable reference inputs

[Two bundled synthetic examples](examples.md) cover automatic routes and a zone-based capacity constraint. They support installation and regression checks without redistributing third-party road inputs. [Run the network workflow](getting-started.md).

## City instances and common interfaces

[Add a source-backed network](add-a-network.md) using the shared [city workflow](city-workflow.md). A complete contribution connects network, zones, OD and available observations through explicit identifiers and units. Future city collections remain in the [roadmap](roadmap.md) until their data and computations actually exist.

## Supporting metadata tools and evidence

[Executable OMDV data tools](data-tools.md) normalize local city/catalog records and perform exact city/country matching. Four authorized OMDV modules and two labelled fixtures are bundled; they are not a live downloader or GPS matcher.

The separate [open-data evidence guide](open-data.md) documents retained source-specific summaries for GHSL, GTFS, realtime, OSM, GBFS and interoperability. Raw feeds, endpoint lists, geometries and bulk archives are excluded. These evidence layers are not additive and do not imply bundled assignment-ready city models.
