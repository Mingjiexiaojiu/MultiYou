<template>
  <div class="step">
    <h2>设置分身角色</h2>
    <p class="sub">第 5 步 / 共 6 步</p>

    <div class="field">
      <label>分身名称</label>
      <input v-model="wizard.avatarName" type="text" placeholder="例如：我的助手" />
    </div>

    <div class="field">
      <label>角色名称</label>
      <input v-model="wizard.personaName" type="text" placeholder="例如：全能助理" />
    </div>

    <div class="field">
      <label>系统提示词 (System Prompt)</label>
      <textarea
        v-model="wizard.systemPrompt"
        rows="6"
        placeholder="你是一个专业的助手，擅长代码、写作和分析。回答简洁专业。"
      />
    </div>

    <div class="nav-row">
      <router-link to="/onboarding/photo" class="btn-back">← 上一步</router-link>
      <button class="btn-primary" :disabled="!ready" @click="next">下一步 →</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboardingStore } from '@/stores/onboarding'

const router = useRouter()
const wizard = useOnboardingStore()
const ready = computed(() => wizard.avatarName && wizard.personaName && wizard.systemPrompt)
function next() { router.push('/onboarding/complete') }
</script>

<style scoped>
.step { }
h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: #666; font-size: 13px; margin-bottom: 24px; }
.field { margin-bottom: 16px; }
label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
input, textarea {
  width: 100%; padding: 10px 12px;
  background: #111; border: 1px solid #333; border-radius: 6px;
  color: #e8e8e8; font-size: 14px; font-family: inherit;
}
input:focus, textarea:focus { outline: none; border-color: #7c6fff; }
textarea { resize: vertical; }
.nav-row { display: flex; justify-content: space-between; margin-top: 16px; }
.btn-back { background: none; border: none; color: #888; font-size: 14px; cursor: pointer; text-decoration: none; align-self: center; }
.btn-primary {
  padding: 10px 20px; background: #7c6fff; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
