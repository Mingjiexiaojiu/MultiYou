import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/home' },

  // Auth
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  { path: '/register', component: () => import('@/views/Register.vue'), meta: { public: true } },

  // Onboarding wizard
  {
    path: '/onboarding',
    component: () => import('@/views/onboarding/OnboardingLayout.vue'),
    meta: { public: false, bypassOnboarding: true },
    children: [
      { path: '', redirect: '/onboarding/welcome' },
      { path: 'welcome', component: () => import('@/views/onboarding/Welcome.vue') },
      { path: 'account', component: () => import('@/views/onboarding/AccountSetup.vue') },
      { path: 'model', component: () => import('@/views/onboarding/ModelConfig.vue') },
      { path: 'photo', component: () => import('@/views/onboarding/PhotoUpload.vue') },
      { path: 'persona', component: () => import('@/views/onboarding/PersonaSetup.vue') },
      { path: 'complete', component: () => import('@/views/onboarding/Complete.vue') },
    ],
  },

  // Main app
  { path: '/home', component: () => import('@/views/Home.vue') },
  { path: '/create-avatar', component: () => import('@/views/CreateAvatar.vue') },
  { path: '/chat/:avatarId', component: () => import('@/views/Chat.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  // Not logged in → send to login, except public routes
  if (!auth.token && !to.meta.public) {
    return '/login'
  }

  // Logged in but onboarding incomplete → force wizard
  if (auth.token && !auth.onboardingDone && !to.meta.public && !to.meta.bypassOnboarding) {
    return '/onboarding'
  }
})

export default router
