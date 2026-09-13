"""Integrity checks for approved A11/as-5 primary solids."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_05_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_05_358": "IPE500-S355JR", "A11_05_353": "IPE500-S355JR",
        "A11_05_316": "HEA200", "A11_05_319": "HEA200",
        "A11_05_347": "IPE450-S355JR", "A11_05_348": "IPE450-S355JR",
    }
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["coordinate_system"] == {"units": "mm", "station_axis": "5", "client_x_mm": 53750.0, "section_span": "A-E", "reference_component_id": "Section_A11_Axis_5"}
    assert catalog["source"]["view"] == "AANZICHT as-5"
    projection = catalog["source"]["source_projection"]
    assert projection["component_id"] == "Section_A11_Axis_5"
    assert projection["direct_pdf_rafter_path_indices"] == [1843, 1844, 1845, 1846]
    assert projection["transform"] == {"source_x0_pt": 139.28027, "source_z0_pt": 1918.103, "scale_mm_per_pt": 35.294279, "axis_registration_max_residual_mm": 0.001632}
    assert {member["id"]: member["profile_label"] for member in catalog["approved_members"]} == expected
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in catalog["approved_members"])
    profiles = catalog["nominal_profile_status"]
    assert profiles["IPE500"]["dimensions_mm"] == {"height_h": 500.0, "flange_width_b": 200.0, "web_thickness_tw": 10.2, "flange_thickness_tf": 16.0, "root_radius_r": 21.0}
    assert profiles["HEA200"]["dimensions_mm"] == {"height_h": 190.0, "flange_width_b": 200.0, "web_thickness_tw": 6.5, "flange_thickness_tf": 10.0, "root_radius_r": 18.0}
    assert profiles["IPE450"]["dimensions_mm"] == {"height_h": 450.0, "flange_width_b": 190.0, "web_thickness_tw": 9.4, "flange_thickness_tf": 14.6, "root_radius_r": 21.0}
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == set(expected)
    assert all(axes[member_id]["start"][0] == 53750.0 and axes[member_id]["end"][0] == 53750.0 for member_id in expected)
    assert axes["A11_05_358"]["start"] == [53750.0, 250.0005465, 3615.00006]
    assert axes["A11_05_358"]["end"][2] == 9166.3675075
    assert axes["A11_05_347"]["end"][1] < axes["A11_05_348"]["start"][1]
    assert axes["A11_05_347"]["end"][2] == axes["A11_05_348"]["start"][2]
    assert "member 374" in catalog["explicitly_not_inferred"][0]
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({"status": "PASS_STATIC_AXIS05_ONLY", "members": len(expected), "approved_ipe500": 2, "approved_hea200": 2, "approved_ipe450": 2, "secondary_member_374_excluded": True, "baseline_json_unchanged": True, "baseline_generator_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()