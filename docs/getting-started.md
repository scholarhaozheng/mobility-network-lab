# Installation and execution

## Source installation

Download or clone this repository, then open a terminal in its root. Use Python 3.13 for the tested source configuration.

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/mnl.py catalog
```

macOS or Linux:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/mnl.py catalog
```

The rest of the examples use `python` to mean the interpreter of this environment. The listed package minima are dependency constraints, not a claim that every combination has been tested. The inspected numerical baseline is recorded in `requirements-tested.txt`.

## Run from raw input

```bash
python tools/mnl.py validate --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json
python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode auto --seed-k 1 --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo
```

Open `results/capacity-demo/report.html`. The result JSON and complete path-flow tables are next to it. `validate` checks input schema, attributes and identifiers; it is not a proof of feasibility. `verify` reads existing results without running an optimizer.

## Supply an initial route pool

```bash
python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode supplied --seeds results/capacity-demo/seeds/static_seed_candidates.csv --output results/capacity-supplied
python tools/mnl.py verify --run results/capacity-supplied
```

Do not use `--seed-k` in supplied mode. The allowed network does not shrink to the supplied routes.

## Execution limits

The profile specifies bounds on network size, time horizon, search effort and CG rounds. The source entry point applies a 300-second worker timeout by default (`--timeout` changes that outer budget). The engine also has its own time and iteration controls. A timeout or incomplete computation is not a successful result. This wrapper supervises the Python worker; it is not a general operating-system job scheduler.

## Portable Windows package

The separately distributed `gmns_cg_0.3.0-rc5_win_x64.zip` is the existing Windows runtime artifact. It is not embedded in the Git source tree. When supplied as a release asset, extract it and run:

```bat
gmns.cmd doctor
gmns.cmd run --input "app\cases\capacity_zone_probe\input" --config "app\cases\capacity_zone_probe\case.json" --seed-mode auto --seed-k 1 --output "results\capacity-demo"
gmns.cmd verify --run "results\capacity-demo"
```

The portable distribution and this source tree have different launchers. Do not copy its `runtime/` into the source tree or overwrite a frozen release. Independent Windows receiver testing is recorded separately from Linux source checks. See [release channels](releases.md).
