## Why

MultiYou 需要一个端到端可运行的最小可行产品（MVP），验证核心价值：用户通过照片创建像素风数字分身并与之对话。当前项目只有设计文档，没有任何可运行代码。Phase 1 将构建从引导流程到分身聊天的完整闭环，优先覆盖 Windows 平台。

## What Changes

- 新建 Electron + Vue3 + Vite + Pinia 前端桌面应用骨架
- 新建 FastAPI + SQLAlchemy + SQLite 后端服务
- 实现Electron 主进程 spawn Python 子进程，含健康检查与进程生命周期管理
- 实现用户注册/登录（JWT + bcrypt），本地账户系统
- 实现首次启动 6 步引导向导（欢迎→注册→模型配置→照片裁剪→人格→完成）
- 实现统一 OpenAI 兼容模型调用层（DeepSeek 默认云端 + Ollama 本地 + 自定义）
- 实现模型配置 CRUD 及连通性测试
- 实现 keyring OS 级 API Key 安全存储
- 实现前端 vue-cropper 手动裁剪 + 后端 Pillow 像素化头像生成
- 实现分身 CRUD（关联人格、模型、头像）
- 实现多会话聊天系统（新建会话、会话列表、标题、上下文滑动窗口）
- 实现 Electron + Python 嵌入式 Windows 打包方案

## Capabilities

### New Capabilities

- `electron-python-packaging`: Electron 主进程管理 Python 子进程的完整生命周期——spawn、健康检查轮询、进程清理、开发/生产路径切换，以及 electron-builder + extraResources 嵌入式打包
- `user-auth`: 本地用户注册/登录系统，JWT Token 认证，bcrypt 密码哈希，路由守卫
- `onboarding-wizard`: 首次启动 6 步强制引导向导，引导用户完成注册、模型配置、照片裁剪、人格设定，一键提交创建首个分身
- `model-config`: 统一 OpenAI 兼容模型调用层（OpenAICompatProvider），支持多模型提供商配置 CRUD、连通性测试、keyring API Key 安全存储
- `avatar-image`: 前端 vue-cropper 手动裁剪照片 + 后端 Pillow 像素化处理生成头像，支持预览
- `avatar-management`: 分身 CRUD（创建、列表、详情），关联人格模板与模型配置
- `chat-system`: 多会话对话系统——新建/切换/列表会话，上下文滑动窗口（最近 20 条），通过统一模型层发送请求，对话持久化

### Modified Capabilities

（无已有 capability，全部为新建）

## Impact

- **新增前端依赖**：Vue 3, Pinia, vue-cropper@next, axios, vue-router, Electron, electron-builder, Vite
- **新增后端依赖**：FastAPI, uvicorn, SQLAlchemy, Pillow, httpx, python-jose, passlib[bcrypt], keyring, python-multipart
- **数据库**：新建 SQLite 数据库，含 user / persona / model / avatar / session / chat_log 六张表
- **文件系统**：assets/avatar/ 存储生成的像素头像，data/ 存储 SQLite 数据库文件
- **网络端口**：后端占用 localhost:8000
- **OS 集成**：Windows Credential Manager（keyring 存储 API Key）
- **打包产物**：Windows NSIS 安装包，含嵌入式 Python (~15MB)
