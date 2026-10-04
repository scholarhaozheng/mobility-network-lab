# Recovered Sioux Falls computations

These eleven supplemental records now have data, configuration, a callable computation route, and a separate saved-evidence inspection route. Seven computations were run again for this delivery; four were checked from saved evidence. The latter checks do not invoke an optimizer.

Use the [machine-readable registry](../../experiments/recovered/sioux-shared.json) for exact file hashes, inputs, environments, commands, and limits. Existing inputs and implementations are reused. See the [finite-time provenance](../../examples/sioux-falls/finite-time-r05/PROVENANCE.json), [data licenses](../../DATA_LICENSES.md), and [third-party notices](../../THIRD_PARTY_NOTICES.md).

## Commands

Run commands from the repository root. Every run or inspection needs a new, empty output directory outside the repository.

~~~sh
python -B tools/mcl_recovered.py list
python -B tools/mcl_recovered.py describe sioux-admm-r2s-development-30
python -B tools/mcl_recovered.py check sioux-admm-r2s-development-30
python -B tools/mcl_recovered.py run sioux-admm-r2s-development-30 --output ../results/sioux-r2s-30
python -B tools/mcl_recovered.py verify sioux-admm-r2s-development-30 --run ../results/sioux-r2s-30
python -B tools/mcl_recovered.py inspect sioux-admm-r2s-development-30 --output ../results/sioux-r2s-30-inspection
~~~

- <code>run</code> executes the computation, then verifies its numerical result.
- <code>inspect</code> checks the original saved state or aggregate audit tables without solving again.
- <code>verify</code> checks an existing run directory without invoking an optimizer.

The output contains execution metadata and <code>verification.json</code>. The evidence basis distinguishes fresh computation from saved-state inspection. Input and source hashes are checked before execution. The optimizer-call count in the verification receipt refers to verification; ADMM metrics separately report solver optimizer calls.

## Coverage in this delivery

| Record | Method / case | Evidence completed |
|---|---|---|
| sioux-taplab-official-parity | Official TAPLab Algorithm B adapter | Fresh run and saved inspection |
| sioux-native-a-reg001-rank50 | Native L3 A_REG001, outer 04 | Saved-state inspection |
| sioux-native-b-beckmann-rank50 | Native L3 B_BECKMANN, outer 04 | Saved-state inspection |
| sioux-cg-200 | Historical finite-time CG, 200 ODs | Saved aggregate audit; execution preflight |
| sioux-cg-250 | Historical finite-time CG, 250 ODs | Saved aggregate audit; execution preflight |
| sioux-admm-r1-200 | ADMM R1, 200 ODs | Fresh run and saved inspection |
| sioux-admm-r1-250 | ADMM R1, 250 ODs | Fresh run and saved inspection |
| sioux-admm-r2s-development-30 | ADMM R2_S development, 30 ODs | Fresh run and saved inspection |
| sioux-admm-r2s-development-60 | ADMM R2_S development, 60 ODs | Fresh run and saved inspection |
| sioux-admm-r2s-development-100 | ADMM R2_S development, 100 ODs | Fresh run and saved inspection |
| sioux-admm-r2s-development-150 | ADMM R2_S development, 150 ODs | Fresh run and saved inspection |

Use the exact record identifiers returned by <code>list</code>; the registry is authoritative.

## ADMM

All six fresh ADMM computations used Python 3.12.14, NumPy 2.5.3 and SciPy 1.18.1 in an existing installed environment. This delivery did not certify a new environment installation. The repository's tested requirements provide the numerical environment:

~~~sh
python -m venv .venv-recovered
.venv-recovered\Scripts\python -m pip install -r requirements-tested.txt
.venv-recovered\Scripts\python -B tools/mcl_recovered.py run sioux-admm-r1-200 --output ../results/sioux-r1-200
~~~

On Unix, use <code>.venv-recovered/bin/python</code>. R1 reuses the published 200/250-OD inputs and original gates; the previous local-only input limitation is resolved for these records. R2_S development records retain their own 30/60/100/150-OD inputs and must not be confused with the separate 200/250-OD experiments. The adapters invoke the published solvers and independent evaluators without changing their scientific implementation.

R1 fresh runs took 74 and 94 iterations. Their objective differences from the saved results were about 3.4e-7 and 3.7e-9, within the recorded tolerance; all original feasibility gates passed. Each smaller R2_S development run completed in one iteration and reproduced its saved objective in the tested environment.

## Native L3 A and B

Saved inspection reconstructs the isolated native case, loads the accepted outer-04 state and runs the original checker. It needs NumPy, SciPy and pandas, but does not need IPOPT. Inspection was tested with Python 3.11.4, NumPy 1.24.3, SciPy 1.10.1 and pandas 1.5.3.

A fresh native run requires the existing published native toolchain plus [pandas 2.2.3](../../algorithms/recovered_sioux/native-additions.txt). The [historical environment record](../../examples/sioux-falls/recovered-r14/native/environment.json) pins Python 3.9.25, NumPy 2.0.2, SciPy 1.13.1, pandas 2.2.3, Pyomo 6.9.5 and IPOPT 3.14.19/MUMPS 5.8.1, including the solver hash. Set <code>MCL_NATIVE_PYTHON</code> and <code>MCL_IPOPT</code> (or pass <code>--ipopt</code> for the solver path) to that environment's interpreter and solver executable. The runtime uses the original Windows controller and its A-before-B sequence, so a fresh request runs that sequence rather than fabricating an isolated B initialization.

No fresh native optimization or new installation of the extended native environment was performed in this delivery. The saved-state criteria passed, but nonzero full-network gaps remain: about 0.08167 for A and 0.04382 for B. These records do not certify full-network user equilibrium.

## Historical finite-time CG

The exact initial generated-column tables were recovered for both 200 and 250 ODs. They are included with the corresponding nodes and frozen manifests; arc and demand tables reuse existing public files. The run route invokes the original published legacy CG driver with the recorded phase limits, candidate limits, costs, and scalar LP reference. It does not load the saved optimal flow as an initialization.

The original driver completed input/configuration preflight for both cases. Its only stop reason was the explicit preflight-only option. A complete fresh CG solve was not run in this delivery; historical times were approximately 24 and 44 minutes. The saved inspections recompute objective and capacity checks from aggregate arc audits and check demand-audit identities. They do not establish independent complete pricing closure, full per-commodity reconstruction, or exact equality of degenerate arc patterns. Later DAG-based driver revisions are separate experiments.

~~~sh
python -B tools/mcl_recovered.py inspect sioux-cg-200 --output ../results/sioux-cg-200-inspection
python -B tools/mcl_recovered.py run sioux-cg-200 --output ../results/sioux-cg-200
~~~

## Official TAPLab route

The official adapter route is kept separate from the direct Algorithm B adapter. It acquires official TAPLab commit <code>081e44a0dd451c549d6903933516bccb4166bbd0</code> and checks the archive and adapter hashes in [acquisition.json](../../examples/sioux-falls/recovered-r14/taplab/acquisition.json). The computation needs PyYAML and the existing source-built tap-b runtime at commit <code>040135a20c771fbb84766df6a97cff981fa5df4b</code>.

~~~sh
python -B tools/reproduction/build_tapb.py --compiler cc --output .mcl-runtime/tap-b
python -B tools/mcl_recovered.py run sioux-taplab-official-parity --output ../results/sioux-official-taplab
~~~

Use the compiler supported by the existing build recipe on your platform. Set <code>MCL_TAPB_RUNTIME</code> if the build directory is elsewhere. An already downloaded, hash-matching source archive can be supplied with <code>MCL_TAPLAB_ARCHIVE</code>. No solver executable is distributed in these fixtures.

The fresh official adapter invocation in this delivery used a previously verified source-built binary; it did not compile that binary again. All 76 physical-link flows matched the direct adapter exactly. The independently computed relative gap was approximately 4.50e-9.

## Remaining historical boundary

The historical 100-iteration Frank–Wolfe result still lacks a sufficiently bound original demand/runtime identity. It is not replaced by a newly run case with a different iteration count. Sioux Falls population, modern observations and mode-choice stages that were never run remain out of scope rather than being represented as missing executable results.
