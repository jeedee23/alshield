# -*- coding: utf-8 -*-
"""Build the approved A11 axis-8 nominal IPE coordination-model extension.

The baseline source JSON and generator remain unchanged. This module copies the
baseline JSON to its unique output folder, creates a fresh baseline document,
then adds only the six authorised as-8 steel members.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
CATALOG = Path(__file__).with_name("steel_catalog_axis_08_draft.json")
TOLERANCE_MM = 0.01


def _load_baseline_generator():
    spec = importlib.util.spec_from_file_location("allshield_axis08_baseline", str(BASE_GENERATOR))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1":
        raise ValueError("Unsupported axis-8 catalog schema.")
    members = catalog.get("confirmed_members", [])
    expected_ids = {
        "A11_08_211", "A11_08_216", "A11_08_221", "A11_08_223",
        "A11_08_504_A", "A11_08_504_E",
    }
    if {member.get("id") for member in members} != expected_ids:
        raise ValueError("Axis-8 catalog must contain exactly the six approved members.")
    for member in members:
        if member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID":
            raise ValueError("Member is not approved for nominal solid generation: " + member["id"])
    return catalog


def _add_property(obj, type_name, name, value, group="Source"):
    if name not in obj.PropertiesList:
        obj.addProperty(type_name, name, group)
    setattr(obj, name, value)
    try:
        obj.setEditorMode(name, 1)
    except Exception:
        pass


def _vector(App, values):
    return App.Vector(float(values[0]), float(values[1]), float(values[2]))


def _point(App, x, z):
    return App.Vector(float(x), 0.0, float(z))


def _ipe_profile_face(App, Part, dimensions):
    """Create one nominal IPE cross-section in the local XZ plane.

    Local +Y is the member axis, local +X is flange width and local +Z is
    section depth. The profile uses the supplied root radius, not a box proxy.
    """
    height = float(dimensions["height_h"])
    flange_width = float(dimensions["flange_width_b"])
    web_thickness = float(dimensions["web_thickness_tw"])
    flange_thickness = float(dimensions["flange_thickness_tf"])
    root_radius = float(dimensions["root_radius_r"])
    if min(height, flange_width, web_thickness, flange_thickness, root_radius) <= 0:
        raise ValueError("Non-positive nominal IPE dimension.")
    if web_thickness + 2 * root_radius >= flange_width:
        raise ValueError("IPE root radius is too large for its flange width.")
    if 2 * flange_thickness + 2 * root_radius >= height:
        raise ValueError("IPE root radius is too large for its section height.")

    half_height = height / 2.0
    half_width = flange_width / 2.0
    half_web = web_thickness / 2.0
    top_inner = half_height - flange_thickness
    bottom_inner = -half_height + flange_thickness
    diagonal = root_radius / math.sqrt(2.0)

    top_left = _point(App, -half_width, half_height)
    top_right = _point(App, half_width, half_height)
    right_top_outer = _point(App, half_width, top_inner)
    right_top_start = _point(App, half_web + root_radius, top_inner)
    right_top_end = _point(App, half_web, top_inner - root_radius)
    right_bottom_start = _point(App, half_web, bottom_inner + root_radius)
    right_bottom_end = _point(App, half_web + root_radius, bottom_inner)
    right_bottom_outer = _point(App, half_width, bottom_inner)
    bottom_right = _point(App, half_width, -half_height)
    bottom_left = _point(App, -half_width, -half_height)
    left_bottom_outer = _point(App, -half_width, bottom_inner)
    left_bottom_start = _point(App, -half_web - root_radius, bottom_inner)
    left_bottom_end = _point(App, -half_web, bottom_inner + root_radius)
    left_top_start = _point(App, -half_web, top_inner - root_radius)
    left_top_end = _point(App, -half_web - root_radius, top_inner)
    left_top_outer = _point(App, -half_width, top_inner)

    right_top_centre = _point(App, half_web + root_radius, top_inner - root_radius)
    right_bottom_centre = _point(App, half_web + root_radius, bottom_inner + root_radius)
    left_bottom_centre = _point(App, -half_web - root_radius, bottom_inner + root_radius)
    left_top_centre = _point(App, -half_web - root_radius, top_inner - root_radius)
    edges = [
        Part.makeLine(top_left, top_right),
        Part.makeLine(top_right, right_top_outer),
        Part.makeLine(right_top_outer, right_top_start),
        Part.Arc(right_top_start, _point(App, right_top_centre.x - diagonal, right_top_centre.z + diagonal), right_top_end).toShape(),
        Part.makeLine(right_top_end, right_bottom_start),
        Part.Arc(right_bottom_start, _point(App, right_bottom_centre.x - diagonal, right_bottom_centre.z - diagonal), right_bottom_end).toShape(),
        Part.makeLine(right_bottom_end, right_bottom_outer),
        Part.makeLine(right_bottom_outer, bottom_right),
        Part.makeLine(bottom_right, bottom_left),
        Part.makeLine(bottom_left, left_bottom_outer),
        Part.makeLine(left_bottom_outer, left_bottom_start),
        Part.Arc(left_bottom_start, _point(App, left_bottom_centre.x + diagonal, left_bottom_centre.z - diagonal), left_bottom_end).toShape(),
        Part.makeLine(left_bottom_end, left_top_start),
        Part.Arc(left_top_start, _point(App, left_top_centre.x + diagonal, left_top_centre.z + diagonal), left_top_end).toShape(),
        Part.makeLine(left_top_end, left_top_outer),
        Part.makeLine(left_top_outer, top_left),
    ]
    face = Part.Face(Part.Wire(edges))
    if face.isNull() or not face.isValid():
        raise ValueError("Invalid nominal IPE profile face.")
    return face


def _member_placement(App, start, end):
    axis = [float(end[index]) - float(start[index]) for index in range(3)]
    length = math.sqrt(sum(value * value for value in axis))
    if length <= 0:
        raise ValueError("Zero-length member centreline.")
    if abs(axis[0]) > TOLERANCE_MM:
        raise ValueError("A11/as-8 member is not on its declared structural station.")
    angle_degrees = math.degrees(math.atan2(axis[2], axis[1]))
    rotation = App.Rotation(App.Vector(1, 0, 0), angle_degrees)
    return App.Placement(_vector(App, start), rotation), length


def _style_change_set(obj, colour):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return
    for key, value in (("ShapeColor", colour), ("LineColor", colour),
                       ("LineWidth", 1.0), ("Transparency", 0)):
        if key in view.PropertiesList:
            setattr(view, key, value)


def _add_group(doc, parent, object_id, label, status, source_note):
    obj = doc.addObject("App::DocumentObjectGroup", object_id)
    obj.Label = label
    _add_property(obj, "App::PropertyString", "EvidenceStatus", status)
    _add_property(obj, "App::PropertyString", "SourceNote", source_note)
    parent.addObject(obj)
    return obj


def _bbox(shape):
    box = shape.BoundBox
    return [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]


def _max_bbox_error(actual, expected):
    return max(abs(a - b) for a, b in zip(actual, expected))


def _descendant_names(obj):
    seen = set()
    todo = [obj]
    while todo:
        current = todo.pop()
        if current.Name in seen:
            continue
        seen.add(current.Name)
        todo.extend(list(getattr(current, "Group", [])))
    return seen


def audit_axis_08(doc, catalog):
    """Check link transforms, parentage, valid solids and section volumes."""
    import FreeCAD as App
    import Part

    library = doc.getObject("Component_Library")
    frame = doc.getObject("Frame_Axis_08")
    primary = doc.getObject("Primary_Members")
    labeled_ipe180 = doc.getObject("Labeled_IPE180_Members")
    if library is None or frame is None or primary is None or labeled_ipe180 is None:
        raise AssertionError("Missing axis-8 hierarchy or Component_Library.")
    expected_members = {member["id"]: member for member in catalog["confirmed_members"]}
    profile_dimensions = catalog["nominal_profile_source"]["profiles_mm"]
    failures = []
    rows = []
    building = doc.getObject("Building")
    structure = doc.getObject("Structure")
    portal_frames = doc.getObject("Portal_Frames")
    if building is None or structure is None or portal_frames is None:
        failures.append("Missing baseline Structure/Building or Portal_Frames.")
    else:
        if library.Name in _descendant_names(building):
            failures.append("Component_Library is nested inside Building.")
        if portal_frames not in structure.Group or frame not in portal_frames.Group:
            failures.append("Wrong Portal_Frames or Frame_Axis_08 parentage.")
        if primary not in frame.Group or labeled_ipe180 not in frame.Group:
            failures.append("Wrong nested axis-8 member-group parentage.")
    for member_id, member in expected_members.items():
        obj = doc.getObject(member_id)
        if obj is None:
            failures.append("Missing member " + member_id)
            continue
        if obj.TypeId != "App::Link" or obj.LinkedObject is None:
            failures.append("Expected linked solid " + member_id)
            continue
        if obj.EvidenceStatus != catalog["centreline_definitions_mm"]["evidence_status"]:
            failures.append("Incorrect centreline evidence status " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        expected_parent = primary if member["profile_label"].startswith("IPE500") else labeled_ipe180
        if obj not in expected_parent.Group:
            failures.append("Member outside axis-8 hierarchy " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        expected_placement, length = _member_placement(App, start, end)
        profile_key = "IPE500" if member["profile_label"].startswith("IPE500") else "IPE180"
        nominal_face = _ipe_profile_face(App, Part, profile_dimensions[profile_key])
        expected = nominal_face.extrude(App.Vector(0, length, 0))
        expected.Placement = expected_placement
        error = _max_bbox_error(_bbox(shape), _bbox(expected))
        if error > TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (member_id, error))
        expected_volume = nominal_face.Area * length
        volume_error = abs(shape.Volume - expected_volume)
        if volume_error > 0.01:
            failures.append("Nominal section volume mismatch %s: %.6f mm3" % (member_id, volume_error))
        rows.append({
            "id": member_id,
            "source_mark": member["source_mark"],
            "profile": member["profile_label"],
            "centreline_length_mm": length,
            "volume_mm3": shape.Volume,
            "world_bbox_mm": _bbox(shape),
            "world_bbox_error_mm": error,
        })
    report = {
        "pass": not failures,
        "members_checked": len(rows),
        "computational_tolerance_mm": TOLERANCE_MM,
        "failures": failures,
        "as_built_verified": False,
        "fabrication_model": False,
        "members": rows,
    }
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def build_axis_08(output_dir, detail_mode="WORK"):
    """Build a fresh source baseline plus the six approved A11/as-8 solids."""
    import FreeCAD as App

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    catalog = _load_catalog()
    change_set = catalog["change_visualisation"]
    change_colour = tuple(float(component) for component in change_set["rgb"])
    if len(change_colour) != 3 or any(component < 0 or component > 1 for component in change_colour):
        raise ValueError("Invalid display-only change-set RGB value.")
    snapshot = output / "allshield_building_02_snapshot.json"
    baseline_bytes = BASE_DATA.read_bytes()
    snapshot.write_bytes(baseline_bytes)
    baseline = _load_baseline_generator()
    doc = baseline.build_from_json(str(snapshot), {
        "detail_mode": detail_mode,
        "autosave": False,
        "validate_shapes": True,
        "show_steel_source_sections": True,
    })
    try:
        doc.openTransaction("Add approved A11 axis-8 nominal IPE members")
        structure = doc.getObject("Structure")
        library = doc.getObject("Component_Library")
        if structure is None or library is None:
            raise RuntimeError("Baseline document has no Structure or Component_Library.")
        portal_frames = _add_group(
            doc, structure, "Portal_Frames", "Portal_Frames", "VECTOR_MEASUREMENT",
            "Only explicitly source-mapped portal members are present; no regular frame repetition.",
        )
        frame = _add_group(
            doc, portal_frames, "Frame_Axis_08", "Frame_Axis_08 | A11 source-based", "VECTOR_MEASUREMENT",
            "A11 page 1, AANZICHT as-8; drawing status TER CONTROLE; nominal IPE coordination solids only.",
        )
        primary = _add_group(
            doc, frame, "Primary_Members", "Primary_Members", "VECTOR_MEASUREMENT",
            "Members 211, 216, 221 and 223 from A11/as-8.",
        )
        labeled_ipe180 = _add_group(
            doc, frame, "Labeled_IPE180_Members", "Labeled_IPE180_Members", "VECTOR_MEASUREMENT",
            "Only the two explicit 504 IPE180 members from A11/as-8.",
        )
        _add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        _add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        _add_property(frame, "App::PropertyString", "NominalProfileStandard", catalog["nominal_profile_source"]["standard"], "Build")
        _add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        _add_property(frame, "App::PropertyString", "ChangeSet", change_set["change_set"], "Display")
        _add_property(frame, "App::PropertyString", "ChangeColourMeaning", change_set["meaning"], "Display")

        prototypes = {}
        profile_dimensions = catalog["nominal_profile_source"]["profiles_mm"]
        for member in catalog["confirmed_members"]:
            member_id = member["id"]
            start = catalog["centreline_definitions_mm"][member_id]["start"]
            end = catalog["centreline_definitions_mm"][member_id]["end"]
            placement, length = _member_placement(App, start, end)
            profile_key = "IPE500" if member["profile_label"].startswith("IPE500") else "IPE180"
            prototype_key = "%s_%.6f" % (profile_key, length)
            if prototype_key not in prototypes:
                import Part
                shape = _ipe_profile_face(App, Part, profile_dimensions[profile_key]).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal solid for " + prototype_key)
                prototype = doc.addObject("Part::Feature", "Prototype_%s" % prototype_key.replace(".", "_"))
                prototype.Label = "Prototype | nominal %s | as-8" % profile_key
                prototype.Shape = shape
                prototype.Placement = placement
                _add_property(prototype, "App::PropertyString", "NominalProfileStandard", catalog["nominal_profile_source"]["standard"])
                _add_property(prototype, "App::PropertyString", "ProfileDimensionsJSON", json.dumps(profile_dimensions[profile_key], sort_keys=True))
                _style_change_set(prototype, change_colour)
                library.addObject(prototype)
                prototype_view = getattr(prototype, "ViewObject", None)
                if prototype_view is not None:
                    prototype_view.Visibility = False
                    if "Selectable" in prototype_view.PropertiesList:
                        prototype_view.Selectable = False
                prototypes[prototype_key] = prototype
            obj = doc.addObject("App::Link", member_id)
            obj.setLink(prototypes[prototype_key])
            obj.Label = "A11 / as-8 / %s / %s" % (member["source_mark"], member["profile_label"])
            if "LinkTransform" in obj.PropertiesList:
                obj.LinkTransform = False
            obj.LinkPlacement = placement
            _add_property(obj, "App::PropertyString", "StableComponentId", member_id)
            _add_property(obj, "App::PropertyString", "SourceMemberMark", member["source_mark"])
            _add_property(obj, "App::PropertyString", "ProfileLabel", member["profile_label"])
            _add_property(obj, "App::PropertyString", "EvidenceStatus", catalog["centreline_definitions_mm"]["evidence_status"])
            _add_property(obj, "App::PropertyString", "EvidenceJSON", json.dumps({
                "file": catalog["source"]["file"],
                "sheet": catalog["source"]["sheet"],
                "page": catalog["source"]["page"],
                "view": catalog["source"]["view"],
                "member_mark": member["source_mark"],
                "nominal_profile_standard": catalog["nominal_profile_source"]["standard"],
            }, sort_keys=True))
            _add_property(obj, "App::PropertyVector", "SourceCentrelineStart", _vector(App, start), "Geometry")
            _add_property(obj, "App::PropertyVector", "SourceCentrelineEnd", _vector(App, end), "Geometry")
            _add_property(obj, "App::PropertyLength", "CentrelineLength", length, "Geometry")
            _add_property(obj, "App::PropertyString", "ExcludedDetail", "No base plates, bolts, connections, stiffeners, haunches or unlabelled secondary steel.", "Geometry")
            _add_property(obj, "App::PropertyString", "ChangeSet", change_set["change_set"], "Display")
            _add_property(obj, "App::PropertyString", "ChangeColourMeaning", change_set["meaning"], "Display")
            _style_change_set(obj, change_colour)
            (primary if profile_key == "IPE500" else labeled_ipe180).addObject(obj)
        library_view = getattr(library, "ViewObject", None)
        if library_view is not None:
            library_view.Visibility = False
        doc.recompute()
        audit_axis_08(doc, catalog)
        doc.commitTransaction()
        doc.recompute()
        return doc
    except Exception:
        try:
            doc.abortTransaction()
        except Exception:
            pass
        raise


def _default_output_dir():
    return ROOT / "outputs" / ("axis08_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))


if __name__ == "__main__":
    build_axis_08(_default_output_dir())