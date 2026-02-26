import { useAppStore } from '../stores/appStore'

export interface BatchProgress {
  type: 'batch_progress'
  batch_id: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  total: number
  completed: number
  failed: number
  current_apl: number | null
}

type ProgressHandler = (progress: BatchProgress) => void

let ws: WebSocket | null = null
let handlers: Set<ProgressHandler> = new Set()
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function buildWsUrl(): string | null {
  const { backendUrl, backendToken } = useAppStore.getState()
  if (!backendUrl || !backendToken) return null

  const u = new URL(backendUrl)
  u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
  u.pathname = '/ws/progress'
  u.searchParams.set('token', backendToken)
  return u.toString()
}

export function connectWebSocket(): void {
  const wsUrl = buildWsUrl()
  if (!wsUrl) return

  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as BatchProgress
      if (data.type === 'batch_progress') {
        handlers.forEach((h) => h(data))
      }
    } catch {
      // Ignore invalid messages
    }
  }

  ws.onclose = () => {
    // Reconnect after delay
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }

  ws.onerror = () => {
    ws?.close()
  }
}

export function onBatchProgress(handler: ProgressHandler): () => void {
  handlers.add(handler)
  return () => handlers.delete(handler)
}

export function cancelBatch(batchId: string): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(`cancel:${batchId}`)
  }
}
