import { contextBridge, ipcRenderer } from 'electron'

export interface ElectronAPI {
  openDirectory: () => Promise<string | null>
  saveFile: (options: { defaultPath?: string; filters?: { name: string; extensions: string[] }[] }) => Promise<string | null>
  openPath: (path: string) => Promise<void>
  showItemInFolder: (path: string) => void
  onBackendUrl: (callback: (url: string) => void) => void
}

const api: ElectronAPI = {
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),
  openPath: (path) => ipcRenderer.invoke('shell:openPath', path),
  showItemInFolder: (path) => ipcRenderer.invoke('shell:showItemInFolder', path),
  onBackendUrl: (callback) => {
    ipcRenderer.on('python-backend-url', (_, url) => callback(url))
  }
}

if (process.contextIsolated) {
  contextBridge.exposeInMainWorld('electronAPI', api)
} else {
  // @ts-expect-error fallback for non-isolated context
  window.electronAPI = api
}
