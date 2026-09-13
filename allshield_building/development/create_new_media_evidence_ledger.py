"""Create an evidence-only ledger for the September 2026 shared media set."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IMAGE_COUNT = 30
EXPECTED_VIDEO_COUNT = 6


def _image_observation(filename: str) -> dict:
    if "11.57.21" in filename:
        return {
            "categories": ["WINDOW_PHYSICAL_LAYER"],
            "observed_facts": ["Interior high window frame and surrounding sandwich wall are visible."],
            "candidate_building_references": ["Exterior facade and grid correspondence unresolved."],
        }
    if "11.57.22" in filename:
        return {
            "categories": ["ROOF_SANDWICH_UNDERSIDE", "PRIMARY_AND_SECONDARY_STEEL"],
            "observed_facts": ["White roof-panel underside, dark roof steel and diagonal bracing are visible."],
            "candidate_building_references": ["Exact roof field, member marks and grid station unresolved."],
        }
    if "11.57.23" in filename:
        return {
            "categories": ["CABLE_LADDER_OR_TRAY", "WINDOW_PHYSICAL_LAYER"],
            "observed_facts": ["A horizontal wire cable support passes the interior wall near a window and door."],
            "candidate_building_references": ["Route endpoints, support spacing, grid station and elevation unresolved."],
        }
    if "11.57.24" in filename:
        return {
            "categories": ["CABLE_LADDER_OR_TRAY", "WIND_BRACING", "WINDOW_PHYSICAL_LAYER"],
            "observed_facts": ["Wire cable support, diagonal bracing and a high interior window are visible together."],
            "candidate_building_references": ["No source-backed coordinate registration between these items is available."],
        }
    if "11.57.25" in filename:
        return {
            "categories": ["CABLE_LADDER_OR_TRAY", "KOOILADDER_OR_LOOPBRIDGE", "WIND_BRACING"],
            "observed_facts": ["A wire cable support and a separate vertical access/bridge structure are visible."],
            "candidate_building_references": ["Cable support and access structure remain distinct unresolved components."],
        }
    if "11.57.26" in filename or "11.57.27" in filename or "11.57.28" in filename:
        return {
            "categories": ["ROOF_SANDWICH_UNDERSIDE", "PRIMARY_AND_SECONDARY_STEEL", "WIND_BRACING"],
            "observed_facts": ["Roof-panel underside, roof steel and diagonal bracing are visible."],
            "candidate_building_references": ["Roof panel seam datum and member identities unresolved."],
        }
    if "11.57.29" in filename or "11.57.30" in filename or "11.57.31" in filename or "11.57.32" in filename:
        return {
            "categories": ["WALL_SANDWICH_PANELS", "WINDOW_PHYSICAL_LAYER", "EXTERIOR_DOOR"],
            "observed_facts": ["Vertical exterior wall panels, a high window and a door zone are visible."],
            "candidate_building_references": ["Facade and grid correspondence are unresolved; no opening dimension is derived."],
        }
    if "11.57.33" in filename or "11.57.34" in filename or "11.57.35" in filename:
        return {
            "categories": ["WALL_SANDWICH_PANELS", "WIND_BRACING", "PRIMARY_AND_SECONDARY_STEEL"],
            "observed_facts": ["Interior sandwich wall, diagonal bracing and adjacent dark steel are visible."],
            "candidate_building_references": ["Exact frame, member mark and coordinate registration unresolved."],
        }
    raise ValueError("No image observation mapping for " + filename)


def _video_observation(filename: str) -> dict:
    if "11.57.19" in filename:
        return {
            "categories": ["WINDOW_PHYSICAL_LAYER", "CABLE_LADDER_OR_TRAY", "KOOILADDER_OR_LOOPBRIDGE"],
            "observed_facts": ["The sequence shows high windows, a door zone, wire cable support and an access structure."],
            "candidate_building_references": ["Interior wall/grid correspondence and metric route geometry unresolved."],
            "sample_indices": [0, 4, 5, 6, 8, 9, 11],
        }
    if "11.57.32" in filename:
        return {
            "categories": ["WINDOW_PHYSICAL_LAYER", "CABLE_LADDER_OR_TRAY", "ROOF_SANDWICH_UNDERSIDE"],
            "observed_facts": ["The sequence shows a door/window wall, wire cable support, roof panels and steel."],
            "candidate_building_references": ["No absolute coordinate or profile-size measurement is available."],
            "sample_indices": [1, 2, 3, 5, 6, 9, 10, 11],
        }
    if "11.57.33 (1)" in filename:
        return {
            "categories": ["EXTERIOR_CONTEXT_ONLY"],
            "observed_facts": ["Street-side context is visible without a reliable building-coordinate reference."],
            "candidate_building_references": ["Not used for model geometry."],
            "sample_indices": [0, 5, 8, 11],
        }
    if "11.57.33" in filename:
        return {
            "categories": ["WALL_SANDWICH_PANELS", "WINDOW_PHYSICAL_LAYER", "EXTERIOR_DOOR"],
            "observed_facts": ["An exterior wall with vertical panels, high window and door zone is visible."],
            "candidate_building_references": ["Facade and grid correspondence unresolved."],
            "sample_indices": [0, 2, 4, 6, 8, 10],
        }
    if "11.57.35" in filename:
        return {
            "categories": ["ROOF_SANDWICH_UNDERSIDE", "PRIMARY_AND_SECONDARY_STEEL", "WIND_BRACING"],
            "observed_facts": ["The sequence shows roof underside panels, steel framing and diagonal bracing."],
            "candidate_building_references": ["Roof seam phase and member IDs unresolved."],
            "sample_indices": [0, 3, 4, 8, 10, 11],
        }
    if "11.57.36" in filename:
        return {
            "categories": ["ROOF_SANDWICH_UNDERSIDE", "PRIMARY_AND_SECONDARY_STEEL", "EXTERIOR_DOOR"],
            "observed_facts": ["The sequence shows roof panels, steel framing and a large door wall."],
            "candidate_building_references": ["Door wall, grid station and member identities unresolved."],
            "sample_indices": [1, 3, 6, 9, 10, 11],
        }
    raise ValueError("No video observation mapping for " + filename)


def _selected_frames(record: dict, indices: list[int]) -> list[dict]:
    samples = record.get("samples", [])
    selected = []
    for index in indices:
        if index >= len(samples):
            raise ValueError("Missing selected frame %d for %s" % (index, record["source"]))
        sample = samples[index]
        selected.append({
            "frame_index": sample["frame_index"],
            "time_seconds": sample["time_seconds"],
            "review_frame": sample["review_frame"],
        })
    return selected


def _image_row(record: dict) -> dict:
    observation = _image_observation(Path(record["source"]).name)
    return {
        "source_type": "IMAGE",
        "source": record["source"],
        "sha256": record["sha256"],
        "pixel_size": record["pixel_size"],
        "evidence_status": "VISUAL_OBSERVATION_ONLY",
        "eligible_for_new_geometry": False,
        "coordinate_status": "UNRESOLVED_NO_REGISTERED_BUILDING_REFERENCES",
        **observation,
    }


def _video_row(record: dict) -> dict:
    if record.get("decode_status") != "PASS":
        raise ValueError("Video did not decode: " + record["source"])
    observation = _video_observation(Path(record["source"]).name)
    return {
        "source_type": "VIDEO",
        "source": record["source"],
        "sha256": record["sha256"],
        "pixel_size": record["metadata"]["pixel_size"],
        "duration_seconds": record["metadata"]["duration_seconds"],
        "evidence_status": "VISUAL_OBSERVATION_ONLY",
        "eligible_for_new_geometry": False,
        "coordinate_status": "UNRESOLVED_NO_REGISTERED_BUILDING_REFERENCES",
        "selected_frames": _selected_frames(record, observation.pop("sample_indices")),
        **observation,
    }


def _output_directory() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = ROOT / "outputs" / ("new_media_evidence_ledger_" + stamp)
    output.mkdir(parents=True, exist_ok=False)
    return output


def create_ledger(review_index: Path) -> Path:
    index = json.loads(review_index.read_text(encoding="utf-8"))
    if index.get("status") != "PASS_REVIEW_ARTIFACTS_CREATED":
        raise ValueError("Review index is not a successful media-review artifact.")
    images = index.get("images", [])
    videos = index.get("videos", [])
    if len(images) != EXPECTED_IMAGE_COUNT or len(videos) != EXPECTED_VIDEO_COUNT:
        raise ValueError("Expected %d images and %d videos." % (EXPECTED_IMAGE_COUNT, EXPECTED_VIDEO_COUNT))
    rows = [_image_row(record) for record in images] + [_video_row(record) for record in videos]
    if len(rows) != EXPECTED_IMAGE_COUNT + EXPECTED_VIDEO_COUNT:
        raise AssertionError("Media ledger did not retain every reviewed source.")
    if any(row["eligible_for_new_geometry"] for row in rows):
        raise AssertionError("Visual observations must not create new geometry eligibility.")
    output = _output_directory()
    report = {
        "schema": "allshield.media-evidence-ledger.draft.v1",
        "revision": "2026-09-13-relocated-shared-media-review",
        "status": "PASS_EVIDENCE_LEDGER_CREATED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "review_index": str(review_index.relative_to(ROOT)).replace("\\", "/"),
        "review_index_sha256": hashlib.sha256(review_index.read_bytes()).hexdigest(),
        "source_files_modified": False,
        "geometry_created": False,
        "records": rows,
        "confirmed_visual_presence": [
            "Vertical exterior sandwich panels and an interior sandwich wall.",
            "Roof sandwich-panel underside, roof steel and diagonal bracing.",
            "High windows with physical inner and exterior frame layers.",
            "A horizontal wire cable support distinct from a vertical access/bridge structure.",
        ],
        "not_promoted_from_visual_evidence": [
            "Absolute coordinates, elevations, dimensions, section profiles, member marks and connection geometry.",
            "Facade-to-photo correspondence for the C4a Facade_1 window bank.",
            "Roof-panel seam phase, steeldeck rib datum or DN900 panel containment.",
            "Cable support route, width, endpoints, supports and height.",
        ],
        "manual_source_required_before_next_geometry": [
            {
                "target": "Next primary-steel solid slice",
                "required_source": "Readable crop or vector export of A11 page 1, AANZICHT as-8, including member labels and the full visible frame.",
                "reason": "The existing PDF text identifies labels but does not associate them to individual source traces."
            },
            {
                "target": "Wire cable ladder/tray",
                "required_source": "Measured plan or two field photos with independently identified grid references, plus tray width, height and endpoint dimensions.",
                "reason": "The media proves presence only; perspective cannot establish a route in the 21/A coordinate system."
            },
            {
                "target": "Physical window assemblies",
                "required_source": "One confirmed facade/grid ID per photographed window and a section or field dimensions for exterior frame, interior frame, glass and reveal depths.",
                "reason": "The C4a six-light projection has no proven correspondence to these photographed assemblies."
            },
            {
                "target": "Roof panel segmentation and steeldeck ribs",
                "required_source": "Roof panel layout or an onsite measurement locating one panel seam and one rib relative to two grid axes or a roof edge.",
                "reason": "Nominal widths do not determine the installed seam or rib phase."
            },
        ],
    }
    target = output / "new_media_evidence_ledger.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-index", type=Path, required=True)
    args = parser.parse_args()
    review_index = args.review_index.resolve()
    try:
        review_index.relative_to(ROOT / "outputs")
    except ValueError as error:
        raise ValueError("Review index must be below the active work directory outputs folder.") from error
    create_ledger(review_index)


if __name__ == "__main__":
    main()