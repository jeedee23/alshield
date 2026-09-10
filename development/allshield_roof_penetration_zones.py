# -*- coding: utf-8 -*-
"""Add non-cutting, user-requested roof-penetration coordination markers."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXIS01_WVB_MODULE = Path(__file__).with_name("allshield_axis_01_wvb.py")
CATALOG = Path(__file__).with_name("roof_penetration_zone_catalog_draft.json")
MARKER_THICKNESS_MM = 5.0


def _load_axis01_wvb():
    spec = importlib.util.spec_from_file_location("allshield_axis01_wvb_for_roof_penetration", str(AXIS01_WVB_MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected_id = "Planned_Roof_Penetration_DN900_01"
    zones = catalog.get("zones", [])
    if catalog.get("schema") != "allshield.roof-penetration-zone-catalog.draft.v1" or len(zones) != 1:
        raise ValueError("Roof penetration catalog must contain exactly one supported zone.")
    zone = zones[0]
    if zone.get("id") != expected_id or zone.get("nominal_opening_diameter_mm") != 900.0:
        raise ValueError("Catalog must contain only the requested DN900 zone.")
    if zone.get("requested_centre_xy_mm") != [10000.0, 8000.0] or zone.get("location_status") != "USER_PROVIDED_APPROXIMATE":
        raise ValueError("Catalog must retain the user-provided approximate location.")
    if zone.get("geometry_status") != "COORDINATION_MARKER_ONLY_DO_NOT_CUT_ROOF":
        raise ValueError("Roof zone must not generate a physical cutout.")
    roof = catalog.get("source", {}).get("roof_datum", {})
    corners = roof.get("crest_plane_corners_mm", [])
    if roof.get("baseline_component_id") != "SteelDeck_Envelope_A_to_Ridge1" or len(corners) != 4:
        raise ValueError("Roof zone must use the documented A-to-ridge-1 crest envelope.")
    if any(len(corner) != 3 for corner in corners):
        raise ValueError("Roof plane corners must be XYZ points.")
    colour = catalog.get("change_visualisation", {}).get("rgb", [])
    if len(colour) != 3 or any(float(value) < 0.0 or float(value) > 1.0 for value in colour):
        raise ValueError("Invalid roof-zone display colour.")
    if catalog["change_visualisation"].get("transparency_percent") != 70:
        raise ValueError("Roof zone display transparency must remain explicit.")
    return catalog


def _roof_centre_and_normal(App, catalog, zone):
    corners = catalog["source"]["roof_datum"]["crest_plane_corners_mm"]
    low_a, low_b, high_b, high_a = corners
    if low_a[1] != low_b[1] or high_a[1] != high_b[1] or low_a[2] != low_b[2] or high_a[2] != high_b[2]:
        raise ValueError("Roof datum corners do not define an X-invariant roof plane.")
    x, y = (float(value) for value in zone["requested_centre_xy_mm"])
    min_x, max_x = min(corner[0] for corner in corners), max(corner[0] for corner in corners)
    min_y, max_y = min(corner[1] for corner in corners), max(corner[1] for corner in corners)
    if not min_x <= x <= max_x or not min_y <= y <= max_y:
        raise ValueError("Requested roof zone lies outside the documented roof envelope.")
    rise = high_a[2] - low_a[2]
    run = high_a[1] - low_a[1]
    if run <= 0.0:
        raise ValueError("Invalid roof-plane Y run.")
    slope = rise / run
    z = low_a[2] + (y - low_a[1]) * slope
    normal_length = math.sqrt(1.0 + slope * slope)
    normal = App.Vector(0.0, -slope / normal_length, 1.0 / normal_length)
    return App.Vector(x, y, z), normal


def _marker_shape(App, Part, catalog, zone):
    centre, normal = _roof_centre_and_normal(App, catalog, zone)
    radius = float(zone["nominal_opening_diameter_mm"]) / 2.0
    if radius <= 0.0:
        raise ValueError("Roof penetration marker radius must be positive.")
    base = App.Vector(
        centre.x - normal.x * MARKER_THICKNESS_MM / 2.0,
        centre.y - normal.y * MARKER_THICKNESS_MM / 2.0,
        centre.z - normal.z * MARKER_THICKNESS_MM / 2.0,
    )
    shape = Part.makeCylinder(radius, MARKER_THICKNESS_MM, base, normal)
    if shape.isNull() or not shape.isValid() or not shape.Solids:
        raise ValueError("Invalid roof penetration marker geometry.")
    return shape, centre, normal


def _style_marker(obj, catalog):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return
    colour = tuple(float(value) for value in catalog["change_visualisation"]["rgb"])
    for key, value in (
        ("ShapeColor", colour),
        ("LineColor", colour),
        ("LineWidth", 3.0),
        ("Transparency", catalog["change_visualisation"]["transparency_percent"]),
    ):
        if key in view.PropertiesList:
            setattr(view, key, value)
    if "Flat Lines" in view.listDisplayModes():
        view.DisplayMode = "Flat Lines"
    view.Visibility = True


def audit_roof_penetration_zones(doc, catalog, axis01_wvb):
    """Check the marker's world geometry and known-modelled WVB clearance."""
    import Part

    axis05 = axis01_wvb._load_axis05()
    axis01_wvb.audit_axis_01_wvb(doc, axis01_wvb._load_catalog(), axis05)
    existing_services = doc.getObject("Existing_Services")
    zone_group = doc.getObject("Planned_Roof_Penetration_Zones")
    zone_definition = catalog["zones"][0]
    zone = doc.getObject(zone_definition["id"])
    if not all((existing_services, zone_group, zone)):
        raise AssertionError("Missing roof-penetration zone hierarchy.")
    failures = []
    if zone_group not in existing_services.Group or zone not in zone_group.Group:
        failures.append("Wrong roof-penetration zone parentage.")
    if zone.TypeId != "Part::Feature":
        failures.append("Roof-penetration zone must be a direct marker feature.")
    if zone.EvidenceStatus != "USER_PROVIDED_APPROXIMATE_COORDINATES":
        failures.append("Incorrect roof-zone evidence status.")
    if zone.GeometryStatus != "COORDINATION_MARKER_ONLY_DO_NOT_CUT_ROOF":
        failures.append("Roof zone incorrectly represents a physical cutout.")
    if zone.PanelContainmentStatus != "UNVERIFIED_PANEL_JOINT_PHASE_UNKNOWN":
        failures.append("Roof zone must retain unresolved sandwich-panel containment.")
    if zone.KnownBracingClearanceStatus != "CHECK_ONLY_AGAINST_CURRENTLY_MODELLED_A11_AXIS01_WVB_BARS":
        failures.append("Roof-zone bracing-clearance scope is incorrect.")
    shape = Part.getShape(zone)
    if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0.0:
        failures.append("Invalid roof-penetration marker geometry.")
        shape = None
    expected, centre, normal = _marker_shape(__import__("FreeCAD"), Part, catalog, zone_definition)
    if shape is not None:
        axis05 = axis01_wvb._load_axis05()
        axis03 = axis05._load_axis03()
        axis02 = axis03._load_axis02()
        axis01 = axis02._load_axis01()
        axis07 = axis01._load_axis07()
        axis08 = axis07._load_axis08()
        bounds_error = axis08._max_bbox_error(axis08._bbox(shape), axis08._bbox(expected))
        if bounds_error > axis08.TOLERANCE_MM:
            failures.append("Effective world bounds mismatch for roof-penetration zone: %.6f mm" % bounds_error)
        expected_volume = math.pi * (float(zone_definition["nominal_opening_diameter_mm"]) / 2.0) ** 2 * MARKER_THICKNESS_MM
        if abs(shape.Volume - expected_volume) > 0.01:
            failures.append("Roof-penetration marker volume mismatch.")
        for brace_id in ("A11_01_WVB400", "A11_01_WVB401_ASC", "A11_01_WVB401_DESC", "A11_01_WVB402", "A11_01_WVB399", "A11_01_WVB403"):
            brace = doc.getObject(brace_id)
            if brace is None:
                failures.append("Missing known WVB bar for clearance check: " + brace_id)
                continue
            intersection = shape.common(Part.getShape(brace))
            if not intersection.isNull() and intersection.Volume > 0.000001:
                failures.append("Roof-penetration marker intersects known modelled WVB bar: " + brace_id)
    report = {
        "pass": not failures,
        "zones_checked": 1,
        "marker_centre_on_crest_plane_mm": [centre.x, centre.y, centre.z],
        "crest_plane_up_normal": [normal.x, normal.y, normal.z],
        "nominal_opening_diameter_mm": zone_definition["nominal_opening_diameter_mm"],
        "physical_roof_cutout_created": False,
        "panel_containment_verified": False,
        "known_modelled_wvb_clearance_checked": True,
        "as_built_verified": False,
        "fabrication_model": False,
        "failures": failures,
    }
    if failures:
        raise AssertionError("; ".join(failures))
    return report


def build_roof_penetration_zones(output_dir, detail_mode="WORK"):
    """Build prior validated slices plus the requested non-cutting DN900 marker."""
    import FreeCAD as App
    import Part

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    axis01_wvb = _load_axis01_wvb()
    catalog = _load_catalog()
    zone_definition = catalog["zones"][0]
    doc = axis01_wvb.build_axis_01_wvb(output, detail_mode)
    try:
        doc.openTransaction("Add user-requested DN900 roof penetration planning zone")
        existing_services = doc.getObject("Existing_Services")
        if existing_services is None:
            raise RuntimeError("Cumulative build has no Existing_Services group.")
        axis05 = axis01_wvb._load_axis05()
        axis03 = axis05._load_axis03()
        axis02 = axis03._load_axis02()
        axis01 = axis02._load_axis01()
        axis07 = axis01._load_axis07()
        axis08 = axis07._load_axis08()
        zone_group = axis08._add_group(
            doc,
            existing_services,
            "Planned_Roof_Penetration_Zones",
            "Planned_Roof_Penetration_Zones",
            "USER_PROVIDED_APPROXIMATE_COORDINATES",
            "One non-cutting DN900 marker at the user-provided approximate X/Y location; roof-plane Z derives from the C4a crest envelope.",
        )
        axis08._add_property(zone_group, "App::PropertyString", "CatalogPath", str(CATALOG), "Build")
        axis08._add_property(zone_group, "App::PropertyString", "CatalogSHA256", hashlib.sha256(CATALOG.read_bytes()).hexdigest(), "Build")
        axis08._add_property(zone_group, "App::PropertyString", "ModelStatus", "COORDINATION_MARKER_NOT_APPROVED_CUTOUT", "Build")
        axis08._add_property(zone_group, "App::PropertyString", "ChangeSetJSON", json.dumps(catalog["change_visualisation"], sort_keys=True), "Display")
        shape, centre, normal = _marker_shape(App, Part, catalog, zone_definition)
        zone = doc.addObject("Part::Feature", zone_definition["id"])
        zone.Label = zone_definition["label"]
        zone.Shape = shape
        axis08._add_property(zone, "App::PropertyString", "StableComponentId", zone_definition["id"], "Source")
        axis08._add_property(zone, "App::PropertyString", "EvidenceStatus", "USER_PROVIDED_APPROXIMATE_COORDINATES", "Source")
        axis08._add_property(zone, "App::PropertyString", "EvidenceJSON", json.dumps(catalog["source"], sort_keys=True), "Source")
        axis08._add_property(zone, "App::PropertyLength", "NominalOpeningDiameter", zone_definition["nominal_opening_diameter_mm"], "Geometry")
        axis08._add_property(zone, "App::PropertyVector", "RequestedCentreXY", App.Vector(centre.x, centre.y, 0.0), "Geometry")
        axis08._add_property(zone, "App::PropertyVector", "CalculatedRoofCentre", centre, "Geometry")
        axis08._add_property(zone, "App::PropertyVector", "RoofPlaneNormal", normal, "Geometry")
        axis08._add_property(zone, "App::PropertyString", "GeometryStatus", zone_definition["geometry_status"], "Geometry")
        axis08._add_property(zone, "App::PropertyString", "PanelContainmentStatus", zone_definition["panel_containment_status"], "Geometry")
        axis08._add_property(zone, "App::PropertyString", "KnownBracingClearanceStatus", zone_definition["known_bracing_clearance_status"], "Geometry")
        axis08._add_property(zone, "App::PropertyString", "ExcludedDetail", zone_definition["excluded_detail"], "Geometry")
        axis08._add_property(zone, "App::PropertyString", "ChangeSet", catalog["change_visualisation"]["change_set"], "Display")
        axis08._add_property(zone, "App::PropertyString", "ChangeColourMeaning", catalog["change_visualisation"]["meaning"], "Display")
        _style_marker(zone, catalog)
        zone_group.addObject(zone)
        doc.recompute()
        audit_roof_penetration_zones(doc, catalog, axis01_wvb)
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
    build_roof_penetration_zones(ROOT / "outputs" / ("roof_penetration_zone_manual_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))