<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>MultiYou</h1>
      <h2>登录</h2>
      <form @submit.prevent="submit">
        <div class="field">
          <label>用户名</label>
          <input v-model="username" type="text" autocomplete="username" required />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '登录中…' : '登录' }}</button>
      </form>
      <p class="link">没有账号？<router-link to="/register">注册</router-link></p>
    </div>
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
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push(auth.onboardingDone ? '/home' : '/onboarding')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #0f0f0f;
}
.auth-card {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 40px;
  width: 360px;
}
h1 { font-size: 24px; color: #7c6fff; margin-bottom: 8px; }
h2 { font-size: 18px; color: #aaa; margin-bottom: 24px; }
.field { margin-bottom: 16px; }
label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
input {
  width: 100%;
  padding: 10px 12px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e8e8e8;
  font-size: 14px;
}
input:focus { outline: none; border-color: #7c6fff; }
button {
  width: 100%;
  padding: 12px;
  background: #7c6fff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  margin-top: 8px;
}
button:disabled { opacity: 0.6; cursor: not-allowed; }
.error { color: #ff6b6b; font-size: 13px; margin-bottom: 8px; }
.link { text-align: center; margin-top: 16px; font-size: 13px; color: #888; }
.link a { color: #7c6fff; text-decoration: none; }
</style>
