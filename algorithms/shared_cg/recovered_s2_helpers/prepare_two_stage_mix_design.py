from pathlib import Path
import json,hashlib,datetime
R=Path(r'E:\mobility_computation_lab_v2\work\shared_cg_cross_city_r1')
p=R/'PIT_S2_H_TWO_STAGE_DUAL_MIX_PRE_RUN.json'
if p.exists():raise FileExistsError(p)
ver=R/'verify_two_stage_dual_mix.py';sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
x={'schema':'PIT_S2_H_TWO_STAGE_DUAL_MIX_PRE_RUN_R1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'CONDITIONAL_NOT_EXECUTED','condition':'Only if 30-to-60-round warm continuation reaches a solved original-primal-feasible stage and remains above frozen relative gap 1e-4. Use its last two distinct complete hash-checked 3-round stage snapshots.','alpha_grid':[0.0,0.25,0.5,0.75,1.0],'dual_rule':'convex combination of two nonpositive original physical time-entry capacity RMP dual vectors; each lower bound independently repriced over every original physical, turn, wait, sink arc and all 168720 releases','upper_rule':'independently verified original-graph primal from same original case, any solved stage; no equality with dual stage required','independent_verifier':str(ver),'independent_verifier_sha256':sha(ver),'science_tolerance_unchanged':1e-4,'claim_limit':'If this certifies gap under 1e-4, warm development closure still requires cold-start same-build regression before final count.'}
p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(p)
