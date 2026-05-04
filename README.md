# Character Sprite GIF Pipeline v3

Executable green-screen 256x256 pixel-art sprite GIF pipeline.

## What this does

This pipeline is designed for source sprite sheets generated on **pure chroma-key green #00FF00**.

Input:

```text
generated_sheets/
  idle.png
  attack.png
  run.png
  hurt.png
```

Output:

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
  validation_report.json
  alignment_log.json
```

Final normalized format:

```text
8 frames × 256x256 = 2048x256
```

## Why green screen?

Black backgrounds can confuse contour detection because pixel-art characters often use black outlines, black clothes, black hair, and dark shadows. Green-screen source sheets allow the script to:

1. remove green into alpha,
2. detect the actual character silhouette,
3. align body center and foot baseline more reliably,
4. export clean black-background GIFs.

## Install

```bash
pip install -r requirements.txt
```

## Run: green-screen source to black GIFs

```bash
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

## Legacy black-background input

```bash
python scripts/sprite_gif_pipeline.py \
  --input-dir generated_sheets \
  --output-dir output \
  --source-bg black \
  --output-bg black
```

## Auto-detect source background

```bash
python scripts/sprite_gif_pipeline.py \
  --input-dir generated_sheets \
  --output-dir output \
  --source-bg auto \
  --output-bg black
```

## Expected input names

The script expects these files by default:

```text
idle.png
attack.png
run.png
hurt.png
```

They can be any wide horizontal generated sprite sheets. The script will:

1. Split each sheet into 8 equal frames.
2. Remove green screen into alpha when `--source-bg green` or `--source-bg auto` detects green.
3. Detect the largest foreground component from the alpha silhouette.
4. Align by median center X and median bottom Y.
5. Normalize each frame to 256x256.
6. Rebuild exact 2048x256 aligned sheets.
7. Export GIFs on black background by default.

## Skill

The prompt and operating rules live at:

```text
skills/character-sprite-gif-pipeline/SKILL.md
```

Use the skill for the generation step, then use the script for deterministic post-processing and GIF export.
