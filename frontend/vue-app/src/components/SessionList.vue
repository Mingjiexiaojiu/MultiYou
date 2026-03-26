<template>
  <div class="session-list">
    <div
      v-for="session in sessions"
      :key="session.id"
      :class="['item', { active: session.id === activeId }]"
      @click="$emit('select', session)"
    >
      <span class="title">{{ session.title }}</span>
      <span class="ts">{{ formatDate(session.updated_at) }}</span>
    </div>
    <div v-if="!sessions.length" class="empty">暂无会话</div>
  </div>
</template>

<script setup>
defineProps({
  sessions: { type: Array, default: () => [] },
  activeId: { type: Number, default: null },
})
defineEmits(['select'])

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.session-list { flex: 1; overflow-y: auto; padding: 8px; }
.item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 2px;
  transition: background 0.15s;
}
.item:hover { background: #2a2a2a; }
.item.active { background: #2a2a3a; border-left: 3px solid #7c6fff; padding-left: 9px; }
.title { display: block; font-size: 13px; color: #ddd; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ts { display: block; font-size: 11px; color: #555; margin-top: 2px; }
.empty { text-align: center; padding: 20px; color: #555; font-size: 13px; }
</style>
