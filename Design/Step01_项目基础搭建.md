# Step 01 — 项目基础搭建

> **目标**：完成 Electron + Vue 3 + FastAPI 三层骨架的初始化，确保前后端能跑通、Electron 能启动并加载前端页面。

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| Electron 主进程 | 能启动窗口、加载前端页面 |
| Vue 3 前端 | 空白 SPA，能在 Electron 中正常渲染 |
| FastAPI 后端 | 健康检查接口 `/health` 可响应 |
| BackendManager | Electron 启动时自动 spawn FastAPI 子进程，并轮询健康状态 |
| 开发 & 构建脚本 | `npm run dev` / `npm run build` 一键启动 |

---

## 二、目录结构（初始）

```
MultiYou/
├── electron/
│   ├── main.ts                # Electron 主进程入口
│   ├── preload.ts             # 预加载脚本（IPC 桥接）
│   └── backend-manager.ts     # FastAPI 子进程管理
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── main.ts            # Vue 入口
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   └── stores/            # Pinia（空）
│   ├── vite.config.ts
│   └── package.json
├── backend/
│   ├── main.py                # FastAPI 入口
│   ├── requirements.txt
│   └── api/
│       └── health.py          # GET /health
├── package.json               # 根 package（Electron）
├── electron-builder.yml
└── scripts/
    ├── dev.ps1                # 一键开发启动
    └── build.ps1              # 一键打包
```

---

## 三、前端初始化

### 3.1 技术选型

| 库 | 版本建议 | 用途 |
|:---|:---|:---|
| Vue 3 | ^3.4 | 框架 |
| Vite | ^5 | 构建工具 |
| Vue Router | ^4 | 路由 |
| Pinia | ^2 | 状态管理 |
| pinia-plugin-persistedstate | ^3 | 状态持久化 |
| Element Plus | ^2 | UI 组件库 |
| axios | ^1 | HTTP 客户端 |

### 3.2 任务清单

- [ ] `npm create vue@latest` 初始化项目
- [ ] 安装 Element Plus、axios、pinia-plugin-persistedstate
- [ ] 配置 `vite.config.ts`（代理后端 `/api` → `localhost:18666`）
- [ ] 创建空路由（`/` → 首页占位）
- [ ] 创建空 Pinia store，挂载 persistedstate 插件
- [ ] 确认 `npm run dev` 能正常启动

---

## 四、后端初始化

### 4.1 技术选型

| 库 | 用途 |
|:---|:---|
| FastAPI | Web 框架 |
| uvicorn | ASGI 服务器 |
| SQLAlchemy | ORM（同步模式） |
| python-jose | JWT |
| passlib[bcrypt] | 密码哈希 |
| keyring | 系统凭据管理 |
| httpx | HTTP 客户端 |

### 4.2 任务清单

- [ ] 创建 `backend/` 目录，编写 `requirements.txt`
- [ ] 编写 `main.py`，注册 CORS 中间件（允许 Electron 前端访问）
- [ ] 创建 `GET /health` 端点，返回 `{"status": "ok"}`
- [ ] 初始化 SQLAlchemy engine + SessionLocal（SQLite：`data/multiyou.db`）
- [ ] 创建 `database.py`（引擎、会话工厂、Base）
- [ ] 确认 `uvicorn backend.main:app --port 18666` 能正常启动

### 4.3 FastAPI 启动配置

```python
# backend/main.py
app = FastAPI(title="MultiYou Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 开发阶段放开，打包后由 Electron 加载
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 五、Electron 主进程

### 5.1 任务清单

- [ ] 创建 `electron/main.ts`：创建 BrowserWindow，加载前端
- [ ] 创建 `electron/preload.ts`：暴露 `electronAPI` 到渲染进程
- [ ] 创建 `electron/backend-manager.ts`：
  - 使用 `child_process.spawn` 启动 FastAPI
  - 每 2 秒轮询 `/health`
  - 健康后通知渲染进程可以开始请求
  - 应用退出时 kill 子进程
- [ ] 配置 `electron-builder.yml`（NSIS 安装包、extraResources 包含 Python 后端）

### 5.2 BackendManager 核心逻辑

```text
应用启动
  ↓
spawn python backend/main.py --port 18666
  ↓
轮询 GET http://localhost:18666/health
  ├── 成功 → 通知前端 "backend-ready"
  └── 失败 → 重试（最多 30 次，间隔 2s）
       └── 超时 → 提示用户后端启动失败
  ↓
应用退出 → kill 子进程
```

### 5.3 IPC 通信约定

| 通道 | 方向 | 用途 |
|:---|:---|:---|
| `backend-ready` | 主进程 → 渲染进程 | 后端就绪通知 |
| `app-version` | 渲染进程 → 主进程 | 获取应用版本号 |

---

## 六、开发流程

### 6.1 开发模式

```text
1. 启动后端：uvicorn backend.main:app --port 18666 --reload
2. 启动前端：cd frontend && npm run dev
3. 启动 Electron：npm run electron:dev（加载 localhost:5173）
```

### 6.2 生产打包流程

```text
1. pip install pyinstaller && pyinstaller backend.spec
2. cd frontend && npm run build（输出到 dist/）
3. electron-builder（将 dist + 后端可执行文件打包为 NSIS 安装包）
```

---

## 七、验收标准

- [ ] `npm run dev` 一键启动后，Electron 窗口正常显示 Vue 页面
- [ ] 前端请求 `/api/health` 返回 `{"status": "ok"}`
- [ ] Electron 关闭时，FastAPI 子进程被正确终止
- [ ] SQLite 数据库文件能自动创建
