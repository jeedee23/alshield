"""Run native FreeCAD checks for the DN900 roof-penetration planning marker."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).with_name("allshield_roof_penetration_zones.py")
CATALOG = Path(__file__).with_name("roof_penetration_zone_catalog_draft.json")
ZONE_ID = "Planned_Roof_Penetration_DN900_01"


def _load_module():
    spec = importlib.util.spec_from_file_location("allshield_roof_penetration_zones_under_test", str(MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(output_dir=None):
    out = Path(output_dir or os.environ.get("ALLSHIELD_TEST_OUTPUT", ROOT / "outputs" / ("roof_penetration_zone_native_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))).resolve()
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
        axis01_wvb = module._load_axis01_wvb()
        doc = module.build_roof_penetration_zones(out)
        try:
            before = module.audit_roof_penetration_zones(doc, catalog, axis01_wvb)
            (out / "roof_penetration_zone_before_save.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
            target = out / "Roof_Penetration_Zone_WORK.FCStd"
            if target.exists():
                raise FileExistsError("Refusing to overwrite " + str(target))
            object_count = len(doc.Objects)
            doc.saveAs(str(target))
            App.closeDocument(doc.Name)
            doc = None
            reopened = App.openDocument(str(target))
            try:
                reopened.recompute()
                after = module.audit_roof_penetration_zones(reopened, catalog, axis01_wvb)
                (out / "roof_penetration_zone_after_reopen.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
                zone = reopened.getObject(ZONE_ID)
                original_shape = zone.Shape.copy()
                shifted = original_shape.copy()
                shifted.translate(App.Vector(100.0, 0.0, 0.0))
                try:
                    zone.Shape = shifted
                    reopened.recompute()
                    try:
                        module.audit_roof_penetration_zones(reopened, catalog, axis01_wvb)
                    except AssertionError as error:
                        shift_detected = "Effective world bounds mismatch" in str(error)
                    else:
                        shift_detected = False
                    if not shift_detected:
                        raise AssertionError("Negative control: 100-mm marker shift was not detected.")
                finally:
                    zone.Shape = original_shape
                    reopened.recompute()
                summary.update({
                    "status": "PASS",
                    "zones_checked": before["zones_checked"],
                    "document_objects": object_count,
                    "fcstd": str(target),
                    "fcstd_bytes": target.stat().st_size,
                    "save_reopen_pass": True,
                    "negative_100mm_shift_detected": shift_detected,
                    "physical_roof_cutout_created": False,
                    "panel_containment_verified": False,
                    "known_modelled_wvb_clearance_checked": True,
                    "meaning": "Native consistency of one non-cutting DN900 roof-penetration marker and retained preceding layers; not as-built, panel-containment or fabrication verification.",
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
        (out / "roof_penetration_zone_native_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("ALLSHIELD_ROOF_PENETRATION_ZONE_NATIVE_RESULT=" + str(out / "roof_penetration_zone_native_summary.json"))
        print("ALLSHIELD_ROOF_PENETRATION_ZONE_NATIVE_STATUS=" + summary["status"])
    return summary


if __name__ == "__main__":
    result = run()
    if result["status"] != "PASS":
        raise RuntimeError("Roof-penetration zone native test failed; see roof_penetration_zone_native_summary.json")