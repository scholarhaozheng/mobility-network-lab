# Development roadmap

The next substantial step is a **complete real-city network instance**, not another summary catalog or a new repository. Existing assignment code and supporting data tools remain the reusable base.

## 1. Connect one city through the existing interface

Choose a bounded study area and reuse a lawful upstream network. Preserve its geometry and directed-link IDs. Supply or prepare zones, centroid/network access and a documented OD input. State whether demand is observed, estimated or synthetic. Run a model whose units and assumptions match those inputs, then map results back to the same network.

This stage must not rename a synthetic fixture as a city or treat a GTFS feed as an OD matrix. Network acquisition and zone creation remain development work, not released automation.

## 2. Add evidence and spatial hierarchy

Connect actual GPS, traffic counts, speeds or transit-service data to common network IDs and time intervals. Keep source, quality, unmatched observations and uncertainty. Record parent/child relations between zone or grid levels; coordinate aggregation alone is not a completed hierarchical transport model.

GPS traces and map matching require a genuine trajectory source and matching implementation. Exact city-name matching in the current metadata tool is a different operation.

## 3. Extend the computational methods

Retain current CG and static FW as distinct, documented baselines. The accepted [official tap-b Algorithm B static results](methods/origin-based-algorithm-b.md) provide a bounded verified origin-based branch: official TAPLab registered-adapter parity is established for classic Sioux; Boston B0/B1 use a task-local lossless adapter because the stock converter changes the frozen input contract. Exporting and inspecting native internal Policy Bush state, and fair repeated runtime comparisons, remain future work.

Bounded [Sioux Lagrangian R2 results](methods/distributed-assignment.md) and [Sioux/Boston ADMM R2_S results](methods/admm-space-time.md) now have explicit models, source and accepted saved checks. They are not full-network solutions or mandatory substitutions for the working CG baseline. The Boston Lagrangian transfer remains gated; the distinct frozen-policy Boston ADMM holdout passed its declared checks. Coupled primal–dual and queue-state / dynamic-programming extensions need their own models and tests.

## 4. Transfer the same workflow

The [bounded Hong Kong GMNS/data pilot](cases/hong-kong-gmns-pilot.md) now demonstrates official-derived object relationships but is **not assignment-ready**. Melbourne, Cairo and Paris remain candidate extensions. Add them through common data contracts, configuration, provenance and verification rather than separate solver rewrites. No complete assignment-ready dataset for these cities is claimed by this release.

[City workflow and current interfaces](city-workflow.md) · [Contribute a network](add-a-network.md)
