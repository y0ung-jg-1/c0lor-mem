import { ChildProcess, spawn } from 'child_process'
import { randomBytes } from 'crypto'
import { createServer } from 'net'
import { join } from 'path'
import { app } from 'electron'
import { logger } from './logger'
import { CONFIG } from '../shared/config'

export class PythonBridge {
  private process: ChildProcess | null = null
  private port: number = 0
  private isRunning = false
  private authToken: string

  constructor() {
    // Per-launch token used by the renderer to authenticate to the local backend.
    this.authToken = randomBytes(32).toString('hex')
  }

  /**
   * Find an available port in the configured range
   */
  private findFreePort(): Promise<number> {
    return new Promise((resolve, reject) => {
      const tryPort = (port: number): void => {
        if (port > CONFIG.PORT_RANGE.MAX) {
          reject(
            new Error(
              `No free port found in range ${CONFIG.PORT_RANGE.MIN}-${CONFIG.PORT_RANGE.MAX}`
            )
          )
          return
        }
        const server = createServer()
        server.listen(port, '127.0.0.1', () => {
          server.close(() => resolve(port))
        })
        server.on('error', () => tryPort(port + 1))
      }
      tryPort(CONFIG.PORT_RANGE.MIN)
    })
  }

  /**
   * Get the path to the Python executable
   */
  private getPythonPath(): string {
    if (app.isPackaged) {
      // In production, use bundled PyInstaller executable
      const ext = process.platform === 'win32' ? '.exe' : ''
      return join(process.resourcesPath, 'python-backend', `c0lor-mem-backend${ext}`)
    }
    // In development, prefer the project venv
    const venvPython =
      process.platform === 'win32'
        ? join(app.getAppPath(), 'python', '.venv', 'Scripts', 'python.exe')
        : join(app.getAppPath(), 'python', '.venv', 'bin', 'python')

    try {
      const fs = require('fs')
      if (fs.existsSync(venvPython)) return venvPython
    } catch {
      /* fall through */
    }

    return process.platform === 'win32' ? 'python' : 'python3'
  }

  /**
   * Get the path to the Python app directory (dev mode)
   */
  private getPythonAppDir(): string {
    return join(app.getAppPath(), 'python')
  }

  /**
   * Poll the /health endpoint until ready
   */
  private async waitForHealth(
    maxRetries = CONFIG.HEALTH_CHECK.MAX_RETRIES,
    interval = CONFIG.HEALTH_CHECK.INTERVAL_MS
  ): Promise<boolean> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(`http://127.0.0.1:${this.port}/api/v1/health`, {
          headers: { 'X-C0lor-Mem-Token': this.authToken },
        })
        if (response.ok) {
          logger.info(`Python backend ready on port ${this.port}`)
          return true
        }
      } catch {
        // Server not ready yet
      }
      await new Promise((r) => setTimeout(r, interval))
    }
    return false
  }

  private getAllowedOriginsEnv(): string {
    const origins = new Set<string>(['null'])
    const devRendererUrl = process.env['ELECTRON_RENDERER_URL']
    if (devRendererUrl) {
      try {
        origins.add(new URL(devRendererUrl).origin)
      } catch {
        // Ignore invalid URL
      }
    }
    return Array.from(origins).join(',')
  }

  private getIccProfilesDir(): string {
    if (app.isPackaged) {
      return join(process.resourcesPath, 'icc-profiles')
    }
    return join(app.getAppPath(), 'resources', 'icc-profiles')
  }

  async start(): Promise<void> {
    this.port = await this.findFreePort()
    logger.info(`Starting Python backend on port ${this.port}`)

    if (app.isPackaged) {
      // Production: run bundled executable with FFmpeg in PATH
      const ffmpegDir = join(process.resourcesPath, 'ffmpeg')
      const env = {
        ...process.env,
        PATH: `${ffmpegDir}${process.platform === 'win32' ? ';' : ':'}${process.env.PATH}`,
        C0LOR_MEM_AUTH_TOKEN: this.authToken,
        C0LOR_MEM_ALLOWED_ORIGINS: this.getAllowedOriginsEnv(),
        C0LOR_MEM_ICC_DIR: this.getIccProfilesDir(),
      }
      this.process = spawn(this.getPythonPath(), ['--port', String(this.port)], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env,
      })
    } else {
      // Development: run with system Python
      const pythonPath = this.getPythonPath()
      const appDir = this.getPythonAppDir()
      const env = {
        ...process.env,
        C0LOR_MEM_AUTH_TOKEN: this.authToken,
        C0LOR_MEM_ALLOWED_ORIGINS: this.getAllowedOriginsEnv(),
        C0LOR_MEM_ICC_DIR: this.getIccProfilesDir(),
      }
      this.process = spawn(
        pythonPath,
        ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(this.port)],
        {
          cwd: appDir,
          stdio: ['pipe', 'pipe', 'pipe'],
          env,
        }
      )
    }

    this.process.stdout?.on('data', (data) => {
      logger.info(`[Python] ${data.toString().trim()}`)
    })

    this.process.stderr?.on('data', (data) => {
      logger.error(`[Python:err] ${data.toString().trim()}`)
    })

    this.process.on('exit', (code) => {
      logger.info(`Python process exited with code ${code}`)
      this.isRunning = false
    })

    const healthy = await this.waitForHealth()
    if (!healthy) {
      logger.error('Python backend failed to start')
      this.stop()
      throw new Error('Python backend failed to start within timeout')
    }

    this.isRunning = true
  }

  stop(): void {
    if (this.process) {
      this.process.kill()
      this.process = null
      this.isRunning = false
    }
  }

  getPort(): number {
    return this.port
  }

  getBaseUrl(): string {
    return `http://127.0.0.1:${this.port}`
  }

  getAuthToken(): string {
    return this.authToken
  }

  getIsRunning(): boolean {
    return this.isRunning
  }
}
