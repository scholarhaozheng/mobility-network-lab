# Boston recovered reproduction packages

This candidate extends existing public calculation code. It contains no raw GPS, person, or property-assessment records. Historical sources and outputs remain unchanged.

## Ready entries

- Conditional choice: one execution computes ABS_PLANNED, ABS_OBS_EXPLORATORY and ABS_RESTORE from the 36-OD frozen panel. All 2,088 probability rows exactly match the historical output. This is a conditional transferred-model sensitivity, not local calibration or raw-source skim reconstruction.
- Algorithm B B0/B1: freshly rebuilt pinned tap-b, original lossless adapter and independent evaluator. B0 has 26 physical ODs; B1 starts with 500 selected source ODs and aggregates to 453 positive endpoint pairs. Both link/path outputs match historical files byte for byte.
- Native L3 rank26/rank52: public isolated builder and frozen 130-path inputs reproduce accepted outer02. A stale published checker source hash is corrected. Original and BPR-adapted mathematical ASTs match historical source exactly; no numerical criterion changes.

## Algorithm B setup

Install a compiler separately. Windows Zig0.15.1 was tested. No compiler, solver executable or source archive is included.

~~~powershell
python tools/reproduction/build_tapb.py --compiler zig --output .mcl-runtime/tap-b
~~~

The command downloads the pinned commit archive and checks SHA256 before building. If downloaded separately:

~~~powershell
python tools/reproduction/build_tapb.py --archive /path/to/tap-b-040135a20c771fbb84766df6a97cff981fa5df4b.zip --compiler zig --output .mcl-runtime/tap-b
~~~

Source: https://github.com/spartalab/tap-b/archive/040135a20c771fbb84766df6a97cff981fa5df4b.zip

Archive SHA256: 5163b43051457c5c72cfc53253db4fc3668524cd3a5190169c99d2606fc430a5.

Only the two historical output-precision changes (%f to %.17g) and serial Windows timing compatibility define are applied. The POSIX cc recipe is supplied but untested. Use MCL_TAPB_RUNTIME for a nondefault build directory. The upstream MIT license stays in the extracted source.

## Native L3 setup

Use a separately installed native environment. Tested: Python3.9.25, Pyomo6.9.5, NumPy2.0.2, SciPy1.13.1, IPOPT3.14.19 and MUMPS5.8.1. The ordinary repository Python invokes this environment through:

~~~powershell
$env:MCL_NATIVE_PYTHON = '/path/to/native/python.exe'
$env:MCL_IPOPT = '/path/to/native/ipopt.exe'
python tools/reproduction/boston_native.py run --repo-root . --output results/boston-native
python tools/reproduction/boston_native.py verify --repo-root . --run results/boston-native
~~~

The frozen controller is Windows-specific because of process/memory sampling. Linux execution is not verified. PATH and temporary directory changes apply only to children. Verification calls the independent original-space checker with no optimization.

