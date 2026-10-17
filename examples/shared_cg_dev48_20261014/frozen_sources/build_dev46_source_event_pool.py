"""Convert source-generated bridge paths to a coupled per-fragment CG pool.

The original 418 OD by 14,400 releases remain on a certified feasible base.
Each selected FIFO fragment receives its own demand group, allowing later
multiple legal alternatives to withdraw old positive flow within one shared
capacity RMP. This is a partial source pool, not full original CG closure.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os
import sys
import time
import numpy as np
from scipy import sparse

R = Path(__file__).resolve().parent
CORE = R / 'sparse_common_dev45_group_row_bound'
sys.path.insert(0, str(CORE))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.source_full_event_base import FullUniformQBase

DESIGN = R / 'DEV46_SOURCE_EVENT_POOL_DESIGN.json'
SOURCE = R / 'runs/dev43_ranked_source_columns_urbana_f'
SEED = R / 'runs/dev35_cold_source_seed_urbana_f'
CFG = R / 'cases/urbana_F_Q__sparse_common_dev35_cold_seed.json'
OUT = R / 'runs/dev46_source_event_pool_urbana_f'


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


def signature(f, edge, entry):
    h = hashlib.sha256()
    h.update(np.asarray([int(f)], np.int64).tobytes())
    h.update(np.asarray(edge, np.int32).tobytes())
    h.update(np.asarray(entry, np.int32).tobytes())
    return h.hexdigest()


def main():
    start = time.monotonic()
    d = read(DESIGN)
    if sha(Path(__file__)) != d['builder_sha256']:
        raise ValueError('frozen Dev46 builder drift')
    for name, wanted in d['core_module_sha256'].items():
        if sha(CORE / 'shared_cg' / name) != wanted:
            raise ValueError('frozen common core drift ' + name)
    for name, path in (('source_matrix_sha256', SOURCE / 'BUNDLE_MATRIX.npz'),
                       ('source_paths_sha256', SOURCE / 'BUNDLE_SOURCE_PATHS.npz'),
                       ('source_stage_sha256', SOURCE / 'STAGE.json'),
                       ('source_config_sha256', CFG),
                       ('fresh_seed_receipt_sha256', SEED / 'RECEIPT.json')):
        if sha(path) != d[name]:
            raise ValueError('source-generated input drift ' + name)
    cfg = read(CFG)
    seed = read(SEED / 'RECEIPT.json')
    if seed['status'] != 'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED':
        raise ValueError('independently certified cold source base required')
    if (sha(SEED / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz') != seed['AON_path_sha256']
            or sha(SEED / 'fifo/FRAGMENTS.npz') != seed['FIFO_fragment_sha256']):
        raise ValueError('cold source base arrays drift')
    model = ImplicitTimeGraph(cfg['source_dir'], cfg['dt_seconds'], cfg['horizon_steps'],
                              cfg['release_steps'], cfg['demand_factor'])
    if model.source_hashes != cfg['expected_source_hashes'] or model.K != d['original_release_events']:
        raise ValueError('original Q graph or demand drift')
    base = FullUniformQBase(model, SEED / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz',
                            SEED / 'fifo/FRAGMENTS.npz')
    with np.load(SOURCE / 'BUNDLE_SOURCE_PATHS.npz', allow_pickle=False) as z:
        payload = {name: z[name].copy() for name in z.files}
    f = payload['fragment_index'].astype(np.int32)
    owner = payload['bundle_id'].astype(np.int32)
    pat = payload['pattern_id'].astype(np.int32)
    n_bundle = len(payload['bundle_weighted_delta_cost'])
    if (len(f) != d['selected_source_fragments'] or len(np.unique(f)) != len(f)
            or np.any(owner < 0) or np.any(owner >= n_bundle)):
        raise ValueError('selected source fragment identity')
    count = np.bincount(owner, minlength=n_bundle)
    single = np.flatnonzero(count == 1).astype(np.int32)
    multiple = np.flatnonzero(count[owner] > 1).astype(np.int32)
    if len(single) + len(multiple) != len(f):
        raise ValueError('bundle-to-event partition')
    first = np.full(n_bundle, -1, np.int32)
    for j, b in enumerate(owner):
        if first[b] == -1:
            first[b] = j
    chosen = first[single]
    sf = f[chosen]
    sp = pat[chosen]
    mass = base.fm[sf].astype(np.float64)
    if np.any(mass <= 0):
        raise ValueError('positive source fragment mass')
    original = sparse.load_npz(SOURCE / 'BUNDLE_MATRIX.npz').tocsc()
    A = original[:, single].tocsc()
    del original
    for j in range(len(single)):
        lo = A.indptr[j]; hi = A.indptr[j + 1]
        normalized = A.data[lo:hi] / mass[j]
        integer = np.rint(normalized)
        if np.max(abs(normalized - integer), initial=0) > 1e-7:
            raise ValueError('single fragment unit capacity coefficient')
        A.data[lo:hi] = integer
    A.eliminate_zeros()
    cost = (payload['bundle_weighted_delta_cost'][single] / mass).astype(np.float64)
    rows = payload['original_capacity_rows'].astype(np.int64)
    rhs = payload['residual_capacity'].astype(np.float64)
    if not np.all(rows[1:] > rows[:-1]):
        raise ValueError('source capacity row order')
    poff = payload['pattern_edge_offset']; pe = payload['pattern_original_edge']
    pt = payload['pattern_entry_offset']; pc = payload['pattern_unit_cost']
    extra = set()
    multi_delta = []
    for index in multiple:
        j = int(index); frag = int(f[j]); pattern = int(pat[j])
        lo = int(poff[pattern]); hi = int(poff[pattern + 1])
        edge = pe[lo:hi]; entry = pt[lo:hi] + int(base.fr[frag])
        after = Counter(int(model.physical_pos[int(e)]) * model.H + int(t)
                        for e, t in zip(edge, entry) if model.physical_pos[int(e)] >= 0)
        before = base.base_rows(frag)
        delta = {int(r): int(after.get(r, 0) - before.get(r, 0))
                 for r in after.keys() | before.keys()}
        delta = {r: v for r, v in delta.items() if v}
        keys = np.fromiter(delta, dtype=np.int64)
        positions = np.searchsorted(rows, keys)
        absent = (positions == len(rows)) | (rows[np.minimum(positions, len(rows) - 1)] != keys)
        extra.update(map(int, keys[absent]))
        multi_delta.append(delta)
    extra_rows = np.asarray(sorted(extra), np.int64)
    if len(extra_rows):
        A = sparse.vstack((A.tocsr(), sparse.csr_matrix((len(extra_rows), A.shape[1]))), format='csr')
        extra_rhs = base.residual_capacity(extra_rows)
        rows = np.r_[rows, extra_rows]
        rhs = np.r_[rhs, extra_rhs]
    else:
        A = A.tocsr()
    position = {int(row): len(payload['original_capacity_rows']) + j
                for j, row in enumerate(extra_rows)}
    rr = []; cc = []; vv = []
    for j, delta in enumerate(multi_delta):
        for row, value in delta.items():
            k = position.get(row)
            if k is None:
                k = int(np.searchsorted(payload['original_capacity_rows'], row))
                if k >= len(payload['original_capacity_rows']) or int(payload['original_capacity_rows'][k]) != row:
                    raise ValueError('missing original row mapping')
            rr.append(k); cc.append(j); vv.append(value)
    B = sparse.coo_matrix((vv, (rr, cc)), shape=(len(rows), len(multiple))).tocsr()
    A = sparse.hstack((A, B), format='csr')
    mf = f[multiple]
    mp = pat[multiple]
    event = np.r_[sf, mf].astype(np.int32)
    pattern = np.r_[sp, mp].astype(np.int32)
    mass = base.fm[event].astype(np.float64)
    multi_cost = pc[mp] - base.donor_cost[mf]
    cost = np.r_[cost, multi_cost]
    if (len(np.unique(event)) != len(event) or len(event) != d['selected_source_fragments']
            or A.shape != (len(rows), len(event))):
        raise ValueError('exact source event columns')
    offsets = [0]; edges = []; times = []; signatures = []
    max_cost_error = 0.0
    for j, (frag0, pattern0) in enumerate(zip(event, pattern)):
        frag = int(frag0); p = int(pattern0)
        lo = int(poff[p]); hi = int(poff[p + 1])
        edge = pe[lo:hi]; entry = pt[lo:hi] + int(base.fr[frag])
        raw_change = float(pc[p] - base.donor_cost[frag])
        max_cost_error = max(max_cost_error, abs(float(cost[j]) - raw_change))
        if max_cost_error > 1e-7 or np.any(entry < 0) or np.any(entry >= model.H):
            raise ValueError('original path cost or time identity')
        edges.extend(map(int, edge)); times.extend(map(int, entry))
        offsets.append(len(edges))
        signatures.append(signature(frag, edge, entry))
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'STAGE.json').exists():
        raise FileExistsError('source event pool already built')
    matrix = OUT / 'INITIAL_STATE_MATRIX.npz'
    state = OUT / 'INITIAL_STATE.npz'
    paths = OUT / 'INITIAL_PATH_POOL.npz'
    sparse.save_npz(matrix.with_suffix('.partial.npz'), A)
    os.replace(matrix.with_suffix('.partial.npz'), matrix)
    np.savez_compressed(state.with_suffix('.partial.npz'),
                        original_rows=rows, residual_capacity=rhs, delta_cost=cost,
                        column_group=np.arange(len(event), dtype=np.int32),
                        group_mass=mass, group_key=event,
                        column_signature=np.asarray(signatures, dtype='U64'))
    os.replace(state.with_suffix('.partial.npz'), state)
    np.savez_compressed(paths.with_suffix('.partial.npz'),
                        edge_offset=np.asarray(offsets, np.int64),
                        original_edge_index=np.asarray(edges, np.int32),
                        original_entry_step=np.asarray(times, np.int32),
                        source_event_key=event,
                        signature=np.asarray(signatures, dtype='U64'))
    os.replace(paths.with_suffix('.partial.npz'), paths)
    stage = {
        'schema': 'DEV46_SOURCE_GENERATED_PER_FRAGMENT_CG_POOL',
        'status': 'COLD_SOURCE_EVENT_POOL_READY_UNSOLVED',
        'design_sha256': sha(DESIGN),
        'builder_sha256': sha(Path(__file__)),
        'source_hashes': model.source_hashes,
        'original_positive_OD': len(model.od), 'original_release_events': model.K,
        'selected_source_fragments': len(event),
        'single_fragment_bundles': len(single),
        'unbundled_multi_fragments': len(multiple),
        'extra_original_capacity_rows_from_unbundling': len(extra_rows),
        'capacity_rows': len(rows), 'matrix_nnz': A.nnz,
        'maximum_unit_cost_error': max_cost_error,
        'matrix_sha256': sha(matrix), 'state_sha256': sha(state),
        'path_pool_sha256': sha(paths),
        'wall_seconds': time.monotonic() - start,
        'scope': 'All original OD/releases remain on independently certified base. One original fragment demand group per selected path, all original capacity rows. No solver flow or dual imported.',
    }
    save(OUT / 'STAGE.json', stage)
    print(json.dumps({k: stage[k] for k in ('status', 'selected_source_fragments',
                                            'extra_original_capacity_rows_from_unbundling',
                                            'capacity_rows', 'matrix_nnz', 'wall_seconds')}), flush=True)


if __name__ == '__main__':
    main()
