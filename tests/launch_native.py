"""Launch installed FreeCADCmd with a timeout. Requires only standard Python.

Example (Windows):
py -3 tests/launch_native.py --exe "C:/Program Files/FreeCAD 1.0/bin/FreeCADCmd.exe"
The executable path is an example; use the actual installed path.
"""
from pathlib import Path
from datetime import datetime
import argparse
import json
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', required=True, type=Path, help='Actual FreeCADCmd executable')
    parser.add_argument('--script', type=Path, help='Optional in-workspace FreeCAD Python test script')
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    exe = args.exe.expanduser().resolve()
    if not exe.is_file():
        parser.error('Executable does not exist: ' + str(exe))
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    root = Path(__file__).resolve().parents[1]
    output = root / 'outputs' / ('native_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env['ALLSHIELD_TEST_OUTPUT'] = str(output)
    native_test = (args.script or root / 'tests' / 'native_test.py').expanduser().resolve()
    if not native_test.is_file():
        parser.error('Test script does not exist: ' + str(native_test))
    try:
        native_test.relative_to(root)
    except ValueError:
        parser.error('Test script must be inside the workspace: ' + str(native_test))
    command = [str(exe), '--console']
    console_input = (
        "script_path = %r\n"
        "namespace = {'__name__': '__main__', '__file__': script_path}\n"
        "exec(compile(open(script_path, encoding='utf-8').read(), script_path, 'exec'), namespace)\n"
    ) % str(native_test)
    print('Output:', output, flush=True)
    state = {'command': command, 'script': str(native_test), 'native_status': 'NOT_COMPLETED'}
    try:
        with (output / 'freecadcmd.log').open('w', encoding='utf-8') as log:
            process = subprocess.run(command, cwd=str(root), env=env,
                input=console_input, text=True, stdout=log, stderr=subprocess.STDOUT,
                timeout=args.timeout, check=False)
        state['returncode'] = process.returncode
        summary = output / 'native_summary.json'
        if not summary.exists():
            candidates = sorted(output.glob('*_native_summary.json'))
            if len(candidates) == 1:
                summary = candidates[0]
        state['summary'] = str(summary) if summary.exists() else None
        if summary.exists():
            state['native_status'] = json.loads(summary.read_text(encoding='utf-8')).get('status')
        ok = process.returncode == 0 and state['native_status'] == 'PASS'
    except subprocess.TimeoutExpired:
        state['timeout_seconds'] = args.timeout
        ok = False
    except Exception as exc:
        state['error'] = repr(exc)
        ok = False
    state['pass'] = ok
    (output / 'launcher_result.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
    print('PASS' if ok else 'FAIL - inspect logs; do not remove checks to force a pass')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
