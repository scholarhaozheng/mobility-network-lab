"""Export V1 plotting inputs from one actual local CG run, without solving.

Only geometry and display units are reused from the published case. Flows,
history, objectives and certificates must come from the supplied workspace.
"""
from pathlib import Path
import argparse,copy,csv,json,math,shutil
from cg_result_projection import read,sha,regular,uniform,joint

REPO=Path(__file__).resolve().parents[2]
DOCS=REPO/'docs'

def require(ok,message):
    if not ok:raise ValueError(message)

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')

def first(obj,names):
    for name in names:
        value=obj.get(name)
        if value is not None:return float(value)
    return None

def bind_actual_outputs(receipt,files):
    """Tie every decoded state to the finished execution, not just its cost."""
    bindings=receipt.get('new_outputs',{})
    require(bool(bindings),'Missing execution output hashes; saved flow cannot be attributed to this run.')
    by_path={Path(item['path']).resolve():item['sha256']for item in bindings.values()}
    for file in files:
        path=Path(file).resolve()
        require(path.is_file()and by_path.get(path)==sha(path),
                'Actual output is not bound to this execution: '+str(path))

def export(index_path,output):
    index_path=index_path.resolve();output=output.resolve();idx=read(index_path)
    require(not output.is_relative_to(REPO),'Export outside the maintained source repository.')
    require(not output.exists()or not any(output.iterdir()),'Use a new empty plot-data output directory.')
    paths=idx['paths'];cid=idx['case_id'];branch=idx['branch']
    for key in ['config','result','independent_certificate']:
        require(key in paths and Path(paths[key]).is_file(),'Missing actual-run output: '+key)
    receipt_path=index_path.parent/'NEW_RUN.json'
    require(receipt_path.is_file(),'Missing NEW_RUN.json execution binding; no historical certificate is substituted.')
    receipt=read(receipt_path)
    require(receipt['case_id']==cid and receipt['new_result_sha256']==sha(paths['result'])and
            receipt['execution_config_sha256']==sha(paths['config']),'Actual execution receipt/config/result SHA mismatch.')
    require(receipt.get('independent_verification')=='PASSED_WITHIN_REPORTED_SCOPE','This execution has not completed its independent verification.')
    def bound_certificate(key,path):
        binding=receipt.get('new_certificates',{}).get(key)
        require(binding is not None and Path(binding['path']).resolve()==Path(path).resolve()and binding['sha256']==sha(path),
                'Certificate is not bound by this execution receipt: '+key)
    bound_certificate('independent_certificate',paths['independent_certificate'])
    state_files=[Path(path)for path in paths.values()if Path(path).is_file()]
    bind_actual_outputs(receipt,state_files)
    if paths.get('latest_checkpoint')and Path(paths['latest_checkpoint']).is_file():
        checkpoint=read(paths['latest_checkpoint'])
        bind_actual_outputs(receipt,[checkpoint['pool_path'],checkpoint['rmp_path']])
    if branch=='joint':
        seed_certificate=Path(paths['uniform_paths']).parent.parent/'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json'
        bind_actual_outputs(receipt,[seed_certificate])
    cfg=read(paths['config']);result=read(paths['result']);cert=read(paths['independent_certificate'])
    if branch=='joint'and 'fresh_seed_certificate_sha256'in cert:
        require(cert['fresh_seed_certificate_sha256']==sha(seed_certificate),'Joint certificate uses another source-seed certificate.')
    require(cfg['case_id']==cid,'Configuration case does not match workspace index.')
    if 'config_sha256'in result:require(result['config_sha256']==sha(paths['config']),'Result/config SHA mismatch.')
    if 'producer_result_sha256'in cert:require(cert['producer_result_sha256']==sha(paths['result']),'Primal certificate/result SHA mismatch.')
    require(cert.get('status','').startswith('PASS'),'The actual run has no passing original-space primal certificate.')
    registered=next(c for c in read(REPO/'examples/shared_cg_dev48_20261014/cases.json')['cases']if c['case_id']==cid)
    require(branch==registered['branch'],'Workspace branch does not match the registered case.')
    frozen_cfg=read(REPO/'examples/shared_cg_dev48_20261014'/registered['config_file'])
    relocated={'source_dir','core_root','output_dir','input_manifest','feasible_fifo_seed_npz','expected_seed_sha256'}
    require(all(cfg.get(k)==v for k,v in frozen_cfg.items()if k not in relocated),
            'Numerical model/algorithm configuration differs from the registered case; fixed display metadata must not be reused.')
    expected=registered['expected_inputs']
    if branch=='explicit':
        manifest=read(cfg['input_manifest']);inputs={Path(v).name:Path(v)for k,v in manifest.items()if k in ['dynamic_arc_file','demand_file']}
    else:inputs={name:Path(cfg['source_dir'])/name for name in expected}
    require({name:sha(inputs[name])for name in expected}==expected,'Model inputs differ from this case; the published geometry cannot be assumed compatible.')
    cert_sources=cert.get('source_hashes',cert.get('original_source_hashes'))
    require(cert_sources==expected,'Certificate is not bound to the actual model inputs.')
    current=read(DOCS/'assets/shared-cg-dev48-20261014/catalog.json')
    reference=next(c for c in current['cases']if c['case_id']==cid)
    metadata=['case_id','city','city_name','OD','events','scale','dt_seconds','release_steps','horizon_steps','objective_unit','code_package','solver_branch','actual_adapter']
    c={key:reference[key]for key in metadata};c['paths']=paths
    for source_key,display_key in [('dt_seconds','dt_seconds'),('release_steps','release_steps'),('horizon_steps','horizon_steps'),('demand_factor','scale')]:
        if source_key in cfg:c[display_key]=cfg[source_key]
    decoder=joint if branch=='joint'else uniform if branch=='uniform'else regular
    flow,U,metrics,used=decoder(c,cfg)
    bind_actual_outputs(receipt,used)
    certU=first(cert,['original_objective','original_primal_objective','independent_full_original_feasible_upper'])
    require(certU is not None and abs(U-certU)<=max(1e-6,abs(certU)*1e-10),'Projected cost differs from the actual-run primal certificate.')
    lower_record=cert;lower_path=Path(paths['independent_certificate'])
    if paths.get('mixed_certificate')and Path(paths['mixed_certificate']).is_file():
        bound_certificate('mixed_certificate',paths['mixed_certificate'])
        lower_path=Path(paths['mixed_certificate']);lower_record=read(lower_path)
        require(lower_record['config_sha256']==sha(paths['config']),'Mixed-bound/config SHA mismatch.')
        require(lower_record['independent_primal_certificate_sha256']==sha(paths['independent_certificate']),'Mixed bound belongs to another primal certificate.')
    elif branch=='joint':
        lower_path=Path(paths.get('full_price_certificate',Path(paths.get('full_price_directory',Path(paths['result']).parent/'FULL_PRICE'))/'INDEPENDENT_DUAL_CERT.json'))
        lower_record=read(lower_path)if lower_path.exists()else {}
        if lower_record:
            bound_certificate('full_price_certificate',lower_path)
            require(lower_record['RMP_independent_cert_sha256']==sha(paths['independent_certificate']),'Full-pricing bound belongs to another RMP.')
            require(lower_record['producer_result_sha256']==sha(lower_path.parent/'RESULT.json'),'Full-pricing result SHA mismatch.')
            require(lower_record['source_hashes']==expected,'Full-pricing bound has other inputs.')
    L=first(lower_record,['verified_full_graph_lower_bound','verified_full_graph_dual_lower_bound','independent_full_graph_lower_bound','best_certified_lower','independent_full_original_lower'])
    gap=None if L is None else(certU-L)/max(abs(certU),1e-12)
    c.pop('paths');c.update(new_run_plot_inputs=True,run_id='local-'+index_path.parent.name,source_dir='records/'+cid,U=certU,L=L,gap_raw=gap,
        accepted_at_frozen_gate=branch!='joint'and gap is not None and abs(gap)<=float(cfg.get('relative_gap_tolerance',1e-4))+1e-10,
        raw_last_minimum_reduced_cost=result.get('last_pricing',{}).get('minimum_reduced_cost'),
        raw_pricing_status='NOT_ESTABLISHED',model_id='LOCAL_RUN_SEE_CONFIG_AND_SOURCE_HASHES')
    rc=c['raw_last_minimum_reduced_cost']
    if rc is not None:c['raw_pricing_status']='MET'if rc>=-1e-6 else'UNMET'
    if paths.get('model_identity')and Path(paths['model_identity']).exists():c['model_identity_record']=read(paths['model_identity'])
    folder=output/c['source_dir'];folder.mkdir(parents=True)
    shutil.copyfile(paths['result'],folder/'result.json');shutil.copyfile(paths['config'],folder/'config.json')
    shutil.copyfile(paths['independent_certificate'],folder/'upper-certificate.json')
    if L is not None:shutil.copyfile(lower_path,folder/'lower-certificate.json')
    base_map=next(f for f in reference['figures']if f['id'].endswith('physical-flow'))
    geometry_path=DOCS/base_map['data'];geometry=copy.deepcopy(read(geometry_path)['geometry']);ids=sorted(flow)
    require(set(ids)<=set(geometry['link_geometry']),'Missing same-case physical-link geometry.')
    geometry['link_geometry']={i:geometry['link_geometry'][i]for i in ids}
    geometry['geometry_only_reuse']={'path':str(geometry_path),'sha256':sha(geometry_path),'fields':['geometry'],'old_flows_read_as_inputs':False}
    sources=[receipt_path,Path(paths['config']),Path(paths['result']),Path(paths['independent_certificate']),*inputs.values(),*used]
    if L is not None:sources.append(lower_path)
    provenance={'case_id':cid,'run_id':c['run_id'],'source_index':str(index_path),'source_index_sha256':sha(index_path),
        'actual_run_sources':[{'path':str(p),'sha256':sha(p)}for p in dict.fromkeys(sources)],
        'historical_flows_or_certificates_used':False,'solver_calls':0,'pricing_calls':0,
        'scope':'Path/flow projection and existing actual-run certificate binding; no new full-graph pricing or optimization.'}
    rows=[{'physical_link_id':i,'integrated_flow':flow[i]}for i in ids]
    unit='native volume'if c['city']=='sioux-falls'else'vehicles'if c['city']=='hong-kong'else'PCE'
    data={'case_id':cid,'run_id':c['run_id'],'city':c['city'],'physical_flow_unit':unit,'aggregation':'Integrated movement across all releases and the full arrival tail',
        'projected_U':U,'certificate_U':certU,'U_residual':U-certU,'metrics':metrics,'rows':rows,'geometry':geometry,'provenance':provenance}
    write(folder/'physical-flow.plot.json',data)
    with(folder/'physical-flow.csv').open('w',encoding='utf8',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=['physical_link_id','integrated_flow']);writer.writeheader();writer.writerows(rows)
    h1=[h for h in result.get('history',[])if h.get('phase')=='I'];h2=[h for h in result.get('history',[])if h.get('phase')=='II']
    write(folder/'phase-i-combined.plot.json',{'round':[h['round']for h in h1],'total_artificial_capacity_slack':[h['artificial_mass']for h in h1],
        'unit':unit,'absence_reason':None if h1 else'Phase I was not executed; see actual seed/exact-construction records.'})
    if branch=='joint':
        rounds=result['round_history'];endpoint=float(result['candidate_upper_pending_independent_replay'])
        require(abs(endpoint-U)<=max(1e-6,abs(U)*1e-10),'Final saved RMP objective differs from its projected paths.')
        objective=[result['fresh_source_base_upper']+h['restricted_delta']for h in rounds]+[endpoint]
        positions=[h['round']for h in rounds]+[max(h['round']for h in rounds)+1]
        labels=['CG '+str(h['round'])for h in rounds]+['Final'];c['saved_cg_rounds']=len(rounds)
    elif h2:objective=[h['true_primal_objective']for h in h2];positions=[h['round']for h in h2];labels=None
    elif branch=='uniform':objective=[U];positions=[1];labels=None
    else:raise ValueError('No Phase II history was saved; no endpoint sequence is fabricated.')
    write(folder/'phase-ii-pair.plot.json',{'position':positions,'round':positions,'objective':objective,'labels':labels,'fixed_reference':L,
        'unit':c['objective_unit'],'saved_cg_rounds':c.get('saved_cg_rounds'),'reference_scope':'This actual run only; absent bound remains null.'})
    write(folder/'run-provenance.json',provenance)
    report={'status':'ACTUAL_RUN_PROJECTION_PASSED','case_id':cid,'run_id':c['run_id'],'projected_U':U,'certificate_U':certU,'objective_residual':U-certU,
        'L':L,'gap_raw':gap,'geometry_links':len(ids),'metrics':metrics,'phase_i_saved_states':len(h1),'phase_ii_saved_states':len(objective),
        'full_graph_bound_scope':'Existing actual-run certificate only'if L is not None else'NOT_ESTABLISHED','solver_calls':0,'pricing_calls':0}
    write(folder/'projection-checks.json',report)
    c['figures']=[{'id':'cg-local-'+cid+'-physical-flow','src':c['source_dir']+'/physical-flow.svg','png':c['source_dir']+'/physical-flow.png',
        'data':c['source_dir']+'/physical-flow.plot.json','source':c['source_dir']+'/run-provenance.json'}]
    write(output/'catalog.json',{'schema':'CG_ACTUAL_LOCAL_RUN_PLOT_INPUTS_V1','code_package':c['code_package'],'cases':[c]})
    write(output/'EXPORT_REPORT.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True,type=Path,help='run.py output directory containing WORKSPACE_INDEX.json')
    parser.add_argument('--output',required=True,type=Path,help='New empty plotting-input directory outside the repository')
    args=parser.parse_args();print(json.dumps(export(args.run/'WORKSPACE_INDEX.json',args.output),indent=2))

if __name__=='__main__':main()
