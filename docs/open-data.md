# Open mobility data evidence

Explore source-qualified evidence about cities, scheduled transit, realtime endpoints, map features and shared mobility. These selected OMDV research results support source selection and provenance in the [city network workflow](city-workflow.md); they are separate from the network solver.

[City frame](#global-city-frame) · [GTFS](#gtfs-static) · [Realtime](#gtfs-realtime) · [OSM](#osm) · [GBFS](#gbfs-and-shared-mobility) · [Model interfaces](#model-and-interoperability-catalog)

## Choose what you need

| Your task | Use this part | What you receive |
|---|---|---|
| Understand source availability evidence | The six research layers below | Fixed, clearly scoped summaries with source references |
| Organize your own city/feed tables | [Executable local data tools](data-tools.md) | Standardized records, exact name/country matches and a quality report |
| Relate data to a network model | [City workflow](city-workflow.md) and [input contract](data-contract.md) | Guidance on identifiers, zones, demand and observations; no automatic raw-data compilation |

The machine-readable source is [catalog/open-data-evidence.json](../catalog/open-data-evidence.json), with [metric provenance](omdv-provenance.md). Its public selection was checked on 2026-09-17 against accepted OMDV tables. **That is an assembly/check date, not a common observation date for all sources.** The layer-specific research views below retain their own scope. No download, endpoint probe or scientific rerun was performed to create this page.

The public package includes compact summaries and selected code, not the full city registry, raw GTFS archives, endpoint lists, OSM extracts or manuscript material. [Data access and licenses](data-access.md)

## How the layers support a city study

| Evidence layer | Useful role | Do not substitute it for |
|---|---|---|
| City frame and catalog visibility | Define comparable study units and record city/source identities | Traffic analysis zones, centroid connectors or OD demand |
| GTFS static | Describe retained schedule-content evidence and potential transit sources | Passenger demand, observed vehicles or a working transit assignment model |
| GTFS-Realtime | Distinguish source metadata from past payload classifications | Current endpoint health, collected GPS trajectories or a continuous live service |
| OSM map features | Describe public-transport point evidence in the declared sample | A complete routable road network or an OSM-to-GMNS conversion |
| GBFS registry | Locate shared-mobility metadata categories | GPS trips, a bike network or reviewed city matches |
| Model-interface crosswalk | Select a relevant data format or upstream tool | Proof that each listed tool is integrated or a city dataset is available |

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

The all-retained and network-snapshot values are distinct views; keep their source scopes separate.

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
