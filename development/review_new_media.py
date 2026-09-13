"""Create a non-destructive review package for the September 2026 media set."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATTERN = "WhatsApp Image 2026-09-02*.jpeg"
VIDEO_PATTERN = "WhatsApp Video 2026-09-02*.mp4"
THUMBNAIL_SIZE = (320, 240)
SAMPLES_PER_VIDEO = 12


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _output_directory() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = ROOT / "outputs" / ("new_media_review_" + stamp)
    output.mkdir(parents=True, exist_ok=False)
    return output


def _labelled_thumbnail(image: Image.Image, label: str) -> Image.Image:
    thumbnail = ImageOps.contain(image.convert("RGB"), THUMBNAIL_SIZE)
    canvas = Image.new("RGB", (THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1] + 32), "white")
    x = (THUMBNAIL_SIZE[0] - thumbnail.width) // 2
    y = (THUMBNAIL_SIZE[1] - thumbnail.height) // 2
    canvas.paste(thumbnail, (x, y))
    ImageDraw.Draw(canvas).text((6, THUMBNAIL_SIZE[1] + 8), label, fill="black")
    return canvas


def _contact_sheet(items: list[tuple[Image.Image, str]], target: Path, title: str) -> None:
    columns = 4
    tile_width, tile_height = THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1] + 32
    rows = max(1, (len(items) + columns - 1) // columns)
    sheet = Image.new("RGB", (columns * tile_width, 38 + rows * tile_height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 10), title, fill="black")
    for index, (image, label) in enumerate(items):
        tile = _labelled_thumbnail(image, label)
        x = (index % columns) * tile_width
        y = 38 + (index // columns) * tile_height
        sheet.paste(tile, (x, y))
    sheet.save(target, format="PNG")


def _image_records(output: Path) -> list[dict]:
    source_paths = sorted((ROOT / "sources" / "images").glob(IMAGE_PATTERN))
    contact_items: list[tuple[Image.Image, str]] = []
    records = []
    for path in source_paths:
        with Image.open(path) as source:
            image = source.copy()
        contact_items.append((image, path.name))
        records.append({
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "pixel_size": [image.width, image.height],
        })
    sheets = output / "image_contact_sheets"
    sheets.mkdir()
    for start in range(0, len(contact_items), 20):
        end = min(start + 20, len(contact_items))
        _contact_sheet(
            contact_items[start:end],
            sheets / ("whatsapp_images_%02d_%02d.png" % (start + 1, end)),
            "WhatsApp images %d-%d" % (start + 1, end),
        )
    return records


def _video_metadata(capture: cv2.VideoCapture) -> dict:
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_seconds = frame_count / fps if frame_count > 0 and fps > 0 else None
    return {
        "frame_count": frame_count,
        "frames_per_second": fps,
        "duration_seconds": duration_seconds,
        "pixel_size": [width, height],
    }


def _video_records(output: Path) -> list[dict]:
    source_paths = sorted((ROOT / "sources" / "video").glob(VIDEO_PATTERN))
    samples_root = output / "video_samples"
    samples_root.mkdir()
    records = []
    for video_index, path in enumerate(source_paths, start=1):
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            records.append({
                "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
                "decode_status": "FAILED_TO_OPEN",
            })
            continue
        try:
            metadata = _video_metadata(capture)
            frame_count = metadata["frame_count"]
            sample_dir = samples_root / ("video_%02d" % video_index)
            sample_dir.mkdir()
            contact_items: list[tuple[Image.Image, str]] = []
            samples = []
            for sample_index in range(SAMPLES_PER_VIDEO):
                frame_index = round(sample_index * max(0, frame_count - 1) / max(1, SAMPLES_PER_VIDEO - 1))
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ok, frame = capture.read()
                if not ok:
                    continue
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                time_seconds = frame_index / metadata["frames_per_second"] if metadata["frames_per_second"] else None
                frame_path = sample_dir / ("frame_%02d.png" % (sample_index + 1))
                image.save(frame_path, format="PNG")
                label = "%02d  %.2fs" % (sample_index + 1, time_seconds) if time_seconds is not None else "%02d" % (sample_index + 1)
                contact_items.append((image, label))
                samples.append({
                    "frame_index": frame_index,
                    "time_seconds": time_seconds,
                    "review_frame": str(frame_path.relative_to(output)).replace("\\", "/"),
                })
            contact_path = sample_dir / "contact_sheet.png"
            _contact_sheet(contact_items, contact_path, path.name)
            records.append({
                "source": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
                "decode_status": "PASS",
                "metadata": metadata,
                "contact_sheet": str(contact_path.relative_to(output)).replace("\\", "/"),
                "samples": samples,
            })
        finally:
            capture.release()
    return records


def _duplicate_groups(records: list[dict]) -> list[list[str]]:
    grouped: dict[str, list[str]] = {}
    for record in records:
        grouped.setdefault(record["sha256"], []).append(record["source"])
    return [paths for paths in grouped.values() if len(paths) > 1]


def main() -> Path:
    output = _output_directory()
    images = _image_records(output)
    videos = _video_records(output)
    report = {
        "status": "PASS_REVIEW_ARTIFACTS_CREATED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_patterns": ["sources/images/" + IMAGE_PATTERN, "sources/video/" + VIDEO_PATTERN],
        "images": images,
        "videos": videos,
        "exact_duplicate_groups": _duplicate_groups(images + videos),
        "source_files_modified": False,
    }
    target = output / "media_review_index.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(target)
    return target


if __name__ == "__main__":
    main()