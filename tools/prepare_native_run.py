#!/usr/bin/env python3
"""Stage an opt-in native L3 run in a NEW directory; do not invoke a solver."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHOD = ROOT / "algorithms/path_compression/diagnostic_l3"
SOURCE = METHOD / "source/build_alm_model_levels.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("boston", "sioux-falls"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="new empty run directory")
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        parser.error("output already exists; choose a new empty directory")
    if args.case == "boston":
        profile = METHOD / "profiles/boston"
        data = ROOT / "examples/boston/assignment_methods_r1"
        groups = ((profile / "adapters", "adapters"),
                  (profile / "checks", "checks"),
                  (data / "inputs_snapshot", "inputs_snapshot"),
                  (data / "reference", "reference"))
    else:
        profile = METHOD / "profiles/sioux"
        data = ROOT / "examples/sioux-falls/native_l3_r1"
        groups = ((profile / "runner", "runner"),
                  (data / "inputs_snapshot", "inputs_snapshot"))
    for source, _ in groups:
        if not source.is_dir():
            parser.error(f"missing public source directory: {source}")
    if not SOURCE.is_file():
        parser.error("missing isolated native builder")
    target.mkdir(parents=True)
    for source, relative in groups:
        shutil.copytree(source, target / relative)
    (target / "source_snapshot").mkdir()
    shutil.copy2(SOURCE, target / "source_snapshot/run_diagnostic_levels.py")
    (target / "tmp").mkdir()
    print(f"Staged {args.case} native source and frozen inputs at {target}")
    print("No solver executed. Native reproduction requires a separate Pyomo/IPOPT/MUMPS environment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
