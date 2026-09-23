"""Isolated invocation of an unmodified, pinned GMNS Plus Level 1/2 reader.

Only the optional DTALite import is isolated: the selected levels never call it.
No upstream validation method or result is patched. Do not run the batch launcher.
"""
import argparse
import importlib.util
import json
import sys
import types
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upstream-file", type=Path, required=True)
    p.add_argument("--exchange", type=Path, required=True)
    p.add_argument("--level", type=int, choices=(1, 2), default=2)
    p.add_argument("--demand", choices=("S1", "S2"), default="S1")
    args = p.parse_args()
    upstream = args.upstream_file.resolve()
    exchange = args.exchange.resolve()
    if not upstream.is_file():
        p.error("Pinned upstream source file not found")
    for name in ("node.csv", "link.csv", f"demand_{args.demand}.csv"):
        if not (exchange / name).is_file():
            p.error(f"Exchange file not found: {name}")
    # Upstream imports DTALite unconditionally, but calls it only in its optional
    # accessibility/assignment path. This sentinel prevents accidental execution.
    sentinel = types.ModuleType("DTALite")
    def forbidden():
        raise RuntimeError("DTALite assignment is outside this structural check")
    sentinel.assignment = forbidden
    sys.modules["DTALite"] = sentinel
    spec = importlib.util.spec_from_file_location("pinned_gmns_plus_reader", upstream)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reader = module.GMNSValidator(str(exchange / "node.csv"), str(exchange / "link.csv"),
                                  str(exchange / f"demand_{args.demand}.csv"))
    report = reader.validate(module.ReadinessLevel(args.level))
    print("MCL_WRAPPER_REPORT_JSON=" + json.dumps(report, ensure_ascii=False, default=str))
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
