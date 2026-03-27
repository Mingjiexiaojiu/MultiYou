# Step 11 — 多分身协作

> **目标**：实现多个分身之间的任务分发与协作机制，用户可以将一个复杂任务交给「分身团队」，由多个分身各司其职、协同完成。

> **前置依赖**：Step 06（分身管理）、Step 07（对话系统）、Step 08（技能系统）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 协作编排引擎 | 将任务拆分并分配给多个分身 |
| 协作会话 | 多分身参与的特殊会话类型 |
| 任务分发 UI | 选择分身团队、查看协作进度 |
| 结果聚合 | 汇总各分身输出，生成最终报告 |

---

## 二、协作模式设计

### 2.1 两种协作模式

| 模式 | 说明 | 适用场景 |
|:---|:---|:---|
| **并行模式** | 多个分身同时独立处理子任务 | 数据分析 + 写报告 + 做图表 |
| **串行模式** | 分身按顺序接力处理 | 写大纲 → 填充内容 → 润色 |

### 2.2 协作流程（并行模式）

```text
用户提交任务
  ↓
协调者（系统 / 指定分身）拆分任务
  ↓
┌──────────┬──────────┬──────────┐
│ 分身 A    │ 分身 B   │ 分身 C   │
│ 子任务 1  │ 子任务 2  │ 子任务 3 │
│ (并行)    │ (并行)   │ (并行)   │
└──────┬───┴────┬─────┴────┬─────┘
       └────────┼──────────┘
                ↓
           结果聚合
                ↓
           最终输出
```

### 2.3 协作流程（串行模式）

```text
用户提交任务
  ↓
分身 A 处理（第一阶段）
  ↓ 输出传递
分身 B 处理（第二阶段）
  ↓ 输出传递
分身 C 处理（第三阶段）
  ↓
最终输出
```

---

## 三、后端设计

### 3.1 数据模型

```python
# backend/models/collaboration.py
class Collaboration(Base):
    __tablename__ = "collaborations"

    id          = Column(String, primary_key=True)
    user_id     = Column(String, ForeignKey("users.id"), nullable=False)
    title       = Column(String(200))
    task        = Column(Text, nullable=False)         # 原始任务描述
    mode        = Column(String(20))                    # parallel / sequential
    status      = Column(String(20), default="pending") # pending / running / completed / failed
    result      = Column(Text)                          # 最终聚合结果
    created_at  = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class CollaborationTask(Base):
    __tablename__ = "collaboration_tasks"

    id               = Column(String, primary_key=True)
    collaboration_id = Column(String, ForeignKey("collaborations.id"), nullable=False)
    avatar_id        = Column(String, ForeignKey("avatars.id"), nullable=False)
    sub_task         = Column(Text, nullable=False)    # 子任务描述
    order            = Column(Integer, default=0)       # 串行模式下的顺序
    status           = Column(String(20), default="pending")
    output           = Column(Text)                     # 子任务输出
    started_at       = Column(DateTime)
    completed_at     = Column(DateTime)
```

### 3.2 协作编排引擎

```python
# backend/services/collaboration_engine.py

TASK_SPLIT_PROMPT = """你是一个任务拆分专家。
用户有以下分身可用：
{avatars_info}

用户的任务是：
{task}

请将任务拆分为子任务，每个子任务分配给最合适的分身。
返回 JSON 数组：
[
  {"avatar_id": "...", "avatar_name": "...", "sub_task": "具体子任务描述"}
]
"""

class CollaborationEngine:
    async def plan(self, task: str, avatars: list[Avatar],
                   mode: str, provider) -> list[dict]:
        """使用 LLM 拆分任务并分配分身"""
        avatars_info = "\n".join(
            f"- {a.name}：{a.persona.description}" for a in avatars
        )

        result = await provider.chat([
            {"role": "system", "content": "你是任务规划助手，只返回 JSON。"},
            {"role": "user", "content": TASK_SPLIT_PROMPT.format(
                avatars_info=avatars_info, task=task
            )},
        ])

        return json.loads(result)

    async def execute_parallel(self, collaboration_id: str):
        """并行执行所有子任务"""
        tasks = get_collaboration_tasks(collaboration_id)
        # 使用 asyncio.gather 并行执行
        results = await asyncio.gather(*[
            self._execute_single_task(task) for task in tasks
        ])
        # 聚合结果
        await self._aggregate_results(collaboration_id, results)

    async def execute_sequential(self, collaboration_id: str):
        """串行执行子任务，每步输出传递给下一步"""
        tasks = get_collaboration_tasks(collaboration_id)
        tasks.sort(key=lambda t: t.order)

        previous_output = ""
        for task in tasks:
            task.sub_task = f"{task.sub_task}\n\n前一步的输出：\n{previous_output}" if previous_output else task.sub_task
            result = await self._execute_single_task(task)
            previous_output = result
        
        await self._aggregate_results(collaboration_id, [t.output for t in tasks])

    async def _execute_single_task(self, task: CollaborationTask) -> str:
        """执行单个子任务"""
        avatar = get_avatar(task.avatar_id)
        provider = create_provider(avatar.model)

        messages = [
            {"role": "system", "content": avatar.persona.system_prompt},
            {"role": "user", "content": task.sub_task},
        ]

        result = await provider.chat(messages)
        task.output = result
        task.status = "completed"
        save(task)
        return result

    async def _aggregate_results(self, collaboration_id, results):
        """聚合所有子任务结果"""
        collab = get_collaboration(collaboration_id)
        
        summary_parts = []
        tasks = get_collaboration_tasks(collaboration_id)
        for task, result in zip(tasks, results):
            avatar = get_avatar(task.avatar_id)
            summary_parts.append(f"## {avatar.name} 的输出\n\n{result}")

        collab.result = "\n\n---\n\n".join(summary_parts)
        collab.status = "completed"
        save(collab)
```

### 3.3 API 端点

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/api/collaborations` | 创建协作任务 |
| GET | `/api/collaborations` | 获取协作历史列表 |
| GET | `/api/collaborations/{id}` | 获取协作详情（含子任务状态） |
| POST | `/api/collaborations/{id}/start` | 开始执行协作 |
| DELETE | `/api/collaborations/{id}` | 删除协作记录 |

### 3.4 创建协作请求

```json
// POST /api/collaborations
{
  "task": "帮我写一份关于 Vue 3 的技术调研报告",
  "mode": "parallel",
  "avatar_ids": ["avatar_1", "avatar_2", "avatar_3"],
  "auto_plan": true    // true: LLM 自动拆分; false: 手动分配
}

// 手动分配模式
{
  "task": "写一篇博客",
  "mode": "sequential",
  "sub_tasks": [
    {"avatar_id": "avatar_1", "sub_task": "写大纲"},
    {"avatar_id": "avatar_2", "sub_task": "填充内容"},
    {"avatar_id": "avatar_3", "sub_task": "润色和校对"}
  ]
}
```

### 3.5 协作详情响应

```json
{
  "id": "collab_uuid",
  "task": "帮我写一份关于 Vue 3 的技术调研报告",
  "mode": "parallel",
  "status": "running",
  "sub_tasks": [
    {
      "avatar": {"id": "...", "name": "小知", "image_url": "..."},
      "sub_task": "调研 Vue 3 核心特性",
      "status": "completed",
      "output": "..."
    },
    {
      "avatar": {"id": "...", "name": "小码", "image_url": "..."},
      "sub_task": "整理代码示例",
      "status": "running",
      "output": null
    }
  ],
  "result": null
}
```

---

## 四、前端设计

### 4.1 页面结构

| 路由 | 页面 | 说明 |
|:---|:---|:---|
| `/collaborate` | CollaboratePage.vue | 协作主页 |
| `/collaborate/new` | CollaborateCreatePage.vue | 创建协作任务 |
| `/collaborate/{id}` | CollaborateDetailPage.vue | 协作进度 & 结果 |

### 4.2 创建协作 UI

```text
┌─────────────────────────────────────────┐
│  🤝 创建协作任务                         │
│                                         │
│  📝 任务描述：                           │
│  ┌───────────────────────────────────┐  │
│  │ 帮我写一份关于 Vue 3 的技术调研报告 │  │
│  └───────────────────────────────────┘  │
│                                         │
│  🔄 协作模式：                           │
│  ○ 并行（各自独立完成子任务）            │
│  ● 串行（接力式处理）                    │
│                                         │
│  👥 选择分身团队：                       │
│  ☑ 📚 小知（学习助手）                   │
│  ☑ 💻 小码（编程助手）                   │
│  ☐ 💬 小聊（闲聊伙伴）                   │
│                                         │
│  📋 任务分配：                           │
│  ○ 自动分配（AI 智能拆分）               │
│  ● 手动分配                              │
│                                         │
│  [开始协作]                              │
└─────────────────────────────────────────┘
```

### 4.3 协作进度 UI

```text
┌─────────────────────────────────────────┐
│  🤝 协作任务：Vue 3 技术调研报告         │
│  模式：并行  |  状态：进行中             │
│                                         │
│  ┌─────────────────┐  ┌───────────────┐ │
│  │ 📚 小知          │  │ 💻 小码        │ │
│  │ 调研核心特性     │  │ 整理代码示例   │ │
│  │ ✅ 已完成        │  │ ⏳ 进行中...   │ │
│  │ [查看输出]       │  │               │ │
│  └─────────────────┘  └───────────────┘ │
│                                         │
│  ───── 最终结果 ─────                    │
│  （等待所有任务完成...）                  │
└─────────────────────────────────────────┘
```

### 4.4 结果展示

协作完成后，展示聚合结果，每个分身的输出用 Tab 或折叠面板分隔。

---

## 五、实时进度推送

通过 SSE 推送协作进度到前端：

```python
# backend/api/collaborations.py
@router.get("/collaborations/{id}/stream")
async def stream_collaboration_progress(id: str):
    async def event_generator():
        while True:
            collab = get_collaboration(id)
            yield f"data: {json.dumps(collab.to_dict())}\n\n"
            if collab.status in ("completed", "failed"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 六、新增目录结构

```
backend/
├── models/
│   └── collaboration.py          # Collaboration + CollaborationTask
├── services/
│   └── collaboration_engine.py   # 协作编排引擎
├── api/
│   └── collaborations.py        # 协作 API
└── schemas/
    └── collaboration.py

frontend/src/
├── views/
│   ├── CollaboratePage.vue
│   ├── CollaborateCreatePage.vue
│   └── CollaborateDetailPage.vue
├── components/
│   ├── AvatarTeamPicker.vue     # 分身团队选择
│   └── CollaborationProgress.vue # 协作进度卡片
```

---

## 七、验收标准

- [ ] 可选择多个分身组建协作团队
- [ ] 自动拆分模式能合理分配子任务
- [ ] 并行模式下多个分身同时执行
- [ ] 串行模式下输出正确传递给下一步
- [ ] 实时显示各分身的执行进度
- [ ] 所有子任务完成后自动聚合最终结果
- [ ] 可查看每个分身的独立输出
- [ ] 协作历史记录可回溯
