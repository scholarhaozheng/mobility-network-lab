# Static Frank–Wolfe implementation

`tap_frank_wolfe.py` is retained byte-for-byte from the existing auxiliary project. It contains BPR costs, Beckmann integration, all-or-nothing shortest paths and line search.

Its historical Sioux result is described in [the data catalog](../../docs/datasets/sioux-static-fw.md). This implementation is separate from the finite space–time CG workflow and is not invoked by `tools/mnl.py run`.

The library callable is `solve_fw_refined(data_dir, run_name, max_iter, cap_scale)`. It writes logs and result CSVs to the working directory. The legacy `__main__` block automatically runs its configured networks, so do not execute the file blindly against a data directory. Use an isolated output directory and inspect the field assumptions before integrating it.

Additional dependency: pandas. The loader has historical assumptions about OD endpoints, BPR fields and capacity scaling. The saved benchmark result supports the documented approximate baseline, not universal input compatibility. Its original console heading is not a numerical proof of equilibrium accuracy.
