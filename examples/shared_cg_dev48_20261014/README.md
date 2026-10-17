# Dev48: minimal executable reproduction

This directory contains the algorithm implementation, required graph/seed/pool
construction and independent verification code, 16 numerical configurations,
and the smallest frozen model inputs needed by these cases. All path pools,
time-expanded networks for Berkeley/Chicago, FIFO states, RMP matrices, flows
and certificates are generated into a new directory on the reader's machine.
No final solution or saved intermediate state is supplied to initialize a run.

The website's selected Dev48 results retain their actual identities: 13 cases
meet their branch-specific acceptance contract; Urbana F Q, Urbana S2 Q and
Pittsburgh S2 Q remain OPEN. The common package has explicit path-CG, implicit
path-CG, exact nonbinding uniform-release and joint delta-CG branches. The
three exact constructions have zero CG iterations. An accepted case does not
automatically pass the separate raw reduced-cost stopping test.

## Connect to the existing four-stage and GPS workflow

The original acquisition, population/activity, trip generation, distribution,
mode choice, assignment and GPS programs remain in their original locations.
Start with the repository [reproduction quickstart](../../REPRODUCTION_QUICKSTART.md)
and [experiment catalog](../../experiments/README.md). This CG entry extends
that workflow at its **frozen parent model/assignment-demand boundary**; it
does not replace those earlier stages or require rerunning them for every CG
method comparison.

Examples from the existing catalog, run from the repository root:

```sh
python -B tools/mcl_reproduce.py run hk-four-stage-r2 --output ../runs/hk-four-stage-r2
python -B tools/mcl_recovered.py run boston-acs-population-allocation-r1 --output ../runs/boston-population
python -B tools/mcl_recovered.py run boston-finite-construction --output ../runs/boston-graph
python -B tools/mcl_recovered.py describe HK-URBANNAV-ASSOCIATION
```

The catalog entries are versioned boundaries, not an automatic pipeline that
feeds every new output into the next command. Hong Kong's four-stage record
starts from published activity and OD mode-cost tables; static assignment has
its own records. Boston population, regional generation and semantic mode
choice have separate records. Use the documented inputs and parameters rather
than combining unrelated snapshots.

For raw acquisition and processing, follow
[Boston's reproduction guide](../../docs/reproduction/recovered-boston.md)
and [Hong Kong's reproduction guide](../../docs/reproduction/recovered-hong-kong.md).
Boston's existing `city_database.py` exposes `fetch-mbta-gps` and `process-gps`
with the documented external source workspace/configuration. Its GPS network
association catalog record is inspection/verification-only. Hong Kong's
UrbanNav record identifies the exact externally obtained snapshot. No raw
personal GPS, original GTFS feed or substitute timetable library is included
here. Fetching current public data does not guarantee the same historical bytes.

For current CG reproduction, use the minimum inputs already in this repository.
To supply an equivalent upstream-generated model, pass `--input-dir PATH` with
the required CSV names. Its SHA must match `cases.json`; a changed demand,
network, sampling period or capacity defines a **new experiment**, not the
displayed frozen case. The Sioux provider's original conversion revision is
unrecovered; its two exact, previously published modeled inputs are the declared
reproduction boundary, as documented in [DATA_LICENSES.md](../../DATA_LICENSES.md).

## Install and prepare

Use Python 3.11. The recorded numerical environment is Python 3.11.4,
NumPy 1.24.3, SciPy 1.10.1, Numba 0.57.0 and psutil 5.9.0.
The following commands run from the **full repository checkout**:

```sh
python -m pip install -r examples/shared_cg_dev48_20261014/requirements.txt
python -B examples/shared_cg_dev48_20261014/run.py --list
python -B examples/shared_cg_dev48_20261014/run.py --case boston_10_H --output ../runs/dev48-boston
```

Without `--execute`, the command checks packaged file hashes, resolves inputs
and writes a derived configuration plus `PREPARATION.json`. It starts no
optimizer. Use a fresh output directory outside the repository. Preparing a
workspace and then executing that same case there is supported.

For Berkeley and Chicago, prepare the exact dynamic graph separately if desired:

```sh
python -B examples/shared_cg_dev48_20261014/run.py --case chicago_T4_H --output ../runs/dev48-chicago --prepare-graphs
```

This invokes the original input-only graph builder and checks the resulting
ordered arc/demand SHA. Chicago's 214 MB expanded arc CSV is produced locally
from its approximately 2.4 MB physical network; Berkeley's 19.5 MB expanded
arc CSV is produced from approximately 245 KB of physical-network input.
Neither large CSV is stored again in the repository.

## Run one complete CG case

`--execute` is an explicit request for a **new computation**, including the
necessary constructors, solver and independent verifier:

```sh
python -B examples/shared_cg_dev48_20261014/run.py --case boston_10_H --output ../runs/dev48-boston --execute
python -B examples/shared_cg_dev48_20261014/run.py --case urbana_S2_H --output ../runs/dev48-urbana-s2-h --execute
python -B examples/shared_cg_dev48_20261014/run.py --case urbana_F_Q --output ../runs/dev48-urbana-f-q --execute
```

Choose any ID in the table below. Run one case at a time. The large joint
problems can require several GB of RAM and significant time; original RMP
time limits, iteration budgets and initial source-column policies are retained
in `configs/` and `policies/`. A resource/round limit remains an OPEN result.
The preparation command does not acquire a research-server lock or contact a
different machine.

The reader's new workspace contains `work/solver/` for retained branches or
`work/joint/` for joint branches, generated initial data under `work/runs/`,
and a top-level `NEW_RUN.json`. Original values in `cases.json` are comparison
targets, never loaded as a warm solution. Independently inspect the new
certificate; original website certificates do not certify a fresh run.
`WORKSPACE_INDEX.json` identifies the actual generated config, pool, flow and
certificate paths for plotting. `PREPARATION.json` hashes the preparation
configuration; `NEW_RUN.json` separately hashes the final execution configuration
and new certificates after generated seed hashes and output paths are bound.
An independent verification failure stops with a nonzero exit status. A retained
branch that does not reach its selected acceptance condition returns status 2;
the three joint recipes can reproduce a valid, independently checked OPEN
diagnostic without claiming optimality.
Floating-point solver/version/platform differences can change ties, paths,
iteration histories and final bytes. Compare the declared feasibility/gap
conditions and scientific quantities, not an identical PNG or runtime.

| Case ID | Parent demand / OD | Time domain | Factor | Actual computation |
|---|---|---|---:|---|
| `sioux_200_H` | Existing selected 200 benchmark OD | Native frozen arc-time domain | 1 | Explicit path-CG |
| `sioux_250_H` | Existing selected 250 benchmark OD | Native frozen arc-time domain | 1 | Explicit path-CG |
| `boston_10_H` | Existing Boston selected 10 OD | Frozen 3-second dynamic graph | 1 | Explicit path-CG |
| `hong_kong_10_H` | Existing Hong Kong selected 10 OD | Frozen 30-second dynamic graph | 1 | Explicit path-CG |
| `berkeley_T4_H` | R2 stage-3 selected 4 OD, hourly PCE / 12 | 30 s, H165; first five-minute pulse, release step 5 | 1 | Build graph → explicit path-CG |
| `chicago_T4_H` | Jane Byrne / West Loop R2 stage-3 selected 4 OD, hourly PCE / 12 | 30 s, H169; first five-minute pulse, release step 5 | 1 | Build graph → explicit path-CG |
| `urbana_F_H` | Frozen representative 418 positive OD | 30 s, 120 releases, H480 | 1 | Implicit path-CG |
| `urbana_S2_H` | Same 418 positive OD | 30 s, 120 releases, H480 | 2 | Generate selective FIFO → implicit path-CG |
| `pittsburgh_F_H` | East End representative 1,406 positive OD | 30 s, 120 releases, corrected H320 | 1 | Implicit path-CG |
| `pittsburgh_S2_H` | Same 1,406 positive OD | 30 s, 120 releases, corrected H320 | 2 | Generate selective FIFO → CG → stage-57/60 mixed certificate |
| `ann_arbor_F_Q` | ChoiceFW V002, 600 positive vehicle OD | 0.5 s, 7,200 releases, H28800 | 1 | Exact uniform-release construction |
| `ithaca_F_Q` | Representative 110 positive OD | 0.25 s, 14,400 releases, H23423 | 1 | Exact uniform-release construction |
| `pittsburgh_F_Q` | Same East End 1,406 positive OD | 0.25 s, 14,400 releases, H38400 | 1 | Exact uniform-release construction |
| `urbana_F_Q` | Same representative 418 positive OD | 0.25 s, 14,400 releases, H57600 | 1 | Generate FIFO → ranked source pool → joint CG; OPEN |
| `urbana_S2_Q` | Same 418 positive OD | 0.25 s, 14,400 releases, H57600 | 2 | Generate FIFO → V5 source pool → joint CG; OPEN |
| `pittsburgh_S2_Q` | Same East End 1,406 positive OD | 0.25 s, 14,400 releases, H38400 | 2 | Generate FIFO → V6 pool → V7 prefix → joint CG; OPEN |

H and Q share a parent static demand only where stated; their time domains
are different mathematical instances. Factor 2 is an engineering stress
scenario, not an observed policy effect. The implicit/uniform cases distribute
the frozen hourly amount over the declared one-hour release window. Explicit
cases preserve their saved demand volumes; no additional upstream multiplier
is inferred. All amounts are modeled demand, not individual traveler records.

Pittsburgh S2 H's accepted displayed certificate combines its own round-60
primal with independently repriced round-57/60 duals over the fixed alpha grid
`0, 0.25, 0.5, 0.75, 1`. The new runner generates and checks those checkpoints;
it never downloads old checkpoints. If a new run has different stages, it
cannot inherit the old mixed certificate.

The two Urbana joint cases include their selected branch's separate full-graph
pricing and independent Bellman audit after the joint primal verification.
Pittsburgh S2 Q's displayed run lacks a verified same-run full-graph lower
bound. Its recipe reproduces that limited scope and does not fabricate an
additional pricing certificate.

## What is retained and what is generated

- `shared_cg/`: 18 actual algorithm/construction modules plus `__init__.py`;
  numerical source bytes match the original Dev48 package.
- `frozen_sources/`: only the original builders and independent verifiers
  used by these recipes. Legacy batch wrappers are loaded by `run.py` with
  explicit new paths; the three H-seed scripts' top-level all-case loops are
  suppressed while their exact function bodies run for the requested case.
- `configs/`, `policies/`: frozen numerical settings. New run-specific SHA
  bindings are written under the output directory; old receipts are not
  edited or falsely reused. The source-ranked Urbana constructor stops after
  its validated input stage, before its unrelated historical restricted RMP.
- `inputs/`: six groups of minimum parent model/graph-construction inputs,
  about 16.16 MB total. Existing Hong Kong, Boston and Sioux inputs are reused
  by their current repository paths and checked byte-for-byte.
- `cases.json`, `provenance/`, `EXECUTABLE_MANIFEST.json`: model identities,
  original source hashes, current executable-subset hashes and comparison
  targets. `ORIGINAL_SOURCE_IDENTITY.json` records the old full 33-module
  package; it is not a claim that all those development modules are shipped.

The 35 evidence archives, mixed code/figure ZIP, saved path pools, RMP states,
full pricing arrays and repeated final-result archives are not dependencies
of this entry. Current displayed figures and their Plot data remain on the
website. Data attribution and reuse terms are in [NOTICE.txt](NOTICE.txt).

## Validation of this packaging change

This maintenance change performs file/source/parameter checks, Python syntax
and import checks, preparation checks, and exact Berkeley/Chicago graph
reconstruction. It does **not** rerun the 16 optimizations, FIFO constructions,
joint initial pools, full pricing or numerical certificates. Their existing
scientific results remain the historical selected results. The new executable
chain is provided for readers; no clean-room full rerun is claimed here.

## Plot a newly computed result

After a new run completes and its independent certificate is written, export
that run's actual values and physical-link flow, then render the selected V1
three-card layout. Run these commands from the repository root:

```sh
python -m pip install matplotlib==3.7.1 Pillow==9.4.0 fonttools==4.25.0
python tools/visuals/export_cg_run_plot_data.py --run /path/to/new-run --output /path/to/new-plot-inputs
python tools/visuals/render_cg_v1_20261017.py --input-root /path/to/new-plot-inputs --output-root /path/to/new-figures
```

The exporter uses `WORKSPACE_INDEX.json` and the completion record
`NEW_RUN.json`. Its `new_outputs` entries bind every existing indexed file to
its actual SHA, including solved pools/RMPs, uniform paths, joint initial and
final states, and the Pittsburgh checkpoint files. It reconstructs flow from
those new path/flow outputs; only map geometry is reused. A missing same-run
lower bound or history remains missing and is never filled with an old result.
Use a separate empty plot-output directory; these commands do not replace the
published website or certify a new run by its historical comparison values.
