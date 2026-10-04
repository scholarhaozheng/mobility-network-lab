# Hong Kong: recovered computations and exact data access

This supplement connects the 20 previously unenabled records to computation source, exact input identities, commands and evidence. Fifteen records have located computation or independent-validation routes. The two historical failures and three preparation-only / not-run scope records remain separate.

**Seven recipes were freshly executed and verified for this release:** R2 turn-aware compilation, building activity, ATC/detector association, UrbanNav projection/association, H1 Frank–Wolfe, H1 finite-path SLSQP, and the finite time-expanded graph. **Native L3, CG and HK4 ADMM were checked against existing saved numerical states; they were not freshly solved in this release.**

All commands below run from the repository root. Output directories must be outside the checkout; acquired external data and per-point outputs therefore cannot accidentally enter this repository.

```sh
python -m pip install -r requirements.txt
python tools/mcl_recovered.py list
python tools/mcl_recovered.py describe HK-H1-FINITE
python tools/reproduction/recovered_hk.py run --repo-root . --record HK-H1-FINITE --output ../runs/hk-h1-finite
python tools/reproduction/recovered_hk.py verify --repo-root . --record HK-H1-FINITE --run ../runs/hk-h1-finite
```

The frozen H1 solver source and prepared 26-OD / 126-path fixture are included. The fresh finite-path test used Python 3.11.4, NumPy 1.24.3 and SciPy 1.10.1. General saved checks used Python 3.12.14 and NumPy 2.5.3. Native L3 requires the [pinned Windows native environment](../../environments/boston-native-win-64.lock) with Pyomo and IPOPT/MUMPS; activate that environment, or pass `--ipopt /path/to/ipopt`. No solver executable is redistributed.

## Commands and current evidence

| Record | Action | Data readiness | Evidence obtained in this release |
|---|---|---|---|
| `HK-GMNS-R1` | `run`, `verify`, `inspect` | requires external input | saved output integrity only |
| `HK-GMNS-R2-ACCESS` | `run`, `verify`, `inspect` | requires external input | fresh computation independently checked |
| `HK-POPULATION-2021` | `run`, `verify`, `inspect` | requires external input | saved output integrity only |
| `HK-BUILDING-ACTIVITY` | `run`, `verify`, `inspect` | requires external input | fresh computation independently checked |
| `HK-GTFS-WALK-R2` | `run`, `verify`, `inspect` | requires external input | saved output integrity only |
| `HK-OBSERVATIONS-ASSOCIATION` | `run`, `verify`, `inspect` | requires external input | fresh computation independently checked |
| `HK-URBANNAV-ASSOCIATION` | `run`, `verify`, `inspect` | requires external input | fresh computation independently checked |
| `HK-H1-FW` | `run`, `verify`, `inspect` | ready | fresh computation independently checked |
| `HK-H1-FINITE` | `run`, `verify`, `inspect` | ready | fresh computation independently checked |
| `HK-H1-L3-R26` | `run`, `verify`, `inspect` | ready | independent saved result validation |
| `HK-H1-L3-R52` | `run`, `verify`, `inspect` | ready | independent saved result validation |
| `HK-PATH-L3-H0` | `inspect`, `verify` | scope only | saved output integrity only |
| `HK-PATH-L3-H2` | `inspect`, `verify` | scope only | saved output integrity only |
| `HK-PATH-L3-FULL` | `inspect`, `verify` | scope only | saved output integrity only |
| `HK10-TIME-GRAPH` | `run`, `verify`, `inspect` | ready | fresh computation independently checked |
| `HK10-CG-R2R4-HISTORICAL` | `inspect`, `verify` | historical failure | saved output integrity only |
| `HK10-CG-R5` | `run`, `verify`, `inspect` | ready | independent saved result validation |
| `HK10-CG-R5-CLOSURE` | `inspect`, `verify` | ready | independent saved result validation |
| `HK10-ADMM-R2-GATED` | `inspect`, `verify` | historical failure | saved output integrity only |
| `HK4-ADMM-R3` | `run`, `verify`, `inspect` | ready | independent saved result validation |

Replace the record ID in the command above to run another recipe. `inspect` recomputes the available saved-state checks in a fresh output directory. It does not invoke an optimizer:

```sh
python tools/reproduction/recovered_hk.py inspect --repo-root . --record HK-H1-L3-R26 --output ../checks/hk-l3-r26
python tools/reproduction/recovered_hk.py inspect --repo-root . --record HK10-CG-R5-CLOSURE --output ../checks/hk-cg-closure
python tools/reproduction/recovered_hk.py inspect --repo-root . --record HK4-ADMM-R3 --output ../checks/hk-admm-r3
```

H1 checks independently reconstruct path/link flow, OD conservation, full-graph shortest-path gap and physical-link projection. CG checks all ten demands on the complete finite DAG using the saved 25-column pool and dual state. ADMM checks original-unit conservation, capacity, consensus, dual update, KKT and objective. A modified H1 path-flow negative control was rejected.

## Exact external data

The seven preparation recipes require selected original provider snapshots. Their complete resource URLs, query parameters, expected SHA-256 values and local layout are in the [recipe manifest](../../experiments/recovered/hong-kong.json). Inputs are not missing locally, but this repository deliberately avoids copying bulk provider archives or original UrbanNav/per-point observations.

Use either exact downloaded snapshots or an existing source folder with this layout:

```text
DATA_DIR/
  hong_kong_gmns_pilot_r1/raw/...
  hong_kong_full_stack_r2_r4/raw/...
```

```sh
python tools/reproduction/recovered_hk.py acquire --repo-root . --record HK-GTFS-WALK-R2 --output ../source-data
python tools/reproduction/recovered_hk.py run --repo-root . --record HK-GTFS-WALK-R2 --input-root ../source-data --output ../runs/hk-transit
```

`acquire` accepts only bytes matching the recorded hash. Government endpoints may now return a newer snapshot; a mismatch stops the acquisition instead of silently changing the experiment. `--input-root` accepts the same exact files from an existing local collection. ATC text extraction is supply-local: its hash describes the original extracted text, not the PDF bytes. The manifest links the original government PDF. UrbanNav remains subject to the provider’s exact-file terms; its source and per-point rows are not in this package.

### Preparation dependency boundaries

- R1 GMNS and population use the complete original R1 builder. It needs the registered road, turn, census geometry, pedestrian, GTFS and detector snapshots; the inspected census ZIPs are not substituted for the actual CSDI geometry/attributes.
- R2 regenerates the bounded turn extract from official TURN.kmz, then compiles the graph from prepared R1 objects, the exact SPEED_LIMIT.gml snapshot, and included bounded road/intersection extracts. Fresh output matched all 3,446 solver links and 1,896 movement edges.
- Activity rebuilds the published zone aggregate from provider building features and prepared zone/population inputs. The generated per-building allocation remains only in the user’s run directory.
- Transit runs GTFS extraction, walk routing and generalized costs in dependency order. It describes a generic Monday 08:00–09:00 engineering scenario.
- Observation association starts from published prepared detector observations plus the exact ATC geometry and original report text. It does not regenerate detector CSV from the live XML endpoint and is not traffic calibration.
- UrbanNav runs the original raw-reference projection and turn-aware Viterbi association. The fresh 13 numeric summary fields matched the saved report; no raw or per-point data was added to this repository.
- Time-graph construction starts from the accepted preselected 10-OD corridor. The original corridor-selection source is included; this command does not rerun the upstream Algorithm B experiment or select a different corridor.

## Numerical computation commands

```sh
python tools/reproduction/recovered_hk.py run --repo-root . --record HK-H1-FW --output ../runs/hk-h1-fw
python tools/reproduction/recovered_hk.py run --repo-root . --record HK-H1-L3-R26 --ipopt /path/to/ipopt --output ../runs/hk-h1-l3-r26
python tools/reproduction/recovered_hk.py run --repo-root . --record HK-H1-L3-R52 --ipopt /path/to/ipopt --output ../runs/hk-h1-l3-r52
python tools/reproduction/recovered_hk.py run --repo-root . --record HK10-CG-R5 --output ../runs/hk10-cg-r5
python tools/reproduction/recovered_hk.py verify --repo-root . --record HK10-CG-R5 --run ../runs/hk10-cg-r5
python tools/reproduction/recovered_hk.py run --repo-root . --record HK4-ADMM-R3 --output ../runs/hk4-admm-r3
```

Native L3 runs from the frozen H1 basis; CG runs from the frozen input-cost K1 seed; HK4 ADMM runs on its own frozen 4-OD graph and R3 policy. These are precise prepared-input contracts. Their source construction routines are retained, but no broader raw-to-all-results claim is made. Historical solver timings were about 13 seconds per H1 native rank, 540 seconds for CG and 150 seconds for HK4 ADMM; runtime and iteration choices may vary with the numerical environment. The fresh heavy solver commands above were not executed for this release. CG uses SciPy linprog/HiGHS plus NumPy and PyYAML; it does not require the native L3 IPOPT environment.

## Historical boundaries

`HK10-CG-R2R4-HISTORICAL` retained Phase I failure at the 50,000-state oracle limit. `HK10-ADMM-R2-GATED` retained failure before any accepted outer iteration; its previously reobserved failure did not have an identical residual. Neither becomes a successful solve because an integrity inspection passes. H0 is an interface check, H2 is a 100-OD / 492-path preflight, and FULL has no 8,930-OD finite-path/L3 solve.

All numerical sources are under [algorithms/recovered_hk](../../algorithms/recovered_hk/); minimal modeled fixtures and machine-readable evidence receipts are under [examples/hong-kong/recovered-r14](../../examples/hong-kong/recovered-r14/). Acquisition and publication remain governed by the project’s [data licenses](../../DATA_LICENSES.md) and [third-party notices](../../THIRD_PARTY_NOTICES.md).
