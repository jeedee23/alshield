# -*- coding: utf-8 -*-
"""Add the approved A11 axis-7 members to the axis-8 development build."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXIS08_MODULE = Path(__file__).with_name("allshield_axis_08.py")
CATALOG = Path(__file__).with_name("steel_catalog_axis_07_draft.json")


def _profile_key(member):
    return member["profile_label"].split("-", 1)[0]


def _member_change_visualisation(catalog, member):
    change_property = {
        "IPE500": "change_visualisation",
        "IPE450": "rafter_change_visualisation",
        "IPE180": "ipe180_change_visualisation",
        "HEA200": "hea200_change_visualisation",
        "HEA180": "hea180_hea160_change_visualisation",
        "HEA160": "hea180_hea160_change_visualisation",
    }.get(_profile_key(member))
    if change_property is None:
        raise ValueError("No display change set for " + member["id"])
    return catalog[change_property]


def _nominal_profile_face(axis08, App, Part, profile):
    face = axis08._ipe_profile_face(App, Part, profile["dimensions_mm"])
    if profile.get("section_orientation") == "FLANGE_WIDTH_B_IN_A11_ELEVATION_PLANE":
        face.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
    return face


def _load_axis08():
    spec = importlib.util.spec_from_file_location("allshield_axis08_for_axis07", str(AXIS08_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema") != "allshield.steel-member-catalog.draft.v1":
        raise ValueError("Unsupported axis-7 catalog schema.")
    expected_profiles = {
        "A11_07_356": "IPE500-S355JR",
        "A11_07_357": "IPE500-S355JR",
        "A11_07_349": "IPE450-S355JR",
        "A11_07_350": "IPE450-S355JR",
        "A11_07_334": "IPE180",
        "A11_07_331": "IPE180",
        "A11_07_333": "IPE180",
        "A11_07_328": "IPE180",
        "A11_07_330": "IPE180",
        "A11_07_332": "IPE180",
        "A11_07_326": "HEA200",
        "A11_07_321": "HEA200",
        "A11_07_317": "HEA200",
        "A11_07_320": "HEA200",
        "A11_07_325": "HEA200",
        "A11_07_314": "HEA180-S355JR",
        "A11_07_300": "HEA160",
    }
    members = catalog.get("approved_members", [])
    if {member.get("id") for member in members} != set(expected_profiles):
        raise ValueError("Axis-7 catalog must contain exactly the seventeen approved members.")
    for member in members:
        if member.get("profile_label") != expected_profiles[member["id"]]:
            raise ValueError("Unapproved profile in axis-7 solid slice: " + member["id"])
        if member.get("geometry_status") != "APPROVED_FOR_NOMINAL_COORDINATION_SOLID":
            raise ValueError("Member is not approved for nominal solid generation: " + member["id"])
        profile = catalog["nominal_profile_status"].get(_profile_key(member), {})
        if profile.get("source") != "NEN-EN 10365:2017" or "dimensions_mm" not in profile:
            raise ValueError("Missing approved nominal profile data for " + member["id"])
    return catalog


def audit_axis_07(doc, catalog, axis08):
    """Check the cumulative build and the seventeen source-derived axis-7 solids."""
    import FreeCAD as App
    import Part

    axis08.audit_axis_08(doc, axis08._load_catalog())
    frame = doc.getObject("Frame_Axis_07")
    columns = doc.getObject("Primary_IPE500_Columns")
    rafters = doc.getObject("Primary_IPE450_Rafters")
    horizontals = doc.getObject("Axis07_Labeled_IPE180_Members")
    hea_verticals = doc.getObject("Axis07_HEA200_Vertical_Members")
    hea_horizontals = doc.getObject("Axis07_Labeled_HEA180_HEA160_Members")
    portal_frames = doc.getObject("Portal_Frames")
    if (frame is None or columns is None or rafters is None or horizontals is None or
            hea_verticals is None or hea_horizontals is None or portal_frames is None):
        raise AssertionError("Missing axis-7 portal hierarchy.")
    failures = []
    if (frame not in portal_frames.Group or columns not in frame.Group or
            rafters not in frame.Group or horizontals not in frame.Group or
            hea_verticals not in frame.Group or hea_horizontals not in frame.Group):
        failures.append("Wrong Frame_Axis_07 parentage.")
    expected_members = {member["id"]: member for member in catalog["approved_members"]}
    actual_axis07 = {obj.Name for obj in doc.Objects if obj.Name.startswith("A11_07_")}
    if actual_axis07 != set(expected_members):
        failures.append("Unexpected axis-7 member set: " + repr(sorted(actual_axis07)))
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
        change_set = _member_change_visualisation(catalog, member)
        if obj.ChangeSet != change_set["change_set"]:
            failures.append("Incorrect change-set ID " + member_id)
        if obj.DisplayVisibilityRequested != "VISIBLE":
            failures.append("Visibility is not explicitly requested for " + member_id)
        if "LinkTransform" in obj.PropertiesList and obj.LinkTransform:
            failures.append("Unexpected LinkTransform=True for " + member_id)
        expected_group = {
            "IPE500": columns,
            "IPE450": rafters,
            "IPE180": horizontals,
            "HEA200": hea_verticals,
            "HEA180": hea_horizontals,
            "HEA160": hea_horizontals,
        }[_profile_key(member)]
        if obj not in expected_group.Group:
            failures.append("Member outside expected axis-7 group " + member_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
            failures.append("Invalid or non-solid geometry " + member_id)
            continue
        start = catalog["centreline_definitions_mm"][member_id]["start"]
        end = catalog["centreline_definitions_mm"][member_id]["end"]
        expected_placement, length = axis08._member_placement(App, start, end)
        profile = catalog["nominal_profile_status"][_profile_key(member)]
        nominal_face = _nominal_profile_face(axis08, App, Part, profile)
        expected = nominal_face.extrude(App.Vector(0, length, 0))
        expected.Placement = expected_placement
        bbox_error = axis08._max_bbox_error(axis08._bbox(shape), axis08._bbox(expected))
        if bbox_error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (member_id, bbox_error))
        volume_error = abs(shape.Volume - nominal_face.Area * length)
        if volume_error > 0.01:
            failures.append("Nominal section volume mismatch %s: %.6f mm3" % (member_id, volume_error))
        if _profile_key(member) == "HEA200":
            if obj.SectionOrientation != profile["section_orientation"]:
                failures.append("Incorrect HEA200 section orientation metadata " + member_id)
            bbox = axis08._bbox(shape)
            if abs((bbox[4] - bbox[1]) - profile["source_projected_in_plane_width_mm"]) > axis08.TOLERANCE_MM:
                failures.append("HEA200 source-plane width mismatch " + member_id)
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["height_h"]) > axis08.TOLERANCE_MM:
                failures.append("HEA200 out-of-plane depth mismatch " + member_id)
        if _profile_key(member) in {"HEA180", "HEA160"}:
            if obj.SectionOrientation != profile["section_orientation"]:
                failures.append("Incorrect horizontal HEA section orientation metadata " + member_id)
            bbox = axis08._bbox(shape)
            if abs((bbox[5] - bbox[2]) - profile["source_projected_in_plane_height_mm"]) > axis08.TOLERANCE_MM:
                failures.append("Horizontal HEA source-plane height mismatch " + member_id)
            if abs((bbox[3] - bbox[0]) - profile["dimensions_mm"]["flange_width_b"]) > axis08.TOLERANCE_MM:
                failures.append("Horizontal HEA out-of-plane flange width mismatch " + member_id)
        rows.append({
            "id": member_id,
            "source_mark": member["source_mark"],
            "profile": member["profile_label"],
            "section_orientation": profile.get("section_orientation", "STANDARD_A11_ELEVATION_ORIENTATION"),
            "change_set": change_set["change_set"],
            "centreline_length_mm": length,
            "volume_mm3": shape.Volume,
            "world_bbox_mm": axis08._bbox(shape),
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


def build_axis_07(output_dir, detail_mode="WORK"):
    """Build the validated axis-8 slice plus the seventeen approved axis-7 members."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    axis08 = _load_axis08()
    catalog = _load_catalog()
    doc = axis08.build_axis_08(output, detail_mode)
    try:
        doc.openTransaction("Add approved A11 axis-7 nominal IPE and HEA members")
        portal_frames = doc.getObject("Portal_Frames")
        library = doc.getObject("Component_Library")
        if portal_frames is None or library is None:
            raise RuntimeError("Axis-8 build has no Portal_Frames or Component_Library.")
        frame = axis08._add_group(
            doc, portal_frames, "Frame_Axis_07", "Frame_Axis_07 | A11 source-based", "VECTOR_MEASUREMENT",
            "A11 page 1, AANZICHT as-7; only approved IPE500, IPE450, IPE180, HEA200, HEA180 and HEA160 members are nominal coordination solids.",
        )
        columns = axis08._add_group(
            doc, frame, "Primary_IPE500_Columns", "Primary_IPE500_Columns", "VECTOR_MEASUREMENT",
            "Only the two approved outer columns 356 and 357 from A11/as-7.",
        )
        rafters = axis08._add_group(
            doc, frame, "Primary_IPE450_Rafters", "Primary_IPE450_Rafters", "VECTOR_MEASUREMENT",
            "Only the two approved roof rafters 349 and 350 from A11/as-7.",
        )
        horizontals = axis08._add_group(
            doc, frame, "Axis07_Labeled_IPE180_Members", "Labeled_IPE180_Members", "VECTOR_MEASUREMENT",
            "Only the six approved horizontal members 334, 331, 333, 328, 330 and 332 from A11/as-7.",
        )
        hea_verticals = axis08._add_group(
            doc, frame, "Axis07_HEA200_Vertical_Members", "HEA200_Vertical_Members", "VECTOR_MEASUREMENT",
            "Only the five approved vertical members 326, 321, 317, 320 and 325 from A11/as-7.",
        )
        hea_horizontals = axis08._add_group(
            doc, frame, "Axis07_Labeled_HEA180_HEA160_Members", "Labeled_HEA180_HEA160_Members", "VECTOR_MEASUREMENT",
            "Only approved horizontal members 314 HEA180-S355JR and 300 HEA160 from A11/as-7.",
        )
        axis08._add_property(frame, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(frame, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(frame, "App::PropertyString", "NominalProfileStandard", "NEN-EN 10365:2017", "Build")
        axis08._add_property(frame, "App::PropertyString", "ModelStatus", "SOURCE_BASED_TER_CONTROLE_NOT_AS_BUILT_OR_FABRICATION", "Build")
        axis08._add_property(frame, "App::PropertyString", "ChangeSetsJSON", json.dumps({
            "IPE500": catalog["change_visualisation"],
            "IPE450": catalog["rafter_change_visualisation"],
            "IPE180": catalog["ipe180_change_visualisation"],
            "HEA200": catalog["hea200_change_visualisation"],
            "HEA180_HEA160": catalog["hea180_hea160_change_visualisation"],
        }, sort_keys=True), "Display")

        prototypes = {}
        for member in catalog["approved_members"]:
            member_id = member["id"]
            start = catalog["centreline_definitions_mm"][member_id]["start"]
            end = catalog["centreline_definitions_mm"][member_id]["end"]
            placement, length = axis08._member_placement(App, start, end)
            profile_key = _profile_key(member)
            profile = catalog["nominal_profile_status"][profile_key]
            change_set = _member_change_visualisation(catalog, member)
            change_colour = tuple(float(component) for component in change_set["rgb"])
            if len(change_colour) != 3 or any(component < 0 or component > 1 for component in change_colour):
                raise ValueError("Invalid display-only change-set RGB value for " + member_id)
            prototype_key = "%s_%.6f" % (profile_key, length)
            if prototype_key not in prototypes:
                shape = _nominal_profile_face(axis08, App, Part, profile).extrude(App.Vector(0, length, 0))
                if shape.isNull() or not shape.isValid() or not shape.Solids:
                    raise RuntimeError("Invalid nominal %s solid for %s" % (profile_key, prototype_key))
                prototype = doc.addObject("Part::Feature", "Prototype_Axis07_%s" % prototype_key.replace(".", "_"))
                prototype.Label = "Prototype | nominal %s | as-7" % profile_key
                prototype.Shape = shape
                prototype.Placement = placement
                axis08._add_property(prototype, "App::PropertyString", "NominalProfileStandard", profile["source"])
                axis08._add_property(prototype, "App::PropertyString", "ProfileDimensionsJSON", json.dumps(profile["dimensions_mm"], sort_keys=True))
                axis08._add_property(prototype, "App::PropertyString", "SectionOrientation", profile.get("section_orientation", "STANDARD_A11_ELEVATION_ORIENTATION"))
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
            obj.Label = "A11 / as-7 / %s / %s" % (member["source_mark"], member["profile_label"])
            if "LinkTransform" in obj.PropertiesList:
                obj.LinkTransform = False
            obj.LinkPlacement = placement
            axis08._add_property(obj, "App::PropertyString", "StableComponentId", member_id)
            axis08._add_property(obj, "App::PropertyString", "SourceMemberMark", member["source_mark"])
            axis08._add_property(obj, "App::PropertyString", "ProfileLabel", member["profile_label"])
            axis08._add_property(obj, "App::PropertyString", "SectionOrientation", profile.get("section_orientation", "STANDARD_A11_ELEVATION_ORIENTATION"))
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
            {
                "IPE500": columns,
                "IPE450": rafters,
                "IPE180": horizontals,
                "HEA200": hea_verticals,
                "HEA180": hea_horizontals,
                "HEA160": hea_horizontals,
            }[profile_key].addObject(obj)
        library_view = getattr(library, "ViewObject", None)
        if library_view is not None:
            library_view.Visibility = False
        doc.recompute()
        audit_axis_07(doc, catalog, axis08)
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
    return ROOT / "outputs" / ("axis07_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))


if __name__ == "__main__":
    build_axis_07(_default_output_dir())