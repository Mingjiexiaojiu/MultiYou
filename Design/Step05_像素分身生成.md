# Step 05 — 像素分身形象生成

> **目标**：实现从用户上传照片到生成像素风格角色形象的完整图像处理管线，这是 MultiYou 区别于其他 AI Agent 项目的**核心差异点**。

> **前置依赖**：Step 03（引导向导，头像上传功能）

---

## 一、本步产出

| 产出物 | 说明 |
|:---|:---|
| 图像预处理模块 | 人脸检测、特征提取（发色 / 服装颜色） |
| 像素化生成管线 | 基础版（Pillow）+ 进阶版（Stable Diffusion） |
| Sprite 输出系统 | 结构化输出 idle / walk / talk 等动画帧 |
| 头像生成 API | `POST /api/avatars/generate-image` |
| 前端生成预览 | 上传 → 实时预览像素化效果 |

---

## 二、双轨方案设计

为降低启动门槛，采用**基础版 + 进阶版**双轨方案：

| 方案 | 技术 | 效果 | 要求 |
|:---|:---|:---|:---|
| 基础版（优先实现） | Pillow 像素化 | 真实照片的像素风格化 | 无 GPU 要求 |
| 进阶版（后续增强） | Stable Diffusion | AI 生成像素角色 | 需要 GPU / 云端 API |

---

## 三、基础版 — Pillow 像素化管线

### 3.1 处理流程

```text
原始照片（任意尺寸）
  ↓
人脸检测 & 裁剪（OpenCV）
  ↓
缩放到 512×512（统一输入尺寸）
  ↓
降采样到 32×32（丢失细节，保留轮廓和颜色块）
  ↓
升采样到 128×128（NEAREST 插值，保持像素锐利边缘）
  ↓
调色板量化（可选，减少到 16/32 色）
  ↓
输出像素风格头像
```

### 3.2 核心代码

```python
# backend/services/image_pipeline.py
from PIL import Image
import cv2
import numpy as np

class ImagePipeline:
    PIXEL_SIZE = 32       # 降采样尺寸
    OUTPUT_SIZE = 128     # 最终输出尺寸
    INPUT_SIZE = 512      # 统一输入尺寸

    def pixelate(self, image_path: str, output_path: str) -> str:
        """基础像素化：512 → 32 → 128 NEAREST"""
        img = Image.open(image_path).convert("RGB")
        img = img.resize((self.INPUT_SIZE, self.INPUT_SIZE), Image.LANCZOS)

        # 降采样（丢失细节）
        small = img.resize(
            (self.PIXEL_SIZE, self.PIXEL_SIZE),
            Image.LANCZOS
        )

        # 升采样（NEAREST 保持像素锐利）
        pixel_art = small.resize(
            (self.OUTPUT_SIZE, self.OUTPUT_SIZE),
            Image.NEAREST
        )

        pixel_art.save(output_path)
        return output_path

    def detect_and_crop_face(self, image_path: str) -> str:
        """人脸检测 & 裁剪（居中正方形）"""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) > 0:
            x, y, w, h = faces[0]
            # 扩展裁剪区域（包含头发和上半身）
            padding = int(w * 0.5)
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img.shape[1], x + w + padding)
            y2 = min(img.shape[0], y + h + padding * 2)

            # 裁剪为正方形
            size = max(x2 - x1, y2 - y1)
            cropped = img[y1:y1+size, x1:x1+size]
        else:
            # 无人脸，居中裁剪
            h, w = img.shape[:2]
            size = min(h, w)
            cropped = img[:size, :size]

        cropped_path = image_path.replace('.', '_cropped.')
        cv2.imwrite(cropped_path, cropped)
        return cropped_path

    def extract_colors(self, image_path: str) -> dict:
        """提取主要颜色（发色、肤色、服装色）"""
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # K-Means 聚类提取主色调
        pixels = img_rgb.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        colors = centers.astype(int).tolist()
        return {
            "dominant_colors": colors,
            "palette_hex": [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]
        }
```

### 3.3 调色板量化（可选增强）

```python
def quantize_colors(self, image_path: str, n_colors: int = 16) -> Image:
    """减少颜色数量，更像像素游戏风格"""
    img = Image.open(image_path).convert("RGB")
    return img.quantize(colors=n_colors, method=Image.MEDIANCUT).convert("RGB")
```

---

## 四、进阶版 — Stable Diffusion 生成（预留）

### 4.1 技术方案

| 组件 | 用途 |
|:---|:---|
| Stable Diffusion (Img2Img) | 基于原图生成像素角色 |
| ControlNet | 姿态控制，半身→全身补全 |
| LoRA | 加载像素风格微调模型 |
| CLIP | 图像语义理解，提取特征描述 |

### 4.2 Prompt 模板

```text
pixel art, full body character, 2D game sprite,
based on the person in the image,
same hairstyle, same color, simple outfit,
8-bit style, front view, transparent background
```

半身补全 Prompt：

```text
complete full body based on upper body image,
pixel art style, standing pose, front view
```

### 4.3 调用方式（预留接口）

```python
# backend/services/sd_generator.py（进阶版）
class SDGenerator:
    def __init__(self, sd_api_url: str = "http://localhost:7860"):
        self.api_url = sd_api_url

    async def img2img(self, input_image: str, prompt: str) -> str:
        """调用 Stable Diffusion WebUI API"""
        # 预留实现
        pass

    async def generate_sprite(self, input_image: str) -> dict:
        """生成完整 Sprite 集（idle / walk / talk）"""
        # 预留实现
        pass
```

---

## 五、Sprite 输出系统

### 5.1 输出目录结构

```
data/avatars/{user_id}/{avatar_id}/
├── original.png      # 原始上传照片
├── idle.png          # 待机状态（128×128）
├── walk.png          # 行走动画（sprite sheet，4帧，512×128）
├── talk.png          # 说话动画（sprite sheet，2帧，256×128）
└── meta.json         # 角色元数据
```

### 5.2 meta.json 结构

```json
{
  "avatar_id": "uuid",
  "generated_at": "2026-03-27T...",
  "method": "pillow_pixelate",
  "colors": {
    "dominant_colors": [[220, 180, 140], [60, 40, 30], [100, 120, 200]],
    "palette_hex": ["#dcb48c", "#3c2820", "#6478c8"]
  },
  "sprites": {
    "idle": { "file": "idle.png", "width": 128, "height": 128, "frames": 1 },
    "walk": { "file": "walk.png", "width": 512, "height": 128, "frames": 4 },
    "talk": { "file": "talk.png", "width": 256, "height": 128, "frames": 2 }
  }
}
```

### 5.3 基础版动画帧生成

基础版通过简单变换生成动画帧（进阶版由 SD 直接生成）：

```python
def generate_sprite_sheet(self, idle_image: str) -> dict:
    """基于 idle 图生成简单动画帧"""
    idle = Image.open(idle_image)

    # walk：左右轻微偏移 + 上下浮动
    walk_frames = []
    for i, offset in enumerate([(0, 0), (2, -2), (0, 0), (-2, -2)]):
        frame = Image.new("RGBA", idle.size, (0, 0, 0, 0))
        frame.paste(idle, offset)
        walk_frames.append(frame)

    # 拼接为 sprite sheet
    sheet_width = idle.width * len(walk_frames)
    walk_sheet = Image.new("RGBA", (sheet_width, idle.height))
    for i, frame in enumerate(walk_frames):
        walk_sheet.paste(frame, (i * idle.width, 0))

    return {"walk": walk_sheet, "talk": ...}
```

---

## 六、后端 API

### 6.1 端点

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/api/avatars/generate-image` | 上传照片，生成像素形象 |
| GET | `/api/avatars/{id}/sprites` | 获取分身的 Sprite 资源列表 |
| GET | `/api/avatars/{id}/sprites/{file}` | 获取指定 Sprite 文件 |
| POST | `/api/avatars/{id}/regenerate` | 重新生成像素形象 |

### 6.2 生成流程

```text
POST /api/avatars/generate-image
  ├── 接收上传的图片文件
  ├── 人脸检测 & 裁剪
  ├── 像素化处理
  ├── 颜色提取
  ├── 生成 sprite sheet
  ├── 保存到 data/avatars/{user_id}/{avatar_id}/
  ├── 写入 meta.json
  └── 返回生成结果（含预览 URL）
```

---

## 七、前端设计

### 7.1 生成预览组件

```text
┌─────────────────────────────────────┐
│  📸 上传你的照片                      │
│                                     │
│  ┌──────────┐    →    ┌──────────┐  │
│  │  原始照片 │         │ 像素分身  │  │
│  │          │         │  预览    │  │
│  └──────────┘         └──────────┘  │
│                                     │
│  [重新上传]           [确认使用]      │
└─────────────────────────────────────┘
```

### 7.2 Sprite 预览

- 使用 Canvas 渲染 sprite sheet 播放动画
- 支持切换 idle / walk / talk 状态
- 帧率可调

---

## 八、新增目录结构

```
backend/
├── services/
│   ├── image_pipeline.py    # Pillow 像素化管线
│   └── sd_generator.py      # SD 生成器（预留）
├── api/
│   └── avatars.py           # 新增图像生成端点
└── data/
    └── avatars/             # 用户头像资源存储

frontend/src/
├── components/
│   ├── AvatarGenerator.vue  # 上传 + 生成预览
│   └── SpritePreview.vue    # Sprite 动画预览
```

---

## 九、验收标准

- [ ] 上传照片后自动检测人脸并裁剪
- [ ] 像素化生成效果清晰，保留人物主要颜色特征
- [ ] 输出文件包含 idle.png + walk.png + talk.png + meta.json
- [ ] 前端可实时预览像素化效果
- [ ] Sprite 动画在 Canvas 中能正常播放
- [ ] 无 GPU 环境下基础版正常运行
- [ ] 重新生成功能正常
