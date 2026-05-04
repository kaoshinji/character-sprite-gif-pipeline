#!/usr/bin/env python3
"""
Character Sprite GIF Pipeline v3

Green-screen first pipeline:
- source sheets may be pure chroma green (#00FF00) or black
- green is removed into alpha before body detection
- frames are aligned by alpha silhouette / foot baseline
- final GIFs are exported on black background by default

Outputs:
- 2048x256 aligned sheets, 8 frames x 256x256
- 256x256-frame GIFs
- validation_report.json
- alignment_log.json
- contact_sheet_aligned.png
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

ACTIONS = ("idle", "attack", "run", "hurt")


def parse_rgb(value: str) -> Tuple[int, int, int]:
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("RGB must be like 0,255,0")
    try:
        rgb = tuple(int(p.strip()) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("RGB values must be integers") from exc
    if any(v < 0 or v > 255 for v in rgb):
        raise argparse.ArgumentTypeError("RGB values must be 0..255")
    return rgb  # type: ignore[return-value]


def is_blackish(rgb: np.ndarray, threshold: int = 8) -> np.ndarray:
    return np.all(rgb <= threshold, axis=-1)


def chroma_key_to_alpha(
    img: Image.Image,
    key_rgb: Tuple[int, int, int] = (0, 255, 0),
    tolerance: float = 70.0,
) -> Image.Image:
    """Convert pixels close to chroma-key green into transparent alpha."""
    arr = np.array(img.convert("RGBA"))
    rgb = arr[:, :, :3].astype(np.int16)
    key = np.array(key_rgb, dtype=np.int16)
    dist = np.sqrt(np.sum((rgb - key) ** 2, axis=2))
    mask = dist <= tolerance
    arr[:, :, 3] = np.where(mask, 0, arr[:, :, 3])
    return Image.fromarray(arr, "RGBA")


def frame_to_working_alpha(
    frame: Image.Image,
    source_bg: str,
    key_rgb: Tuple[int, int, int],
    green_tolerance: float,
    black_threshold: int,
) -> Image.Image:
    """
    Convert source frame to RGBA with background alpha removed when possible.

    source_bg:
    - green: remove chroma key green
    - black: leave black background and use non-black detection later
    - auto: remove green only if the image contains substantial green
    """
    fr = frame.convert("RGBA")
    if source_bg == "green":
        return chroma_key_to_alpha(fr, key_rgb=key_rgb, tolerance=green_tolerance)
    if source_bg == "auto":
        arr = np.array(fr)
        rgb = arr[:, :, :3].astype(np.int16)
        key = np.array(key_rgb, dtype=np.int16)
        dist = np.sqrt(np.sum((rgb - key) ** 2, axis=2))
        green_ratio = float(np.mean(dist <= green_tolerance))
        if green_ratio > 0.20:
            return chroma_key_to_alpha(fr, key_rgb=key_rgb, tolerance=green_tolerance)
    return fr


def foreground_mask(frame: Image.Image, black_threshold: int = 8) -> np.ndarray:
    arr = np.array(frame.convert("RGBA"))
    # Prefer alpha silhouette when chroma key created transparency.
    if np.any(arr[:, :, 3] == 0):
        return arr[:, :, 3] > 0
    visible = arr[:, :, 3] > 0
    non_black = ~is_blackish(arr[:, :, :3], threshold=black_threshold)
    return visible & non_black


def largest_component_bbox(mask: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
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
    w, h = img.size
    xs = [round(i * w / frame_count) for i in range(frame_count + 1)]
    return [img.crop((xs[i], 0, xs[i + 1], h)).convert("RGBA") for i in range(frame_count)]


def paste_shifted(frame: Image.Image, dx: int, dy: int, transparent: bool = True) -> Image.Image:
    bg = (0, 0, 0, 0) if transparent else (0, 0, 0, 255)
    canvas = Image.new("RGBA", frame.size, bg)
    canvas.alpha_composite(frame.convert("RGBA"), (dx, dy))
    return canvas


def align_frames(
    frames: List[Image.Image],
    black_threshold: int = 8,
    baseline_mode: str = "median",
) -> Tuple[List[Image.Image], List[dict]]:
    infos = []
    for idx, frame in enumerate(frames):
        bbox = largest_component_bbox(foreground_mask(frame, black_threshold=black_threshold))
        if bbox is None:
            bbox = (0, 0, frame.width, frame.height)
        x0, y0, x1, y1 = bbox
        infos.append({"frame": idx + 1, "bbox": bbox, "center_x": (x0 + x1) / 2.0, "bottom_y": y1})

    target_cx = int(round(float(np.median([i["center_x"] for i in infos]))))
    bottoms = [i["bottom_y"] for i in infos]
    target_by = int(max(bottoms)) if baseline_mode == "max" else int(round(float(np.median(bottoms))))

    aligned = []
    logs = []
    for frame, info in zip(frames, infos):
        dx = int(round(target_cx - info["center_x"]))
        dy = int(round(target_by - info["bottom_y"]))
        aligned.append(paste_shifted(frame, dx, dy, transparent=True))
        logs.append({**info, "target_center_x": target_cx, "target_bottom_y": target_by, "dx": dx, "dy": dy})
    return aligned, logs


def normalize_frame_to_square(frame: Image.Image, frame_size: int = 256, scale_limit: float = 1.0) -> Image.Image:
    src = frame.convert("RGBA")
    canvas = Image.new("RGBA", (frame_size, frame_size), (0, 0, 0, 0))
    scale = min(frame_size / src.width, frame_size / src.height, scale_limit)
    new_w = max(1, int(round(src.width * scale)))
    new_h = max(1, int(round(src.height * scale)))
    resized = src.resize((new_w, new_h), Image.NEAREST)
    x = (frame_size - new_w) // 2
    y = (frame_size - new_h) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def render_background(frame: Image.Image, output_bg: str) -> Image.Image:
    if output_bg == "transparent":
        return frame.convert("RGBA")
    bg_color = (0, 255, 0, 255) if output_bg == "green" else (0, 0, 0, 255)
    canvas = Image.new("RGBA", frame.size, bg_color)
    canvas.alpha_composite(frame.convert("RGBA"), (0, 0))
    return canvas


def rebuild_sheet(frames: List[Image.Image], output_bg: str = "black") -> Image.Image:
    fw, fh = frames[0].size
    bg_color = (0, 0, 0, 0) if output_bg == "transparent" else ((0, 255, 0, 255) if output_bg == "green" else (0, 0, 0, 255))
    sheet = Image.new("RGBA", (fw * len(frames), fh), bg_color)
    for idx, frame in enumerate(frames):
        sheet.alpha_composite(frame.convert("RGBA"), (idx * fw, 0))
    return sheet


def save_gif(frames: List[Image.Image], output_path: Path, duration: int = 110, output_bg: str = "black") -> None:
    rendered = [render_background(frame, output_bg if output_bg != "transparent" else "black") for frame in frames]
    pal_frames = [frame.convert("P", palette=Image.ADAPTIVE, colors=255) for frame in rendered]
    pal_frames[0].save(
        output_path,
        save_all=True,
        append_images=pal_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=False,
    )


def validate_sheet(sheet: Image.Image, action: str, source_bg: str, key_rgb: Tuple[int, int, int], green_tolerance: float, black_threshold: int, frame_count: int = 8) -> dict:
    w, h = sheet.size
    report = {"action": action, "source_size": [w, h], "is_horizontal": w > h, "frame_count_assumed": frame_count, "warnings": [], "frames": []}
    frames = split_equal_frames(sheet, frame_count)
    for idx, raw in enumerate(frames, start=1):
        frame = frame_to_working_alpha(raw, source_bg, key_rgb, green_tolerance, black_threshold)
        bbox = largest_component_bbox(foreground_mask(frame, black_threshold=black_threshold))
        if bbox is None:
            report["warnings"].append(f"frame {idx}: no foreground detected")
            report["frames"].append({"frame": idx, "bbox": None, "foreground_ok": False})
        else:
            x0, y0, x1, y1 = bbox
            bw, bh = x1 - x0, y1 - y0
            if bw < 10 or bh < 10:
                report["warnings"].append(f"frame {idx}: foreground bbox very small")
            report["frames"].append({"frame": idx, "bbox": [x0, y0, x1, y1], "bbox_size": [bw, bh], "foreground_ok": True})
    if not report["is_horizontal"]:
        report["warnings"].append("source sheet is not horizontal")
    return report


def process_action(action: str, src_path: Path, out_dir: Path, frame_size: int, duration: int, black_threshold: int, baseline_mode: str, source_bg: str, output_bg: str, key_rgb: Tuple[int, int, int], green_tolerance: float) -> Tuple[dict, dict]:
    sheet = Image.open(src_path).convert("RGBA")
    validation = validate_sheet(sheet, action, source_bg, key_rgb, green_tolerance, black_threshold)
    raw_frames = split_equal_frames(sheet, 8)
    working_frames = [frame_to_working_alpha(f, source_bg, key_rgb, green_tolerance, black_threshold) for f in raw_frames]
    aligned_raw, alignment_log = align_frames(working_frames, black_threshold=black_threshold, baseline_mode=baseline_mode)
    normalized = [normalize_frame_to_square(frame, frame_size=frame_size) for frame in aligned_raw]
    normalized_aligned, final_alignment_log = align_frames(normalized, black_threshold=black_threshold, baseline_mode=baseline_mode)

    original_copy = out_dir / f"{action}_sheet_original.png"
    transparent_sheet_path = out_dir / f"{action}_sheet_transparent.png"
    aligned_path = out_dir / f"{action}_sheet_aligned.png"
    gif_path = out_dir / f"{action}.gif"

    sheet.save(original_copy)
    rebuild_sheet(normalized_aligned, output_bg="transparent").save(transparent_sheet_path)
    rebuild_sheet(normalized_aligned, output_bg=output_bg).save(aligned_path)
    save_gif(normalized_aligned, gif_path, duration=duration, output_bg=output_bg)

    return validation, {"action": action, "source": str(src_path), "source_bg": source_bg, "output_bg": output_bg, "first_alignment": alignment_log, "final_alignment": final_alignment_log, "output_sheet": str(aligned_path), "output_gif": str(gif_path)}


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
    parser = argparse.ArgumentParser(description="Green-screen sprite sheets into aligned 256x256 GIF packages.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frame-size", type=int, default=256)
    parser.add_argument("--duration", type=int, default=110)
    parser.add_argument("--black-threshold", type=int, default=8)
    parser.add_argument("--baseline-mode", choices=("median", "max"), default="median")
    parser.add_argument("--source-bg", choices=("green", "black", "auto"), default="green", help="Use green for chroma-key source sheets. Default: green")
    parser.add_argument("--output-bg", choices=("black", "green", "transparent"), default="black", help="Final sheet background. GIFs use black when transparent is selected.")
    parser.add_argument("--green-key", type=parse_rgb, default=(0, 255, 0), help="Chroma key RGB, e.g. 0,255,0")
    parser.add_argument("--green-tolerance", type=float, default=85.0, help="Euclidean RGB tolerance for chroma key")
    parser.add_argument("--actions", nargs="*", default=list(ACTIONS))
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
        validation, log = process_action(action, src, args.output_dir, args.frame_size, args.duration, args.black_threshold, args.baseline_mode, args.source_bg, args.output_bg, args.green_key, args.green_tolerance)
        validation_reports[action] = validation
        alignment_logs[action] = log

    if missing:
        validation_reports["_missing"] = missing

    (args.output_dir / "validation_report.json").write_text(json.dumps(validation_reports, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.output_dir / "alignment_log.json").write_text(json.dumps(alignment_logs, indent=2, ensure_ascii=False), encoding="utf-8")
    create_contact_sheet(args.output_dir, tuple(args.actions), args.frame_size)

    if missing:
        print("Missing input files:")
        for p in missing:
            print(f"- {p}")
    print(f"Done. Output written to: {args.output_dir}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
