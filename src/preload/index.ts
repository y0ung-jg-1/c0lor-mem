import { contextBridge, ipcRenderer } from 'electron'

export interface BackendInfo {
  url: string
  token: string
}

export interface ElectronAPI {
  openDirectory: () => Promise<string | null>
  saveFile: (options: { defaultPath?: string; filters?: { name: string; extensions: string[] }[] }) => Promise<string | null>
  openPath: (path: string) => Promise<void>
  showItemInFolder: (path: string) => void
  onBackendInfo: (callback: (info: BackendInfo) => void) => () => void
}

const api: ElectronAPI = {
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),
  openPath: (path) => ipcRenderer.invoke('shell:openPath', path),
  showItemInFolder: (path) => ipcRenderer.invoke('shell:showItemInFolder', path),
  onBackendInfo: (callback) => {
    const listener = (_: Electron.IpcRendererEvent, info: BackendInfo) => callback(info)
    ipcRenderer.on('python-backend-info', listener)
    return () => ipcRenderer.removeListener('python-backend-info', listener)
  }
}

if (process.contextIsolated) {
  contextBridge.exposeInMainWorld('electronAPI', api)
} else {
  // @ts-expect-error fallback for non-isolated context
  window.electronAPI = api
}
