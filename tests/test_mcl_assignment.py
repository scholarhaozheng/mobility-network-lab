"""Contract tests for changed inputs, identities, units and numerical output."""
from __future__ import annotations
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"tools/mcl_assignment.py"
FIX=ROOT/"examples/scalable_vehicle_fixture"


def call(*args,okay=True):
    p=subprocess.run([sys.executable,"-B",str(TOOL),*map(str,args)],capture_output=True,text=True,env=runtime_env())
    if okay and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
    return p


def runtime_env():
    env=os.environ.copy()
    library_bin=Path(sys.executable).parent/"Library"/"bin"
    if library_bin.is_dir():env["PATH"]=str(library_bin)+os.pathsep+env.get("PATH","")
    env.update(PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",MKL_NUM_THREADS="2")
    return env


class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get("MCL_TEST_TMP"))
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)

    def prepare(self,demand,config,name):
        out=self.base/name
        call("prepare","--input",FIX/"network","--demand",demand,"--config",config,"--output",out)
        return out,json.loads((out/"manifest.json").read_text())

    def test_changed_demand_recomputes_and_row_reorder_invariant(self):
        base,ma=self.prepare(FIX/"vehicle.csv",FIX/"config.json","base")
        call("solve","--instance",base,"--method","fw","--output",self.base/"base_run")
        call("verify","--run",self.base/"base_run")
        with (FIX/"vehicle.csv").open(newline="",encoding="utf-8") as f:
            original=list(csv.DictReader(f))
        perturbed=[dict(r) for r in original]
        perturbed[0]["volume"]=str(float(perturbed[0]["volume"])*1.07)
        changed=self.base/"changed.csv"
        with changed.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=original[0]);w.writeheader();w.writerows(perturbed)
        b,mb=self.prepare(changed,FIX/"config.json","changed")
        call("solve","--instance",b,"--method","fw","--output",self.base/"changed_run")
        call("verify","--run",self.base/"changed_run")
        fa=json.loads((self.base/"base_run"/"run.json").read_text())
        fb=json.loads((self.base/"changed_run"/"run.json").read_text())
        self.assertNotEqual(ma["instance_signature"],mb["instance_signature"])
        self.assertNotEqual(fa["objective"],fb["objective"])
        reordered=self.base/"reordered.csv"
        with reordered.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=original[0]);w.writeheader();w.writerows(reversed(original))
        _,mc=self.prepare(reordered,FIX/"config.json","reordered")
        self.assertEqual(ma["instance_signature"],mc["instance_signature"])

    def test_unreachable_and_coaccess_accounting(self):
        p=call("prepare","--input",FIX/"network","--demand",FIX/"vehicle_unreachable.csv",
               "--config",FIX/"config.json","--output",self.base/"bad",okay=False)
        self.assertNotEqual(p.returncode,0)
        _,m=self.prepare(FIX/"person_like_zonal_vehicle.csv",FIX/"zonal_config.json","zones")
        self.assertEqual(m["node_od"],1)
        self.assertEqual(m["excluded_by_reason_pce"]["same_access_node"],4.0)
        self.assertEqual(m["loaded_pce"],20.0)
        with (self.base/"zones"/"link.csv").open(newline="",encoding="utf-8") as f:
            lines=list(csv.DictReader(f))
        self.assertEqual(float(lines[0]["capacity"]),100.0)

    def test_invalid_config_and_help(self):
        c=json.loads((FIX/"config.json").read_text())
        c["capcity_basis"]="typo"
        bad=self.base/"bad.json";bad.write_text(json.dumps(c),encoding="utf-8")
        p=call("prepare","--input",FIX/"network","--demand",FIX/"vehicle.csv",
               "--config",bad,"--output",self.base/"bad",okay=False)
        self.assertNotEqual(p.returncode,0)
        self.assertFalse((self.base/"bad").exists())
        classed=self.base/"classed.csv"
        classed.write_text("o_node_id,d_node_id,volume,mode_class\n001,Z9,3,car\n001,Z9,4,truck\n",encoding="utf-8")
        p=call("prepare","--input",FIX/"network","--demand",classed,
               "--config",FIX/"config.json","--output",self.base/"classed",okay=False)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(call("--help").returncode,0)

    def test_source_output_overlap_and_invalid_returned_flow(self):
        p=call("prepare","--input",FIX/"network","--demand",FIX/"vehicle.csv",
               "--config",FIX/"config.json","--output",FIX/"network"/"accidental_output",okay=False)
        self.assertNotEqual(p.returncode,0)
        self.assertFalse((FIX/"network"/"accidental_output").exists())
        instance,_=self.prepare(FIX/"vehicle.csv",FIX/"config.json","instance")
        run=self.base/"fw"
        call("solve","--instance",instance,"--method","fw","--output",run)
        flow=run/"link_flow.csv"
        text=flow.read_text(encoding="utf-8")
        lines=text.splitlines()
        first=lines[1].split(",")
        first[1]="-100"
        lines[1]=",".join(first)
        flow.write_text("\n".join(lines)+"\n",encoding="utf-8")
        p=call("verify","--run",run,okay=False)
        self.assertNotEqual(p.returncode,0)

    def test_corrupt_path_cache_and_missing_native_solver(self):
        instance,_=self.prepare(FIX/"vehicle.csv",FIX/"config.json","instance")
        pool=self.base/"pool"
        path_tool=ROOT/"tools/mcl_path_methods.py"
        p=subprocess.run([sys.executable,"-B",str(path_tool),"paths","--instance",str(instance),
                          "--output",str(pool)],capture_output=True,text=True,env=runtime_env())
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        full_config=self.base/"full.json"
        full_config.write_text(json.dumps({"k":5,"pool_dir":str(pool),"max_iterations":10}),encoding="utf-8")
        paths=pool/"paths.csv"
        original=paths.read_text(encoding="utf-8")
        paths.write_text(original+"\n",encoding="utf-8")
        bad=call("solve","--instance",instance,"--method","full-path","--config",full_config,
                 "--output",self.base/"bad_pool",okay=False)
        self.assertNotEqual(bad.returncode,0)
        paths.write_text(original,encoding="utf-8")
        native_config=self.base/"native.json"
        native_config.write_text(json.dumps({"k":5,"pool_dir":str(pool),"rank_fraction":0.25,
            "ipopt_executable":str(self.base/"missing_ipopt.exe"),"temp_dir":str(self.base/"tmp"),
            "inner_timeout":15,"total_timeout":30,"max_outer":1}),encoding="utf-8")
        missing=call("solve","--instance",instance,"--method","diagnostic-l3","--config",native_config,
                     "--output",self.base/"missing_solver",okay=False)
        self.assertNotEqual(missing.returncode,0)
        native=json.loads((self.base/"missing_solver"/"run.json").read_text(encoding="utf-8"))
        self.assertNotEqual(native["solver"]["status"],"SOLVED_WITHIN_DECLARED_TOLERANCE")

    def test_explicit_hour_lane_and_pce_conversion_once(self):
        network=self.base/"hourly_network"
        network.mkdir()
        with (FIX/"network"/"link.csv").open(newline="",encoding="utf-8") as f:
            links=list(csv.DictReader(f))
        links[0]["lanes"]="2"
        links[0]["vdf_plf"]="0.8"
        with (network/"link.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=links[0]);w.writeheader();w.writerows(links)
        cfg=json.loads((FIX/"config.json").read_text(encoding="utf-8"))
        cfg.update(demand_unit="vehicles_per_hour",period_hours=2.0,
                   capacity_basis="hourly_pce_per_lane",pce_factor=1.5)
        path=self.base/"hourly.json"
        path.write_text(json.dumps(cfg),encoding="utf-8")
        out=self.base/"hourly_instance"
        call("prepare","--input",network,"--demand",FIX/"vehicle.csv","--config",path,"--output",out)
        m=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
        baseline=json.loads((self.prepare(FIX/"vehicle.csv",FIX/"config.json","baseline")[0]/"manifest.json").read_text())
        self.assertAlmostEqual(m["loaded_pce"],baseline["loaded_pce"]*3)
        self.assertNotEqual(m["instance_signature"],baseline["instance_signature"])
        with (out/"link.csv").open(newline="",encoding="utf-8") as f:
            by_id={r["link_id"]:r for r in csv.DictReader(f)}
        self.assertAlmostEqual(float(by_id["parallel-A"]["capacity"]),160.0)

    def test_person_choice_unknown_fare_and_unavailable_route_remain_distinct(self):
        fixture=ROOT/"examples/scalable_person_fixture"
        tool=ROOT/"tools/mcl_person_choice.py"
        with (fixture/"skims.csv").open(newline="",encoding="utf-8") as f:
            skim=list(csv.DictReader(f))
        def evaluate(changed,name):
            source=self.base/(name+".csv")
            with source.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(changed[0]));w.writeheader();w.writerows(changed)
            out=self.base/name
            p=subprocess.run([sys.executable,"-B",str(tool),"--person-od",str(fixture/"person.csv"),
                "--skims",str(source),"--spec",str(ROOT/"examples/boston/scalable_tool_r1/choice_spec.json"),
                "--config",str(fixture/"choice_config.json"),"--output",str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            with (out/"choice_ledger.csv").open(newline="",encoding="utf-8") as f:
                return {r["od_id"]:r for r in csv.DictReader(f)}
        missing=[dict(r) for r in skim]
        missing[1]["fare_usd"]=""
        fare=evaluate(missing,"missing_fare")
        self.assertEqual(fare["fixture-001"]["status"],"UNKNOWN_CONDITIONAL_SCOPE")
        self.assertIn("selected_itinerary_fare",fare["fixture-001"]["reason"])
        unavailable=[dict(r) for r in skim]
        unavailable[1]["availability_status"]="confirmed_unavailable_within_declared_search_limits"
        route=evaluate(unavailable,"unavailable_route")
        self.assertEqual(route["fixture-001"]["status"],"DECLARED_SEARCH_UNAVAILABLE_FOUR_MODE_SCOPE")
        self.assertIn("confirmed_unavailable_within_declared_search_limits",route["fixture-001"]["reason"])
        self.assertNotEqual(fare["fixture-001"]["reason"],route["fixture-001"]["reason"])


if __name__=="__main__":unittest.main()
