"""Integrity checks for approved A11/as-2 nominal HEA solids."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_02_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["coordinate_system"] == {
        "units": "mm",
        "station_axis": "2",
        "client_x_mm": 61050.0,
        "section_span": "C-E",
        "reference_component_id": None,
    }
    assert catalog["change_visualisation"] == {
        "change_set": "2026-09-08_axis02_hea_members",
        "rgb": [0.95, 0.58, 0.15],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["source"]["view"] == "AANZICHT as-2"
    assert catalog["source"]["drawing_status"] == "TER CONTROLE"
    assert catalog["source"]["source_projection"] == {
        "component_id": None,
        "status": "SOURCE_PROJECTION_NOT_YET_REPRESENTED_IN_BASELINE",
        "path_indices": [804, 805, 806, 807, 808, 809, 840, 841],
    }
    profiles = catalog["nominal_profile_status"]
    assert profiles["HEA180"]["source"] == "NEN-EN 10365:2017"
    assert profiles["HEA180"]["dimensions_mm"] == {
        "height_h": 171.0, "flange_width_b": 180.0, "web_thickness_tw": 6.0,
        "flange_thickness_tf": 9.5, "root_radius_r": 15.0,
    }
    assert profiles["HEA180"]["section_orientation"] == "FLANGE_WIDTH_B_IN_A11_ELEVATION_PLANE"
    assert profiles["HEA180"]["source_projected_in_plane_width_mm"] == 180.0
    assert profiles["HEA160"]["source"] == "NEN-EN 10365:2017"
    assert profiles["HEA160"]["dimensions_mm"] == {
        "height_h": 152.0, "flange_width_b": 160.0, "web_thickness_tw": 6.0,
        "flange_thickness_tf": 9.0, "root_radius_r": 15.0,
    }
    assert profiles["HEA160"]["section_orientation"] == "SECTION_HEIGHT_H_IN_A11_ELEVATION_PLANE"
    assert profiles["HEA160"]["source_projected_in_plane_height_mm"] == 152.0
    members = catalog["approved_members"]
    expected_profiles = {
        "A11_02_313": "HEA180",
        "A11_02_311": "HEA180",
        "A11_02_312": "HEA180",
        "A11_02_301": "HEA160",
    }
    assert {member["id"]: member["profile_label"] for member in members} == expected_profiles
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in members)
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == set(expected_profiles)
    for member_id in expected_profiles:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[0] == 61050.0 and end[0] == 61050.0, member_id
        assert start != end, member_id
    for member_id in {"A11_02_313", "A11_02_311", "A11_02_312"}:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[1] == end[1] and start[2] < end[2], member_id
    assert axes["A11_02_301"]["start"] == [61050.0, 18367.0, 4076.6]
    assert axes["A11_02_301"]["end"] == [61050.0, 27633.0, 4076.6]
    assert "No A11/as-2' member is included because its longitudinal station remains unresolved." in catalog["explicitly_not_inferred"]
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({
        "status": "PASS_STATIC_AXIS02_ONLY",
        "members": len(members),
        "approved_hea180_columns": 3,
        "approved_hea160_horizontal": 1,
        "source_view": catalog["source"]["view"],
        "nominal_profile_standards": {key: profiles[key]["source"] for key in ("HEA180", "HEA160")},
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()