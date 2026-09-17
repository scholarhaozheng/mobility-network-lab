# Data access and notices

Code, source datasets and derived results have different provenance and may have different terms. A source repository's top-level license does not automatically resolve the rights of every externally obtained dataset.

## Included content

This source tree contains selected engine code, synthetic reference inputs, result metadata, compact aggregate evidence, selected non-geometric city/relationship result projections, user documentation and original presentation assets. Source-file hashes are recorded in `catalog/source-files.json`; OMDV provenance is recorded separately in `catalog/omdv-provenance.json`.

## Open-mobility evidence

The OMDV-derived public layer contains factual aggregate summaries plus the
selected 11,422-city result table and accepted source/content/city relationship
tables described in [open-data sources](open-data-sources.md). Raw GTFS ZIPs,
provider and endpoint URLs, credentials, geometries, realtime payloads, OSM/GBFS
source files, SEDAC fields and manuscript materials are excluded. Evidence
layers remain independent and must not be summed into a coverage count.

## Historical road data

The public catalog contains results-only records for the two historical Sioux CG experiments and the static FW baseline. Their private input tables and reconstruction volumes are not included. Consult the original data provider and the relevant data card before obtaining or redistributing source tables.

## Software dependencies

NumPy, SciPy, PyYAML and optional pandas retain their own licenses. They are installed as dependencies, not copied into the source tree. The separately distributed Windows runtime carries its own third-party notices.

## Project terms

The root [MIT License](../LICENSE) applies only to original project code for which the copyright holder has the right to grant that license. It does not relicense upstream code, external tools or third-party datasets. Review the repository's [third-party notices](../THIRD_PARTY_NOTICES.md) and [data license boundaries](../DATA_LICENSES.md) before reuse or redistribution.

## Contributions

Supply a specific source and access statement for every dataset. Keep private traces, credentials, full personal logs and unreviewed raw datasets out of public submissions.
