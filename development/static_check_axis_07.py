"""Integrity checks for approved axis-7 solids and source-mapped pending members."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_07_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["change_visualisation"] == {
        "change_set": "2026-09-07_axis07_ipe500_columns",
        "rgb": [0.1, 0.7, 0.85],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["rafter_change_visualisation"] == {
        "change_set": "2026-09-07_axis07_ipe450_rafters",
        "rgb": [0.2, 0.78, 0.24],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["ipe180_change_visualisation"] == {
        "change_set": "2026-09-08_axis07_ipe180_horizontals",
        "rgb": [0.88, 0.24, 0.25],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["hea200_change_visualisation"] == {
        "change_set": "2026-09-08_axis07_hea200_verticals",
        "rgb": [0.62, 0.28, 0.84],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["hea180_hea160_change_visualisation"] == {
        "change_set": "2026-09-08_axis07_hea180_hea160_horizontals",
        "rgb": [0.95, 0.72, 0.12],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    profile = catalog["nominal_profile_status"]["IPE500"]
    assert profile["source"] == "NEN-EN 10365:2017"
    assert profile["dimensions_mm"] == {
        "height_h": 500.0, "flange_width_b": 200.0, "web_thickness_tw": 10.2,
        "flange_thickness_tf": 16.0, "root_radius_r": 21.0,
    }
    rafter_profile = catalog["nominal_profile_status"]["IPE450"]
    assert rafter_profile["source"] == "NEN-EN 10365:2017"
    assert rafter_profile["dimensions_mm"] == {
        "height_h": 450.0, "flange_width_b": 190.0, "web_thickness_tw": 9.4,
        "flange_thickness_tf": 14.6, "root_radius_r": 21.0,
    }
    hea200 = catalog["nominal_profile_status"]["HEA200"]
    assert hea200["source"] == "NEN-EN 10365:2017"
    assert hea200["dimensions_mm"] == {
        "height_h": 190.0, "flange_width_b": 200.0, "web_thickness_tw": 6.5,
        "flange_thickness_tf": 10.0, "root_radius_r": 18.0,
    }
    assert hea200["section_orientation"] == "FLANGE_WIDTH_B_IN_A11_ELEVATION_PLANE"
    assert hea200["source_projected_in_plane_width_mm"] == 200.0
    hea180 = catalog["nominal_profile_status"]["HEA180"]
    assert hea180["source"] == "NEN-EN 10365:2017"
    assert hea180["dimensions_mm"] == {
        "height_h": 171.0, "flange_width_b": 180.0, "web_thickness_tw": 6.0,
        "flange_thickness_tf": 9.5, "root_radius_r": 15.0,
    }
    assert hea180["section_orientation"] == "FLANGE_WIDTH_B_OUT_OF_A11_ELEVATION_PLANE"
    assert hea180["source_projected_in_plane_height_mm"] == 171.0
    hea160 = catalog["nominal_profile_status"]["HEA160"]
    assert hea160["source"] == "NEN-EN 10365:2017"
    assert hea160["dimensions_mm"] == {
        "height_h": 152.0, "flange_width_b": 160.0, "web_thickness_tw": 6.0,
        "flange_thickness_tf": 9.0, "root_radius_r": 15.0,
    }
    assert hea160["section_orientation"] == "FLANGE_WIDTH_B_OUT_OF_A11_ELEVATION_PLANE"
    assert hea160["source_projected_in_plane_height_mm"] == 152.0
    members = catalog["approved_members"]
    ipe180_ids = {"A11_07_334", "A11_07_331", "A11_07_333", "A11_07_328", "A11_07_330", "A11_07_332"}
    hea200_ids = {"A11_07_326", "A11_07_321", "A11_07_317", "A11_07_320", "A11_07_325"}
    hea_horizontal_ids = {"A11_07_314", "A11_07_300"}
    expected_ids = {"A11_07_356", "A11_07_357", "A11_07_349", "A11_07_350"} | ipe180_ids | hea200_ids | hea_horizontal_ids
    assert {member["id"] for member in members} == expected_ids
    assert {member["profile_label"] for member in members} == {"IPE500-S355JR", "IPE450-S355JR", "IPE180", "HEA200", "HEA180-S355JR", "HEA160"}
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in members)
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == expected_ids
    for member_id in expected_ids:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[0] == 51100.0 and end[0] == 51100.0, member_id
        assert start != end, member_id
    assert axes["A11_07_349"]["end"][2] == axes["A11_07_350"]["start"][2]
    assert axes["A11_07_349"]["end"][1] < axes["A11_07_350"]["start"][1]
    ipe180 = catalog["nominal_profile_status"]["IPE180"]
    assert ipe180["source"] == "NEN-EN 10365:2017"
    assert ipe180["dimensions_mm"] == {
        "height_h": 180.0, "flange_width_b": 91.0, "web_thickness_tw": 5.3,
        "flange_thickness_tf": 8.0, "root_radius_r": 9.0,
    }
    for member_id in ipe180_ids:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[0] == 51100.0 and end[0] == 51100.0, member_id
        assert start[2] == 4370.00682 and end[2] == 4370.00682, member_id
        assert start[1] < end[1], member_id
    for member_id in hea200_ids:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[0] == 51100.0 and end[0] == 51100.0, member_id
        assert start[1] == end[1] and start[2] < end[2], member_id
    assert axes["A11_07_314"]["start"] == [51100.0, 8916.99560425, 7913.50745425]
    assert axes["A11_07_314"]["end"] == [51100.0, 13032.99631564, 7913.50745425]
    assert axes["A11_07_300"]["start"] == [51100.0, 18297.00012701, 4077.00662316]
    assert axes["A11_07_300"]["end"] == [51100.0, 27662.99378848, 4077.00662316]
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "7bda242a27ede07407efe873d35efd8be2a385d23002d690ead2caf21b857656"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "d09953da5f01a2c613cab92668485e9e148284c37925efec7b766c3fc20750ff"
    print(json.dumps({
        "status": "PASS_STATIC_AXIS07_ONLY",
        "members": len(members),
        "approved_ipe180_members": len(ipe180_ids),
        "approved_hea200_members": len(hea200_ids),
        "approved_horizontal_hea_members": len(hea_horizontal_ids),
        "source_view": catalog["source"]["view"],
        "nominal_profile_standards": {
            "IPE500": profile["source"], "IPE450": rafter_profile["source"], "IPE180": ipe180["source"], "HEA200": hea200["source"],
            "HEA180": hea180["source"], "HEA160": hea160["source"],
        },
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()