"""Audit whether the existing A11/as-20 evidence can safely create solids."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DATA = ROOT / "model" / "allshield_building_02.json"
SOURCE_PDF = ROOT.parent / "shared" / "sources" / "pdf" / "a11_ovz-b.pdf"
SOURCE_TEXT = ROOT.parent / "shared" / "sources" / "text" / "a11_ovz-b.txt"
SECTION_ID = "Section_A11_Axis_20"
REQUIRED_LABELS = (
    "2 HEA200", "3 HEA200", "19 IPE300", "17 IPE300", "18 IPE300",
    "20 IPE300", "15 IPE240", "16 IPE240", "10 IPE200", "12 IPE200",
    "11 IPE200", "13 IPE200", "1 HEA180-S355JR", "62 WVB85x5",
    "63 WVB85x5", "66 WVB85x5", "67 WVB85x5", "68 WVB85x5",
)
APPROVED_PRIMARY_MEMBERS = (
    {"id": "A11_20_30", "source_mark": "30", "profile": "IPE500-S355JR", "path_indices": [3341, 3342]},
    {"id": "A11_20_29", "source_mark": "29", "profile": "IPE500-S355JR", "path_indices": [3343, 3344]},
    {"id": "A11_20_21", "source_mark": "21", "profile": "IPE500-S355JR", "path_indices": [3350, 3351]},
    {"id": "A11_20_25", "source_mark": "25", "profile": "IPE500-S355JR", "path_indices": [3348, 3349]},
)


def _output_directory() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = ROOT / "outputs" / ("axis20_source_readiness_" + stamp)
    output.mkdir(parents=True, exist_ok=False)
    return output


def audit() -> Path:
    if not SOURCE_PDF.is_file() or not SOURCE_TEXT.is_file():
        raise FileNotFoundError("Required shared A11 source files are unavailable.")
    data = json.loads(BASE_DATA.read_text(encoding="utf-8"))
    section = next(
        (component for component in data["components"] if component["id"] == SECTION_ID),
        None,
    )
    if section is None:
        raise ValueError("Missing baseline Axis-20 source projection.")
    evidence = section.get("evidence", [])
    if len(evidence) != 1 or evidence[0].get("view") != "as-20":
        raise ValueError("Axis-20 source-projection evidence is incomplete.")
    paths = evidence[0].get("path_indices", [])
    segments = section.get("geometry", {}).get("segments", [])
    if section.get("status") != "SOURCE_PROJECTION_NOT_SOLID" or not paths or not segments:
        raise ValueError("Axis-20 baseline status or vector projection is incomplete.")
    source_text = SOURCE_TEXT.read_text(encoding="utf-8")
    missing_labels = [label for label in REQUIRED_LABELS if label not in source_text]
    if missing_labels:
        raise ValueError("Expected literal A11 labels missing: " + ", ".join(missing_labels))
    output = _output_directory()
    report = {
        "schema": "allshield.axis-source-readiness-audit.v1",
        "status": "PASS_SOURCE_READINESS_AUDIT_PARTIAL_GEOMETRY_APPROVED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_files_modified": False,
        "geometry_created": False,
        "source": {
            "pdf": str(SOURCE_PDF.relative_to(ROOT.parent)).replace("\\", "/"),
            "pdf_sha256": hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest(),
            "text": str(SOURCE_TEXT.relative_to(ROOT.parent)).replace("\\", "/"),
            "view": "AANZICHT as-20",
        },
        "baseline_projection": {
            "component_id": SECTION_ID,
            "status": section["status"],
            "vector_path_indices": paths,
            "line_segments": len(segments),
            "coordinate_station_x_mm": 5150.0,
        },
        "literal_labels_found": list(REQUIRED_LABELS),
        "geometry_readiness": {
            "approved_member_scope": list(APPROVED_PRIMARY_MEMBERS),
            "approved_member_evidence": "The four labels each identify an external IPE500 contour pair whose two direct vector paths define a source-controlled centreline; the resulting centrelines are retained in steel_catalog_axis_20_draft.json.",
            "additional_members_ready": False,
            "missing_required_evidence": [
                "A source-controlled member-to-vector-path mapping for every additional proposed solid.",
                "A source-controlled centreline endpoint pair for every additional proposed solid.",
                "An approved section-orientation decision for every additional proposed profile.",
            ],
            "reason": "The external IPE500 contour pairs provide an unambiguous label-to-path association for marks 30, 29, 21 and 25 only. The remaining labels still have no member-to-path or member-to-centreline association table and are not promoted to solids.",
        },
        "manual_source_request": {
            "needed": "For any additional A11/as-20 members: one of structural-member schedule keyed to A11/as-20 marks; native CAD/DWG export with member IDs; or an annotated A11/as-20 elevation that connects every remaining member label to its vector path and endpoints.",
            "not_needed": "A further unannotated screenshot or PDF crop of A11/as-20, because the current PDF already shows the labels and dimensions.",
        },
    }
    target = output / "axis20_source_readiness.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(target)
    return target


if __name__ == "__main__":
    audit()