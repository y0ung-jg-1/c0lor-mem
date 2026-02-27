export interface BackendInfo {
  url: string
  token: string
}

export interface ElectronAPI {
  openDirectory: () => Promise<string | null>
  saveFile: (options: {
    defaultPath?: string
    filters?: { name: string; extensions: string[] }[]
  }) => Promise<string | null>
  openPath: (path: string) => Promise<void>
  showItemInFolder: (path: string) => void
  onBackendInfo: (callback: (info: BackendInfo) => void) => () => void
}

