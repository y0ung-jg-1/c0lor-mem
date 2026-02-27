/**
 * WebSocket module - provides convenience functions using WebSocketManager.
 * @deprecated Use WebSocketManager directly for better control.
 */

import { WebSocketManager, getWebSocketManager } from './WebSocketManager'
import type { BatchProgress } from './WebSocketManager'

// Re-export types for backward compatibility
export type { BatchProgress }

/**
 * Connect to the WebSocket server.
 */
export function connectWebSocket(): void {
  getWebSocketManager().connect()
}

/**
 * Subscribe to batch progress updates.
 * @param handler - Callback function for progress updates
 * @returns Unsubscribe function
 */
export function onBatchProgress(handler: (progress: BatchProgress) => void): () => void {
  return getWebSocketManager().subscribe(handler)
}

/**
 * Send a cancel command for a batch job.
 */
export function cancelBatch(batchId: string): void {
  getWebSocketManager().sendCancel(batchId)
}

// Re-export WebSocketManager for direct access
export { WebSocketManager, getWebSocketManager }
