# Reproduction guide · 20261004-r18.1

**Start here:** [Reproduction guide](https://scholarhaozheng.github.io/mobility-network-lab/reproduction.html) · [Experiment catalog](https://scholarhaozheng.github.io/mobility-network-lab/reproduce.html) · [Static experiment catalog](https://scholarhaozheng.github.io/mobility-network-lab/reproduction/experiment-catalog.html).

This checkout contains registered computational source, packaged frozen inputs, configuration and verification receipts. Python packages and compiled solver binaries are installed separately. The documentation release is **r18**; computational recipe and source links remain pinned to [`reproduction-2026-10-04-r14`](https://github.com/scholarhaozheng/mobility-network-lab/tree/reproduction-2026-10-04-r14). A documentation update does not mean that every computation was rerun.

## 1. Download and extract

Download [computational-checkout.zip](https://scholarhaozheng.github.io/mobility-network-lab/downloads/computational-checkout.zip) and extract it into a new directory. The [download manifest](https://scholarhaozheng.github.io/mobility-network-lab/downloads/downloads.json) gives its SHA-256; the [file manifest](https://scholarhaozheng.github.io/mobility-network-lab/downloads/computational-checkout.manifest.json) identifies its contents. No ZIP merging or Git installation is required.

Windows PowerShell, from the directory containing the ZIP:

```powershell
if (Test-Path -LiteralPath .\mobility-reproduction) { throw 'Choose a new empty destination.' }
Expand-Archive -LiteralPath .\computational-checkout.zip -DestinationPath .\mobility-reproduction
Set-Location .\mobility-reproduction
```

## 2. Choose the exact experiment

In the [Experiment catalog](https://scholarhaozheng.github.io/mobility-network-lab/reproduce.html), select the city, method, scale and version. Keep that record open: it brings together the input links, environment setup, run command, verification, expected outputs and receipts. The catalog selects the registered command interface for you; there is no need to decide which historical catalog owns the experiment.

Use [Show verified run commands only](https://scholarhaozheng.github.io/mobility-network-lab/reproduce.html?ready=1) to begin with a recorded run and passing verification. Each record distinguishes a verified run from an available but unverified run, an external-input requirement, or historical inspection only. A structural check, a prepared-input replay and a full optimizer run retain their own scientific scope. Some verified partial workflows still need external inputs to reconstruct an upstream preparation stage.

If the interactive catalog fails or JavaScript is disabled, use the [static experiment catalog](https://scholarhaozheng.github.io/mobility-network-lab/reproduction/experiment-catalog.html).

## 3. Install the selected environment and check inputs

Copy the selected record’s environment commands into a terminal at the checkout root. Use that record’s Python version, requirements file and native build instructions; do not combine requirements files across recipes. Acquire any explicitly required external input and check its recorded hash. A current provider download may differ from the historical snapshot.

After Python is available, check the packaged files:

```powershell
py -3 -B tools/mcl_reproduction_check.py
```

This standard-library integrity check makes no optimizer or network call. It checks registered file hashes and archived receipts; it does not run a new computation. For the next steps, use the interpreter from the selected experiment’s environment.

The standard recipes use Python 3.12. Historical Hong Kong FW, public prepared-input controls and several integrated workflows use their separately specified Python 3.11 environments. Algorithm B requires a pinned tap-b build. Native Boston L3 has a separate exact environment lock; see [its installation guide](docs/reproduction/boston-native-environment.md) and [runtime setup](experiments/runtime-setup.json). The catalog tells you which setup applies.

## 4. Run, then verify the expected result

Copy the record’s run command, using a new or empty output directory. Then copy its verification command against that same result directory. Require successful exit codes and every required verification check to pass. Compare the objective, balances, capacities, gap or structural checks with that record’s fixed tolerances and expected outputs. A reproducible numerical result need not be a byte-for-byte identical floating-point file.

Retain the new run and verification receipts with your outputs. An archived PASS receipt establishes what was checked previously; it does not verify your new run. `inspect` checks retained historical evidence and must not substitute for `run`. A failed historical acceptance gate remains a failure even when its evidence inspection passes.

### Optional first run: a small public ADMM control

This authored control is a quick check of the workflow, not a Boston, Sioux Falls or Hong Kong city experiment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
.\.venv\Scripts\python.exe -B tools/mcl_reproduction_check.py --experiment admm-r2s-public-C1 --environment
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py run admm-r2s-public-C1 --output results/admm-r2s-public-C1
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py verify admm-r2s-public-C1 --run results/admm-r2s-public-C1
```

Both commands must exit 0 and `verification.json` must report PASS with every required numerical check passing. Use the exact catalog instructions when moving to a city experiment.

## Coverage and boundaries

Downloading published frozen data and recomputing a documented result is a valid reproduction path. The inventory contains 108 records, including historical attempts and scope-only entries. Use each record’s resolved status and linked receipt, rather than adding counts from different batches.

- The original 41 verified commands map to 46 records: 37 fresh-computation records and 9 bounded prepared-input replays. In the earlier r12 delivery, 18 commands were executed in four scoped batches with independent checks; the other 23 retain earlier actual run provenance. Existing environments were used. See [the execution summary](docs/reproduction/execution-evidence-summary.json).
- The supplemental catalog contains 44 entries, including 35 run actions and 44 inspection actions. The r14 delivery executed and independently checked 21 distinct workflows, including prepared-input arithmetic, structural validation and optimization. Command availability does not mean every workflow was freshly run. See [the supplemental validation record](docs/reproduction/recovered-validation.json).
- Exact Sioux P07 Lagrangian and R2_S ADMM have freshly verified 200-OD and 250-OD instances. The historical Sioux CG pricing-closure limitation is unchanged. Boston S1/S2 semantic recipes rerun assignment only.
- The immediate GMNS provider revision for the Sioux conversion snapshot remains unrecovered. Frozen derived inputs retain upstream academic-research restrictions and attribution; see [PROVENANCE.json](examples/sioux-falls/finite-time-r05/PROVENANCE.json) and [DATA_LICENSES.md](DATA_LICENSES.md). Code licensing does not relicense upstream data.
- Larger native-L3 and CG workflows may have run commands plus historical result checks without a fresh complete solve in the current delivery. External source preparation and remaining historical identities are stated per record. No full raw-source-to-final-city pipeline is certified.

Actual numerical validation was on Windows. A limited native Boston L3 clean-environment installation was validated; most other runs used existing validated environments. A clean installation for every recipe and complete macOS/Linux validation remain unclaimed. On macOS/Linux, the usual standard-environment forms are `python3.12 -m venv .venv` and `.venv/bin/python`; native L3 is Windows-specific.

## Advanced reference

The established command adapters remain available for scripts and historical receipts: `tools/mcl_reproduce.py` for the original registered recipes and `tools/mcl_recovered.py` for supplemental workflows. Prefer the exact command block in the selected catalog record. No new unified solver command is introduced in this documentation release.

See [experiments/README.md](experiments/README.md) for the complete interface. Supplemental instructions: [Boston](docs/reproduction/recovered-boston.md), [Sioux Falls](docs/reproduction/recovered-sioux.md), [Hong Kong](docs/reproduction/recovered-hong-kong.md), and [city query](docs/reproduction/recovered-shared.md). `experiments/reproduction-status.json` records resolved status; recipe manifests and receipts retain exact source/input identities.

For the full website and project, clone `https://github.com/scholarhaozheng/mobility-network-lab.git`, check out `reproduction-2026-10-04-r18.1`, and record `git rev-parse HEAD`. The compact computation checkout intentionally omits most website assets. Numerical recipes retain their r14 immutable source links and hashes.
