"""Run inside real FreeCADCmd, or import from the GUI test macro.

Tests implementation consistency against the supplied JSON, not as-built truth.
Only closes documents created by this test. Never opens a user document.
Native FreeCAD execution was NOT available when this handoff was prepared.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'model' / 'allshield_build.py'
DATA = ROOT / 'model' / 'allshield_building_02.json'
TOL = 0.01  # Numerical transform tolerance, NOT a physical survey tolerance.


def read_generator():
    spec = importlib.util.spec_from_file_location('allshield_under_test', str(MODEL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_bounds(g):
    """Independent JSON-to-world bounding box; do not call generator's helper."""
    kind = g['kind']
    if kind == 'box':
        pts = [g['origin'], [g['origin'][i] + g['size'][i] for i in range(3)]]
    elif kind in ('face', 'prism'):
        pts = list(g['outer'])
        if kind == 'prism':
            pts += [[p[i] + g['vector'][i] for i in range(3)] for p in g['outer']]
    elif kind == 'lines':
        pts = [p for segment in g['segments'] for p in segment]
    elif kind == 'polyline':
        pts = g['points']
    else:
        raise ValueError('Unknown geometry kind: ' + kind)
    return [min(p[i] for p in pts) for i in range(3)] + [max(p[i] for p in pts) for i in range(3)]


def descendants(obj):
    seen, todo = set(), [obj]
    while todo:
        node = todo.pop()
        if node.Name in seen:
            continue
        seen.add(node.Name)
        todo.extend(list(getattr(node, 'Group', [])))
    return seen


def audit_document(doc, nodes, Part):
    failures, rows = [], []
    root = doc.getObject('Building')
    library = doc.getObject('Component_Library')
    if root is None or library is None:
        raise AssertionError('Missing Building or Component_Library')
    building_members = descendants(root)
    if library.Name in building_members:
        failures.append('Component_Library is nested inside Building')
    for obj in getattr(library, 'Group', []):
        if obj.Name in building_members:
            failures.append('Prototype is also in Building: ' + obj.Name)
    expected_ids = {c['id'] for c in nodes}
    for c in nodes:
        obj = doc.getObject(c['id'])
        if obj is None:
            failures.append('Missing component ' + c['id'])
            continue
        if re.search(r'magnetron|microwave', obj.Name + ' ' + obj.Label, re.I):
            failures.append('Excluded machine component: ' + obj.Name)
        parent_id = c.get('parent_id')
        if parent_id:
            parent = doc.getObject(parent_id)
            if parent is None or obj not in getattr(parent, 'Group', []):
                failures.append('Wrong parent: ' + c['id'])
        if 'geometry' not in c:
            continue
        if obj.TypeId != 'App::Link':
            failures.append('Expected App::Link: ' + c['id'])
        if getattr(obj, 'LinkedObject', None) is None:
            failures.append('Missing linked source: ' + c['id'])
        if 'LinkTransform' in obj.PropertiesList and obj.LinkTransform:
            failures.append('Unexpected LinkTransform=True: ' + c['id'])
        # Requires the actual FreeCAD Part API; no mock or raw Shape substitute.
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid():
            failures.append('Empty/invalid effective shape: ' + c['id'])
            continue
        b = shape.BoundBox
        actual = [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]
        target = expected_bounds(c['geometry'])
        delta = max(abs(a-b) for a, b in zip(actual, target))
        if not math.isfinite(delta) or delta > TOL:
            failures.append('World bounds mismatch: %s (%s mm)' % (c['id'], delta))
        kind = c['geometry']['kind']
        if kind in ('box', 'prism') and (not shape.Solids or shape.Volume <= 0):
            failures.append('Expected nonzero solid: ' + c['id'])
        rows.append({'id': c['id'], 'representation': kind,
                     'category': c.get('category'), 'max_bbox_error_mm': delta,
                     'world_bbox_mm': actual, 'solids': len(shape.Solids),
                     'faces': len(shape.Faces), 'edges': len(shape.Edges)})
    for obj in doc.Objects:
        if obj.TypeId == 'App::Link' and obj.Name not in expected_ids:
            failures.append('Unexpected geometry instance: ' + obj.Name)
    report = {'pass': not failures, 'checked_geometry_instances': len(rows),
              'max_bbox_error_mm': max((r['max_bbox_error_mm'] for r in rows), default=0),
              'computational_tolerance_mm': TOL, 'failures': failures,
              'as_built_verified': False, 'instances': rows}
    return report


def run(out_dir=None):
    out = Path(out_dir or os.environ.get('ALLSHIELD_TEST_OUTPUT', ROOT / 'outputs' / ('native_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f')))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    summary = {'status': 'RUNNING', 'started_utc': datetime.now(timezone.utc).isoformat(),
               'native_runtime_started': False, 'gui_tested': False,
               'model_completeness_certified': False, 'as_built_verified': False,
               'json_sha256': hashlib.sha256(DATA.read_bytes()).hexdigest(), 'modes': {}}
    summary_path = out / 'native_summary.json'
    try:
        import FreeCAD as App
        import Part
        summary['native_runtime_started'] = True
        summary['freecad_version'] = list(App.Version())
        summary['python_version'] = sys.version
        summary['executable'] = sys.executable
        summary['gui_up'] = bool(getattr(App, 'GuiUp', False))
        summary['occ_version'] = str(getattr(Part, 'OCC_VERSION', 'not exposed'))
        module = read_generator()
        data = json.loads(DATA.read_text(encoding='utf-8'))
        module.validate_data(data)
        preexisting = set(App.listDocuments())
        for mode in ('WORK', 'PANELS'):
            start = time.perf_counter()
            settings = dict(data['settings'])
            settings.update(detail_mode=mode, autosave=False, validate_shapes=True)
            nodes = module.active_nodes(data, settings)
            doc = module.build_from_json(str(DATA), overrides=settings)
            try:
                if doc.Name in preexisting:
                    raise AssertionError('Generator reused an existing document')
                first = audit_document(doc, nodes, Part)
                (out / (mode + '_before_save.json')).write_text(json.dumps(first, indent=2), encoding='utf-8')
                if not first['pass']:
                    raise AssertionError('Before-save audit failed: ' + '; '.join(first['failures'][:8]))
                target = out / (mode + '.FCStd')
                if target.exists():
                    raise FileExistsError('Refusing to overwrite ' + str(target))
                doc.saveAs(str(target))
                object_count = len(doc.Objects)
                App.closeDocument(doc.Name)
                doc = None
                reopened = App.openDocument(str(target))
                try:
                    reopened.recompute()
                    second = audit_document(reopened, nodes, Part)
                    (out / (mode + '_after_reopen.json')).write_text(json.dumps(second, indent=2), encoding='utf-8')
                    if not second['pass']:
                        raise AssertionError('After-reopen audit failed: ' + '; '.join(second['failures'][:8]))
                    # Negative control: a known shift must be detected; restore
                    # immediately in memory and never save the shifted document.
                    node = next(c for c in nodes if c.get('geometry', {}).get('kind') == 'box')
                    obj = reopened.getObject(node['id'])
                    old = obj.LinkPlacement
                    shifted = App.Placement(old)
                    shifted.Base = old.Base + App.Vector(100, 0, 0)
                    try:
                        obj.LinkPlacement = shifted
                        reopened.recompute()
                        neg = audit_document(reopened, nodes, Part)
                        detected = any(node['id'] in s for s in neg['failures'])
                        if not detected:
                            raise AssertionError('Negative control: 100-mm shift was not detected')
                    finally:
                        obj.LinkPlacement = old
                        reopened.recompute()
                    summary['modes'][mode] = {'pass': True, 'geometry_instances': first['checked_geometry_instances'],
                        'document_objects': object_count, 'fcstd': str(target),
                        'fcstd_bytes': target.stat().st_size, 'elapsed_seconds': time.perf_counter() - start,
                        'save_reopen_pass': True, 'negative_shift_detected': detected}
                finally:
                    App.closeDocument(reopened.Name)
            finally:
                if doc is not None and doc.Name not in preexisting and doc.Name in App.listDocuments():
                    App.closeDocument(doc.Name)
        summary['status'] = 'PASS'
        summary['meaning'] = 'Native JSON-to-FreeCAD consistency only; GUI and source-to-real-building checks still required.'
    except Exception:
        summary['status'] = 'FAIL'
        summary['traceback'] = traceback.format_exc()
        print(summary['traceback'])
    finally:
        summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print('ALLSHIELD_NATIVE_RESULT=' + str(summary_path))
        print('ALLSHIELD_NATIVE_STATUS=' + summary['status'])
    return summary


if __name__ == '__main__':
    result = run()
    # The launcher also checks the JSON: FreeCAD versions may handle exit codes differently.
    if result['status'] != 'PASS':
        raise RuntimeError('Allshield native tests failed; see native_summary.json')
