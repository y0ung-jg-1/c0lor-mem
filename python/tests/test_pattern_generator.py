"""Tests for pattern generator core logic."""

import math
from app.core.pattern_generator import calc_rectangle, calc_circle, generate_pattern
from app.core.models import Shape


def test_calc_rectangle_50_percent():
    x, y, rw, rh = calc_rectangle(1080, 1920, 50)
    scale = math.sqrt(0.5)
    assert rw == round(1080 * scale)
    assert rh == round(1920 * scale)
    # Centered
    assert x == (1080 - rw) // 2
    assert y == (1920 - rh) // 2


def test_calc_rectangle_100_percent():
    x, y, rw, rh = calc_rectangle(1080, 1920, 100)
    assert rw == 1080
    assert rh == 1920
    assert x == 0
    assert y == 0


def test_calc_circle_50_percent():
    cx, cy, radius = calc_circle(1080, 1920, 50)
    expected_r = math.sqrt(50 * 1080 * 1920 / (100 * math.pi))
    assert cx == 540
    assert cy == 960
    assert abs(radius - expected_r) < 0.01


def test_generate_pattern_rectangle():
    img = generate_pattern(100, 100, 50, Shape.RECTANGLE, mode="L")
    assert img.size == (100, 100)
    # Center pixel should be white
    assert img.getpixel((50, 50)) == 255
    # Corner should be black
    assert img.getpixel((0, 0)) == 0


def test_generate_pattern_circle():
    img = generate_pattern(100, 100, 50, Shape.CIRCLE, mode="L")
    assert img.size == (100, 100)
    # Center pixel should be white
    assert img.getpixel((50, 50)) == 255
    # Corner should be black
    assert img.getpixel((0, 0)) == 0
