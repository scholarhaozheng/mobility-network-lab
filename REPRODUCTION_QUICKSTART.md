# Reproduction checkout · 20261004-r12

This is a computational checkout of Mobility Computation Lab. It contains the pinned public baseline plus reviewed code, frozen inputs and numerical receipts. It is included in the public repository release. It does not include a Python environment or compiled solver binaries.

## First run (Windows PowerShell)

Extract computational-checkout.zip to a NEW directory, open a terminal in that directory, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
.\.venv\Scripts\python.exe -B tools/mcl_reproduction_check.py
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py list
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py describe admm-r2s-public-C1
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py run admm-r2s-public-C1 --output results/admm-r2s-public-C1
.\.venv\Scripts\python.exe -B tools/mcl_reproduce.py verify admm-r2s-public-C1 --run results/admm-r2s-public-C1
```

The example is a small authored control, not a city reproduction. Use an exact ID from list to select another recipe. Both run and verify must exit 0; verification.json must say PASS with all checks passing. Results directories must be new or empty. The integrity command does not run an optimizer and does not prove a fresh reproduction.

## Exact city examples

The newly included Sioux city IDs are sioux-lagrangian-p07-200, sioux-lagrangian-p07-250, sioux-admm-r2s-200 and sioux-admm-r2s-250. They use the standard environment above. Replace the example ID and its result directory with the selected ID. The four original independent numerical gates, historical objective comparisons and iteration counts have passed actual fresh runs.

## Environments and scope

See experiments/README.md for the complete command interface and additional installation requirements. The five legacy Hong Kong FW instances require a separate Python 3.11/pandas environment. Algorithm B requires a pinned tap-b source build. Native Boston L3 uses docs/reproduction/boston-native-environment.md and experiments/runtime-setup.json. Do not combine the environment requirements files.

41 verified recipes map to 46 of the 108 inventory records. See experiments/reproduction-status.json for all records and outstanding requirements. Computations begin from exact frozen inputs; raw-source-to-final-city reconstruction is not certified. The original Sioux CG pricing-closure limitation remains.

The exact Sioux converted input snapshot is published as a frozen derived benchmark fixture. The immediate provider revision remains unrecovered; the upstream academic-research use restriction and attribution are retained. See examples/sioux-falls/finite-time-r05/PROVENANCE.json and DATA_LICENSES.md. Code licensing does not relicense upstream data.

On macOS/Linux use python3.12 -m venv .venv and .venv/bin/python. Those command forms are provided, but validation was on Windows; native L3 is Windows-specific.

For the full website/project, clone https://github.com/scholarhaozheng/mobility-network-lab.git and record git rev-parse HEAD. This compact checkout intentionally omits most website assets. experiments/publication.json provides public source/data URLs plus immutable file hashes; the `reproduction-2026-10-04-r12` release tag fixes the repository snapshot.

The 46 enabled records comprise 37 fresh-computation records and 9 prepared-input replays with limited scope. The two Boston semantic S1/S2 recipes rerun assignment only. Seven public synthetic controls use Python 3.11 and `requirements-reproduction-public-controls.txt` in `.venv-public-controls`; see experiments/README.md for exact commands. Do not use the standard Python 3.12 environment for those pinned controls.

Execution evidence for this delivery is summarized in `docs/reproduction/execution-evidence-summary.json`: 18 distinct commands were run in four scoped batches, followed by independent verification. Existing environments were used. The final combined archive checks all 41 receipt identities and all 200 pinned files; it does not rerun every solver. Detailed portable run/verification receipts are in `experiments/verification/`. Batch reports may name local audit logs outside this compact package.
