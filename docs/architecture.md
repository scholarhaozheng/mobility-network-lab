# Architecture

The public tree presents four layers while retaining the tested Mobility Network Lab numerical layout.

## 1. Local data tools and evidence

- catalog/open-data-evidence.json — accepted aggregate values and claim boundaries;
- catalog/interoperability-sources.json — formats, standards, and upstream tools;
- catalog/omdv-provenance.json — source commits, hashes, package identities, and reuse decisions;
- catalog/omdv-authorized-files.json — selected-copy MIT allowlist and destination hashes;
- src/mobilitylab/omdv/ — selected OMDV normalization, matching, audit, and summary implementations;
- src/mobilitylab/data/ — the connected local workflow plus evidence loaders;
- tools/mcl_data.py — public local-file CLI.

No raw OMDV dataset or source checkout is required. The executable workflow
accepts caller-supplied CSVs and remains separate from the fixed accepted
evidence catalog.

## 2. City and model interface

- app/src/gmns_dynamic/external_network_input.py — current input contract and normalization;
- app/src/gmns_dynamic/external_sioux_ingest.py — benchmark-oriented ingestion support;
- app/cases/ — small self-contained examples;
- schemas/ — machine-readable catalog and instance contracts.

This is a model-ready interface, not a city compiler. Hierarchical zones and general network compilation remain on the roadmap.

## 3. Assignment and optimization

- algorithms/static_fw/ — static Frank–Wolfe implementation;
- app/src/gmns_dynamic/explicit_network_workflow.py — explicit space–time network;
- app/src/gmns_dynamic/run_full_cg_v1.py — reference LP and Phase-I/Phase-II column generation;
- tools/mnl.py — public command entry point.

## 4. Benchmarks and verification

- catalog/datasets.json — runnable examples, evidence summaries, and benchmark records;
- docs/datasets/ — result cards and interpretation boundaries;
- launcher/ — solver-free verification;
- tools/check_repository.py and tools/publication_gate.py — repository and publication checks.

The compatibility layout avoids moving tested solver files merely to match a new package tree. Navigation and contracts provide the layer separation.
