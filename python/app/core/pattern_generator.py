"""
Core pattern generator: creates APL test pattern images.

Generates black background images with white shapes (rectangle or circle)
at specified APL (Average Picture Level) percentages.

RELATIONSHIP TO FRONTEND:
The frontend counterpart is `src/renderer/src/utils/pattern-math.ts`, which uses
floating-point calculations for Canvas-based preview rendering.

WHY INTEGER HERE:
PIL (Pillow) requires integer coordinates for pixel-perfect image generation.
This module rounds the calculations to produce exact pixel values for the
final output images.

WHY FLOATING-POINT IN FRONTEND:
Canvas API accepts fractional pixel values and handles sub-pixel rendering,
allowing for smooth preview visualization.

FORMULAS:
- Rectangle: scale = sqrt(APL/100), dimensions = screen_size * scale
- Circle: radius = sqrt(APL * width * height / (100 * PI))
"""

import math
from PIL import Image, ImageDraw
from app.core.models import Shape


def calc_rectangle(width: int, height: int, apl_percent: int) -> tuple[int, int, int, int]:
    """
    Calculate rectangle position and size for given APL.
    Returns (x, y, rect_w, rect_h) — top-left corner and dimensions.
    """
    scale = math.sqrt(apl_percent / 100.0)
    rect_w = round(width * scale)
    rect_h = round(height * scale)
    x = (width - rect_w) // 2
    y = (height - rect_h) // 2
    return x, y, rect_w, rect_h


def calc_circle(width: int, height: int, apl_percent: int) -> tuple[int, int, float]:
    """
    Calculate circle center and radius for given APL.
    Returns (cx, cy, radius).
    """
    radius = math.sqrt(apl_percent * width * height / (100.0 * math.pi))
    cx = width // 2
    cy = height // 2
    return cx, cy, radius


def generate_pattern(
    width: int,
    height: int,
    apl_percent: int,
    shape: Shape,
    mode: str = "L",
) -> Image.Image:
    """
    Generate a test pattern image.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        apl_percent: White area percentage (1-100)
        shape: 'rectangle' or 'circle'
        mode: PIL image mode ('L' for grayscale, 'RGB' for color)

    Returns:
        PIL Image with black background and white shape
    """
    img = Image.new(mode, (width, height), 0)
    draw = ImageDraw.Draw(img)

    fill = 255 if mode == "L" else (255, 255, 255)

    if shape == Shape.RECTANGLE:
        x, y, rw, rh = calc_rectangle(width, height, apl_percent)
        draw.rectangle([x, y, x + rw - 1, y + rh - 1], fill=fill)
    elif shape == Shape.CIRCLE:
        cx, cy, radius = calc_circle(width, height, apl_percent)
        r = round(radius)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)

    return img


def generate_pattern_rgba(
    width: int,
    height: int,
    apl_percent: int,
    shape: Shape,
) -> Image.Image:
    """Generate an RGB test pattern image."""
    return generate_pattern(width, height, apl_percent, shape, mode="RGB")
