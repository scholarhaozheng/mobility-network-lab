"""Acquire pinned tap-b source, apply only recorded output-precision changes, build locally."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, urllib.request, zipfile
from pathlib import Path
COMMIT="040135a20c771fbb84766df6a97cff981fa5df4b"
URL="https://github.com/spartalab/tap-b/archive/"+COMMIT+".zip"
ARCHIVE_SHA="5163b43051457c5c72cfc53253db4fc3668524cd3a5190169c99d2606fc430a5"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,help="Optional already-downloaded pinned source archive")
    ap.add_argument("--compiler",default="cc",help="C compiler, or path to zig")
    ap.add_argument("--output",type=Path,default=Path(".mcl-runtime/tap-b"))
    args=ap.parse_args(); out=args.output.resolve()
    if out.exists() and any(out.iterdir()): raise ValueError("Build output must be new or empty")
    out.mkdir(parents=True,exist_ok=True)
    archive=args.archive.resolve() if args.archive else out/"tap-b-source.zip"
    if not args.archive:
        with urllib.request.urlopen(URL,timeout=90) as response: archive.write_bytes(response.read())
    if sha(archive)!=ARCHIVE_SHA: raise ValueError("Pinned source archive SHA256 mismatch")
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            target=(out/"source"/member.filename).resolve()
            if not target.is_relative_to(out/"source"): raise ValueError("Unsafe archive path")
        z.extractall(out/"source")
    source=out/"source"/("tap-b-"+COMMIT)
    patches=(("fileio.c",r'fprintf(outFile, "(%d,%d) %f \n",',r'fprintf(outFile, "(%d,%d) %.17g \n",',"6a52bc609f00da34bf5a1cd42b4e421b0bf39aa1c8cd58b3e09cc5848d5d2f3d"),
             ("bush.c",r'fprintf(pathFlowsFile, "] : %f\n", flowStack[pathLen]);',r'fprintf(pathFlowsFile, "] : %.17g\n", flowStack[pathLen]);',"608e030747330ad0ad1d26583b8071c268d51edaee063b0c555d90e1e4adde7d"))
    for name,old,new,expected in patches:
        p=source/"src"/name; text=p.read_text(encoding="utf-8")
        if text.count(old)!=1: raise ValueError("Unexpected precision patch context: "+name)
        p.write_text(text.replace(old,new),encoding="utf-8",newline="\n")
        if sha(p)!=expected: raise ValueError("Patched source hash mismatch: "+name)
    exe=out/("tap-b.exe" if os.name=="nt" else "tap-b")
    compiler=str(args.compiler); is_zig=Path(compiler).stem.lower()=="zig"
    command=[compiler]+(["cc"] if is_zig else [])
    if os.name=="nt" and is_zig: command += ["-target","x86_64-windows-gnu"]
    command += ["-O2","-DCLOCK_MONOTONIC_RAW=CLOCK_MONOTONIC","-I",str(source/"include")]
    command += [str(p) for p in sorted((source/"src").glob("*.c")) if p.name not in {"parallel_bush.c","thpool.c"}]
    command += ["-o",str(exe)]
    if os.name!="nt": command += ["-lm"]
    env=os.environ.copy(); env["ZIG_GLOBAL_CACHE_DIR"]=str(out/"compiler-cache")
    child=subprocess.run(command,cwd=out,capture_output=True,text=True,env=env,timeout=300)
    (out/"build.stdout.log").write_text(child.stdout,encoding="utf-8"); (out/"build.stderr.log").write_text(child.stderr,encoding="utf-8")
    report={"source_commit":COMMIT,"archive_sha256":ARCHIVE_SHA,"source_url":URL,"build_command":command,"exit_code":child.returncode,"platform":platform.platform(),"executable":exe.name,"executable_sha256":sha(exe) if exe.exists() else None,"patch_scope":"Two text-output format strings changed from %f to %.17g; serial compile compatibility macro. No mathematical algorithm changes.","source_sha256":{p.relative_to(source).as_posix():sha(p) for p in source.rglob("*") if p.is_file()}}
    (out/"build.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if child.returncode: raise SystemExit(child.returncode)
if __name__=="__main__": main()
