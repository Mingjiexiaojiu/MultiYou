const { app } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')

class BackendManager {
  constructor() {
    this.process = null
    this.port = 8000
  }

  getPythonPath() {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'python-backend', 'python-embed', 'python.exe')
    }
    return 'python'
  }

  getBackendDir() {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'python-backend', 'backend')
    }
    return path.join(__dirname, '..', '..', 'backend')
  }

  start() {
    const pythonPath = this.getPythonPath()
    const backendDir = this.getBackendDir()

    this.process = spawn(
      pythonPath,
      ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(this.port)],
      {
        cwd: backendDir,
        stdio: ['pipe', 'pipe', 'pipe']
      }
    )

    this.process.stdout.on('data', (data) => {
      console.log('[Backend]', data.toString().trim())
    })

    this.process.stderr.on('data', (data) => {
      console.error('[Backend ERR]', data.toString().trim())
    })

    this.process.on('exit', (code) => {
      console.log(`[Backend] process exited with code ${code}`)
    })
  }

  async waitForReady(maxAttempts = 20, interval = 500) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        await this._healthCheck()
        console.log('[Backend] ready')
        return true
      } catch {
        await new Promise((r) => setTimeout(r, interval))
      }
    }
    throw new Error('Backend failed to start after maximum attempts')
  }

  _healthCheck() {
    return new Promise((resolve, reject) => {
      const req = http.get(`http://127.0.0.1:${this.port}/health`, (res) => {
        if (res.statusCode === 200) {
          resolve()
        } else {
          reject(new Error(`Unexpected status: ${res.statusCode}`))
        }
      })
      req.on('error', reject)
      req.setTimeout(400, () => {
        req.destroy()
        reject(new Error('Health check timeout'))
      })
    })
  }

  stop() {
    if (this.process) {
      this.process.kill()
      this.process = null
      console.log('[Backend] process killed')
    }
  }
}

module.exports = BackendManager
