# Character Sprite GIF Pipeline v2

Executable 256x256 pixel-art sprite GIF pipeline.

## What this does

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

  contact_sheet_aligned.png
  validation_report.json
  alignment_log.json
```

Final normalized format:

```text
8 frames × 256x256 = 2048x256
```

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python scripts/sprite_gif_pipeline.py \
  --input-dir generated_sheets \
  --output-dir output \
  --frame-size 256 \
  --duration 110
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
2. Detect the largest foreground component.
3. Align by median center X and median bottom Y.
4. Normalize each frame to 256x256.
5. Rebuild exact 2048x256 aligned sheets.
6. Export GIFs.

## Skill

The prompt and operating rules live at:

```text
skills/character-sprite-gif-pipeline/SKILL.md
```

Use the skill for the generation step, then use the script for deterministic post-processing and GIF export.
