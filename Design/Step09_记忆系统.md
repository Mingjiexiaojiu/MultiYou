# Step 09 — 记忆系统

> **目标**：基于向量数据库（Chroma）实现分身的长期记忆能力，让分身能记住用户偏好、重要信息，跨会话保持个性化交互。

> **前置依赖**：Step 07（对话系统）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 记忆存储服务 | 基于 Chroma 的向量存储与检索 |
| 自动记忆提取 | 对话结束后自动提取值得记住的信息 |
| 记忆注入对话 | 对话时自动检索相关记忆并注入上下文 |
| 记忆管理 API | 查看 / 删除分身的记忆 |
| 记忆管理 UI | 前端查看与管理分身记忆 |

---

## 二、记忆类型设计

| 类型 | 说明 | 示例 |
|:---|:---|:---|
| `preference` | 用户偏好 | "用户喜欢用 Python" |
| `fact` | 事实信息 | "用户是前端工程师" |
| `instruction` | 用户指令 | "回答时用中文" |
| `summary` | 对话摘要 | "讨论了 Vue 组件通信的方式" |

---

## 三、核心设计

### 3.1 Chroma 集合结构

每个分身拥有独立的 Chroma Collection：

```python
# 集合命名：avatar_{avatar_id}
collection = chroma_client.get_or_create_collection(
    name=f"avatar_{avatar_id}",
    metadata={"hnsw:space": "cosine"}
)
```

### 3.2 记忆文档结构

```python
{
    "id": "mem_uuid",
    "document": "用户是一名 Python 后端开发者，工作三年",  # 记忆内容
    "metadata": {
        "type": "fact",              # 记忆类型
        "session_id": "sess_uuid",   # 来源会话
        "avatar_id": "avatar_uuid",
        "created_at": "2026-03-27",
        "importance": 0.8,           # 重要性评分（0-1）
    }
}
```

### 3.3 记忆存储服务

```python
# backend/services/memory_store.py
import chromadb

class MemoryStore:
    def __init__(self, persist_dir: str = "data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_dir)

    def get_collection(self, avatar_id: str):
        return self.client.get_or_create_collection(f"avatar_{avatar_id}")

    async def add_memory(self, avatar_id: str, content: str,
                         memory_type: str, session_id: str,
                         importance: float = 0.5):
        collection = self.get_collection(avatar_id)
        mem_id = str(uuid4())
        collection.add(
            ids=[mem_id],
            documents=[content],
            metadatas=[{
                "type": memory_type,
                "session_id": session_id,
                "avatar_id": avatar_id,
                "created_at": datetime.utcnow().isoformat(),
                "importance": importance,
            }]
        )
        return mem_id

    async def search_memories(self, avatar_id: str, query: str,
                              n_results: int = 5) -> list[dict]:
        collection = self.get_collection(avatar_id)
        if collection.count() == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
        )
        memories = []
        for i, doc in enumerate(results["documents"][0]):
            memories.append({
                "id": results["ids"][0][i],
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return memories

    async def delete_memory(self, avatar_id: str, memory_id: str):
        collection = self.get_collection(avatar_id)
        collection.delete(ids=[memory_id])

    async def list_memories(self, avatar_id: str, limit: int = 50) -> list[dict]:
        collection = self.get_collection(avatar_id)
        if collection.count() == 0:
            return []
        results = collection.get(limit=limit, include=["documents", "metadatas"])
        return [
            {"id": results["ids"][i], "content": results["documents"][i],
             "metadata": results["metadatas"][i]}
            for i in range(len(results["ids"]))
        ]

    async def clear_avatar_memories(self, avatar_id: str):
        """删除分身时清理所有记忆"""
        self.client.delete_collection(f"avatar_{avatar_id}")
```

---

## 四、自动记忆提取

### 4.1 提取时机

每次对话结束（用户切换会话 / 关闭对话 / 5 分钟无活动）时，异步分析对话内容并提取有价值的记忆。

### 4.2 提取逻辑

```python
# backend/services/memory_extractor.py

EXTRACT_PROMPT = """分析以下对话，提取值得长期记住的信息。
返回 JSON 数组，每项包含：
- content: 记忆内容（简洁的陈述句）
- type: 类型（preference / fact / instruction / summary）
- importance: 重要性 0-1

只提取真正有价值的信息，不要提取无意义的闲聊。
如果没有值得记住的信息，返回空数组 []。

对话内容：
{conversation}
"""

async def extract_memories(
    conversation: list[dict],
    provider: OpenAICompatProvider
) -> list[dict]:
    conv_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in conversation
        if m['role'] != 'system'
    )

    result = await provider.chat([
        {"role": "system", "content": "你是一个记忆提取助手，只返回 JSON。"},
        {"role": "user", "content": EXTRACT_PROMPT.format(conversation=conv_text)},
    ])

    try:
        memories = json.loads(result)
        return [m for m in memories if isinstance(m, dict) and "content" in m]
    except json.JSONDecodeError:
        return []
```

### 4.3 去重

存储前检查是否已有相似记忆（余弦相似度 > 0.9），有则跳过或更新：

```python
async def add_memory_with_dedup(self, avatar_id, content, **kwargs):
    existing = await self.search_memories(avatar_id, content, n_results=1)
    if existing and existing[0]["distance"] < 0.1:  # cosine distance < 0.1 ≈ 相似度 > 0.9
        return None  # 跳过重复
    return await self.add_memory(avatar_id, content, **kwargs)
```

---

## 五、记忆注入对话

### 5.1 修改对话构建流程

在 Step 07 的 `build_messages` 基础上增加记忆检索：

```python
async def build_messages_with_memory(
    session_id: str,
    persona: Persona,
    user_input: str,
    avatar_id: str,
    memory_store: MemoryStore,
) -> list[dict]:
    # 1. System Prompt
    messages = [{"role": "system", "content": persona.system_prompt}]

    # 2. 检索相关记忆
    memories = await memory_store.search_memories(avatar_id, user_input, n_results=5)
    if memories:
        memory_text = "\n".join(f"- {m['content']}" for m in memories)
        messages.append({
            "role": "system",
            "content": f"以下是你记住的关于用户的信息，请在适当时候参考：\n{memory_text}"
        })

    # 3. 历史消息
    history = get_recent_messages(session_id, limit=MAX_CONTEXT_MESSAGES)
    # ...（同 Step 07）

    # 4. 用户输入
    messages.append({"role": "user", "content": user_input})

    return messages
```

### 5.2 消息结构示意

```text
[system] 你是小知，一个专注学习的助手...
[system] 以下是你记住的关于用户的信息：
         - 用户是 Python 后端开发者
         - 用户偏好用中文交流
         - 用户正在学习 Vue 3
[user]   帮我写个 Vue 组件
[assistant] ...
[user]   再加个 Props 验证
```

---

## 六、后端 API

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | `/api/avatars/{id}/memories` | 获取分身的所有记忆 |
| GET | `/api/avatars/{id}/memories/search?q=xxx` | 搜索分身记忆 |
| POST | `/api/avatars/{id}/memories` | 手动添加记忆 |
| DELETE | `/api/avatars/{id}/memories/{mem_id}` | 删除单条记忆 |
| DELETE | `/api/avatars/{id}/memories` | 清空分身所有记忆 |

---

## 七、前端设计

### 7.1 记忆管理面板（在分身详情页中）

```text
───── 记忆 (12 条) ─────

🏷️ 事实
  · 用户是 Python 后端开发者            [删除]
  · 用户工作三年                        [删除]

🏷️ 偏好
  · 用户偏好用中文交流                   [删除]
  · 喜欢简洁的代码风格                   [删除]

🏷️ 指令
  · 回答时先给结论再解释                 [删除]

🏷️ 摘要
  · 讨论了 Vue 组件通信的方式            [删除]
  · 学习了 Python 装饰器                 [删除]

[+ 手动添加记忆]  [清空所有]
```

### 7.2 对话中的记忆提示

当 AI 回复中使用了记忆信息时，可在消息旁显示小标签：

```text
小知: 你之前提到过在学 Vue 3，这个组件可以用
      Composition API 来写...

      💡 基于记忆：用户正在学习 Vue 3
```

---

## 八、新增目录结构

```
backend/
├── services/
│   ├── memory_store.py       # Chroma 记忆存储
│   └── memory_extractor.py   # 自动记忆提取
├── api/
│   └── memories.py           # 记忆管理 API
└── data/
    └── chroma/               # Chroma 持久化目录

frontend/src/
├── components/
│   └── MemoryPanel.vue       # 记忆管理面板
```

---

## 九、验收标准

- [ ] 对话结束后自动提取有价值的记忆存入 Chroma
- [ ] 后续对话中，相关记忆被检索并注入上下文
- [ ] 分身能"记住"用户之前提过的偏好和事实
- [ ] 前端可查看、搜索、删除、手动添加记忆
- [ ] 重复记忆不会被重复存储
- [ ] 删除分身时，其所有记忆被清理
- [ ] 记忆数据持久化，重启后不丢失
