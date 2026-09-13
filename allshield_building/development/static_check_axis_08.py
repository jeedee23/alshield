"""Standard-Python integrity checks for the approved A11 axis-8 extension."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_08_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["change_visualisation"] == {
        "change_set": "2026-09-07_axis08_nominal_ipe",
        "rgb": [0.95, 0.55, 0.12],
        "meaning": "Display-only identification of this development change set. It does not describe steel paint, coating, material, construction status or source confidence.",
    }
    assert catalog["nominal_profile_source"]["standard"] == "NEN-EN 10365:2017"
    assert catalog["nominal_profile_source"]["profiles_mm"] == {
        "IPE500": {"height_h": 500.0, "flange_width_b": 200.0, "web_thickness_tw": 10.2,
                   "flange_thickness_tf": 16.0, "root_radius_r": 21.0},
        "IPE180": {"height_h": 180.0, "flange_width_b": 91.0, "web_thickness_tw": 5.3,
                   "flange_thickness_tf": 8.0, "root_radius_r": 9.0},
    }
    expected_ids = {"A11_08_211", "A11_08_216", "A11_08_221", "A11_08_223", "A11_08_504_A", "A11_08_504_E"}
    members = catalog["confirmed_members"]
    assert {member["id"] for member in members} == expected_ids
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in members)
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == expected_ids
    for member_id in expected_ids:
        start, end = axes[member_id]["start"], axes[member_id]["end"]
        assert start[0] == 45950.0 and end[0] == 45950.0, member_id
        assert start != end, member_id
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "7bda242a27ede07407efe873d35efd8be2a385d23002d690ead2caf21b857656"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "d09953da5f01a2c613cab92668485e9e148284c37925efec7b766c3fc20750ff"
    print(json.dumps({
        "status": "PASS_STATIC_AXIS08_ONLY",
        "members": len(members),
        "source_view": catalog["source"]["view"],
        "nominal_profile_standard": catalog["nominal_profile_source"]["standard"],
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()