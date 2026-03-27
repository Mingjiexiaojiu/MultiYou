# Step 12 — 打包与发布

> **目标**：将 MultiYou 打包为可分发的桌面安装程序，实现一键安装、开箱即用，无需用户手动配置 Python 或 Node.js 环境。

> **前置依赖**：所有功能步骤完成

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| Windows 安装包 | `.exe` NSIS 安装程序 |
| macOS 安装包 | `.dmg`（可选） |
| 自动化构建脚本 | 一键打包全流程 |
| 自动更新机制 | electron-updater（可选） |

---

## 二、打包架构总览

```text
最终安装包
├── Electron 应用
│   ├── main.js（主进程）
│   ├── preload.js
│   └── renderer/（Vue 前端构建产物）
├── Python 后端（PyInstaller 打包后的可执行文件）
│   └── backend.exe（或 backend 二进制）
└── resources/
    ├── data/（默认数据目录模板）
    └── assets/（应用图标等）
```

---

## 三、Python 后端打包

### 3.1 PyInstaller 配置

```python
# backend.spec
a = Analysis(
    ['backend/main.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        ('backend/data/templates', 'data/templates'),  # 预设模板
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'passlib.handlers.bcrypt',
        'chromadb',
        'cv2',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='backend',
    console=False,       # 无控制台窗口
)

coll = COLLECT(
    exe, a.binaries, a.zipped_data, a.datas,
    name='backend',
)
```

### 3.2 注意事项

- 确保 `opencv-python-headless` 替代 `opencv-python`（减小体积，不需要 GUI）
- Chroma 的 SQLite 相关依赖需要正确打包
- keyring 在 Windows 上依赖 `pywin32`，需包含

### 3.3 打包命令

```powershell
cd backend
pip install pyinstaller
pyinstaller backend.spec --clean
# 输出到 backend/dist/backend/
```

---

## 四、Vue 前端构建

### 4.1 构建配置

```typescript
// frontend/vite.config.ts
export default defineConfig({
  base: './',              // 相对路径（Electron 文件加载）
  build: {
    outDir: '../dist/renderer',
    emptyOutDir: true,
  },
})
```

### 4.2 构建命令

```powershell
cd frontend
npm run build
# 输出到 dist/renderer/
```

---

## 五、Electron 打包

### 5.1 electron-builder 配置

```yaml
# electron-builder.yml
appId: com.multiyou.app
productName: MultiYou
copyright: Copyright © 2026

directories:
  output: release
  buildResources: build

files:
  - electron/dist/**/*        # Electron 主进程编译产物
  - dist/renderer/**/*        # Vue 前端构建产物

extraResources:
  - from: backend/dist/backend   # PyInstaller 打包的后端
    to: backend
    filter:
      - "**/*"

win:
  target:
    - target: nsis
      arch: [x64]
  icon: build/icon.ico

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  installerIcon: build/icon.ico
  uninstallerIcon: build/icon.ico
  installerHeaderIcon: build/icon.ico
  createDesktopShortcut: true
  createStartMenuShortcut: true
  shortcutName: MultiYou

mac:
  target:
    - target: dmg
      arch: [x64, arm64]
  icon: build/icon.icns
  category: public.app-category.productivity

dmg:
  contents:
    - x: 130
      y: 220
    - x: 410
      y: 220
      type: link
      path: /Applications
```

### 5.2 BackendManager 路径适配

打包后，Python 后端的路径不再是源码目录，需要适配：

```typescript
// electron/backend-manager.ts
import { app } from 'electron'
import path from 'path'

function getBackendPath(): string {
  if (app.isPackaged) {
    // 生产环境：extraResources 中的打包后端
    return path.join(process.resourcesPath, 'backend', 'backend.exe')
  } else {
    // 开发环境：直接运行 Python
    return 'python'
  }
}

function getBackendArgs(): string[] {
  if (app.isPackaged) {
    return []  // exe 不需要额外参数
  } else {
    return ['-m', 'uvicorn', 'backend.main:app', '--port', '18666']
  }
}
```

### 5.3 数据目录

用户数据存储在系统用户目录下，而非安装目录：

```typescript
import { app } from 'electron'

const USER_DATA_DIR = app.getPath('userData')
// Windows: C:\Users\{user}\AppData\Roaming\MultiYou
// macOS:   ~/Library/Application Support/MultiYou

// 后端启动时传入数据目录
const backendProcess = spawn(getBackendPath(), [
  ...getBackendArgs(),
  '--data-dir', USER_DATA_DIR,
])
```

---

## 六、自动化构建脚本

### 6.1 一键构建脚本

```powershell
# scripts/build.ps1

Write-Host "===== Step 1: Build Python Backend =====" -ForegroundColor Cyan
Push-Location backend
pip install -r requirements.txt
pyinstaller backend.spec --clean
Pop-Location

Write-Host "===== Step 2: Build Vue Frontend =====" -ForegroundColor Cyan
Push-Location frontend
npm ci
npm run build
Pop-Location

Write-Host "===== Step 3: Build Electron App =====" -ForegroundColor Cyan
npm ci
npm run electron:build

Write-Host "===== Build Complete =====" -ForegroundColor Green
Write-Host "Output: release/" -ForegroundColor Green
```

### 6.2 开发启动脚本

```powershell
# scripts/dev.ps1

Write-Host "Starting MultiYou in development mode..." -ForegroundColor Cyan

# 启动后端
Start-Process -NoNewWindow powershell -ArgumentList @(
    "cd backend; uvicorn main:app --port 18666 --reload"
)

# 启动前端
Start-Process -NoNewWindow powershell -ArgumentList @(
    "cd frontend; npm run dev"
)

# 等待后端就绪
Start-Sleep -Seconds 3

# 启动 Electron
npm run electron:dev
```

---

## 七、安装包体积优化

| 优化项 | 说明 |
|:---|:---|
| opencv-python-headless | 替代完整 opencv-python，减少约 50MB |
| PyInstaller --exclude-module | 排除不需要的模块（tkinter 等） |
| Electron 排除 Source Map | 生产构建不输出 .map 文件 |
| 压缩 Sprite 资源 | PNG 压缩工具优化图片体积 |
| UPX 压缩（可选） | 对 PyInstaller 产物进一步压缩 |

### 预估安装包体积

| 组件 | 大小 |
|:---|:---|
| Electron 框架 | ~80MB |
| Vue 前端构建产物 | ~5MB |
| Python 后端（含依赖） | ~150MB |
| 总计 | ~235MB |

---

## 八、首次启动逻辑

```text
用户安装并启动 MultiYou
  ↓
Electron 主进程启动
  ↓
检查数据目录是否存在
  ├── 不存在 → 初始化数据目录（创建子文件夹、初始化 SQLite）
  └── 存在 → 继续
  ↓
BackendManager 启动后端
  ↓
轮询 /health 直到就绪
  ↓
加载前端页面
  ↓
前端检查登录态
  ├── 未登录 → 跳转注册 / 登录页
  └── 已登录 → 检查 onboarding 状态
       ├── 未完成 → 跳转引导向导
       └── 已完成 → 进入主页
```

---

## 九、自动更新（可选）

使用 `electron-updater` 实现自动更新：

```typescript
// electron/updater.ts
import { autoUpdater } from 'electron-updater'

autoUpdater.autoDownload = false

autoUpdater.on('update-available', (info) => {
  // 通知前端有新版本
  mainWindow.webContents.send('update-available', info.version)
})

autoUpdater.on('update-downloaded', () => {
  // 用户确认后安装
  autoUpdater.quitAndInstall()
})

// 启动时检查更新
app.on('ready', () => {
  autoUpdater.checkForUpdates()
})
```

更新服务可使用 GitHub Releases 或自建文件服务器。

---

## 十、验收标准

- [ ] `scripts/build.ps1` 一键完成全流程打包
- [ ] 生成 NSIS 安装包，可在无 Python/Node.js 的干净 Windows 上安装
- [ ] 安装后启动正常，后端自动启动，前端页面加载
- [ ] 用户数据存储在 AppData 目录，卸载后可选保留
- [ ] 安装包体积在合理范围内（< 300MB）
- [ ] 开发模式 `scripts/dev.ps1` 正常启动三层服务
- [ ] 更新后用户数据不丢失
