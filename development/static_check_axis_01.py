"""Integrity checks for approved A11/as-1 main-profile solids."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_01_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["coordinate_system"] == {
        "units": "mm",
        "station_axis": "1",
        "client_x_mm": 65160.0,
        "section_span": "A-E",
        "reference_component_id": "Section_A11_Axis_1",
    }
    assert catalog["change_visualisation"] == {
        "change_set": "2026-09-08_axis01_main_profiles",
        "rgb": [0.94, 0.25, 0.55],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["source"]["view"] == "AANZICHT as-1"
    assert catalog["source"]["drawing_status"] == "TER CONTROLE"
    assert catalog["source"]["source_projection"] == {
        "component_id": "Section_A11_Axis_1",
        "status": "SOURCE_PROJECTION_NOT_SOLID",
        "path_indices": [161, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 210, 211, 212, 213],
    }
    profiles = catalog["nominal_profile_status"]
    assert profiles["HEA200"]["source"] == "NEN-EN 10365:2017"
    assert profiles["HEA200"]["dimensions_mm"] == {
        "height_h": 190.0, "flange_width_b": 200.0, "web_thickness_tw": 6.5,
        "flange_thickness_tf": 10.0, "root_radius_r": 18.0,
    }
    assert profiles["HEA200"]["section_orientation"] == "SECTION_HEIGHT_H_IN_A11_ELEVATION_PLANE"
    assert profiles["HEA200"]["source_projected_in_plane_height_mm"] == 190.0
    assert profiles["IPE300"]["source"] == "NEN-EN 10365:2017"
    assert profiles["IPE300"]["dimensions_mm"] == {
        "height_h": 300.0, "flange_width_b": 150.0, "web_thickness_tw": 7.1,
        "flange_thickness_tf": 10.7, "root_radius_r": 15.0,
    }
    assert profiles["IPE300"]["section_orientation"] == "FLANGE_WIDTH_B_IN_A11_ELEVATION_PLANE"
    assert profiles["IPE300"]["source_projected_in_plane_width_mm"] == 150.0
    assert profiles["HEA180"]["source"] == "NEN-EN 10365:2017"
    assert profiles["HEA180"]["dimensions_mm"] == {
        "height_h": 171.0, "flange_width_b": 180.0, "web_thickness_tw": 6.0,
        "flange_thickness_tf": 9.5, "root_radius_r": 15.0,
    }
    assert profiles["HEA180"]["section_orientation"] == "SECTION_HEIGHT_H_IN_A11_ELEVATION_PLANE"
    assert profiles["HEA180"]["source_projected_in_plane_height_mm"] == 171.245311
    members = catalog["approved_members"]
    expected_profiles = {
        "A11_01_324": "HEA200", "A11_01_323": "HEA200",
        "A11_01_341": "IPE300", "A11_01_339": "IPE300", "A11_01_337": "IPE300",
        "A11_01_338": "IPE300", "A11_01_340": "IPE300",
        "A11_01_302": "HEA180", "A11_01_303": "HEA180",
    }
    assert {member["id"]: member["profile_label"] for member in members} == expected_profiles
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in members)
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == set(expected_profiles)
    for member_id in expected_profiles:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[0] == 65160.0 and end[0] == 65160.0, member_id
        assert start != end, member_id
    for member_id in {"A11_01_324", "A11_01_323", "A11_01_341", "A11_01_339", "A11_01_337", "A11_01_338", "A11_01_340"}:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[1] == end[1] and start[2] < end[2], member_id
    assert axes["A11_01_302"]["start"] == [65160.0, 202.998217, 9090.2546905]
    assert axes["A11_01_302"]["end"] == [65160.0, 13902.997911, 9823.7440215]
    assert axes["A11_01_303"]["start"] == [65160.0, 13926.999915, 9823.7440215]
    assert axes["A11_01_303"]["end"] == [65160.0, 27626.999609, 9090.2546905]
    assert axes["A11_01_302"]["end"][1] < axes["A11_01_303"]["start"][1]
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "7bda242a27ede07407efe873d35efd8be2a385d23002d690ead2caf21b857656"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "d09953da5f01a2c613cab92668485e9e148284c37925efec7b766c3fc20750ff"
    print(json.dumps({
        "status": "PASS_STATIC_AXIS01_ONLY",
        "members": len(members),
        "approved_hea200_columns": 2,
        "approved_ipe300_columns": 5,
        "approved_hea180_rafters": 2,
        "source_view": catalog["source"]["view"],
        "nominal_profile_standards": {key: profiles[key]["source"] for key in ("HEA200", "IPE300", "HEA180")},
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()