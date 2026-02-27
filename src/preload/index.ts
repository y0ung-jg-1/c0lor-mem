import { contextBridge, ipcRenderer } from 'electron'
import type { BackendInfo, ElectronAPI } from '../shared/electron-api'

export type { BackendInfo, ElectronAPI } from '../shared/electron-api'

const api: ElectronAPI = {
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),
  openPath: (path) => ipcRenderer.invoke('shell:openPath', path),
  showItemInFolder: (path) => ipcRenderer.invoke('shell:showItemInFolder', path),
  onBackendInfo: (callback) => {
    const listener = (_: Electron.IpcRendererEvent, info: BackendInfo) => callback(info)
    ipcRenderer.on('python-backend-info', listener)
    return () => ipcRenderer.removeListener('python-backend-info', listener)
  },
}

if (process.contextIsolated) {
  contextBridge.exposeInMainWorld('electronAPI', api)
} else {
  // Fallback for non-isolated context
  (window as unknown as { electronAPI: ElectronAPI }).electronAPI = api
}
