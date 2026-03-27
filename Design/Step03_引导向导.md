# Step 03 — 引导向导（Onboarding）

> **目标**：新用户注册后进入引导流程，完成「配置 AI 模型 → 上传头像 → 创建第一个分身」三步向导，一步到位地初始化核心数据。

> **前置依赖**：Step 02（用户认证系统）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 引导向导页面 | 3 步 Stepper UI |
| Onboarding API | `POST /api/onboarding/complete` 一步写入所有数据 |
| Pinia onboarding store | 跨步骤暂存向导数据 |
| 基础数据模型 | Model、Persona、Avatar 表（schema 先建好，CRUD 在后续步骤完善） |

---

## 二、向导流程设计

```text
注册成功
  ↓
Step 1 ─ 配置 AI 模型
  · 选择提供商（DeepSeek / Ollama / 自定义 OpenAI 兼容）
  · 填写 API Key / 端点地址
  · 点击「测试连接」验证可用性
  ↓
Step 2 ─ 上传头像
  · 上传照片 or 选择默认头像
  · vue-cropper 裁剪为正方形
  · 本地预览
  ↓
Step 3 ─ 创建第一个分身
  · 输入分身名称
  · 选择 / 自定义人格描述
  · 系统自动绑定 Step1 的模型 + Step2 的头像
  ↓
提交 → 后端一次性写入 Model + Persona + Avatar
  ↓
跳转主页 → 分身就绪
```

---

## 三、后端设计

### 3.1 数据模型（新增）

```python
# backend/models/model_config.py
class ModelConfig(Base):
    __tablename__ = "model_configs"

    id          = Column(String, primary_key=True)
    user_id     = Column(String, ForeignKey("users.id"), nullable=False)
    provider    = Column(String(50))    # deepseek / ollama / custom
    model_name  = Column(String(100))   # deepseek-chat / llama3 / ...
    api_base    = Column(String(255))   # https://api.deepseek.com/v1
    api_key_ref = Column(String(100))   # keyring 中的 key 名称
    is_default  = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
```

```python
# backend/models/persona.py
class Persona(Base):
    __tablename__ = "personas"

    id          = Column(String, primary_key=True)
    user_id     = Column(String, ForeignKey("users.id"), nullable=False)
    name        = Column(String(100))
    description = Column(Text)          # 人格描述 / System Prompt
    created_at  = Column(DateTime, default=datetime.utcnow)
```

```python
# backend/models/avatar.py
class Avatar(Base):
    __tablename__ = "avatars"

    id          = Column(String, primary_key=True)
    user_id     = Column(String, ForeignKey("users.id"), nullable=False)
    name        = Column(String(100))
    image_path  = Column(String(255))   # 头像文件路径
    persona_id  = Column(String, ForeignKey("personas.id"))
    model_id    = Column(String, ForeignKey("model_configs.id"))
    created_at  = Column(DateTime, default=datetime.utcnow)
```

### 3.2 API 端点

#### `POST /api/onboarding/complete`

一次提交所有引导数据，后端在事务中依次创建：

**请求体**：

```json
{
  "model": {
    "provider": "deepseek",
    "model_name": "deepseek-chat",
    "api_base": "https://api.deepseek.com/v1",
    "api_key": "sk-xxx"
  },
  "avatar_image": "<base64 或 multipart file>",
  "persona": {
    "name": "学习分身",
    "description": "你是一个专注学习的助手..."
  },
  "avatar_name": "小知"
}
```

**后端处理流程**：

```text
1. 创建 ModelConfig（api_key 通过 keyring 存储，数据库只存引用名）
2. 保存头像图片到 data/avatars/{user_id}/{avatar_id}.png
3. 创建 Persona
4. 创建 Avatar（关联 model_id + persona_id + image_path）
5. 提交事务
6. 返回完整的 Avatar 对象
```

**响应**：`201 Created`

```json
{
  "avatar": { "id": "...", "name": "小知", "image_path": "..." },
  "model": { "id": "...", "provider": "deepseek" },
  "persona": { "id": "...", "name": "学习分身" }
}
```

#### `POST /api/models/test-connection`

测试 AI 模型连接可用性。

**请求体**：

```json
{
  "provider": "deepseek",
  "api_base": "https://api.deepseek.com/v1",
  "api_key": "sk-xxx",
  "model_name": "deepseek-chat"
}
```

**处理**：发送一个简短的 completion 请求，检查是否返回有效响应。

**响应**：`200 OK`

```json
{ "success": true, "message": "连接成功，模型可用" }
```

### 3.3 API Key 安全存储

```python
import keyring

# 存储
keyring.set_password("multiyou", f"model_{model_id}", api_key)

# 读取
api_key = keyring.get_password("multiyou", f"model_{model_id}")
```

数据库中只保存 `api_key_ref = f"model_{model_id}"`，不直接存储密钥。

---

## 四、前端设计

### 4.1 页面结构

| 路由 | 页面 | 说明 |
|:---|:---|:---|
| `/onboarding` | OnboardingPage.vue | 向导容器（el-steps） |
| — | StepModel.vue | 步骤 1：模型配置 |
| — | StepAvatar.vue | 步骤 2：头像上传 |
| — | StepPersona.vue | 步骤 3：分身创建 |

### 4.2 Pinia Onboarding Store

```typescript
// frontend/src/stores/onboarding.ts
interface OnboardingState {
  step: number                    // 当前步骤（0/1/2）
  model: {
    provider: string
    modelName: string
    apiBase: string
    apiKey: string
  } | null
  avatarImage: File | null        // 裁剪后的头像文件
  persona: {
    name: string
    description: string
  } | null
  avatarName: string
}
```

### 4.3 各步骤 UI 要点

**Step 1 — 模型配置**
- 提供商下拉选择（预设 DeepSeek / Ollama / 自定义）
- 选择后自动填充 `api_base`
- API Key 输入框（password 模式）
- 「测试连接」按钮，成功后才允许下一步

**Step 2 — 头像上传**
- 拖拽上传 or 点击选择
- vue-cropper 组件裁剪为 1:1
- 裁剪预览
- 可跳过（使用默认头像）

**Step 3 — 创建分身**
- 分身名称输入
- 人格模板快速选择（学习 / 工作 / 编程 / 数据 / 社交）
- 自定义人格描述文本框
- 「完成创建」按钮 → 调用 onboarding/complete

---

## 五、路由守卫增强

```typescript
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!auth.token && to.path !== '/login' && to.path !== '/register') {
    next('/login')
  } else if (auth.token && auth.needsOnboarding && to.path !== '/onboarding') {
    next('/onboarding')  // 未完成引导的用户强制进入向导
  } else {
    next()
  }
})
```

---

## 六、验收标准

- [ ] 新注册用户自动跳转到引导向导页面
- [ ] 模型配置步骤可以成功测试连接
- [ ] 头像上传与裁剪功能正常
- [ ] 完成向导后，数据库中正确创建 ModelConfig + Persona + Avatar 记录
- [ ] API Key 通过 keyring 安全存储，数据库中无明文密钥
- [ ] 完成引导后跳转主页，不再显示向导
- [ ] 已完成引导的用户登录后直接进入主页
