# -*- coding: utf-8 -*-
"""Add approved A11 axis-3 members to the cumulative development build."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXIS02_MODULE = Path(__file__).with_name("allshield_axis_02.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_03_draft.json")


def _profile_key(member):
    return member["profile_label"].split("-", 1)[0]


def _load_axis02():
    spec = importlib.util.spec_from_file_location("allshield_axis02_for_axis03", str(AXIS02_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_03_354": "IPE500-S355JR", "A11_03_355": "IPE500-S355JR",
        "A11_03_318": "HEA200", "A11_03_322": "HEA200",
        "A11_03_352": "IPE500-S355JR", "A11_03_351": "IPE500-S355JR",
    }
    members = catalog.get("approved_members", [])
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1" or {
            member.get("id"): member.get("profile_label") for member in members} != expected:
        raise ValueError("Axis-3 catalog must contain exactly the six approved members.")
    for member in members:
        profile = catalog["nominal_profile_status"].get(_profile_key(member), {})
        if member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" or member["id"] not in catalog["centreline_definitions_mm"]:
            raise ValueError("Missing approved source geometry for " + member["id"])
        if profile.get("source") != "NEN-EN 10365:2017" or "dimensions_mm" not in profile:
            raise ValueError("Missing nominal profile data for " + member["id"])
    return catalog


def audit_axis_03(doc, catalog, axis02, axis01, axis07, axis08):
    """Check the cumulative build and six source-derived axis-3 solids."""
    import FreeCAD as App
    import Part

    axis02.audit_axis_02(doc, axis02._load_catalog(), axis01, axis07, axis08)
    frame = doc.getObject("Frame_Axis_03")
    ipe_members = doc.getObject("Axis03_IPE500_Members")
    hea_members = doc.getObject("Axis03_HEA200_Members")
    portal_frames = doc.getObject("Portal_Frames")
    if not all((frame, ipe_members, hea_members, portal_frames)):
        raise AssertionError("Missing axis-3 portal hierarchy.")
    failures = []
    if frame not in portal_frames.Group or ipe_members not in frame.Group or hea_members not in frame.Group:
        failures.append("Wrong Frame_Axis_03 parentage.")
    expected_members = {member["id"]: member for member in catalog["approved_members"]}
    actual_members = {obj.Name for obj in doc.Objects if obj.Name.startswith("A11_03_")}
    if actual_members != set(expected_members):
        failures.append("Unexpected axis-3 member set: " + repr(sorted(actual_members)))
    rows = []
    for member_id, member in expected_members.items():
        obj = doc.getObject(member_id)
        if obj is None or obj.TypeId != "App::Link" or obj.LinkedObject is None:
            failures.append("Missing linked nominal profile solid " + member_id)
            continue
        profile_key = _profile_key(member)
        expected_group = ipe_members if profile_key == "IPE500" else hea_members
        if obj not in expected_group.Group or obj.EvidenceStatus != "VECTOR_MEASUREMENT":
            failures.append("Incorrect group or evidence status " + member_id)
        if obj.ChangeSet != catalog["change_visualisation"]["change_set"] or obj.DisplayVisibilityRequested != "VISIBLE":
            failures.append("Incorrect display metadata " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        placement, length = axis08._member_placement(App, start, end)
        profile = catalog["nominal_profile_status"][profile_key]
        face = axis01._nominal_profile_face(axis08, App, Part, profile)
        expected = face.extrude(App.Vector(0, length, 0))
        expected.Placement = placement
        bbox = axis08._bbox(shape)
        error = axis08._max_bbox_error(bbox, axis08._bbox(expected))
        if error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (member_id, error))
        if abs(shape.Volume - face.Area * length) > 0.01:
            failures.append("Nominal section volume mismatch " + member_id)
        if obj.SectionOrientation != profile["section_orientation"]:
            failures.append("Incorrect section orientation metadata " + member_id)
        if profile_key == "HEA200" and abs((bbox[4] - bbox[1]) - profile["source_projected_in_plane_height_mm"]) > axis08.TOLERANCE_MM:
            failures.append("HEA200 source-plane height mismatch " + member_id)
        rows.append({"id": member_id, "source_mark": member["source_mark"], "profile": member["profile_label"], "centreline_length_mm": length, "volume_mm3": shape.Volume, "world_bbox_mm": bbox, "world_bbox_error_mm": error})
    report = {"pass": not failures, "members_checked": len(rows), "computational_tolerance_mm": axis08.TOLERANCE_MM, "failures": failures, "as_built_verified": False, "fabrication_model": False, "members": rows}
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def build_axis_03(output_dir, detail_mode="WORK"):
    """Build the validated prior slices plus six approved A11/as-3 members."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    axis02 = _load_axis02()
    axis01 = axis02._load_axis01()
    axis07 = axis01._load_axis07()
    axis08 = axis07._load_axis08()
    catalog = _load_catalog()
    doc = axis02.build_axis_02(output, detail_mode)
    try:
        doc.openTransaction("Add approved A11 axis-3 nominal primary members")
        portal_frames, library = doc.getObject("Portal_Frames"), doc.getObject("Component_Library")
        if portal_frames is None or library is None:
            raise RuntimeError("Cumulative build has no Portal_Frames or Component_Library.")
        frame = axis08._add_group(doc, portal_frames, "Frame_Axis_03", "Frame_Axis_03 | A11 source-based", "VECTOR_MEASUREMENT", "A11 page 1, AANZICHT as-3; only approved IPE500 and HEA200 members are nominal coordination solids.")
        ipe_members = axis08._add_group(doc, frame, "Axis03_IPE500_Members", "IPE500_Members", "VECTOR_MEASUREMENT", "Only approved outer columns 354/355 and roof members 352/351 from A11/as-3.")
        hea_members = axis08._add_group(doc, frame, "Axis03_HEA200_Members", "HEA200_Members", "VECTOR_MEASUREMENT", "Only approved vertical members 318/322 from A11/as-3.")
        axis08._add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(frame, "App::PropertyString", "NominalProfileStandard", "NEN-EN 10365:2017", "Build")
        axis08._add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        axis08._add_property(frame, "App::PropertyString", "ChangeSetJSON", json.dumps(catalog["change_visualisation"], sort_keys=True), "Display")
        groups, prototypes = {"IPE500": ipe_members, "HEA200": hea_members}, {}
        change_set = catalog["change_visualisation"]
        colour = tuple(float(value) for value in change_set["rgb"])
        for member in catalog["approved_members"]:
            member_id, profile_key = member["id"], _profile_key(member)
            start, end = catalog["centreline_definitions_mm"][member_id]["start"], catalog["centreline_definitions_mm"][member_id]["end"]
            placement, length = axis08._member_placement(App, start, end)
            profile = catalog["nominal_profile_status"][profile_key]
            prototype_key = "%s_%.6f" % (profile_key, length)
            if prototype_key not in prototypes:
                shape = axis01._nominal_profile_face(axis08, App, Part, profile).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal solid " + prototype_key)
                prototype = doc.addObject("Part::Feature", "Prototype_Axis03_" + prototype_key.replace(".", "_"))
                prototype.Label, prototype.Shape, prototype.Placement = "Prototype | nominal %s | as-3" % profile_key, shape, placement
                axis08._add_property(prototype, "App::PropertyString", "NominalProfileStandard", profile["source"])
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
            obj.Label, obj.LinkPlacement = "A11 / as-3 / %s / %s" % (member["source_mark"], member["profile_label"]), placement
            if "LinkTransform" in obj.PropertiesList:
                obj.LinkTransform = False
            for type_name, name, value, group in (
                ("App::PropertyString", "StableComponentId", member_id, "Source"), ("App::PropertyString", "SourceMemberMark", member["source_mark"], "Source"),
                ("App::PropertyString", "ProfileLabel", member["profile_label"], "Source"), ("App::PropertyString", "SectionOrientation", profile["section_orientation"], "Source"),
                ("App::PropertyString", "EvidenceStatus", "VECTOR_MEASUREMENT", "Source"), ("App::PropertyVector", "SourceCentrelineStart", axis08._vector(App, start), "Geometry"),
                ("App::PropertyVector", "SourceCentrelineEnd", axis08._vector(App, end), "Geometry"), ("App::PropertyLength", "CentrelineLength", length, "Geometry"),
                ("App::PropertyString", "ExcludedDetail", "No base plates, bolts, connections, stiffeners, haunches or unlabelled secondary steel.", "Geometry"),
                ("App::PropertyString", "ChangeSet", change_set["change_set"], "Display"), ("App::PropertyString", "ChangeColourMeaning", change_set["meaning"], "Display"), ("App::PropertyString", "DisplayVisibilityRequested", "VISIBLE", "Display")):
                axis08._add_property(obj, type_name, name, value, group)
            axis08._add_property(obj, "App::PropertyString", "EvidenceJSON", json.dumps({"file": catalog["source"]["file"], "sheet": "A11", "page": 1, "view": "AANZICHT as-3", "member_mark": member["source_mark"], "nominal_profile_standard": profile["source"]}, sort_keys=True))
            axis08._style_change_set(obj, colour)
            obj_view = getattr(obj, "ViewObject", None)
            if obj_view is not None:
                obj_view.Visibility = True
            groups[profile_key].addObject(obj)
        library_view = getattr(library, "ViewObject", None)
        if library_view is not None:
            library_view.Visibility = False
        doc.recompute()
        audit_axis_03(doc, catalog, axis02, axis01, axis07, axis08)
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
    build_axis_03(ROOT / "outputs" / ("axis03_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))