"""Recompute Boston conditional-choice scenarios using the unchanged public model."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, shutil, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

BASE = "examples/boston/conditional_choice_r1"
SCENARIOS = ("ABS_PLANNED", "ABS_OBS_EXPLORATORY", "ABS_RESTORE")

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def inputs(root):
    manifest = load(root / BASE / "inputs/INPUT_MANIFEST.json")
    for entry in manifest["files"]:
        p = (root / entry["repository_path"]).resolve()
        if not p.is_relative_to(root) or sha(p) != entry["sha256"]:
            raise ValueError("Frozen input missing or changed: " + entry["repository_path"])
    return manifest

def verify(root, output):
    inputs(root)
    actual = rows(output / "computed/od_baseline_probabilities.csv")
    expected = rows(root / BASE / "od_baseline_probabilities.csv")
    keys = ("scenario_id", "od_id", "departure_time", "scale_id", "mode_id")
    fields = ("probability_conditional", "person_trips_conditional_engineering_mass", "person_trips_panel")
    def index(data):
        result = {tuple(r[k] for k in keys): r for r in data}
        if len(result) != len(data):
            raise ValueError("Duplicate probability key")
        return result
    ai, ei = index(actual), index(expected)
    if set(ai) != set(ei):
        raise ValueError("Probability row keys differ from historical result")
    errors = []
    groups, scenario_mass = defaultdict(list), defaultdict(float)
    max_reference_delta = 0.0
    max_mass_error = 0.0
    for key, r in ai.items():
        for field in fields:
            value = float(r[field]); reference = float(ei[key][field])
            if not math.isfinite(value) or not math.isfinite(reference):
                raise ValueError("Nonfinite probability or mass")
            max_reference_delta = max(max_reference_delta, abs(value-reference))
        p = float(r["probability_conditional"])
        if p < 0 or p > 1:
            errors.append("Probability outside [0,1]")
        groups[key[:4]].append(p)
        max_mass_error = max(max_mass_error, abs(float(r[fields[1]]) - p*float(r[fields[2]])))
        if r["scale_id"] == "UNIT_BOUNDARY_PRIMARY" and r["mode_id"] == "TW":
            scenario_mass[r["scenario_id"]] += float(r[fields[1]])
    probability_sum_error = max(abs(sum(v)-1) for v in groups.values())
    restored = max(abs(float(ai[("ABS_PLANNED",)+k[1:]]["probability_conditional"])-float(r["probability_conditional"])) for k,r in ai.items() if k[0] == "ABS_RESTORE")
    ledger = rows(output / "computed/person_to_vehicle_ledger.csv")
    max_occupancy_error = 0.0
    expected_ledger = rows(root / BASE / "reference/person_to_vehicle_ledger.csv")
    ledger_keys = ("scenario_id", "od_id", "departure_time", "scale_id", "mode_id")
    la = {tuple(r[k] for k in ledger_keys):r for r in ledger}
    le = {tuple(r[k] for k in ledger_keys):r for r in expected_ledger}
    if not ledger or len(la)!=len(ledger) or len(le)!=len(expected_ledger) or set(la)!=set(le):
        raise ValueError("Vehicle ledger row keys, count or uniqueness differ from historical result")
    ledger_delta = 0.0
    for key,r in la.items():
        for field in ("probability_conditional","person_trips_conditional_engineering_mass","occupancy","vehicle_trips"):
            value=float(r[field]); ref=float(le[key][field])
            if not math.isfinite(value): raise ValueError("Nonfinite vehicle ledger value")
            ledger_delta=max(ledger_delta,abs(value-ref))
        for field in ("o_node_id","d_node_id","assignment_eligible"):
            if r[field]!=le[key][field]: raise ValueError("Vehicle ledger endpoint/eligibility mismatch")
    for r in ledger:
        f = float(r["vehicle_trips"]); occ = float(r["occupancy"])
        if not math.isfinite(f) or f < 0 or occ <= 0: errors.append("Invalid vehicle/occupancy value")
        max_occupancy_error = max(max_occupancy_error, abs(f*occ-float(r["person_trips_conditional_engineering_mass"])))
    exclusions = rows(output / "computed/exclusion_ledger.csv")
    scenario_counts = {s:{"evaluated":sum(r["scenario_id"]==s and r["full_four_mode_case"]=="True" for r in exclusions), "unknown":sum(r["scenario_id"]==s and r["full_four_mode_case"]=="False" for r in exclusions)} for s in SCENARIOS}
    checks = {"historical_probability_rows":len(actual)==len(expected), "historical_numeric_match":max_reference_delta<=1e-10,
              "probability_bounds":not errors,"probability_sums":probability_sum_error<=1e-12,
              "mass_accounting":max_mass_error<=1e-10,"occupancy_conversion":max_occupancy_error<=1e-10,"historical_vehicle_ledger":ledger_delta<=1e-10,
              "restoration_exact":restored==0, "fixed_scope":all(v=={"evaluated":87,"unknown":21} for v in scenario_counts.values())}
    report = {"status":"PASS" if all(checks.values()) else "FAIL", "success":all(checks.values()), "checks":[{"name":k,"pass":v} for k,v in checks.items()], "optimizer_calls":0, "metrics":{"probability_rows":len(actual),"max_historical_numeric_delta":max_reference_delta,"probability_sum_error":probability_sum_error,"person_mass_error":max_mass_error,"occupancy_error":max_occupancy_error,"restoration_probability_difference":restored,"primary_transit_person_mass":dict(scenario_mass),"scenario_counts":scenario_counts},"errors":errors,"scope":"All three frozen conditional choice scenarios, two declared scale vectors. No raw-source skim rebuilding or local calibration."}
    write(output / "verification.json", report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("run","verify"))
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument("--output",type=Path)
    p.add_argument("--run",dest="run_dir",type=Path)
    args=p.parse_args(); root=args.repo_root.resolve(); target=args.output if args.action=="run" else args.run_dir
    if target is None: p.error("run requires --output; verify requires --run")
    out=target.resolve()
    if args.action=="run":
        manifest=inputs(root)
        if out.exists() and any(out.iterdir()): raise ValueError("Output must be new or empty")
        (out/"inputs_snapshot/derived").mkdir(parents=True,exist_ok=True)
        for f in manifest["files"]: shutil.copyfile(root/f["repository_path"],out/"inputs_snapshot/derived"/f["name"])
        shutil.copyfile(root/BASE/"inputs/INPUT_MANIFEST.json",out/"SOURCE_SNAPSHOT_MANIFEST.json")
        command=[sys.executable,"-B",str(root/"algorithms/mode_choice_conditional/build_and_evaluate.py"),"--snapshot",str(out/"inputs_snapshot"),"--spec",str(root/"algorithms/mode_choice_conditional/choice_spec.json"),"--out",str(out/"computed")]
        started=time.perf_counter(); child=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=60)
        (out/"solver.stdout.log").write_text(child.stdout,encoding="utf-8"); (out/"solver.stderr.log").write_text(child.stderr,encoding="utf-8")
        write(out/"choice-execution.json",{"command":command,"exit_code":child.returncode,"elapsed_seconds":time.perf_counter()-started,"input_hashes":{x["repository_path"]:x["sha256"] for x in manifest["files"]}})
        if child.returncode: raise RuntimeError("Unchanged public model failed; see solver.stderr.log")
    result=verify(root,out); print(json.dumps(result,indent=2))
    if result["status"]!="PASS": sys.exit(2)

if __name__=="__main__": main()
