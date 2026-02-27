/**
 * Application configuration constants shared across main/renderer.
 * Keep this in sync with the Python backend defaults when relevant.
 */

export const CONFIG = {
  /** Port range for Python backend */
  PORT_RANGE: { MIN: 18100, MAX: 18200 },

  /** Health check settings */
  HEALTH_CHECK: { MAX_RETRIES: 30, INTERVAL_MS: 500 },

  /** WebSocket settings */
  WEBSOCKET: { RECONNECT_DELAY_MS: 3000 },

  /** Batch job settings */
  BATCH: { MAX_JOBS: 50, MAX_AGE_SECONDS: 3600 },
} as const

