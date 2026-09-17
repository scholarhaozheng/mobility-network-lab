# Open mobility evidence files

These are public, non-geometric projections of accepted Open Mobility Data
Visibility (OMDV) result tables. They are historical research snapshots, not a
live registry or a statement that an unmatched city has no transport data.

## Files

- `city_evidence.csv` / `.json.gz`: all 11,422 cities in the accepted frame.
- `content_city.csv` / `.json.gz`: all 12,442 accepted content-hash-to-city links.
- `source_content_city.csv` / `.json.gz`: 14,328 complete source-to-content-to-city
  relations plus 2,377 explicit source/content rows with no accepted city link.
- `*_schema.json`: field definitions, source columns and transformation rules.

The JSON copies use deterministic gzip compression to keep the manual upload
small. They expand to the same row arrays as the corresponding CSV files.

The source/content/city files intentionally preserve many-to-many links. Two
accepted content-city rows have no mapped source record; this state is retained
in `content_city` as `CONTENT_CITY_ONLY_NO_MAPPED_SOURCE_RECORD`.

No raw GTFS ZIP, provider URL, credential, geometry, SEDAC input or inferred
bbox relationship is included. See [Sources](../../open-data-sources.md) and
the [browser](../../open-data-explorer.md).
