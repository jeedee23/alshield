# -*- coding: utf-8 -*-
"""Add approved A11 axis-1 members to the cumulative development build."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXIS07_MODULE = Path(__file__).with_name("allshield_axis_07.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_01_draft.json")


def _profile_key(member):
    return member["profile_label"].split("-", 1)[0]


def _load_axis07():
    spec = importlib.util.spec_from_file_location("allshield_axis07_for_axis01", str(AXIS07_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1":
        raise ValueError("Unsupported axis-1 catalog schema.")
    expected_profiles = {
        "A11_01_324": "HEA200",
        "A11_01_323": "HEA200",
        "A11_01_341": "IPE300",
        "A11_01_339": "IPE300",
        "A11_01_337": "IPE300",
        "A11_01_338": "IPE300",
        "A11_01_340": "IPE300",
        "A11_01_302": "HEA180",
        "A11_01_303": "HEA180",
    }
    members = catalog.get("approved_members", [])
    if {member.get("id") for member in members} != set(expected_profiles):
        raise ValueError("Axis-1 catalog must contain exactly the nine approved members.")
    for member in members:
        member_id = member["id"]
        if member.get("profile_label") != expected_profiles[member_id]:
            raise ValueError("Unapproved profile in axis-1 solid slice: " + member_id)
        if member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID":
            raise ValueError("Member is not approved for nominal solid generation: " + member_id)
        if member_id not in catalog["centreline_definitions_mm"]:
            raise ValueError("Missing source-derived centreline for " + member_id)
        profile = catalog["nominal_profile_status"].get(_profile_key(member), {})
        if profile.get("source") != "NEN-EN 10365:2017" or "dimensions_mm" not in profile:
            raise ValueError("Missing approved nominal profile data for " + member_id)
    return catalog


def _nominal_profile_face(axis08, App, Part, profile):
    face = axis08._ipe_profile_face(App, Part, profile["dimensions_mm"])
    if profile.get("section_orientation") == "FLANGE_WIDTH_B_IN_A11_ELEVATION_PLANE":
        face.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
    return face


def audit_axis_01(doc, catalog, axis07, axis08):
    """Check the cumulative build and the nine source-derived axis-1 solids."""
    import FreeCAD as App
    import Part

    axis07.audit_axis_07(doc, axis07._load_catalog(), axis08)
    frame = doc.getObject("Frame_Axis_01")
    hea_columns = doc.getObject("Axis01_HEA200_Columns")
    ipe_columns = doc.getObject("Axis01_IPE300_Columns")
    hea_rafters = doc.getObject("Axis01_HEA180_Rafters")
    portal_frames = doc.getObject("Portal_Frames")
    if (frame is None or hea_columns is None or ipe_columns is None or
            hea_rafters is None or portal_frames is None):
        raise AssertionError("Missing axis-1 portal hierarchy.")
    failures = []
    if (frame not in portal_frames.Group or hea_columns not in frame.Group or
            ipe_columns not in frame.Group or hea_rafters not in frame.Group):
        failures.append("Wrong Frame_Axis_01 parentage.")
    expected_members = {member["id"]: member for member in catalog["approved_members"]}
    actual_axis01 = {obj.Name for obj in doc.Objects if obj.Name.startswith("A11_01_")}
    if actual_axis01 != set(expected_members):
        failures.append("Unexpected axis-1 member set: " + repr(sorted(actual_axis01)))
    expected_groups = {
        "HEA200": hea_columns,
        "IPE300": ipe_columns,
        "HEA180": hea_rafters,
    }
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
        change_set = catalog["change_visualisation"]
        if obj.ChangeSet != change_set["change_set"]:
            failures.append("Incorrect change-set ID " + member_id)
        if obj.DisplayVisibilityRequested != "VISIBLE":
            failures.append("Visibility is not explicitly requested for " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        profile_key = _profile_key(member)
        if obj not in expected_groups[profile_key].Group:
            failures.append("Member outside expected axis-1 group " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        expected_placement, length = axis08._member_placement(App, start, end)
        profile = catalog["nominal_profile_status"][profile_key]
        nominal_face = _nominal_profile_face(axis08, App, Part, profile)
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
        if profile_key == "HEA200":
            if abs((bbox[4] - bbox[1]) - profile["source_projected_in_plane_height_mm"]) > axis08.TOLERANCE_MM:
                failures.append("HEA200 source-plane height mismatch " + member_id)
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["flange_width_b"]) > axis08.TOLERANCE_MM:
                failures.append("HEA200 out-of-plane flange width mismatch " + member_id)
        if profile_key == "IPE300":
            if abs((bbox[4] - bbox[1]) - profile["source_projected_in_plane_width_mm"]) > axis08.TOLERANCE_MM:
                failures.append("IPE300 source-plane flange width mismatch " + member_id)
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["height_h"]) > axis08.TOLERANCE_MM:
                failures.append("IPE300 out-of-plane section height mismatch " + member_id)
        if profile_key == "HEA180":
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["flange_width_b"]) > axis08.TOLERANCE_MM:
                failures.append("HEA180 out-of-plane flange width mismatch " + member_id)
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


def build_axis_01(output_dir, detail_mode="WORK"):
    """Build the validated axis-8/axis-7 slices plus nine axis-1 members."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    axis07 = _load_axis07()
    axis08 = axis07._load_axis08()
    catalog = _load_catalog()
    doc = axis07.build_axis_07(output, detail_mode)
    try:
        doc.openTransaction("Add approved A11 axis-1 nominal main profiles")
        portal_frames = doc.getObject("Portal_Frames")
        library = doc.getObject("Component_Library")
        if portal_frames is None or library is None:
            raise RuntimeError("Cumulative build has no Portal_Frames or Component_Library.")
        frame = axis08._add_group(
            doc, portal_frames, "Frame_Axis_01", "Frame_Axis_01 | A11 source-based", "VECTOR_MEASUREMENT",
            "A11 page 1, AANZICHT as-1; only approved HEA200, IPE300 and HEA180 members are nominal coordination solids.",
        )
        hea_columns = axis08._add_group(
            doc, frame, "Axis01_HEA200_Columns", "HEA200_Columns", "VECTOR_MEASUREMENT",
            "Only approved outer columns 324 and 323 from A11/as-1.",
        )
        ipe_columns = axis08._add_group(
            doc, frame, "Axis01_IPE300_Columns", "IPE300_Columns", "VECTOR_MEASUREMENT",
            "Only approved internal vertical members 341, 339, 337, 338 and 340 from A11/as-1.",
        )
        hea_rafters = axis08._add_group(
            doc, frame, "Axis01_HEA180_Rafters", "HEA180_Rafters", "VECTOR_MEASUREMENT",
            "Only approved roof rafters 302 and 303 from A11/as-1.",
        )
        axis08._add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(frame, "App::PropertyString", "NominalProfileStandard", "NEN-EN 10365:2017", "Build")
        axis08._add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        axis08._add_property(frame, "App::PropertyString", "ChangeSetJSON", json.dumps(catalog["change_visualisation"], sort_keys=True), "Display")

        prototypes = {}
        groups = {"HEA200": hea_columns, "IPE300": ipe_columns, "HEA180": hea_rafters}
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
                shape = _nominal_profile_face(axis08, App, Part, profile).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal %s solid for %s" % (profile_key, prototype_key))
                prototype = doc.addObject("Part::Feature", "Prototype_Axis01_%s" % prototype_key.replace(".", "_"))
                prototype.Label = "Prototype | nominal %s | as-1" % profile_key
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
            obj.Label = "A11 / as-1 / %s / %s" % (member["source_mark"], member["profile_label"])
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
        audit_axis_01(doc, catalog, axis07, axis08)
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
    return ROOT / "outputs" / ("axis01_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))


if __name__ == "__main__":
    build_axis_01(_default_output_dir())