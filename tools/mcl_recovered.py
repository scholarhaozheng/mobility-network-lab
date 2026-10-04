"""Portable entries for recovered experiments; historical inspection is not a fresh solve."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ('list', 'describe', 'check', 'run', 'inspect', 'verify', 'acquire')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''): h.update(part)
    return h.hexdigest()

def rooted(root, relative):
    rel = Path(relative)
    path = (root / rel).resolve()
    if rel.is_absolute() or ':' in str(relative) or not path.is_relative_to(root):
        raise ValueError('Repository-relative path required: ' + str(relative))
    return path

def records(root):
    result = {}
    for manifest in sorted((root / 'experiments/recovered').glob('*.json')):
        data = read(manifest)
        for entry in data.get('records', []):
            if entry['id'] in result: raise ValueError('Duplicate recovered record: ' + entry['id'])
            item = dict(entry)
            item['manifest'] = manifest.relative_to(root).as_posix()
            result[item['id']] = item
    return result

def check(root, entry):
    checks, errors = [], []
    for item in entry.get('files', []):
        path = rooted(root, item['path'])
        actual = sha(path) if path.is_file() else None
        ok = actual == item.get('sha256') and actual is not None
        checks.append({'path': item['path'], 'sha256': actual, 'expected': item.get('sha256'), 'matches': ok})
        if not ok: errors.append('Missing or changed pinned file: ' + item['path'])
    entrypoint = entry.get('entrypoint')
    if entrypoint and not any(f['path'] == entrypoint for f in entry.get('files', [])):
        errors.append('Entrypoint is not hash-pinned')
    return {'id': entry['id'], 'status': 'PASS' if not errors else 'FAIL', 'files': checks,
            'errors': errors, 'state': entry.get('state'), 'environment': entry.get('environment', {}),
            'external_inputs': entry.get('dataSources', []), 'scope': 'Packaged file integrity only; no numerical computation.'}

def invoke(root, entry, args):
    if args.action not in entry.get('supportedActions', []):
        raise ValueError('Action is not available for this record: ' + args.action)
    checked = check(root, entry)
    if checked['errors']: raise ValueError('; '.join(checked['errors']))
    if not entry.get('entrypoint'): raise ValueError('No executable entrypoint for this scope record')
    script = rooted(root, entry['entrypoint'])
    command = [sys.executable, '-B', str(script), args.action, '--repo-root', str(root)]
    target = args.run if args.action == 'verify' else args.output
    if target is None: raise ValueError('Supply --run for verify, or --output for other actions')
    target = target.resolve()
    if target.is_relative_to(root):
        raise ValueError('Keep recovered outputs outside the repository; use ../results/RECORD_ID-action')
    if args.action == 'verify':
        if not target.is_dir(): raise ValueError('Run directory does not exist')
        identities = [target / 'entry-run.json', target / 'entry-inspect.json']
        matched = []
        for identity in identities:
            if identity.is_file():
                saved = read(identity)
                if saved.get('id') == entry['id'] and saved.get('exit_code') == 0 and saved.get('entrypoint_sha256') == sha(script):
                    matched.append(saved)
        if not matched:
            raise ValueError('No matching successful run/inspect receipt for this record and adapter; use the same entry or the original adapter to verify direct runs')
        command += ['--run', str(target)]
    else:
        if target.exists() and (not target.is_dir() or any(target.iterdir())):
            raise ValueError('Output must be a new or empty directory')
        command += ['--output', str(target)]
    command += entry.get('arguments', ['--record', entry['id']])
    if args.input_root: command += ['--input-root', str(args.input_root.resolve())]
    if getattr(args, 'ipopt', None): command += ['--ipopt', str(args.ipopt.resolve())]
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    start = time.perf_counter()
    timed_out = False
    with tempfile.TemporaryFile(mode='w+b') as log:
        try:
            process = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=args.timeout or entry.get('timeoutSeconds', 900), shell=False,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            code = process.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = 124, True
        log.seek(0)
        output = log.read().decode('utf-8', errors='replace')
    target.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'mcl_recovered_execution_v1', 'id': entry['id'], 'action': args.action,
               'exit_code': code, 'timed_out': timed_out, 'seconds': time.perf_counter() - start,
               'command': command, 'entrypoint_sha256': sha(script), 'manifest_sha256': sha(root / entry['manifest']),
               'front_end_sha256': sha(Path(__file__)), 'checked_files': len(checked['files']),
               'success': code == 0,
               'evidence_basis': ('fresh_execution' if args.action == 'run' else 'saved_result_inspection' if args.action == 'inspect' else args.action) if code == 0 else 'failed_execution_attempt',
               'scope': entry.get('scope', '')}
    (target / ('entry-' + args.action + '.log')).write_text(output, encoding='utf-8')
    (target / ('entry-' + args.action + '.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    if code and output: print(output[-8000:], file=sys.stderr)
    return code

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=ACTIONS)
    parser.add_argument('id', nargs='?')
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--input-root', type=Path, help='Local exact external input snapshot, where the selected adapter supports it')
    parser.add_argument('--ipopt', type=Path, help='Installed IPOPT executable for supported native recipes')
    parser.add_argument('--timeout', type=int, help='Optional maximum command time in seconds')
    parser.add_argument('--city')
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        entries = records(root)
        if args.action == 'list':
            print(json.dumps([{'id': e['id'], 'title': e['title'], 'city': e.get('city'), 'state': e.get('state'),
                               'actions': e.get('supportedActions', []), 'evidenceBasis': e.get('evidenceBasis')}
                              for e in entries.values() if not args.city or e.get('city') == args.city], indent=2))
            return 0
        if args.action == 'check' and not args.id:
            reports = [check(root, e) for e in entries.values()]
            print(json.dumps({'status': 'PASS' if all(r['status'] == 'PASS' for r in reports) else 'FAIL',
                              'records': len(reports), 'checks': reports}, indent=2))
            return 0 if all(r['status'] == 'PASS' for r in reports) else 2
        if args.id not in entries: raise ValueError('Unknown recovered record; use list')
        entry = entries[args.id]
        if args.action == 'describe': print(json.dumps(entry, indent=2)); return 0
        if args.action == 'check':
            report = check(root, entry); print(json.dumps(report, indent=2)); return 0 if report['status'] == 'PASS' else 2
        return invoke(root, entry, args)
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error': str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__': raise SystemExit(main())
