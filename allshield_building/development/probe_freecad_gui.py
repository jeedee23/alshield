"""Verify that the installed full FreeCAD GUI can execute a positional Python script."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "outputs" / ("gui_runtime_probe_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "freecad_version": list(App.Version()),
        "gui_up": bool(getattr(App, "GuiUp", False)),
        "test_document_created": False,
        "test_document_closed": False,
    }
    document = None
    try:
        if not report["gui_up"]:
            raise RuntimeError("Full FreeCAD GUI is unavailable: App.GuiUp is false.")
        document = App.newDocument("Allshield_GUI_Runtime_Probe")
        report["test_document_created"] = True
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.updateGui()
        App.closeDocument(document.Name)
        document = None
        report["test_document_closed"] = True
        report["status"] = "PASS_GUI_RUNTIME_AVAILABLE"
    except Exception as error:
        report["status"] = "FAIL_GUI_RUNTIME_UNAVAILABLE"
        report["error"] = repr(error)
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
    finally:
        (output / "gui_runtime_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        Gui.getMainWindow().close()


main()