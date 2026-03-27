# Step 04 — AI 模型接入

> **目标**：实现多 AI 模型的统一接入层，支持 DeepSeek / Ollama / 任意 OpenAI 兼容 API 的管理、切换和调用。

> **前置依赖**：Step 03（引导向导，ModelConfig 已可创建）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| OpenAI 兼容 Provider | 统一的 LLM 调用抽象层 |
| 模型配置 CRUD API | 增删改查 + 连接测试 |
| 模型管理页面 | 前端 UI：列表、新增、编辑、删除、测试 |
| 多模型切换 | 分身可绑定不同模型 |

---

## 二、核心设计：统一 Provider 抽象

### 2.1 为什么只需一个 Provider

DeepSeek、Ollama、通义千问等都实现了 **OpenAI 兼容 API**，格式一致：

| 提供商 | API Base | 说明 |
|:---|:---|:---|
| DeepSeek | `https://api.deepseek.com/v1` | 云端，需 API Key |
| Ollama | `http://localhost:11434/v1` | 本地，无需 Key |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 云端，需 Key |
| 自定义 | 用户填写 | 任意 OpenAI 兼容端点 |

### 2.2 Provider 实现

```python
# backend/services/ai_provider.py
import httpx

class OpenAICompatProvider:
    def __init__(self, api_base: str, api_key: str | None, model: str):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str | AsyncIterator:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            if stream:
                return self._stream_chat(client, headers, payload)
            else:
                resp = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

    async def _stream_chat(self, client, headers, payload):
        """SSE 流式响应"""
        async with client.stream(
            "POST",
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=payload,
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]

    async def test_connection(self) -> bool:
        """发送简短请求测试连通性"""
        try:
            result = await self.chat([
                {"role": "user", "content": "Hi"}
            ])
            return bool(result)
        except Exception:
            return False
```

### 2.3 Provider 工厂

```python
# backend/services/ai_provider.py
import keyring

def create_provider(model_config: ModelConfig) -> OpenAICompatProvider:
    api_key = None
    if model_config.api_key_ref:
        api_key = keyring.get_password("multiyou", model_config.api_key_ref)

    return OpenAICompatProvider(
        api_base=model_config.api_base,
        api_key=api_key,
        model=model_config.model_name,
    )
```

---

## 三、后端 API 设计

### 3.1 模型配置 CRUD

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | `/api/models` | 获取当前用户所有模型配置 |
| POST | `/api/models` | 新增模型配置 |
| PUT | `/api/models/{id}` | 更新模型配置 |
| DELETE | `/api/models/{id}` | 删除模型配置 |
| POST | `/api/models/test-connection` | 测试连接（不保存） |
| POST | `/api/models/{id}/test` | 测试已保存的模型 |
| PUT | `/api/models/{id}/default` | 设为默认模型 |

### 3.2 请求 / 响应示例

#### `POST /api/models`

```json
// 请求
{
  "provider": "deepseek",
  "model_name": "deepseek-chat",
  "api_base": "https://api.deepseek.com/v1",
  "api_key": "sk-xxx",
  "is_default": true
}

// 响应 201
{
  "id": "uuid",
  "provider": "deepseek",
  "model_name": "deepseek-chat",
  "api_base": "https://api.deepseek.com/v1",
  "is_default": true,
  "created_at": "2026-03-27T..."
}
```

> **注意**：响应中不返回 API Key。

#### `GET /api/models`

```json
[
  {
    "id": "uuid",
    "provider": "deepseek",
    "model_name": "deepseek-chat",
    "api_base": "https://api.deepseek.com/v1",
    "is_default": true,
    "has_api_key": true
  }
]
```

---

## 四、预设模型模板

前端提供快速配置模板：

```typescript
const MODEL_PRESETS = {
  deepseek: {
    provider: 'deepseek',
    modelName: 'deepseek-chat',
    apiBase: 'https://api.deepseek.com/v1',
    needsKey: true,
  },
  ollama: {
    provider: 'ollama',
    modelName: 'llama3',
    apiBase: 'http://localhost:11434/v1',
    needsKey: false,
  },
  qwen: {
    provider: 'qwen',
    modelName: 'qwen-plus',
    apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    needsKey: true,
  },
  custom: {
    provider: 'custom',
    modelName: '',
    apiBase: '',
    needsKey: true,
  },
}
```

---

## 五、前端设计

### 5.1 页面

| 路由 | 页面 | 说明 |
|:---|:---|:---|
| `/settings/models` | ModelListPage.vue | 模型列表（卡片式） |
| — | ModelFormDialog.vue | 新增 / 编辑模型对话框 |

### 5.2 模型卡片 UI

```text
┌─────────────────────────────────┐
│  🤖 DeepSeek Chat    [默认]     │
│  端点：api.deepseek.com         │
│  Key：已配置 ✅                  │
│                                 │
│  [测试连接]  [编辑]  [删除]      │
└─────────────────────────────────┘
```

### 5.3 模型表单

- 提供商选择 → 自动填充模板
- 模型名称输入（Ollama 可下拉选择已安装模型）
- API Base 输入
- API Key 输入（可选，password 模式）
- 「测试连接」按钮（必须通过后才可保存）
- 设为默认开关

---

## 六、Ollama 特殊处理

Ollama 运行在本地，可通过 API 获取已安装的模型列表：

```python
# GET http://localhost:11434/api/tags
async def list_ollama_models(api_base: str) -> list[str]:
    base = api_base.replace("/v1", "")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{base}/api/tags")
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
```

前端在选择 Ollama 时，调用 `GET /api/models/ollama-models` 获取本地模型列表，供用户下拉选择。

---

## 七、新增目录结构

```
backend/
├── services/
│   └── ai_provider.py       # OpenAICompatProvider + 工厂
├── api/
│   └── models.py             # 模型配置 CRUD 路由
└── schemas/
    └── model.py              # Pydantic 模型

frontend/src/
├── views/settings/
│   └── ModelListPage.vue
├── components/
│   └── ModelFormDialog.vue
└── stores/
    └── model.ts              # 模型配置 store
```

---

## 八、验收标准

- [ ] 可新增 DeepSeek / Ollama / 自定义模型配置
- [ ] 测试连接成功后显示绿色提示
- [ ] API Key 通过 keyring 安全存储，接口不返回明文
- [ ] 可设置默认模型，切换默认时原默认被取消
- [ ] Ollama 提供商可自动获取本地模型列表
- [ ] 删除模型时，如有分身绑定则提示不可删除
- [ ] 编辑模型后可重新测试连接
