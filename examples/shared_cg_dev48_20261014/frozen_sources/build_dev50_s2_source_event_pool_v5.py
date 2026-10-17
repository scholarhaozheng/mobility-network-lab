"""Build a bounded initial CG column pool with full original S2 demand.

The independent FIFO source seed serves every OD/release.  The path pool only
limits alternative columns; it never filters demand or changes capacities.
"""
from array import array
from collections import Counter
from hashlib import sha256
from pathlib import Path
import io
import json
import os
import sys
import time
import zipfile

import numpy as np

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'sparse_common_dev48_balanced_selection'))
from shared_cg.implicit_graph import ImplicitTimeGraph
from shared_cg.source_full_event_base import FullUniformQBase
from shared_cg.source_bridge_candidates import SourceBridgePrefixCandidates

CASES = {
    'urbana_S2_Q': ('urbana_S2_Q__sparse_common_dev41_wide_bridge_cg_cold_seed.json',
                    'dev41_cold_source_seed_urbana_S2_Q'),
    'pittsburgh_S2_Q': ('pittsburgh_S2_Q__sparse_common_dev41_wide_bridge_cg_cold_seed.json',
                       'dev41_cold_source_seed_pittsburgh_S2_Q'),
}


def digest(path):
    h = sha256()
    with Path(path).open('rb') as handle:
        for part in iter(lambda: handle.read(1048576), b''):
            h.update(part)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.partial')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(temp, path)


def signature(fragment, edge, entry):
    h = sha256()
    h.update(np.asarray([fragment], np.int64).tobytes())
    h.update(np.asarray(edge, np.int32).tobytes())
    h.update(np.asarray(entry, np.int32).tobytes())
    return h.hexdigest()


def npy_header(dtype, shape):
    stream = io.BytesIO()
    np.lib.format.write_array_header_1_0(stream, {
        'descr': np.lib.format.dtype_to_descr(np.dtype(dtype)),
        'fortran_order': False, 'shape': shape})
    return stream.getvalue()


def stream_npy(archive, name, dtype, count, chunks):
    with archive.open(name + '.npy', 'w') as out:
        out.write(npy_header(dtype, (count,)))
        total = 0
        for chunk in chunks:
            values = np.asarray(chunk, dtype=dtype)
            total += len(values)
            out.write(values.tobytes(order='C'))
        if total != count:
            raise ValueError('streamed sparse member count')


def small_npy(archive, name, values):
    stream = io.BytesIO()
    np.save(stream, np.asarray(values), allow_pickle=False)
    archive.writestr(name + '.npy', stream.getvalue())


def main(case):
    if case not in CASES:
        raise ValueError(case)
    start = time.monotonic()
    design_path = R / f'DEV50_{case}_SOURCE_EVENT_POOL_DESIGN_V5.json'
    design = read(design_path)
    cfg_file, seed_dir = CASES[case]
    cfg_path = R / 'cases' / cfg_file
    seed_path = R / 'runs' / seed_dir
    out = R / 'runs' / f'dev50_source_event_pool_{case}_v5'
    cfg = read(cfg_path)
    seed = read(seed_path / 'RECEIPT.json')
    for key, path in (
        ('builder_sha256', Path(__file__)),
        ('source_config_sha256', cfg_path),
        ('fresh_seed_receipt_sha256', seed_path / 'RECEIPT.json'),
    ):
        if digest(path) != design[key]:
            raise ValueError(f'frozen input drift {key}')
    core = R / 'sparse_common_dev48_balanced_selection' / 'shared_cg'
    for name, wanted in design['core_module_sha256'].items():
        if digest(core / name) != wanted:
            raise ValueError(f'frozen core drift {name}')
    if seed['status'] != 'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED':
        raise ValueError('independent full-demand source seed missing')
    aon = seed_path / 'aon' / 'UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
    fifo = seed_path / 'fifo' / 'FRAGMENTS.npz'
    if digest(aon) != seed['AON_path_sha256'] or digest(fifo) != seed['FIFO_fragment_sha256']:
        raise ValueError('cold source arrays drift')
    model = ImplicitTimeGraph(cfg['source_dir'], cfg['dt_seconds'],
                              cfg['horizon_steps'], cfg['release_steps'], cfg['demand_factor'])
    if (model.source_hashes != cfg['expected_source_hashes'] or
            model.K != cfg['expected_commodity_events'] or
            cfg['demand_factor'] != 2.0):
        raise ValueError('original S2 model identity')
    base = FullUniformQBase(model, aon, fifo)
    bridge = SourceBridgePrefixCandidates(model, base)
    good = bridge.eligible[bridge.saving[bridge.eligible] > design['minimum_raw_saving_minutes']]
    score = np.asarray(base.fm[good] * bridge.saving[good], np.float64)
    if not np.all(np.isfinite(score)):
        raise ValueError('nonfinite source score')
    rank = np.lexsort((good, -score))
    chosen = good[rank[:min(len(good), design['maximum_source_fragments'])]]
    if len(chosen) == 0 or len(np.unique(chosen)) != len(chosen):
        raise ValueError('source selection empty or duplicate')
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'STAGE.json').exists():
        raise FileExistsError(out / 'STAGE.json')
    # Sequential raw row/coefficient streams keep the original row identity
    # without allocating hundreds of millions of Python/NumPy index objects.
    raw_row_path = out / 'RESOURCE_ROW_ABS.stream'
    raw_val_path = out / 'RESOURCE_COEFFICIENT.stream'
    if raw_row_path.exists() or raw_val_path.exists():
        raise FileExistsError('previous V3 raw stream exists')
    column_offset = array('i', [0])
    touched = np.zeros(model.resource_count, dtype=np.bool_)
    edges = array('i')
    times = array('i')
    offsets = array('q', [0])
    costs = array('d')
    signatures = []
    H = model.H
    with raw_row_path.open('wb') as row_file, raw_val_path.open('wb') as val_file:
        for j, f0 in enumerate(chosen):
            f = int(f0)
            edge, entry, raw = bridge.recover(f)
            if len(edge) != len(entry) or np.any(entry < 0) or np.any(entry >= H):
                raise ValueError('original path/time mapping')
            if abs(raw - bridge.candidate_unit[f]) > 1e-7:
                raise ValueError('recovered source path cost')
            after = Counter(int(model.physical_pos[int(e)]) * H + int(t)
                            for e, t in zip(edge, entry) if model.physical_pos[int(e)] >= 0)
            before = base.base_rows(f)
            changed = [(int(r), int(after.get(r, 0) - before.get(r, 0)))
                       for r in sorted(after.keys() | before.keys())]
            changed = [(r, value) for r, value in changed if value]
            if any(not -128 <= value <= 127 for _, value in changed):
                raise ValueError('exact physical coefficient range')
            row_chunk = np.asarray([r for r, _ in changed], dtype=np.int32)
            val_chunk = np.asarray([value for _, value in changed], dtype=np.int8)
            if (np.any(row_chunk < 0) or np.any(row_chunk >= model.resource_count)
                    or len(changed) != len(row_chunk)):
                raise ValueError('exact physical row/coefficient range')
            row_file.write(row_chunk.tobytes()); val_file.write(val_chunk.tobytes())
            touched[row_chunk] = True
            column_offset.append(column_offset[-1] + len(row_chunk))
            edges.extend(map(int, edge)); times.extend(map(int, entry))
            offsets.append(len(edges))
            costs.append(float(raw - base.donor_cost[f]))
            signatures.append(signature(f, edge, entry))
            if (j + 1) % 2000 == 0:
                row_file.flush(); val_file.flush()
                print(json.dumps({'case': case, 'paths_built': j + 1,
                                  'of': len(chosen), 'raw_nnz': column_offset[-1]}), flush=True)
    nnz = int(column_offset[-1])
    if raw_row_path.stat().st_size != 4 * nnz or raw_val_path.stat().st_size != nnz:
        raise ValueError('exact raw stream size')
    original_rows = np.memmap(raw_row_path, dtype=np.int32, mode='r', shape=(nnz,))
    original_vals = np.memmap(raw_val_path, dtype=np.int8, mode='r', shape=(nnz,))
    rows = np.flatnonzero(touched).astype(np.int64)
    local = np.full(len(touched), -1, dtype=np.int32)
    local[rows] = np.arange(len(rows), dtype=np.int32)
    residual = np.empty(len(rows), dtype=np.float64)
    capacity_chunk_rows = 50_000
    for a in range(0, len(rows), capacity_chunk_rows):
        b = min(a + capacity_chunk_rows, len(rows))
        residual[a:b] = base.residual_capacity(rows[a:b])
        if a and a % 1_000_000 == 0:
            print(json.dumps({'case': case, 'capacity_rows_verified': b,
                              'of': len(rows)}), flush=True)
    if np.any(~np.isfinite(residual)):
        raise ValueError('nonfinite base residual')
    mass = base.fm[chosen].astype(np.float64)
    if np.any(mass <= 0) or np.any(~np.isfinite(mass)):
        raise ValueError('nonpositive source fragment mass')
    matrix = out / 'INITIAL_STATE_MATRIX.npz'
    state = out / 'INITIAL_STATE.npz'
    paths = out / 'INITIAL_PATH_POOL.npz'
    matrix_tmp = matrix.with_suffix('.partial.npz')
    with zipfile.ZipFile(matrix_tmp, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as archive:
        block = 1_000_000
        stream_npy(archive, 'indices', np.int32, nnz,
                   (local[original_rows[a:min(a + block, nnz)]]
                    for a in range(0, nnz, block)))
        stream_npy(archive, 'data', np.int8, nnz,
                   (original_vals[a:min(a + block, nnz)]
                    for a in range(0, nnz, block)))
        small_npy(archive, 'indptr', np.frombuffer(column_offset, dtype=np.int32))
        small_npy(archive, 'shape', np.asarray([len(rows), len(chosen)], np.int64))
        small_npy(archive, 'format', np.asarray(b'csc'))
    with zipfile.ZipFile(matrix_tmp) as archive:
        if archive.testzip() is not None:
            raise ValueError('streamed CSC ZIP CRC failure')
    os.replace(matrix_tmp, matrix)
    np.savez_compressed(state.with_suffix('.partial.npz'),
                        original_rows=rows, residual_capacity=residual,
                        delta_cost=np.frombuffer(costs, dtype=np.float64).copy(),
                        column_group=np.arange(len(chosen), dtype=np.int32),
                        group_mass=mass, group_key=chosen.astype(np.int64),
                        column_signature=np.asarray(signatures, dtype='U64'))
    os.replace(state.with_suffix('.partial.npz'), state)
    np.savez_compressed(paths.with_suffix('.partial.npz'),
                        edge_offset=np.frombuffer(offsets, dtype=np.int64).copy(),
                        original_edge_index=np.frombuffer(edges, dtype=np.int32).copy(),
                        original_entry_step=np.frombuffer(times, dtype=np.int32).copy(),
                        source_event_key=chosen.astype(np.int64),
                        signature=np.asarray(signatures, dtype='U64'))
    os.replace(paths.with_suffix('.partial.npz'), paths)
    stage = {'schema': 'DEV50_COLD_S2_SOURCE_EVENT_POOL',
             'status': 'COLD_SOURCE_EVENT_POOL_READY_UNSOLVED', 'case_id': case,
             'design_sha256': digest(design_path), 'builder_sha256': digest(Path(__file__)),
             'source_hashes': model.source_hashes, 'source_bridge_original_edge': bridge.edge,
             'original_positive_OD': len(model.od), 'original_release_events': model.K,
             'source_positive_fragments': len(good), 'selected_source_fragments': len(chosen),
             'capacity_rows': len(rows), 'matrix_nnz': nnz,
             'minimum_source_path_saving': float(np.min(bridge.saving[chosen])),
             'selected_unconstrained_saving_PCE_minutes': float(np.sum(score[rank[:len(chosen)]])),
             'matrix_sha256': digest(matrix), 'state_sha256': digest(state),
             'path_pool_sha256': digest(paths), 'wall_seconds': time.monotonic() - start,
             'scope': 'All original OD/releases on independent S2 FIFO base; each selected source fragment has one original path and exact shared physical-time resource delta. No older solution/dual imported.'}
    save(out / 'STAGE.json', stage)
    original_rows._mmap.close(); original_vals._mmap.close()
    del original_rows, original_vals
    raw_row_path.unlink(); raw_val_path.unlink()
    print(json.dumps(stage), flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: build_dev50_s2_source_event_pool.py CASE_ID')
    main(sys.argv[1])
