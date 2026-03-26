import { defineStore } from 'pinia'

export const useOnboardingStore = defineStore('onboarding', {
  state: () => ({
    // Step 3 — Model config
    provider: 'deepseek',
    endpoint: 'https://api.deepseek.com',
    modelIdStr: 'deepseek-chat',
    apiKey: '',
    isLocal: false,

    // Step 4 — Photo
    croppedBlob: null,

    // Step 5 — Persona / Avatar
    avatarName: '',
    personaName: '',
    systemPrompt: '',
  }),
})
