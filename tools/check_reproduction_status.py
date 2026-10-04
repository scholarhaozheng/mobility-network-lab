"""Regression checks for receipt-backed reader status; no optimizer or network calls."""
from copy import deepcopy
from pathlib import Path
import argparse
import json
from build_recovered_docs import ROOT, read, load_fresh_evidence, validate_fresh_evidence
from build_reproduction_docs import reproduction_status, status_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated', action='store_true', help='Also check synchronized portal and JSON outputs')
    args = parser.parse_args()
    source = (ROOT / 'docs/assets/reproduction/data.js').read_text(encoding='utf-8')
    data = json.loads(source.removeprefix('window.MCL_REPRODUCTION=').strip().removesuffix(';'))
    records = {r['id']: r for r in data['records']}
    recovered = {r['id']: r for p in (ROOT / 'experiments/recovered').glob('*.json') for r in read(p).get('records', [])}
    fresh = load_fresh_evidence(recovered)
    resolved = {key: reproduction_status(record, recovered.get(key), fresh.get(key)) for key, record in records.items()}
    checks = {}
    checks['boston_lp_in_verified_filter'] = resolved['boston-finite-arc-flow-lp']['verified'] and resolved['boston-finite-arc-flow-lp']['key'] == 'verified_run'
    checks['query_in_verified_filter'] = resolved['TOOL-CITY-EVIDENCE-QUERY']['verified']
    checks['original_registered_commands_remain_verified'] = all(resolved[key]['verified'] for key, record in records.items() if record.get('recipe'))
    checks['no_saved_inspection_promoted_to_verified'] = all(not resolved[key]['verified'] for key in recovered if key not in fresh)
    checks['heavy_boston_cg_still_runnable_only'] = resolved['boston-finite-cg-pilot-r2-r3']['key'] == 'runnable'
    checks['hk_preparation_keeps_external_caveat'] = resolved['HK-BUILDING-ACTIVITY']['verified'] and resolved['HK-BUILDING-ACTIVITY']['externalInputsRequired']
    checks['external_input_unrun_not_verified'] = resolved['HK-GMNS-R1']['key'] == 'external_inputs' and not resolved['HK-GMNS-R1']['verified']
    checks['historical_failure_not_accepted'] = resolved['HK10-ADMM-R2-GATED']['key'] == 'no_accepted_experiment'
    checks['unperformed_experiment_not_accepted'] = resolved['boston-expanded-native-l3-all']['key'] == 'no_accepted_experiment'
    negative = [
        ('boston-finite-arc-flow-lp', lambda receipt: receipt.update(success=False)),
        ('boston-finite-arc-flow-lp', lambda receipt: receipt['verifierUpdate']['result']['checks'].update(objective=False)),
        ('HK-BUILDING-ACTIVITY', lambda receipt: receipt.update(freshComputation=False)),
        ('HK-H1-FW', lambda receipt: receipt['verification'].update(optimizer_calls=1)),
        ('sioux-admm-r1-200', lambda receipt: receipt.update(source_input_hashes_verified=False)),
        ('TOOL-CITY-EVIDENCE-QUERY', lambda receipt: receipt.update(exitCode=1)),
    ]
    for index, (key, mutate) in enumerate(negative):
        receipt = read(ROOT / recovered[key]['evidenceReceipt'])
        mutate(receipt)
        try:
            validate_fresh_evidence(recovered[key], fresh[key], receipt)
            rejected = False
        except ValueError:
            rejected = True
        checks['invalid_execution_or_verification_rejected_' + str(index + 1)] = rejected
    for key in ('boston-finite-arc-flow-lp', 'HK-BUILDING-ACTIVITY'):
        copy = deepcopy(recovered[key])
        copy['state'] = 'historical_failure'
        try:
            validate_fresh_evidence(copy, fresh[key], read(ROOT / copy['evidenceReceipt']))
            rejected = False
        except ValueError:
            rejected = True
        checks['failed_scientific_scope_rejected_' + key] = rejected
    if args.generated:
        checks['portal_matches_resolved_status'] = all(record.get('reproductionStatus') == resolved[key] and record['auditStatus'] == resolved[key]['key'] and record['auditLabel'] == resolved[key]['label'] for key, record in records.items())
        checks['summary_matches_records'] = data.get('statusSummary') == status_summary(list(records.values()))
        ledgers = [read(ROOT / p) for p in ('experiments/reproduction-status.json', 'docs/assets/reproduction/reproduction-status.json')]
        checks['ledger_copies_identical'] = ledgers[0] == ledgers[1]
        checks['ledger_current_fields_match_portal'] = all(record.get('reproductionStatus') == resolved[record['id']] and record['status'] == resolved[record['id']]['key'] and record['statusLabel'] == resolved[record['id']]['label'] and record['receiptUrl'] == resolved[record['id']]['receiptUrl'] for record in ledgers[0]['records'])
        query = next(record for record in ledgers[0]['records'] if record['id'] == 'TOOL-CITY-EVIDENCE-QUERY')
        checks['query_stale_registration_requirement_removed'] = query['remainingRequirements'] == [] and bool(query['commands']['run'])
        checks['original_audit_retained_separately'] = 'historicalAuditSummary' in ledgers[0] and all('historicalAudit' in r for r in ledgers[0]['records'])
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({'status': 'FAIL' if failed else 'PASS', 'checks': len(checks), 'failed': failed,
                      'verifiedRecords': sum(value['verified'] for value in resolved.values()), 'freshRecoveredWorkflows': len(fresh),
                      'optimizerCalls': 0, 'networkCalls': 0}, indent=2))
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
