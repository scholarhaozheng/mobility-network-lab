"""Run Boston Algorithm B cases with a locally source-built pinned tap-b runtime."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, subprocess, sys
from pathlib import Path
BASE="algorithms/origin_based_algorithm_b/code"
COMMIT="040135a20c771fbb84766df6a97cff981fa5df4b"
ARCHIVE_SHA="5163b43051457c5c72cfc53253db4fc3668524cd3a5190169c99d2606fc430a5"
def load(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def rows(p):
    with Path(p).open(newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))
def invoke(args,root,out,label):
    child=subprocess.run([sys.executable,"-B",*map(str,args)],cwd=root,capture_output=True,text=True,timeout=1950)
    (out/(label+".stdout.log")).write_text(child.stdout,encoding="utf-8");(out/(label+".stderr.log")).write_text(child.stderr,encoding="utf-8")
    if child.returncode: raise RuntimeError(label+" failed: "+str(child.returncode))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("action",choices=("run","verify"));p.add_argument("--case",required=True,choices=("boston-b0","boston-b1"));p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--runtime",type=Path);p.add_argument("--output",type=Path);p.add_argument("--run",dest="run_dir",type=Path)
    a=p.parse_args();root=a.repo_root.resolve();target=a.output if a.action=="run" else a.run_dir
    if target is None: p.error("run requires --output; verify requires --run")
    out=target.resolve();case=load(root/"examples/boston/algorithm_b_r1/cases.json")["cases"][a.case];inputs=root/case["input_dir"]
    for n in ("link","demand"):
        if sha(inputs/(n+".csv"))!=case["input_sha256"][n]: raise ValueError("Frozen input changed: "+n)
    if a.action=="run":
        if out.exists() and any(out.iterdir()): raise ValueError("Output must be new or empty")
        runtime=(a.runtime or Path(os.environ.get("MCL_TAPB_RUNTIME",str(root/".mcl-runtime/tap-b")))).resolve();build=load(runtime/"build.json");exe=runtime/build["executable"]
        if build["exit_code"]!=0 or build["source_commit"]!=COMMIT or build["archive_sha256"]!=ARCHIVE_SHA or sha(exe)!=build["executable_sha256"]: raise ValueError("Pinned source-build provenance failed")
        out.mkdir(parents=True,exist_ok=True);write(out/"runtime-provenance.json",build)
        invoke([root/BASE/"taplab_bush_solver_adapter.py","run","--exe",exe,"--link",inputs/"link.csv","--demand",inputs/"demand.csv","--out",out/"computed"],root,out,"solve")
    build=load(out/"runtime-provenance.json")
    invoke([root/BASE/"independent_static_ue_evaluator.py","--link",inputs/"link.csv","--demand",inputs/"demand.csv","--run",out/"computed","--expected-exe-sha",build["executable_sha256"]],root,out,"verify")
    ev=load(out/"computed/evaluation.json");delta=abs(ev["objective"]-case["reference"]["objective"]);maxflow=0.0
    if case["reference_flow"]:
        actual={r["link_id"]:float(r["volume"]) for r in rows(out/"computed/link_flow.csv")};expected={r["link_id"]:float(r["volume"]) for r in rows(root/case["reference_flow"])}
        if actual.keys()!=expected.keys(): raise ValueError("Historical link ID mismatch")
        maxflow=max(abs(v-expected[k]) for k,v in actual.items())
    checks={"independent_full_graph_gates":ev["status"]=="ACCEPTED","historical_objective":delta<=case["tolerances"]["objective_abs"],"historical_flow":maxflow<=case["tolerances"]["link_flow_abs"],"physical_od_count":ev["positive_od"]==case["reference"]["positive_od"],"total_demand":abs(ev["total_demand"]-case["reference"]["total_demand"])<=1e-8}
    report={"success":all(checks.values()),"status":"PASS" if all(checks.values()) else "FAIL","checks":[{"name":k,"pass":v} for k,v in checks.items()],"optimizer_calls":0,"case":a.case,"metrics":{**{k:ev[k] for k in ("objective","total_demand","positive_od","relative_gap","max_od_residual","max_origin_node_residual","max_link_mismatch")},"historical_objective_delta":delta,"historical_link_flow_delta":maxflow},"historical_bytes_match":{"link":sha(out/"computed/link_flow.csv")==case["historical_output_sha256"]["link"],"path":sha(out/"computed/path_flow.csv")==case["historical_output_sha256"]["path"]},"scope":case["claim_boundary"]}
    write(out/"verification.json",report);print(json.dumps(report,indent=2))
    if not report["success"]: raise SystemExit(2)
if __name__=="__main__": main()
