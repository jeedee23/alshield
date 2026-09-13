"""Static contract checks for four source-mapped A11/as-20 IPE500 solids."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("steel_catalog_axis_20_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"
SOURCE_A11 = ROOT.parent / "shared" / "sources" / "pdf" / "a11_ovz-b.pdf"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = {
        "A11_20_30": "IPE500-S355JR",
        "A11_20_29": "IPE500-S355JR",
        "A11_20_21": "IPE500-S355JR",
        "A11_20_25": "IPE500-S355JR",
    }
    assert catalog["schema"] == "allshield.steel-member-catalog.draft.v1"
    assert catalog["coordinate_system"] == {
        "units": "mm",
        "station_axis": "20",
        "client_x_mm": 5150.0,
        "section_span": "A-E",
        "reference_component_id": "Section_A11_Axis_20",
    }
    assert catalog["source"]["view"] == "AANZICHT as-20"
    projection = catalog["source"]["source_projection"]
    assert projection["component_id"] == "Section_A11_Axis_20"
    assert projection["calibration"] == {
        "source_x0_pt": 1252.18054,
        "source_z0_pt": 1413.625,
        "scale_mm_per_pt": 35.294279,
        "axis_registration_max_residual_mm": 0.002956,
    }
    assert {member["id"]: member["profile_label"] for member in catalog["approved_members"]} == expected
    assert all(member["geometry_status"] == "APPROVED_FOR_NOMINAL_COORDINATION_SOLID" for member in catalog["approved_members"])
    assert {member["source_mark"] for member in catalog["approved_members"]} == {"21", "25", "29", "30"}
    assert {tuple(member["direct_pdf_path_indices"]) for member in catalog["approved_members"]} == {
        (3341, 3342), (3343, 3344), (3348, 3349), (3350, 3351),
    }
    profile = catalog["nominal_profile_status"]["IPE500"]
    assert profile["dimensions_mm"] == {
        "height_h": 500.0,
        "flange_width_b": 200.0,
        "web_thickness_tw": 10.2,
        "flange_thickness_tf": 16.0,
        "root_radius_r": 21.0,
    }
    axes = catalog["centreline_definitions_mm"]
    assert axes["evidence_status"] == "VECTOR_MEASUREMENT"
    assert set(axes) - {"method", "evidence_status", "section_orientation"} == set(expected)
    assert all(axes[member_id]["start"][0] == 5150.0 and axes[member_id]["end"][0] == 5150.0 for member_id in expected)
    assert axes["A11_20_30"]["start"] == [5150.0, 249.998147, -162.01246]
    assert axes["A11_20_29"]["end"] == [5150.0, 27579.9995045, 9166.357701]
    assert axes["A11_20_21"]["end"][1] < axes["A11_20_25"]["start"][1]
    assert axes["A11_20_21"]["end"][2] == axes["A11_20_25"]["start"][2]
    assert hashlib.sha256(SOURCE_A11.read_bytes()).hexdigest() == "377a91cdfd02d63ae0a422e9eabf5369dcaca4e61a740a9b6050c1e3497303b4"
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({
        "status": "PASS_STATIC_AXIS20_ONLY",
        "members": len(expected),
        "approved_ipe500": len(expected),
        "source_projection": "Section_A11_Axis_20",
        "secondary_steel_excluded": True,
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()