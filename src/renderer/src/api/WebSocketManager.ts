/**
 * WebSocket Manager - encapsulates WebSocket connection lifecycle.
 * Replaces module-level variables with a singleton class.
 */

import { useAppStore } from '../stores/appStore'
import { CONFIG } from '../config/constants'
import type { BatchStatus } from '../types/api'

export interface BatchProgress extends BatchStatus {
  type: 'batch_progress'
}

type ProgressHandler = (progress: BatchProgress) => void

/**
 * Manages WebSocket connection with automatic reconnection.
 */
export class WebSocketManager {
  private ws: WebSocket | null = null
  private handlers: Set<ProgressHandler> = new Set()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private shouldReconnect = true

  private static instance: WebSocketManager | null = null

  private constructor() {}

  /**
   * Get the singleton instance.
   */
  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager()
    }
    return WebSocketManager.instance
  }

  /**
   * Build WebSocket URL from current app state.
   */
  private buildWsUrl(): string | null {
    const { backendUrl, backendToken } = useAppStore.getState()
    if (!backendUrl || !backendToken) return null

    const u = new URL(backendUrl)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/ws/progress'
    u.searchParams.set('token', backendToken)
    return u.toString()
  }

  /**
   * Connect to the WebSocket server.
   * Does nothing if already connected or connecting.
   */
  connect(): void {
    this.shouldReconnect = true
    const wsUrl = this.buildWsUrl()
    if (!wsUrl) return

    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    this.ws = new WebSocket(wsUrl)

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as BatchProgress
        if (data.type === 'batch_progress') {
          this.handlers.forEach((h) => h(data))
        }
      } catch {
        // Ignore invalid messages
      }
    }

    this.ws.onclose = () => {
      if (!this.shouldReconnect) return
      // Reconnect after delay
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
      this.reconnectTimer = setTimeout(() => this.connect(), CONFIG.WEBSOCKET.RECONNECT_DELAY_MS)
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * Subscribe to batch progress updates.
   * @param handler - Callback function for progress updates
   * @returns Unsubscribe function
   */
  subscribe(handler: ProgressHandler): () => void {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  /**
   * Send a cancel command for a batch job.
   */
  sendCancel(batchId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(`cancel:${batchId}`)
    }
  }
}

// Export singleton getter for convenience
export const getWebSocketManager = (): WebSocketManager => WebSocketManager.getInstance()
