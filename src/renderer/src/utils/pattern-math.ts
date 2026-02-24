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
    radius
  }
}
