"""Standard-Python checks. PASS is NOT native FreeCAD validation."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    model = ROOT / 'model'
    spec = importlib.util.spec_from_file_location('static_generator', str(model / 'allshield_build.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    data = json.loads((model / 'allshield_building_02.json').read_text(encoding='utf-8'))
    m.validate_data(data)
    assert (model / 'allshield_build.py').read_bytes() == (model / 'Allshield_Build.FCMacro').read_bytes(), 'Macro/Python mismatch'
    failures = []
    for src in data['sources']:
        candidates = [ROOT / 'sources' / 'pdf' / src['filename'], ROOT / 'reference' / src['filename']]
        p = next((x for x in candidates if x.is_file()), None)
        if p is None:
            failures.append('Source missing: ' + src['filename'])
        elif hashlib.sha256(p.read_bytes()).hexdigest() != src['sha256']:
            failures.append('Source hash mismatch: ' + src['filename'])
    assert not failures, '\n'.join(failures)
    counts = {}
    for mode in ['WORK', 'PANELS']:
        nodes = m.active_nodes(data, dict(data['settings'], detail_mode=mode))
        shapes = [c for c in nodes if 'geometry' in c]
        style_keys = set()
        for c in shapes:
            _, _, digest = m.canonical_geometry(c['geometry'])
            style_keys.add(digest + ':' + c.get('material_role', c.get('category', 'wall')))
        counts[mode] = {'active_geometry_nodes': len(shapes), 'shape_style_prototypes': len(style_keys)}
    negative = {}
    bad = copy.deepcopy(data)
    bad['units'] = 'm'
    try:
        m.validate_data(bad)
    except ValueError:
        negative['wrong_units_rejected'] = True
    else:
        raise AssertionError('Wrong units not rejected')
    bad = copy.deepcopy(data)
    bad['components'][0]['name'] = 'Microwave placeholder'
    try:
        m.validate_data(bad)
    except ValueError:
        negative['excluded_machine_rejected'] = True
    else:
        raise AssertionError('Excluded machine not rejected')
    report = {'status': 'PASS_STATIC_ONLY', 'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'component_nodes': len(data['components']),
        'geometry_nodes_all_modes': sum('geometry' in c for c in data['components']),
        'mode_counts': counts, 'negative_controls': negative,
        'source_hashes_match': True, 'native_FreeCAD_executed': False,
        'GUI_executed': False, 'notes': 'Structure, source byte identity and pure-Python functions only; not a shape/kernel test.'}
    out = ROOT / 'verification'
    out.mkdir(exist_ok=True)
    (out / 'static_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
