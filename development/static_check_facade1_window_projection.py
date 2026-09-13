"""Static contract checks for the Facade_1 C4a planar window-bank projection."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("facade1_window_projection_catalog_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"
SOURCE_C4A = ROOT / "sources" / "pdf" / "c04a_gevels.pdf"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema"] == "allshield.facade-window-projection-catalog.draft.v1"
    assert catalog["source"]["file"] == "sources/pdf/c04a_gevels.pdf"
    assert catalog["source"]["calibration"]["mm_per_pdf_point"] == 35.294277268675316
    assert catalog["source"]["photo_evidence"]["status"] == "PHYSICAL_FRAME_LAYERS_VISIBLE_BUT_LOCATION_CORRESPONDENCE_UNRESOLVED"
    assert len(catalog["window_banks"]) == 1
    bank = catalog["window_banks"][0]
    assert bank["id"] == "Facade1_C4a_WindowBank_01"
    assert bank["geometry_status"] == "PLANAR_SOURCE_PROJECTION_NO_PHYSICAL_DEPTH"
    assert bank["world_plane_x_mm"] == 65260.0
    assert bank["source_path_indices"] == {"outer_perimeter": [322, 323, 324, 325], "mullions": [327, 329], "transoms": [326, 328, 330], "glazing": [597, 598, 599, 600, 601, 602]}
    assert bank["outer_bounds_yz_mm"] == {"y_min": 33755.0, "y_max": 36845.0, "z_min": 4482.0, "z_max": 6930.0}
    assert bank["directly_measured_projection_dimensions_mm"] == {"outer_width_y": 3090.0, "outer_height_z": 2448.0, "glazing_light_width_y": 910.0, "upper_glazing_height_z": 1472.0, "lower_glazing_height_z": 735.0, "vertical_mullion_projection_width_y": 94.0, "horizontal_transom_projection_height_z": 94.0}
    assert bank["baseline_glazing_component_ids"] == ["Facade_1_Glass_Projection_26", "Facade_1_Glass_Projection_27", "Facade_1_Glass_Projection_28", "Facade_1_Glass_Projection_29", "Facade_1_Glass_Projection_30", "Facade_1_Glass_Projection_31"]
    assert len(bank["projection_regions_yz_mm"]["outer_frame"]) == 4
    assert len(bank["projection_regions_yz_mm"]["mullions"]) == 2
    assert len(bank["projection_regions_yz_mm"]["transoms"]) == 3
    assert "No physical frame section" in bank["excluded_detail"]
    assert hashlib.sha256(SOURCE_C4A.read_bytes()).hexdigest() == "1f4af215ff58087125339029a950113a4cda1819f6a5c2bebd53a6422df37fa0"
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({
        "status": "PASS_STATIC_FACADE1_WINDOW_PROJECTION_ONLY",
        "window_banks": 1,
        "projection_objects": 2,
        "physical_window_frame_created": False,
        "inner_or_street_side_frame_depth_verified": False,
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()