"""Run native FreeCAD checks for approved A11 axis-2 nominal HEA members."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import traceback


ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).with_name("allshield_axis_02.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_02_draft.json")


def _load_module():
    spec = importlib.util.spec_from_file_location("allshield_axis02_under_test", str(MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(output_dir=None):
    out = Path(output_dir or os.environ.get(
        "ALLSHIELD_TEST_OUTPUT",
        ROOT / "outputs" / ("axis02_native_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")),
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
        axis01 = module._load_axis01()
        axis07 = axis01._load_axis07()
        axis08 = axis07._load_axis08()
        doc = module.build_axis_02(out)
        try:
            before = module.audit_axis_02(doc, catalog, axis01, axis07, axis08)
            (out / "axis02_before_save.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
            target = out / "Axis02_WORK.FCStd"
            if target.exists():
                raise FileExistsError("Refusing to overwrite " + str(target))
            object_count = len(doc.Objects)
            doc.saveAs(str(target))
            App.closeDocument(doc.Name)
            doc = None
            reopened = App.openDocument(str(target))
            try:
                reopened.recompute()
                after = module.audit_axis_02(reopened, catalog, axis01, axis07, axis08)
                (out / "axis02_after_reopen.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
                member = reopened.getObject("A11_02_311")
                old_placement = member.LinkPlacement
                shifted_placement = App.Placement(old_placement)
                shifted_placement.Base = old_placement.Base + App.Vector(100, 0, 0)
                try:
                    member.LinkPlacement = shifted_placement
                    reopened.recompute()
                    try:
                        module.audit_axis_02(reopened, catalog, axis01, axis07, axis08)
                    except AssertionError as error:
                        shift_detected = "A11_02_311" in str(error)
                    else:
                        shift_detected = False
                    if not shift_detected:
                        raise AssertionError("Negative control: 100-mm member shift was not detected.")
                finally:
                    member.LinkPlacement = old_placement
                    reopened.recompute()
                summary.update({
                    "status": "PASS",
                    "axis02_members_checked": before["members_checked"],
                    "document_objects": object_count,
                    "fcstd": str(target),
                    "fcstd_bytes": target.stat().st_size,
                    "save_reopen_pass": True,
                    "negative_100mm_shift_detected": shift_detected,
                    "meaning": "Native consistency of the four approved nominal A11/as-2 members (HEA180 columns 313/311/312 and HEA160 horizontal 301) plus retained axis-8, axis-7 and axis-1 slices; not as-built or fabrication verification.",
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
        (out / "axis02_native_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("ALLSHIELD_AXIS02_NATIVE_RESULT=" + str(out / "axis02_native_summary.json"))
        print("ALLSHIELD_AXIS02_NATIVE_STATUS=" + summary["status"])
    return summary


if __name__ == "__main__":
    result = run()
    if result["status"] != "PASS":
        raise RuntimeError("Axis-2 native test failed; see axis02_native_summary.json")