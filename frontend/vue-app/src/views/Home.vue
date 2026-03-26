<template>
  <div class="home">
    <header class="topbar">
      <span class="brand">MultiYou</span>
      <button class="btn-ghost" @click="router.push('/create-avatar')">+ 创建分身</button>
    </header>

    <main class="grid" v-if="store.avatars.length">
      <div
        v-for="avatar in store.avatars"
        :key="avatar.id"
        class="card"
        @click="router.push(`/chat/${avatar.id}`)"
      >
        <img
          v-if="avatar.image_path"
          :src="`http://localhost:8000${avatar.image_path}`"
          class="avatar-img"
        />
        <div v-else class="avatar-placeholder">{{ avatar.name?.[0] ?? '?' }}</div>
        <div class="card-info">
          <p class="card-name">{{ avatar.name }}</p>
          <p class="card-persona">{{ avatar.persona?.name }}</p>
        </div>
      </div>
    </main>

    <div v-else class="empty">
      <p>还没有分身，点击右上角创建第一个吧</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAvatarStore } from '@/stores/avatar'

const router = useRouter()
const store = useAvatarStore()

onMounted(() => store.fetchAvatars())
</script>

<style scoped>
.home { display: flex; flex-direction: column; height: 100vh; }
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}
.brand { font-size: 18px; font-weight: 600; color: #7c6fff; }
.btn-ghost {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #7c6fff;
  color: #7c6fff;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.btn-ghost:hover { background: #7c6fff22; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
  padding: 24px;
  overflow-y: auto;
}
.card {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s, transform 0.15s;
}
.card:hover { border-color: #7c6fff; transform: translateY(-2px); }
.avatar-img { width: 100%; aspect-ratio: 1; object-fit: cover; image-rendering: pixelated; }
.avatar-placeholder {
  width: 100%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  background: #2a2a2a;
  color: #555;
}
.card-info { padding: 12px; }
.card-name { font-size: 14px; font-weight: 500; }
.card-persona { font-size: 12px; color: #888; margin-top: 4px; }
.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  font-size: 15px;
}
</style>
