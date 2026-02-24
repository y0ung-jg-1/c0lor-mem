import { ChildProcess, spawn } from 'child_process'
import { createServer } from 'net'
import { join } from 'path'
import { app } from 'electron'

export class PythonBridge {
  private process: ChildProcess | null = null
  private port: number = 0
  private isRunning = false

  /**
   * Find an available port in the range 18100-18200
   */
  private findFreePort(): Promise<number> {
    return new Promise((resolve, reject) => {
      const tryPort = (port: number): void => {
        if (port > 18200) {
          reject(new Error('No free port found in range 18100-18200'))
          return
        }
        const server = createServer()
        server.listen(port, '127.0.0.1', () => {
          server.close(() => resolve(port))
        })
        server.on('error', () => tryPort(port + 1))
      }
      tryPort(18100)
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
    const venvPython = process.platform === 'win32'
      ? join(app.getAppPath(), 'python', '.venv', 'Scripts', 'python.exe')
      : join(app.getAppPath(), 'python', '.venv', 'bin', 'python')

    try {
      const fs = require('fs')
      if (fs.existsSync(venvPython)) return venvPython
    } catch { /* fall through */ }

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
  private async waitForHealth(maxRetries = 30, interval = 500): Promise<boolean> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(`http://127.0.0.1:${this.port}/api/v1/health`)
        if (response.ok) {
          console.log(`Python backend ready on port ${this.port}`)
          return true
        }
      } catch {
        // Server not ready yet
      }
      await new Promise((r) => setTimeout(r, interval))
    }
    return false
  }

  async start(): Promise<void> {
    this.port = await this.findFreePort()
    console.log(`Starting Python backend on port ${this.port}`)

    if (app.isPackaged) {
      // Production: run bundled executable with FFmpeg in PATH
      const ffmpegDir = join(process.resourcesPath, 'ffmpeg')
      const env = { ...process.env, PATH: `${ffmpegDir}${process.platform === 'win32' ? ';' : ':'}${process.env.PATH}` }
      this.process = spawn(this.getPythonPath(), ['--port', String(this.port)], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env
      })
    } else {
      // Development: run with system Python
      const pythonPath = this.getPythonPath()
      const appDir = this.getPythonAppDir()
      this.process = spawn(pythonPath, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(this.port)], {
        cwd: appDir,
        stdio: ['pipe', 'pipe', 'pipe']
      })
    }

    this.process.stdout?.on('data', (data) => {
      console.log(`[Python] ${data.toString().trim()}`)
    })

    this.process.stderr?.on('data', (data) => {
      console.log(`[Python:err] ${data.toString().trim()}`)
    })

    this.process.on('exit', (code) => {
      console.log(`Python process exited with code ${code}`)
      this.isRunning = false
    })

    const healthy = await this.waitForHealth()
    if (!healthy) {
      console.error('Python backend failed to start')
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

  getIsRunning(): boolean {
    return this.isRunning
  }
}
