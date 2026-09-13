# -*- coding: utf-8 -*-
"""Add approved A11 axis-2 members to the cumulative development build."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXIS01_MODULE = Path(__file__).with_name("allshield_axis_01.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_02_draft.json")


def _profile_key(member):
    return member["profile_label"].split("-", 1)[0]


def _load_axis01():
    spec = importlib.util.spec_from_file_location("allshield_axis01_for_axis02", str(AXIS01_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1":
        raise ValueError("Unsupported axis-2 catalog schema.")
    expected_profiles = {
        "A11_02_313": "HEA180",
        "A11_02_311": "HEA180",
        "A11_02_312": "HEA180",
        "A11_02_301": "HEA160",
    }
    members = catalog.get("approved_members", [])
    if {member.get("id") for member in members} != set(expected_profiles):
        raise ValueError("Axis-2 catalog must contain exactly the four approved members.")
    for member in members:
        member_id = member["id"]
        if member.get("profile_label") != expected_profiles[member_id]:
            raise ValueError("Unapproved profile in axis-2 solid slice: " + member_id)
        if member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID":
            raise ValueError("Member is not approved for nominal solid generation: " + member_id)
        if member_id not in catalog["centreline_definitions_mm"]:
            raise ValueError("Missing source-derived centreline for " + member_id)
        profile = catalog["nominal_profile_status"].get(_profile_key(member), {})
        if profile.get("source") != "NEN-EN 10365:2017" or "dimensions_mm" not in profile:
            raise ValueError("Missing approved nominal profile data for " + member_id)
    return catalog


def audit_axis_02(doc, catalog, axis01, axis07, axis08):
    """Check the cumulative build and four source-derived axis-2 solids."""
    import FreeCAD as App
    import Part

    axis01.audit_axis_01(doc, axis01._load_catalog(), axis07, axis08)
    frame = doc.getObject("Frame_Axis_02")
    hea180_columns = doc.getObject("Axis02_HEA180_Columns")
    hea160_horizontal = doc.getObject("Axis02_HEA160_Horizontal")
    portal_frames = doc.getObject("Portal_Frames")
    if (frame is None or hea180_columns is None or hea160_horizontal is None or
            portal_frames is None):
        raise AssertionError("Missing axis-2 portal hierarchy.")
    failures = []
    if (frame not in portal_frames.Group or hea180_columns not in frame.Group or
            hea160_horizontal not in frame.Group):
        failures.append("Wrong Frame_Axis_02 parentage.")
    expected_members = {member["id"]: member for member in catalog["approved_members"]}
    actual_axis02 = {obj.Name for obj in doc.Objects if obj.Name.startswith("A11_02_")}
    if actual_axis02 != set(expected_members):
        failures.append("Unexpected axis-2 member set: " + repr(sorted(actual_axis02)))
    expected_groups = {
        "HEA180": hea180_columns,
        "HEA160": hea160_horizontal,
    }
    change_set = catalog["change_visualisation"]
    rows = []
    for member_id, member in expected_members.items():
        obj = doc.getObject(member_id)
        if obj is None:
            failures.append("Missing member " + member_id)
            continue
        if obj.TypeId != "App::Link" or obj.LinkedObject is None:
            failures.append("Expected linked nominal profile solid " + member_id)
            continue
        if obj.EvidenceStatus != catalog["centreline_definitions_mm"]["evidence_status"]:
            failures.append("Incorrect centreline evidence status " + member_id)
        if obj.ChangeSet != change_set["change_set"]:
            failures.append("Incorrect change-set ID " + member_id)
        if obj.DisplayVisibilityRequested != "VISIBLE":
            failures.append("Visibility is not explicitly requested for " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        profile_key = _profile_key(member)
        if obj not in expected_groups[profile_key].Group:
            failures.append("Member outside expected axis-2 group " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        expected_placement, length = axis08._member_placement(App, start, end)
        profile = catalog["nominal_profile_status"][profile_key]
        nominal_face = axis01._nominal_profile_face(axis08, App, Part, profile)
        expected = nominal_face.extrude(App.Vector(0, length, 0))
        expected.Placement = expected_placement
        bbox = axis08._bbox(shape)
        bbox_error = axis08._max_bbox_error(bbox, axis08._bbox(expected))
        if bbox_error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (member_id, bbox_error))
        volume_error = abs(shape.Volume - nominal_face.Area * length)
        if volume_error > 0.01:
            failures.append("Nominal section volume mismatch %s: %.6f mm3" % (member_id, volume_error))
        if obj.SectionOrientation != profile["section_orientation"]:
            failures.append("Incorrect section orientation metadata " + member_id)
        if profile_key == "HEA180":
            if abs((bbox[4] - bbox[1]) - profile["source_projected_in_plane_width_mm"]) > axis08.TOLERANCE_MM:
                failures.append("HEA180 source-plane flange width mismatch " + member_id)
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["height_h"]) > axis08.TOLERANCE_MM:
                failures.append("HEA180 out-of-plane section height mismatch " + member_id)
        if profile_key == "HEA160":
            if abs((bbox[5] - bbox[2]) - profile["source_projected_in_plane_height_mm"]) > axis08.TOLERANCE_MM:
                failures.append("HEA160 source-plane height mismatch " + member_id)
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["flange_width_b"]) > axis08.TOLERANCE_MM:
                failures.append("HEA160 out-of-plane flange width mismatch " + member_id)
        rows.append({
            "id": member_id,
            "source_mark": member["source_mark"],
            "profile": member["profile_label"],
            "section_orientation": profile["section_orientation"],
            "change_set": change_set["change_set"],
            "centreline_length_mm": length,
            "volume_mm3": shape.Volume,
            "world_bbox_mm": bbox,
            "world_bbox_error_mm": bbox_error,
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


def build_axis_02(output_dir, detail_mode="WORK"):
    """Build the validated axis-8/axis-7/axis-1 slices plus four axis-2 members."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    axis01 = _load_axis01()
    axis07 = axis01._load_axis07()
    axis08 = axis07._load_axis08()
    catalog = _load_catalog()
    doc = axis01.build_axis_01(output, detail_mode)
    try:
        doc.openTransaction("Add approved A11 axis-2 nominal HEA members")
        portal_frames = doc.getObject("Portal_Frames")
        library = doc.getObject("Component_Library")
        if portal_frames is None or library is None:
            raise RuntimeError("Cumulative build has no Portal_Frames or Component_Library.")
        frame = axis08._add_group(
            doc, portal_frames, "Frame_Axis_02", "Frame_Axis_02 | A11 source-based", "VECTOR_MEASUREMENT",
            "A11 page 1, AANZICHT as-2; only approved HEA180 and HEA160 members are nominal coordination solids.",
        )
        hea180_columns = axis08._add_group(
            doc, frame, "Axis02_HEA180_Columns", "HEA180_Columns", "VECTOR_MEASUREMENT",
            "Only approved vertical members 313, 311 and 312 from A11/as-2.",
        )
        hea160_horizontal = axis08._add_group(
            doc, frame, "Axis02_HEA160_Horizontal", "HEA160_Horizontal", "VECTOR_MEASUREMENT",
            "Only approved horizontal member 301 from A11/as-2.",
        )
        axis08._add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(frame, "App::PropertyString", "NominalProfileStandard", "NEN-EN 10365:2017", "Build")
        axis08._add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        axis08._add_property(frame, "App::PropertyString", "ChangeSetJSON", json.dumps(catalog["change_visualisation"], sort_keys=True), "Display")

        prototypes = {}
        groups = {"HEA180": hea180_columns, "HEA160": hea160_horizontal}
        change_set = catalog["change_visualisation"]
        change_colour = tuple(float(component) for component in change_set["rgb"])
        if len(change_colour) != 3 or any(component < 0 or component > 1 for component in change_colour):
            raise ValueError("Invalid display-only change-set RGB value.")
        for member in catalog["approved_members"]:
            member_id = member["id"]
            start = catalog["centreline_definitions_mm"][member_id]["start"]
            end = catalog["centreline_definitions_mm"][member_id]["end"]
            placement, length = axis08._member_placement(App, start, end)
            profile_key = _profile_key(member)
            profile = catalog["nominal_profile_status"][profile_key]
            prototype_key = "%s_%.6f" % (profile_key, length)
            if prototype_key not in prototypes:
                shape = axis01._nominal_profile_face(axis08, App, Part, profile).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal %s solid for %s" % (profile_key, prototype_key))
                prototype = doc.addObject("Part::Feature", "Prototype_Axis02_%s" % prototype_key.replace(".", "_"))
                prototype.Label = "Prototype | nominal %s | as-2" % profile_key
                prototype.Shape = shape
                prototype.Placement = placement
                axis08._add_property(prototype, "App::PropertyString", "NominalProfileStandard", profile["source"])
                axis08._add_property(prototype, "App::PropertyString", "ProfileDimensionsJSON", json.dumps(profile["dimensions_mm"], sort_keys=True))
                axis08._add_property(prototype, "App::PropertyString", "SectionOrientation", profile["section_orientation"])
                axis08._style_change_set(prototype, change_colour)
                library.addObject(prototype)
                prototype_view = getattr(prototype, "ViewObject", None)
                if prototype_view is not None:
                    prototype_view.Visibility = False
                    if "Selectable" in prototype_view.PropertiesList:
                        prototype_view.Selectable = False
                prototypes[prototype_key] = prototype
            obj = doc.addObject("App::Link", member_id)
            obj.setLink(prototypes[prototype_key])
            obj.Label = "A11 / as-2 / %s / %s" % (member["source_mark"], member["profile_label"])
            if "LinkTransform" in obj.PropertiesList:
                obj.LinkTransform = False
            obj.LinkPlacement = placement
            axis08._add_property(obj, "App::PropertyString", "StableComponentId", member_id)
            axis08._add_property(obj, "App::PropertyString", "SourceMemberMark", member["source_mark"])
            axis08._add_property(obj, "App::PropertyString", "ProfileLabel", member["profile_label"])
            axis08._add_property(obj, "App::PropertyString", "SectionOrientation", profile["section_orientation"])
            axis08._add_property(obj, "App::PropertyString", "EvidenceStatus", catalog["centreline_definitions_mm"]["evidence_status"])
            axis08._add_property(obj, "App::PropertyString", "EvidenceJSON", json.dumps({
                "file": catalog["source"]["file"],
                "sheet": catalog["source"]["sheet"],
                "page": catalog["source"]["page"],
                "view": catalog["source"]["view"],
                "member_mark": member["source_mark"],
                "nominal_profile_standard": profile["source"],
            }, sort_keys=True))
            axis08._add_property(obj, "App::PropertyVector", "SourceCentrelineStart", axis08._vector(App, start), "Geometry")
            axis08._add_property(obj, "App::PropertyVector", "SourceCentrelineEnd", axis08._vector(App, end), "Geometry")
            axis08._add_property(obj, "App::PropertyLength", "CentrelineLength", length, "Geometry")
            axis08._add_property(obj, "App::PropertyString", "ExcludedDetail", "No base plates, bolts, connections, stiffeners, haunches or unlabelled secondary steel.", "Geometry")
            axis08._add_property(obj, "App::PropertyString", "ChangeSet", change_set["change_set"], "Display")
            axis08._add_property(obj, "App::PropertyString", "ChangeColourMeaning", change_set["meaning"], "Display")
            axis08._add_property(obj, "App::PropertyString", "DisplayVisibilityRequested", "VISIBLE", "Display")
            axis08._style_change_set(obj, change_colour)
            obj_view = getattr(obj, "ViewObject", None)
            if obj_view is not None:
                obj_view.Visibility = True
            groups[profile_key].addObject(obj)
        library_view = getattr(library, "ViewObject", None)
        if library_view is not None:
            library_view.Visibility = False
        doc.recompute()
        audit_axis_02(doc, catalog, axis01, axis07, axis08)
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
    return ROOT / "outputs" / ("axis02_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))


if __name__ == "__main__":
    build_axis_02(_default_output_dir())