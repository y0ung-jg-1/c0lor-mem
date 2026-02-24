import { ipcMain, dialog, shell } from 'electron'

export function registerIpcHandlers(): void {
  ipcMain.handle('dialog:openDirectory', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory', 'createDirectory']
    })
    return result.canceled ? null : result.filePaths[0]
  })

  ipcMain.handle('dialog:saveFile', async (_, options: { defaultPath?: string; filters?: Electron.FileFilter[] }) => {
    const result = await dialog.showSaveDialog({
      defaultPath: options.defaultPath,
      filters: options.filters
    })
    return result.canceled ? null : result.filePath
  })

  ipcMain.handle('shell:openPath', async (_, path: string) => {
    await shell.openPath(path)
  })

  ipcMain.handle('shell:showItemInFolder', (_, path: string) => {
    shell.showItemInFolder(path)
  })
}
