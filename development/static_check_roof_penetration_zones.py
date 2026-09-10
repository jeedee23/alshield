"""Static contract checks for the non-cutting DN900 roof-penetration marker."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("roof_penetration_zone_catalog_draft.json")
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
BASE_GENERATOR = ROOT / "model" / "allshield_build.py"


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert catalog["schema"] == "allshield.roof-penetration-zone-catalog.draft.v1"
    assert catalog["scope"].startswith("One non-cutting")
    assert catalog["change_visualisation"] == {
        "change_set": "2026-09-09_dn900_roof_penetration_zone",
        "rgb": [1.0, 0.72, 0.0],
        "transparency_percent": 70,
        "meaning": "Display-only warning marker for an unresolved planned roof penetration. It is not physical roof material or a construction-status claim.",
    }
    roof = catalog["source"]["roof_datum"]
    assert roof["file"] == "sources/pdf/c04a_gevels.pdf"
    assert roof["baseline_component_id"] == "SteelDeck_Envelope_A_to_Ridge1"
    assert roof["crest_plane_corners_mm"] == [
        [-100.0, -100.0, 9544.610133],
        [65260.0, -100.0, 9544.610133],
        [65260.0, 13915.0, 10300.0],
        [-100.0, 13915.0, 10300.0],
    ]
    assert catalog["source"]["planned_location"]["evidence_type"] == "USER_PROVIDED_APPROXIMATE_COORDINATES"
    assert catalog["source"]["planned_location"]["coordinate_accuracy_mm"] is None
    assert len(catalog["zones"]) == 1
    zone = catalog["zones"][0]
    assert zone["id"] == "Planned_Roof_Penetration_DN900_01"
    assert zone["nominal_opening_diameter_mm"] == 900.0
    assert zone["requested_centre_xy_mm"] == [10000.0, 8000.0]
    assert zone["location_status"] == "USER_PROVIDED_APPROXIMATE"
    assert zone["geometry_status"] == "COORDINATION_MARKER_ONLY_DO_NOT_CUT_ROOF"
    assert zone["panel_containment_status"] == "UNVERIFIED_PANEL_JOINT_PHASE_UNKNOWN"
    assert zone["known_bracing_clearance_status"] == "CHECK_ONLY_AGAINST_CURRENTLY_MODELLED_A11_AXIS01_WVB_BARS"
    assert hashlib.sha256(BASE_DATA.read_bytes()).hexdigest() == "3805f4a178ccbb8b2103850b47c28014763526177b6cda42ba2926d766b58745"
    assert hashlib.sha256(BASE_GENERATOR.read_bytes()).hexdigest() == "ce76b7b36c347cf5022b06441bf05e85682fca7f409082d9093cf07541eb7c1e"
    print(json.dumps({
        "status": "PASS_STATIC_ROOF_PENETRATION_ZONE_ONLY",
        "zones": 1,
        "nominal_opening_diameter_mm": zone["nominal_opening_diameter_mm"],
        "physical_roof_cutout_created": False,
        "panel_containment_verified": False,
        "baseline_json_unchanged": True,
        "baseline_generator_unchanged": True,
    }, indent=2))


if __name__ == "__main__":
    main()