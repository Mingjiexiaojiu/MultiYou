# 🚀 MultiYou 项目设计文档

## 一、项目简介
MultiYou 是一个基于 AI 的桌面分身助手，通过上传用户照片生成像素风数字人，并结合人格（Persona）、技能（Skills）与模型（Model），构建多 Agent 分身系统。

---

## 二、技术架构

### 总体架构
```
Electron + Vue3（前端桌面）
        ↓
FastAPI（本地后端）
        ↓
Agent Core（Python）
        ↓
Model Layer（Ollama / Cloud API）
        ↓
SQLite（本地数据库）
```

---

## 三、技术选型

| 模块 | 技术 |
|------|------|
| 前端 | Vue3 + Electron |
| 后端 | FastAPI |
| AI模型 | Ollama + 云端API |
| 数据库 | SQLite |
| 动画 | Canvas |
| 图像处理 | Pillow |

---

## 四、项目目录结构

```
MultiYou/
├── frontend/
│   ├── electron/
│   └── vue-app/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── services/
│   │   ├── avatar_service.py
│   │   ├── agent_service.py
│   │   └── skill_service.py
│   ├── models/
│   └── db/
│
├── assets/
│   ├── avatar/
│   │   ├── body/
│   │   ├── clothes/
│   │   └── face/
│
└── data/
```

---

## 五、核心模块设计

### 1. Avatar系统（分身）

结构：
```
Avatar = Face + Body + Clothes + Persona + Model + Skills
```

---

### 2. 图像生成流程

```
上传图片
 → 人脸裁剪
 → 像素化处理
 → 选择身份（衣服）
 → 拼接生成头像
```

---

### 3. 像素化实现（Pillow）

```python
img_small = img.resize((32,32), Image.NEAREST)
img_pixel = img_small.resize((128,128), Image.NEAREST)
```

---

### 4. 拼接系统

图层顺序：
```
身体 → 衣服 → 脸
```

---

### 5. Agent系统

```
输入 → Persona → Model → Skills → 输出
```

---

### 6. Skills设计

```python
class Skill:
    def execute(self, input):
        pass
```

---

### 7. 模型层

支持：
- Ollama（本地）
- OpenAI / DeepSeek（云端）

---

## 六、桌面动画系统

### 原理
Canvas + requestAnimationFrame

### 动画流程
```
更新位置 → 渲染 → 循环
```

---

### 示例
```javascript
function loop(){
  update()
  render()
  requestAnimationFrame(loop)
}
```

---

### 移动逻辑
```javascript
x += velocity
```

---

## 七、阶段开发计划

### 第一阶段（基础版）
- 上传图片
- 像素化头像
- 单分身展示
- 简单聊天

---

### 第二阶段（进阶）
- 多分身
- Skills系统
- 模型切换

---

### 第三阶段（增强）
- 桌面动画
- 状态系统（走路/待机）
- UI优化

---

### 第四阶段（扩展）
- 云端同步
- Skills市场
- 多Agent协作

---

## 八、关键难点

- 人脸裁剪精度
- 像素风统一
- 动画流畅度
- Agent调度逻辑

---

## 九、总结

MultiYou = 像素分身 + AI Agent + Skills系统 + 桌面交互
