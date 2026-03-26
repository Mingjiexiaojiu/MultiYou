<template>
  <div class="step">
    <h2>配置 AI 模型</h2>
    <p class="sub">第 3 步 / 共 6 步</p>

    <div class="field">
      <label>模型提供商</label>
      <select v-model="wizard.provider" @change="onProviderChange">
        <option value="deepseek">DeepSeek（推荐）</option>
        <option value="ollama">Ollama（本地）</option>
        <option value="custom">自定义 OpenAI 兼容</option>
      </select>
    </div>

    <div class="field">
      <label>API 端点</label>
      <input v-model="wizard.endpoint" type="text" placeholder="https://api.deepseek.com" />
    </div>

    <div class="field">
      <label>模型 ID</label>
      <input v-model="wizard.modelIdStr" type="text" placeholder="deepseek-chat" />
    </div>

    <div class="field" v-if="!wizard.isLocal">
      <label>API Key</label>
      <input v-model="wizard.apiKey" type="password" placeholder="sk-..." autocomplete="off" />
    </div>

    <button class="btn-test" :disabled="testing" @click="testConnection">
      {{ testing ? '测试中…' : '测试连接' }}
    </button>
    <p v-if="testResult" :class="testResult.success ? 'ok' : 'error'">{{ testResult.message }}</p>

    <div class="nav-row">
      <router-link to="/onboarding/account" class="btn-back">← 上一步</router-link>
      <button class="btn-primary" @click="next">下一步 →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboardingStore } from '@/stores/onboarding'
import { testModel as apiTestModel, createModel } from '@/api/model'

const router = useRouter()
const wizard = useOnboardingStore()

const testing = ref(false)
const testResult = ref(null)

function onProviderChange() {
  if (wizard.provider === 'deepseek') {
    wizard.endpoint = 'https://api.deepseek.com'
    wizard.modelIdStr = 'deepseek-chat'
    wizard.isLocal = false
  } else if (wizard.provider === 'ollama') {
    wizard.endpoint = 'http://localhost:11434'
    wizard.modelIdStr = 'llama3'
    wizard.isLocal = true
  } else {
    wizard.isLocal = false
  }
}

async function testConnection() {
  testResult.value = null
  testing.value = true
  try {
    // Create a temporary model record for testing, then delete it
    const { data: model } = await createModel({
      name: '_test',
      model_id: wizard.modelIdStr,
      provider: wizard.provider,
      endpoint: wizard.endpoint,
      api_key: wizard.apiKey || null,
      is_local: wizard.isLocal,
    })
    const { data } = await apiTestModel(model.id)
    testResult.value = data
    // Clean up temp model
    await import('@/api/model').then(({ deleteModel }) => deleteModel(model.id))
  } catch (e) {
    testResult.value = { success: false, message: e.response?.data?.detail || '连接失败' }
  } finally {
    testing.value = false
  }
}

function next() {
  router.push('/onboarding/photo')
}
</script>

<style scoped>
.step { }
h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: #666; font-size: 13px; margin-bottom: 24px; }
.field { margin-bottom: 16px; }
label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
input, select {
  width: 100%; padding: 10px 12px;
  background: #111; border: 1px solid #333; border-radius: 6px;
  color: #e8e8e8; font-size: 14px;
}
input:focus, select:focus { outline: none; border-color: #7c6fff; }
.btn-test {
  padding: 8px 16px; background: #222; border: 1px solid #444; color: #aaa;
  border-radius: 6px; font-size: 13px; cursor: pointer; margin-bottom: 8px;
}
.ok { color: #6fcf97; font-size: 13px; margin-bottom: 8px; }
.error { color: #ff6b6b; font-size: 13px; margin-bottom: 8px; }
.nav-row { display: flex; justify-content: space-between; margin-top: 16px; }
.btn-back { background: none; border: none; color: #888; font-size: 14px; cursor: pointer; text-decoration: none; align-self: center; }
.btn-primary {
  padding: 10px 20px; background: #7c6fff; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
</style>
