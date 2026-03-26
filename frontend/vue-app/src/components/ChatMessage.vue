<template>
  <div :class="['msg', role]">
    <img
      v-if="role === 'assistant' && avatarImg"
      :src="`http://localhost:8000${avatarImg}`"
      class="bubble-avatar"
    />
    <div class="bubble">
      <pre class="content">{{ content }}</pre>
    </div>
  </div>
</template>

<script setup>
defineProps({
  role: { type: String, required: true },   // 'user' | 'assistant'
  content: { type: String, required: true },
  avatarImg: { type: String, default: null },
})
</script>

<style scoped>
.msg { display: flex; gap: 10px; max-width: 85%; }
.msg.user { flex-direction: row-reverse; align-self: flex-end; }
.msg.assistant { align-self: flex-start; }
.bubble-avatar {
  width: 36px; height: 36px;
  border-radius: 4px;
  image-rendering: pixelated;
  flex-shrink: 0;
  align-self: flex-end;
}
.bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 100%;
}
.user .bubble { background: #7c6fff; color: #fff; border-bottom-right-radius: 4px; }
.assistant .bubble { background: #1e1e1e; border: 1px solid #2a2a2a; border-bottom-left-radius: 4px; }
.content { white-space: pre-wrap; word-break: break-word; font-family: inherit; margin: 0; }
</style>
