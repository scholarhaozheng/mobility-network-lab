from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,time,hashlib
R=Path(__file__).resolve().parent
cases=json.loads((R/'DEV18_ELEVEN_CASE_PRE_RUN.json').read_text(encoding='utf-8'))['cases']
out=R/'DEV18_ELEVEN_CASE_FRESH_REGRESSION.json'
rows=[];start=time.monotonic()
for case in cases:
 t=time.monotonic()
 proc=subprocess.run([sys.executable,'-B',str(R/'run_dev18_case_and_verify.py'),case],cwd=R,capture_output=True,text=True)
 receipt=R/'runs'/'sparse_common_dev18_demand_weighted_columns'/case/'DEV18_REGRESSION_RECEIPT.json'
 x=json.loads(receipt.read_text(encoding='utf-8')) if receipt.exists() else {}
 row={'case_id':case,'runner_exit_code':proc.returncode,'independent_status':x.get('independent_status'),'objective':x.get('independent_objective'),'gap':x.get('independent_gap'),'receipt':str(receipt) if receipt.exists() else None,'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest() if receipt.exists() else None,'elapsed_seconds':time.monotonic()-t,'stdout_tail':proc.stdout[-1000:],'stderr_tail':proc.stderr[-1000:]}
 rows.append(row)
 report={'schema':'SHARED_CG_DEV18_FRESH_11_CASE_REGRESSION_R1','created_utc':datetime.now(timezone.utc).isoformat(),'build_id':'sparse_common_dev18_demand_weighted_columns','rows':rows,'completed_cases':len(rows),'total_cases':len(cases),'status':'RUNNING' if len(rows)<len(cases) else ('PASS_ALL_11_FULL_GRAPH' if all(z['independent_status']=='PASS_FULL_GRAPH' for z in rows) else 'SOME_CASES_OPEN'),'wall_seconds':time.monotonic()-start}
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:row[k] for k in ('case_id','runner_exit_code','independent_status','objective','elapsed_seconds')},ensure_ascii=False),flush=True)
print(json.dumps({'status':report['status'],'completed_cases':len(rows),'wall_seconds':report['wall_seconds']}),flush=True)
