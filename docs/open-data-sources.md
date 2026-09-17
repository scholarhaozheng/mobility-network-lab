# Open data sources and reproduction scope

The downloadable tables are deterministic, non-geometric projections of
tracked accepted results from Open Mobility Data Visibility (OMDV). They were
prepared on 2026-09-17 from OMDV source head
`09575a51973f4289fda7adae85130a10ab554b36` and accepted release commit
`e0c7d2f7ca4e3f72563f14346d96df5f0c04e937`.

## Public products

| Product | Rows | Unit and scope |
|---|---:|---|
| [City evidence CSV](data/open-mobility/city_evidence.csv) | 11,422 | One accepted GHSL urban-centre row; selected catalog, GTFS and realtime fields |
| [Content–city CSV](data/open-mobility/content_city.csv) | 12,442 | One accepted content-hash/city relationship |
| [Source–content–city CSV](data/open-mobility/source_content_city.csv) | 16,705 | 14,328 complete chains plus 2,377 explicit source/content rows without an accepted city link |

Equivalent JSON files and machine-readable schemas are in
[`data/open-mobility/`](data/open-mobility/README.md). The product hashes and
row checks are recorded in
[`catalog/open-data-products.json`](../catalog/open-data-products.json).

## Accepted source files

| Role | OMDV repository path | SHA-256 |
|---|---|---|
| Complete city frame | `outputs/tables/v25a_3_4_global_city_analysis_matrix.csv` | `9784dd2b2c4eaef94ae63b82b0904b9cf89920a03d96d77d1a7cd448eb354f09` |
| Source record → content | `outputs/tables/v25a_3_2_feed_provenance_roles.csv` | `109b32d49e7aa4eb3984dbc1aa6f766ba230b77fa16b57816f97086b60a0e90f` |
| Content → city | `outputs/tables/v25a_3_1_gtfs_content_city_links.csv` | `7d591d2ccfed082adcea48cdcc1121f11c7d5bedafbf5408f974013ca254c070` |
| Content view membership | `outputs/tables/v25a_3_2_gtfs_content_view_membership.csv` | `07c9609796f2d92225b47b305d88c8fdca101d0dd691851eda3f753eee78defa` |
| Accepted accounting summary | `outputs/tables/v25a_3_3_gtfs_global_content_view_summary.csv` | `0878b80eddc7109087ce493f4340a46a02006688ef1cab7b785b9e70b3757e8c` |

The exporter verifies these hashes before writing. It selects and renames
columns, performs exact `content_sha256` joins, adds explicit relationship-state
labels, and sorts records. It does not spatially rematch stops, infer a city
from a name/bbox, refetch a feed, or recompute an accepted scientific result.

## Relationship accounting

- 5,182 mapped parseable source records reference 4,423 content hashes.
- The all-retained content universe has 4,425 hashes. Two accepted content
  hashes have no mapped source record.
- 12,442 accepted content–city pairs cover 2,959 cities.
- Exact joins yield 14,328 source-record–city associations. Source records
  that have no accepted city link remain visible as
  `SOURCE_CONTENT_ONLY_NO_CITY_LINK`.
- Two content–city rows for one hash have no mapped source record and remain
  visible as `CONTENT_CITY_ONLY_NO_MAPPED_SOURCE_RECORD`.

This deliberately preserves many-to-many relationships: different records can
share one hash, and one content hash can link to several cities.

## Source and rights boundaries

The city frame originates from GHSL UCDB R2024A under the European Commission
reuse terms referenced by the OMDV source manifest. The public projection keeps
the stable city identifier, label, country codes and accepted population value;
it excludes geometry, area geometry, coordinates and SEDAC fields.

GTFS and catalog columns are factual identifiers, hash relationships, counts
and accepted research classifications. The projection excludes raw feed files,
provider URLs, endpoint URLs, tokens, logins, cookies and provider metadata not
needed for the relationship. It does not relicense any absent upstream feed.

The root MIT License covers Mobility Computation Lab software and the selected
OMDV original implementation authorized by the copyright holder. It is not a
blanket license for upstream data. See [Data licenses](../DATA_LICENSES.md).

## Reproduction modes

- **Compact:** run `tools/build_open_mobility_exports.py` against the named,
  hash-matched accepted OMDV outputs. This reproduces these public projections.
- **Exact historical:** reconstruct the accepted OMDV analysis from its
  specified historical inputs. Some inputs may require separate lawful access;
  the public repository does not pretend to bundle them.
- **Current-source:** acquire current external sources and rerun the relevant
  OMDV workflow. Results may differ from the fixed historical snapshot.

The accepted R1.2.4 Package A and B files remain in the source OMDV project and
were not rebuilt or copied. Their verified source hashes are respectively
`c3e3a3c46a4126e110a6690b21f89e9b2853c0bbf13dedf996d8d2e57189a7bb`
and `565f4edddeb528f2648b3a44e0edba1a1af9bd4eaf81387a31f8a104ad9e83fa`.
