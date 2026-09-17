# Local city-evidence, catalog and GTFS tools

Mobility Computation Lab includes a bounded, executable workflow selected from
original Open Mobility Data Visibility code:

1. normalize a user-supplied MobilityDatabase-style feed catalog;
2. standardize a user-supplied external-city table;
3. match feed municipality names to cities by exact normalized name plus
   two-letter country code;
4. write catalog summaries, schema audits, match tables, city summaries, and a
   machine-readable quality report.

This is local metadata processing. It makes no network request and does not
require the OMDV source repository.

The same command also queries the bundled 11,422-row public evidence table and
runs an authorized OMDV-derived content parser on a user-supplied local GTFS
ZIP. These modes are offline and do not modify the ZIP.

## Isolated installation

The data tools have their own dependency file so the retained RC5 numerical
runtime is not changed. The exact pre-existing environment used for this
release check is recorded in `requirements-data-tools-tested.txt`.

```bash
python -m venv .venv-data
.venv-data/bin/python -m pip install -r requirements-data-tools.txt
```

On Windows PowerShell, use
`.venv-data\Scripts\python.exe` instead of `.venv-data/bin/python`.

## Run the included example

```bash
python -B tools/mcl_data.py catalog-city-match --catalog examples/data-tools/feeds_sample.csv --cities examples/data-tools/external_city_universe_sample.csv --output results/data-tools-demo
```

The output directory must be new or empty. The command writes:

- `normalized_catalog.csv`;
- `standardized_cities.csv`;
- `feed_city_matches.csv`;
- `city_feed_summary.csv`;
- `ambiguous_city_keys.csv`;
- catalog summary and source-schema audit tables;
- `quality_report.json`.

The report includes input hashes, row counts, match-status counts, ambiguous
keys, output hashes, and explicit limitations. Every value depends on the
supplied files; headline evidence constants are not used as processing output.

## Query accepted city evidence

Use the stable city ID when known:

```bash
python -B tools/mcl_data.py query-city --city-id ghsl_urban_centre:R2024A_V1_1:ID_UC_G0:11185 --include-relations
```

Or use an exact city name plus ISO2/ISO3 country code:

```bash
python -B tools/mcl_data.py query-city --name "Hong Kong" --country CHN --include-relations
python -B tools/mcl_data.py query-city --name Melbourne --country AUS
python -B tools/mcl_data.py query-city --name Cairo --country EGY
python -B tools/mcl_data.py query-city --name Paris --country FRA
```

Hong Kong, Melbourne and Paris return accepted source/content relationships.
Cairo returns a real matched city row with `no_stop_content` in the checked
historical GTFS views; that state is not the same as a failed city lookup and
does not claim Cairo has no transport data today.

City names are not unique keys. `Lawrence, USA`, for example, resolves to three
city IDs. The command exits with an ambiguity message unless `--all-matches`
is supplied. A name absent from the table returns `not_found`, which remains
distinct from a matched city with `no` evidence in a layer.

The [browser](open-data-explorer.md) provides a no-server view. CSV, JSON and
field dictionaries are in [`data/open-mobility/`](data/open-mobility/README.md).

## Process one local GTFS ZIP

```bash
python -B tools/mcl_data.py process-gtfs --zip path/to/feed.zip --output results/gtfs-content-report
```

This OMDV-derived path calculates content/member, row-count, coordinate-quality,
route-type, date and streamed stop-time metrics. It never downloads a feed or
extracts files into the project. See the [GTFS tool specification and real-feed
validation](gtfs-zip-tool.md).

## Catalog input

The catalog input is CSV. The normalizer accepts common evolving aliases:

| Meaning | Example accepted names |
|---|---|
| Feed identifier | `feed_id`, `source_id`, `mdb_source_id`, `id` |
| Feed type | `feed_type`, `data_type`, `format` |
| Municipality | `municipality`, `location.municipality`, `city` |
| Country code | `country_iso2`, `location.country_code`, `country_code` |
| Provider | `provider`, `operator`, `agency`, `organization_name` |
| URL | `url`, `feed_url`, `urls.latest`, direct-download aliases |
| Bounding box | minimum/maximum latitude and longitude aliases |

Missing optional columns are retained as missing values. Feed types and status
labels are normalized. Invalid two-letter country codes are not silently
accepted as ISO2 codes.

## City input

The city input is CSV. Useful fields are:

- `external_city_id` (or `city_id`/`id`); a deterministic identifier is
  generated when absent;
- `city_name` (or `name`/`city`);
- `country_iso2` (or `country_code`/`iso2`);
- optional country name, population, latitude, longitude, source, source year,
  capital/megacity flags, and notes.

A city name and valid two-letter country code are needed for matching. Other
fields remain available in `standardized_cities.csv`.

## Matching and ambiguity

The selected OMDV matcher lowercases names, trims whitespace, and treats
hyphens and underscores as spaces. It does not remove diacritics, guess
transliterations, use coordinates, or perform fuzzy matching.

The MCL adapter detects duplicate normalized city/country keys before invoking
the matcher. Such keys receive `ambiguous_city_key` and are not automatically
assigned. Missing municipality and country fields remain distinct unmatched
statuses. All source feed rows remain in the match output.

## Python API

```python
from mobilitylab.data.catalog_city_workflow import run_catalog_city_workflow

report = run_catalog_city_workflow(
    "my_feed_catalog.csv",
    "my_cities.csv",
    "results/my_catalog_match",
)
print(report["quality"]["match_status_counts"])
```

The selected lower-level functions are also importable from
`mobilitylab.omdv.geospatial` and `mobilitylab.omdv.ingest`.

## Related evidence and next steps

The [open mobility evidence guide](open-data.md) provides fixed research summaries and their source scopes. `query-city` reads the bundled accepted projection; `catalog-city-match` and `process-gtfs` compute results from user-supplied local files. None regenerates the global study. Use the [city workflow](city-workflow.md) to decide which identifiers and observations a network model still needs.

## Scientific boundary

Named-entity city matching is not GPS map matching. GTFS content metrics are
not a service-quality or assignment model. A metadata URL is not evidence of
current endpoint health. These tools do not compile a city road network,
estimate demand, build hierarchical zones, or connect GTFS/GPS data to the
column-generation solver.
