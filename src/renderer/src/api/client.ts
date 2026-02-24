import { useAppStore } from '../stores/appStore'

class ApiClient {
  private getBaseUrl(): string {
    const url = useAppStore.getState().backendUrl
    if (!url) throw new Error('Backend not ready')
    return url
  }

  async health(): Promise<{ status: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/v1/health`)
    return res.json()
  }

  async generatePreview(params: Record<string, unknown>): Promise<Blob> {
    const res = await fetch(`${this.getBaseUrl()}/api/v1/test-pattern/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    return res.blob()
  }

  async generate(params: Record<string, unknown>): Promise<{ output_path: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/v1/test-pattern/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Generation failed')
    }
    return res.json()
  }

  async batchGenerate(params: Record<string, unknown>): Promise<{ batch_id: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/v1/test-pattern/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    return res.json()
  }

  async getBatchStatus(batchId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.getBaseUrl()}/api/v1/test-pattern/batch/${batchId}/status`)
    return res.json()
  }

  getWebSocketUrl(): string {
    const base = this.getBaseUrl().replace('http', 'ws')
    return `${base}/ws/progress`
  }
}

export const apiClient = new ApiClient()
