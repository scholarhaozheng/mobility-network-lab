from pathlib import Path
import json,hashlib,datetime
R=Path(r'E:\mobility_computation_lab_v2\work\shared_cg_cross_city_r1')
base=R/'cases'/'pittsburgh_S2_H__sparse_common_dev18_demand_weighted_columns_fullbatch6000.json'
prior_budget=R/'cases'/'pittsburgh_S2_H__sparse_common_dev18_fullbatch_continue60_budget_launch448.json'
new=R/'cases'/'pittsburgh_S2_H__sparse_common_dev18_fullbatch60_cold.json'
new_budget=R/'cases'/'pittsburgh_S2_H__sparse_common_dev18_fullbatch60_cold_budget.json'
design=R/'PIT_S2_H_DEV18_FULLBATCH60_COLD_PRE_RUN_DESIGN.json'
for p in (new,new_budget,design):
 if p.exists():raise FileExistsError(p)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads(base.read_text(encoding='utf-8-sig'));b=json.loads(prior_budget.read_text(encoding='utf-8-sig'))
assert c['phase_II_max_rounds']==30 and c['max_new_columns_per_round']==6000
c['phase_II_max_rounds']=60;c['output_dir']=str(R/'runs'/'sparse_common_dev18_demand_weighted_columns'/'pittsburgh_S2_H_fullbatch60_cold'/'solver')
c['algorithmic_batch_change']='Cold-start from original FIFO seed under same dev18 common source, full original 1406 OD x120 releases, 6000 full-priced novel paths/round, up to 60 computational rounds; scientific gap unchanged 1e-4'
b['algorithmic_batch_change']=c['algorithmic_batch_change'];b['science_policy']='Cold-start original H graph and demand, same capacities, costs, 30s dt and 1e-4 gap; 60-round computational ceiling, measured 3GiB private cap, 192MiB runtime free-memory stop and 448MiB launch floor'
new.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
new_budget.write_text(json.dumps(b,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
x={'schema':'PIT_S2_H_DEV18_FULLBATCH60_COLD_PRE_RUN_R1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_30_round_config':str(base),'parent_config_sha256':sha(base),'source_identity':str(R/'sparse_common_dev18_demand_weighted_columns'/'SOURCE_IDENTITY.json'),'source_identity_sha256':sha(R/'sparse_common_dev18_demand_weighted_columns'/'SOURCE_IDENTITY.json'),'new_config':str(new),'new_config_sha256':sha(new),'new_budget':str(new_budget),'new_budget_sha256':sha(new_budget),'science_model_unchanged':True,'cold_start':True,'no_saved_pool_or_dual_injected':True,'assessment':'Independent original graph primal and full pricing, plus pre-registered 0,0.25,0.5,0.75,1 mixing of last two complete dual snapshots if raw same-stage gap remains open. No 16/16 claim without all cases.'}
design.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'config':str(new),'budget':str(new_budget)}))
