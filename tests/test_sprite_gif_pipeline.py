import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sprite_gif_pipeline.py"
spec = importlib.util.spec_from_file_location("sprite_gif_pipeline", MODULE_PATH)
sprite_gif_pipeline = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(sprite_gif_pipeline)


def test_rgb_distance_does_not_overflow_for_far_pixels():
    rgb = np.array([[[0, 0, 0], [255, 255, 255], [0, 255, 0]]], dtype=np.uint8)

    dist = sprite_gif_pipeline.rgb_distance(rgb, (0, 255, 0))

    assert dist[0, 0] == 255
    assert dist[0, 1] > 300
    assert dist[0, 2] == 0


def test_chroma_key_only_makes_green_pixels_transparent():
    image = Image.new("RGBA", (3, 1))
    image.putdata([
        (0, 255, 0, 255),
        (0, 0, 0, 255),
        (255, 255, 255, 255),
    ])

    keyed = sprite_gif_pipeline.chroma_key_to_alpha(image, tolerance=85)
    alpha = np.array(keyed)[:, :, 3]

    assert alpha[0, 0] == 0
    assert alpha[0, 1] == 255
    assert alpha[0, 2] == 255


def test_auto_source_detects_green_background_but_not_black():
    green = Image.new("RGBA", (10, 10), (0, 255, 0, 255))
    black = Image.new("RGBA", (10, 10), (0, 0, 0, 255))

    green_keyed = sprite_gif_pipeline.frame_to_working_alpha(green, "auto", (0, 255, 0), 85, 8)
    black_keyed = sprite_gif_pipeline.frame_to_working_alpha(black, "auto", (0, 255, 0), 85, 8)

    assert np.array(green_keyed)[:, :, 3].min() == 0
    assert np.array(black_keyed)[:, :, 3].min() == 255
