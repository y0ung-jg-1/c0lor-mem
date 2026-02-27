/**
 * APL (Average Picture Level) calculation utilities for Canvas preview.
 *
 * RELATIONSHIP TO BACKEND:
 * This module provides floating-point calculations for Canvas-based preview rendering.
 * The backend counterpart is `python/app/core/pattern_generator.py`, which uses
 * integer-based calculations for PIL image generation.
 *
 * WHY FLOATING-POINT HERE:
 * Canvas API accepts fractional pixel values and handles sub-pixel rendering,
 * allowing for smooth preview visualization. The frontend uses these calculations
 * for the real-time preview canvas.
 *
 * WHY INTEGER IN BACKEND:
 * PIL (Pillow) requires integer coordinates for pixel-perfect image generation.
 * The backend rounds the calculations to produce exact pixel values for the
 * final output images.
 *
 * FORMULAS:
 * - Rectangle: scale = sqrt(APL/100), dimensions = screen_size * scale
 * - Circle: radius = sqrt(APL * width * height / (100 * PI))
 */

/**
 * Calculate the rectangle dimensions for a given APL percentage.
 * Rectangle maintains the screen aspect ratio.
 */
export function calcRectangle(
  screenW: number,
  screenH: number,
  aplPercent: number
): { x: number; y: number; w: number; h: number } {
  const scale = Math.sqrt(aplPercent / 100)
  const w = screenW * scale
  const h = screenH * scale
  const x = (screenW - w) / 2
  const y = (screenH - h) / 2
  return { x, y, w, h }
}

/**
 * Calculate the circle parameters for a given APL percentage.
 */
export function calcCircle(
  screenW: number,
  screenH: number,
  aplPercent: number
): { cx: number; cy: number; radius: number } {
  const radius = Math.sqrt((aplPercent * screenW * screenH) / (100 * Math.PI))
  return {
    cx: screenW / 2,
    cy: screenH / 2,
    radius,
  }
}
