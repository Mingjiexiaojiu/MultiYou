# Step 06 — 分身管理系统

> **目标**：实现分身（Avatar）的完整生命周期管理，包括创建、编辑、删除、列表展示，以及人格配置和模型绑定的管理。

> **前置依赖**：Step 04（AI 模型接入）、Step 05（像素分身生成）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 分身 CRUD API | 完整的分身增删改查接口 |
| 人格 CRUD API | 人格模板管理 |
| 分身管理页面 | 卡片列表 + 详情编辑 |
| 分身创建向导 | 快速创建新分身（复用引导向导中的组件） |
| Pinia avatar store | 分身状态管理 |

---

## 二、数据模型关系

```text
User (1)
 ├── ModelConfig (N)      ← 多个 AI 模型配置
 ├── Persona (N)          ← 多个人格模板
 └── Avatar (N)           ← 多个分身
      ├── → Persona (1)   ← 绑定一个人格
      ├── → ModelConfig (1) ← 绑定一个模型
      └── → Skills (N)    ← 装配多个技能（Step 08）
```

### 2.1 Avatar 完整字段

```python
class Avatar(Base):
    __tablename__ = "avatars"

    id          = Column(String, primary_key=True)
    user_id     = Column(String, ForeignKey("users.id"), nullable=False)
    name        = Column(String(100), nullable=False)
    image_path  = Column(String(255))        # 像素形象目录
    persona_id  = Column(String, ForeignKey("personas.id"))
    model_id    = Column(String, ForeignKey("model_configs.id"))
    status      = Column(String(20), default="idle")  # idle / active / archived
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, onupdate=datetime.utcnow)
```

### 2.2 Persona 完整字段

```python
class Persona(Base):
    __tablename__ = "personas"

    id            = Column(String, primary_key=True)
    user_id       = Column(String, ForeignKey("users.id"), nullable=False)
    name          = Column(String(100), nullable=False)
    description   = Column(Text)           # 人格概述（展示用）
    system_prompt = Column(Text)           # 实际发送给 LLM 的 System Prompt
    is_template   = Column(Boolean, default=False)  # 是否为预设模板
    created_at    = Column(DateTime, default=datetime.utcnow)
```

---

## 三、预设人格模板

系统内置常用人格模板，用户可直接选用或基于模板自定义：

| 名称 | 描述 | System Prompt 摘要 |
|:---|:---|:---|
| 📚 学习助手 | 帮你整理知识、答疑解惑 | 你是一个耐心的学习导师，擅长用简洁的方式解释复杂概念... |
| 💼 工作助手 | 文档撰写、邮件处理 | 你是一个高效的工作助理，擅长起草专业文档... |
| 💻 编程助手 | 代码生成、Debug | 你是一个资深程序员，擅长多种编程语言... |
| 📊 数据分析 | 数据处理、报告生成 | 你是一个数据分析专家，擅长从数据中提取洞察... |
| 💬 闲聊伙伴 | 日常陪伴、情绪支持 | 你是一个温暖的朋友，善于倾听和鼓励... |

---

## 四、后端 API 设计

### 4.1 分身 API

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | `/api/avatars` | 获取当前用户所有分身 |
| GET | `/api/avatars/{id}` | 获取分身详情（含 persona、model 信息） |
| POST | `/api/avatars` | 创建新分身 |
| PUT | `/api/avatars/{id}` | 更新分身信息 |
| DELETE | `/api/avatars/{id}` | 删除分身（含关联的会话、Sprite 文件） |
| PUT | `/api/avatars/{id}/persona` | 更换分身人格 |
| PUT | `/api/avatars/{id}/model` | 更换分身绑定的模型 |
| PUT | `/api/avatars/{id}/status` | 切换状态（idle / active / archived） |
| PUT | `/api/avatars/reorder` | 调整分身排序 |

### 4.2 人格 API

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | `/api/personas` | 获取所有人格（含系统模板 + 用户自定义） |
| POST | `/api/personas` | 创建自定义人格 |
| PUT | `/api/personas/{id}` | 编辑人格 |
| DELETE | `/api/personas/{id}` | 删除人格（有分身绑定时禁止） |

### 4.3 创建分身请求

```json
// POST /api/avatars
{
  "name": "小知",
  "persona_id": "persona_uuid",      // 选择已有人格
  "model_id": "model_uuid",          // 选择已有模型
  "image": "<multipart file>"        // 上传照片（触发像素化生成）
}

// 或使用默认头像
{
  "name": "小知",
  "persona_id": "persona_uuid",
  "model_id": "model_uuid",
  "use_default_image": true
}
```

### 4.4 分身详情响应

```json
{
  "id": "avatar_uuid",
  "name": "小知",
  "status": "idle",
  "image_url": "/api/avatars/avatar_uuid/sprites/idle.png",
  "persona": {
    "id": "persona_uuid",
    "name": "学习助手",
    "description": "帮你整理知识、答疑解惑"
  },
  "model": {
    "id": "model_uuid",
    "provider": "deepseek",
    "model_name": "deepseek-chat"
  },
  "sprites": {
    "idle": "/api/avatars/avatar_uuid/sprites/idle.png",
    "walk": "/api/avatars/avatar_uuid/sprites/walk.png",
    "talk": "/api/avatars/avatar_uuid/sprites/talk.png"
  },
  "created_at": "2026-03-27T..."
}
```

---

## 五、前端设计

### 5.1 页面结构

| 路由 | 页面 | 说明 |
|:---|:---|:---|
| `/` | DashboardPage.vue | 主页——分身卡片网格 |
| `/avatars/create` | AvatarCreatePage.vue | 创建新分身（可复用引导向导组件） |
| `/avatars/{id}` | AvatarDetailPage.vue | 分身详情 & 编辑 |

### 5.2 分身卡片 UI

```text
┌───────────────────────┐
│   ┌──────┐            │
│   │ 像素  │  小知       │
│   │ 形象  │  学习助手   │
│   └──────┘            │
│                       │
│  🤖 DeepSeek Chat     │
│  📚 擅长学习辅导       │
│                       │
│  [对话]  [编辑]  [···] │
└───────────────────────┘
```

### 5.3 分身详情页

```text
┌───────────────────────────────────────────┐
│  ← 返回                                   │
│                                           │
│  ┌────────┐                               │
│  │  像素   │  小知                         │
│  │  形象   │  创建于 2026-03-27            │
│  │  动画   │                              │
│  └────────┘  [更换形象]                    │
│                                           │
│  ───── 人格设定 ─────                      │
│  当前：学习助手                            │
│  描述：帮你整理知识...                     │
│  [更换人格]  [编辑]                        │
│                                           │
│  ───── AI 模型 ─────                       │
│  当前：DeepSeek Chat                      │
│  [更换模型]                               │
│                                           │
│  ───── 技能 ─────                          │
│  （Step 08 实现）                          │
│                                           │
│  [开始对话]        [删除分身]              │
└───────────────────────────────────────────┘
```

### 5.4 Pinia Avatar Store

```typescript
// frontend/src/stores/avatar.ts
interface AvatarState {
  avatars: Avatar[]
  currentAvatar: Avatar | null
  loading: boolean
}

const useAvatarStore = defineStore('avatar', {
  state: (): AvatarState => ({ ... }),
  actions: {
    async fetchAvatars() { ... },
    async createAvatar(data: CreateAvatarDTO) { ... },
    async updateAvatar(id: string, data: Partial<Avatar>) { ... },
    async deleteAvatar(id: string) { ... },
    async changePersona(avatarId: string, personaId: string) { ... },
    async changeModel(avatarId: string, modelId: string) { ... },
  },
  persist: true,
})
```

---

## 六、删除处理

删除分身时需要级联清理：

```text
删除 Avatar
  ├── 删除关联的 Session 记录
  ├── 删除关联的 ChatLog 记录
  ├── 删除 Sprite 文件目录 data/avatars/{user_id}/{avatar_id}/
  └── 删除数据库记录
```

前端需二次确认对话框，提示"此操作将同时删除所有对话记录"。

---

## 七、新增目录结构

```
backend/
├── api/
│   ├── avatars.py         # 分身 CRUD（增强）
│   └── personas.py        # 人格 CRUD
├── schemas/
│   ├── avatar.py
│   └── persona.py
└── data/
    └── templates/
        └── personas.json  # 预设人格模板

frontend/src/
├── views/
│   ├── DashboardPage.vue
│   ├── AvatarCreatePage.vue
│   └── AvatarDetailPage.vue
├── components/
│   ├── AvatarCard.vue
│   ├── PersonaSelector.vue
│   └── ModelSelector.vue
└── stores/
    └── avatar.ts
```

---

## 八、验收标准

- [ ] 主页展示所有分身卡片，像素形象正常显示
- [ ] 可创建新分身（上传头像 + 选择人格 + 选择模型）
- [ ] 分身详情页可编辑名称、更换人格、更换模型、更换形象
- [ ] 删除分身时二次确认，关联数据正确清理
- [ ] 预设人格模板可正常选用
- [ ] 可自定义人格并保存
- [ ] 分身卡片可拖拽排序
- [ ] 空状态提示"还没有分身，点击创建"
