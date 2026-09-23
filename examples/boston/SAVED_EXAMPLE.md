# Run the Central Boston saved-result example

This command rebuilds a small SQLite database from the accepted public CSV component and exports five saved-result queries. It uses Python 3.12 or a compatible Python 3 interpreter and the standard library. The tested platform was Windows with Python 3.12.14. The public CSV component must already be present locally; this command does not download or extract it.

Place `run_saved_example.py` in `examples/boston/` beside the existing `behavior_feedback_r1_semantic_fix_r1/` directory, which supplies the trusted builder and query definitions. Point `--data-dir` to an extracted copy of that versioned public component containing `data/public_table_manifest.csv`. The copied data can be in a different directory from the trusted code.

Two accepted data locations are available. With the compact component already included in this repository, use `--data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1"`. With the separately downloaded `BOSTON_BEHAVIOR_FEEDBACK_PUBLIC_DATA_EN.zip`, extract the ZIP and use the extracted **`public_component/` subdirectory** as `--data-dir`; it contains the same accepted manifest and CSVs. Do not pass the outer ZIP or its parent directory. The trusted builder and query utility still come from the sibling repository component, even when CSV data live elsewhere.

From the repository root:

```sh
python -B examples/boston/run_saved_example.py \
  --data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1" \
  --output "saved example output"
```

On PowerShell, put the command on one line or replace each trailing `\` with a backtick. Choose a new or empty output directory outside both the data and code directories. Paths with spaces and non-ASCII characters are supported.

The output contains `boston_saved_example.sqlite`, `queries/trace.csv`, `queries/response.csv`, `queries/unavailable.csv`, `queries/parameters.csv`, `queries/transfers.csv`, `DEMO_RESULTS.md`, and `demo_summary.json`. The response query defaults to saved OD `panel_od_019` at `12:30:00`; use `--od-id` and `--departure-time` to inspect another saved key. A key with no response rows yields a header-only response CSV and a `no_saved_rows_for_selected_key` status. Input and build failures exit nonzero. A failed build or query leaves `demo_failure.log` in its output directory for local diagnosis; choose a fresh output directory to retry.

The wrapper checks the accepted semantic-fix manifest, its 26 declared CSV files, hashes, rows, and required query columns before invoking the shipped builder. It rejects source paths that escape the component. It preserves the builder's identifier policy, including leading zeros in identifier fields. This entry point is version-pinned; newer scientific components require deliberate review and an updated wrapper.

The generation total in the report is a transferred household-rate daily person-trip estimate. Fixed-panel assigned S1/S2 vehicle-trip totals are separate modeled quantities. The scenario execution and validation labels are read from saved tables and do not mean that any scientific experiment ran during this command.

This rebuilds and inspects saved results. It did **not** download sources, estimate demand, match GPS, reroute transit, estimate parameters, run FW/CG, or validate predictions.
