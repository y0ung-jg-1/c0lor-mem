import { app, BrowserWindow, Menu, shell } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { registerIpcHandlers } from './ipc-handlers'
import { PythonBridge } from './python-bridge'
import { logger } from './logger'

let mainWindow: BrowserWindow | null = null
let pythonBridge: PythonBridge | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,
    backgroundColor: '#141414',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow!.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    try {
      const target = new URL(details.url)
      if (target.protocol === 'http:' || target.protocol === 'https:') {
        shell.openExternal(details.url)
      }
    } catch {
      // Ignore invalid URLs
    }
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.c0lor-mem.app')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  Menu.setApplicationMenu(null)

  registerIpcHandlers()

  // Create window first so user sees UI immediately
  createWindow()

  // Start Python backend in background
  pythonBridge = new PythonBridge()
  pythonBridge
    .start()
    .then(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('python-backend-info', {
          url: pythonBridge!.getBaseUrl(),
          token: pythonBridge!.getAuthToken(),
        })
      }
    })
    .catch((err) => {
      logger.error('Failed to start Python backend:', err)
    })

  // Also send URL when renderer reloads (HMR in dev)
  if (mainWindow) {
    mainWindow.webContents.on('did-finish-load', () => {
      if (pythonBridge?.getIsRunning()) {
        mainWindow!.webContents.send('python-backend-info', {
          url: pythonBridge!.getBaseUrl(),
          token: pythonBridge!.getAuthToken(),
        })
      }
    })
  }
})

app.on('window-all-closed', () => {
  pythonBridge?.stop()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  pythonBridge?.stop()
})
