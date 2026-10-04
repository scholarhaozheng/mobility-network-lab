# Hong Kong recovered computation entry points

The four-stage runner executes the recovered original source without changing its scientific calculations. The static runner delegates to the existing public Frank–Wolfe implementation. Both start from the pinned prepared input tables already in this repository.

Run `python algorithms/hong_kong_reproduction/run_hk_four_stage.py run --repo-root . --output results/hk-four-stage-r2`, followed by the same command with `verify --run results/hk-four-stage-r2`.

For historical Phase B FW, use `python algorithms/hong_kong_reproduction/run_hk_static_fw.py run --repo-root . --tier full --output results/hk-static-b-full-fw`; verification replaces `run --output` with `verify --run`. Tiers are `smoke` (10 ODs), `medium` (1,000 ODs), and `full` (8,930 ODs).

Install the dependencies recorded by the experiment catalog in an isolated environment. No raw GPS, receiver-only seed pools, saved private route states, or private numerical handoffs are included.
