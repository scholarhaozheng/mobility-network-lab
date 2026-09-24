"""Sequential, budgeted Boston profile runner for new prepared instances."""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from mcl_assignment import atomic_json, rows, sha
from mcl_native_l3 import task_tree_memory

GIB=1024**3


def available_ram():
    if os.name!="nt":return None
    from ctypes import wintypes
    class Status(ctypes.Structure):
        _fields_=[("dwLength",wintypes.DWORD),("dwMemoryLoad",wintypes.DWORD),
                  ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                  ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                  ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                  ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
    x=Status();x.dwLength=ctypes.sizeof(Status)
    return int(x.ullAvailPhys) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(x)) else None


def run_command(cmd,log,timeout,temp):
    """One task process group; sample only its PID and descendants."""
    env=os.environ.copy()
    interpreter=Path(cmd[0])
    library_bin=interpreter.parent/"Library"/"bin"
    if library_bin.is_dir():env["PATH"]=str(library_bin)+os.pathsep+env.get("PATH","")
    env.update({"PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"2","OPENBLAS_NUM_THREADS":"2",
                "MKL_NUM_THREADS":"2","NUMEXPR_NUM_THREADS":"2"})
    for k in ("TEMP","TMP","TMPDIR","MPLCONFIGDIR"):env[k]=str(temp)
    temp.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter();samples=[]
    with log.open("w",encoding="utf-8") as stream:
        p=subprocess.Popen([str(x) for x in cmd],stdout=stream,stderr=subprocess.STDOUT,env=env,
                           cwd=str(temp.parent),creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
        timeout_hit=False
        while p.poll() is None:
            elapsed=time.perf_counter()-start
            if timeout is not None and elapsed>=timeout:
                timeout_hit=True
                if os.name=="nt":subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],capture_output=True)
                else:p.kill()
                break
            s=task_tree_memory(p.pid);s["elapsed_seconds"]=elapsed;samples.append(s)
            time.sleep(5)
        code=None if timeout_hit else p.returncode
    record={"command":[str(x) for x in cmd],"exit_code":code,"timeout":timeout_hit,
            "wall_seconds":time.perf_counter()-start,"sampled_peak_tree_working_set_bytes":max((x.get("working_set_sum",0) for x in samples),default=None),
            "sampled_peak_tree_private_bytes":max((x.get("private_bytes_sum",0) for x in samples),default=None),
            "missed_short_peaks_possible":True,"samples":samples}
    atomic_json(log.with_suffix(".resource.json"),record)
    return record


def load_json(path):return json.loads(Path(path).read_text(encoding="utf-8"))


def run_scale(args):
    profile=load_json(args.profile)
    required={"regional_od","zone_crosswalk","boston_source_root","physical_network_dir",
              "choice_spec","choice_config","assignment_config","routing_python","solver_python",
              "skim_budget_seconds","heavy_budget_seconds"}
    if not required.issubset(profile) or set(profile)-required-{"requested_levels"}:
        raise ValueError(f"profile key mismatch: missing={sorted(required-set(profile))}, unknown={sorted(set(profile)-required-{'requested_levels'})}")
    requested=args.levels.split(",") if args.levels else profile.get("requested_levels",["500","2000","all"])
    if not requested or any(x not in ("500","2000","all") for x in requested):raise ValueError("invalid scale levels")
    for key in ("regional_od","zone_crosswalk","boston_source_root","physical_network_dir",
                "choice_spec","choice_config","assignment_config"):
        p=Path(profile[key])
        if not p.is_absolute():profile[key]=str((Path(args.profile).resolve().parent/p).resolve())
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    tools=Path(__file__).parent
    temp=out.parent/"tmp"
    selection=out/"selection_r1"
    summary={"status":"STARTED","requested_levels":requested,"tiers":{},"profile_sha256":sha(args.profile),
             "started_unix":time.time(),"stage_attempts":[]}
    if not (selection/"selection_order.csv").is_file():
        if selection.is_dir() and any(selection.iterdir()):
            raise ValueError("incomplete selection directory; use a fresh scale output")
        rec=run_command([profile["routing_python"],"-B",tools/"boston_scale_select.py","--regional-od",profile["regional_od"],
                         "--zone-crosswalk",profile["zone_crosswalk"],"--output",selection],out/"selection.log",600,temp)
        summary["stage_attempts"].append({"stage":"selection","record":str((out/"selection.resource.json").name)})
        if rec["exit_code"]!=0:raise RuntimeError("selection failed; inspect selection.log")
    lock=load_json(selection/"SOURCE_LOCK.json")
    if lock["regional_od_sha256"]!=sha(profile["regional_od"]) or lock["zone_crosswalk_sha256"]!=sha(profile["zone_crosswalk"]):
        raise ValueError("selection source changed; use a fresh scale output")
    output_hashes=lock.get("output_hashes")
    if not output_hashes or any(sha(selection/name)!=digest for name,digest in output_hashes.items()):
        raise ValueError("selection output integrity mismatch; use a fresh scale output")
    elapsed_skim=0.0;heavy=0.0
    for level in ("500","2000","all"):
        if level not in summary["requested_levels"]:continue
        tier={"status":"STARTED"};summary["tiers"][level]=tier
        panel=selection/f"selected_{level}.csv"
        if not panel.is_file():raise FileNotFoundError(panel)
        skim_dir=out/f"skims_{level}";skim=skim_dir/"mode_specific_od_costs.csv"
        old=load_json(skim_dir/"summary.json") if (skim_dir/"summary.json").is_file() else None
        if old and old["status"]=="COMPLETE" and old["output_sha256"]==sha(skim):
            elapsed_skim+=old["total_seconds"]
            tier["skims"]="VERIFIED_COMPLETE_CACHE_HIT"
        else:
            limit=profile["skim_budget_seconds"]
            remain=None if limit is None else limit-elapsed_skim
            if remain is not None and remain<=0:
                tier.update(status="RESOURCE_LIMIT",reason="cumulative skim subbudget exhausted");break
            cmd=[profile["routing_python"],"-B",tools/"boston_planned_costs.py","--panel",panel,
                 "--source-root",profile["boston_source_root"],"--output",skim_dir,
                 "--max-wall-seconds",remain if remain is not None else "inf"]
            prior="500" if level=="2000" else "2000" if level=="all" else None
            if prior and (out/f"skims_{prior}"/"summary.json").is_file():
                cmd+= ["--reuse-skims",out/f"skims_{prior}"/"mode_specific_od_costs.csv",
                       "--reuse-panel",selection/f"selected_{prior}.csv"]
            rec=run_command(cmd,out/f"skims_{level}.log",remain,temp)
            elapsed_skim+=rec["wall_seconds"]
            summary["stage_attempts"].append({"stage":f"skims_{level}","record":f"skims_{level}.resource.json"})
            if rec["exit_code"]!=0 or not (skim_dir/"summary.json").is_file():
                tier.update(status="RESOURCE_LIMIT" if (skim_dir/"partial_status.json").exists() or rec["timeout"] else "ERROR",
                            reason="skim partial/failed; completed origin chunks are resumable")
                break
            tier["skims"]="NEW_COMPLETE"
        choice=out/f"choice_{level}"
        if (choice/"summary.json").is_file():
            old_choice=load_json(choice/"summary.json")
            expected={panel.name:sha(panel),skim.name:sha(skim),
                      Path(profile["choice_spec"]).name:sha(profile["choice_spec"]),
                      Path(profile["choice_config"]).name:sha(profile["choice_config"])}
            if old_choice.get("input_hashes")!=expected or not (choice/"vehicle_demand.csv").is_file():
                raise ValueError(f"choice_{level} source/cache integrity mismatch; use a fresh output")
        if not (choice/"summary.json").is_file():
            rec=run_command([profile["solver_python"],"-B",tools/"mcl_person_choice.py",
                 "--person-od",panel,"--skims",skim,"--spec",profile["choice_spec"],
                 "--config",profile["choice_config"],"--output",choice],out/f"choice_{level}.log",300,temp)
            summary["stage_attempts"].append({"stage":f"choice_{level}","record":f"choice_{level}.resource.json"})
            if rec["exit_code"]!=0:
                tier.update(status="ERROR",reason=f"choice_{level} failed; inspect choice_{level}.log")
                break
        chosen=load_json(choice/"summary.json")
        tier["choice"]={k:chosen.get(k) for k in ("selected_zone_od","selected_person_mass","evaluated_person_mass",
            "unknown_person_mass","declared_search_unavailable_person_mass","non_evaluated_person_mass",
            "loaded_vehicle_trips","node_od","distinct_endpoint_nodes")}
        if chosen["node_od"]==0:
            tier.update(status="MISSING_INPUT",reason="no complete four-mode mapped vehicle OD");break
        instance=out/f"instance_{level}"
        if (instance/"manifest.json").is_file():
            old_instance=load_json(instance/"manifest.json")
            assignment_cfg=load_json(profile["assignment_config"])
            expected={"link":sha(Path(profile["physical_network_dir"])/assignment_cfg.get("link_file","link.csv")),
                      "demand":sha(choice/"vehicle_demand.csv"),"config":sha(profile["assignment_config"])}
            if old_instance.get("source_hashes")!=expected or sha(instance/"link.csv")!=old_instance.get("link_sha256") or sha(instance/"demand.csv")!=old_instance.get("demand_sha256"):
                raise ValueError(f"instance_{level} source/cache integrity mismatch; use a fresh output")
        if not (instance/"manifest.json").is_file():
            rec=run_command([profile["solver_python"],"-B",tools/"mcl_assignment.py","prepare",
                "--input",profile["physical_network_dir"],"--demand",choice/"vehicle_demand.csv",
                "--config",profile["assignment_config"],"--output",instance],out/f"prepare_{level}.log",300,temp)
            summary["stage_attempts"].append({"stage":f"prepare_{level}","record":f"prepare_{level}.resource.json"})
            if rec["exit_code"]!=0:
                tier.update(status="ERROR",reason=f"prepare_{level} failed; inspect prepare_{level}.log")
                break
        im=load_json(instance/"manifest.json");tier["instance_signature"]=im["instance_signature"]
        avail=available_ram();ceiling=min(8*GIB,avail//2) if avail else None
        disk=shutil.disk_usage(out).free
        # Python graph/CSV overhead plus per-OD and per-link work arrays. This
        # is deliberately above the sampled 500/2000 FW process-tree peaks.
        fw_estimate=128*1024**2+2048*int(im["node_od"])+512*int(im["physical_links"])
        tier["pre_fw_resources"]={"available_physical_bytes":avail,"working_memory_ceiling":ceiling,
                                  "fw_preflight_estimate_bytes":fw_estimate,"disk_free_bytes":disk}
        fw=out/f"fw_{level}"
        if not (fw/"run.json").is_file() and ceiling is not None and ceiling<fw_estimate:
            tier.update(status="RESOURCE_LIMIT",reason="FW preflight estimate exceeds measured half-free-memory ceiling");break
        if (fw/"run.json").is_file():
            old_fw=load_json(fw/"run.json")
            if old_fw.get("instance_signature")!=im["instance_signature"] or sha(fw/"link_flow.csv")!=old_fw.get("link_flow_sha256") or sha(fw/"path_flow.csv")!=old_fw.get("path_flow_sha256"):
                raise ValueError(f"fw_{level} source/cache integrity mismatch; use a fresh output")
        if not (fw/"run.json").is_file():
            rec=run_command([profile["solver_python"],"-B",tools/"mcl_assignment.py","solve",
                "--instance",instance,"--method","fw","--config",profile["assignment_config"],"--output",fw],
                out/f"fw_{level}.log",1800,temp)
            heavy+=rec["wall_seconds"]
            summary["stage_attempts"].append({"stage":f"fw_{level}","record":f"fw_{level}.resource.json"})
            if rec["exit_code"]!=0:
                tier.update(status="SOLVER_TERMINATED_BUT_NOT_ACCEPTED" if (fw/"run.json").is_file() else "ERROR",
                            reason=f"FW_{level} nonzero exit; inspect fw_{level}.log")
                break
        rec=run_command([profile["solver_python"],"-B",tools/"mcl_assignment.py","verify","--run",fw],
            out/f"verify_fw_{level}.log",300,temp)
        summary["stage_attempts"].append({"stage":f"verify_fw_{level}","record":f"verify_fw_{level}.resource.json"})
        fv=load_json(fw/"verification.json") if (fw/"verification.json").is_file() else None
        tier["fw"]={"status":fv["status"] if fv else "NO_CHECK", "objective":fv.get("objective_checked") if fv else None,
                    "relative_gap":fv.get("full_network_relative_gap") if fv else None}
        if rec["exit_code"]!=0 or fv["status"]!="SOLVED_WITHIN_DECLARED_TOLERANCE":
            tier.update(status="SOLVER_TERMINATED_BUT_NOT_ACCEPTED",reason="FW independent gate failed");break
        fig=out/f"figures_{level}"
        if (fig/"plot.json").is_file():
            old_plot=load_json(fig/"plot.json")
            if old_plot.get("instance_signature") not in (None,im["instance_signature"]) or old_plot.get("link_flow_sha256") not in (None,sha(fw/"link_flow.csv")) or sha(fig/"plot_link_table.csv")!=old_plot.get("link_table_sha256"):
                raise ValueError(f"figures_{level} source/cache integrity mismatch; use a fresh output")
            plotted={r["link_id"]:float(r["flow_pce_per_period"]) for r in rows(fig/"plot_link_table.csv")}
            current={r["link_id"]:float(r["flow_pce_per_period"]) for r in rows(fw/"link_flow.csv")}
            if plotted.keys()!=current.keys() or any(abs(plotted[k]-current[k])>1e-12 for k in current):
                raise ValueError(f"figures_{level} flow differs from current FW; use a fresh output")
        if not (fig/"plot.json").is_file():
            rec=run_command([profile["solver_python"],"-B",tools/"mcl_assignment.py","plot","--run",fw,"--output",fig],
                out/f"plot_{level}.log",300,temp)
            summary["stage_attempts"].append({"stage":f"plot_{level}","record":f"plot_{level}.resource.json"})
            tier["plot_status"]="COMPLETE" if rec["exit_code"]==0 else "ERROR"
        zone_fig=out/f"source_zone_figures_{level}"
        if (zone_fig/"plot.json").is_file():
            zone_plot=load_json(zone_fig/"plot.json")
            zone_file=Path(profile["boston_source_root"])/"database/zones/zone.csv"
            if zone_plot.get("panel_sha256")!=sha(panel) or zone_plot.get("zones_sha256")!=sha(zone_file) or zone_plot.get("source_table_sha256")!=sha(zone_fig/"source_zone_coverage.csv"):
                raise ValueError(f"source_zone_figures_{level} source/cache integrity mismatch")
        if not (zone_fig/"plot.json").is_file():
            rec=run_command([profile["solver_python"],"-B",tools/"boston_zone_coverage.py",
                "--panel",panel,"--zones",Path(profile["boston_source_root"])/"database/zones/zone.csv",
                "--tier-label",level,"--output",zone_fig],out/f"source_zone_plot_{level}.log",300,temp)
            summary["stage_attempts"].append({"stage":f"source_zone_plot_{level}","record":f"source_zone_plot_{level}.resource.json"})
            tier["source_zone_plot_status"]="COMPLETE" if rec["exit_code"]==0 else "ERROR"
        tier["status"]="SOLVED_WITHIN_DECLARED_TOLERANCE"
        if profile["heavy_budget_seconds"] is not None and heavy>=profile["heavy_budget_seconds"]:break
    summary["skim_seconds_counted"]=elapsed_skim;summary["heavy_seconds_counted"]=heavy
    summary["status"]="COMPLETE_REQUESTED_LEVELS" if all(x.get("status")=="SOLVED_WITHIN_DECLARED_TOLERANCE" for x in summary["tiers"].values()) and len(summary["tiers"])==len(summary["requested_levels"]) else "PARTIAL"
    summary["total_wall_seconds"]=time.time()-summary["started_unix"]
    atomic_json(out/"scale_status.json",summary)
    return summary
