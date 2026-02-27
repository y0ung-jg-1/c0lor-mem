/**
 * Format compatibility matrix for HDR modes.
 * Defines which export formats are allowed for each HDR mode.
 */

import type { HdrMode, ExportFormat } from './api'

/**
 * Allowed export formats for each HDR mode.
 * - SDR (none): all formats supported
 * - Ultra HDR: JPEG only (ISO 21496-1 gain map format)
 * - HDR10 PQ: PNG, H.264, H.265 (10-bit PQ video)
 */
export const FORMAT_BY_HDR: Record<HdrMode, readonly ExportFormat[]> = {
  none: ['png', 'jpeg', 'heif', 'h264', 'h265'],
  'ultra-hdr': ['jpeg'],
  'hdr10-pq': ['png', 'h264', 'h265'],
} as const

/**
 * Check if a format is allowed for a given HDR mode.
 */
export function isFormatAllowed(hdrMode: HdrMode, format: ExportFormat): boolean {
  return FORMAT_BY_HDR[hdrMode].includes(format)
}

/**
 * Get the first allowed format for a given HDR mode.
 * Useful for resetting format when HDR mode changes.
 */
export function getDefaultFormat(hdrMode: HdrMode): ExportFormat {
  return FORMAT_BY_HDR[hdrMode][0]
}
