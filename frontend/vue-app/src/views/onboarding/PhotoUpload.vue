<template>
  <div class="step">
    <h2>上传头像照片</h2>
    <p class="sub">第 4 步 / 共 6 步</p>

    <div class="upload-area" v-if="!croppedDataUrl">
      <label class="upload-label">
        <input type="file" accept="image/jpeg,image/png" @change="onFile" hidden />
        <span>点击选择照片（JPG / PNG，≤5MB）</span>
      </label>
    </div>

    <div v-if="srcUrl && !croppedDataUrl" class="cropper-wrap">
      <ImageCropper :src="srcUrl" @cropped="onCropped" />
    </div>

    <div v-if="croppedDataUrl" class="preview-area">
      <div class="preview-pair">
        <div>
          <p class="preview-label">原图裁剪</p>
          <img :src="croppedDataUrl" class="preview-orig" />
        </div>
        <div>
          <p class="preview-label">像素预览</p>
          <canvas ref="canvas" class="preview-pixel" width="128" height="128" />
        </div>
      </div>
      <button class="btn-reselect" @click="reset">重新选择</button>
    </div>

    <div class="nav-row">
      <router-link to="/onboarding/model" class="btn-back">← 上一步</router-link>
      <button class="btn-primary" :disabled="!wizard.croppedBlob" @click="next">下一步 →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboardingStore } from '@/stores/onboarding'
import ImageCropper from '@/components/ImageCropper.vue'

const router = useRouter()
const wizard = useOnboardingStore()

const srcUrl = ref('')
const croppedDataUrl = ref('')
const canvas = ref(null)

function onFile(e) {
  const file = e.target.files[0]
  if (!file) return
  srcUrl.value = URL.createObjectURL(file)
  croppedDataUrl.value = ''
}

async function onCropped(blob) {
  wizard.croppedBlob = blob
  croppedDataUrl.value = URL.createObjectURL(blob)
  await nextTick()
  renderPixel()
}

function renderPixel() {
  const img = new Image()
  img.onload = () => {
    const ctx = canvas.value.getContext('2d')
    // Draw 32×32 then scale to 128×128 for pixel effect
    ctx.imageSmoothingEnabled = false
    const off = document.createElement('canvas')
    off.width = 32; off.height = 32
    off.getContext('2d').drawImage(img, 0, 0, 32, 32)
    ctx.drawImage(off, 0, 0, 128, 128)
  }
  img.src = croppedDataUrl.value
}

function reset() {
  srcUrl.value = ''
  croppedDataUrl.value = ''
  wizard.croppedBlob = null
}

function next() { router.push('/onboarding/persona') }
</script>

<style scoped>
.step { }
h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: #666; font-size: 13px; margin-bottom: 24px; }
.upload-area {
  border: 2px dashed #333; border-radius: 8px; padding: 32px;
  text-align: center; margin-bottom: 20px; cursor: pointer;
}
.upload-area:hover { border-color: #7c6fff; }
.upload-label { cursor: pointer; color: #888; font-size: 14px; }
.cropper-wrap { margin-bottom: 16px; }
.preview-area { margin-bottom: 16px; }
.preview-pair { display: flex; gap: 24px; margin-bottom: 12px; }
.preview-label { font-size: 12px; color: #888; margin-bottom: 6px; text-align: center; }
.preview-orig { width: 128px; height: 128px; object-fit: cover; border-radius: 4px; }
.preview-pixel { width: 128px; height: 128px; image-rendering: pixelated; border-radius: 4px; }
.btn-reselect {
  background: none; border: 1px solid #444; color: #888;
  padding: 6px 14px; border-radius: 4px; font-size: 13px; cursor: pointer;
}
.nav-row { display: flex; justify-content: space-between; margin-top: 16px; }
.btn-back { background: none; border: none; color: #888; font-size: 14px; cursor: pointer; text-decoration: none; align-self: center; }
.btn-primary {
  padding: 10px 20px; background: #7c6fff; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
