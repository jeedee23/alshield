"""Integrity checks for the six approved A11/as-1 WVB brace-bar solids."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_01_wvb_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_01_WVB400": "WVB100*7",
        "A11_01_WVB401_ASC": "WVB100*7",
        "A11_01_WVB401_DESC": "WVB100*7",
        "A11_01_WVB402": "WVB100*7",
        "A11_01_WVB399": "WVB100*7",
        "A11_01_WVB403": "WVB100*7",
    }
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["coordinate_system"] == {"units": "mm", "station_axis": "1", "client_x_mm": 65160.0, "section_span": "A-D", "reference_component_id": "Section_A11_Axis_1"}
    assert catalog["source"]["view"] == "AANZICHT as-1"
    projection = catalog["source"]["source_projection"]
    assert projection["component_id"] == "Section_A11_Axis_1"
    assert projection["calibration"] == {"source_x0_pt": 139.28027, "source_z0_pt": 1918.103, "scale_mm_per_pt": 35.294279, "axis_registration_max_residual_mm": 0.001632}
    assert {member["id"]: member["profile_label"] for member in catalog["approved_members"]} == expected
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in catalog["approved_members"])
    assert {member["source_mark"] for member in catalog["approved_members"]} == {"399", "400", "401", "402", "403"}
    assert sum(member["source_mark"] == "401" for member in catalog["approved_members"]) == 2
    assert catalog["nominal_profile_status"]["WVB100*7"]["dimensions_mm"] == {"width_in_A11_elevation_plane": 100.0, "thickness_out_of_A11_elevation_plane": 7.0}
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == set(expected)
    assert all(axes[member_id]["start"][0] == 65160.0 and axes[member_id]["end"][0] == 65160.0 for member_id in expected)
    assert axes["A11_01_WVB400"]["start"] == [65160.0, 262.85674, -105.1428545]
    assert axes["A11_01_WVB401_ASC"]["end"] == [65160.0, 8660.5571185, 6888.0159525]
    assert axes["A11_01_WVB401_DESC"]["start"][2] > axes["A11_01_WVB401_DESC"]["end"][2]
    assert axes["A11_01_WVB402"]["end"][2] > axes["A11_01_WVB402"]["start"][2]
    assert axes["A11_01_WVB399"]["end"] == [65160.0, 13067.046609, -101.089743]
    assert all(member["endpoint_outline_half_width_max_mm"] > 0 for member in catalog["approved_members"])
    assert "No unobserved counterpart" in catalog["explicitly_not_inferred"][1]
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({"status": "PASS_STATIC_AXIS01_WVB_ONLY", "members": len(expected), "physical_wvb_bars": 6, "repeated_source_mark_401_is_two_drawn_bars": True, "baseline_json_unchanged": True, "baseline_generator_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()