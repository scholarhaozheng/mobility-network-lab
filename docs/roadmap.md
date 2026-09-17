# Development roadmap

The next substantial step is a **complete real-city network instance**, not another summary catalog or a new repository. Existing assignment code and supporting data tools remain the reusable base.

## 1. Connect one city through the existing interface

Choose a bounded study area and reuse a lawful upstream network. Preserve its geometry and directed-link IDs. Supply or prepare zones, centroid/network access and a documented OD input. State whether demand is observed, estimated or synthetic. Run a model whose units and assumptions match those inputs, then map results back to the same network.

This stage must not rename a synthetic fixture as a city or treat a GTFS feed as an OD matrix. Network acquisition and zone creation remain development work, not released automation.

## 2. Add evidence and spatial hierarchy

Connect actual GPS, traffic counts, speeds or transit-service data to common network IDs and time intervals. Keep source, quality, unmatched observations and uncertainty. Record parent/child relations between zone or grid levels; coordinate aggregation alone is not a completed hierarchical transport model.

GPS traces and map matching require a genuine trajectory source and matching implementation. Exact city-name matching in the current metadata tool is a different operation.

## 3. Extend the computational methods

Retain current CG and static FW as distinct, documented baselines. Reuse an identified origin-based / Policy Bush implementation and develop transparent forward-flow, backward-value and feasible-update calculations. Do not label path aggregation as a completed Bush solver.

Primal–dual, Lagrangian, ADMM and queue-state / dynamic-programming extensions need explicit models and their own tests. They are not mandatory substitutions for the working CG baseline.

## 4. Transfer the same workflow

Hong Kong, Melbourne, Cairo and Paris are candidate city extensions. Add them through common data contracts, configuration, provenance and verification rather than separate solver rewrites. No complete dataset for those cities is claimed by this release.

[City workflow and current interfaces](city-workflow.md) · [Contribute a network](add-a-network.md)
