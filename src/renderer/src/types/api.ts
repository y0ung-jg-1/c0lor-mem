/**
 * Shared type definitions matching Python models.py exactly.
 * These types are used across the frontend for type safety.
 */

// Shape types
export type Shape = 'rectangle' | 'circle'

// Color space types
export type ColorSpace = 'rec709' | 'displayP3' | 'rec2020'

// HDR mode types
export type HdrMode = 'none' | 'ultra-hdr' | 'hdr10-pq'

// Export format types
export type ExportFormat = 'png' | 'jpeg' | 'heif' | 'h264' | 'h265'

// Batch status types
export type BatchStatusType = 'running' | 'completed' | 'failed' | 'cancelled'

/**
 * Request payload for single image generation.
 * Matches Python GenerateRequest model.
 */
export interface GenerateRequest {
  width: number
  height: number
  apl_percent: number
  shape: Shape
  color_space: ColorSpace
  hdr_mode: HdrMode
  hdr_peak_nits: number
  hdr_video_peak_nits: number
  export_format: ExportFormat
  output_directory: string
}

/**
 * Request payload for preview generation.
 * Matches Python PreviewRequest model.
 */
export interface PreviewRequest {
  width: number
  height: number
  apl_percent: number
  shape: Shape
}

/**
 * Request payload for batch generation.
 * Matches Python BatchRequest model.
 */
export interface BatchRequest {
  width: number
  height: number
  apl_range_start: number
  apl_range_end: number
  apl_step: number
  shape: Shape
  color_space: ColorSpace
  hdr_mode: HdrMode
  hdr_peak_nits: number
  hdr_video_peak_nits: number
  export_format: ExportFormat
  output_directory: string
}

/**
 * Batch status response.
 * Matches Python BatchStatus model.
 */
export interface BatchStatus {
  batch_id: string
  status: BatchStatusType
  total: number
  completed: number
  failed: number
  current_apl: number | null
}

/**
 * Batch creation response.
 */
export interface BatchResponse {
  batch_id: string
}

/**
 * Health check response.
 */
export interface HealthResponse {
  status: string
}

/**
 * Generate response with output path.
 */
export interface GenerateResponse {
  output_path: string
  file_size: number
}
