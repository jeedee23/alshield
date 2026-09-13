"""Verify that FreeCAD's configured GUI test runner reaches local tests."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

import FreeCAD as App


class GuiRunnerSentinel(unittest.TestCase):
    def test_runner_writes_sentinel(self):
        output = Path(__file__).resolve().parents[1] / "outputs" / (
            "gui_runner_sentinel_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        )
        output.mkdir(parents=True, exist_ok=False)
        report = {
            "status": "RUNNING",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "gui_up": bool(getattr(App, "GuiUp", False)),
        }

        try:
            import FreeCADGui as Gui

            document = App.newDocument("GuiRunnerSentinel")
            active_document = Gui.activeDocument()
            report["freecad_gui_imported"] = True
            report["active_view_available"] = (
                active_document is not None and active_document.activeView() is not None
            )
            report["status"] = "PASS_GUI_TEST_RUNNER"
        except Exception as error:
            report["freecad_gui_imported"] = False
            report["error"] = repr(error)
            report["status"] = "FAIL_GUI_TEST_RUNNER"
        finally:
            if "document" in locals() and document.Name in App.listDocuments():
                App.closeDocument(document.Name)

        (output / "gui_runner_sentinel.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        self.assertTrue(report["gui_up"], report)
        self.assertTrue(report["freecad_gui_imported"], report)
        self.assertTrue(report["active_view_available"], report)
