# Open mobility data evidence

Mobility Computation Lab publishes a compact, rights-conscious view of accepted Open Mobility Data Visibility results. It does not redistribute raw feeds, source registries, city geometries, endpoint URLs, or manuscript material.

The machine-readable source for this page is [catalog/open-data-evidence.json](../catalog/open-data-evidence.json). Values were checked against current tracked OMDV reference files on 2026-09-17. They are not a new scientific run.

These fixed evidence summaries are separate from the
[executable local data tools](data-tools.md). Processing a user-supplied
catalog does not reproduce or replace the accepted research totals below.

## Global city frame

The common analytical denominator contains **11,422 GHSL urban centres**. It is a frame for comparison, not a list of every settlement and not transport evidence by itself.

The frozen strict two-registry catalog scenario contains **439 cities**. That number describes a defined metadata-visibility rule; it is not a service-coverage count.

## GTFS static

| Measure | Accepted value | Meaning |
|---|---:|---|
| Eligible GTFS source records | 6,951 | Feed-record universe; not cities |
| All-retained parseable source records | 5,182 | Source records represented in the retained content view |
| All-retained unique content hashes | 4,425 | Deduplicated parseable contents; not source records |
| Cities with inside-polygon stop evidence | 2,959 | Stop-content evidence; not operating-service coverage |
| Network-snapshot unique content hashes | 4,357 | Separate V25A.2 snapshot view |

The older example value 4,418 is not used: the current accepted tracked reference is **4,425**.

## GTFS-Realtime

The accepted table contains **2,465 metadata-level endpoint representatives**. It does not establish present endpoint health.

In the bounded network snapshot, 433 cities were classified as having static evidence plus a realtime parse-success snapshot. In the all-retained sensitivity view, the corresponding class contains 505 cities and the requires-key-or-blocked class contains 59 cities. These classes are snapshot evidence, not continuous service availability.

## OSM

The accepted V6 evidence is a bounded **29-extract** sample. Within the sample countries, 916 GHSL urban-centre rows were evaluated, 791 had at least one bbox-joined OSM point feature, and 245,561 point-feature joins were recorded.

OSM evidence means map-feature visibility. It does not prove GTFS availability, official service, a timetable, route coverage, or service coverage.

## GBFS and shared mobility

The accepted local registry summary contains **1,516 system rows** across 48 countries and 1,146 location strings. No live GBFS feed was fetched for that summary. Location strings were not treated as reviewed GHSL city matches.

GBFS is shared-mobility metadata and is kept separate from public-transport feed evidence.

## Model and interoperability catalog

The compact [interoperability catalog](../catalog/interoperability-sources.json) records 13 formats, standards, and tools, including GMNS, OSM2GMNS, TNTP, MATSim, SUMO, AequilibraE, OpenDRIVE, GTFS, NeTEx, and SIRI.

An entry documents an interface or reuse pathway. It does not establish that a city dataset exists, and it does not mean that every listed tool is implemented here.

## Non-additivity rule

Never sum these layers into a global “covered cities” total. Their units, source frames, observation dates, and meanings differ. Use a layer-qualified metric and preserve its boundary statement.
