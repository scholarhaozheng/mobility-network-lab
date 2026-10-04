"""Bounded, sequential official-file retriever; no optional large archives."""
import csv
import hashlib
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RAW=ROOT/"raw"
RAW.mkdir(exist_ok=True)
MAX_BYTES=2_000_000_000
names={
 "TD_ROAD_CENTERLINE":"road_centerline.kmz", "TD_ROAD_TURN":"road_turn.kmz",
 "CENSUS_SSG":"census_ssg.zip", "CENSUS_STPUG":"census_stpug.zip",
 "TD_GTFS":"td_gtfs.zip", "TD_DETECTOR_INFO":"detector_info.csv",
 "TD_DETECTOR_RAW":"detector_raw.xml", "TD_SPEED_SEGMENTS":"speed_segments.csv",
}
reg=ROOT/"SOURCE_REGISTER.csv"
with reg.open(encoding="utf-8",newline="") as f:
 reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
for row in rows:
 sid=row["source_id"]
 if sid not in names: continue
 target=RAW/names[sid]
 legacy=ROOT/"detector_info.csv"
 if sid=="TD_DETECTOR_INFO" and legacy.exists() and not target.exists():
  legacy.replace(target)
 start=time.monotonic(); stamp=datetime.now(timezone.utc).isoformat(); status="ok"; error=""
 if not target.exists():
  temp=target.with_suffix(target.suffix+".part")
  try:
   req=urllib.request.Request(row["exact_data_resource_url"],headers={"User-Agent":"HongKongGMNSPilotR1/1.0"})
   with urllib.request.urlopen(req,timeout=90) as src,temp.open("wb") as out:
    n=0
    content_length=src.headers.get("Content-Length")
    if content_length and int(content_length)>MAX_BYTES: raise ValueError("2 GB per-source gate")
    while True:
     b=src.read(1024*1024)
     if not b: break
     n+=len(b)
     if n>MAX_BYTES: raise ValueError("2 GB per-source gate while streaming")
     out.write(b)
   temp.replace(target)
  except Exception as e:
   status="failed"; error=repr(e)
   if temp.exists(): temp.unlink()
 else: status="existing_verified"
 size=target.stat().st_size if target.exists() else 0
 with (ROOT/"DOWNLOAD_LOG.csv").open("a",encoding="utf-8",newline="") as f:
  csv.writer(f).writerow([sid,row["exact_data_resource_url"],stamp,status,size,round(time.monotonic()-start,3),error])
 if target.exists():
  row["retrieval_timestamp_utc"]=stamp; row["local_raw_file_path"]=str(target.relative_to(ROOT)); row["sha256"]=sha(target)
  with (ROOT/"RAW_FILE_MANIFEST.csv").open("a",encoding="utf-8",newline="") as f:
   csv.writer(f).writerow([sid,str(target.relative_to(ROOT)),size,row["sha256"],stamp])
 print(sid,status,size,error,flush=True)
with reg.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
