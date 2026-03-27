# Step 08 — 技能系统

> **目标**：实现可插拔的技能（Tool）系统，让分身在对话中能调用外部工具（联网搜索、文件处理、代码执行等），基于 LLM Function Calling 机制。

> **前置依赖**：Step 07（对话系统）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 技能注册中心 | 统一管理所有可用技能的注册与发现 |
| Function Calling 集成 | 在对话流中集成工具调用循环 |
| 内置技能集 | 联网搜索、文件读写、代码执行、系统时间等 |
| 技能装配 UI | 为分身勾选 / 取消技能 |
| 技能调用可视化 | 对话中展示工具调用过程 |

---

## 二、核心设计：技能抽象

### 2.1 技能接口

```python
# backend/skills/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class SkillBase(ABC):
    """所有技能的基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """技能的唯一标识"""

    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述（会传给 LLM）"""

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema 格式的参数定义"""

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行技能，返回文本结果"""
```

### 2.2 技能示例

```python
# backend/skills/builtin/web_search.py
class WebSearchSkill(SkillBase):
    name = "web_search"
    description = "搜索互联网获取最新信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str) -> str:
        # 调用搜索 API
        results = await self._search(query)
        return f"搜索结果：\n{results}"
```

### 2.3 技能注册中心

```python
# backend/skills/registry.py
class SkillRegistry:
    _skills: dict[str, SkillBase] = {}

    @classmethod
    def register(cls, skill: SkillBase):
        cls._skills[skill.name] = skill

    @classmethod
    def get(cls, name: str) -> SkillBase | None:
        return cls._skills.get(name)

    @classmethod
    def get_tools_schema(cls, skill_names: list[str]) -> list[dict]:
        """生成 OpenAI Function Calling 格式的 tools 数组"""
        tools = []
        for name in skill_names:
            skill = cls._skills.get(name)
            if skill:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": skill.name,
                        "description": skill.description,
                        "parameters": skill.parameters,
                    }
                })
        return tools

# 启动时注册所有内置技能
SkillRegistry.register(WebSearchSkill())
SkillRegistry.register(FileReadSkill())
SkillRegistry.register(CodeExecuteSkill())
SkillRegistry.register(CurrentTimeSkill())
```

---

## 三、Function Calling 集成

### 3.1 修改对话流程

在 Step 07 的基础上，对话流程增加 **工具调用循环**：

```text
用户消息
  ↓
构建 messages + tools
  ↓
调用 LLM（带 tools 参数）
  ↓
LLM 返回
  ├── 普通文本 → 直接返回给用户
  └── tool_calls → 进入工具调用循环
       ├── 解析 tool_calls
       ├── 执行对应技能
       ├── 将执行结果作为 tool 消息加入 messages
       ├── 再次调用 LLM
       └── 重复直到 LLM 返回普通文本（最多 5 轮）
```

### 3.2 对话服务升级

```python
# backend/services/chat_service.py
async def chat_with_tools(
    messages: list[dict],
    provider: OpenAICompatProvider,
    avatar_skills: list[str],
    stream: bool = True,
) -> AsyncIterator:
    tools = SkillRegistry.get_tools_schema(avatar_skills)

    for _ in range(5):  # 最多 5 轮工具调用
        response = await provider.chat_completion(
            messages=messages,
            tools=tools if tools else None,
            stream=False,  # 工具调用阶段不流式
        )

        choice = response["choices"][0]
        message = choice["message"]

        if message.get("tool_calls"):
            # 有工具调用
            messages.append(message)

            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])

                skill = SkillRegistry.get(func_name)
                result = await skill.execute(**func_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                })

                # 通过 SSE 通知前端工具调用进度
                yield {"type": "tool_call", "name": func_name, "args": func_args}
                yield {"type": "tool_result", "name": func_name, "result": result[:200]}
        else:
            # 无工具调用，流式返回最终回复
            final_messages = messages + [{"role": "user", "content": ""}]
            # 用最终的 messages 做流式调用
            async for token in provider.chat(messages, stream=True):
                yield {"type": "delta", "content": token}
            return

    # 超过最大轮次
    yield {"type": "delta", "content": "（工具调用已达上限，已停止）"}
```

### 3.3 Provider 升级

在 `OpenAICompatProvider` 中增加支持 `tools` 参数的 `chat_completion` 方法：

```python
async def chat_completion(self, messages, tools=None, stream=False):
    payload = {
        "model": self.model,
        "messages": messages,
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{self.api_base}/chat/completions",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
```

---

## 四、内置技能清单

| 技能名 | 说明 | 安全级别 |
|:---|:---|:---|
| `current_time` | 获取当前日期时间 | 安全 |
| `web_search` | 联网搜索（调用搜索 API） | 安全 |
| `file_read` | 读取本地文件内容 | 需确认 |
| `file_write` | 写入本地文件 | 需确认 |
| `code_execute` | 执行 Python 代码片段 | 沙箱 |
| `calculator` | 数学计算 | 安全 |
| `clipboard` | 读取 / 写入系统剪贴板 | 需确认 |

### 4.1 代码执行安全沙箱

```python
# backend/skills/builtin/code_execute.py
import subprocess
import tempfile

class CodeExecuteSkill(SkillBase):
    name = "code_execute"
    description = "执行 Python 代码并返回结果"

    async def execute(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write(code)
            f.flush()

            result = subprocess.run(
                ['python', f.name],
                capture_output=True,
                text=True,
                timeout=10,                 # 10 秒超时
                cwd=tempfile.gettempdir(),  # 限制工作目录
            )

        output = result.stdout or result.stderr
        return output[:2000]  # 限制输出长度
```

---

## 五、分身-技能绑定

### 5.1 数据模型

```python
# backend/models/avatar_skill.py
class AvatarSkill(Base):
    __tablename__ = "avatar_skills"

    id        = Column(String, primary_key=True)
    avatar_id = Column(String, ForeignKey("avatars.id"), nullable=False)
    skill_name = Column(String(50), nullable=False)

    __table_args__ = (UniqueConstraint('avatar_id', 'skill_name'),)
```

### 5.2 API

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | `/api/skills` | 获取所有可用技能列表 |
| GET | `/api/avatars/{id}/skills` | 获取分身已装配的技能 |
| PUT | `/api/avatars/{id}/skills` | 更新分身的技能装配 |

---

## 六、前端设计

### 6.1 技能装配 UI（在分身详情页中）

```text
───── 技能装配 ─────

☑ 🕐 获取当前时间
☑ 🔍 联网搜索
☑ 🧮 数学计算
☐ 📄 读取文件        ⚠️ 需要确认
☐ 📝 写入文件        ⚠️ 需要确认
☐ 💻 执行代码        ⚠️ 沙箱运行
☐ 📋 剪贴板操作      ⚠️ 需要确认

[保存]
```

### 6.2 对话中的工具调用展示

当分身调用工具时，在对话流中插入工具调用卡片：

```text
┌─────────────────────────────────┐
│ 🔧 正在使用：联网搜索             │
│ 关键词：Python 递归 教程         │
│ ─────────                       │
│ ✅ 已获取 3 条搜索结果           │
└─────────────────────────────────┘
```

### 6.3 安全确认对话框

标记了「需确认」的技能在执行前弹出确认框：

```text
┌──────────────────────────────────┐
│  ⚠️ 分身请求执行以下操作：        │
│                                  │
│  📄 读取文件                      │
│  路径：D:\Documents\report.txt   │
│                                  │
│  [允许]  [拒绝]  [始终允许]       │
└──────────────────────────────────┘
```

---

## 七、新增目录结构

```
backend/
├── skills/
│   ├── __init__.py
│   ├── base.py              # SkillBase 抽象类
│   ├── registry.py          # SkillRegistry 注册中心
│   └── builtin/
│       ├── current_time.py
│       ├── web_search.py
│       ├── file_read.py
│       ├── file_write.py
│       ├── code_execute.py
│       ├── calculator.py
│       └── clipboard.py
├── models/
│   └── avatar_skill.py
└── api/
    └── skills.py

frontend/src/
├── components/
│   ├── SkillToggleList.vue   # 技能勾选列表
│   └── chat/
│       └── ToolCallCard.vue  # 工具调用展示卡片
```

---

## 八、验收标准

- [ ] 分身可装配 / 卸载技能
- [ ] 对话中 LLM 能正确触发 Function Calling
- [ ] 工具调用过程在对话中可视化展示
- [ ] 联网搜索技能正常返回结果
- [ ] 代码执行在沙箱内运行，10 秒超时
- [ ] 需确认的技能弹出确认框，拒绝后不执行
- [ ] 工具调用最多 5 轮，防止无限循环
- [ ] 未装配技能的分身正常对话（不带 tools 参数）
