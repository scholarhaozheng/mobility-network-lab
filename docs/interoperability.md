# Interoperability source catalog

The [machine-readable catalog](../catalog/interoperability-sources.json) separates three ideas:

1. a source or feed registry;
2. an exchange or file standard;
3. a modeling or conversion tool.

These roles must not be conflated. GMNS, TNTP, MATSim XML, SUMO, or OpenDRIVE can describe model-ready networks without proving that a current city dataset is publicly available. GTFS, GTFS-Realtime, NeTEx, and SIRI describe information structures or interfaces; they are not global city registries.

The current executable input path is the declared finite network profile in [the data contract](data-contract.md). OSM2GMNS and other upstream tools may prepare compatible inputs independently, but their code is not vendored and their outputs still require unit, identifier, demand, capacity, and provenance checks.
