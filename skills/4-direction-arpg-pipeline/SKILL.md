# 4-Direction ARPG Pipeline

## Purpose

Create a 4-direction 2D ARPG character animation package from one character prompt.

This skill is separate from the single-direction `character-sprite-gif-pipeline`.

It is designed for 2D ARPG character sprites that need four facing directions:

```text
right = side view facing right
left  = side view facing left
up    = back view / facing away from camera
down  = front view / facing camera
```

Each direction can produce four default actions:

```text
idle
attack
run
hurt
```

Full package target:

```text
4 directions × 4 actions = 16 GIFs
```

Default final format:

```text
8 frames × 256x256 = 2048x256 aligned sprite sheet per action
```

GIFs are generated from aligned 256x256 frames.

---

## Core Lessons From Testing

The old approach failed because it generated four directions independently. That made the model redesign the character for each direction.

The improved approach is:

```text
master character first
→ direction anchors from the master
→ consistency gate
→ action generation from approved anchors
→ green-screen post-processing
→ GIF export
```

Do not start animation generation until the direction anchors look like the same character.

---

## High-Level Workflow

When the user gives a character prompt:

1. Generate `master_front.png` first.
2. Use `master_front.png` as the identity lock.
3. Generate direction anchors from the master:
   - `base_right.png`
   - `base_up.png`
   - `base_down.png`
4. Create `base_left.png` by horizontally flipping `base_right.png` by default.
5. Check character consistency across all anchors.
6. If anchors pass, generate action sprite sheets from the relevant anchor.
7. Use pose blueprints for smoother action planning.
8. Remove green background into alpha.
9. Split into 8 frames.
10. Align by silhouette center and foot baseline.
11. Normalize every frame to exact `256x256`.
12. Export black-background GIFs.

---

## Output Contract

Full output:

```text
right_idle.gif
right_attack.gif
right_run.gif
right_hurt.gif

left_idle.gif
left_attack.gif
left_run.gif
left_hurt.gif

up_idle.gif
up_attack.gif
up_run.gif
up_hurt.gif

down_idle.gif
down_attack.gif
down_run.gif
down_hurt.gif
```

Aligned sheets:

```text
right_idle_sheet_aligned.png
right_attack_sheet_aligned.png
right_run_sheet_aligned.png
right_hurt_sheet_aligned.png

left_idle_sheet_aligned.png
left_attack_sheet_aligned.png
left_run_sheet_aligned.png
left_hurt_sheet_aligned.png

up_idle_sheet_aligned.png
up_attack_sheet_aligned.png
up_run_sheet_aligned.png
up_hurt_sheet_aligned.png

down_idle_sheet_aligned.png
down_attack_sheet_aligned.png
down_run_sheet_aligned.png
down_hurt_sheet_aligned.png
```

Optional diagnostic outputs:

```text
master_front.png
base_right.png
base_left.png
base_up.png
base_down.png
contact_sheet_aligned.png
validation_report.json
alignment_log.json
```

---

## Default Strategy

Use this efficient strategy by default:

```text
master_front = generated directly
right        = generated from master_front
left         = horizontally flipped from right
up           = generated from master_front as back view
down         = generated from master_front as front view
```

Generate `left` directly only when the user explicitly needs non-mirrored asymmetry.

```text
left_mode = flip_from_right       # default
left_mode = generate_direct       # optional
```

---

## Green-Screen Source Workflow

All generation should use pure chroma-key green source background:

```text
#00FF00
```

Pipeline:

```text
source generation: pure green #00FF00
post-processing: remove green into alpha
alignment: use alpha silhouette / body contour
final output: black-background GIFs by default
```

Green-screen source images are preferred because black outlines, dark hair, dark clothing, and dark shadows should not be mistaken for background.

---

## Master Character Stage

### Purpose

Create one strongest identity reference before any direction or animation generation.

The master should be a clear front-facing neutral pose because it best preserves:

- face
- makeup
- hairstyle
- hair ornaments
- outfit
- wrist cuffs and bracelets
- jewelry
- palette
- body proportions
- chibi scale

### Master Front Prompt Template

```text
Create one canonical master character reference on a pure chroma-key green background #00FF00.

Subject:
{USER_CHARACTER_PROMPT}

View:
front view, facing camera / facing down direction in a 2D ARPG.
Neutral standing pose.
Orthographic 2D game sprite camera.

Requirements:
- one full-body character only
- no sprite sheet
- no presentation board
- no labels, no text, no UI, no grid, no frame numbers
- clean pixel art
- sharp edges
- 32-bit sprite style
- pure #00FF00 green background only
- no gradient, no shadow, no floor, no texture
- centered with large empty green space
- compact game-sprite-friendly silhouette
- character occupies about 35% to 45% of the canvas height

Identity lock:
This image is the master identity reference.
Preserve the exact same character in all later views:
hairstyle, hair color, face, makeup, outfit, jewelry, blue/gold wrist cuffs,
bracelets, ornaments, palette, proportions, and chibi scale.
```

---

## Direction Anchor Stage

Use `master_front.png` as Image A for every directional conversion.

### Right Anchor Prompt

```text
Image A is the master identity reference.
Create the same exact character from a side view facing right.

Do not redesign the character.
Only rotate the view.

Direction:
side view facing right.
Profile view.
Front of body points to screen-right.
Orthographic 2D ARPG sprite camera.

Preserve exactly:
- same silver-white hair
- same heavy stylized makeup
- same blue and gold jeweled wrist cuffs and bracelets
- same outfit colors and ornament style
- same chibi body proportions
- same jewelry and palette

Requirements:
- one full-body character only
- neutral standing pose
- pure #00FF00 green background only
- no text, no labels, no UI, no border, no grid
- no shadow, no floor, no texture
- clean pixel art, sharp edges, 32-bit sprite style
- centered, large empty green space
```

### Up Anchor Prompt

```text
Image A is the master identity reference.
Create the same exact character from a back view.

Do not redesign the character.
Only rotate the view.

Direction:
back view, facing upward / away from camera.
Face is not visible.
Show back of head, back hair, shoulders, back outfit, back jewelry, and rear silhouette.
Orthographic 2D ARPG sprite camera.

Preserve exactly:
- same silver-white hair and ornaments, adapted to back view
- same blue and gold jewelry and wrist cuffs
- same outfit colors and rear costume logic
- same chibi body proportions
- same palette and scale

Requirements:
- one full-body character only
- neutral standing pose
- pure #00FF00 green background only
- no text, no labels, no UI, no border, no grid
- no shadow, no floor, no texture
- clean pixel art, sharp edges, 32-bit sprite style
- centered, large empty green space
```

### Down Anchor Prompt

```text
Image A is the master identity reference.
Create the same exact character from a front view.

Do not redesign the character.
Only normalize and preserve the same view as a 2D ARPG down-facing anchor.

Direction:
front view, facing downward / toward camera.
Face and front outfit visible.
Orthographic 2D ARPG sprite camera.

Preserve exactly:
- same face and heavy stylized makeup
- same silver-white hair
- same blue and gold jeweled wrist cuffs and bracelets
- same outfit colors and front ornament layout
- same chibi body proportions
- same jewelry, palette, and scale

Requirements:
- one full-body character only
- neutral standing pose
- pure #00FF00 green background only
- no text, no labels, no UI, no border, no grid
- no shadow, no floor, no texture
- clean pixel art, sharp edges, 32-bit sprite style
- centered, large empty green space
```

### Left Anchor Rule

Default:

```text
base_left = horizontal flip of base_right
```

Only generate left directly if the user requires asymmetry.

---

## Direction Consistency Gate

Before generating animations, inspect the anchors.

Pass criteria:

- all directions look like the same character
- hair color is the same
- hairstyle silhouette is compatible across views
- makeup / facial style is consistent where visible
- blue/gold wrist cuffs and bracelets remain present
- outfit color palette remains consistent
- jewelry style remains consistent
- chibi body scale is similar
- character height and silhouette are close
- up view shows back, not face
- down view shows front, not side

Fail criteria:

- any direction looks like a different person
- different hairstyle or major outfit redesign
- missing key jewelry or wrist cuffs
- up view shows face
- down view becomes side view
- scale mismatch is too large

If failed, regenerate only the failed anchor using stronger language:

```text
Do not redesign the character.
Only rotate the view.
Use Image A as the exact identity lock.
Preserve hairstyle, jewelry, outfit, colors, proportions, and chibi scale.
```

Do not proceed to animation until anchors pass.

---

## Animation Generation Stage

Use the approved directional anchor as Image A.

Each generated action sheet should be:

```text
2048x256 pixel art sprite sheet, 8 frames in one horizontal row
```

The model may not output exact size, so post-processing must normalize final frames to `256x256` and final aligned sheet to `2048x256`.

---

## Universal Action Sheet Prompt Template

```text
Image A is the approved {DIRECTION} direction anchor.
Use Image A as the exact character identity reference.
Do not redesign the character.
Preserve hairstyle, face/makeup where visible, outfit, jewelry, blue/gold wrist cuffs,
bracelets, colors, proportions, and chibi scale.

Create one STRICT pixel art sprite sheet for {DIRECTION}_{ACTION} only.

Character:
{USER_CHARACTER_PROMPT}

Direction:
{DIRECTION_DESCRIPTION}

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
- body root remains near the same center point
- feet contact frames align to the same baseline
- same camera direction in all frames
- no pose drifting
- no shape distortion

Animation rule:
Follow the exact 8-frame pose blueprint below.
Do not create random poses.
Make the motion visually continuous from frame to frame.
```

---

## Pose Blueprint System

The model does not naturally understand animation fluidity. Always provide an explicit 8-frame pose blueprint.

### Idle Blueprint

Idle should be subtle. It should not look like eight different poses.

```text
Idle animation, 8 frames:
1 neutral standing pose, root centered, feet planted
2 body lowers 1 pixel, hair and cloth follow slightly
3 body lowers 2 pixels, soft breathing compression
4 hold low pose, hands and ornaments barely move
5 body rises 1 pixel, hair lags behind
6 blink if face visible; for back view use subtle hair/shoulder settle
7 return near neutral, ornaments settle
8 same as frame 1 for seamless loop

Motion rules:
- feet stay planted
- body center stays locked
- only tiny breathing motion
- no large arm or leg movement
- no effects
```

### Attack Blueprint — No Weapon

Use this when the prompt says no weapon or no blade.

```text
Attack animation, 8 frames:
1 deeper crouch, root centered, both feet planted
2 anticipation hold, torso compressed, hands pull slightly back
3 wind-up start, shoulders rotate slightly, attack hand prepares
4 wind-up peak, attack hand pulled back, hair/cloth lag
5 release, torso moves forward slightly, attack hand begins forward motion
6 impact, hand fully extends, compact impact effect attached to hand/body
7 follow-through, body overshoots slightly, effect fades
8 recovery, returns close to frame 1 stance

Effect control:
- compact punch / palm / energy impact only in frames 6 and 7
- effect size 25% to 35% of character size
- effect stays attached to hand / body
- no large outward arc
- no glow beyond character width
- no particles spreading outward
- all effects stay inside safe box

Motion rules:
- frame 1 to 4 builds energy
- frame 5 to 6 releases action
- frame 7 to 8 recovers
- avoid random pose jumps
```

### Attack Blueprint — Weapon

Use this if the character has a weapon.

```text
Attack animation, 8 frames:
1 deeper crouch, root centered, both feet planted
2 anticipation hold, weapon/hand pulls back
3 wind-up start, torso rotates slightly
4 wind-up peak, weapon/hand reaches maximum backward pose
5 attack start, weapon/hand begins forward swing
6 impact, compact slash/impact attached to weapon/hand
7 follow-through, body overshoots slightly, slash fades
8 recovery, returns close to frame 1 stance

Effect control:
- slash / impact effect only in frames 6 and 7
- effect size 25% to 35% of character size
- effect stays attached to weapon / paw / hand
- no large outward arc
- no glow beyond character width
- no particles spreading outward
- all effects stay inside safe box
```

### Run Blueprint — Side View

Use for `right_run` and direct `left_run`.

```text
Run animation, 8 frames:
1 contact pose, front foot contacts ground, rear leg extended
2 down pose, body compresses slightly, both knees bent
3 passing pose, rear foot passes under body, torso centered
4 up pose, body rises slightly, legs switch
5 opposite contact pose, opposite foot contacts ground
6 down pose, body compresses slightly
7 passing pose, opposite foot passes under body
8 up pose, returns smoothly to frame 1

Motion rules:
- root center stays stable
- contact frames share the same foot baseline
- head bob pattern is subtle: neutral, down, neutral, up, neutral, down, neutral, up
- hair and cloth follow the run motion with slight delay
- no dust unless requested
```

### Run Blueprint — Front / Back View

Use for `down_run` and `up_run`.

```text
Run animation, 8 frames:
1 left foot contact, body centered, shoulders level
2 compression, body lowers slightly
3 right foot passing under body, arms swing opposite legs
4 lift, body rises slightly
5 right foot contact, body centered
6 compression, body lowers slightly
7 left foot passing under body, arms swing opposite legs
8 lift, returns smoothly to frame 1

Direction rules:
- down direction: motion implies moving toward camera / downward
- up direction: motion implies moving away from camera / upward
- face visible only for down direction
- face not visible for up direction

Motion rules:
- body root stays near center
- feet contact frames share baseline
- avoid side-view turning
- no dust unless requested
```

### Hurt Blueprint

```text
Hurt animation, 8 frames:
1 normal ready pose
2 impact reaction, small impact spark close to body
3 recoil, body leans away from impact
4 recoil peak, strongest bend / flinch
5 fall or crouch, body lowers
6 stunned hold, tiny stars/daze marks if appropriate
7 recovery start, body rises
8 return to normal ready pose

Effect control:
- optional tiny impact spark only in frame 2
- optional tiny stars or dazed marks only around frame 6
- all effects small and close to body
- all effects stay inside safe box

Motion rules:
- recoil follows a clear arc
- do not teleport between poses
- root stays readable
- frame 8 should reconnect to idle/ready pose
```

---

## Direction Descriptions

Use these in action prompts.

### Right

```text
side view facing right.
Profile view.
Front of body points to screen-right.
Movement and attacks go toward screen-right.
```

### Left

Default is horizontal flip from right outputs.

If generated directly:

```text
side view facing left.
Profile view.
Front of body points to screen-left.
Movement and attacks go toward screen-left.
```

### Up

```text
back view, facing upward / away from camera.
Face is not visible.
Back of head, back hair, shoulders, rear outfit, and rear silhouette visible.
Movement and attacks go upward / away from camera.
```

### Down

```text
front view, facing downward / toward camera.
Face, makeup, chest/front outfit, and front jewelry visible.
Movement and attacks go downward / toward camera.
```

---

## Left Direction Generation

Default:

```text
left = horizontal flip of right
```

Important rules:

- Flip only after right-facing sheets are aligned and normalized.
- Flip both GIF frames and aligned sheets.
- Preserve exact 256x256 frame cells.
- File names should be `left_idle.gif`, `left_attack.gif`, etc.

If direct left generation is needed:

```text
left_mode = generate_direct
```

Then use the right prompts with direction changed to side view facing left.

---

## Post-Processing Requirements

After image generation:

1. Remove green screen into alpha.
2. Split sprite sheet into 8 equal frames.
3. Detect alpha silhouette.
4. Align by median body center X.
5. Align by median foot/bottom Y where appropriate.
6. Normalize each frame to `256x256`.
7. Rebuild action sheet to `2048x256`.
8. Export GIF on black background.

Do not export GIFs from raw unaligned sheets.

---

## Suggested File Layout

Expected input layout for generated action sheets:

```text
generated_sheets/
  right_idle.png
  right_attack.png
  right_run.png
  right_hurt.png

  up_idle.png
  up_attack.png
  up_run.png
  up_hurt.png

  down_idle.png
  down_attack.png
  down_run.png
  down_hurt.png
```

If `left_mode=flip_from_right`, no left source sheets are required.

Expected output:

```text
output/
  right_idle.gif
  right_attack.gif
  right_run.gif
  right_hurt.gif

  left_idle.gif
  left_attack.gif
  left_run.gif
  left_hurt.gif

  up_idle.gif
  up_attack.gif
  up_run.gif
  up_hurt.gif

  down_idle.gif
  down_attack.gif
  down_run.gif
  down_hurt.gif
```

---

## Final Response Template

If the user asks for GIFs only:

```text
[右-待機 GIF](...)
[右-攻擊 GIF](...)
[右-奔跑 GIF](...)
[右-被擊中 GIF](...)

[左-待機 GIF](...)
[左-攻擊 GIF](...)
[左-奔跑 GIF](...)
[左-被擊中 GIF](...)

[上-待機 GIF](...)
[上-攻擊 GIF](...)
[上-奔跑 GIF](...)
[上-被擊中 GIF](...)

[下-待機 GIF](...)
[下-攻擊 GIF](...)
[下-奔跑 GIF](...)
[下-被擊中 GIF](...)
```

If only testing one direction, return only that direction's GIFs.

If only testing one action, return only that GIF.

---

## Quality Checklist

### Anchor Quality

- [ ] `master_front` exists.
- [ ] `base_right` was generated from `master_front`.
- [ ] `base_up` was generated from `master_front`.
- [ ] `base_down` was generated from `master_front`.
- [ ] `base_left` was flipped from `base_right` unless direct generation requested.
- [ ] All anchors look like the same character.
- [ ] Up view shows back, not face.
- [ ] Down view shows front, not side.

### Animation Quality

- [ ] No presentation board.
- [ ] No text, labels, frame numbers, UI, grid, or borders.
- [ ] Source sheets use pure green #00FF00.
- [ ] Green background is removed before contour detection.
- [ ] Each GIF has 8 frames.
- [ ] Each GIF frame is 256x256.
- [ ] Each aligned sheet is 2048x256.
- [ ] Body center is stable.
- [ ] Foot baseline is stable where appropriate.
- [ ] Motion follows the pose blueprint.
- [ ] Action reads as a continuous animation, not random poses.
- [ ] GIFs loop correctly.

---

## Failure Recovery

### Direction Anchor Looks Like a Different Character

Regenerate only that anchor with stronger identity-lock wording:

```text
Do not redesign the character.
Only rotate the view.
Use Image A as the exact identity lock.
Preserve hairstyle, jewelry, outfit, colors, proportions, and chibi scale.
```

### Up View Shows Face

Regenerate up anchor and affected up actions:

```text
Back view only.
Face is not visible.
Facing away from camera.
Show back hair and rear outfit.
```

### Down View Becomes Side View

Regenerate down anchor and affected down actions:

```text
Front view only.
Facing camera.
Face and front outfit visible.
Do not rotate to side view.
```

### Animation Looks Like Random Poses

Regenerate the affected action with stronger blueprint wording:

```text
Follow the exact 8-frame pose blueprint.
Do not create random poses.
Each frame must transition smoothly from the previous frame.
Keep root position stable.
Keep foot contact baseline stable.
```

### Presentation Board or Labels Appear

Reject and regenerate:

```text
Do not create a presentation board.
Do not create a contact sheet.
Do not add labels, numbers, captions, UI, borders, or grids.
Create only one single horizontal animation strip.
Use pure #00FF00 green background only.
```

### Green Removal Leaves Artifacts

1. Increase green tolerance.
2. Confirm source background is flat green.
3. Regenerate with stronger `pure #00FF00 only` wording if needed.
