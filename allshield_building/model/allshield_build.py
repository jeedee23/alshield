# -*- coding: utf-8 -*-
"""Allshield Ter Aar - fresh, JSON-driven source/reference build.

Run this file in FreeCAD (Macro > Macros > Execute).
Keep allshield_building_02.json beside this macro, or select it when prompted.
Revision 02: source library outside Building, sources anchored to their first
occurrence, and effective world-coordinate checks after recompute.
No legacy V3 imports. No microwave/magnetron body, footprint or placeholder.

The JSON distinguishes drawing-based envelopes, source projections and unresolved
components. A SOURCE_PROJECTION is not a collision solid or an as-built record.
The document stores its JSON snapshot so that it stays auditable when moved.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------- user switches --------------------------------
JSON_PATH = ""             # Empty: beside macro, otherwise file-selection dialog.
DETAIL_MODE = "WORK"        # WORK or PANELS; PANELS adds measured facade divisions.
SHOW_ROOF = False          # Roof crest-envelope surfaces, independent of ceiling.
SHOW_CEILING = False       # Sandwich bulk/underside representation.
SHOW_FACADES = True
SHOW_FLOOR = True
SHOW_STEEL_SOURCE_SECTIONS = True  # Located source outlines, NOT solid members.
SHOW_REFERENCE_GRID = False
SHOW_EQUIPMENT_FOOTPRINTS = True   # 2D only; microwave is always excluded.
CREATE_SOURCE_ELEVATIONS = False # Additional full C4a linework; off for speed.
SHOW_SOURCE_ELEVATIONS = False
AUTOSAVE = False           # Save manually with Save As, or create new unique file.
VALIDATE_SHAPES = True

SCHEMA = "allshield.freecad.build.v1"
DOCUMENT_NAME = "Allshield_Source_Rebuild_02"

# These are display colours, not inferred building/material specifications.
COLOURS = {
    "wall": (0.68, 0.70, 0.72), "plinth": (0.60, 0.59, 0.56),
    "floor": (0.75, 0.74, 0.70), "roof": (0.72, 0.75, 0.77),
    "ceiling": (0.90, 0.90, 0.85), "steel_source": (0.20, 0.27, 0.32),
    "glass": (0.39, 0.64, 0.73), "door": (0.28, 0.31, 0.34),
    "frame": (0.23, 0.25, 0.27), "equipment": (0.33, 0.47, 0.35),
    "reference": (0.61, 0.61, 0.61), "source_elevation": (0.32, 0.40, 0.52),
    "datum": (0.82, 0.36, 0.12),
}


def _finite(values: Any, location: str) -> None:
    if isinstance(values, (int, float)) and not isinstance(values, bool):
        if not math.isfinite(values):
            raise ValueError("Non-finite coordinate at " + location)
    elif isinstance(values, list):
        for i, value in enumerate(values):
            _finite(value, "%s[%s]" % (location, i))
    elif isinstance(values, dict):
        for key, value in values.items():
            _finite(value, location + "." + key)


def validate_data(data: Dict[str, Any]) -> None:
    """Validate before creating any FreeCAD document or modifying the screen."""
    if data.get("schema") != SCHEMA or data.get("units") != "mm":
        raise ValueError("Unsupported schema or units. Expected %s, mm." % SCHEMA)
    nodes = data.get("components")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("JSON contains no component tree.")
    ids = [c["id"] for c in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate component id.")
    index = {c["id"]: c for c in nodes}
    source_ids = {s["id"] for s in data.get("sources", [])}
    forbidden = re.compile(r"magnetron|microwave", re.I)
    for c in nodes:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", c["id"]):
            raise ValueError("Invalid stable CAD id: " + c["id"])
        if forbidden.search(c["id"] + " " + c["name"]):
            raise ValueError("Excluded microwave component in input: " + c["id"])
        parent = c.get("parent_id")
        if parent is not None and parent not in index:
            raise ValueError("Unknown parent for " + c["id"])
        children = c.get("children", [])
        if len(children) != len(set(children)):
            raise ValueError("Duplicate child in " + c["id"])
        for child in children:
            if child not in index or index[child].get("parent_id") != c["id"]:
                raise ValueError("Inconsistent parent/child links at " + c["id"])
        if parent and c["id"] not in index[parent].get("children", []):
            raise ValueError("Missing reverse child reference for " + c["id"])
        path, here = set(), c
        while here is not None:
            if here["id"] in path:
                raise ValueError("Cycle in component hierarchy.")
            path.add(here["id"])
            here = index.get(here.get("parent_id"))
        g = c.get("geometry")
        if g is None:
            continue
        if "PENDING" in c.get("status", ""):
            raise ValueError("Unresolved component contains geometry: " + c["id"])
        if not c.get("evidence") and c.get("category") != "datum":
            raise ValueError("Geometry has no evidence: " + c["id"])
        for ev in c.get("evidence", []):
            if ev.get("source_id") not in source_ids:
                raise ValueError("Unrecognized source in " + c["id"])
        if g.get("kind") not in {"box", "prism", "face", "polyline", "lines"}:
            raise ValueError("Unknown geometry kind in " + c["id"])
        if g["kind"] == "box" and any(v <= 0 for v in g["size"]):
            raise ValueError("Non-positive box dimension in " + c["id"])
        if g["kind"] == "prism" and sum(v*v for v in g["vector"]) == 0:
            raise ValueError("Zero extrusion in " + c["id"])
        _finite(g, c["id"])


def active_nodes(data: Dict[str, Any], settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Do not build a heavy variant just to hide it afterwards."""
    mode = settings.get("detail_mode", "WORK").upper()
    if mode not in {"WORK", "PANELS"}:
        raise ValueError("detail_mode must be WORK or PANELS.")
    keep = []
    for c in data["components"]:
        if c.get("modes") and mode not in c["modes"]:
            continue
        cat = c.get("category")
        if "geometry" in c:
            if cat == "source_elevation" and not settings.get("create_source_elevations"):
                continue
            if cat == "steel_source" and not settings.get("create_steel_source_sections", True):
                continue
        keep.append(c)
    # Include metadata ancestors even when their siblings were filtered out.
    return keep


def canonical_geometry(g: Dict[str, Any]) -> Tuple[Dict[str, Any], List[float], str]:
    """Translation-only local geometry; global placement remains explicit."""
    kind = g["kind"]
    if kind == "box":
        origin = list(g["origin"])
    elif kind in {"prism", "face"}:
        origin = list(g["outer"][0])
    elif kind == "polyline":
        origin = list(g["points"][0])
    elif kind == "lines":
        if not g["segments"]:
            raise ValueError("Empty line compound.")
        origin = list(g["segments"][0][0])
    else:
        raise ValueError("Unknown geometry kind.")
    def pt(p):
        # 1e-6 mm normalization is below the stored source precision. No grid
        # pitch, nominal member size, or physical location is rounded to fit.
        return [round(p[i] - origin[i], 6) for i in range(3)]
    if kind == "box":
        local = {"kind": kind, "origin": [0, 0, 0], "size": g["size"]}
    elif kind in {"face", "prism"}:
        local = {"kind": kind, "outer": [pt(p) for p in g["outer"]],
                 "holes": [[pt(p) for p in h] for h in g.get("holes", [])]}
        if kind == "prism":
            local["vector"] = g["vector"]
    elif kind == "polyline":
        local = {"kind": kind, "points": [pt(p) for p in g["points"]],
                 "closed": bool(g.get("closed"))}
    else:
        seen, segments = set(), []
        for a, b in g["segments"]:
            aa, bb = pt(a), pt(b)
            if sum((aa[i]-bb[i])**2 for i in range(3)) < 1e-12:
                continue
            key = tuple(sorted((tuple(aa), tuple(bb))))
            if key not in seen:
                segments.append([aa, bb]); seen.add(key)
        local = {"kind": "lines", "segments": segments}
    blob = json.dumps(local, sort_keys=True, separators=(",", ":"))
    return local, origin, hashlib.sha256(blob.encode("utf-8")).hexdigest()



def geometry_bounds(g):
    """Expected world-coordinate bounding box from explicit JSON geometry."""
    kind = g["kind"]
    if kind == "box":
        points = [g["origin"], [a+b for a,b in zip(g["origin"], g["size"])]]
    elif kind in {"face", "prism"}:
        points = list(g["outer"])
        if kind == "prism":
            points += [[a+b for a,b in zip(p, g["vector"])] for p in g["outer"]]
    elif kind == "lines":
        points = [p for segment in g["segments"] for p in segment]
    else:
        points = g["points"]
    return [min(p[i] for p in points) for i in range(3)] + [max(p[i] for p in points) for i in range(3)]


def audit_world_geometry(nodes, objects, part_module, tolerance_mm=0.01):
    """Fail rather than silently deliver a displaced link.

    Part.getShape resolves the effective link transform. A linked object's raw
    Shape property is NOT used as a substitute for its rendered world geometry.
    The tolerance is a computational check, not claimed as-built accuracy.
    """
    checked = 0
    worst = 0.0
    failures = []
    for c in nodes:
        if "geometry" not in c:
            continue
        obj = objects[c["id"]]
        effective = part_module.getShape(obj)
        if effective.isNull():
            failures.append(c["id"] + ": empty effective shape")
            continue
        box = effective.BoundBox
        actual = [box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax]
        expected = geometry_bounds(c["geometry"])
        error = max(abs(a-b) for a,b in zip(actual, expected))
        worst = max(worst, error)
        checked += 1
        if not math.isfinite(error) or error > tolerance_mm:
            failures.append("%s: %.6f mm world-bounds error" % (c["id"], error))
    if failures:
        raise RuntimeError("FreeCAD placement check failed; no automatic save. " + "; ".join(failures[:12]))
    return {"checked_instances": checked, "max_bbox_error_mm": worst,
            "computational_tolerance_mm": tolerance_mm,
            "method": "Part.getShape: effective instance bounding box versus explicit JSON", 
            "as_built_accuracy_claim": False}


def _safe_prop(obj, type_name: str, name: str, value: Any, group="Source") -> None:
    if name not in obj.PropertiesList:
        obj.addProperty(type_name, name, group)
    setattr(obj, name, value)
    try:
        obj.setEditorMode(name, 1)
    except Exception:
        pass


def _visible(c, settings):
    category = c.get("category", "building")
    key = {"roof": "show_roof", "ceiling": "show_ceiling", "facade": "show_facades",
           "floor": "show_floor", "steel_source": "show_steel_source_sections",
           "equipment": "show_equipment_footprints", "reference": "show_reference_grid",
           "source_elevation": "show_source_elevations"}.get(category)
    return bool(settings.get(key, True)) if key else category != "pending"


def _style(obj, c) -> None:
    if not hasattr(obj, "ViewObject") or obj.ViewObject is None:
        return
    role = c.get("material_role", c.get("category", "wall"))
    colour = COLOURS.get(role, COLOURS["wall"])
    v = obj.ViewObject
    for key, value in [("ShapeColor", colour), ("LineColor", colour),
                       ("LineWidth", 1.4 if role == "steel_source" else 1.0),
                       ("PointSize", 3.0), ("Deviation", 0.5), ("AngularDeflection", 28.5),
                       ("Transparency", 55 if role == "glass" else 0)]:
        if key in getattr(v, "PropertiesList", []):
            try:
                setattr(v, key, value)
            except Exception:
                pass


def build_from_json(path: str, overrides: Optional[Dict[str, Any]] = None):
    """Create a NEW document; never close, clear, or overwrite a user's document."""
    import FreeCAD as App
    import Part
    try:
        import FreeCADGui as Gui
    except ImportError:
        Gui = None
    source_path = Path(path).expanduser().resolve()
    data = json.loads(source_path.read_text(encoding="utf-8"))
    validate_data(data)
    settings = dict(data.get("settings", {}))
    settings.update(overrides or {})
    nodes = active_nodes(data, settings)
    App.Console.PrintMessage("\nAllshield: %s; %s; microwave excluded.\n" % (source_path.name, settings["detail_mode"]))
    doc = App.newDocument(DOCUMENT_NAME)
    doc.Label = "Allshield | source rebuild 02 | " + settings["detail_mode"]
    objects, prototypes, prototype_objects = {}, {}, []
    report = {"schema": SCHEMA, "mode": settings["detail_mode"], "json": str(source_path),
              "json_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
              "instances": 0, "prototype_count": 0, "skipped": [],
              "microwave_geometry_count": 0, "scope": data["scope_note"],
              "unresolved": data.get("unresolved", [])}

    def vec(p):
        return App.Vector(float(p[0]), float(p[1]), float(p[2]))

    def wire(points):
        clean = []
        for p in points:
            if not clean or sum((p[i]-clean[-1][i])**2 for i in range(3)) > 1e-14:
                clean.append(p)
        if len(clean) < 3:
            raise ValueError("Degenerate closed contour.")
        if sum((clean[-1][i]-clean[0][i])**2 for i in range(3)) > 1e-14:
            clean.append(clean[0])
        return Part.makePolygon([vec(p) for p in clean])

    def shape_for(g):
        kind = g["kind"]
        if kind == "box":
            return Part.makeBox(*[float(v) for v in g["size"]])
        if kind in {"face", "prism"}:
            result = Part.Face(wire(g["outer"]))
            for hole in g.get("holes", []):
                result = result.cut(Part.Face(wire(hole)))
            if kind == "prism":
                result = result.extrude(vec(g["vector"]))
            return result
        if kind == "polyline":
            points = list(g["points"])
            if g.get("closed") and points[0] != points[-1]:
                points.append(points[0])
            return Part.makePolygon([vec(p) for p in points])
        if kind == "lines":
            return Part.makeCompound([Part.makeLine(vec(a), vec(b)) for a, b in g["segments"]])
        raise ValueError("Unsupported shape type.")

    try:
        doc.openTransaction("Allshield source-driven build")
        # Create groups first. Creation order is deliberately not dependent on
        # the numerical axis ordering, and parents are populated in a second pass.
        for c in nodes:
            if "geometry" not in c:
                obj = doc.addObject("App::DocumentObjectGroup", c["id"])
                obj.Label = c["name"]
                objects[c["id"]] = obj
                _safe_prop(obj, "App::PropertyString", "EvidenceStatus", c.get("status", ""))
                if c.get("note"):
                    _safe_prop(obj, "App::PropertyString", "SourceNote", c["note"])
        library = doc.addObject("App::DocumentObjectGroup", "Component_Library")
        library.Label = "Component_Library - NIET TONEN (bronvormen)"
        # Keep definition geometry OUTSIDE the user-toggleable Building tree.
        # Each source is also anchored to its first physical occurrence, so
        # Show All cannot reveal an exploded copy around the global origin.
        for c in nodes:
            if "geometry" in c:
                local, position, digest = canonical_geometry(c["geometry"])
                # Separate prototype styles as well as shapes, so glass/steel
                # do not share one material definition accidentally.
                key = digest + ":" + c.get("material_role", c.get("category", "wall"))
                if key not in prototypes:
                    shape = shape_for(local)
                    if shape.isNull():
                        raise ValueError("Null shape for " + c["id"])
                    if settings.get("validate_shapes", True) and not shape.isValid():
                        raise ValueError("Invalid OpenCASCADE shape for " + c["id"])
                    proto = doc.addObject("Part::Feature", "Prototype_%04d" % (len(prototypes)+1))
                    proto.Label = "Prototype | " + c["name"]
                    proto.Shape = shape
                    # LinkTransform=False below means each link replaces the
                    # source placement. Store the source at its first occurrence,
                    # not as loose local geometry around the model origin.
                    proto.Placement = App.Placement(vec(position), App.Rotation())
                    _safe_prop(proto, "App::PropertyString", "GeometryHash", digest)
                    _style(proto, c)
                    library.addObject(proto)
                    if Gui and getattr(App, "GuiUp", False):
                        proto.ViewObject.Visibility = False
                        if "Selectable" in proto.ViewObject.PropertiesList:
                            proto.ViewObject.Selectable = False
                    prototypes[key] = proto; prototype_objects.append(proto)
                obj = doc.addObject("App::Link", c["id"])
                obj.setLink(prototypes[key])
                obj.Label = c["name"]
                # Each link has an absolute placement independent of its source.
                # No rectangular steel grid is inferred.
                if "LinkTransform" in obj.PropertiesList:
                    obj.LinkTransform = False
                obj.LinkPlacement = App.Placement(vec(position), App.Rotation())
                objects[c["id"]] = obj
                _safe_prop(obj, "App::PropertyString", "EvidenceStatus", c["status"])
                _safe_prop(obj, "App::PropertyString", "EvidenceJSON", json.dumps(c.get("evidence", []), ensure_ascii=False))
                _safe_prop(obj, "App::PropertyString", "Representation", c["geometry"]["kind"])
                _safe_prop(obj, "App::PropertyString", "SourceNote", c.get("note", ""))
                _safe_prop(obj, "App::PropertyString", "StableComponentId", c["id"])
                report["instances"] += 1
        for c in nodes:
            parent = c.get("parent_id")
            if parent and c["id"] in objects:
                objects[parent].addObject(objects[c["id"]])
        info = objects["Building"]
        _safe_prop(info, "App::PropertyString", "ModelScope", data["scope_note"], "Build")
        _safe_prop(info, "App::PropertyString", "SourceJSONFile", str(source_path), "Build")
        _safe_prop(info, "App::PropertyString", "SourceJSONSHA256", report["json_sha256"], "Build")
        _safe_prop(info, "App::PropertyString", "EmbeddedSourceJSON", json.dumps(data, ensure_ascii=False, separators=(",", ":")), "Build")
        _safe_prop(info, "App::PropertyString", "BuildSettingsJSON", json.dumps(settings), "Build")
        _safe_prop(info, "App::PropertyBool", "MicrowaveExcluded", True, "Build")
        doc.recompute()
        # The old test checked only local shapes. Verify the EFFECTIVE shape of
        # every placed App::Link in the actual FreeCAD process as well.
        report["native_world_coordinate_check"] = audit_world_geometry(nodes, objects, Part)
        # Set parent groups before children; enabling a parent should not undo
        # the separate roof and ceiling visibility switches.
        if Gui and getattr(App, "GuiUp", False):
            for c in nodes:
                if "geometry" not in c:
                    objects[c["id"]].ViewObject.Visibility = True
            for c in nodes:
                if "geometry" in c:
                    objects[c["id"]].ViewObject.Visibility = _visible(c, settings)
            for proto in prototype_objects:
                proto.ViewObject.Visibility = False
            library.ViewObject.Visibility = False
            Gui.activeDocument().activeView().viewAxonometric()
            Gui.activeDocument().activeView().fitAll()
        report["prototype_count"] = len(prototypes)
        report["document_object_count"] = len(doc.Objects)
        report["shape_validity"] = "all generated prototypes valid" if settings.get("validate_shapes", True) else "not requested"
        _safe_prop(info, "App::PropertyString", "BuildReportJSON", json.dumps(report, ensure_ascii=False), "Build")
        doc.commitTransaction()
        # Recompute once more only for completed metadata and document bounds.
        doc.recompute()
        audit_world_geometry(nodes, objects, Part)
        if settings.get("autosave", False):
            target = source_path.parent / (doc.Name + ".FCStd")
            suffix = 1
            while target.exists():
                target = source_path.parent / (doc.Name + "_%02d.FCStd" % suffix)
                suffix += 1
            doc.saveAs(str(target))
            report["saved_as"] = str(target)
        report_target = source_path.parent / (doc.Name + "_last_build.json")
        try:
            report_target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            App.Console.PrintWarning("Report could not be written beside the JSON; it is embedded in Building.\n")
        App.Console.PrintMessage("Allshield: %d geometry links; %d shared prototypes.\n" % (report["instances"], report["prototype_count"]))
        App.Console.PrintWarning("Drawing-based model: steel source sections are NOT 3D collision solids. See Pending entries and Building.ModelScope.\n")
        return doc
    except Exception:
        try:
            doc.abortTransaction()
        except Exception:
            pass
        # Do not close an existing document or hide a failure in the source data.
        App.Console.PrintError("Allshield build failed. The new document was not saved.\n")
        raise


def _choose_json() -> str:
    if JSON_PATH:
        path = Path(JSON_PATH).expanduser()
        if not path.is_file():
            raise FileNotFoundError("JSON_PATH does not exist: " + str(path))
        return str(path)
    candidates = []
    if "__file__" in globals():
        candidates.append(Path(__file__).resolve().parent / "allshield_building_02.json")
    candidates.append(Path.cwd() / "allshield_building_02.json")
    for path in candidates:
        if path.is_file():
            return str(path)
    try:
        from PySide import QtGui
        dialog = QtGui.QFileDialog
    except (ImportError, AttributeError):
        try:
            from PySide2.QtWidgets import QFileDialog
        except ImportError:
            from PySide6.QtWidgets import QFileDialog
        dialog = QFileDialog
    result = dialog.getOpenFileName(None, "Select allshield_building_02.json", "", "JSON (*.json)")
    filename = result[0] if isinstance(result, (tuple, list)) else result
    if not filename:
        raise RuntimeError("No JSON selected; nothing was changed.")
    return str(filename)


def main():
    return build_from_json(_choose_json(), {
        "detail_mode": DETAIL_MODE,
        "show_roof": SHOW_ROOF, "show_ceiling": SHOW_CEILING,
        "show_facades": SHOW_FACADES, "show_floor": SHOW_FLOOR,
        "show_steel_source_sections": SHOW_STEEL_SOURCE_SECTIONS,
        "show_reference_grid": SHOW_REFERENCE_GRID,
        "show_equipment_footprints": SHOW_EQUIPMENT_FOOTPRINTS,
        "create_source_elevations": CREATE_SOURCE_ELEVATIONS,
        "show_source_elevations": SHOW_SOURCE_ELEVATIONS,
        "autosave": AUTOSAVE, "validate_shapes": VALIDATE_SHAPES,
    })


if __name__ == "__main__":
    main()
