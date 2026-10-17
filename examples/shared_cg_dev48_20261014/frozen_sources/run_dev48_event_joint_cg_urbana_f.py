"""Cold source-generated partial CG on the registered full Urbana F Q model.

All original demand remains on the certified FIFO base. The Dev46 pool is
source-generated, contains no previous solver flow or dual, and each selected
fragment has one shared mass constraint for every later alternative path.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy import sparse

R = Path(__file__).resolve().parent
CORE = R / 'sparse_common_dev48_balanced_selection'
sys.path.insert(0, str(CORE))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.rolling_price import RollingModel
from shared_cg.batch_rolling_paths import recover_many_paths
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.balanced_event_selection import BalancedEventSelector
from shared_cg.joint_cg_loop import Candidate, JointState, run_joint_cg

DESIGN = R / 'DEV48_EVENT_JOINT_CG_DESIGN.json'
CFG = R / 'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
SEED = R / 'runs/dev35_cold_source_seed_urbana_f'
INITIAL = R / 'runs/dev46_source_event_pool_urbana_f'
OUT = R / 'runs/dev48_event_joint_cg_urbana_f'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.partial')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def signature(fragment, edge, entry):
    h = hashlib.sha256()
    h.update(np.asarray([fragment], np.int64).tobytes())
    h.update(np.asarray(edge, np.int32).tobytes())
    h.update(np.asarray(entry, np.int32).tobytes())
    return h.hexdigest()


def save_new_paths(path, paths):
    offsets = [0]
    edges = []
    times = []
    fragments = []
    signatures = []
    for edge, entry, fragment, sig in paths:
        edges.extend(map(int, edge))
        times.extend(map(int, entry))
        offsets.append(len(edges))
        fragments.append(int(fragment))
        signatures.append(sig)
    tmp = path.with_suffix('.partial.npz')
    np.savez_compressed(tmp, edge_offset=np.asarray(offsets, np.int64),
                        original_edge_index=np.asarray(edges, np.int32),
                        original_entry_step=np.asarray(times, np.int32),
                        source_event_key=np.asarray(fragments, np.int64),
                        signature=np.asarray(signatures, dtype='U64'))
    os.replace(tmp, path)


def load_state(path, base):
    with np.load(path / 'STATE.npz') as z:
        state = {k: z[k].copy() for k in z.files}
    return JointState(sparse.load_npz(path / 'STATE_MATRIX.npz'),
                      state['original_rows'], state['residual_capacity'],
                      state['delta_cost'], state['column_group'],
                      state['group_mass'], list(map(int, state['group_key'])),
                      list(map(str, state['column_signature'])), base.residual_capacity)


def main():
    started = time.monotonic()
    design = read(DESIGN)
    cfg = read(CFG)
    seed = read(SEED / 'RECEIPT.json')
    initial = read(INITIAL / 'STAGE.json')
    for name, path in [('source_config_sha256', CFG),
                       ('fresh_seed_receipt_sha256', SEED / 'RECEIPT.json'),
                       ('initial_stage_sha256', INITIAL / 'STAGE.json'),
                       ('initial_matrix_sha256', INITIAL / 'INITIAL_STATE_MATRIX.npz'),
                       ('initial_state_sha256', INITIAL / 'INITIAL_STATE.npz'),
                       ('initial_path_pool_sha256', INITIAL / 'INITIAL_PATH_POOL.npz'),
                       ('runner_sha256', Path(__file__))]:
        if sha(path) != design[name]:
            raise ValueError('frozen input drift: ' + name)
    for name, wanted in design['core_module_sha256'].items():
        if sha(CORE / 'shared_cg' / name) != wanted:
            raise ValueError('common core drift: ' + name)
    if (seed['status'] != 'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED'
            or initial['status'] != 'COLD_SOURCE_EVENT_POOL_READY_UNSOLVED'
            or initial['source_hashes'] != cfg['expected_source_hashes']):
        raise ValueError('cold source identity')
    model = ImplicitTimeGraph(cfg['source_dir'], cfg['dt_seconds'],
                              cfg['horizon_steps'], cfg['release_steps'], cfg['demand_factor'])
    if model.source_hashes != cfg['expected_source_hashes'] or model.K != design['original_release_events']:
        raise ValueError('original graph/demand identity')
    if (sha(SEED / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz') != seed['AON_path_sha256']
            or sha(SEED / 'fifo/FRAGMENTS.npz') != seed['FIFO_fragment_sha256']):
        raise ValueError('certified base drift')
    base = FullUniformQBase(model, SEED / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz',
                            SEED / 'fifo/FRAGMENTS.npz')
    oracle = RollingModel.from_implicit(model)
    dest_by_od = np.asarray([x[3] for x in model.od], np.int32)
    origin_by_od = np.asarray([x[2] for x in model.od], np.int32)
    fifo_dest = dest_by_od[base.fod]
    policy = design['algorithm_policy']
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'RESULT.json').exists():
        raise FileExistsError('candidate already solved')
    checkpoint = OUT / 'STAGE_CHECKPOINT.json'
    new_paths = []
    if checkpoint.exists():
        cp = read(checkpoint)
        if (cp['design_sha256'] != sha(DESIGN)
                or cp['state_sha256'] != sha(OUT / 'STATE.npz')
                or cp['matrix_sha256'] != sha(OUT / 'STATE_MATRIX.npz')
                or cp['new_path_pool_sha256'] != sha(OUT / 'NEW_PATH_POOL.npz')):
            raise ValueError('checkpoint drift')
        state = load_state(OUT, base)
        with np.load(OUT / 'NEW_PATH_POOL.npz') as z:
            pool = {k: z[k].copy() for k in z.files}
        for j, frag in enumerate(pool['source_event_key']):
            a = int(pool['edge_offset'][j]); b = int(pool['edge_offset'][j + 1])
            new_paths.append((pool['original_edge_index'][a:b],
                              pool['original_entry_step'][a:b], int(frag),
                              str(pool['signature'][j])))
        completed = int(cp['completed_rounds'])
        prior_history = cp['history']
    else:
        with np.load(INITIAL / 'INITIAL_STATE.npz') as z:
            arr = {k: z[k].copy() for k in z.files}
        state = JointState(sparse.load_npz(INITIAL / 'INITIAL_STATE_MATRIX.npz'),
                           arr['original_rows'], arr['residual_capacity'], arr['delta_cost'],
                           arr['column_group'], arr['group_mass'],
                           list(map(int, arr['group_key'])),
                           list(map(str, arr['column_signature'])), base.residual_capacity)
        if len(state.keys) != initial['selected_source_fragments']:
            raise ValueError('initial source group count')
        completed = 0
        prior_history = []
    initial_cols = initial['selected_source_fragments']
    price_receipts = []
    exact_receipts = []

    def price(lambda_by_row, nu_by_key, mode):
        t0 = time.monotonic()
        active = {int(r): float(v) for r, v in lambda_by_row.items() if v > 1e-12}
        rows = np.fromiter(active, dtype=np.int64)
        lam = np.fromiter(active.values(), dtype=np.float64)
        if mode == 'exact':
            weighted = 0.0
            for dest in model.destinations:
                ids = np.asarray([i for i, item in enumerate(model.od) if int(item[3]) == int(dest)], np.int32)
                release = np.tile(np.arange(model.release_steps, dtype=np.int32), len(ids))
                values = oracle.price(int(dest), release,
                                      np.repeat(origin_by_od[ids], model.release_steps), rows, lam)
                weighted += float(np.dot(base.hourly[ids] / model.release_steps,
                                         values.reshape(len(ids), model.release_steps).sum(axis=1)))
            lower = weighted - float(np.dot(model.capacity_for_rows(rows), lam))
            receipt = {'mode': 'exact', 'original_events': model.K,
                       'capacity_price_rows': len(rows), 'full_original_lower': lower,
                       'seconds': time.monotonic() - t0}
            exact_receipts.append(receipt)
            print(json.dumps(receipt), flush=True)
            return [], {'full_original_lower': lower, 'minimum_reduced_cost': -np.inf}
        selector = BalancedEventSelector(model.release_steps,
                                         window_steps=int(policy['pricing_window_steps']),
                                         per_window_per_lane=int(policy['per_window_per_lane']),
                                         per_od_window_per_lane=int(policy['per_od_window_per_lane']),
                                         per_lane_total=int(policy['per_lane_total']), epsilon=1e-6)
        shortcut = not active and not nu_by_key
        calls = 0
        for dest in model.destinations:
            fragments = np.flatnonzero(fifo_dest == dest).astype(np.int64)
            unsplit = base.unsplit_od[dest_by_od[base.unsplit_od] == dest]
            if shortcut:
                unsplit = np.empty(0, dtype=np.int32)
            other = (base.n_fragments + np.repeat(unsplit, model.release_steps).astype(np.int64)
                     * model.release_steps + np.tile(np.arange(model.release_steps, dtype=np.int64), len(unsplit)))
            keys = np.r_[fragments, other]
            if not len(keys):
                continue
            i, release, mass, base_cost = base.event_arrays(keys)
            adjusted = oracle.price(int(dest), release, origin_by_od[i], rows, lam)
            base_toll = base.base_toll_keys(keys, active)
            nu = np.fromiter((nu_by_key.get(int(k), 0.0) for k in keys), dtype=np.float64, count=len(keys))
            selector.add(keys, i, release, mass, adjusted, base_cost, base_toll, nu)
            calls += 1
        selected, windows = selector.select()
        offers = []
        sweeps = 0
        for dest in model.destinations:
            chosen = [x for x in selected if dest_by_od[x.od] == dest]
            if not chosen:
                continue
            keys = np.asarray([x.key for x in chosen], np.int64)
            i, release, mass, base_cost = base.event_arrays(keys)
            recovered = recover_many_paths(oracle, int(dest), origin_by_od[i], release, rows, lam,
                                            window_steps=int(policy['pricing_window_steps']),
                                            max_windows_per_path=int(policy['max_windows_per_path']))
            sweeps += recovered.full_horizon_sweeps
            for j, key in enumerate(keys):
                if abs(float(recovered.adjusted_cost[j]) - chosen[j].adjusted_cost) > 1e-6:
                    raise ValueError('same-dual path recovery')
                edge = recovered.original_edge_index[j]
                entry = recovered.original_entry_step[j]
                sig = signature(int(key), edge, entry)
                after = Counter(int(model.physical_pos[int(e)]) * model.H + int(t)
                                for e, t in zip(edge, entry) if model.physical_pos[int(e)] >= 0)
                before = base.base_rows(int(key))
                delta = {r: after.get(r, 0) - before.get(r, 0) for r in after.keys() | before.keys()}
                delta = {r: v for r, v in delta.items() if v}
                change = float(recovered.raw_cost[j] - base_cost[j])
                if not delta and abs(change) <= 1e-14:
                    continue
                diverse = (int(i[j]), int(release[j] // policy['pricing_window_steps']),
                           int(min(delta) // model.H) if delta else -1)
                col = Candidate(int(key), float(mass[j]), change, tuple(sorted(delta.items())),
                                sig, diverse, chosen[j].lane)
                offers.append(col)
                new_paths.append((edge.copy(), entry.copy(), int(key), sig))
        receipt = {'mode': 'partial', 'original_events_total': model.K,
                   'events_priced': selector.events_priced,
                   'destination_calls': calls, 'capacity_price_rows': len(rows),
                   'negative_events': selector.negative_events,
                   'positive_donor_toll_events': selector.positive_donor_toll_events,
                   'selected_windows': windows, 'selected_events': len(selected),
                   'selected_release_lane': sum(x.lane == 'capacity_release' for x in selected),
                   'selected_negative_lane': sum(x.lane == 'negative_rc' for x in selected),
                   'recovered_paths': len(offers), 'full_horizon_recovery_sweeps': sweeps,
                   'minimum_reduced_cost': selector.minimum_reduced_cost,
                   'seconds': time.monotonic() - t0}
        price_receipts.append(receipt)
        print(json.dumps(receipt), flush=True)
        return offers, {'minimum_reduced_cost': selector.minimum_reduced_cost}

    def checkpoint_after_add(current, history):
        matrix = OUT / 'STATE_MATRIX.npz'
        sparse.save_npz(OUT / 'STATE_MATRIX.partial.npz', current.A)
        os.replace(OUT / 'STATE_MATRIX.partial.npz', matrix)
        state_path = OUT / 'STATE.npz'
        np.savez_compressed(OUT / 'STATE.partial.npz',
                            original_rows=np.asarray(current.rows, np.int64),
                            residual_capacity=np.asarray(current.rhs),
                            delta_cost=np.asarray(current.cost),
                            column_group=np.asarray(current.group, np.int32),
                            group_mass=np.asarray(current.mass),
                            group_key=np.asarray(current.keys, np.int64),
                            column_signature=np.asarray(current.column_signatures, dtype='U64'))
        os.replace(OUT / 'STATE.partial.npz', state_path)
        save_new_paths(OUT / 'NEW_PATH_POOL.npz', new_paths)
        save(checkpoint, {'schema': 'DEV48_JOINT_CG_STAGE', 'status': 'POOL_ADDED_PENDING_NEXT_RMP',
                          'design_sha256': sha(DESIGN),
                          'completed_rounds': completed + len(history),
                          'column_count': current.A.shape[1],
                          'matrix_sha256': sha(matrix), 'state_sha256': sha(state_path),
                          'new_path_pool_sha256': sha(OUT / 'NEW_PATH_POOL.npz'),
                          'history': prior_history + history,
                          'source_hashes': model.source_hashes})

    remaining = int(policy['max_rounds']) - completed
    if remaining > 0:
        status, _, history = run_joint_cg(state, price, max_rounds=remaining,
                                          max_new_per_round=int(policy['max_new_columns_per_round']),
                                          max_per_group=int(policy['max_per_group']), epsilon=1e-7,
                                          rmp_seconds=float(design['resources']['RMP_seconds_each']),
                                          stabilization_alpha=float(policy['stabilization_alpha_initial']),
                                          checkpoint=checkpoint_after_add,
                                          lane_minimums={'capacity_release': int(policy['per_lane_total']),
                                                         'negative_rc': int(policy['per_lane_total'])})
    else:
        status = 'ROUND_LIMIT_OPEN'
        history = []
    final = state.solve(float(design['resources']['RMP_seconds_each']))
    if final.max_capacity_excess > 1e-7 or final.max_group_excess > 1e-8:
        raise ValueError('joint original-row primal violation')
    checkpoint_after_add(state, history)
    np.savez_compressed(OUT / 'FINAL_RMP.npz',
                        original_rows=np.asarray(state.rows, np.int64),
                        residual_capacity=np.asarray(state.rhs),
                        delta_cost=np.asarray(state.cost),
                        column_group=np.asarray(state.group, np.int32),
                        group_mass=np.asarray(state.mass),
                        group_key=np.asarray(state.keys, np.int64),
                        column_signature=np.asarray(state.column_signatures, dtype='U64'),
                        flow=final.y, capacity_mu=final.capacity_mu, group_mu=final.group_mu)
    upper = float(seed['independent_feasible_upper'] + final.objective_delta)
    result = {'schema': 'DEV48_BALANCED_SOURCE_EVENT_PARTIAL_JOINT_CG', 'status': status,
              'case_id': cfg['case_id'], 'build_id': design['core_build_id'],
              'source_hashes': model.source_hashes, 'design_sha256': sha(DESIGN),
              'runner_sha256': sha(Path(__file__)), 'original_positive_OD': len(model.od),
              'original_release_events': model.K,
              'fresh_seed_receipt_sha256': sha(SEED / 'RECEIPT.json'),
              'initial_pool_sha256': sha(INITIAL / 'STAGE.json'),
              'initial_columns': initial_cols, 'total_columns': state.A.shape[1],
              'represented_source_events_or_fragments': len(state.keys),
              'round_history': prior_history + history,
              'partial_price_receipts': price_receipts,
              'exact_price_receipts': exact_receipts,
              'fresh_source_base_upper': seed['independent_feasible_upper'],
              'candidate_upper_pending_independent_replay': upper,
              'historical_best_independent_upper_evaluation_only': design['historical_best_evaluation_only']['upper'],
              'final_RMP_iterations': final.iterations,
              'final_positive_columns': int(np.count_nonzero(final.y > 1e-10)),
              'final_max_original_touched_capacity_excess': final.max_capacity_excess,
              'final_max_group_demand_excess': final.max_group_excess,
              'final_rmp_sha256': sha(OUT / 'FINAL_RMP.npz'),
              'final_matrix_sha256': sha(OUT / 'STATE_MATRIX.npz'),
              'new_path_pool_sha256': sha(OUT / 'NEW_PATH_POOL.npz'),
              'wall_seconds': time.monotonic() - started,
              'scientific_limit': 'Source-generated fragment CG pool; original full-graph optimum open until separate exact independent certificate.'}
    save(OUT / 'RESULT.json', result)
    print(json.dumps({'status': status, 'columns': state.A.shape[1],
                      'upper_pending_independent_replay': upper,
                      'wall_seconds': result['wall_seconds']}), flush=True)


if __name__ == '__main__':
    main()

