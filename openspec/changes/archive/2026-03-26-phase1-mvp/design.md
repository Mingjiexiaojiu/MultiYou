## Context

MultiYou 是一个桌面端 AI 分身应用，用户上传照片生成像素风头像，创建带有人格的数字分身并与之对话。当前项目处于零代码状态，仅有设计文档。Phase 1 需要从零搭建完整技术栈，交付 Windows 平台可运行的 MVP。

技术栈约束：
- 前端：Vue 3 + Pinia + Vite + Electron（桌面壳）
- 后端：FastAPI（Python）+ SQLAlchemy（同步）+ SQLite
- 模型：OpenAI 兼容协议统一接口（DeepSeek 云端默认 / Ollama 本地 / 自定义）
- 打包：Electron + 嵌入式 Python（Windows 优先）

## Goals / Non-Goals

**Goals:**
- 端到端闭环可运行：引导 → 创建分身 → 对话
- Electron 与 Python 子进程的稳定通信与生命周期管理
- 统一模型调用层支持云端和本地模型无缝切换
- 可打包为 Windows 独立安装程序
- API Key 的 OS 级安全存储

**Non-Goals:**
- macOS / Linux 平台支持（延后）
- 多分身管理（Phase 2）
- 流式响应 / SSE 推送（Phase 2）
- 技能系统 / 工具路由（Phase 2+）
- 桌面动画 / 悬浮窗（Phase 3+）
- 自动人脸检测（用户手动裁剪替代）

## Decisions

### D1: Electron spawn 子进程而非 sidecar / HTTP 独立服务

**选择**：Electron 主进程通过 `child_process.spawn` 启动 FastAPI 子进程

**替代方案**：
- (A) sidecar 模式（electron-builder sidecar plugin）：配置复杂，社区维护不活跃
- (B) 要求用户单独启动后端：用户体验差，部署复杂

**理由**：spawn 方式最直接可控。通过 `BackendManager` 类封装启动、健康检查轮询（GET /health，500ms 间隔，最多 20 次）、`before-quit` 杀进程。`app.isPackaged` 区分开发/生产环境的 Python 路径。

### D2: SQLAlchemy 同步模式而非 async

**选择**：SQLAlchemy 同步模式 + 同步 Session

**替代方案**：
- (A) SQLAlchemy async（asyncio + aiosqlite）：增加复杂度无明显收益
- (B) 原始 SQL：缺少 ORM 便利性

**理由**：SQLite 是本地嵌入式数据库，不涉及网络 I/O。async 模式增加了 `async def` 传染性和调试复杂度，对 SQLite 无性能提升。同步模式代码更简洁直观。

### D3: 前端 vue-cropper 手动裁剪而非后端自动人脸检测

**选择**：前端 vue-cropper@next 手动框选 → 发送裁剪后正方形图 → Pillow 仅做像素化

**替代方案**：
- (A) OpenCV Haar Cascade 自动检测：增加 ~50MB 依赖，准确率不稳定
- (B) dlib 检测：更重的依赖，编译困难
- (C) 云端人脸 API：引入外部依赖，隐私问题

**理由**：手动裁剪完全消除 OpenCV 依赖，用户控制裁剪结果更精确。vue-cropper 提供强制正方形、可视化裁剪框、内置预览。后端仅需 Pillow（纯 Python，零编译依赖）。

### D4: 统一 OpenAI 兼容接口而非每个模型单独适配器

**选择**：`OpenAICompatProvider` 单一类，所有模型通过 `/v1/chat/completions` 调用

**替代方案**：
- (A) 为每个提供商写独立 adapter（OllamaAdapter、DeepSeekAdapter 等）
- (B) 使用 langchain 等框架抽象

**理由**：DeepSeek、Ollama、OpenAI 等均已支持 `/v1/chat/completions` 兼容接口。单一 Provider 类通过 endpoint + model_id + api_key 参数化即可覆盖所有模型。无需框架依赖，代码量极小。

### D5: keyring 存储 API Key 而非加密文件 / 环境变量

**选择**：`keyring` 库 → Windows Credential Manager

**替代方案**：
- (A) 加密本地文件：需管理加密密钥，密钥存放本身成问题
- (B) .env 文件：明文存储，不安全
- (C) Electron safeStorage：只能在渲染进程，跨进程不便

**理由**：keyring 利用 OS 原生凭据管理器，Windows 上自动使用 Credential Manager。数据库 model 表仅存储引用标识（`apikey_deepseek`），不存明文 Key。

### D6: 嵌入式 Python 而非 PyInstaller / 系统 Python

**选择**：Windows `python-3.x-embed-amd64.zip`（~15MB）放入 electron-builder `extraResources`

**替代方案**：
- (A) PyInstaller 打包后端为 exe：启动慢（数秒解包），调试困难
- (B) 要求用户安装系统 Python：用户体验差，版本冲突风险
- (C) conda/venv 嵌入：体积过大（200MB+）

**理由**：嵌入式 Python 体积小，解压即用，可通过 `get-pip.py` 安装依赖。开发环境用系统 Python/venv，生产用嵌入式，通过 `app.isPackaged` 无缝切换。

### D7: 强制 Onboarding 向导而非可选设置

**选择**：首次启动强制 6 步引导，未完成前无法进入主页

**替代方案**：
- (A) 跳过引导直接进入，后续手动配置：用户可能遗漏关键配置
- (B) 简化为 3 步引导：模型配置和照片裁剪难以省略

**理由**：MVP 需要模型配置（API Key）+ 照片 + 人格才能创建分身。强制引导确保用户完成所有必要配置。路由守卫 `beforeEach` 检查 `onboardingDone` 状态。

## Risks / Trade-offs

- **[高风险] Electron + 嵌入式 Python 打包** → 任务 #1 最先验证。进程管理、路径切换、依赖安装均需实际测试。失败方案 B：PyInstaller 打包后端为独立 exe
- **[中风险] vue-cropper@next Vue3 兼容性** → 开发初期验证。备选：直接使用底层 cropperjs
- **[中风险] keyring 在嵌入式 Python 环境可用性** → 打包原型验证时一并测试。备选：AES 加密本地 JSON 文件
- **[低风险] DeepSeek API 可用性** → 用户可配置多个模型随时切换
- **[权衡] 同步 SQLAlchemy** → 对话请求期间 httpx 调用 LLM 会阻塞。Phase 1 可接受（单用户本地应用），Phase 2 可引入后台任务
