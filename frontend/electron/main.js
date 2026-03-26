const { app, BrowserWindow, dialog } = require('electron')
const path = require('path')
const BackendManager = require('./backend-manager')

const backend = new BackendManager()
let mainWindow = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    show: false
  })

  const isDev = !app.isPackaged
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../vue-app/dist/index.html'))
  }

  mainWindow.once('ready-to-show', () => mainWindow.show())
}

app.whenReady().then(async () => {
  try {
    backend.start()
    await backend.waitForReady()
    createWindow()
  } catch (err) {
    dialog.showErrorBox(
      'MultiYou 启动失败',
      `后端服务无法启动，请检查 Python 环境。\n\n错误信息：${err.message}`
    )
    app.quit()
  }
})

app.on('before-quit', () => {
  backend.stop()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
