# -*- coding: utf-8 -*-
"""Add one directly projected C4a Facade_1 window-bank reference layer."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOF_ZONE_MODULE = Path(__file__).with_name("allshield_roof_penetration_zones.py")
CATALOG = Path(__file__).with_name("facade1_window_projection_catalog_draft.json")


def _load_roof_zones():
    spec = importlib.util.spec_from_file_location("allshield_roof_zones_for_facade1_window_projection", str(ROOF_ZONE_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    banks = catalog.get("window_banks", [])
    expected_glazing = [
        "Facade_1_Glass_Projection_26",
        "Facade_1_Glass_Projection_27",
        "Facade_1_Glass_Projection_28",
        "Facade_1_Glass_Projection_29",
        "Facade_1_Glass_Projection_30",
        "Facade_1_Glass_Projection_31",
    ]
    if catalog.get("schema") != "allshield.facade-window-projection-catalog.draft.v1" or len(banks) != 1:
        raise ValueError("Facade_1 window-projection catalog must contain exactly one bank.")
    bank = banks[0]
    if bank.get("id") != "Facade1_C4a_WindowBank_01":
        raise ValueError("Unexpected Facade_1 window-bank ID.")
    if bank.get("geometry_status") != "PLANAR_SOURCE_PROJECTION_NO_PHYSICAL_DEPTH":
        raise ValueError("Facade_1 window bank must remain a planar source projection.")
    if bank.get("world_plane_x_mm") != 65260.0 or bank.get("baseline_glazing_component_ids") != expected_glazing:
        raise ValueError("Facade_1 window-bank location or glazing references are incorrect.")
    paths = bank.get("source_path_indices", {})
    if paths != {"outer_perimeter": [322, 323, 324, 325], "mullions": [327, 329], "transoms": [326, 328, 330], "glazing": [597, 598, 599, 600, 601, 602]}:
        raise ValueError("Facade_1 window-bank source paths are incomplete or unexpected.")
    regions = bank.get("projection_regions_yz_mm", {})
    if len(regions.get("outer_frame", [])) != 4 or len(regions.get("mullions", [])) != 2 or len(regions.get("transoms", [])) != 3:
        raise ValueError("Facade_1 window-bank projection regions are incomplete.")
    if catalog.get("source", {}).get("photo_evidence", {}).get("status") != "PHYSICAL_FRAME_LAYERS_VISIBLE_BUT_LOCATION_CORRESPONDENCE_UNRESOLVED":
        raise ValueError("Photo-to-window correspondence must remain unresolved.")
    return catalog


def _rectangle_face(App, Part, plane_x, region):
    y_min, y_max, z_min, z_max = (float(value) for value in region)
    if y_max <= y_min or z_max <= z_min:
        raise ValueError("Invalid planar window-projection rectangle.")
    corners = [
        App.Vector(plane_x, y_min, z_min),
        App.Vector(plane_x, y_max, z_min),
        App.Vector(plane_x, y_max, z_max),
        App.Vector(plane_x, y_min, z_max),
    ]
    face = Part.Face(Part.makePolygon(corners + [corners[0]]))
    if face.isNull() or not face.isValid():
        raise ValueError("Invalid Facade_1 planar window-projection face.")
    return face


def _projection_shape(App, Part, plane_x, regions):
    faces = [_rectangle_face(App, Part, plane_x, region) for region in regions]
    shape = Part.makeCompound(faces)
    if shape.isNull() or not shape.isValid() or not shape.Faces or shape.Solids:
        raise ValueError("Facade_1 window projection must be a valid zero-depth face compound.")
    return shape


def _style_projection(obj, catalog):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return
    colour = tuple(float(value) for value in catalog["change_visualisation"]["rgb"])
    for key, value in (("ShapeColor", colour), ("LineColor", colour), ("LineWidth", 2.0), ("Transparency", 0)):
        if key in view.PropertiesList:
            setattr(view, key, value)
    if "Flat Lines" in view.listDisplayModes():
        view.DisplayMode = "Flat Lines"
    view.Visibility = True


def _window_projection_groups(doc, bank):
    return (
        doc.getObject("Facade_1_Openings"),
        doc.getObject("Facade1_C4a_Window_Projections"),
        doc.getObject(bank["id"]),
        doc.getObject(bank["id"] + "_OuterFrameProjection"),
        doc.getObject(bank["id"] + "_GridProjection"),
    )


def audit_facade1_window_projection(doc, catalog, roof_zones):
    """Check direct C4a planar-projection geometry and parentage."""
    import FreeCAD as App
    import Part

    axis01_wvb = roof_zones._load_axis01_wvb()
    roof_zones.audit_roof_penetration_zones(doc, roof_zones._load_catalog(), axis01_wvb)
    bank = catalog["window_banks"][0]
    openings, projection_root, bank_group, outer, grid = _window_projection_groups(doc, bank)
    if not all((openings, projection_root, bank_group, outer, grid)):
        raise AssertionError("Missing Facade_1 window-projection hierarchy.")
    failures = []
    if projection_root not in openings.Group or bank_group not in projection_root.Group or outer not in bank_group.Group or grid not in bank_group.Group:
        failures.append("Wrong Facade_1 window-projection parentage.")
    if set(obj.Name for obj in bank_group.Group) != {outer.Name, grid.Name}:
        failures.append("Unexpected Facade_1 window-bank child set.")
    axis05 = axis01_wvb._load_axis05()
    axis03 = axis05._load_axis03()
    axis02 = axis03._load_axis02()
    axis01 = axis02._load_axis01()
    axis07 = axis01._load_axis07()
    axis08 = axis07._load_axis08()
    expected_by_object = {
        outer.Name: _projection_shape(App, Part, bank["world_plane_x_mm"], bank["projection_regions_yz_mm"]["outer_frame"]),
        grid.Name: _projection_shape(App, Part, bank["world_plane_x_mm"], bank["projection_regions_yz_mm"]["mullions"] + bank["projection_regions_yz_mm"]["transoms"]),
    }
    rows = []
    for object_id, expected in expected_by_object.items():
        obj = doc.getObject(object_id)
        if obj.TypeId != "Part::Feature" or obj.EvidenceStatus != "DIRECT_C4A_VECTOR_PROJECTION":
            failures.append("Incorrect type or evidence status " + object_id)
            continue
        if obj.GeometryStatus != bank["geometry_status"] or obj.PhysicalDepthStatus != "UNRESOLVED_NOT_MODELLED":
            failures.append("Incorrect no-depth metadata " + object_id)
        shape = Part.getShape(obj)
        if shape.isNull() or not shape.isValid() or not shape.Faces or shape.Solids or abs(shape.Volume) > axis08.TOLERANCE_MM:
            failures.append("Invalid zero-depth projection geometry " + object_id)
            continue
        error = axis08._max_bbox_error(axis08._bbox(shape), axis08._bbox(expected))
        if error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch %s: %.6f mm" % (object_id, error))
        if abs(shape.BoundBox.XMin - bank["world_plane_x_mm"]) > axis08.TOLERANCE_MM or abs(shape.BoundBox.XMax - bank["world_plane_x_mm"]) > axis08.TOLERANCE_MM:
            failures.append("Unexpected physical depth in " + object_id)
        rows.append({"id": object_id, "faces": len(shape.Faces), "world_bbox_mm": axis08._bbox(shape), "world_bbox_error_mm": error})
    for glazing_id in bank["baseline_glazing_component_ids"]:
        glazing = doc.getObject(glazing_id)
        if glazing is None:
            failures.append("Missing mapped baseline glazing projection " + glazing_id)
    report = {
        "pass": not failures,
        "window_banks_checked": 1,
        "projection_objects_checked": len(rows),
        "physical_window_frame_created": False,
        "physical_glazing_created": False,
        "inner_frame_depth_verified": False,
        "street_side_frame_depth_verified": False,
        "photo_to_bank_correspondence_verified": False,
        "as_built_verified": False,
        "fabrication_model": False,
        "objects": rows,
        "failures": failures,
    }
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def build_facade1_window_projection(output_dir, detail_mode="WORK"):
    """Build preceding validated slices plus one C4a planar window-bank projection."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    roof_zones = _load_roof_zones()
    catalog = _load_catalog()
    bank = catalog["window_banks"][0]
    doc = roof_zones.build_roof_penetration_zones(output, detail_mode)
    try:
        doc.openTransaction("Add Facade 1 C4a window-bank source projection")
        openings = doc.getObject("Facade_1_Openings")
        if openings is None:
            raise RuntimeError("Cumulative build has no Facade_1_Openings group.")
        axis01_wvb = roof_zones._load_axis01_wvb()
        axis05 = axis01_wvb._load_axis05()
        axis03 = axis05._load_axis03()
        axis02 = axis03._load_axis02()
        axis01 = axis02._load_axis01()
        axis07 = axis01._load_axis07()
        axis08 = axis07._load_axis08()
        projection_root = axis08._add_group(
            doc, openings, "Facade1_C4a_Window_Projections", "C4a_Window_Projections", "DIRECT_C4A_VECTOR_PROJECTION",
            "Planar C4a window-bank source projections only; physical frame depth remains unresolved.",
        )
        bank_group = axis08._add_group(
            doc, projection_root, bank["id"], bank["label"], "DIRECT_C4A_VECTOR_PROJECTION",
            "Six baseline cyan glazing fields with directly adjacent black C4a outer-perimeter, mullion and transom paths.",
        )
        axis08._add_property(bank_group, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(bank_group, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(bank_group, "App::PropertyString", "ModelStatus", "PLANAR_SOURCE_PROJECTION_NOT_PHYSICAL_WINDOW", "Build")
        axis08._add_property(bank_group, "App::PropertyString", "SourcePathIndicesJSON", json.dumps(bank["source_path_indices"], sort_keys=True), "Source")
        axis08._add_property(bank_group, "App::PropertyString", "EvidenceJSON", json.dumps(catalog["source"], sort_keys=True), "Source")
        definitions = (
            ("OuterFrameProjection", "C4a outer frame projection", "outer_frame", bank["source_path_indices"]["outer_perimeter"]),
            ("GridProjection", "C4a mullion and transom projection", "mullions", bank["source_path_indices"]["mullions"] + bank["source_path_indices"]["transoms"]),
        )
        for suffix, label, region_key, source_paths in definitions:
            regions = bank["projection_regions_yz_mm"][region_key]
            if region_key == "mullions":
                regions = regions + bank["projection_regions_yz_mm"]["transoms"]
            obj = doc.addObject("Part::Feature", bank["id"] + "_" + suffix)
            obj.Label = label
            obj.Shape = _projection_shape(App, Part, bank["world_plane_x_mm"], regions)
            axis08._add_property(obj, "App::PropertyString", "StableComponentId", obj.Name, "Source")
            axis08._add_property(obj, "App::PropertyString", "EvidenceStatus", "DIRECT_C4A_VECTOR_PROJECTION", "Source")
            axis08._add_property(obj, "App::PropertyString", "DirectPDFPathIndicesJSON", json.dumps(source_paths), "Source")
            axis08._add_property(obj, "App::PropertyString", "EvidenceJSON", json.dumps(catalog["source"], sort_keys=True), "Source")
            axis08._add_property(obj, "App::PropertyVector", "ProjectionPlanePoint", App.Vector(bank["world_plane_x_mm"], 0.0, 0.0), "Geometry")
            axis08._add_property(obj, "App::PropertyString", "GeometryStatus", bank["geometry_status"], "Geometry")
            axis08._add_property(obj, "App::PropertyString", "PhysicalDepthStatus", "UNRESOLVED_NOT_MODELLED", "Geometry")
            axis08._add_property(obj, "App::PropertyString", "ExcludedDetail", bank["excluded_detail"], "Geometry")
            axis08._add_property(obj, "App::PropertyString", "ChangeSet", catalog["change_visualisation"]["change_set"], "Display")
            axis08._add_property(obj, "App::PropertyString", "ChangeColourMeaning", catalog["change_visualisation"]["meaning"], "Display")
            _style_projection(obj, catalog)
            bank_group.addObject(obj)
        doc.recompute()
        audit_facade1_window_projection(doc, catalog, roof_zones)
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
    build_facade1_window_projection(ROOT / "outputs" / ("facade1_window_projection_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))