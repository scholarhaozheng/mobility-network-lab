# Data catalog

The catalog separates **runnable inputs**, **historical result records** and **external sources**. Browse the machine-readable [`catalog/datasets.json`](../catalog/datasets.json) or run `python tools/mnl.py catalog`.

## Road benchmark results

| Record | Network | Model | Access |
|---|---|---|---|
| [Sioux Falls · 200 OD](datasets/sioux-200od.md) | 24 physical nodes, 64 selected links | Historical finite space–time CG | Results record |
| [Sioux Falls · 250 OD](datasets/sioux-250od.md) | 24 physical nodes, 69 selected links | Historical finite space–time CG | Results record |
| [Sioux Falls · static FW](datasets/sioux-static-fw.md) | 24 physical nodes, 76 links, 528 OD records | Approximate static Beckmann assignment | Results record |

These are benchmark instances rather than newly collected city networks. Historical source inputs are not bundled in this public candidate; consult each record for access and verification details.

## Runnable reference inputs

[Two bundled synthetic examples](examples.md) cover automatic routes and a zone-based capacity constraint. They support a clean source quick start without redistributing third-party road data.

## City contributions

Add a source-backed city instance through the [instance guide](add-a-network.md). Publish only datasets that actually exist and have a declared access policy. Future city collections are listed in the [roadmap](roadmap.md), not in the available-data table.
