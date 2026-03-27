# Step 02 — 用户认证系统

> **目标**：实现用户注册、登录功能，基于 JWT 的会话管理，前端登录页面与路由守卫。

> **前置依赖**：Step 01（项目基础搭建完成）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| User 数据模型 | 用户表（SQLAlchemy） |
| 注册 / 登录 API | `POST /api/auth/register`、`POST /api/auth/login` |
| JWT 中间件 | 签发 & 验证 Token，保护需要认证的路由 |
| 前端登录 / 注册页 | 表单 UI（Element Plus） |
| Pinia auth store | 管理登录态、Token 持久化 |
| 路由守卫 | 未登录自动跳转登录页 |

---

## 二、后端设计

### 2.1 数据模型

```python
# backend/models/user.py
class User(Base):
    __tablename__ = "users"

    id          = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username    = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
```

### 2.2 API 端点

#### `POST /api/auth/register`

| 字段 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| username | string | 是 | 用户名（3-50 字符） |
| password | string | 是 | 密码（6 位以上） |

**响应**：`201 Created`

```json
{
  "id": "uuid",
  "username": "xxx",
  "token": "jwt_token"
}
```

**错误**：`409 Conflict`（用户名已存在）

#### `POST /api/auth/login`

| 字段 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应**：`200 OK`（同上）

**错误**：`401 Unauthorized`（用户名或密码错误）

### 2.3 JWT 设计

| 配置项 | 值 |
|:---|:---|
| 算法 | HS256 |
| 过期时间 | 7 天 |
| Payload | `{ sub: user_id, exp: timestamp }` |
| 密钥来源 | 首次启动自动生成，存入 `data/secret.key` |

### 2.4 密码处理

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 注册时
password_hash = pwd_context.hash(plain_password)

# 登录时
pwd_context.verify(plain_password, password_hash)
```

### 2.5 认证依赖

```python
# backend/deps/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """从 JWT 中解析 user_id，查询数据库返回 User 对象"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = db.query(User).get(payload["sub"])
    if not user:
        raise HTTPException(401)
    return user
```

---

## 三、前端设计

### 3.1 新增页面

| 路由 | 页面 | 说明 |
|:---|:---|:---|
| `/login` | LoginPage.vue | 登录表单 |
| `/register` | RegisterPage.vue | 注册表单 |
| `/` | HomePage.vue | 登录后首页（占位） |

### 3.2 Pinia Auth Store

```typescript
// frontend/src/stores/auth.ts
interface AuthState {
  token: string | null
  user: { id: string; username: string } | null
}

const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    user: null,
  }),
  actions: {
    async login(username: string, password: string) { ... },
    async register(username: string, password: string) { ... },
    logout() { ... },
  },
  persist: true,  // pinia-plugin-persistedstate
})
```

### 3.3 Axios 拦截器

```typescript
// frontend/src/utils/http.ts
const http = axios.create({ baseURL: '/api' })

// 请求拦截：自动附加 Token
http.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截：401 自动跳转登录
http.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      useAuthStore().logout()
      router.push('/login')
    }
    return Promise.reject(err)
  }
)
```

### 3.4 路由守卫

```typescript
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  const publicPages = ['/login', '/register']
  if (!publicPages.includes(to.path) && !auth.token) {
    next('/login')
  } else {
    next()
  }
})
```

---

## 四、新增目录结构

```
backend/
├── models/
│   └── user.py
├── schemas/
│   └── auth.py           # Pydantic 请求 / 响应模型
├── api/
│   └── auth.py           # 注册 / 登录路由
├── deps/
│   └── auth.py           # get_current_user 依赖
└── utils/
    └── security.py       # JWT 签发 / 验证、密码哈希

frontend/src/
├── views/
│   ├── LoginPage.vue
│   ├── RegisterPage.vue
│   └── HomePage.vue
├── stores/
│   └── auth.ts
└── utils/
    └── http.ts           # axios 实例 + 拦截器
```

---

## 五、验收标准

- [ ] 注册新用户后自动获得 Token 并跳转首页
- [ ] 登录成功后 Token 存入 localStorage，刷新页面不丢失
- [ ] 未登录访问 `/` 被重定向到 `/login`
- [ ] 错误的用户名 / 密码返回 401，前端提示错误信息
- [ ] 重复用户名注册返回 409，前端提示"用户名已存在"
- [ ] 后端受保护接口在无 Token / Token 过期时返回 401
