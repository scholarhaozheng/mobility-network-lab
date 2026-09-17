# Local GTFS ZIP content tool

`process-gtfs` exposes the accepted OMDV content-metrics implementation as a
small, parameterized offline command. It accepts one user-supplied local ZIP,
never downloads a feed, never extracts into the source directory, and writes
only to a new or empty output directory.

```bash
python -m pip install -r requirements-data-tools.txt
python -B tools/mcl_data.py process-gtfs \
  --zip path/to/feed.zip \
  --output results/gtfs-content-report
```

Outputs:

- `metrics.json`: content SHA-256; archive/member presence; agency, stop,
  route, trip, service, shape, frequency and transfer counts; coordinate
  validity; route-type/mode distributions; date evidence; streamed stop-time
  counts and referential checks.
- `member_presence.csv`: required/optional member presence and uncompressed
  member size.
- `warnings.csv`: retained parse warnings, including invalid stop-time
  references.
- `report.json`: concise run state and output list.

`stop_times.txt` is processed in one streaming pass. The tool does not claim to
evaluate service quality, current operations, road networks, TAZs, OD demand,
GPS map matching or assignment readiness.

## Reused implementation

The public adapter is
[`src/mobilitylab/omdv/gtfs/content_metrics.py`](../src/mobilitylab/omdv/gtfs/content_metrics.py).
It is adapted from OMDV
`scripts/analysis/parse_v25a_3_gtfs_unique_content.py`, source commit
`b2dca4449445c474c77db72ba4c8d18947108606`, source SHA-256
`bc4636f6eea18a66f4309d31f1e6576f50d5cbddc422e84f53709834426485cd`.
The adaptation removes OMDV repository/SQLite state, makes the input and output
paths caller-controlled, and adds a compact report. Parsing semantics and the
memory-bounded stop-times pass are retained.

## Real-feed validation

The adapter was run offline on one retained, read-only real feed already inside
the authorized OMDV source root:

- source record: `tld-821` (`Mobility Database local feeds_v2`)
- accepted city link: Victoria, Canada,
  `ghsl_urban_centre:R2024A_V1_1:ID_UC_G0:6`
- input size: 5,010 bytes
- content SHA-256:
  `5e16fc5ff45eb58fe99a3200d7f67a7628ec8ed99997c706561234a8f3a00d5b`
- output status: `parsed`
- matched accepted metrics: 1 agency, 3 stops, 2 routes, 11 trips, 22
  stop-time rows, 3 valid coordinates, 0 invalid coordinates, ferry mode,
  feed-info range 2025-10-30 through 2027-01-03

All 11 compared fields matched the accepted OMDV content-metrics row. The ZIP
is not redistributed; external users should run the command on a GTFS feed they
are permitted to obtain and process.
