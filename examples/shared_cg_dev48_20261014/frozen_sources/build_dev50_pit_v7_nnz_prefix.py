"""Materialize a source-only sparse prefix without changing original demand."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import time

import numpy as np
from scipy import sparse

R = Path(__file__).resolve().parent
CASE = 'pittsburgh_S2_Q'


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    start = time.monotonic()
    design_path = R / f'DEV50_{CASE}_SOURCE_EVENT_POOL_DESIGN_V7.json'
    design = json.loads(design_path.read_text(encoding='utf-8'))
    if design['builder_sha256'] != digest(Path(__file__)):
        raise ValueError('frozen V7 builder drift')
    parent = R / 'runs' / f'dev50_source_event_pool_{CASE}_v6'
    stage_path = parent / 'STAGE.json'
    old = json.loads(stage_path.read_text(encoding='utf-8'))
    if (digest(stage_path) != design['parent_v6_stage_sha256'] or
            old['source_hashes'] != design['source_hashes'] or
            old['original_positive_OD'] != design['original_positive_OD'] or
            old['original_release_events'] != design['original_release_events']):
        raise ValueError('parent source identity drift')
    names = ('INITIAL_STATE_MATRIX.npz', 'INITIAL_STATE.npz', 'INITIAL_PATH_POOL.npz')
    keys = ('parent_v6_matrix_sha256', 'parent_v6_state_sha256',
            'parent_v6_path_pool_sha256')
    for name, key in zip(names, keys):
        if digest(parent / name) != design[key]:
            raise ValueError('parent source array drift: ' + name)
    n = int(design['initial_source_prefix_columns'])
    nnz = int(design['initial_source_prefix_nonzeros'])
    out = R / 'runs' / f'dev50_source_event_pool_{CASE}_v7'
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'STAGE.json').exists():
        raise FileExistsError(out / 'STAGE.json')
    A0 = sparse.load_npz(parent / names[0])
    if A0.format != 'csc' or int(A0.indptr[n]) != nnz or nnz > design['maximum_initial_nonzeros']:
        raise ValueError('original source prefix sparse identity')
    A = A0[:, :n].tocsc()
    if A.nnz != nnz:
        raise ValueError('exact source prefix nonzeros')
    matrix = out / names[0]
    sparse.save_npz(matrix.with_suffix('.partial.npz'), A, compressed=True)
    os.replace(matrix.with_suffix('.partial.npz'), matrix)
    del A, A0
    with np.load(parent / names[1], allow_pickle=False) as z:
        state = {key: z[key] for key in z.files}
    if (len(state['delta_cost']) < n or len(state['group_key']) < n or
            len(state['original_rows']) != len(state['residual_capacity'])):
        raise ValueError('parent source state dimensions')
    state_path = out / names[1]
    np.savez_compressed(state_path.with_suffix('.partial.npz'),
                        original_rows=state['original_rows'],
                        residual_capacity=state['residual_capacity'],
                        delta_cost=state['delta_cost'][:n],
                        column_group=state['column_group'][:n],
                        group_mass=state['group_mass'][:n],
                        group_key=state['group_key'][:n],
                        column_signature=state['column_signature'][:n])
    os.replace(state_path.with_suffix('.partial.npz'), state_path)
    with np.load(parent / names[2], allow_pickle=False) as z:
        paths = {key: z[key] for key in z.files}
    end = int(paths['edge_offset'][n])
    if (len(paths['source_event_key']) < n or
            not np.array_equal(state['group_key'][:n], paths['source_event_key'][:n]) or
            not np.array_equal(state['column_signature'][:n], paths['signature'][:n])):
        raise ValueError('parent source path-state identity')
    path_path = out / names[2]
    np.savez_compressed(path_path.with_suffix('.partial.npz'),
                        edge_offset=paths['edge_offset'][:n + 1],
                        original_edge_index=paths['original_edge_index'][:end],
                        original_entry_step=paths['original_entry_step'][:end],
                        source_event_key=paths['source_event_key'][:n],
                        signature=paths['signature'][:n])
    os.replace(path_path.with_suffix('.partial.npz'), path_path)
    stage = {
        'schema': 'DEV50_COLD_S2_SOURCE_EVENT_POOL_NNZ_PREFIX_V7',
        'status': 'COLD_SOURCE_EVENT_POOL_READY_UNSOLVED',
        'case_id': CASE, 'design_sha256': digest(design_path),
        'builder_sha256': digest(Path(__file__)),
        'parent_v6_stage_sha256': digest(stage_path),
        'source_hashes': old['source_hashes'],
        'source_bridge_original_edge': old['source_bridge_original_edge'],
        'original_positive_OD': old['original_positive_OD'],
        'original_release_events': old['original_release_events'],
        'source_positive_fragments': old['source_positive_fragments'],
        'selected_source_fragments': n,
        'capacity_rows': old['capacity_rows'],
        'matrix_nnz': nnz,
        'selected_unconstrained_saving_PCE_minutes':
            float(np.dot(-state['delta_cost'][:n], state['group_mass'][:n])),
        'matrix_sha256': digest(matrix),
        'state_sha256': digest(state_path),
        'path_pool_sha256': digest(path_path),
        'wall_seconds': time.monotonic() - start,
        'scope': design['scope'],
    }
    temp = out / 'STAGE.partial.json'
    temp.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(temp, out / 'STAGE.json')
    print(json.dumps(stage), flush=True)


if __name__ == '__main__':
    main()
