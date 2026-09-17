# Local catalog and city-matching tools

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

The [open mobility evidence guide](open-data.md) provides fixed research summaries and their source scopes. The command above instead computes results from your own local tables; it does not regenerate those global totals. Use the [city workflow](city-workflow.md) to decide which identifiers and observations a network model still needs.

## Scientific boundary

Named-entity city matching is not GPS map matching. Catalog parsing is not a
GTFS ZIP parser. A metadata URL is not evidence of current endpoint health.
These tools do not compile a city network, estimate demand, build hierarchical
zones, or connect GTFS/GPS data to the column-generation solver.
