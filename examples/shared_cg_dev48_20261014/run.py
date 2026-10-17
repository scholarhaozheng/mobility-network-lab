"""Prepare or reproduce one frozen Dev48 mathematical instance.

The default is input/source preflight only. --execute explicitly starts new
computation. No saved solution, column pool or RMP checkpoint is distributed.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib
import json
import math
import shutil
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CORE_NAME = 'sparse_common_dev48_balanced_selection'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def get_case(case_id):
    return next(c for c in read(HERE / 'cases.json')['cases'] if c['case_id'] == case_id)


def check_files(folder, expected):
    actual = {name: digest(Path(folder) / name) for name in expected}
    require(actual == expected, f'Frozen mathematical input differs: {folder}')
    return actual


def check_package():
    manifest = read(HERE / 'EXECUTABLE_MANIFEST.json')
    for item in manifest['files']:
        p = HERE / item['file']
        require(p.is_file() and digest(p) == item['sha256'], f'Published file changed: {p}')
    return len(manifest['files'])


def load_module(work, name, omit_legacy_batch_loop=False):
    """Import exact source; old unguarded batch scripts are loaded as functions.

    For the three FIFO construction files only, omit their top-level batch
    for-loop. The original function bodies and numerical implementation stay
    byte-identical. The caller selects exactly one registered instance.
    """
    if not omit_legacy_batch_loop:
        module = importlib.import_module(name)
    else:
        path = work / (name + '.py')
        module = types.ModuleType(name)
        module.__file__ = str(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        tree.body = [node for node in tree.body if not isinstance(node, ast.For)]
        exec(compile(tree, str(path), 'exec'), module.__dict__)
    module.R = work
    if hasattr(module, 'CORE'):
        module.CORE = work / CORE_NAME
    return module


@contextlib.contextmanager
def argv(arguments):
    old = sys.argv
    sys.argv = ['run.py', *map(str, arguments)]
    try:
        yield
    finally:
        sys.argv = old


def core_hashes(work):
    return {p.name: digest(p) for p in sorted((work / CORE_NAME / 'shared_cg').glob('*.py'))}


def policy(work, name, updates):
    """Keep the old receipt read-only and bind a new run to its actual inputs."""
    original = HERE / 'policies' / (name + '.json')
    value = read(original)
    value.update(updates)
    if 'core_module_sha256' in value:
        value['core_module_sha256'] = core_hashes(work)
    value['reproduction_binding'] = {
        'original_policy_sha256': digest(original),
        'kind': 'new run paths and generated-input hashes; original numerical policy retained',
        'original_acceptance_does_not_certify_this_new_run': True,
    }
    destination = work / (name + '.json')
    save(destination, value)
    return destination


def graph_inputs(case, work, build=False, input_dir=None):
    if input_dir:
        folder = Path(input_dir).resolve()
        check_files(folder, case['expected_inputs'])
        return folder
    kind, group = case['input_kind'], case['input_group']
    if kind == 'existing_explicit':
        folder = REPO / group
    elif kind == 'implicit':
        folder = HERE / 'inputs' / group
    else:
        builder_dir = work / 'graph-build' / group
        template = HERE / 'inputs' / group
        if not builder_dir.exists():
            shutil.copytree(template, builder_dir)
        folder = builder_dir / 'runs/T_case'
        if build and not (folder / 'dynamic_arc.csv').exists():
            script = 'chicago_build_T_input.py' if group == 'chicago' else 'berkeley_build_t_case.py'
            source = HERE / 'frozen_sources' / script
            target = builder_dir / ('build_T_input.py' if group == 'chicago' else 'build_t_case.py')
            shutil.copyfile(source, target)
            # These two original builders only construct a graph; no optimizer.
            namespace = {'__name__': '__main__', '__file__': str(target)}
            exec(compile(target.read_text(encoding='utf-8-sig'), str(target), 'exec'), namespace)
        if not folder.exists():
            return folder
    check_files(folder, case['expected_inputs'])
    return folder


def workspace_index(case, work, cfg_path):
    """Explicit generated-output locations for independent projection/rendering."""
    paths = {'config': str(cfg_path), 'result': str(work / 'solver/RESULT.json'),
             'model_identity': str(work / 'solver/MODEL_IDENTITY.json')}
    if case['branch'] == 'uniform':
        paths['uniform_paths'] = str(work / 'solver/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz')
        paths['independent_certificate'] = str(work / 'solver/INDEPENDENT_CERTIFICATE.json')
    elif case['branch'] != 'joint':
        paths.update(column_pool=str(work / 'solver/COLUMN_POOL.npz'),
                     rmp=str(work / 'solver/LAST_RMP.npz'),
                     independent_certificate=str(work / 'solver/INDEPENDENT_CERTIFICATE.json'))
        if case['case_id'] == 'pittsburgh_S2_H':
            paths.update(independent_certificate=str(work / 'solver/STAGE_CHECKPOINT_INDEPENDENT_PRIMAL_CERTIFICATE.json'),
                         latest_checkpoint=str(work / 'solver/LATEST_STAGE_CHECKPOINT.json'),
                         mixed_certificate=str(work / 'INDEPENDENT_MIX.json'))
            if Path(paths['latest_checkpoint']).is_file():
                checkpoint = read(paths['latest_checkpoint'])
                paths['checkpoint_pool'] = str(Path(checkpoint['pool_path']).resolve())
                paths['checkpoint_rmp'] = str(Path(checkpoint['rmp_path']).resolve())
            for slot in ('slot_a', 'slot_b'):
                receipt = work / 'solver/STAGE_CHECKPOINTS' / slot / 'CHECKPOINT_RECEIPT.json'
                if receipt.is_file():
                    checkpoint = read(receipt)
                    paths[slot + '_checkpoint_receipt'] = str(receipt)
                    paths[slot + '_checkpoint_pool'] = str(Path(checkpoint['pool_path']).resolve())
                    paths[slot + '_checkpoint_rmp'] = str(Path(checkpoint['rmp_path']).resolve())
    else:
        name = case['case_id']
        seed = work / 'runs' / ('dev35_cold_source_seed_urbana_f' if name == 'urbana_F_Q' else 'dev41_cold_source_seed_' + name)
        initial_name = {'urbana_F_Q': 'dev46_source_event_pool_urbana_f',
                        'urbana_S2_Q': 'dev50_source_event_pool_urbana_S2_Q_v5',
                        'pittsburgh_S2_Q': 'dev50_source_event_pool_pittsburgh_S2_Q_v7'}[name]
        initial = work / 'runs' / initial_name
        paths = {'config': str(cfg_path), 'result': str(work / 'joint/RESULT.json'),
                 'rmp': str(work / 'joint/FINAL_RMP.npz'), 'state_matrix': str(work / 'joint/STATE_MATRIX.npz'),
                 'new_path_pool': str(work / 'joint/NEW_PATH_POOL.npz'),
                 'independent_certificate': str(work / 'joint/INDEPENDENT_CERT.json'),
                 'seed_receipt': str(seed / 'RECEIPT.json'), 'uniform_paths': str(seed / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'),
                 'seed_independent_certificate': str(seed / 'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json'),
                 'fifo_fragments': str(seed / 'fifo/FRAGMENTS.npz'),
                 'initial_stage': str(initial / 'STAGE.json'), 'initial_path_pool': str(initial / 'INITIAL_PATH_POOL.npz'),
                 'initial_state': str(initial / 'INITIAL_STATE.npz'), 'initial_matrix': str(initial / 'INITIAL_STATE_MATRIX.npz')}
        if name != 'pittsburgh_S2_Q':
            paths['full_price_result'] = str(work / 'joint/FULL_PRICE/RESULT.json')
            paths['full_price_directory'] = str(work / 'joint/FULL_PRICE')
            paths['full_price_certificate'] = str(work / 'joint/FULL_PRICE/INDEPENDENT_DUAL_CERT.json')
    save(work.parent / 'WORKSPACE_INDEX.json', {'schema': 'DEV48_NEW_RUN_WORKSPACE_V1',
         'case_id': case['case_id'], 'branch': case['branch'], 'paths': paths,
         'files_present': {name: Path(path).exists() for name, path in paths.items()},
         'scope': 'New local run only. Listed outputs may not exist until the corresponding computation completes.'})


def prepare(case, output, build=False, input_dir=None):
    output = Path(output).resolve()
    require(not output.is_relative_to(REPO), 'Put generated output outside the source repository.')
    require(not output.is_relative_to(HERE), 'Do not overwrite packaged inputs.')
    count = check_package()
    output.mkdir(parents=True, exist_ok=True)
    binding = output / 'PREPARATION.json'
    if binding.exists():
        require(read(binding)['case_id'] == case['case_id'], 'Output belongs to a different case.')
    elif any(output.iterdir()):
        raise ValueError('Use a new empty output directory.')
    work = output / 'work'
    work.mkdir(exist_ok=True)
    for source in (HERE / 'frozen_sources').glob('*.py'):
        dest = work / source.name
        if dest.exists():
            require(digest(dest) == digest(source), 'Working source changed: ' + str(dest))
        else:
            shutil.copyfile(source, dest)
    core = work / CORE_NAME / 'shared_cg'
    core.mkdir(parents=True, exist_ok=True)
    for source in (HERE / 'shared_cg').glob('*.py'):
        dest = core / source.name
        if dest.exists():
            require(digest(dest) == digest(source), 'Working core changed: ' + str(dest))
        else:
            shutil.copyfile(source, dest)
    source_dir = graph_inputs(case, work, build, input_dir)
    cfg = read(HERE / case['config_file'])
    cfg['core_root'] = str(work / CORE_NAME)
    cfg['output_dir'] = str(work / 'solver')
    if case['branch'] == 'explicit':
        manifest = work / 'input-manifest.json'
        save(manifest, {'dynamic_arc_file': str(source_dir / 'dynamic_arc.csv'),
                        'demand_file': str(source_dir / 'dynamic_demand.csv')})
        cfg['input_manifest'] = str(manifest)
    else:
        cfg['source_dir'] = str(source_dir)
    if case['cold_fifo_seed']:
        cfg['feasible_fifo_seed_npz'] = str(work / f'H_S2_SELECTIVE_FIFO_PATHS_{case["case_id"]}.npz')
    cfg_path = work / 'cases' / (case['case_id'] + '.json')
    save(cfg_path, cfg)
    status = 'INPUTS_READY' if source_dir.exists() else 'GRAPH_CONSTRUCTION_REQUIRED'
    record = {'case_id': case['case_id'], 'branch': case['branch'], 'status': status,
              'package_files_sha_checked': count, 'input_directory': str(source_dir),
              'configuration': str(cfg_path), 'original_config_sha256': case['original_config_sha256'],
              'preparation_config_sha256': digest(cfg_path), 'original_source_hashes': case['expected_inputs'],
              'selected_historical_result': case['selected_result'], 'solver_calls': 0,
              'new_run_is_not_certified_by_historical_receipts': True}
    save(binding, record)
    workspace_index(case, work, cfg_path)
    return work, cfg_path, record


def construct_h_seed(work, case, cfg_path):
    """Rebuild the exact source-derived Q routing and H FIFO construction."""
    hcase = case['case_id']
    qcase = hcase[:-1] + 'Q'
    hcfg = read(cfg_path)
    qcfg = read(HERE / 'configs' / (qcase + '.json'))
    screen = {k: qcfg[k] for k in ('expected_source_hashes', 'dt_seconds', 'release_steps', 'horizon_steps', 'demand_factor')}
    screen['source_hashes'] = screen.pop('expected_source_hashes')
    screen['source_path'] = hcfg['source_dir']
    save(work / f'Q_AON_SCREEN_{qcase}.json', screen)
    save(work / 'cases' / f'{hcase}__sparse_common_dev3_exact_fixed.json', hcfg)
    load_module(work, 'construct_q_fifo_feasible', True).solve(qcase)
    load_module(work, 'construct_q_selective_fifo', True).solve(qcase)
    load_module(work, 'construct_h_s2_selective_fifo', True).solve(hcase, qcase)
    # Compare numerical arrays, not ZIP-container metadata. Bind the new NPZ
    # SHA only after all frozen numerical array hashes have matched.
    import numpy as np
    expected = read(HERE / 'provenance/CONSTRUCTED_SEED_ARRAY_HASHES.json')[hcase]
    with np.load(hcfg['feasible_fifo_seed_npz'], allow_pickle=False) as z:
        actual = {n: {'dtype': str(z[n].dtype), 'shape': list(z[n].shape),
                      'sha256': hashlib.sha256(z[n].tobytes(order='C')).hexdigest()} for n in z.files}
    require(actual == expected['arrays'], 'Generated cold FIFO numerical seed differs from the frozen construction.')
    hcfg['expected_seed_sha256'] = digest(hcfg['feasible_fifo_seed_npz'])
    save(cfg_path, hcfg)


def verify_retained(work, case, cfg_path):
    if case['case_id'] == 'pittsburgh_S2_H':
        primal = load_module(work, 'verify_stage_checkpoint_primal')
        require(primal.verify(str(cfg_path)) == 0, 'New stage primal failed independent verification.')
        cfg = read(cfg_path)
        checkpoints = Path(cfg['output_dir']) / 'STAGE_CHECKPOINTS'
        available = sorted([checkpoints / slot / 'CHECKPOINT_RECEIPT.json' for slot in ('slot_a', 'slot_b')],
                           key=lambda p: read(p)['round'])
        require(sorted(read(p)['round'] for p in available) == [57, 60],
                'New run did not retain the selected 57/60 stages. It cannot inherit the published mixed certificate.')
        d = read(HERE / 'policies/DEV48_PIT_S2_H_COLD_RETRY_V1_MIX_PRE_OUTCOME.json')
        with argv(['--config', cfg_path, '--checkpoint-a', available[0], '--checkpoint-b', available[1],
                   '--alphas', ','.join(map(str, d['alpha_grid'])), '--output', work / 'INDEPENDENT_MIX.json']):
            load_module(work, 'verify_two_stage_dual_mix').main()
        mix = read(work / 'INDEPENDENT_MIX.json')
        upper, lower, gap = (mix['separately_independently_certified_primal_upper'],
                             mix['best_certified_lower'], mix['relative_open_gap'])
        require(all(math.isfinite(v) for v in (upper, lower, gap)) and lower <= upper + 1e-6,
                'New mixed bound is nonfinite or exceeds the independently feasible upper.')
        passed = abs(gap) <= cfg['relative_gap_tolerance'] + 1e-10
        save(work / 'NEW_RUN_ACCEPTANCE.json', {
            'case_id': case['case_id'], 'upper': mix['separately_independently_certified_primal_upper'],
            'lower': mix['best_certified_lower'], 'relative_gap': mix['relative_open_gap'],
            'status': 'PASS_NEW_RUN_MIXED_BOUND_GATE' if passed else 'OPEN',
            'same_run_stages': [57, 60], 'alpha_grid': d['alpha_grid'],
            'mixed_certificate_sha256': digest(work / 'INDEPENDENT_MIX.json')})
        require(passed, 'New 57/60 mixed bound did not meet the selected original gap gate.')
        return
    name = {'explicit': 'verify_explicit', 'implicit': 'verify_implicit_recompute',
            'uniform': 'verify_uniform_release'}[case['branch']]
    require(load_module(work, name).verify(str(cfg_path)) == 0,
            'New result failed independent verification: ' + case['case_id'])


def make_joint_seed(work, case, cfg_path):
    import shared_cg.solve as solver
    from shared_cg.source_fifo import main as fifo
    seed_name = 'dev35_cold_source_seed_urbana_f' if case['case_id'] == 'urbana_F_Q' else 'dev41_cold_source_seed_' + case['case_id']
    seed = work / 'runs' / seed_name
    cfg = read(cfg_path)
    cfg['output_dir'] = str(seed / 'aon')
    save(cfg_path, cfg)
    require(solver.run(str(cfg_path)) == 2, 'Expected the original nonbinding-screen overload before joint CG.')
    require(read(seed / 'aon/RESULT.json')['status'] == 'AON_CAPACITY_OVERLOAD_NEEDS_GENERIC_CG', 'Unexpected source AON status')
    aon = seed / 'aon/UNIFORM_AON_FULL_ORIGINAL_PATHS.npz'
    fifo(cfg_path, aon, seed / 'fifo')
    load_module(work, 'verify_dev35_cold_source_fifo').run(cfg_path, aon, seed / 'fifo')
    cert = read(seed / 'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json')
    require(cert['status'] == 'PASS_FULL_ORIGINAL_OD_RELEASE_PATH_TIME_CAPACITY_OBJECTIVE', 'Unverified new FIFO seed')
    save(seed / 'RECEIPT.json', {
        'schema': 'NEW_RUN_SOURCE_Q_FIFO_SEED', 'status': 'PASS_COLD_SOURCE_ORIGINAL_FEASIBLE_SEED',
        'case_id': case['case_id'], 'source_hashes': cfg['expected_source_hashes'],
        'source_config_sha256': digest(cfg_path), 'AON_result_sha256': digest(seed / 'aon/RESULT.json'),
        'AON_path_sha256': digest(aon), 'FIFO_result_sha256': digest(seed / 'fifo/RESULT.json'),
        'FIFO_fragment_sha256': digest(seed / 'fifo/FRAGMENTS.npz'),
        'independent_certificate_sha256': digest(seed / 'fifo/INDEPENDENT_ORIGINAL_TIME_CERTIFICATE.json'),
        'independent_feasible_upper': cert['independent_feasible_primal_upper'],
        'original_positive_OD': cert['original_positive_OD'], 'original_release_events': cert['original_release_events']})
    return seed


def source_ranked_pool(work, cfg_path, seed):
    """Call the original source-only build stage; skip its unrelated old RMP."""
    module = load_module(work, 'run_dev43_ranked_source_columns_urbana_f')
    source = work / 'runs/dev43_ranked_source_columns_urbana_f'
    module.CFG, module.SEED, module.OUT = cfg_path, seed, source
    module.DESIGN = policy(work, 'DEV43_RANKED_SOURCE_COLUMNS_DESIGN', {
        'source_config_sha256': digest(cfg_path), 'fresh_seed_receipt_sha256': digest(seed / 'RECEIPT.json'),
        'builder_sha256': digest(work / 'run_dev42_source_bundle_urbana_f.py'),
        'runner_sha256': digest(work / 'run_dev43_ranked_source_columns_urbana_f.py')})
    # The source main writes its validated source STAGE before calling state.solve.
    # Extract that exact prefix structurally; no optimizer from the old Dev43 run.
    path = work / 'run_dev43_ranked_source_columns_urbana_f.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    cut = next(i for i, n in enumerate(function.body) if isinstance(n, ast.Assign)
               and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
               and n.value.func.id == 'JointState')
    function.body = function.body[:cut]
    module_tree = ast.Module(body=[function], type_ignores=[])
    exec(compile(module_tree, str(path), 'exec'), module.__dict__)
    module.main()
    builder = load_module(work, 'build_dev46_source_event_pool')
    initial = work / 'runs/dev46_source_event_pool_urbana_f'
    builder.CFG, builder.SEED, builder.SOURCE, builder.OUT = cfg_path, seed, source, initial
    builder.DESIGN = policy(work, 'DEV46_SOURCE_EVENT_POOL_DESIGN', {
        'source_config_sha256': digest(cfg_path), 'fresh_seed_receipt_sha256': digest(seed / 'RECEIPT.json'),
        'source_matrix_sha256': digest(source / 'BUNDLE_MATRIX.npz'),
        'source_paths_sha256': digest(source / 'BUNDLE_SOURCE_PATHS.npz'),
        'source_stage_sha256': digest(source / 'STAGE.json'),
        'builder_sha256': digest(work / 'build_dev46_source_event_pool.py')})
    builder.main()
    return initial


def s2_pool(work, case, cfg_path, seed):
    name = case['case_id']
    version = 'V5' if name == 'urbana_S2_Q' else 'V6'
    builder_name = 'build_dev50_s2_source_event_pool_' + version.lower()
    builder = load_module(work, builder_name)
    builder.CASES = {name: (cfg_path.name, seed.name)}
    policy(work, f'DEV50_{name}_SOURCE_EVENT_POOL_DESIGN_{version}', {
        'builder_sha256': digest(work / (builder_name + '.py')),
        'source_config_sha256': digest(cfg_path), 'fresh_seed_receipt_sha256': digest(seed / 'RECEIPT.json')})
    builder.main(name)
    initial = work / 'runs' / f'dev50_source_event_pool_{name}_{version.lower()}'
    if name == 'pittsburgh_S2_Q':
        policy(work, f'DEV50_{name}_SOURCE_EVENT_POOL_DESIGN_V7', {
            'builder_sha256': digest(work / 'build_dev50_pit_v7_nnz_prefix.py'),
            'parent_v6_stage_sha256': digest(initial / 'STAGE.json'),
            'parent_v6_matrix_sha256': digest(initial / 'INITIAL_STATE_MATRIX.npz'),
            'parent_v6_state_sha256': digest(initial / 'INITIAL_STATE.npz'),
            'parent_v6_path_pool_sha256': digest(initial / 'INITIAL_PATH_POOL.npz')})
        load_module(work, 'build_dev50_pit_v7_nnz_prefix').main()
        initial = work / 'runs' / f'dev50_source_event_pool_{name}_v7'
    return initial


def execute_joint(work, case, cfg_path):
    seed = make_joint_seed(work, case, cfg_path)
    initial = source_ranked_pool(work, cfg_path, seed) if case['case_id'] == 'urbana_F_Q' else s2_pool(work, case, cfg_path, seed)
    suffix = case['case_id']
    design_name = 'DEV48_EVENT_JOINT_CG_DESIGN' if suffix == 'urbana_F_Q' else ('DEV50_' + suffix + '_JOINT_CG_DESIGN' + ('_V7' if suffix == 'pittsburgh_S2_Q' else ''))
    design = policy(work, design_name, {
        'source_config_sha256': digest(cfg_path), 'fresh_seed_receipt_sha256': digest(seed / 'RECEIPT.json'),
        'initial_stage_sha256': digest(initial / 'STAGE.json'),
        'initial_matrix_sha256': digest(initial / 'INITIAL_STATE_MATRIX.npz'),
        'initial_state_sha256': digest(initial / 'INITIAL_STATE.npz'),
        'initial_path_pool_sha256': digest(initial / 'INITIAL_PATH_POOL.npz'),
        'runner_sha256': digest(work / 'run_dev48_event_joint_cg_urbana_f.py')})
    out = work / 'joint'
    engine = load_module(work, 'run_dev48_event_joint_cg_urbana_f')
    engine.CFG, engine.SEED, engine.INITIAL, engine.OUT, engine.DESIGN = cfg_path, seed, initial, out, design
    engine.main()
    verifier = {'urbana_F_Q': 'verify_dev48_event_joint_cg_urbana_f',
                'urbana_S2_Q': 'verify_dev50_s2_joint_cg',
                'pittsburgh_S2_Q': 'verify_dev50_s2_joint_cg_pit_v7'}[suffix]
    audit = load_module(work, verifier)
    audit.CFG, audit.SEED, audit.INITIAL, audit.OUT, audit.DESIGN = cfg_path, seed, initial, out, design
    audit.main()
    # Two displayed Q cases have same-run full pricing; Pittsburgh S2 Q has none.
    # Do not silently invent that missing published bound.
    if suffix != 'pittsburgh_S2_Q':
        price_name = 'price_dev48_event_joint_full_q' if suffix == 'urbana_F_Q' else 'price_dev50_s2_joint_full_q'
        price = load_module(work, price_name)
        price.ROOT, price.OUT, price.CFG = out, out / 'FULL_PRICE', cfg_path
        price.DESIGN = design
        price.main()
        audit = load_module(work, 'verify_dev48_event_joint_full_q')
        audit.ROOT, audit.OUT, audit.CASE = out, out / 'FULL_PRICE', cfg_path
        audit.main()
    return out / 'RESULT.json'


def execute(work, case, cfg_path):
    sys.path.insert(0, str(work))
    sys.path.insert(0, str(work / CORE_NAME))
    if case['branch'] == 'joint':
        result_path = execute_joint(work, case, cfg_path)
        verified = True
    else:
        if case['cold_fifo_seed']:
            construct_h_seed(work, case, cfg_path)
        import shared_cg.solve as solver
        code = solver.run(str(cfg_path))
        result_path = Path(read(cfg_path)['output_dir']) / 'RESULT.json'
        # A round limit is a scientific state, not permission to reuse old proof.
        if code == 0 or case['case_id'] == 'pittsburgh_S2_H':
            verify_retained(work, case, cfg_path)
            verified = True
        else:
            verified = False
    result = read(result_path)
    workspace_index(case, work, cfg_path)
    index = read(work.parent / 'WORKSPACE_INDEX.json')
    certificates = {key: {'path': path, 'sha256': digest(path), 'status': read(path).get('status')}
                    for key, path in index['paths'].items()
                    if 'certificate' in key and Path(path).is_file()}
    outputs = {key: {'path': str(Path(path).resolve()), 'sha256': digest(path)}
               for key, path in index['paths'].items() if Path(path).is_file()}
    report = {'case_id': case['case_id'], 'new_result_file': str(result_path),
              'new_result_sha256': digest(result_path), 'new_status': result['status'],
              'execution_config': str(cfg_path), 'execution_config_sha256': digest(cfg_path),
              'independent_verification': 'PASSED_WITHIN_REPORTED_SCOPE' if verified else 'NOT_RUN_PRODUCER_DID_NOT_CLOSE',
              'new_certificates': certificates, 'new_outputs': outputs, 'exit_code': 0 if verified else 2,
              'original_selected_result': case['selected_result'],
              'original_receipts_do_not_certify_new_run': True,
              'note': 'Compare new independently verified outputs; do not replace original published values automatically.'}
    save(work.parent / 'NEW_RUN.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='List the 16 registered instances.')
    parser.add_argument('--case', choices=[c['case_id'] for c in read(HERE / 'cases.json')['cases']])
    parser.add_argument('--output', help='Fresh generated workspace outside the repository.')
    parser.add_argument('--input-dir', help='Use upstream-generated model inputs; frozen SHA must match.')
    parser.add_argument('--prepare-graphs', action='store_true', help='Also generate Berkeley/Chicago time graphs, no optimizer.')
    parser.add_argument('--execute', action='store_true', help='Explicitly construct seeds/pools, solve and independently verify a NEW run.')
    args = parser.parse_args()
    if args.list:
        print(json.dumps(read(HERE / 'cases.json'), indent=2))
        return 0
    if not args.case or not args.output:
        parser.error('--case and --output are required unless --list is used')
    case = get_case(args.case)
    work, cfg, record = prepare(case, args.output, args.execute or args.prepare_graphs, args.input_dir)
    print(json.dumps(record, indent=2))
    if args.execute:
        report = execute(work, case, cfg)
        print(json.dumps(report, indent=2))
        return report['exit_code']
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
