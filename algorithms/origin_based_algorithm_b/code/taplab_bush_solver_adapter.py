"""Task-local TAPLab-supported tap-b Algorithm B format/process adapter.

The executable is the official spartalab/tap-b mathematical core, with only
text output precision widened in a separately recorded compatibility diff.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from static_ue_problem_contract import export_tntp, load_problem, sha256

POLICY = dict(solver_gap=1e-8, max_iterations=10000, max_run_time_seconds=1800,
              evaluator_relative_gap=1e-4, max_used_arc_slack_minutes=0.05,
              max_used_path_slack_minutes=0.05, unused_arc_slack_floor_minutes=-1e-8,
              balance_abs=1e-6, balance_rel_total=1e-9,
              active_flow_abs=1e-9, active_flow_rel_od=1e-8,
              nonnegative_floor=-1e-10, first_thru_node=1,
              batches=1, gap_function="RELATIVE GAP")


def prepare(link, demand, run_dir):
    work = Path(run_dir)
    work.mkdir(parents=True, exist_ok=True)
    p = load_problem(link, demand)
    mapping = export_tntp(p, work)
    params = ["<NETWORK FILE> r2_net.txt", "<TRIPS FILE> r2_trips.txt",
              "<FLOWS FILE> r2_flows.txt", "<PATH FLOWS FILE> r2_pathflows.txt",
              f"<CONVERGENCE GAP> {POLICY['solver_gap']:.17g}",
              f"<MAX ITERATIONS> {POLICY['max_iterations']}",
              f"<MAX RUN TIME> {POLICY['max_run_time_seconds']}",
              "<NUMBER OF BATCHES> 1", "<GAP FUNCTION> RELATIVE GAP"]
    (work / "params.txt").write_text("\n".join(params) + "\n", encoding="ascii")
    input_lock = dict(source_link=str(Path(link).resolve()),
                      source_demand=str(Path(demand).resolve()),
                      source_link_sha256=p["link_sha256"],
                      source_demand_sha256=p["demand_sha256"],
                      converted=mapping["converted_hashes"],
                      mapping_sha256=sha256(work / "mapping.json"),
                      params_sha256=sha256(work / "params.txt"),
                      policy=POLICY)
    (work / "input_lock.json").write_text(json.dumps(input_lock, indent=2, sort_keys=True), encoding="utf-8")
    return input_lock


def _parse_flow(raw, mapping, dest):
    inv = {int(k): v for k, v in mapping["tntp_to_old"].items()}
    pair_to_id = mapping["directed_pair_to_link_id"]
    rows = []
    for line in raw.splitlines():
        m = re.fullmatch(r"\s*\((\d+),(\d+)\)\s+([-+\d.eE]+)\s*", line)
        if not m:
            continue
        u, v = inv[int(m[1])], inv[int(m[2])]
        key = f"{u},{v}"
        if key not in pair_to_id:
            raise ValueError(f"unknown solver link {key}")
        rows.append((pair_to_id[key], u, v, float(m[3])))
    if len(rows) != mapping["link_count"] or len({r[0] for r in rows}) != len(rows):
        raise ValueError(f"solver returned {len(rows)} unique/mapped flows; expected {mapping['link_count']}")
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(("link_id", "from_node_id", "to_node_id", "volume"))
        w.writerows(rows)


def _parse_paths(raw_path, mapping, dest):
    inv = {int(k): v for k, v in mapping["tntp_to_old"].items()}
    pair_to_id = mapping["directed_pair_to_link_id"]
    count = 0
    with open(raw_path, encoding="ascii") as inp, open(dest, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(("origin", "destination", "volume", "node_ids", "link_ids"))
        for line in inp:
            m = re.fullmatch(r"\s*\[([\d,]+)\]\s*:\s*([-+\d.eE]+)\s*", line)
            if not m:
                raise ValueError(f"invalid upstream path line {line[:120]!r}")
            seq = [inv[int(x)] for x in m[1].split(",")]
            if len(seq) < 2 or len(seq) != len(set(seq)):
                raise ValueError("upstream path has loop or no link")
            lids = []
            for u, v in zip(seq, seq[1:]):
                key = f"{u},{v}"
                if key not in pair_to_id:
                    raise ValueError(f"unknown upstream path link {key}")
                lids.append(pair_to_id[key])
            w.writerow((seq[0], seq[-1], float(m[2]), ";".join(map(str, seq)), ";".join(lids)))
            count += 1
    return count


def run(exe, link, demand, run_dir):
    work, exe = Path(run_dir).resolve(), Path(exe).resolve()
    lock = prepare(link, demand, work)
    if not exe.is_file():
        raise FileNotFoundError(exe)
    start = time.monotonic()
    try:
        proc = subprocess.run([str(exe), "params.txt"], cwd=work,
                              capture_output=True, text=True, errors="replace",
                              timeout=POLICY["max_run_time_seconds"] + 120)
    except subprocess.TimeoutExpired as e:
        (work / "timeout.json").write_text(json.dumps(dict(error=str(e))), encoding="utf-8")
        raise
    (work / "stdout.log").write_text(proc.stdout, encoding="utf-8")
    (work / "stderr.log").write_text(proc.stderr, encoding="utf-8")
    record = dict(command=[str(exe), "params.txt"], exit_code=proc.returncode,
                  wall_seconds=time.monotonic() - start, executable_sha256=sha256(exe),
                  input_lock=lock)
    (work / "process.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"tap-b exit {proc.returncode}; see {work / 'stderr.log'}")
    mapping = json.loads((work / "mapping.json").read_text(encoding="utf-8"))
    flows = work / "r2_flows.txt"
    paths = work / "r2_pathflows.txt"
    if not flows.exists() or not paths.exists():
        raise FileNotFoundError("tap-b omitted required link/path output")
    _parse_flow(flows.read_text(encoding="ascii"), mapping, work / "link_flow.csv")
    count = _parse_paths(paths, mapping, work / "path_flow.csv")
    if not count:
        raise ValueError("tap-b emitted no OD path flows")
    gaps = [(int(i), float(g)) for i, g in re.findall(
        r"Iteration\s+(\d+):\s+gap\s+([-+\d.eE]+)", proc.stdout)]
    with open(work / "history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(("iteration", "solver_reported_gap")); w.writerows(gaps)
    record.update(path_count=count, final_solver_reported_gap=gaps[-1][1] if gaps else None,
                  output_hashes={name: sha256(work / name) for name in
                                 ("r2_flows.txt", "r2_pathflows.txt", "link_flow.csv", "path_flow.csv")})
    (work / "process.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("prepare", "run"))
    ap.add_argument("--exe")
    ap.add_argument("--link", required=True)
    ap.add_argument("--demand", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.mode == "run" and not a.exe:
        ap.error("--exe is required for run")
    x = prepare(a.link, a.demand, a.out) if a.mode == "prepare" else run(a.exe, a.link, a.demand, a.out)
    print(json.dumps(x, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ADAPTER_FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(2)
