# Network and data catalog

Browse **network computations and their visual results** first. Supporting data tools and OMDV evidence summaries are separate resources, not a count of runnable city models. Machine-readable records remain in [catalog/datasets.json](../catalog/datasets.json); use `python tools/mnl.py catalog` to list them.

## Source-backed city instance

| Record | Network | Model | Access |
|---|---|---|---|
| [Central Boston](datasets/boston-central.md) | 2,852 physical nodes, 5,091 directed links, 177 H3 model zones | Preserved network-proxy demand plus actual-assessment activity prior, static FW baseline, real bus GPS road matching, GTFS linkage | Rebuildable component, SQLite queries, two offline maps and a [five-map gallery](datasets/boston-central.md#boston-visual-gallery) |
| [Central Boston demand and transit feedback](datasets/boston-behavior-feedback.md) | Shared Boston road network and 177 H3 zones; fixed 36-OD midday panel | Transferred household rates, activity-weighted distribution, nested mode response, observation sensitivity and static FW | Current semantic-fix component; 26 CSV data tables, queryable SQLite and a [saved-result example](../examples/boston/SAVED_EXAMPLE.md) |
| [Boston bounded space–time CG](cases/boston-space-time.md) | 90 physical nodes, 125 directed links, 10 ODs; 3-second steps / 100-step horizon | Fixed-cost hard-capacity Phase I/II; same-graph arc-LP match; R4 independent full-DAG pricing closure | Ten PNG/SVG figure pairs, exact public plot inputs, source hashes and numerical validation; **not citywide** |
| [Hong Kong bounded GMNS/data pilot](cases/hong-kong-gmns-pilot.md) | 780 physical nodes, 1,239 directed links, 95 SSG fine/10 STPUG parent zones | Official-derived network, 2021 census allocation, GTFS and detector relationships; deterministic seed | Five SVGs, offline validation/trace; **assignment_ready=false**, no solver run |

The original network and activity-prior tracks remain bounded engineering examples. Their 50,000-trip total and behaviour parameters are assumptions. The newer feedback component uses transferred regional household rates and a conditional midday panel; it does not convert its generation total into assigned traffic. The short bus-position capture is not passenger OD, and no LODES employment association is included. The bounded CG pilot is a **separate demand/model instance**, not a continuation of static FW or the semantic service-feedback panel.

## Road benchmark results

| Record | Network | Model | Access |
|---|---|---|---|
| [Sioux Falls · 200 OD](datasets/sioux-200od.md) | 24 physical nodes, 64 selected links | Historical finite space–time CG | Result record and figures |
| [Sioux Falls · 250 OD](datasets/sioux-250od.md) | 24 physical nodes, 69 selected links | Historical finite space–time CG | Result record and figures |
| [Sioux Falls · static FW](datasets/sioux-static-fw.md) | 24 physical nodes, 76 links, 528 OD records | Approximate static Beckmann assignment | Result record |

[Open the six-figure gallery](visualizations.md). These are benchmark experiments, not newly collected city networks. Historical raw inputs are not bundled; consult each record for access and verification scope. The static and space–time objectives are not the same model.

Accepted Sioux 200/250-OD [Lagrangian R2 and ADMM R1](methods/distributed-assignment.md) results use selected-OD finite space–time shared-capacity instances; they are additional bounded algorithm evidence, not full-network or static UE results.

## Runnable reference inputs

[Two bundled synthetic examples](examples.md) cover automatic routes and a zone-based capacity constraint. They support installation and regression checks without redistributing third-party road inputs. [Run the network workflow](getting-started.md).

## Common interfaces and additional cities

[Add a source-backed network](add-a-network.md) using the shared [city workflow](city-workflow.md). A complete contribution connects network, zones, OD and available observations through explicit identifiers and units. The Central Boston instance demonstrates one bounded implementation; it is not a universal raw-city compiler. Future city collections remain in the [roadmap](roadmap.md) until their data and computations actually exist.

## Supporting metadata tools and evidence

[Executable OMDV data tools](data-tools.md) normalize local city/catalog records and perform exact city/country matching. Four authorized OMDV modules and two labelled fixtures are bundled; they are not a live downloader or GPS matcher.

The separate [open-data evidence guide](open-data.md) documents retained source-specific summaries for GHSL, GTFS, realtime, OSM, GBFS and interoperability. Raw feeds, endpoint lists, geometries and bulk archives are excluded. These evidence layers are not additive and do not imply bundled assignment-ready city models.
