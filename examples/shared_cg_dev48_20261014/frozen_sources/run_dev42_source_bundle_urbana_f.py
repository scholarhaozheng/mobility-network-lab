"""Exact source-only path bundles on the full original Urbana Q demand.

A bundle variable moves the same fraction of each of its disjoint original
FIFO fragments from its base path to a legal alternate path. Every fragment
remains explicit in the saved unbundling map. This is a restricted primal
candidate, and full-graph CG optimality is not asserted here.
"""
from pathlib import Path
from collections import Counter, defaultdict
from array import array
import hashlib, json, os, sys, time
import numpy as np
from scipy import sparse

R = Path(__file__).resolve().parent
CORE = R / 'sparse_common_dev42_source_bundle_cg'
sys.path.insert(0, str(CORE))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates
from shared_cg.joint_cg_loop import JointState

DESIGN = R / 'DEV42_SOURCE_BUNDLE_JOINT_RMP_DESIGN.json'
CFG = R / 'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
SEED = R / 'runs/dev35_cold_source_seed_urbana_f'
OUT = R / 'runs/dev42_source_bundle_joint_rmp_urbana_f'


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


def pattern_arrays(patterns):
    offsets = [0]
    edges = []
    times = []
    costs = []
    for edge, rel, raw in patterns:
        edges.extend(map(int, edge))
        times.extend(map(int, rel))
        offsets.append(len(edges))
        costs.append(float(raw))
    return {
        'pattern_edge_offset': np.asarray(offsets, np.int64),
        'pattern_original_edge': np.asarray(edges, np.int32),
        'pattern_entry_offset': np.asarray(times, np.int32),
        'pattern_unit_cost': np.asarray(costs, np.float64),
    }


def build(model, base, bridge, policy):
    block = int(policy['release_bundle_steps'])
    positive = bridge.eligible[bridge.saving[bridge.eligible] > float(policy['minimum_source_raw_saving_minutes'])]
    groups = defaultdict(list)
    for f0 in positive:
        f = int(f0)
        groups[(int(base.fod[f]), int(base.fr[f]) // block)].append(f)
    if not groups or sum(map(len, groups.values())) != len(positive):
        raise ValueError('source fragment partition')
    keys = sorted(groups)
    patterns = []
    pattern_by_key = {}
    member_f = array('i')
    member_b = array('i')
    member_p = array('i')
    all_row = array('q')
    all_col = array('i')
    all_value = array('d')
    costs = []
    signatures = []
    H = model.H
    for b, (od, window) in enumerate(keys):
        delta = defaultdict(float)
        weighted = 0.0
        digest = hashlib.sha256()
        digest.update(np.asarray([od, window], np.int32).tobytes())
        for f in groups[(od, window)]:
            if int(base.fod[f]) != od or int(base.fr[f]) // block != window:
                raise ValueError('bundle fragment identity')
            after = bridge.od_route[od][3]
            pattern_key = (od, int(bridge.delay[f]),
                           tuple(int(x) for x in base.fw[f, list(after)]))
            p = pattern_by_key.get(pattern_key)
            if p is None:
                edge, entry, raw = bridge.recover(f)
                rel = entry.astype(np.int64) - int(base.fr[f])
                if np.any(rel < 0) or np.any(rel >= H):
                    raise ValueError('original alternate time path')
                p = len(patterns)
                pattern_by_key[pattern_key] = p
                patterns.append((edge.copy(), rel.astype(np.int32), float(raw)))
            edge, rel, raw = patterns[p]
            if abs(raw - float(bridge.candidate_unit[f])) > 1e-7:
                raise ValueError('canonical source path cost drift')
            release = int(base.fr[f])
            after_rows = Counter(int(model.physical_pos[int(e)]) * H + release + int(t)
                                 for e, t in zip(edge, rel) if model.physical_pos[int(e)] >= 0)
            before_rows = base.base_rows(f)
            mass = float(base.fm[f])
            for row in after_rows.keys() | before_rows.keys():
                delta[int(row)] += mass * (after_rows[row] - before_rows[row])
            weighted += mass * (raw - float(base.donor_cost[f]))
            member_f.append(f)
            member_b.append(b)
            member_p.append(p)
            digest.update(np.asarray([f, p], np.int32).tobytes())
        if weighted >= -1e-12:
            raise ValueError('bundle has no positive raw saving')
        for row, value in delta.items():
            if abs(value) <= 1e-15:
                continue
            all_row.append(int(row))
            all_col.append(b)
            all_value.append(float(value))
        costs.append(weighted)
        signatures.append(digest.hexdigest())
        if (b + 1) % 1000 == 0:
            print(json.dumps({'bundles_built': b + 1, 'of': len(keys),
                              'members': len(member_f), 'patterns': len(patterns),
                              'raw_coefficient_entries': len(all_row)}), flush=True)
    if len(member_f) != len(positive) or len(set(member_f)) != len(positive):
        raise ValueError('missing or repeated original fragment in disjoint bundles')
    original = np.frombuffer(all_row, dtype=np.int64)
    col = np.frombuffer(all_col, dtype=np.int32)
    val = np.frombuffer(all_value, dtype=np.float64)
    rows, inverse = np.unique(original, return_inverse=True)
    A = sparse.coo_matrix((val, (inverse, col)), shape=(len(rows), len(keys))).tocsr()
    A.sum_duplicates()
    rhs = base.residual_capacity(rows)
    payload = {
        'fragment_index': np.frombuffer(member_f, dtype=np.int32).copy(),
        'bundle_id': np.frombuffer(member_b, dtype=np.int32).copy(),
        'pattern_id': np.frombuffer(member_p, dtype=np.int32).copy(),
        'bundle_original_od': np.asarray([key[0] for key in keys], np.int32),
        'bundle_release_window': np.asarray([key[1] for key in keys], np.int32),
        'bundle_weighted_delta_cost': np.asarray(costs, np.float64),
        'bundle_signature': np.asarray(signatures, dtype='U64'),
        'original_capacity_rows': rows,
        'residual_capacity': rhs,
    }
    payload.update(pattern_arrays(patterns))
    return A, payload, len(positive)


def main():
    began = time.monotonic()
    design = read(DESIGN)
    cfg = read(CFG)
    seed = read(SEED / 'RECEIPT.json')
    if sha(CFG) != design['source_config_sha256'] or sha(SEED / 'RECEIPT.json') != design['fresh_seed_receipt_sha256']:
        raise ValueError('frozen original input/seed drift')
    if sha(Path(__file__)) != design['runner_sha256']:
        raise ValueError('frozen bundle runner drift')
    for name, wanted in design['core_module_sha256'].items():
        if sha(CORE / 'shared_cg' / name) != wanted:
            raise ValueError('frozen common core drift ' + name)
    if seed['status'] != 'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED':
        raise ValueError('independent source-only seed missing')
    model = ImplicitTimeGraph(cfg['source_dir'], cfg['dt_seconds'], cfg['horizon_steps'],
                              cfg['release_steps'], cfg['demand_factor'])
    if model.source_hashes != cfg['expected_source_hashes'] or model.K != design['original_release_events']:
        raise ValueError('original source/model identity')
    aon = SEED / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
    fifo = SEED / 'fifo/FRAGMENTS.npz'
    if sha(aon) != seed['AON_path_sha256'] or sha(fifo) != seed['FIFO_fragment_sha256']:
        raise ValueError('source-only path assets drift')
    base = FullUniformQBase(model, aon, fifo)
    bridge = SourceBridgePrefixCandidates(model, base)
    if bridge.edge != design['source_bridge_original_edge']:
        raise ValueError('source-selected bridge edge drift')
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'RESULT.json').exists():
        raise FileExistsError(OUT / 'RESULT.json')
    matrix_file = OUT / 'BUNDLE_MATRIX.npz'
    payload_file = OUT / 'BUNDLE_SOURCE_PATHS.npz'
    stage_file = OUT / 'STAGE.json'
    if stage_file.exists():
        stage = read(stage_file)
        if stage['design_sha256'] != sha(DESIGN) or stage['status'] != 'SOURCE_BUNDLE_RMP_INPUT_READY':
            raise ValueError('incompatible source bundle stage')
        if stage['matrix_sha256'] != sha(matrix_file) or stage['source_paths_sha256'] != sha(payload_file):
            raise ValueError('source bundle stage arrays drift')
        A = sparse.load_npz(matrix_file).tocsr()
        with np.load(payload_file, allow_pickle=False) as z:
            payload = {name: z[name].copy() for name in z.files}
        positive = stage['source_positive_fragments']
    else:
        A, payload, positive = build(model, base, bridge, design['algorithm_policy'])
        sparse.save_npz(matrix_file.with_suffix('.partial.npz'), A)
        os.replace(matrix_file.with_suffix('.partial.npz'), matrix_file)
        np.savez_compressed(payload_file.with_suffix('.partial.npz'), **payload)
        os.replace(payload_file.with_suffix('.partial.npz'), payload_file)
        stage = {'schema': 'DEV42_SOURCE_BUNDLE_STAGE',
                 'status': 'SOURCE_BUNDLE_RMP_INPUT_READY',
                 'design_sha256': sha(DESIGN),
                 'matrix_sha256': sha(matrix_file),
                 'source_paths_sha256': sha(payload_file),
                 'source_positive_fragments': positive,
                 'bundle_count': A.shape[1],
                 'capacity_rows': A.shape[0],
                 'matrix_nnz': A.nnz,
                 'seconds_to_build': time.monotonic() - began}
        save(stage_file, stage)
        print(json.dumps(stage), flush=True)
    n = A.shape[1]
    if (positive != int(design['source_positive_fragments'])
            or A.shape[0] != len(payload['original_capacity_rows'])
            or n != len(payload['bundle_weighted_delta_cost'])
            or len(payload['fragment_index']) != positive):
        raise ValueError('saved bundle dimensions')
    state = JointState(A, payload['original_capacity_rows'], payload['residual_capacity'],
                       payload['bundle_weighted_delta_cost'], np.arange(n, dtype=np.int32),
                       np.ones(n), list(range(n)),
                       list(map(str, payload['bundle_signature'])), base.residual_capacity)
    solved = state.solve(float(design['resources']['RMP_seconds']))
    if solved.max_capacity_excess > 1e-8 or solved.max_group_excess > 1e-8:
        raise ValueError('restricted bundle RMP capacity or group demand')
    np.savez_compressed(OUT / 'BUNDLE_RMP_SOLUTION.npz',
                        bundle_fraction=solved.y, original_capacity_rows=payload['original_capacity_rows'],
                        capacity_mu=solved.capacity_mu, bundle_mu=solved.group_mu)
    upper = float(seed['independent_feasible_upper'] + solved.objective_delta)
    result = {'schema': 'DEV42_FULL_ORIGINAL_SOURCE_BUNDLE_RESTRICTED_RMP',
              'status': 'RESTRICTED_BUNDLE_PRIMAL_PENDING_INDEPENDENT_ORIGINAL_REPLAY',
              'case_id': cfg['case_id'], 'build_id': design['core_build_id'],
              'source_hashes': model.source_hashes,
              'design_sha256': sha(DESIGN), 'runner_sha256': sha(Path(__file__)),
              'original_positive_OD': len(model.od), 'original_release_events': model.K,
              'fresh_seed_receipt_sha256': sha(SEED / 'RECEIPT.json'),
              'source_bridge_original_edge': bridge.edge,
              'source_positive_fragments': positive,
              'disjoint_bundle_count': n,
              'bundle_positive_variables': int(np.count_nonzero(solved.y > 1e-10)),
              'bundle_member_positive_fragments': int(np.count_nonzero(solved.y[payload['bundle_id']] > 1e-10)),
              'original_capacity_rows': A.shape[0], 'matrix_nnz': A.nnz,
              'restricted_delta': solved.objective_delta,
              'candidate_upper_pending_independent_replay': upper,
              'max_touched_capacity_excess': solved.max_capacity_excess,
              'restricted_RMP_iterations': solved.iterations,
              'matrix_sha256': sha(matrix_file),
              'source_paths_sha256': sha(payload_file),
              'solution_sha256': sha(OUT / 'BUNDLE_RMP_SOLUTION.npz'),
              'wall_seconds': time.monotonic() - began,
              'historical_best_upper_evaluation_only': design['historical_best_evaluation_only']['upper'],
              'scientific_limit': 'Valid restricted candidate only after independent full original replay; bundle restrictions are not full graph CG optimality.'}
    save(OUT / 'RESULT.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'source_positive_fragments',
                                             'disjoint_bundle_count', 'bundle_positive_variables',
                                             'candidate_upper_pending_independent_replay', 'wall_seconds')}), flush=True)


if __name__ == '__main__':
    main()
