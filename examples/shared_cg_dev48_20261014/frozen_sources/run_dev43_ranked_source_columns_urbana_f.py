"""Cold full-demand Urbana Q restricted master with source-ranked original paths.

Every original OD and release remains on the independently certified FIFO base.
The ranking limits *new columns*, not demand. A fresh path is recovered for each
selected source fragment; identical OD/release fragments share one exact
fractional group and one common physical-time capacity master.
"""
from pathlib import Path
import hashlib
import json
import os
import sys
import time
import numpy as np
from scipy import sparse

R = Path(__file__).resolve().parent
CORE = R / 'sparse_common_dev42_source_bundle_cg'
sys.path.insert(0, str(CORE))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates
from shared_cg.joint_cg_loop import JointState
from run_dev42_source_bundle_urbana_f import build

DESIGN = R / 'DEV43_RANKED_SOURCE_COLUMNS_DESIGN.json'
CFG = R / 'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
SEED = R / 'runs/dev35_cold_source_seed_urbana_f'
OUT = R / 'runs/dev43_ranked_source_columns_urbana_f'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.partial')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def main():
    begun = time.monotonic()
    design = read(DESIGN)
    cfg = read(CFG)
    seed = read(SEED / 'RECEIPT.json')
    for path, key in ((CFG, 'source_config_sha256'),
                      (SEED / 'RECEIPT.json', 'fresh_seed_receipt_sha256'),
                      (R / 'run_dev42_source_bundle_urbana_f.py', 'builder_sha256')):
        if sha(path) != design[key]:
            raise ValueError('frozen source or builder drift: ' + str(path))
    if sha(Path(__file__)) != design['runner_sha256']:
        raise ValueError('frozen runner drift')
    for name, wanted in design['core_module_sha256'].items():
        if sha(CORE / 'shared_cg' / name) != wanted:
            raise ValueError('common core drift: ' + name)
    if seed['status'] != 'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED':
        raise ValueError('missing independent source-only base')
    model = ImplicitTimeGraph(cfg['source_dir'], cfg['dt_seconds'], cfg['horizon_steps'],
                              cfg['release_steps'], cfg['demand_factor'])
    if model.source_hashes != cfg['expected_source_hashes'] or model.K != design['original_release_events']:
        raise ValueError('original source/model identity')
    aon = SEED / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
    fifo = SEED / 'fifo/FRAGMENTS.npz'
    if sha(aon) != seed['AON_path_sha256'] or sha(fifo) != seed['FIFO_fragment_sha256']:
        raise ValueError('source-only base arrays drift')
    base = FullUniformQBase(model, aon, fifo)
    bridge = SourceBridgePrefixCandidates(model, base)
    if bridge.edge != design['source_bridge_original_edge']:
        raise ValueError('source selected bridge drift')
    policy = design['algorithm_policy']
    eligible = np.asarray(bridge.eligible, dtype=np.int32)
    eligible = eligible[bridge.saving[eligible] > policy['minimum_source_raw_saving_minutes']]
    score = np.asarray(base.fm[eligible] * bridge.saving[eligible], np.float64)
    if len(eligible) != design['source_positive_fragments'] or not np.all(np.isfinite(score)):
        raise ValueError('source candidate screen drift')
    rank = np.lexsort((eligible, -score))
    nselect = min(int(policy['maximum_new_source_fragments']), len(eligible))
    selected = eligible[rank[:nselect]]
    if len(np.unique(selected)) != nselect:
        raise ValueError('duplicate selected fragment')
    bridge.eligible = selected
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'RESULT.json').exists() or (OUT / 'STAGE.json').exists():
        raise FileExistsError('ranked master already started; inspect its receipt')
    A, payload, count = build(model, base, bridge, policy)
    if count != nselect:
        raise ValueError('selected source columns omitted')
    matrix_file = OUT / 'BUNDLE_MATRIX.npz'
    paths_file = OUT / 'BUNDLE_SOURCE_PATHS.npz'
    sparse.save_npz(matrix_file.with_suffix('.partial.npz'), A)
    os.replace(matrix_file.with_suffix('.partial.npz'), matrix_file)
    payload['selected_fragment_score'] = np.asarray(base.fm[payload['fragment_index']] *
                                                    bridge.saving[payload['fragment_index']], np.float64)
    np.savez_compressed(paths_file.with_suffix('.partial.npz'), **payload)
    os.replace(paths_file.with_suffix('.partial.npz'), paths_file)
    stage = {
        'schema': 'DEV43_RANKED_SOURCE_COLUMNS_STAGE',
        'status': 'RANKED_SOURCE_RMP_INPUT_READY',
        'design_sha256': sha(DESIGN),
        'matrix_sha256': sha(matrix_file),
        'source_paths_sha256': sha(paths_file),
        'original_source_positive_fragments': len(eligible),
        'selected_source_fragments': count,
        'selection_unconstrained_source_saving_PCE_minutes': float(np.sum(score[rank[:nselect]])),
        'bundle_count': A.shape[1],
        'capacity_rows': A.shape[0],
        'matrix_nnz': A.nnz,
        'build_seconds': time.monotonic() - begun,
    }
    save(OUT / 'STAGE.json', stage)
    print(json.dumps(stage), flush=True)
    n = A.shape[1]
    state = JointState(A, payload['original_capacity_rows'], payload['residual_capacity'],
                       payload['bundle_weighted_delta_cost'], np.arange(n, dtype=np.int32),
                       np.ones(n), list(range(n)), list(map(str, payload['bundle_signature'])),
                       base.residual_capacity)
    solved = state.solve(float(design['resources']['RMP_seconds']))
    if solved.max_capacity_excess > 1e-8 or solved.max_group_excess > 1e-8:
        raise ValueError('restricted RMP infeasible')
    np.savez_compressed(OUT / 'BUNDLE_RMP_SOLUTION.npz',
                        bundle_fraction=solved.y,
                        original_capacity_rows=payload['original_capacity_rows'],
                        capacity_mu=solved.capacity_mu, bundle_mu=solved.group_mu)
    result = {
        'schema': 'DEV43_FULL_ORIGINAL_RANKED_SOURCE_RESTRICTED_RMP',
        'status': 'RESTRICTED_BUNDLE_PRIMAL_PENDING_INDEPENDENT_ORIGINAL_REPLAY',
        'case_id': cfg['case_id'], 'build_id': design['core_build_id'],
        'source_hashes': model.source_hashes,
        'design_sha256': sha(DESIGN), 'runner_sha256': sha(Path(__file__)),
        'fresh_seed_receipt_sha256': sha(SEED / 'RECEIPT.json'),
        'original_positive_OD': len(model.od),
        'original_release_events': model.K,
        'source_bridge_original_edge': bridge.edge,
        'original_source_positive_fragments': len(eligible),
        'source_positive_fragments': count,
        'disjoint_bundle_count': n,
        'bundle_positive_variables': int(np.count_nonzero(solved.y > 1e-10)),
        'bundle_member_positive_fragments': int(np.count_nonzero(solved.y[payload['bundle_id']] > 1e-10)),
        'original_capacity_rows': A.shape[0], 'matrix_nnz': A.nnz,
        'restricted_delta': solved.objective_delta,
        'candidate_upper_pending_independent_replay': float(seed['independent_feasible_upper'] + solved.objective_delta),
        'max_touched_capacity_excess': solved.max_capacity_excess,
        'restricted_RMP_iterations': solved.iterations,
        'matrix_sha256': sha(matrix_file),
        'source_paths_sha256': sha(paths_file),
        'solution_sha256': sha(OUT / 'BUNDLE_RMP_SOLUTION.npz'),
        'wall_seconds': time.monotonic() - begun,
        'historical_best_upper_evaluation_only': design['historical_best_evaluation_only']['upper'],
        'scientific_limit': 'Full original demand is served; ranked source candidates form a restricted master only. Full graph CG optimality remains open.',
    }
    save(OUT / 'RESULT.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'source_positive_fragments',
                                             'disjoint_bundle_count', 'bundle_positive_variables',
                                             'candidate_upper_pending_independent_replay',
                                             'wall_seconds')}), flush=True)


if __name__ == '__main__':
    main()
