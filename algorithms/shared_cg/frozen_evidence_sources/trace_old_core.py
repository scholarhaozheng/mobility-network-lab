"""Lightweight actual-import and key-call trace for legacy shared CG runs.

This wrapper changes no numerical arguments or implementation. It counts a
small set of function entries by wrapping module globals, then records actual
loaded local modules and their file hashes at solver exit.
"""
from pathlib import Path
import functools,hashlib,importlib,json,os,sys,time

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def save(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(".json.tmp")
 tmp.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
 os.replace(tmp,path)

def main():
 if len(sys.argv)<4 or sys.argv[1]!="--core-source-root":
  raise ValueError("expected --core-source-root PATH then the unchanged core CLI")
 src=Path(sys.argv[2]).resolve()
 argv=sys.argv[3:]
 if "--output-dir" not in argv:raise ValueError("missing old core output-dir")
 output=Path(argv[argv.index("--output-dir")+1]).resolve()
 sys.path.insert(0,str(src))
 core=importlib.import_module("run_full_cg_v1")
 tracked=("run_full_cg_v1","run_phase_i","solve_phase1_pool",
          "run_phase_i_oracle","run_phase_ii_loop",
          "run_phase_ii_oracle_probes","k_shortest_phase_ii_paths")
 calls={name:0 for name in tracked if hasattr(core,name)}
 for name in calls:
  original=getattr(core,name)
  @functools.wraps(original)
  def wrap(*args,_name=name,_original=original,**kwargs):
   calls[_name]+=1
   return _original(*args,**kwargs)
  setattr(core,name,wrap)
 sys.argv=[str(src/"run_full_cg_v1.py")]+argv
 started=time.monotonic();status="EXCEPTION";exit_code=2
 try:
  exit_code=core.main()
  status="RETURNED"
  return exit_code
 finally:
  loaded={}
  for name,module in sorted(sys.modules.items()):
   location=getattr(module,"__file__",None)
   if not location:continue
   path=Path(location).resolve()
   try:path.relative_to(src)
   except ValueError:continue
   if path.is_file():
    loaded[name]={"path":str(path),"sha256":sha(path)}
  save(output/"ACTUAL_CALL_TRACE.json",{
   "schema":"SHARED_CG_ACTUAL_CALL_TRACE_R1",
   "core_source_root":str(src),"core_entry":str(src/"run_full_cg_v1.py"),
   "actual_local_import_modules":loaded,"tracked_function_calls":calls,
   "trace_status":status,"core_exit_code":exit_code,
   "wall_seconds":time.monotonic()-started,
   "policy":"entry wrappers count calls only; unchanged core numerical arguments"})
if __name__=="__main__":raise SystemExit(main())
