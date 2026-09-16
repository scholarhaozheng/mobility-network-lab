# Roadmap

The current release surface is the finite-network optimization workflow, synthetic reference inputs, and documented road-benchmark results. This page describes future extensions rather than available datasets.

## City instances

Add source-backed Hong Kong, Melbourne, Cairo and Paris instances through the same catalog and explicit input profiles. Begin with a defensible study area and data provenance; add more cities after the first instance is reproducible.

## Spatial and demand layers

Support reusable zone boundaries, centroid/connector maps and cross-resolution relationships. Extend demand preparation with clearly separated benchmark, synthetic, inferred and observed inputs.

## Evidence adapters

Add permitted public GPS samples, segment-level quality control and explicit map-matching to network link IDs. Connect traffic counts/speeds and GTFS through separate provenance-preserving adapters. A GTFS shape or a generated shortest path is not a GPS observation.

## Solver adapters

Integrate origin-based/Bush methods and promote compressed ALM only after the exact model, successful implementation and complete output evidence are aligned. Keep static UE, hard-capacitated space–time optimization and coupled dynamic models distinct.

## Release criteria

A feature enters the supported catalog when it has an actual entry point, declared inputs, a permitted example or documented acquisition route, and repeatable checks. Roadmap items carry no promised completion date.
