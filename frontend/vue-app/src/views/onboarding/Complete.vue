<template>
  <div class="step">
    <h2>确认并完成设置</h2>
    <p class="sub">第 6 步 / 共 6 步</p>

    <div class="summary">
      <div class="row"><span class="lbl">分身名称</span><span>{{ wizard.avatarName }}</span></div>
      <div class="row"><span class="lbl">角色名称</span><span>{{ wizard.personaName }}</span></div>
      <div class="row"><span class="lbl">AI 模型</span><span>{{ wizard.provider }} — {{ wizard.modelIdStr }}</span></div>
      <div class="row"><span class="lbl">本地模型</span><span>{{ wizard.isLocal ? '是' : '否' }}</span></div>
      <div class="row"><span class="lbl">头像</span><span>{{ wizard.croppedBlob ? '已上传' : '⚠️ 未上传' }}</span></div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="nav-row">
      <router-link to="/onboarding/persona" class="btn-back">← 上一步</router-link>
      <button class="btn-primary" :disabled="loading || !canSubmit" @click="submit">
        {{ loading ? '创建中…' : '完成设置 🎉' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboardingStore } from '@/stores/onboarding'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/index'

const router = useRouter()
const wizard = useOnboardingStore()
const auth = useAuthStore()

const loading = ref(false)
const error = ref('')

const canSubmit = computed(() =>
  wizard.avatarName &&
  wizard.personaName &&
  wizard.systemPrompt &&
  wizard.croppedBlob &&
  wizard.endpoint &&
  wizard.modelIdStr,
)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('model_name', `${wizard.provider} — ${wizard.modelIdStr}`)
    fd.append('provider', wizard.provider)
    fd.append('endpoint', wizard.endpoint)
    fd.append('model_id_str', wizard.modelIdStr)
    fd.append('is_local', wizard.isLocal ? 'true' : 'false')
    fd.append('api_key', wizard.apiKey || '')
    fd.append('avatar_name', wizard.avatarName)
    fd.append('persona_name', wizard.personaName)
    fd.append('system_prompt', wizard.systemPrompt)
    fd.append('image', wizard.croppedBlob, 'avatar.png')

    await api.post('/api/onboarding/setup', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    auth.markOnboardingDone()
    wizard.$reset()
    router.push('/home')
  } catch (e) {
    error.value = e.response?.data?.detail || '设置失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.step { }
h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: #666; font-size: 13px; margin-bottom: 24px; }
.summary {
  background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px;
  padding: 16px; margin-bottom: 20px;
}
.row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2a2a; font-size: 14px; }
.row:last-child { border-bottom: none; }
.lbl { color: #888; }
.error { color: #ff6b6b; font-size: 13px; margin-bottom: 12px; }
.nav-row { display: flex; justify-content: space-between; }
.btn-back { background: none; border: none; color: #888; font-size: 14px; cursor: pointer; text-decoration: none; align-self: center; }
.btn-primary {
  padding: 10px 20px; background: #7c6fff; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
