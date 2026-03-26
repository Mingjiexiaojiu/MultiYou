<template>
  <div class="create-page">
    <header class="topbar">
      <button class="btn-back" @click="router.back()">← 返回</button>
      <span>创建分身</span>
    </header>

    <div class="form-area">
      <div class="field">
        <label>分身名称</label>
        <input v-model="form.name" type="text" placeholder="给你的分身起个名字" />
      </div>

      <div class="field">
        <label>上传照片（JPG / PNG，≤5MB）</label>
        <div v-if="!croppedBlob">
          <label class="upload-label">
            <input type="file" accept="image/jpeg,image/png" @change="onFile" hidden />
            <span class="upload-btn">{{ imgSrc ? '已选择，点击重选' : '点击选择照片' }}</span>
          </label>
          <ImageCropper v-if="imgSrc" :src="imgSrc" @cropped="onCropped" />
        </div>
        <div v-else class="crop-done">
          <span>✅ 已裁剪</span>
          <button type="button" class="btn-reselect" @click="croppedBlob = null; imgSrc = ''">重选</button>
        </div>
      </div>

      <div class="field">
        <label>角色 (Persona)</label>
        <select v-model="form.personaId">
          <option value="" disabled>选择角色</option>
          <option v-for="p in personas" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>

      <div class="field">
        <label>AI 模型</label>
        <select v-model="form.modelId">
          <option value="" disabled>选择模型</option>
          <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn-primary" :disabled="loading || !ready" @click="submit">
        {{ loading ? '创建中…' : '创建分身' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ImageCropper from '@/components/ImageCropper.vue'
import { listPersonas, createAvatar } from '@/api/avatar'
import { listModels } from '@/api/model'

const router = useRouter()

const form = ref({ name: '', personaId: '', modelId: '' })
const croppedBlob = ref(null)
const imgSrc = ref('')
const personas = ref([])
const models = ref([])
const loading = ref(false)
const error = ref('')

const ready = computed(() =>
  form.value.name && croppedBlob.value && form.value.personaId && form.value.modelId
)

onMounted(async () => {
  const [p, m] = await Promise.all([listPersonas(), listModels()])
  personas.value = p.data
  models.value = m.data
})

function onFile(e) {
  const file = e.target.files[0]
  if (file) imgSrc.value = URL.createObjectURL(file)
}

function onCropped(blob) {
  croppedBlob.value = blob
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.value.name)
    fd.append('persona_id', form.value.personaId)
    fd.append('model_id', form.value.modelId)
    fd.append('image', croppedBlob.value, 'avatar.png')    await createAvatar(fd)
    router.push('/home')
  } catch (e) {
    error.value = e.response?.data?.detail || '创建失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-page { display: flex; flex-direction: column; height: 100vh; }
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 24px;
  height: 56px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  font-size: 16px;
  font-weight: 500;
  flex-shrink: 0;
}
.btn-back { background: none; border: none; color: #7c6fff; font-size: 14px; cursor: pointer; }
.form-area { flex: 1; overflow-y: auto; padding: 32px; max-width: 540px; }
.field { margin-bottom: 20px; }
label { display: block; font-size: 13px; color: #888; margin-bottom: 8px; }
input, select {
  width: 100%;
  padding: 10px 12px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e8e8e8;
  font-size: 14px;
}
input:focus, select:focus { outline: none; border-color: #7c6fff; }
.btn-primary {
  padding: 12px 24px;
  background: #7c6fff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  width: 100%;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: #ff6b6b; font-size: 13px; margin-bottom: 12px; }
.upload-label { cursor: pointer; display: block; }
.upload-btn {
  display: inline-block; padding: 8px 16px; background: #222;
  border: 1px dashed #444; border-radius: 6px; color: #888; font-size: 13px; margin-bottom: 10px;
}
.crop-done { display: flex; gap: 12px; align-items: center; }
.btn-reselect {
  background: none; border: 1px solid #444; color: #888;
  padding: 5px 12px; border-radius: 4px; font-size: 13px; cursor: pointer;
}
</style>
