# -*- coding: utf-8 -*-
"""Add four source-mapped A11/as-20 IPE500 primary members to the cumulative build."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACADE_MODULE = Path(__file__).with_name("allshield_facade1_window_projection.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_20_draft.json")


def _load_facade():
    spec = importlib.util.spec_from_file_location("allshield_facade1_for_axis20", str(FACADE_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_20_30": "IPE500-S355JR",
        "A11_20_29": "IPE500-S355JR",
        "A11_20_21": "IPE500-S355JR",
        "A11_20_25": "IPE500-S355JR",
    }
    members = catalog.get("approved_members", [])
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1" or {
            member.get("id"): member.get("profile_label") for member in members} != expected:
        raise ValueError("Axis-20 catalog must contain exactly four approved IPE500 members.")
    profile = catalog.get("nominal_profile_status", {}).get("IPE500", {})
    if profile.get("source") != "NEN-EN 10365:2017" or "dimensions_mm" not in profile:
        raise ValueError("Axis-20 catalog has no valid nominal IPE500 profile.")
    for member in members:
        member_id = member["id"]
        if (member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" or
                member_id not in catalog.get("centreline_definitions_mm", {}) or
                len(member.get("direct_pdf_path_indices", [])) != 2):
            raise ValueError("Missing approved source geometry for " + member_id)
    return catalog


def _load_dependencies(facade):
    roof_zones = facade._load_roof_zones()
    axis01_wvb = roof_zones._load_axis01_wvb()
    axis05 = axis01_wvb._load_axis05()
    axis03 = axis05._load_axis03()
    axis02 = axis03._load_axis02()
    axis01 = axis02._load_axis01()
    axis07 = axis01._load_axis07()
    axis08 = axis07._load_axis08()
    return roof_zones, axis01_wvb, axis05, axis03, axis02, axis01, axis07, axis08


def audit_axis_20(doc, catalog, facade):
    """Check prior layers plus four source-mapped Axis-20 IPE500 solids."""
    import FreeCAD as App
    import Part

    roof_zones, axis01_wvb, axis05, axis03, axis02, axis01, axis07, axis08 = _load_dependencies(facade)
    facade.audit_facade1_window_projection(doc, facade._load_catalog(), roof_zones)
    frame = doc.getObject("Frame_Axis_20")
    primary = doc.getObject("Axis20_IPE500_Primary")
    portal_frames = doc.getObject("Portal_Frames")
    library = doc.getObject("Component_Library")
    if not all((frame, primary, portal_frames, library)):
        raise AssertionError("Missing Axis-20 portal hierarchy or Component_Library.")
    failures = []
    if frame not in portal_frames.Group or primary not in frame.Group:
        failures.append("Wrong Frame_Axis_20 parentage.")
    if library.Name in axis08._descendant_names(doc.getObject("Building")):
        failures.append("Component_Library is nested inside Building.")
    expected_members = {member["id"]: member for member in catalog["approved_members"]}
    actual_members = {obj.Name for obj in doc.Objects if obj.Name.startswith("A11_20_")}
    if actual_members != set(expected_members):
        failures.append("Unexpected Axis-20 member set: " + repr(sorted(actual_members)))
    profile = catalog["nominal_profile_status"]["IPE500"]
    rows = []
    for member_id, member in expected_members.items():
        obj = doc.getObject(member_id)
        if obj is None or obj.TypeId != "App::Link" or obj.LinkedObject is None:
            failures.append("Missing linked nominal profile solid " + member_id)
            continue
        if obj not in primary.Group or obj.EvidenceStatus != "VECTOR_MEASUREMENT":
            failures.append("Incorrect group or evidence status " + member_id)
        if obj.SourceMemberMark != member["source_mark"]:
            failures.append("Incorrect source member mark " + member_id)
        if obj.SectionOrientation != profile["section_orientation"]:
            failures.append("Incorrect section orientation metadata " + member_id)
        if obj.ChangeSet != catalog["change_visualisation"]["change_set"] or obj.DisplayVisibilityRequested != "VISIBLE":
            failures.append("Incorrect display metadata " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0.0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        placement, length = axis08._member_placement(App, start, end)
        face = axis01._nominal_profile_face(axis08, App, Part, profile)
        expected = face.extrude(App.Vector(0, length, 0))
        expected.Placement = placement
        error = axis08._max_bbox_error(axis08._bbox(shape), axis08._bbox(expected))
        if error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (member_id, error))
        if abs(shape.Volume - face.Area * length) > 0.01:
            failures.append("Nominal section volume mismatch " + member_id)
        rows.append({
            "id": member_id,
            "source_mark": member["source_mark"],
            "profile": member["profile_label"],
            "centreline_length_mm": length,
            "volume_mm3": shape.Volume,
            "world_bbox_mm": axis08._bbox(shape),
            "world_bbox_error_mm": error,
        })
    report = {
        "pass": not failures,
        "members_checked": len(rows),
        "computational_tolerance_mm": axis08.TOLERANCE_MM,
        "secondary_steel_created": False,
        "as_built_verified": False,
        "fabrication_model": False,
        "members": rows,
        "failures": failures,
    }
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def build_axis_20(output_dir, detail_mode="WORK"):
    """Build prior validated slices plus four approved A11/as-20 IPE500 members."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    facade = _load_facade()
    catalog = _load_catalog()
    _, _, _, _, _, axis01, _, axis08 = _load_dependencies(facade)
    doc = facade.build_facade1_window_projection(output, detail_mode)
    try:
        doc.openTransaction("Add four source-mapped A11 axis-20 IPE500 primary members")
        portal_frames = doc.getObject("Portal_Frames")
        library = doc.getObject("Component_Library")
        if portal_frames is None or library is None:
            raise RuntimeError("Cumulative build has no Portal_Frames or Component_Library.")
        frame = axis08._add_group(
            doc, portal_frames, "Frame_Axis_20", "Frame_Axis_20 | A11 source-based", "VECTOR_MEASUREMENT",
            "A11 page 1, AANZICHT as-20; only four source-mapped IPE500 primary members are nominal coordination solids.",
        )
        primary = axis08._add_group(
            doc, frame, "Axis20_IPE500_Primary", "IPE500_Primary", "VECTOR_MEASUREMENT",
            "Only A11/as-20 source marks 30, 29, 21 and 25 are included; all other labels remain unresolved.",
        )
        axis08._add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(frame, "App::PropertyString", "NominalProfileStandard", "NEN-EN 10365:2017", "Build")
        axis08._add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        axis08._add_property(frame, "App::PropertyString", "ChangeSetJSON", json.dumps(catalog["change_visualisation"], sort_keys=True), "Display")
        profile = catalog["nominal_profile_status"]["IPE500"]
        change_set = catalog["change_visualisation"]
        colour = tuple(float(value) for value in change_set["rgb"])
        prototypes = {}
        for member in catalog["approved_members"]:
            member_id = member["id"]
            start = catalog["centreline_definitions_mm"][member_id]["start"]
            end = catalog["centreline_definitions_mm"][member_id]["end"]
            placement, length = axis08._member_placement(App, start, end)
            prototype_key = "IPE500_%.6f" % length
            if prototype_key not in prototypes:
                shape = axis01._nominal_profile_face(axis08, App, Part, profile).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal IPE500 solid " + prototype_key)
                prototype = doc.addObject("Part::Feature", "Prototype_Axis20_" + prototype_key.replace(".", "_"))
                prototype.Label = "Prototype | nominal IPE500 | as-20"
                prototype.Shape = shape
                prototype.Placement = placement
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
            obj.Label = "A11 / as-20 / %s / %s" % (member["source_mark"], member["profile_label"])
            obj.LinkPlacement = placement
            if "LinkTransform" in obj.PropertiesList:
                obj.LinkTransform = False
            source_centreline = catalog["centreline_definitions_mm"][member_id]
            properties = (
                ("App::PropertyString", "StableComponentId", member_id, "Source"),
                ("App::PropertyString", "SourceMemberMark", member["source_mark"], "Source"),
                ("App::PropertyString", "ProfileLabel", member["profile_label"], "Source"),
                ("App::PropertyString", "SectionOrientation", profile["section_orientation"], "Source"),
                ("App::PropertyString", "EvidenceStatus", "VECTOR_MEASUREMENT", "Source"),
                ("App::PropertyString", "DirectPDFPathIndicesJSON", json.dumps(member["direct_pdf_path_indices"]), "Source"),
                ("App::PropertyVector", "SourceCentrelineStart", axis08._vector(App, start), "Geometry"),
                ("App::PropertyVector", "SourceCentrelineEnd", axis08._vector(App, end), "Geometry"),
                ("App::PropertyLength", "CentrelineLength", length, "Geometry"),
                ("App::PropertyString", "ExcludedDetail", "No base plates, bolts, connections, stiffeners, haunches, secondary steel, WVB bars or unlabelled members.", "Geometry"),
                ("App::PropertyString", "ChangeSet", change_set["change_set"], "Display"),
                ("App::PropertyString", "ChangeColourMeaning", change_set["meaning"], "Display"),
                ("App::PropertyString", "DisplayVisibilityRequested", "VISIBLE", "Display"),
            )
            for type_name, name, value, group in properties:
                axis08._add_property(obj, type_name, name, value, group)
            axis08._add_property(obj, "App::PropertyString", "EvidenceJSON", json.dumps({
                "file": catalog["source"]["file"], "sheet": catalog["source"]["sheet"], "page": catalog["source"]["page"],
                "view": catalog["source"]["view"], "member_mark": member["source_mark"],
                "direct_pdf_path_indices": member["direct_pdf_path_indices"], "centreline_derivation": source_centreline["derivation"],
                "nominal_profile_standard": profile["source"],
            }, sort_keys=True))
            axis08._style_change_set(obj, colour)
            obj_view = getattr(obj, "ViewObject", None)
            if obj_view is not None:
                obj_view.Visibility = True
            primary.addObject(obj)
        library_view = getattr(library, "ViewObject", None)
        if library_view is not None:
            library_view.Visibility = False
        doc.recompute()
        audit_axis_20(doc, catalog, facade)
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
    build_axis_20(ROOT / "outputs" / ("axis20_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))