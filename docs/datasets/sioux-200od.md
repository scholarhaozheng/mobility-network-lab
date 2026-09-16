# Sioux Falls · 200 OD

**Historical road-benchmark result · finite space–time column generation.**

| Quantity | Value |
|---|---:|
| Physical nodes / selected links | 24 / 64 |
| OD pairs | 200 |
| Dynamic nodes / arcs | 1,192 / 9,406 |
| Final columns | 446 |
| Recomputed path-flow objective | 943155.589771 |

## Verification

195 final candidate flows were directly saved. The remaining 251 final column flows were uniquely recovered from the saved final arc loads and the final path-link incidence identities. The reconstruction did not constrain the objective to the reference value. Path connectivity, demand conservation, shared capacity, nonnegativity and the objective were checked against saved records; the independently recomputed reference-primal objective agrees within the stated audit tolerance.

This is a recovered historical result, not a rerun of the current source distribution. Conditional recovery of a missing vector does not establish uniqueness of the original LP optimum. Final RMP duals and a separate complete pricing certificate were not preserved.

## Data access

Public access is limited to this result record and catalog metadata. Historical raw inputs and private reconstruction evidence are not redistributed here. The general Sioux Falls data source is linked under [upstream sources](../integrations.md); a freshly obtained upstream snapshot is not automatically byte-identical to the historical input.

## Reuse

Cite the exact instance and verification scope. To execute a new experiment with the current engine, supply a compatible input profile and record a new run; do not label it as a replay of this historical run without checking model and source identity.
