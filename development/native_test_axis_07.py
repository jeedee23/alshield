"""Run native FreeCAD checks for the approved A11 axis-7 nominal profile slice."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import traceback


ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).with_name("allshield_axis_07.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_07_draft.json")


def _load_module():
    spec = importlib.util.spec_from_file_location("allshield_axis07_under_test", str(MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(output_dir=None):
    out = Path(output_dir or os.environ.get(
        "ALLSHIELD_TEST_OUTPUT",
        ROOT / "outputs" / ("axis07_native_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")),
    )).resolve()
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
        axis08 = module._load_axis08()
        doc = module.build_axis_07(out)
        try:
            before = module.audit_axis_07(doc, catalog, axis08)
            (out / "axis07_before_save.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
            target = out / "Axis07_WORK.FCStd"
            if target.exists():
                raise FileExistsError("Refusing to overwrite " + str(target))
            object_count = len(doc.Objects)
            doc.saveAs(str(target))
            App.closeDocument(doc.Name)
            doc = None
            reopened = App.openDocument(str(target))
            try:
                reopened.recompute()
                after = module.audit_axis_07(reopened, catalog, axis08)
                (out / "axis07_after_reopen.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
                member = reopened.getObject("A11_07_314")
                old_placement = member.LinkPlacement
                shifted_placement = App.Placement(old_placement)
                shifted_placement.Base = old_placement.Base + App.Vector(100, 0, 0)
                try:
                    member.LinkPlacement = shifted_placement
                    reopened.recompute()
                    try:
                        module.audit_axis_07(reopened, catalog, axis08)
                    except AssertionError as error:
                        shift_detected = "A11_07_314" in str(error)
                    else:
                        shift_detected = False
                    if not shift_detected:
                        raise AssertionError("Negative control: 100-mm member shift was not detected.")
                finally:
                    member.LinkPlacement = old_placement
                    reopened.recompute()
                summary.update({
                    "status": "PASS",
                    "members_checked": before["members_checked"],
                    "document_objects": object_count,
                    "fcstd": str(target),
                    "fcstd_bytes": target.stat().st_size,
                    "save_reopen_pass": True,
                    "negative_100mm_shift_detected": shift_detected,
                    "meaning": "Native consistency of the seventeen approved nominal A11/as-7 members (IPE500 columns 356/357, IPE450 rafters 349/350, IPE180 horizontals 334/331/333/328/330/332, HEA200 verticals 326/321/317/320/325, HEA180 horizontal 314 and HEA160 horizontal 300) plus retained axis-8 slice; not as-built or fabrication verification.",
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
        (out / "axis07_native_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("ALLSHIELD_AXIS07_NATIVE_RESULT=" + str(out / "axis07_native_summary.json"))
        print("ALLSHIELD_AXIS07_NATIVE_STATUS=" + summary["status"])
    return summary


if __name__ == "__main__":
    result = run()
    if result["status"] != "PASS":
        raise RuntimeError("Axis-7 native test failed; see axis07_native_summary.json")