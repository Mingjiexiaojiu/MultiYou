# Step 10 — 桌面悬浮助手（宠物形态）

> **目标**：实现桌面悬浮窗模式，让分身以像素宠物形态常驻桌面，可自主行走、表情变化、右键互动，点击打开快捷对话窗口。

> **前置依赖**：Step 05（像素分身生成）、Step 07（对话系统）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 悬浮窗口 | 无边框、透明、置顶的 Electron 窗口 |
| Sprite 动画引擎 | Canvas 渲染 sprite sheet，播放多种动画 |
| 自主行为系统 | 分身自主行走、待机、表情切换 |
| 右键菜单 | 快捷交互（对话、切换分身、设置等） |
| 快捷对话窗口 | 点击分身弹出轻量对话框 |
| 托盘图标 | 系统托盘，控制显隐和退出 |

---

## 二、Electron 悬浮窗口

### 2.1 窗口配置

```typescript
// electron/pet-window.ts
const petWindow = new BrowserWindow({
  width: 128,
  height: 128,
  frame: false,             // 无边框
  transparent: true,        // 透明背景
  alwaysOnTop: true,        // 置顶
  resizable: false,
  skipTaskbar: true,         // 不在任务栏显示
  hasShadow: false,
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,
  },
})

// 允许鼠标穿透（非角色区域）
petWindow.setIgnoreMouseEvents(true, { forward: true })
```

### 2.2 鼠标穿透处理

角色区域可交互，其他透明区域鼠标穿透：

```typescript
// 前端通知主进程：鼠标在角色上 / 不在角色上
ipcMain.on('set-mouse-passthrough', (event, passthrough: boolean) => {
  petWindow.setIgnoreMouseEvents(passthrough, { forward: true })
})
```

### 2.3 拖拽移动

```typescript
// 前端 Canvas 上监听拖拽
let dragging = false
let dragOffset = { x: 0, y: 0 }

canvas.addEventListener('mousedown', (e) => {
  dragging = true
  dragOffset = { x: e.screenX - window.screenX, y: e.screenY - window.screenY }
})

document.addEventListener('mousemove', (e) => {
  if (dragging) {
    window.electronAPI.moveWindow(e.screenX - dragOffset.x, e.screenY - dragOffset.y)
  }
})

document.addEventListener('mouseup', () => { dragging = false })
```

---

## 三、Sprite 动画引擎

### 3.1 动画状态

| 状态 | 动画 | 触发 |
|:---|:---|:---|
| `idle` | 原地待机，轻微呼吸 | 默认状态 |
| `walk` | 左右行走 | 自主行走 |
| `talk` | 嘴部动画 | 对话中 |
| `think` | 头顶冒泡 | AI 思考中 |
| `happy` | 蹦跳 | 收到好评 / 完成任务 |
| `sleep` | 闭眼 + zzz | 长时间无互动 |

### 3.2 Canvas 渲染器

```typescript
// frontend/src/components/pet/SpriteRenderer.ts
class SpriteRenderer {
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private sprites: Map<string, HTMLImageElement> = new Map()
  private currentState: string = 'idle'
  private frame: number = 0
  private frameCount: Map<string, number> = new Map()
  private fps: number = 8

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')!
  }

  async loadSprites(spriteUrls: Record<string, string>) {
    for (const [state, url] of Object.entries(spriteUrls)) {
      const img = new Image()
      img.src = url
      await new Promise(resolve => img.onload = resolve)
      this.sprites.set(state, img)
      // 根据图片宽度计算帧数（每帧 128px 宽）
      this.frameCount.set(state, img.width / 128)
    }
  }

  setState(state: string) {
    if (this.currentState !== state) {
      this.currentState = state
      this.frame = 0
    }
  }

  render() {
    const sprite = this.sprites.get(this.currentState)
    if (!sprite) return

    const frames = this.frameCount.get(this.currentState) || 1
    const frameWidth = sprite.width / frames

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
    this.ctx.drawImage(
      sprite,
      this.frame * frameWidth, 0,    // 源位置
      frameWidth, sprite.height,      // 源尺寸
      0, 0,                           // 目标位置
      this.canvas.width, this.canvas.height // 目标尺寸
    )

    this.frame = (this.frame + 1) % frames
  }

  startLoop() {
    setInterval(() => this.render(), 1000 / this.fps)
  }
}
```

---

## 四、自主行为系统

### 4.1 行为状态机

```text
         ┌─── 10秒无互动 ──→ idle
         │                     │
idle ────┤                     ├── 30秒 → walk
         │                     │
         └─── 5分钟无互动 ──→ sleep
                                │
walk ──── 到达边界 ──→ idle     │
                                │
用户点击 ──────────→ happy      │
                                │
对话中 ────────────→ talk       │
AI思考中 ──────────→ think      │
```

### 4.2 自主行走逻辑

```typescript
// frontend/src/components/pet/PetBehavior.ts
class PetBehavior {
  private position: { x: number, y: number }
  private direction: 'left' | 'right' = 'right'
  private state: string = 'idle'
  private idleTimer: number = 0
  private walkSpeed: number = 2   // 像素/帧

  update() {
    this.idleTimer++

    if (this.state === 'idle' && this.idleTimer > 30 * 8) {  // 30秒后
      this.state = 'walk'
      this.direction = Math.random() > 0.5 ? 'right' : 'left'
      this.idleTimer = 0
    }

    if (this.state === 'walk') {
      // 沿屏幕底部左右行走
      const dx = this.direction === 'right' ? this.walkSpeed : -this.walkSpeed
      this.position.x += dx

      // 碰到屏幕边界则转向或停下
      const screenWidth = screen.width
      if (this.position.x <= 0 || this.position.x >= screenWidth - 128) {
        this.state = 'idle'
        this.idleTimer = 0
      }

      // 通知主进程移动窗口
      window.electronAPI.moveWindow(this.position.x, this.position.y)
    }

    if (this.state === 'idle' && this.idleTimer > 300 * 8) {  // 5分钟后
      this.state = 'sleep'
    }
  }
}
```

---

## 五、右键菜单

```typescript
// 右键分身弹出上下文菜单
canvas.addEventListener('contextmenu', (e) => {
  e.preventDefault()
  window.electronAPI.showPetMenu()
})

// electron/main.ts
ipcMain.on('show-pet-menu', () => {
  const menu = Menu.buildFromTemplate([
    { label: '💬 打开对话', click: () => openQuickChat() },
    { label: '🔄 切换分身', submenu: avatarSubmenu },
    { type: 'separator' },
    { label: '📌 固定位置', type: 'checkbox', checked: isPinned },
    { label: '🔇 关闭自主行走', type: 'checkbox', checked: !autoWalk },
    { type: 'separator' },
    { label: '⚙️ 打开主窗口', click: () => mainWindow.show() },
    { label: '👋 隐藏宠物', click: () => petWindow.hide() },
  ])
  menu.popup()
})
```

---

## 六、快捷对话窗口

点击分身或选择「打开对话」时，在分身旁弹出一个轻量对话气泡：

### 6.1 气泡窗口

```typescript
const chatBubble = new BrowserWindow({
  width: 360,
  height: 480,
  frame: false,
  transparent: true,
  alwaysOnTop: true,
  resizable: false,
  skipTaskbar: true,
  // 定位在宠物窗口旁边
  x: petWindow.getBounds().x - 380,
  y: petWindow.getBounds().y - 400,
})
```

### 6.2 气泡 UI

```text
       ┌───────────────────────┐
       │ 小知 · 学习助手    [×] │
       │───────────────────────│
       │                       │
       │ 你: 帮我解释递归      │
       │                       │
       │ 小知: 递归是指...     │
       │                       │
       │───────────────────────│
       │ [输入消息...]    [发送] │
       └───────────────────────┘
                              △
                         ┌──────┐
                         │ 像素  │
                         │ 宠物  │
                         └──────┘
```

---

## 七、系统托盘

```typescript
// electron/tray.ts
const tray = new Tray(path.join(__dirname, 'assets/tray-icon.png'))

tray.setToolTip('MultiYou')
tray.setContextMenu(Menu.buildFromTemplate([
  { label: '显示主窗口', click: () => mainWindow.show() },
  { label: '显示/隐藏宠物', click: () => togglePetWindow() },
  { type: 'separator' },
  { label: '退出', click: () => app.quit() },
]))

// 双击托盘图标打开主窗口
tray.on('double-click', () => mainWindow.show())
```

---

## 八、IPC 通信扩展

| 通道 | 方向 | 用途 |
|:---|:---|:---|
| `move-pet-window` | 渲染 → 主 | 移动宠物窗口位置 |
| `set-mouse-passthrough` | 渲染 → 主 | 设置鼠标穿透 |
| `show-pet-menu` | 渲染 → 主 | 显示右键菜单 |
| `open-quick-chat` | 主 → 渲染 | 打开快捷对话 |
| `pet-state-change` | 主 → 渲染 | 通知宠物状态变化（如开始对话） |
| `switch-avatar` | 渲染 → 主 | 切换当前桌面分身 |

---

## 九、新增目录结构

```
electron/
├── pet-window.ts          # 宠物悬浮窗口管理
├── tray.ts                # 系统托盘
└── chat-bubble.ts         # 快捷对话气泡窗口

frontend/src/
├── views/pet/
│   └── PetView.vue        # 宠物窗口的 Vue 页面
├── views/bubble/
│   └── ChatBubble.vue     # 快捷对话窗口页面
├── components/pet/
│   ├── SpriteRenderer.ts  # Canvas 动画渲染器
│   └── PetBehavior.ts     # 自主行为系统
```

---

## 十、验收标准

- [ ] 分身以像素角色形态悬浮在桌面上
- [ ] 悬浮窗透明背景，非角色区域鼠标穿透
- [ ] 可拖拽分身移动桌面位置
- [ ] 分身自主行走，碰到屏幕边界停止
- [ ] 长时间无互动进入睡眠状态
- [ ] 右键弹出功能菜单
- [ ] 点击分身弹出快捷对话窗口
- [ ] 对话中分身有 talk 动画
- [ ] 系统托盘可控制显隐和退出
- [ ] 可切换桌面显示的分身
