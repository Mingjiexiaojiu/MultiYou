import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    userId: null,
    onboardingDone: false,
  }),

  persist: true,

  actions: {
    async login(username, password) {
      const { data } = await apiLogin(username, password)
      this.token = data.token
      this.userId = data.user_id
      this.onboardingDone = data.onboarding_done
    },

    async register(username, password) {
      await apiRegister(username, password)
      await this.login(username, password)
    },

    logout() {
      this.token = null
      this.userId = null
      this.onboardingDone = false
    },

    markOnboardingDone() {
      this.onboardingDone = true
    },
  },
})
