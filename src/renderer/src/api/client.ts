import { useAppStore } from '../stores/appStore'
import type {
  GenerateRequest,
  PreviewRequest,
  BatchRequest,
  BatchStatus,
  BatchResponse,
  HealthResponse,
  GenerateResponse,
} from '../types/api'

class ApiClient {
  private getBackend(): { baseUrl: string; token: string } {
    const { backendUrl, backendToken } = useAppStore.getState()
    if (!backendUrl || !backendToken) throw new Error('Backend not ready')
    return { baseUrl: backendUrl, token: backendToken }
  }

  private async requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
    const { baseUrl, token } = this.getBackend()
    const headers = new Headers(init.headers)
    headers.set('X-C0lor-Mem-Token', token)

    const res = await fetch(`${baseUrl}${path}`, { ...init, headers })

    const contentType = res.headers.get('content-type') || ''
    let body: unknown
    if (contentType.includes('application/json')) {
      try {
        body = await res.json()
      } catch {
        body = null
      }
    } else {
      try {
        body = await res.text()
      } catch {
        body = null
      }
    }

    if (!res.ok) {
      const detail =
        typeof body === 'object' && body && 'detail' in body
          ? (body as { detail?: unknown }).detail
          : null
      throw new Error(typeof detail === 'string' ? detail : 'Request failed')
    }

    return body as T
  }

  private async requestBlob(path: string, init: RequestInit = {}): Promise<Blob> {
    const { baseUrl, token } = this.getBackend()
    const headers = new Headers(init.headers)
    headers.set('X-C0lor-Mem-Token', token)

    const res = await fetch(`${baseUrl}${path}`, { ...init, headers })
    if (!res.ok) {
      let detail: string | null = null
      try {
        const err = (await res.json()) as { detail?: unknown }
        if (typeof err.detail === 'string') detail = err.detail
      } catch {
        // Ignore parse errors
      }
      throw new Error(detail || 'Request failed')
    }
    return res.blob()
  }

  async health(): Promise<HealthResponse> {
    return this.requestJson('/api/v1/health')
  }

  async generatePreview(params: PreviewRequest): Promise<Blob> {
    return this.requestBlob('/api/v1/test-pattern/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
  }

  async generate(params: GenerateRequest): Promise<GenerateResponse> {
    return this.requestJson('/api/v1/test-pattern/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
  }

  async batchGenerate(params: BatchRequest): Promise<BatchResponse> {
    return this.requestJson('/api/v1/test-pattern/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
  }

  async getBatchStatus(batchId: string): Promise<BatchStatus> {
    return this.requestJson(`/api/v1/test-pattern/batch/${batchId}/status`)
  }

  getWebSocketUrl(): string {
    const { baseUrl, token } = this.getBackend()
    const u = new URL(baseUrl)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/ws/progress'
    u.searchParams.set('token', token)
    return u.toString()
  }
}

export const apiClient = new ApiClient()
