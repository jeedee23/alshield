"""Verify STEP geometry against optional Fusion-exported component properties.

Run with FreeCADCmd. The STEP geometry is measured independently; labels are
only claims that receive a separate bounding-box plausibility check.

Example:
    FreeCADCmd.exe verify_step_bom.py -- --step "assembly.stp" --report "report.json"
"""

from __future__ import print_function

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import FreeCAD as App
import Import


DEFAULT_TOLERANCE_MM = 2.0


def normalize(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _number_or_none(value):
    if value in (None, ""):
        return None
    return float(value)


def read_fusion_components(json_path, tsv_path):
    if json_path is None and tsv_path is None:
        return []
    if json_path is not None:
        payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        components = payload.get("components")
        if not isinstance(components, list):
            raise ValueError("Fusion JSON must be a list or contain a components list.")
        return components
    with Path(tsv_path).open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    components = []
    for row in rows:
        if row.get("validation_status") == "ROOT_ASSEMBLY":
            continue
        bbox_values = [_number_or_none(row.get(key)) for key in ("bbox_x_mm", "bbox_y_mm", "bbox_z_mm")]
        components.append({
            "step_object": row.get("body_name", ""),
            "fusion_name": row.get("component_name", ""),
            "name": row.get("component_name", ""),
            "bbox_mm": bbox_values if all(value is not None for value in bbox_values) else None,
            "area_mm2": _number_or_none(row.get("surface_area_mm2")),
            "volume_mm3": _number_or_none(row.get("volume_mm3")),
            "mass_kg": _number_or_none(row.get("mass_kg")),
            "material": row.get("material_name", ""),
            "fusion_validation_status": row.get("validation_status", ""),
            "fusion_validation_details": row.get("validation_details", ""),
            "fusion_component_classification": row.get("component_classification", ""),
            "fusion_tm_bom_scope": row.get("tm_bom_scope", ""),
        })
    return components


def find_fusion_component(object_name, object_label, components):
    step_keys = {normalize(object_name), normalize(object_label)}
    for component in components:
        candidates = {
            normalize(component.get("step_object", "")),
            normalize(component.get("fusion_name", "")),
            normalize(component.get("name", "")),
        }
        candidates.discard("")
        if step_keys & candidates:
            return component
    return None


def bbox_values(shape):
    bounds = shape.BoundBox
    dimensions = [bounds.XLength, bounds.YLength, bounds.ZLength]
    return {
        "x_mm": round(bounds.XLength, 3),
        "y_mm": round(bounds.YLength, 3),
        "z_mm": round(bounds.ZLength, 3),
        "sorted_mm": [round(value, 3) for value in sorted(dimensions)],
    }


def extract_name_claims(label):
    claims = []
    for match in re.finditer(r"(?:\bID|\bDN|\bOD|[\u00d8\u2300]|(?<=\d)D)\s*([0-9]+(?:[.,][0-9]+)?)", label, re.I):
        claims.append({"kind": "diameter_mm", "value_mm": float(match.group(1).replace(",", "."))})
    for match in re.finditer(r"\btube\s+([0-9]+(?:[.,][0-9]+)?)", label, re.I):
        claims.append({"kind": "diameter_mm", "value_mm": float(match.group(1).replace(",", "."))})
    for match in re.finditer(r"\bL\s*=?\s*([0-9]+(?:[.,][0-9]+)?)", label, re.I):
        claims.append({"kind": "length_mm", "value_mm": float(match.group(1).replace(",", "."))})
    for match in re.finditer(r"\b([0-9]+(?:[.,][0-9]+)?)\s*[xX]\s*([0-9]+(?:[.,][0-9]+)?)", label):
        claims.append({
            "kind": "rectangular_size_mm",
            "value_mm": [
                float(match.group(1).replace(",", ".")),
                float(match.group(2).replace(",", ".")),
            ],
        })
    for match in re.finditer(r"([0-9]+(?:[.,][0-9]+)?)\s*(?:\u00b0|gr(?:aden)?)", label, re.I):
        claims.append({"kind": "angle_degrees", "value": float(match.group(1).replace(",", "."))})
    for match in re.finditer(r"\bR\s*=\s*([0-9]+(?:[.,][0-9]+)?)(D)?", label, re.I):
        claims.append({
            "kind": "radius",
            "value": float(match.group(1).replace(",", ".")),
            "unit": "diameter_multiplier" if match.group(2) else "mm",
        })
    return claims


def name_claim_checks(label, bbox, tolerance_mm):
    dimensions = bbox["sorted_mm"]
    checks = []
    for claim in extract_name_claims(label):
        if claim["kind"] in ("angle_degrees", "radius"):
            checks.append({
                "claim": claim,
                "method": "not measurable from a bounding box",
                "result": "NOT_CHECKABLE_FROM_BBOX",
                "measured_bbox_mm": None,
            })
            continue
        if claim["kind"] == "length_mm":
            measured = max(dimensions)
            matches = abs(measured - claim["value_mm"]) <= tolerance_mm
            method = "largest bounding-box dimension"
        elif claim["kind"] == "diameter_mm":
            measured = [value for value in dimensions if abs(value - claim["value_mm"]) <= tolerance_mm]
            matches = bool(measured)
            method = "any bounding-box dimension"
        else:
            values = claim["value_mm"]
            measured = dimensions
            matches = all(any(abs(actual - expected) <= tolerance_mm for actual in dimensions) for expected in values)
            method = "any two bounding-box dimensions"
        checks.append({
            "claim": claim,
            "method": method,
            "result": "PLAUSIBLE" if matches else "NO_BBOX_MATCH",
            "measured_bbox_mm": measured,
        })
    return checks


def expected_bbox_check(expected, actual, tolerance_mm):
    expected_bbox = expected.get("bbox_mm")
    if expected_bbox is None:
        return None
    if not isinstance(expected_bbox, list) or len(expected_bbox) != 3:
        return {"result": "INVALID_FUSION_INPUT", "expected_bbox_mm": expected_bbox}
    expected_sorted = sorted(float(value) for value in expected_bbox)
    actual_sorted = actual["sorted_mm"]
    deltas = [round(actual_value - expected_value, 3) for actual_value, expected_value in zip(actual_sorted, expected_sorted)]
    return {
        "result": "MATCH" if all(abs(value) <= tolerance_mm for value in deltas) else "MISMATCH",
        "expected_bbox_mm": [round(value, 3) for value in expected_sorted],
        "actual_bbox_mm": actual_sorted,
        "delta_mm": deltas,
        "tolerance_mm": tolerance_mm,
    }


def component_report(obj, fusion_components, tolerance_mm):
    shape = obj.Shape
    bbox = bbox_values(shape)
    raw_area_mm2 = round(shape.Area, 3)
    volume_mm3 = round(shape.Volume, 3)
    fusion = find_fusion_component(obj.Name, obj.Label, fusion_components)
    fusion_result = None
    if fusion is not None:
        fusion_result = {
            "fusion_name": fusion.get("fusion_name", fusion.get("name", "")),
            "fusion_area_mm2": fusion.get("area_mm2"),
            "step_raw_area_mm2": raw_area_mm2,
            "fusion_area_delta_mm2": (
                round(raw_area_mm2 - float(fusion["area_mm2"]), 3)
                if fusion.get("area_mm2") is not None
                else None
            ),
            "fusion_volume_mm3": fusion.get("volume_mm3"),
            "step_volume_mm3": volume_mm3,
            "fusion_volume_delta_mm3": (
                round(volume_mm3 - float(fusion["volume_mm3"]), 3)
                if fusion.get("volume_mm3") is not None
                else None
            ),
            "fusion_mass_kg": fusion.get("mass_kg"),
            "fusion_material": fusion.get("material"),
            "fusion_validation_status": fusion.get("fusion_validation_status"),
            "fusion_validation_details": fusion.get("fusion_validation_details"),
            "fusion_component_classification": fusion.get("fusion_component_classification"),
            "fusion_tm_bom_scope": fusion.get("fusion_tm_bom_scope"),
            "bbox_check": expected_bbox_check(fusion, bbox, tolerance_mm),
        }
    return {
        "step_object_name": obj.Name,
        "step_label": obj.Label,
        "object_type": obj.TypeId,
        "bbox_mm": bbox,
        "raw_step_area_mm2": raw_area_mm2,
        "step_volume_mm3": volume_mm3,
        "face_count": len(shape.Faces),
        "solid_count": len(shape.Solids),
        "name_claim_bbox_checks": name_claim_checks(obj.Label, bbox, tolerance_mm),
        "fusion_comparison": fusion_result,
    }


def parse_arguments():
    parser = argparse.ArgumentParser(description="Inspect STEP geometry and compare optional Fusion properties.")
    parser.add_argument("--step", required=True, help="Released STEP subassembly or assembly file.")
    fusion_group = parser.add_mutually_exclusive_group()
    fusion_group.add_argument("--fusion-json", help="Optional Fusion component-properties JSON export.")
    fusion_group.add_argument("--fusion-tsv", help="TSV written by fusion_export_active_f3d.py.")
    parser.add_argument("--report", required=True, help="JSON report path below allshield_AHU outputs.")
    parser.add_argument("--tolerance-mm", type=float, default=DEFAULT_TOLERANCE_MM)
    return parser.parse_args(sys.argv[1:])


def main():
    arguments = parse_arguments()
    step_path = Path(arguments.step).resolve()
    report_path = Path(arguments.report).resolve()
    if not step_path.is_file():
        raise FileNotFoundError("STEP file does not exist: {0}".format(step_path))
    if arguments.tolerance_mm < 0:
        raise ValueError("--tolerance-mm must be zero or greater.")

    fusion_components = read_fusion_components(arguments.fusion_json, arguments.fusion_tsv)
    document = App.newDocument("StepBomVerification")
    try:
        Import.insert(str(step_path), document.Name)
        document.recompute()
        shaped_objects = [
            obj for obj in document.Objects
            if hasattr(obj, "Shape")
            and not obj.Shape.isNull()
            and len(obj.Shape.Solids) > 0
            and not hasattr(obj, "Group")
        ]
        if not shaped_objects:
            raise RuntimeError("STEP import produced no visible shape objects.")
        components = [component_report(obj, fusion_components, arguments.tolerance_mm) for obj in shaped_objects]
        report = {
            "schema": "allshield.ahu.step-bom-verification.v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "step_file": str(step_path),
            "fusion_properties_file": str(Path(arguments.fusion_json).resolve()) if arguments.fusion_json else None,
            "fusion_tsv_file": str(Path(arguments.fusion_tsv).resolve()) if arguments.fusion_tsv else None,
            "tolerance_mm": arguments.tolerance_mm,
            "component_count": len(components),
            "components": components,
            "pricing_status": "RAW_CAD_AREA_ONLY_NOT_A_LUKANORM_PRICE_SURFACE",
            "limitations": [
                "STEP labels are checked only as claims against a bounding-box screen.",
                "A bounding box cannot certify developed length, bend radius, port face, flange geometry or sheet thickness.",
                "Raw CAD area includes all imported faces and must not be used directly as the TM Technics price surface.",
                "Weight needs an explicit Fusion material/density input; no density is inferred from STEP geometry.",
            ],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({
            "status": "PASS_STEP_GEOMETRY_EXTRACTED",
            "report": str(report_path),
            "component_count": len(components),
            "fusion_components_matched": sum(item["fusion_comparison"] is not None for item in components),
        }, indent=2))
    finally:
        App.closeDocument(document.Name)


if __name__ == "__main__":
    main()