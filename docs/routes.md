# Route initialization

Two initialization modes feed the same finite-network optimizer.

## Automatic routes

Use `--seed-mode auto --seed-k K`. The standard-library generator enumerates a bounded number of simple physical paths in deterministic travel-time/link-ID order. It preserves directed parallel links and rejects routes outside the fixed time horizon. If fewer than K paths exist, it records the actual number rather than duplicating routes.

`seeds/static_seed_candidates.csv` stores physical link sequences. The time-expansion stage produces `dynamic_inputs/dynamic_columns.csv`, the initial RMP pool. Neither file is the final column pool.

## Supplied routes

Use `--seed-mode supplied --seeds path/to/seeds.csv`. At minimum the input identifies `column_id`, `demand_id` and `link_sequence`. Paths must refer to this instance's allowed links and satisfy its endpoints and time horizon. The generator output is accepted as a supplied-route file.

## Optimization columns

After initialization, pricing may add columns. Complete final path definitions are in `full_cg_v1_phase_ii_final_pool.csv`. Their final flows, including zero flows, are in `full_cg_v1_phase_ii_final_solution_by_column.csv`. Always match these files to the last successfully solved pool and its signatures.
