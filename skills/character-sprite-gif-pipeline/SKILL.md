# Character Sprite GIF Pipeline

## Purpose

Turn a short character prompt into a complete 2D pixel-art animation package.

Default deliverables:

- `idle.gif`
- `attack.gif`
- `run.gif`
- `hurt.gif`
- `idle_sheet_aligned.png`
- `attack_sheet_aligned.png`
- `run_sheet_aligned.png`
- `hurt_sheet_aligned.png`
- optional `base_reference.png`, `contact_sheet_aligned.png`, `alignment_log.txt`

The main goal is to deliver GIFs first. Do not show intermediate previews unless the user asks.

---

## Core Workflow

When the user gives a character prompt:

1. Generate one canonical base character reference.
2. Generate four separate horizontal sprite sheets:
   - idle
   - attack
   - run
   - hurt
3. Split each sheet into 8 equal frames.
4. Align frames by body center and foot baseline.
5. Rebuild aligned sprite sheets.
6. Export GIFs from the aligned frames.
7. Reply with GIF links first.

---

## Hard Rules

### Do

- Use a base character as the identity lock.
- Use the base as reference for all four action sheets.
- Generate one action per sheet.
- Keep every sheet as one horizontal strip.
- Use a pure black background.
- Split sheets into 8 frames.
- Align frames before GIF export.
- Deliver GIFs as the primary output.

### Do Not

- Do not create a presentation board.
- Do not create a labeled showcase image.
- Do not add text, labels, frame numbers, UI, borders, or grids.
- Do not deliver only images when GIFs are expected.
- Do not export GIFs from raw unaligned sheets.
- Do not leave obvious foot baseline bounce or horizontal drifting if post-processing can fix it.

---

## Default Sprite Sheet Specification

Use this unless the user overrides it:

```text
3840x320 pixel art sprite sheet, 8 frames in one horizontal row

EXACT OUTPUT:
- final image should follow a 3840x320 sprite-sheet layout
- 8 frames, each frame conceptually 320x320
- one horizontal row only
- perfectly even spacing
- no borders, no grid lines, no UI
- pure black background only
- each frame visually separated by empty black space
- all animation stays within a fixed bounding box centered in each frame

STYLE:
clean pixel art, sharp edges, 32-bit sprite style,
no blur, no anti-aliasing glow

CONSISTENCY:
same character, same scale, same camera angle
feet aligned to same baseline
body center aligned
no pose drifting
no shape distortion

CHARACTER SCALE:
character occupies only 35% to 40% of frame height
character occupies only 35% to 40% of frame width
very large empty space around character
do not zoom in

SAFE AREA:
all visible pixels stay inside the center 50% of each frame
outer 50% remains empty black

BOUNDARY:
no element may approach frame edges
no overflow between frames
no touching borders
no cross-frame bleeding

VERTICAL:
character centered vertically
large empty space above and below
```

---

## Prompt Templates

### Base Character

```text
Create a single base character reference image on a pure black background.

Subject:
{USER_CHARACTER_PROMPT}

Requirements:
- one full-body character only
- no sprite sheet
- no presentation board
- no labels, text, UI, grid, frame numbers, or captions
- side view facing right unless user specifies otherwise
- clean pixel art
- sharp edges
- 32-bit sprite style
- pure black background
- centered with large empty space
- compact game-sprite-friendly silhouette

Purpose:
This is the canonical base character reference for all later animation sheets.
Preserve identity, palette, silhouette, proportions, hairstyle, outfit,
weapons, accessories, ears, tail, and facial expression.
```

### Idle

```text
Image A is the canonical base character. Use it to preserve identity,
silhouette, palette, proportions, hairstyle, outfit, accessories, and scale.

Create one STRICT pixel art sprite sheet for IDLE only.

Character:
{USER_CHARACTER_PROMPT}

Layout:
- one horizontal row
- 8 frames
- 3840x320 layout intent
- each frame conceptually 320x320
- pure black background only
- no text, labels, borders, grid, UI, or presentation layout
- large black spacing between frames
- centered safe box per frame

Style:
clean pixel art, sharp edges, 32-bit sprite style, no blur, no glow

Scale and alignment:
- character occupies 35% to 40% of frame height and width
- feet aligned to same baseline
- body center aligned
- same camera angle
- no pose drifting
- no shape distortion

Idle animation, 8 frames:
1 ready idle
2 slight bob down
3 slight bob up
4 subtle ear / hair / cloth / tail twitch
5 neutral hold
6 blink
7 settle
8 return to ready idle
```

### Attack

```text
Image A is the canonical base character. Use it to preserve identity,
silhouette, palette, proportions, hairstyle, outfit, accessories, weapons, and scale.

Create one STRICT pixel art sprite sheet for ATTACK only.

Attack animation, 8 frames:
1 deeper crouch
2 anticipation hold
3 wind-up start
4 wind-up peak
5 attack start
6 attack peak impact
7 follow-through
8 recovery

Effect control:
- slash / impact effect only in frames 6 and 7
- effect size 25% to 35% of character size
- effect stays attached to weapon / paw / hand
- no large outward arc
- no glow beyond character width
- no particles spreading outward
- all effects stay inside safe box

Apply the same layout, style, scale, and alignment rules as IDLE.
```

### Run

```text
Image A is the canonical base character. Use it to preserve identity,
silhouette, palette, proportions, hairstyle, outfit, accessories, weapons, and scale.

Create one STRICT pixel art sprite sheet for RUN only.

Run animation, 8 frames:
1 contact pose
2 passing pose
3 extended stride
4 compressed stride
5 opposite contact pose
6 opposite passing pose
7 opposite extended stride
8 loop back toward contact pose

No dust or extra effects unless user asks.
Apply the same layout, style, scale, and alignment rules as IDLE.
```

### Hurt

```text
Image A is the canonical base character. Use it to preserve identity,
silhouette, palette, proportions, hairstyle, outfit, accessories, weapons, and scale.

Create one STRICT pixel art sprite sheet for HURT only.

Hurt animation, 8 frames:
1 ready pose
2 impact reaction
3 recoil backward
4 flinch peak
5 stunned crouch
6 dazed hold
7 recovery start
8 return to ready pose

Effect control:
- optional tiny impact spark only in frame 2
- optional tiny stars or dazed marks only around frame 6
- all effects small and close to body
- all effects stay inside safe box

Apply the same layout, style, scale, and alignment rules as IDLE.
```

---

## Post-Processing Code

Use deterministic processing after image generation.

```python
from PIL import Image
from pathlib import Path
import numpy as np
from collections import deque

def split_equal_frames(img: Image.Image, n=8):
    w, h = img.size
    xs = [round(i * w / n) for i in range(n + 1)]
    return [img.crop((xs[i], 0, xs[i + 1], h)).convert("RGBA") for i in range(n)]

def nonblack_mask(frame: Image.Image):
    arr = np.array(frame)
    return np.any(arr[:, :, :3] != 0, axis=2)

def largest_component_bbox(mask: np.ndarray):
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
                for ny, nx in ((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny,nx] and not visited[ny,nx]:
                        visited[ny,nx] = True
                        q.append((ny,nx))
            if area > best_area:
                best_area = area
                best_bbox = (minx, miny, maxx + 1, maxy + 1)
    return best_bbox

def align_frames(frames):
    infos = []
    for fr in frames:
        bbox = largest_component_bbox(nonblack_mask(fr))
        if bbox is None:
            bbox = (0, 0, fr.width, fr.height)
        minx, miny, maxx, maxy = bbox
        infos.append((bbox, (minx + maxx) / 2, maxy))
    target_cx = int(round(float(np.median([i[1] for i in infos]))))
    target_by = int(round(float(np.median([i[2] for i in infos]))))
    aligned = []
    logs = []
    for fr, (bbox, cx, by) in zip(frames, infos):
        dx = int(round(target_cx - cx))
        dy = int(round(target_by - by))
        canvas = Image.new("RGBA", fr.size, (0, 0, 0, 255))
        canvas.alpha_composite(fr, (dx, dy))
        aligned.append(canvas)
        logs.append({"bbox": bbox, "dx": dx, "dy": dy})
    return aligned, logs

def save_aligned_sheet(frames, output_path):
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 255))
    for i, fr in enumerate(frames):
        sheet.alpha_composite(fr, (i * fw, 0))
    sheet.save(output_path)

def save_gif(frames, output_path, duration=110):
    pal_frames = [fr.convert("P", palette=Image.ADAPTIVE, colors=255) for fr in frames]
    pal_frames[0].save(
        output_path,
        save_all=True,
        append_images=pal_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=False,
    )

def process_sprite_sheet(src_path, aligned_sheet_path, gif_path):
    img = Image.open(src_path).convert("RGBA")
    frames = split_equal_frames(img, 8)
    aligned_frames, logs = align_frames(frames)
    save_aligned_sheet(aligned_frames, aligned_sheet_path)
    save_gif(aligned_frames, gif_path)
    return logs
```

---

## Quality Checklist

Before final delivery:

- [ ] No presentation board.
- [ ] No labels, text, frame numbers, UI, grid, or borders.
- [ ] Four action sheets exist.
- [ ] Each sheet has 8 frames.
- [ ] Each sheet is horizontal.
- [ ] Pure black background.
- [ ] GIFs are generated from aligned sheets.
- [ ] Foot baseline is stabilized.
- [ ] Horizontal body center is stabilized.
- [ ] GIFs loop correctly.

---

## Final Response Template

If the user asks for full delivery:

```text
已完成 GIF：

[待機 GIF](...)
[攻擊 GIF](...)
[奔跑 GIF](...)
[被擊中 GIF](...)

對齊版 spritesheet：
[待機 spritesheet](...)
[攻擊 spritesheet](...)
[奔跑 spritesheet](...)
[被擊中 spritesheet](...)
```

If the user only asks for GIF delivery:

```text
[待機 GIF](...)
[攻擊 GIF](...)
[奔跑 GIF](...)
[被擊中 GIF](...)
```

---

## Failure Recovery

If the generated image becomes a presentation board or contains text:

1. Reject that generation as invalid.
2. Regenerate the affected action only.
3. Strengthen prompt with:

```text
Do not create a presentation board.
Do not create a contact sheet.
Do not add labels, numbers, captions, UI, borders, or grids.
Create only one single horizontal animation strip.
```

If GIFs are missing:

1. Do not regenerate images first.
2. Locate the existing sprite sheets.
3. Run post-processing.
4. Deliver GIF links.

If alignment is poor:

1. Re-run alignment using largest connected component.
2. Align by median bottom Y and median center X.
3. If effects distort detection, reduce effect size in prompt or mask effects manually.
