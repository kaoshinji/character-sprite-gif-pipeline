#!/usr/bin/env python3
"""
Character Sprite GIF Pipeline v2

Post-processes 4 generated horizontal sprite sheets into:
- 2048x256 aligned sprite sheets
- 256x256-frame GIFs
- validation report
- alignment log
- contact sheet

Expected inputs by default:
  idle.png
  attack.png
  run.png
  hurt.png
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from PIL import Image


ACTIONS = ("idle", "attack", "run", "hurt")


def is_blackish(rgb: np.ndarray, threshold: int = 8) -> np.ndarray:
    return np.all(rgb <= threshold, axis=-1)


def foreground_mask(frame: Image.Image, black_threshold: int = 8) -> np.ndarray:
    arr = np.array(frame.convert("RGBA"))
    visible = arr[:, :, 3] > 0
    non_black = ~is_blackish(arr[:, :, :3], threshold=black_threshold)
    return visible & non_black


def largest_component_bbox(mask: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Return bbox (x0, y0, x1, y1) of largest 4-connected component."""
    h, w = mask.shape
    visited = np.zeros((h, w), dtype=bool)
    best_bbox = None
    best_area = 0

    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue

            q = deque([(y, x)])
            visited[y, x] = True
            area = 0
            minx = maxx = x
            miny = maxy = y

            while q:
                cy, cx = q.popleft()
                area += 1
                minx = min(minx, cx)
                maxx = max(maxx, cx)
                miny = min(miny, cy)
                maxy = max(maxy, cy)

                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append((ny, nx))

            if area > best_area:
                best_area = area
                best_bbox = (minx, miny, maxx + 1, maxy + 1)

    return best_bbox


def split_equal_frames(img: Image.Image, frame_count: int = 8) -> List[Image.Image]:
    """Split a horizontal sheet into equal-width frames."""
    w, h = img.size
    xs = [round(i * w / frame_count) for i in range(frame_count + 1)]
    return [img.crop((xs[i], 0, xs[i + 1], h)).convert("RGBA") for i in range(frame_count)]


def bbox_center_bottom(bbox: Tuple[int, int, int, int]) -> Tuple[float, int]:
    x0, y0, x1, y1 = bbox
    return (x0 + x1) / 2.0, y1


def paste_shifted(frame: Image.Image, dx: int, dy: int) -> Image.Image:
    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 255))
    canvas.alpha_composite(frame.convert("RGBA"), (dx, dy))
    return canvas


def align_frames(
    frames: List[Image.Image],
    black_threshold: int = 8,
    baseline_mode: str = "median",
) -> Tuple[List[Image.Image], List[dict]]:
    """
    Align frames by largest component center X and bottom Y.

    baseline_mode:
    - median: target baseline = median bottom among frames
    - max: target baseline = max bottom among frames
    """
    infos = []
    for idx, frame in enumerate(frames):
        mask = foreground_mask(frame, black_threshold=black_threshold)
        bbox = largest_component_bbox(mask)
        if bbox is None:
            bbox = (0, 0, frame.width, frame.height)
        cx, by = bbox_center_bottom(bbox)
        infos.append({"frame": idx + 1, "bbox": bbox, "center_x": cx, "bottom_y": by})

    target_cx = int(round(float(np.median([i["center_x"] for i in infos]))))
    bottoms = [i["bottom_y"] for i in infos]
    if baseline_mode == "max":
        target_by = int(max(bottoms))
    else:
        target_by = int(round(float(np.median(bottoms))))

    aligned = []
    logs = []
    for frame, info in zip(frames, infos):
        dx = int(round(target_cx - info["center_x"]))
        dy = int(round(target_by - info["bottom_y"]))
        aligned_frame = paste_shifted(frame, dx, dy)
        aligned.append(aligned_frame)
        logs.append({**info, "target_center_x": target_cx, "target_bottom_y": target_by, "dx": dx, "dy": dy})

    return aligned, logs


def crop_foreground_bbox(frame: Image.Image, black_threshold: int = 8) -> Optional[Tuple[int, int, int, int]]:
    return largest_component_bbox(foreground_mask(frame, black_threshold=black_threshold))


def normalize_frame_to_square(
    frame: Image.Image,
    frame_size: int = 256,
    scale_limit: float = 1.0,
) -> Image.Image:
    """
    Put a frame onto a frame_size x frame_size black canvas.

    Preserves pixel art using NEAREST. It downscales only if the source frame
    is larger than the target canvas.
    """
    src = frame.convert("RGBA")
    canvas = Image.new("RGBA", (frame_size, frame_size), (0, 0, 0, 255))
    scale = min(frame_size / src.width, frame_size / src.height, scale_limit)
    new_w = max(1, int(round(src.width * scale)))
    new_h = max(1, int(round(src.height * scale)))
    resized = src.resize((new_w, new_h), Image.NEAREST)
    x = (frame_size - new_w) // 2
    y = (frame_size - new_h) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def rebuild_sheet(frames: List[Image.Image]) -> Image.Image:
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 255))
    for idx, frame in enumerate(frames):
        sheet.alpha_composite(frame.convert("RGBA"), (idx * fw, 0))
    return sheet


def save_gif(frames: List[Image.Image], output_path: Path, duration: int = 110) -> None:
    pal_frames = [frame.convert("P", palette=Image.ADAPTIVE, colors=255) for frame in frames]
    pal_frames[0].save(
        output_path,
        save_all=True,
        append_images=pal_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=False,
    )


def validate_sheet(sheet: Image.Image, action: str, frame_count: int = 8, black_threshold: int = 8) -> dict:
    w, h = sheet.size
    report = {
        "action": action,
        "source_size": [w, h],
        "is_horizontal": w > h,
        "frame_count_assumed": frame_count,
        "warnings": [],
        "frames": [],
    }

    frames = split_equal_frames(sheet, frame_count)
    for idx, frame in enumerate(frames, start=1):
        bbox = crop_foreground_bbox(frame, black_threshold=black_threshold)
        if bbox is None:
            report["warnings"].append(f"frame {idx}: no foreground detected")
            frame_info = {"frame": idx, "bbox": None, "foreground_ok": False}
        else:
            x0, y0, x1, y1 = bbox
            bw, bh = x1 - x0, y1 - y0
            frame_info = {
                "frame": idx,
                "bbox": [x0, y0, x1, y1],
                "bbox_size": [bw, bh],
                "foreground_ok": True,
            }
            if bw < 10 or bh < 10:
                report["warnings"].append(f"frame {idx}: foreground bbox very small")
        report["frames"].append(frame_info)

    if not report["is_horizontal"]:
        report["warnings"].append("source sheet is not horizontal")

    return report


def process_action(
    action: str,
    src_path: Path,
    out_dir: Path,
    frame_size: int,
    duration: int,
    black_threshold: int,
    baseline_mode: str,
) -> Tuple[dict, dict]:
    sheet = Image.open(src_path).convert("RGBA")
    validation = validate_sheet(sheet, action=action, black_threshold=black_threshold)

    raw_frames = split_equal_frames(sheet, 8)
    aligned_raw, alignment_log = align_frames(
        raw_frames,
        black_threshold=black_threshold,
        baseline_mode=baseline_mode,
    )

    normalized = [normalize_frame_to_square(frame, frame_size=frame_size) for frame in aligned_raw]
    normalized_aligned, final_alignment_log = align_frames(
        normalized,
        black_threshold=black_threshold,
        baseline_mode=baseline_mode,
    )

    aligned_sheet = rebuild_sheet(normalized_aligned)

    original_copy = out_dir / f"{action}_sheet_original.png"
    aligned_path = out_dir / f"{action}_sheet_aligned.png"
    gif_path = out_dir / f"{action}.gif"

    sheet.save(original_copy)
    aligned_sheet.save(aligned_path)
    save_gif(normalized_aligned, gif_path, duration=duration)

    combined_log = {
        "action": action,
        "source": str(src_path),
        "first_alignment": alignment_log,
        "final_alignment": final_alignment_log,
        "output_sheet": str(aligned_path),
        "output_gif": str(gif_path),
    }

    return validation, combined_log


def create_contact_sheet(out_dir: Path, actions: Tuple[str, ...], frame_size: int) -> None:
    strips = []
    for action in actions:
        p = out_dir / f"{action}_sheet_aligned.png"
        if p.exists():
            im = Image.open(p).convert("RGBA")
            target_h = min(180, frame_size)
            target_w = int(im.width * target_h / im.height)
            strips.append(im.resize((target_w, target_h), Image.NEAREST))

    if not strips:
        return

    pad = 16
    width = max(im.width for im in strips) + pad * 2
    height = sum(im.height for im in strips) + pad * (len(strips) + 1)
    contact = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    y = pad
    for im in strips:
        x = (width - im.width) // 2
        contact.alpha_composite(im, (x, y))
        y += im.height + pad
    contact.save(out_dir / "contact_sheet_aligned.png")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize sprite sheets into aligned 256x256 GIF packages.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing idle.png, attack.png, run.png, hurt.png")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to write GIFs and aligned sheets")
    parser.add_argument("--frame-size", type=int, default=256, help="Final square frame size. Default: 256")
    parser.add_argument("--duration", type=int, default=110, help="GIF frame duration in milliseconds. Default: 110")
    parser.add_argument("--black-threshold", type=int, default=8, help="RGB threshold for treating pixels as black background")
    parser.add_argument("--baseline-mode", choices=("median", "max"), default="median", help="Baseline target mode")
    parser.add_argument("--actions", nargs="*", default=list(ACTIONS), help="Actions to process. Default: idle attack run hurt")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    validation_reports: Dict[str, dict] = {}
    alignment_logs: Dict[str, dict] = {}

    missing = []
    for action in args.actions:
        src = args.input_dir / f"{action}.png"
        if not src.exists():
            missing.append(str(src))
            continue

        validation, log = process_action(
            action=action,
            src_path=src,
            out_dir=args.output_dir,
            frame_size=args.frame_size,
            duration=args.duration,
            black_threshold=args.black_threshold,
            baseline_mode=args.baseline_mode,
        )
        validation_reports[action] = validation
        alignment_logs[action] = log

    if missing:
        validation_reports["_missing"] = missing

    (args.output_dir / "validation_report.json").write_text(
        json.dumps(validation_reports, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (args.output_dir / "alignment_log.json").write_text(
        json.dumps(alignment_logs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    create_contact_sheet(args.output_dir, tuple(args.actions), args.frame_size)

    if missing:
        print("Missing input files:")
        for p in missing:
            print(f"- {p}")

    print(f"Done. Output written to: {args.output_dir}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
