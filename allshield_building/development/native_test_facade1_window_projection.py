"""Run native FreeCAD checks for the Facade_1 C4a planar window-bank projection."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).with_name("allshield_facade1_window_projection.py")
CATALOG = Path(__file__).with_name("facade1_window_projection_catalog_draft.json")
OUTER_PROJECTION_ID = "Facade1_C4a_WindowBank_01_OuterFrameProjection"


def _load_module():
    spec = importlib.util.spec_from_file_location("allshield_facade1_window_projection_under_test", str(MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(output_dir=None):
    out = Path(output_dir or os.environ.get("ALLSHIELD_TEST_OUTPUT", ROOT / "outputs" / ("facade1_window_projection_native_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "native_runtime_started": False,
        "gui_tested": False,
        "as_built_verified": False,
        "fabrication_model": False,
        "catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
    }
    try:
        import FreeCAD as App

        summary["native_runtime_started"] = True
        summary["freecad_version"] = list(App.Version())
        module = _load_module()
        catalog = module._load_catalog()
        roof_zones = module._load_roof_zones()
        doc = module.build_facade1_window_projection(out)
        try:
            before = module.audit_facade1_window_projection(doc, catalog, roof_zones)
            (out / "facade1_window_projection_before_save.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
            target = out / "Facade1_Window_Projection_WORK.FCStd"
            if target.exists():
                raise FileExistsError("Refusing to overwrite " + str(target))
            object_count = len(doc.Objects)
            doc.saveAs(str(target))
            App.closeDocument(doc.Name)
            doc = None
            reopened = App.openDocument(str(target))
            try:
                reopened.recompute()
                after = module.audit_facade1_window_projection(reopened, catalog, roof_zones)
                (out / "facade1_window_projection_after_reopen.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
                projection = reopened.getObject(OUTER_PROJECTION_ID)
                original_shape = projection.Shape.copy()
                shifted = original_shape.copy()
                shifted.translate(App.Vector(100.0, 0.0, 0.0))
                try:
                    projection.Shape = shifted
                    reopened.recompute()
                    try:
                        module.audit_facade1_window_projection(reopened, catalog, roof_zones)
                    except AssertionError as error:
                        shift_detected = OUTER_PROJECTION_ID in str(error)
                    else:
                        shift_detected = False
                    if not shift_detected:
                        raise AssertionError("Negative control: 100-mm window-projection shift was not detected.")
                finally:
                    projection.Shape = original_shape
                    reopened.recompute()
                summary.update({
                    "status": "PASS",
                    "window_banks_checked": before["window_banks_checked"],
                    "projection_objects_checked": before["projection_objects_checked"],
                    "document_objects": object_count,
                    "fcstd": str(target),
                    "fcstd_bytes": target.stat().st_size,
                    "save_reopen_pass": True,
                    "negative_100mm_shift_detected": shift_detected,
                    "physical_window_frame_created": False,
                    "inner_or_street_side_frame_depth_verified": False,
                    "meaning": "Native consistency of one directly projected C4a Facade_1 window bank plus preceding layers; not physical frame, glazing, as-built or fabrication verification.",
                })
            finally:
                App.closeDocument(reopened.Name)
        finally:
            if doc is not None and doc.Name in App.listDocuments():
                App.closeDocument(doc.Name)
    except Exception:
        summary["status"] = "FAIL"
        summary["traceback"] = traceback.format_exc()
        print(summary["traceback"])
    finally:
        (out / "facade1_window_projection_native_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("ALLSHIELD_FACADE1_WINDOW_PROJECTION_NATIVE_RESULT=" + str(out / "facade1_window_projection_native_summary.json"))
        print("ALLSHIELD_FACADE1_WINDOW_PROJECTION_NATIVE_STATUS=" + summary["status"])
    return summary


if __name__ == "__main__":
    result = run()
    if result["status"] != "PASS":
        raise RuntimeError("Facade_1 window-projection native test failed; see facade1_window_projection_native_summary.json")