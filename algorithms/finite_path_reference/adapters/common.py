"""Frozen Boston CSV and exact heterogeneous BPR helpers."""
from __future__ import annotations

import csv
import ctypes
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def write_rows(path: Path, data: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(data)

def load_instance(input_dir: Path):
    links=rows(input_dir/"link.csv")
    demand=rows(input_dir/"demand.csv")
    ids=[r["link_id"] for r in links]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate link_id")
    od=[(r["o_zone_id"],r["d_zone_id"]) for r in demand]
    if len(od)!=len(set(od)) or not all(float(r["volume"])>0 for r in demand):
        raise ValueError("duplicate or nonpositive demand pair")
    q=np.array([float(r["volume"]) for r in demand],dtype=float)
    cap=np.maximum(np.array([float(r["capacity"]) for r in links]),1.0)
    t0=np.array([float(r["vdf_fftt"]) for r in links])
    alpha=np.array([float(r["vdf_alpha"]) for r in links])
    beta=np.array([float(r["vdf_beta"]) for r in links])
    if np.any(cap<=0) or np.any(t0<=0) or np.any(alpha<0) or np.any(beta<=0):
        raise ValueError("invalid BPR parameter")
    return {"links":links,"demand":demand,"link_ids":ids,"link_index":{k:i for i,k in enumerate(ids)},"od":od,"q":q,"cap":cap,"t0":t0,"alpha":alpha,"beta":beta}

def link_cost(v, instance):
    return instance["t0"]*(1+instance["alpha"]*(v/instance["cap"])**instance["beta"])

def beckmann(v, instance):
    if np.min(v)<-1e-10:
        raise ValueError("negative link flow outside BPR domain")
    x=np.maximum(v,0.0)
    return float(np.sum(instance["t0"]*x + instance["t0"]*instance["alpha"]/(instance["beta"]+1)*x*(x/instance["cap"])**instance["beta"]))

def load_pool(pool_dir: Path, instance):
    paths=rows(pool_dir/"path_pool.csv")
    A=sparse.load_npz(pool_dir/"A_link_path.npz").tocsr()
    C=sparse.load_npz(pool_dir/"C_od_path.npz").tocsr()
    f0=np.array([float(r["flow"]) for r in rows(pool_dir/"f0.csv")],dtype=float)
    if A.shape!=(len(instance["links"]),len(paths)) or C.shape!=(len(instance["od"]),len(paths)) or f0.shape!=(len(paths),):
        raise ValueError("pool dimensions incompatible with frozen instance")
    return {"paths":paths,"A":A,"C":C,"f0":f0}

def peak_working_set_bytes():
    """Windows GetProcessMemoryInfo peak working set for the current process."""
    if sys.platform != "win32": return None
    size=ctypes.c_size_t
    class Counters(ctypes.Structure):
        _fields_=[("cb",ctypes.c_uint32),("PageFaultCount",ctypes.c_uint32),
                 ("PeakWorkingSetSize",size),("WorkingSetSize",size),
                 ("QuotaPeakPagedPoolUsage",size),("QuotaPagedPoolUsage",size),
                 ("QuotaPeakNonPagedPoolUsage",size),("QuotaNonPagedPoolUsage",size),
                 ("PagefileUsage",size),("PeakPagefileUsage",size)]
    c=Counters();c.cb=ctypes.sizeof(c)
    okay=ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(c),c.cb)
    return int(c.PeakWorkingSetSize) if okay else None
