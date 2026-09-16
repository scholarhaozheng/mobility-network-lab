# Add a network

Add data and configuration rather than branching the optimization code for each city.

## 1. Define the instance

Choose a stable instance ID, geographical extent, time period, mode and mathematical problem. Record the source and whether each input is observed, inferred, synthetic or inherited from a benchmark.

## 2. Prepare compatible inputs

Follow the [input profile](data-contract.md). Preserve upstream IDs or provide a reversible mapping. Declare units. Use explicit zone access and keep the full allowed road set independent of initial routes. A clipped network requires an explicit treatment of boundary demand.

The current finite CG profile does not accept arbitrary static city data without adaptation. Travel times, capacity rates and demand periods must be translated through a documented modeling choice, not silently rounded or rescaled.

## 3. Validate, run, verify

Use `tools/mnl.py validate`, `run`, and `verify` with a new output directory. Keep the configuration, exact source identity and a concise result summary. Retain all final columns, including zeros.

## 4. Publish a data card

Create `docs/datasets/<instance-id>.md` with scope, source, license/access, network statistics, demand provenance, model profile, commands, outputs and verification limits. Add the corresponding entry to `catalog/datasets.json`.

The schema in `schemas/instance.schema.json` is catalog metadata; it does not replace the executable `case.json` profile. Reserved optional evidence slots are declarations only, not implemented GPS or transit adapters.

## 5. Update the catalog

Only list an instance as a bundled runnable case when its required files are present and permitted for redistribution. A results-only record must say so. Regenerate documentation, run the repository checks, and submit a focused change.
