# Project contributions and attribution

Mobility Computation Lab is presented by [Hao Zheng](../CITATION.cff). The contribution here is the documented modeling, implementation, integration and case analysis in this repository—not authorship of the upstream GMNS specification, `tap-b`/TAPLab, Frank–Wolfe, CG, ADMM, or underlying city datasets. The [third-party notices](../THIRD_PARTY_NOTICES.md), [data licenses](../DATA_LICENSES.md) and case source records retain distinct provenance and collaborators' credit.

## City-to-model representations

The project links roads, hierarchical zones, population and activity inputs, transit services, and supported observations to explicit demand and network models. Its adapters preserve identifiers, units, access semantics, and physical-link mappings across the documented city cases.

The [GMNS contract](data-contract.md) distinguishes a directed physical link from a centroid or other nonphysical connector. Boston's [GMNS exchange](datasets/boston-gmns-exchange.md) and [ACS/H3 population allocation](datasets/boston-population-households.md) connect source IDs and geographically distinct zone systems without declaring an observation to be an OD pair. The [Boston four-stage source record](datasets/boston-four-step-sources.md) and [Hong Kong engineering scenario](cases/hong-kong-four-stage.md) document the different assumptions that turn zonal attributes and service costs into demand. Sioux Falls instead begins with supplied benchmark OD. [Observation and feedback evidence](datasets/boston-behavior-feedback.md) is explicitly associated with the network; it does not silently calibrate all stages.

## Computational implementations and diagnostics

The repository brings together path-based and compressed static-assignment experiments with finite time-expanded CG, Lagrangian, and ADMM implementations. Project-specific work includes feasibility restoration, pricing and degeneracy handling, local-subproblem scaling, and reconstruction in the original flow space.

The static [Frank–Wolfe implementation](../algorithms/static_fw/) and [finite-path/native L3 controls](cases/boston-assignment.md) use a BPR/Beckmann contract. The [Algorithm B integration](integrations/taplab-tapb.md) reports official TAPLab registered-adapter parity only for classic Sioux Falls; Boston and Hong Kong numerical transfers use task-local lossless TAPLab-compatible adapters. Finite [two-phase CG](methods/space-time-cg.md), [Lagrangian capacity pricing](methods/distributed-assignment.md) and [ADMM R2](methods/admm-space-time.md) instead operate on bounded fixed-cost, hard-capacity time-expanded instances. Their reference agreements, pricing closure, feasible recoveries and residual checks have different meanings. Case pages retain the [Boston](cases/boston-space-time.md), [Sioux Falls](cases/sioux-space-time.md) and [Hong Kong](cases/hong-kong-space-time.md) results and individual limitations.

## Reusable cross-city computational tools

The project packages shared data interfaces, case configurations, and analysis tools for the eight real-city cases and the separate Sioux Falls demonstration benchmark. Documented examples connect zonal demand, generated paths, and physical-link results, allowing researchers to reuse the supported workflows and compare demand scales, network representations, and solution methods.

The reusable [vehicle-OD preparation and assignment CLI](RUN_YOUR_OWN_GMNS.md), [generic network command](getting-started.md), [saved-result inspector](../tools/mcl_results.py), [public Boston SQLite example](../examples/boston/SAVED_EXAMPLE.md), [source/catalog tools](data-tools.md) and [presentation builders](../tools/) expose separate supported entry points. This is not a universal any-city pipeline: the generic space–time command retains a 0.3.0-rc5 scope, while later Boston and Hong Kong CG case implementations have separately versioned evidence. [Architecture and source paths](architecture.md) · [Capability/instance statistics](capabilities.md) · [Complete technical walkthrough](full-walkthrough.md).

## Upstream foundation, implementation and evidence

| Established/upstream foundation | Project-specific implementation or integration | Evidence and source | Demonstrated scope |
|---|---|---|---|
| GMNS vocabulary and source city networks | Directed physical/access/zone mappings, source IDs and unit-preserving exchange | [Data contract](data-contract.md), [Boston GMNS exchange](datasets/boston-gmns-exchange.md), [Hong Kong GMNS](datasets/hong-kong-gmns.md) | City-specific bounded networks; not a new GMNS standard |
| Census, land-use, GTFS and observation providers | Versioned zonal preparation, declared cost/choice attributes and qualified network association | [Boston population fields](datasets/boston-population-households.md), [four-stage sources](datasets/boston-four-step-sources.md), [Hong Kong scenario](cases/hong-kong-four-stage.md) | Limited Boston and Hong Kong workflows; Sioux uses supplied OD |
| Static BPR/Beckmann and Frank–Wolfe | Static solver, scalable interfaces and independent original-space checks | [Static source](../algorithms/static_fw/), [Boston assignment](cases/boston-assignment.md), [Sioux static](datasets/sioux-static-fw.md) | Different cohorts and units; no cross-city objective ranking |
| `tap-b` Algorithm B and TAPLab | Adapter contracts and independent evaluation of accepted saved runs | [Algorithm B method](methods/origin-based-algorithm-b.md), [integration](integrations/taplab-tapb.md) | Official registered-adapter parity: Sioux only; task-local lossless transfers: Boston/Hong Kong |
| Finite path, compression and native L3 ideas | Explicit-path controls, representation change and reconstructed-flow diagnostics | [Boston method case](cases/boston-assignment.md), [native source](../algorithms/path_compression/diagnostic_l3/) | Accepted small controls; expanded tiers remain separately scoped |
| Finite time-expanded LP/CG and capacity decomposition | Case preparation, Phase-I/II pricing/degeneracy handling, feasible recovery, local QPs and original-space checks | [CG method](methods/space-time-cg.md), [Lagrangian](methods/distributed-assignment.md), [ADMM](methods/admm-space-time.md), [source layout](source-layout.md) | Bounded Boston/Sioux/Hong Kong evidence with method-specific acceptance |
| Open-data registries and documented source files | Catalog/explorer, exact name-country matching and local content-query tools | [Explorer](open-data-explorer.md), [data tools](data-tools.md), [provenance](open-data-sources.md) | Supporting evidence; catalog rows are not automatic model inputs |

The table is a guide to inspectable source and saved evidence. [Cite the repository and original sources](citation.md).
