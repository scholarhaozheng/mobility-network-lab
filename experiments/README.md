# Reproduce a documented experiment

This catalog connects the retained experiments to their exact computational source, frozen inputs, configuration and acceptance checks. The reader-facing inventory remains 108 records; a scope record, archived checkpoint or located source does not automatically become an executable recipe.

This release includes the computational source, exact frozen inputs, registered commands and numerical receipts. The historical public baseline is `6ce18b8bea5bf3b9b7caa6ee4c0ff4e701a34a8b`; new files are identified in `publication.json` by SHA-256. New computational entry URLs point to the immutable `reproduction-2026-10-04-r14` tag; the catalog hashes are the exact executable contract. Record `git rev-parse HEAD` when cloning. No private conversations or raw restricted city observations are included.

This revision contains 41 verified commands covering 46 inventory records: 33 city records and 13 public tool/control records. These comprise 37 fresh-computation records and 9 explicitly bounded prepared-input replays. Every command has an actual execution receipt and separate verification. The other 62 inventory records have been traced to retained materials or explicit scope evidence. Their newly integrated commands and inspection results are tracked separately below.

## Download or clone

Download [computational-checkout.zip](../docs/downloads/computational-checkout.zip) and extract it into a new directory. [The manifest](../docs/downloads/computational-checkout.manifest.json) records the ZIP and every source-file hash. Follow [REPRODUCTION_QUICKSTART.md](../REPRODUCTION_QUICKSTART.md). Python packages and native solver binaries are installed separately.

For the complete project, including documentation and figure assets:

~~~powershell
git clone -c core.autocrlf=false https://github.com/scholarhaozheng/mobility-network-lab.git
cd mobility-network-lab
git checkout reproduction-2026-10-04-r14
git rev-parse HEAD
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
.\.venv\Scripts\python.exe -B tools/mcl_reproduction_check.py
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py list
~~~

The integrity command uses only the Python standard library. It checks the original 200 pinned inputs, computational source/runtime files and 41 archived receipt identities, plus every supplemental recovered-file pin, without optimization or network access. Passing it confirms checkout integrity; a fresh run followed by verify is required to reproduce a numerical result. To check one environment use `python -B tools/mcl_reproduction_check.py --experiment EXPERIMENT_ID --environment`.

`reproduction-status.json` accounts for all 108 inventory records, including those without an executable recipe. No entry certifies an end-to-end rebuild from raw observations to every city figure.

## Standard setup

Use Python 3.12 for the tested standard environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
.\.venv\Scripts\python.exe tools/mcl_reproduce.py list
```

The five historical Hong Kong FW instances use a separate tested Python 3.11 environment, because their unchanged source uses pandas:

```powershell
py -3.11 -m venv .venv-hk-fw
.\.venv-hk-fw\Scripts\python.exe -m pip install -r requirements-reproduction-hk-fw.txt
```

On macOS/Linux, create the standard environment with `python3.12 -m venv .venv`, then use `.venv/bin/python`. Actual validation was on Windows; other platforms have not been exercised. Each catalog entry and execution receipt records its actual Python/package versions. Do not combine the requirements files in one environment.

## Command interface

```text
python -B tools/mcl_reproduce.py list
python -B tools/mcl_reproduce.py describe EXPERIMENT_ID
python -B tools/mcl_reproduce.py run EXPERIMENT_ID --output results/EXPERIMENT_ID
python -B tools/mcl_reproduce.py verify EXPERIMENT_ID --run results/EXPERIMENT_ID
```

Use the selected environment interpreter in place of `python`. `run` requires a new or empty output directory, validates pinned source/input hashes, invokes the selected computation and then verifies its new results. `verify` makes no optimizer call: it rechecks input and output identities and recomputes scientific quantities. An old saved PASS marker cannot establish acceptance. Existing result bundles retain their original run-wrapper identity when checked by a newer verifier.

The code, input and output files are referenced by repository-relative paths. Optional `--repo-root` supports a separately located checkout; no fixed drive letter is needed. Some original tools save the prepared-instance location, so preserve the recorded result-directory location when verifying those bundles.

## Algorithm B runtime

Algorithm B uses the original spartalab/tap-b source at commit `040135a20c771fbb84766df6a97cff981fa5df4b`. Build it once, then use the registered Boston, Sioux Falls or Hong Kong entry. On Windows the validated compiler was Zig 0.15.1 available on PATH:

```powershell
.\.venv\Scripts\python.exe tools/reproduction/build_tapb.py --compiler zig --output .mcl-runtime/tap-b
```

The helper downloads the exact upstream source archive, verifies SHA-256 `5163b43051457c5c72cfc53253db4fc3668524cd3a5190169c99d2606fc430a5`, applies the two documented output-precision substitutions and compiles a serial executable. No solver executable or source ZIP is shipped in this repository. An already downloaded archive can be supplied with `--archive PATH`; `--compiler PATH` selects an installed compiler. On POSIX the provided `--compiler cc` recipe is untested. Set `MCL_TAPB_RUNTIME` only when using another build directory. The run adapter checks build provenance and executable identity.

## Source recovery and scientific boundaries

- Boston conditional choice now includes the missing aggregate mode-cost input. A single command recomputes the three ABS scenarios; it does not acquire or rebuild raw observations.
- Hong Kong generation, base IPF and mode choice use the two already public aggregate input tables. Capture and mode sensitivity scope is stated explicitly in the recipe.
- The recovered Hong Kong FW source reports its gap using the historical Beckmann-objective denominator. This convention is retained and should not be confused with a total-system-travel-time-normalized relative gap.
- Historical static instances retain their own city, phase, scale, demand and reference. A new Sioux public FW solve is distinct from the historical 100-iteration result.
- Lagrangian public controls now use the recovered original P07 plan. Controls are not substitutes for the historical city instances.
- Selected historical city inputs and saved states are now included in the recovered recipes. The exact Sioux 200/250-OD arc/demand inputs and four verified recipes are now included as described below. Other recovered city sources and saved-state checks retain their individual status; located code, a checked saved point and a fresh runnable recipe are different outcomes.

Numerical verification includes the relevant OD/path/link balances, nonnegative flows, capacity constraints, objectives, gap or pricing checks and original reference comparisons. Thresholds are fixed per experiment in `catalog.json`; scientific limitations stay visible even when a command passes. Reference-only files do not initialize the solve.

## Files and documentation

`catalog.json` defines the executable commands and hashes. `audit_entries` maps one command to one or several inventory records; shared preprocessing is executed once. `inventory.json` retains all 108 records and the figure-to-experiment mapping. `verification/` contains sanitized receipts from actual runs.

`tools/build_reproduction_docs.py` refreshes English portal metadata without running a solver. It only enables a recipe if the receipt matches the experiment identity, catalog signature, current source/input hashes, verifier identity and passing numerical gates. Supply `--published-revision COMMIT` only when that exact revision is public. Source recovery does not itself publish files.

Run records contain executed argument arrays, dependency versions, input/source/output hashes and elapsed time. Verification records separately identify the original run wrapper and current independent verifier. Exit code 0 means success; 2 means blocked, invalid or not accepted. Nonempty outputs, mismatched inputs and failed scientific checks are rejected.

## Native L3 installation

The Windows native environment has a separate exact Conda lock, hash-pinned PyPI wheel list and identity checker. See [the installation guide](../docs/reproduction/boston-native-environment.md) and `runtime-setup.json`. A new environment was installed from these exact files; all 42 environment checks and a fresh native rank-26/rank-52 run with independent verification passed. Use a short writable Conda package cache on Windows. The clean-install receipt is in `environment-verification/boston-native-clean.json`. The numerical experiment manifest and the installation recipe have separate identities.

## Newly verified exact Sioux instances

This repository includes the exact 200-OD and 250-OD arc/demand pairs and four registered P07 Lagrangian / R2_S ADMM recipes. All four were freshly solved with unchanged public source and policy; the original independent gates, historical objectives and iteration counts passed. No reference flow, reference path pool or saved state initializes these solves. Historical CG has a separate recovered command and inspected evidence; it does not acquire a full pricing-closure certificate through these results.

The prior public snapshot excluded the city inputs. The frozen derived inputs and original policy hashes are included in this release. The immediate GMNS provider revision remains unrecovered; this limits raw-source reconstruction, rather than the exact frozen-input solve. See examples/sioux-falls/finite-time-r05/PROVENANCE.json. The Transportation Networks benchmark reference states academic-research use and source attribution; these data are not relabeled under the code license.

The native L3 describe output records its frozen experimental contract. Follow docs/reproduction/boston-native-environment.md and experiments/runtime-setup.json for the complete validated Conda installation commands, rather than the illustrative executable-path placeholders in that frozen contract.

## Prepared-input commands added in r05

Boston `boston-semantic-fix-s1-assignment` and `boston-semantic-fix-s2-assignment` prepare the public S1/S2 vehicle OD inputs, load their physical endpoints and solve the frozen static assignment using the public Frank–Wolfe implementation. All 5,091 historical link flows match within 2.85e-14. These are assignment-only replays; the original four-stage preparation, service feedback and historical tap_frank_wolfe executable are not rerun.

The seven `public-control-*` commands run fixed synthetic fixtures for static FW, finite paths, supplied-person choice, capacity CG, automatic initialization, catalog matching and synthetic GTFS parsing. They do not reconstruct the city models. The GTFS fixture is a deterministic six-member synthetic ZIP; the historical Victoria feed remains unavailable. Generic CG verification does not establish independent full ungenerated-path pricing closure.

Use their separate tested environment, including pandas for data tools:

```powershell
py -3.11 -m venv .venv-public-controls
.\.venv-public-controls\Scripts\python.exe -m pip install -r requirements-reproduction-public-controls.txt
.\.venv-public-controls\Scripts\python.exe -B tools/mcl_reproduction_check.py --experiment public-control-gtfs-parser --environment
.\.venv-public-controls\Scripts\python.exe -B tools/mcl_reproduce.py run public-control-gtfs-parser --output results/public-control-gtfs-parser
.\.venv-public-controls\Scripts\python.exe -B tools/mcl_reproduce.py verify public-control-gtfs-parser --run results/public-control-gtfs-parser
```

The recipe freezes numpy 1.24.3, scipy 1.10.1 and pandas 1.5.3, and was exercised with Python 3.11.4. Existing validated environments were used; r05 does not claim a new clean environment installation.

## Recovered city workflows

`recovered/*.json` adds portable source, input/configuration hashes, provider acquisition information and per-record commands. Use `python -B tools/mcl_recovered.py list` and `describe RECORD_ID` to select an exact workflow. The existing `mcl_reproduce.py` catalog and its 41 archived receipts retain their original scientific meaning.

- `check` checks packaged-file identity without computation or network access.
- `inspect` verifies retained evidence. Its success is not a fresh-solver claim, and an expected historical failure remains a failure.
- `run` executes the selected computation. Use its documented environment and a new output directory.
- `verify` checks that result using the selected adapter. The recipe states whether this is structural validation, independent numerical verification, or both.

```text
python -B tools/mcl_recovered.py describe RECORD_ID
python -B tools/mcl_recovered.py inspect RECORD_ID --output ../results/RECORD_ID-inspect
python -B tools/mcl_recovered.py run RECORD_ID --output ../results/RECORD_ID-run
python -B tools/mcl_recovered.py verify RECORD_ID --run ../results/RECORD_ID-run
```

Actions are enabled per record. An external-data workflow requires the documented exact input snapshot; follow `dataSources` and use `--input-root`. Expensive historical CG/native cases may have inspected saved states and a runnable command without a new full solve in this release. Original scientific gates and missing historical version identities remain visible. No private conversations or original restricted observations are included.

Instructions: [Boston](../docs/reproduction/recovered-boston.md) · [Sioux Falls](../docs/reproduction/recovered-sioux.md) · [Hong Kong](../docs/reproduction/recovered-hong-kong.md) · [City query](../docs/reproduction/recovered-shared.md). The [complete status ledger](reproduction-status.json) distinguishes these recovered workflows from fresh numerical reproduction.
