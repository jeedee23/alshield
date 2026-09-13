# -*- coding: utf-8 -*-
"""Add the six source-projected A11/as-1 WVB brace bars."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXIS05_MODULE = Path(__file__).with_name("allshield_axis_05.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_01_wvb_draft.json")


def _load_axis05():
    spec = importlib.util.spec_from_file_location("allshield_axis05_for_axis01_wvb", str(AXIS05_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_01_WVB400": "WVB100*7",
        "A11_01_WVB401_ASC": "WVB100*7",
        "A11_01_WVB401_DESC": "WVB100*7",
        "A11_01_WVB402": "WVB100*7",
        "A11_01_WVB399": "WVB100*7",
        "A11_01_WVB403": "WVB100*7",
    }
    members = catalog.get("approved_members", [])
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1" or {
            member.get("id"): member.get("profile_label") for member in members} != expected:
        raise ValueError("Axis-1 WVB catalog must contain exactly the six approved brace bars.")
    profile = catalog.get("nominal_profile_status", {}).get("WVB100*7", {})
    dimensions = profile.get("dimensions_mm", {})
    if profile.get("section_orientation") != "FLAT_BAR_WIDTH_IN_A11_ELEVATION_PLANE" or dimensions != {
            "width_in_A11_elevation_plane": 100.0,
            "thickness_out_of_A11_elevation_plane": 7.0}:
        raise ValueError("Axis-1 WVB catalog has no approved 100x7 flat-bar section.")
    centreline_definitions = catalog.get("centreline_definitions_mm", {})
    for member in members:
        member_id = member["id"]
        if member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID":
            raise ValueError("Member is not approved for nominal solid generation: " + member_id)
        if member_id not in centreline_definitions or not member.get("direct_pdf_path_indices"):
            raise ValueError("Missing source-derived centreline or direct PDF path for " + member_id)
        if float(member.get("endpoint_outline_half_width_max_mm", 0)) <= 0:
            raise ValueError("Missing individual endpoint uncertainty for " + member_id)
    return catalog


def _flat_bar_face(App, Part, dimensions):
    thickness = float(dimensions["thickness_out_of_A11_elevation_plane"])
    width = float(dimensions["width_in_A11_elevation_plane"])
    if thickness <= 0 or width <= 0:
        raise ValueError("Non-positive WVB flat-bar dimensions.")
    corners = [
        App.Vector(-thickness / 2.0, 0.0, -width / 2.0),
        App.Vector(thickness / 2.0, 0.0, -width / 2.0),
        App.Vector(thickness / 2.0, 0.0, width / 2.0),
        App.Vector(-thickness / 2.0, 0.0, width / 2.0),
    ]
    face = Part.Face(Part.makePolygon(corners + [corners[0]]))
    if face.isNull() or not face.isValid():
        raise ValueError("Invalid WVB100*7 flat-bar profile face.")
    return face


def audit_axis_01_wvb(doc, catalog, axis05):
    """Check prior cumulative geometry and the six source-derived WVB solids."""
    import FreeCAD as App
    import Part

    axis03 = axis05._load_axis03()
    axis02 = axis03._load_axis02()
    axis01 = axis02._load_axis01()
    axis07 = axis01._load_axis07()
    axis08 = axis07._load_axis08()
    axis05.audit_axis_05(doc, axis05._load_catalog(), axis03, axis02, axis01, axis07, axis08)
    structure = doc.getObject("Structure")
    secondary = doc.getObject("Secondary_Steel")
    wind_bracing = doc.getObject("Wind_Bracing")
    frame = doc.getObject("Frame_Axis_01_WVB")
    bars = doc.getObject("Axis01_WVB100x7_Bars")
    if not all((structure, secondary, wind_bracing, frame, bars)):
        raise AssertionError("Missing axis-1 WVB secondary-steel hierarchy.")
    failures = []
    if (secondary not in structure.Group or wind_bracing not in secondary.Group or
            frame not in wind_bracing.Group or bars not in frame.Group):
        failures.append("Wrong axis-1 WVB parentage.")
    expected_members = {member["id"]: member for member in catalog["approved_members"]}
    actual_members = {obj.Name for obj in doc.Objects if obj.Name.startswith("A11_01_WVB")}
    if actual_members != set(expected_members):
        failures.append("Unexpected axis-1 WVB member set: " + repr(sorted(actual_members)))
    profile = catalog["nominal_profile_status"]["WVB100*7"]
    face = _flat_bar_face(App, Part, profile["dimensions_mm"])
    rows = []
    for member_id, member in expected_members.items():
        obj = doc.getObject(member_id)
        if obj is None or obj.TypeId != "App::Link" or obj.LinkedObject is None:
            failures.append("Missing linked WVB flat-bar solid " + member_id)
            continue
        if obj not in bars.Group or obj.EvidenceStatus != "VECTOR_MEASUREMENT":
            failures.append("Incorrect group or evidence status " + member_id)
        if obj.ProfileLabel != "WVB100*7" or obj.SectionOrientation != profile["section_orientation"]:
            failures.append("Incorrect profile metadata " + member_id)
        if obj.ChangeSet != catalog["change_visualisation"]["change_set"] or obj.DisplayVisibilityRequested != "VISIBLE":
            failures.append("Incorrect display metadata " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        if json.loads(obj.DirectPDFPathIndicesJSON) != member["direct_pdf_path_indices"]:
            failures.append("Incorrect direct PDF path metadata " + member_id)
        if abs(obj.EndpointOutlineHalfWidthMax.Value - member["endpoint_outline_half_width_max_mm"]) > axis08.TOLERANCE_MM:
            failures.append("Incorrect endpoint uncertainty metadata " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        placement, length = axis08._member_placement(App, start, end)
        expected = face.extrude(App.Vector(0, length, 0))
        expected.Placement = placement
        error = axis08._max_bbox_error(axis08._bbox(shape), axis08._bbox(expected))
        if error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (member_id, error))
        if abs(shape.Volume - face.Area * length) > 0.01:
            failures.append("Nominal flat-bar volume mismatch " + member_id)
        rows.append({
            "id": member_id,
            "source_mark": member["source_mark"],
            "profile": member["profile_label"],
            "centreline_length_mm": length,
            "endpoint_outline_half_width_max_mm": member["endpoint_outline_half_width_max_mm"],
            "volume_mm3": shape.Volume,
            "world_bbox_mm": axis08._bbox(shape),
            "world_bbox_error_mm": error,
        })
    report = {
        "pass": not failures,
        "members_checked": len(rows),
        "computational_tolerance_mm": axis08.TOLERANCE_MM,
        "failures": failures,
        "as_built_verified": False,
        "fabrication_model": False,
        "members": rows,
    }
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def build_axis_01_wvb(output_dir, detail_mode="WORK"):
    """Build the validated prior slices plus six A11/as-1 WVB brace bars."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    axis05 = _load_axis05()
    axis03 = axis05._load_axis03()
    axis02 = axis03._load_axis02()
    axis01 = axis02._load_axis01()
    axis07 = axis01._load_axis07()
    axis08 = axis07._load_axis08()
    catalog = _load_catalog()
    doc = axis05.build_axis_05(output, detail_mode)
    try:
        doc.openTransaction("Add approved A11 axis-1 WVB brace bars")
        structure = doc.getObject("Structure")
        library = doc.getObject("Component_Library")
        if structure is None or library is None:
            raise RuntimeError("Cumulative build has no Structure or Component_Library.")
        secondary = axis08._add_group(
            doc, structure, "Secondary_Steel", "Secondary_Steel", "VECTOR_MEASUREMENT",
            "Only explicitly source-mapped secondary steel is present; no regular repetition.",
        )
        wind_bracing = axis08._add_group(
            doc, secondary, "Wind_Bracing", "Wind_Bracing", "VECTOR_MEASUREMENT",
            "Only the six explicitly drawn WVB100*7 bars from A11/as-1.",
        )
        frame = axis08._add_group(
            doc, wind_bracing, "Frame_Axis_01_WVB", "Frame_Axis_01_WVB | A11 source-based", "VECTOR_MEASUREMENT",
            "A11 page 1, AANZICHT as-1; six source-projected WVB100*7 bars only.",
        )
        bars = axis08._add_group(
            doc, frame, "Axis01_WVB100x7_Bars", "WVB100x7_Bars", "VECTOR_MEASUREMENT",
            "WVB400, both separately drawn WVB401 bars, WVB402, WVB399 and WVB403 only.",
        )
        axis08._add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        axis08._add_property(frame, "App::PropertyString", "ChangeSetJSON", json.dumps(catalog["change_visualisation"], sort_keys=True), "Display")
        change_set = catalog["change_visualisation"]
        colour = tuple(float(value) for value in change_set["rgb"])
        if len(colour) != 3 or any(value < 0 or value > 1 for value in colour):
            raise ValueError("Invalid display-only change-set RGB value.")
        profile = catalog["nominal_profile_status"]["WVB100*7"]
        prototypes = {}
        for member in catalog["approved_members"]:
            member_id = member["id"]
            start = catalog["centreline_definitions_mm"][member_id]["start"]
            end = catalog["centreline_definitions_mm"][member_id]["end"]
            placement, length = axis08._member_placement(App, start, end)
            prototype_key = "WVB100x7_%.6f" % length
            if prototype_key not in prototypes:
                shape = _flat_bar_face(App, Part, profile["dimensions_mm"]).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal WVB100*7 solid " + prototype_key)
                prototype = doc.addObject("Part::Feature", "Prototype_Axis01_WVB_" + prototype_key.replace(".", "_"))
                prototype.Label = "Prototype | nominal WVB100*7 | as-1"
                prototype.Shape = shape
                prototype.Placement = placement
                axis08._add_property(prototype, "App::PropertyString", "ProfileDimensionsJSON", json.dumps(profile["dimensions_mm"], sort_keys=True))
                axis08._add_property(prototype, "App::PropertyString", "SectionOrientation", profile["section_orientation"])
                axis08._style_change_set(prototype, colour)
                library.addObject(prototype)
                prototype_view = getattr(prototype, "ViewObject", None)
                if prototype_view is not None:
                    prototype_view.Visibility = False
                    if "Selectable" in prototype_view.PropertiesList:
                        prototype_view.Selectable = False
                prototypes[prototype_key] = prototype
            obj = doc.addObject("App::Link", member_id)
            obj.setLink(prototypes[prototype_key])
            obj.Label = "A11 / as-1 / %s / WVB100*7" % member["source_mark"]
            if "LinkTransform" in obj.PropertiesList:
                obj.LinkTransform = False
            obj.LinkPlacement = placement
            for type_name, name, value, group in (
                ("App::PropertyString", "StableComponentId", member_id, "Source"),
                ("App::PropertyString", "SourceMemberMark", member["source_mark"], "Source"),
                ("App::PropertyString", "ProfileLabel", member["profile_label"], "Source"),
                ("App::PropertyString", "SectionOrientation", profile["section_orientation"], "Source"),
                ("App::PropertyString", "EvidenceStatus", catalog["centreline_definitions_mm"]["evidence_status"], "Source"),
                ("App::PropertyString", "DirectPDFPathIndicesJSON", json.dumps(member["direct_pdf_path_indices"]), "Source"),
                ("App::PropertyLength", "EndpointOutlineHalfWidthMax", member["endpoint_outline_half_width_max_mm"], "Source"),
                ("App::PropertyVector", "SourceCentrelineStart", axis08._vector(App, start), "Geometry"),
                ("App::PropertyVector", "SourceCentrelineEnd", axis08._vector(App, end), "Geometry"),
                ("App::PropertyLength", "CentrelineLength", length, "Geometry"),
                ("App::PropertyString", "ExcludedDetail", "No bolts, gusset plates, cleats, rails, crossings, base details or unlabelled secondary steel.", "Geometry"),
                ("App::PropertyString", "ChangeSet", change_set["change_set"], "Display"),
                ("App::PropertyString", "ChangeColourMeaning", change_set["meaning"], "Display"),
                ("App::PropertyString", "DisplayVisibilityRequested", "VISIBLE", "Display")):
                axis08._add_property(obj, type_name, name, value, group)
            axis08._add_property(obj, "App::PropertyString", "EvidenceJSON", json.dumps({
                "file": catalog["source"]["file"],
                "sheet": catalog["source"]["sheet"],
                "page": catalog["source"]["page"],
                "view": catalog["source"]["view"],
                "member_mark": member["source_mark"],
                "direct_pdf_path_indices": member["direct_pdf_path_indices"],
                "endpoint_outline_half_width_max_mm": member["endpoint_outline_half_width_max_mm"],
            }, sort_keys=True))
            axis08._style_change_set(obj, colour)
            obj_view = getattr(obj, "ViewObject", None)
            if obj_view is not None:
                obj_view.Visibility = True
            bars.addObject(obj)
        library_view = getattr(library, "ViewObject", None)
        if library_view is not None:
            library_view.Visibility = False
        doc.recompute()
        audit_axis_01_wvb(doc, catalog, axis05)
        doc.commitTransaction()
        doc.recompute()
        return doc
    except Exception:
        try:
            doc.abortTransaction()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    build_axis_01_wvb(ROOT / "outputs" / ("axis01_wvb_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))