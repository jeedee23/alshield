"""Probe whether the installed FreeCADCmd can render an offscreen GUI view."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import traceback

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]


def main():
    supplied_output = os.environ.get("ALLSHIELD_TEST_OUTPUT")
    output = Path(supplied_output) if supplied_output else ROOT / "outputs" / (
        "offscreen_gui_probe_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "freecad_version": list(App.Version()),
        "gui_up_before_setup": bool(getattr(App, "GuiUp", False)),
        "gui_up_after_setup": None,
        "active_view_available": False,
        "screenshot_created": False,
    }
    document = None
    try:
        import FreeCADGui as Gui

        report["freecad_gui_members"] = sorted(
            name for name in dir(Gui) if not name.startswith("_")
        )
        report["setup_without_gui_available"] = hasattr(Gui, "setupWithoutGUI")
        if not App.GuiUp:
            report["setup_without_gui_result"] = Gui.setupWithoutGUI()
        report["gui_up_after_setup"] = bool(getattr(App, "GuiUp", False))
        document = App.newDocument("Allshield_Offscreen_GUI_Probe")
        box = document.addObject("Part::Box", "Probe_Box")
        box.Length = 1000.0
        box.Width = 800.0
        box.Height = 600.0
        document.recompute()
        gui_document = Gui.activeDocument() if hasattr(Gui, "activeDocument") else None
        active_view = gui_document.activeView() if gui_document is not None else None
        report["active_view_available"] = active_view is not None
        if active_view is None:
            report["status"] = "NO_OFFSCREEN_ACTIVE_VIEW"
            return report
        active_view.viewAxonometric()
        active_view.fitAll()
        Gui.updateGui()
        screenshot = output / "offscreen_gui_probe.png"
        active_view.saveImage(str(screenshot), 640, 480, "Current")
        report["screenshot"] = str(screenshot)
        report["screenshot_created"] = screenshot.is_file() and screenshot.stat().st_size > 0
        report["status"] = "PASS_OFFSCREEN_GUI_RENDER" if report["screenshot_created"] else "FAIL_EMPTY_OFFSCREEN_SCREENSHOT"
    except Exception:
        report["status"] = "FAIL_OFFSCREEN_GUI_PROBE"
        report["traceback"] = traceback.format_exc()
    finally:
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        (output / "offscreen_gui_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (output / "native_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()