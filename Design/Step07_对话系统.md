# Step 07 — 对话系统

> **目标**：实现分身的核心对话能力，支持流式回复、会话管理和聊天历史记录，让每个分身成为一个可交互的 AI 角色。

> **前置依赖**：Step 04（AI 模型接入）、Step 06（分身管理系统）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 会话管理 API | 创建 / 列表 / 删除会话 |
| 对话 API | 发送消息、流式 SSE 回复 |
| 聊天 UI | 对话气泡、流式打字效果、Markdown 渲染 |
| 分身人格注入 | 每次对话自动注入 System Prompt |
| 上下文管理 | 控制发送给 LLM 的上下文长度 |

---

## 二、数据模型

### 2.1 Session（会话）

```python
class Session(Base):
    __tablename__ = "sessions"

    id         = Column(String, primary_key=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    avatar_id  = Column(String, ForeignKey("avatars.id"), nullable=False)
    title      = Column(String(200))        # 会话标题（自动生成）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### 2.2 ChatLog（消息记录）

```python
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id         = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role       = Column(String(20))         # user / assistant / system
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 三、后端 API 设计

### 3.1 会话管理

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | `/api/sessions?avatar_id=xxx` | 获取某分身的所有会话 |
| POST | `/api/sessions` | 创建新会话 |
| GET | `/api/sessions/{id}` | 获取会话详情（含消息列表） |
| DELETE | `/api/sessions/{id}` | 删除会话（含所有消息） |
| PUT | `/api/sessions/{id}/title` | 修改会话标题 |

### 3.2 对话

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/api/chat` | 发送消息并获取回复（SSE 流式） |
| GET | `/api/sessions/{id}/messages` | 获取会话消息列表（分页） |

### 3.3 对话请求 / 响应

#### `POST /api/chat`

**请求**：

```json
{
  "session_id": "session_uuid",
  "message": "帮我解释一下什么是递归"
}
```

**响应（SSE 流式）**：

```text
Content-Type: text/event-stream

data: {"type": "start", "message_id": "msg_uuid"}
data: {"type": "delta", "content": "递归"}
data: {"type": "delta", "content": "是指"}
data: {"type": "delta", "content": "函数"}
data: {"type": "delta", "content": "调用自身"}
...
data: {"type": "done", "message_id": "msg_uuid"}
```

### 3.4 对话核心流程

```text
前端发送消息
  ↓
后端接收
  ├── 将用户消息写入 ChatLog
  ├── 查询 Avatar → 获取 Persona + ModelConfig
  ├── 构建 messages 数组：
  │   ├── [0] system: Persona.system_prompt
  │   ├── [1..N] 历史消息（最近 N 条）
  │   └── [N+1] user: 本次用户输入
  ├── 调用 OpenAICompatProvider.chat(messages, stream=True)
  ├── 流式返回每个 token（SSE）
  ├── 完成后将完整回复写入 ChatLog
  └── 自动生成 / 更新会话标题（首次对话时）
```

### 3.5 上下文窗口控制

```python
# backend/services/chat_service.py
MAX_CONTEXT_MESSAGES = 20    # 最多携带最近 20 条消息
MAX_CONTEXT_CHARS = 8000     # 最多携带 8000 字符

def build_messages(session_id: str, persona: Persona, user_input: str) -> list:
    messages = [{"role": "system", "content": persona.system_prompt}]

    # 从数据库获取历史消息（按时间正序）
    history = get_recent_messages(session_id, limit=MAX_CONTEXT_MESSAGES)

    # 按字符数截断
    total_chars = 0
    selected = []
    for msg in reversed(history):
        total_chars += len(msg.content)
        if total_chars > MAX_CONTEXT_CHARS:
            break
        selected.insert(0, {"role": msg.role, "content": msg.content})

    messages.extend(selected)
    messages.append({"role": "user", "content": user_input})

    return messages
```

### 3.6 会话标题自动生成

首条消息对话完成后，用 LLM 生成一个简短标题：

```python
async def generate_session_title(first_message: str, first_reply: str, provider) -> str:
    resp = await provider.chat([
        {"role": "system", "content": "根据以下对话生成一个简短的标题（10字以内，不要引号）"},
        {"role": "user", "content": first_message},
        {"role": "assistant", "content": first_reply[:200]},
    ])
    return resp.strip()[:50]
```

---

## 四、前端设计

### 4.1 页面结构

| 路由 | 页面 | 说明 |
|:---|:---|:---|
| `/chat/{avatarId}` | ChatPage.vue | 对话主页面 |
| — | SessionList.vue | 左侧会话列表 |
| — | ChatWindow.vue | 右侧对话窗口 |

### 4.2 对话页面布局

```text
┌──────────────┬──────────────────────────────┐
│  📚 小知      │  帮我解释递归                 │
│              │                              │
│  会话列表     │  ┌──────┐                    │
│  ─────────── │  │ 像素  │  我来解释一下递归... │
│  递归是什么？ │  │ 头像  │                    │
│  排序算法比较 │  └──────┘                    │
│  Python入门  │                              │
│              │  ┌─────────────────────────┐  │
│              │  │                         │  │
│  [+ 新会话]   │  │  你: 帮我解释递归        │  │
│              │  │  小知: 递归是指函数调用    │  │
│              │  │  自身的编程技巧...        │  │
│              │  │                         │  │
│              │  └─────────────────────────┘  │
│              │                              │
│              │  ┌────────────────────┐ [发送] │
│              │  │ 输入你的问题...      │       │
│              │  └────────────────────┘       │
└──────────────┴──────────────────────────────┘
```

### 4.3 关键前端组件

| 组件 | 说明 |
|:---|:---|
| ChatPage.vue | 对话容器，管理布局 |
| SessionList.vue | 左侧会话列表，支持新建 / 删除 / 切换 |
| ChatWindow.vue | 消息滚动区域，自动滚底 |
| MessageBubble.vue | 单条消息气泡（区分 user / assistant） |
| ChatInput.vue | 底部输入框，支持 Enter 发送、Shift+Enter 换行 |
| MarkdownRenderer.vue | AI 回复的 Markdown 渲染（代码高亮等） |

### 4.4 流式接收（SSE）

```typescript
// frontend/src/utils/sse.ts
async function streamChat(sessionId: string, message: string, onDelta: (text: string) => void) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ session_id: sessionId, message }),
  })

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value)
    for (const line of text.split('\n')) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'delta') {
          onDelta(data.content)
        }
      }
    }
  }
}
```

### 4.5 消息气泡中的分身形象

AI 回复的消息气泡左侧显示分身的像素形象（idle sprite），对话过程中切换为 talk 动画，完成后回到 idle。

---

## 五、新增目录结构

```
backend/
├── models/
│   ├── session.py
│   └── chat_log.py
├── services/
│   └── chat_service.py      # 对话核心逻辑
├── api/
│   ├── sessions.py
│   └── chat.py               # SSE 流式对话端点
└── schemas/
    ├── session.py
    └── chat.py

frontend/src/
├── views/
│   └── ChatPage.vue
├── components/chat/
│   ├── SessionList.vue
│   ├── ChatWindow.vue
│   ├── MessageBubble.vue
│   ├── ChatInput.vue
│   └── MarkdownRenderer.vue
├── utils/
│   └── sse.ts
└── stores/
    └── avatar.ts             # 增加 sessions & messages 管理
```

---

## 六、验收标准

- [ ] 可为任意分身创建新会话
- [ ] 发送消息后，AI 以流式打字效果逐字回复
- [ ] AI 回复内容正确渲染 Markdown（标题、列表、代码块等）
- [ ] 不同分身的对话风格符合各自人格设定
- [ ] 会话标题在首次对话后自动生成
- [ ] 左侧会话列表可切换、可删除
- [ ] 刷新页面后聊天历史正常恢复
- [ ] 对话过程中分身像素形象有 talk 动画
- [ ] 长对话时上下文控制正常，不超出 Token 限制
