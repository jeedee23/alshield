"""Integrity checks for approved A11/as-3 primary solids."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_03_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_03_354": "IPE500-S355JR", "A11_03_355": "IPE500-S355JR",
        "A11_03_318": "HEA200", "A11_03_322": "HEA200",
        "A11_03_352": "IPE500-S355JR", "A11_03_351": "IPE500-S355JR",
    }
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["coordinate_system"] == {"units": "mm", "station_axis": "3", "client_x_mm": 59100.0, "section_span": "A-E", "reference_component_id": "Section_A11_Axis_3"}
    assert catalog["source"]["view"] == "AANZICHT as-3"
    assert catalog["source"]["source_projection"] == {"component_id": "Section_A11_Axis_3", "status": "SOURCE_PROJECTION_NOT_SOLID", "path_indices": [1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1210, 1211, 1212]}
    assert {member["id"]: member["profile_label"] for member in catalog["approved_members"]} == expected
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in catalog["approved_members"])
    profiles = catalog["nominal_profile_status"]
    assert profiles["IPE500"]["source"] == "NEN-EN 10365:2017"
    assert profiles["IPE500"]["dimensions_mm"] == {"height_h": 500.0, "flange_width_b": 200.0, "web_thickness_tw": 10.2, "flange_thickness_tf": 16.0, "root_radius_r": 21.0}
    assert profiles["HEA200"]["dimensions_mm"] == {"height_h": 190.0, "flange_width_b": 200.0, "web_thickness_tw": 6.5, "flange_thickness_tf": 10.0, "root_radius_r": 18.0}
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == set(expected)
    assert all(axes[member_id]["start"][0] == 59100.0 and axes[member_id]["end"][0] == 59100.0 for member_id in expected)
    assert axes["A11_03_352"]["end"][1] < axes["A11_03_351"]["start"][1]
    assert "member 372" in catalog["explicitly_not_inferred"][0]
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({"status": "PASS_STATIC_AXIS03_ONLY", "members": len(expected), "approved_ipe500": 4, "approved_hea200": 2, "baseline_json_unchanged": True, "baseline_generator_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()