<template>
  <div class="step">
    <h2>创建账号</h2>
    <p class="sub">第 2 步 / 共 6 步</p>
    <form @submit.prevent="submit">
      <div class="field">
        <label>用户名</label>
        <input v-model="username" type="text" autocomplete="username" required />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" autocomplete="new-password" required />
      </div>
      <div class="field">
        <label>确认密码</label>
        <input v-model="confirm" type="password" autocomplete="new-password" required />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="nav-row">
        <router-link to="/onboarding/welcome" class="btn-back">← 上一步</router-link>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '注册中…' : '下一步 →' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (password.value !== confirm.value) { error.value = '两次密码不一致'; return }
  loading.value = true
  try {
    await auth.register(username.value, password.value)
    router.push('/onboarding/model')
  } catch (e) {
    error.value = e.response?.data?.detail || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.step { }
h2 { font-size: 20px; margin-bottom: 4px; }
.sub { color: #666; font-size: 13px; margin-bottom: 24px; }
.field { margin-bottom: 16px; }
label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
input {
  width: 100%; padding: 10px 12px;
  background: #111; border: 1px solid #333; border-radius: 6px;
  color: #e8e8e8; font-size: 14px;
}
input:focus { outline: none; border-color: #7c6fff; }
.error { color: #ff6b6b; font-size: 13px; margin-bottom: 8px; }
.nav-row { display: flex; justify-content: space-between; margin-top: 16px; }
.btn-back { background: none; border: none; color: #888; font-size: 14px; cursor: pointer; text-decoration: none; align-self: center; }
.btn-primary {
  padding: 10px 20px; background: #7c6fff; color: #fff;
  border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
