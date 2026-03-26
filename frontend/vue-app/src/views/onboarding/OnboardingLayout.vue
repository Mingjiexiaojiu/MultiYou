<template>
  <div class="onboarding-shell">
    <!-- Step indicator -->
    <div class="step-indicator">
      <span
        v-for="n in 6"
        :key="n"
        :class="['dot', { active: n === currentStep, done: n < currentStep }]"
      />
    </div>

    <div class="wizard-body">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const stepMap = {
  '/onboarding/welcome': 1,
  '/onboarding/account': 2,
  '/onboarding/model': 3,
  '/onboarding/photo': 4,
  '/onboarding/persona': 5,
  '/onboarding/complete': 6,
}
const currentStep = computed(() => stepMap[route.path] ?? 1)
</script>

<style scoped>
.onboarding-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  background: #0f0f0f;
  padding: 40px 20px;
}
.step-indicator { display: flex; gap: 10px; margin-bottom: 40px; }
.dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #333;
  transition: background 0.3s;
}
.dot.active { background: #7c6fff; }
.dot.done { background: #5a5a8a; }
.wizard-body { width: 100%; max-width: 500px; }
</style>
