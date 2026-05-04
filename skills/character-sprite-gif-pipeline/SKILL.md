# Character Sprite GIF Pipeline v3 — Green-Screen 256x256 Executable Package

## Purpose

Turn a short character prompt into a complete 2D pixel-art animation package.

This v3 version uses a **green-screen source workflow** for better contour extraction:

```text
source generation: pure chroma-key green #00FF00
post-processing: remove green into alpha
alignment: use alpha silhouette / body contour
final output: black-background GIFs by default
```

Final normalized format:

```text
8 frames × 256x256 = 2048x256 final aligned sprite sheet
```

Default output:

```text
idle.gif
attack.gif
run.gif
hurt.gif

idle_sheet_aligned.png
attack_sheet_aligned.png
run_sheet_aligned.png
hurt_sheet_aligned.png

idle_sheet_transparent.png
attack_sheet_transparent.png
run_sheet_transparent.png
hurt_sheet_transparent.png
```

GIFs are generated from aligned 256x256 frames.

---

## Default Actions

Always generate these four actions unless the user overrides them:

1. `idle`
2. `attack`
3. `run`
4. `hurt`

---

## Core Workflow

When the user gives a character prompt:

1. Generate one canonical base character reference on pure green background.
2. Generate four separate horizontal sprite sheets on pure green background: `idle`, `attack`, `run`, `hurt`.
3. Split each sheet into 8 equal frames.
4. Remove chroma green into transparency.
5. Detect character body by alpha silhouette.
6. Align each frame by horizontal body center and foot baseline.
7. Normalize each frame to exact `256x256`.
8. Rebuild aligned sheets as exact `2048x256`.
9. Export GIFs on black background by default.
10. Deliver GIF links first.

---

## Why Green Background

Black source backgrounds can damage contour detection because pixel-art characters often include black outlines, black hair, black clothes, and dark shadows. Green-screen source images make it easier to:

- preserve black outlines
- remove background cleanly
- detect the true body silhouette
- align foot baseline more accurately
- reduce horizontal drift and vertical bounce

Final GIFs should still be exported on black background unless the user asks for transparent or green output.

---

## Hard Rules

### Do

- Use a base character as the identity lock.
- Use the base as reference for all four action sheets.
- Generate one action per sheet.
- Keep every sheet as one horizontal strip.
- Use pure chroma-key green `#00FF00` during source generation.
- Remove green to alpha before contour detection.
- Split sheets into 8 frames.
- Normalize every final frame to `256x256`.
- Normalize every final aligned sheet to `2048x256`.
- Align frames before GIF export.
- Deliver GIFs as the primary output.

### Do Not

- Do not create a presentation board.
- Do not create a labeled showcase image.
- Do not add text, labels, frame numbers, UI, borders, or grids.
- Do not use gradients, shadows, floors, scenery, texture, or lighting on the green background.
- Do not export GIFs from raw unaligned sheets.
- Do not leave obvious foot-baseline bounce or horizontal drifting if post-processing can fix it.

---

## Default Sprite Sheet Specification

Use this unless the user overrides it:

```text
2048x256 pixel art sprite sheet, 8 frames in one horizontal row

SOURCE BACKGROUND:
- pure chroma-key green #00FF00 only
- no gradients
- no shadows
- no floor
- no texture
- no background objects
- green will be removed in post-processing
- final GIF will be exported on pure black background

EXACT OUTPUT:
- final aligned sheet must be exactly 2048x256
- 8 frames, each exactly 256x256
- one horizontal row only
- no borders, no grid lines, no UI
- final normalized frames must stay centered inside 256x256 cells

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
character occupies only 35% to 45% of each 256x256 frame height
character occupies only 35% to 45% of each 256x256 frame width
large empty space around character
do not zoom in

SAFE AREA:
all visible character pixels should stay inside the center 60% of each frame
outer area remains green in source, then black/transparent in final

BOUNDARY:
no element may approach frame edges
no overflow between frames
no touching borders
no cross-frame bleeding

VERTICAL:
character centered vertically after baseline alignment
large empty space above and below
```

---

## Prompt Templates

### Base Character

```text
Create a single base character reference image on a pure chroma-key green background #00FF00.

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
- pure #00FF00 green background only
- no gradient, no shadow, no floor, no texture
- centered with large empty green space
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
- 8 frames only
- final normalized output will be 2048x256
- each final frame will be 256x256
- pure chroma-key green #00FF00 background only
- no text, labels, borders, grid, UI, or presentation layout
- no gradient, no shadow, no floor, no texture
- large green spacing around the character
- centered safe box per frame

Style:
clean pixel art, sharp edges, 32-bit sprite style, no blur, no glow

Scale and alignment:
- character occupies 35% to 45% of frame height and width
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

Character:
{USER_CHARACTER_PROMPT}

Layout:
- one horizontal row
- 8 frames only
- final normalized output will be 2048x256
- each final frame will be 256x256
- pure chroma-key green #00FF00 background only
- no text, labels, borders, grid, UI, or presentation layout
- no gradient, no shadow, no floor, no texture
- large green spacing around the character
- centered safe box per frame

Style:
clean pixel art, sharp edges, 32-bit sprite style, no blur, no glow

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
```

### Run

```text
Image A is the canonical base character. Use it to preserve identity,
silhouette, palette, proportions, hairstyle, outfit, accessories, weapons, and scale.

Create one STRICT pixel art sprite sheet for RUN only.

Character:
{USER_CHARACTER_PROMPT}

Layout:
- one horizontal row
- 8 frames only
- final normalized output will be 2048x256
- each final frame will be 256x256
- pure chroma-key green #00FF00 background only
- no text, labels, borders, grid, UI, or presentation layout
- no gradient, no shadow, no floor, no texture
- large green spacing around the character
- centered safe box per frame

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
```

### Hurt

```text
Image A is the canonical base character. Use it to preserve identity,
silhouette, palette, proportions, hairstyle, outfit, accessories, weapons, and scale.

Create one STRICT pixel art sprite sheet for HURT only.

Character:
{USER_CHARACTER_PROMPT}

Layout:
- one horizontal row
- 8 frames only
- final normalized output will be 2048x256
- each final frame will be 256x256
- pure chroma-key green #00FF00 background only
- no text, labels, borders, grid, UI, or presentation layout
- no gradient, no shadow, no floor, no texture
- large green spacing around the character
- centered safe box per frame

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
```

---

## Executable Scripts

Use green-screen mode:

```bash
pip install -r requirements.txt
python scripts/sprite_gif_pipeline.py \
  --input-dir generated_sheets \
  --output-dir output \
  --frame-size 256 \
  --duration 110 \
  --source-bg green \
  --output-bg black \
  --green-key 0,255,0 \
  --green-tolerance 85
```

Expected input files:

```text
generated_sheets/
  idle.png
  attack.png
  run.png
  hurt.png
```

Expected output files:

```text
output/
  idle.gif
  attack.gif
  run.gif
  hurt.gif
  idle_sheet_aligned.png
  attack_sheet_aligned.png
  run_sheet_aligned.png
  hurt_sheet_aligned.png
  idle_sheet_transparent.png
  attack_sheet_transparent.png
  run_sheet_transparent.png
  hurt_sheet_transparent.png
  contact_sheet_aligned.png
  alignment_log.json
  validation_report.json
```

For legacy black-background inputs, use:

```bash
python scripts/sprite_gif_pipeline.py \
  --input-dir generated_sheets \
  --output-dir output \
  --source-bg black \
  --output-bg black
```

For auto detection, use:

```bash
python scripts/sprite_gif_pipeline.py \
  --input-dir generated_sheets \
  --output-dir output \
  --source-bg auto \
  --output-bg black
```

---

## Quality Checklist

Before final delivery:

- [ ] Source generation used pure green #00FF00.
- [ ] No presentation board.
- [ ] No labels, text, frame numbers, UI, grid, or borders.
- [ ] Four action sheets exist.
- [ ] Each sheet is horizontal.
- [ ] Green background was removed before alignment.
- [ ] Final aligned sheets are exact `2048x256`.
- [ ] Final GIF frames are exact `256x256`.
- [ ] Final GIFs use black background unless user asks otherwise.
- [ ] GIFs are generated from aligned sheets.
- [ ] Foot baseline is stabilized where appropriate.
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
Use pure #00FF00 green background only.
```

If green removal leaves artifacts:

1. Increase `--green-tolerance` gradually, for example 85 to 100.
2. Confirm the source background is not a gradient.
3. Regenerate with stricter green-screen prompt if needed.

If GIFs are missing:

1. Do not regenerate images first.
2. Locate the existing sprite sheets.
3. Run the executable pipeline.
4. Deliver GIF links.

If alignment is poor:

1. Re-run alignment using alpha silhouette from green-screen removal.
2. Align by median bottom Y and median center X.
3. If effects distort detection, reduce effect size.
4. If the source sheet has fewer or more than 8 visible subjects, regenerate that action sheet.
