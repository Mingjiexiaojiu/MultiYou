<template>
  <div class="chat-page">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="avatar-name">{{ avatarStore.currentAvatar?.name ?? '加载中…' }}</span>
        <button class="btn-icon" @click="newSession" title="新建对话">＋</button>
      </div>
      <SessionList
        :sessions="avatarStore.sessions"
        :active-id="avatarStore.currentSession?.id"
        @select="selectSession"
      />
    </aside>

    <!-- Main chat area -->
    <main class="chat-main">
      <div class="messages" ref="msgEl">
        <ChatMessage
          v-for="log in avatarStore.chatLogs"
          :key="log.id"
          :role="log.role"
          :content="log.content"
          :avatar-img="avatarStore.currentAvatar?.image_path"
        />
        <div v-if="sending" class="typing">
          <span class="dot" /><span class="dot" /><span class="dot" />
        </div>
      </div>

      <form class="input-bar" @submit.prevent="send">
        <textarea
          v-model="message"
          placeholder="输入消息… (Enter 发送，Shift+Enter 换行)"
          rows="1"
          @keydown.enter.exact.prevent="send"
        />
        <button type="submit" :disabled="sending || !message.trim()">发送</button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAvatarStore } from '@/stores/avatar'
import { createSession } from '@/api/avatar'
import { sendMessage } from '@/api/chat'
import SessionList from '@/components/SessionList.vue'
import ChatMessage from '@/components/ChatMessage.vue'

const route = useRoute()
const router = useRouter()
const avatarStore = useAvatarStore()

const message = ref('')
const sending = ref(false)
const msgEl = ref(null)

const avatarId = Number(route.params.avatarId)

onMounted(async () => {
  await avatarStore.fetchAvatars()
  const avatar = avatarStore.avatars.find((a) => a.id === avatarId)
  if (!avatar) return router.push('/home')
  avatarStore.setCurrentAvatar(avatar)
  await avatarStore.fetchSessions(avatarId)
  if (avatarStore.sessions.length) {
    await avatarStore.selectSession(avatarStore.sessions[0])
  }
  scrollToBottom()
})

watch(() => avatarStore.chatLogs.length, scrollToBottom)

async function newSession() {
  const { data } = await createSession(avatarId)
  avatarStore.prependSession(data)
}

async function selectSession(session) {
  await avatarStore.selectSession(session)
  scrollToBottom()
}

async function send() {
  const text = message.value.trim()
  if (!text || !avatarStore.currentSession) return
  message.value = ''
  sending.value = true
  avatarStore.appendLog({ id: Date.now(), role: 'user', content: text })
  try {
    const { data } = await sendMessage(avatarStore.currentSession.id, text)
    avatarStore.appendLog({ id: Date.now() + 1, role: 'assistant', content: data.reply })
  } catch {
    avatarStore.appendLog({ id: Date.now() + 1, role: 'assistant', content: '❌ 发送失败，请重试' })
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (msgEl.value) msgEl.value.scrollTop = msgEl.value.scrollHeight
  })
}
</script>

<style scoped>
.chat-page { display: flex; height: 100vh; }
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #141414;
  border-right: 1px solid #2a2a2a;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #2a2a2a;
}
.avatar-name { font-size: 15px; font-weight: 600; color: #e8e8e8; truncate: overflow; }
.btn-icon { background: none; border: none; color: #7c6fff; font-size: 20px; cursor: pointer; }
.chat-main { flex: 1; display: flex; flex-direction: column; }
.messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.typing { display: flex; gap: 5px; align-items: center; padding: 4px; }
.dot { width: 6px; height: 6px; background: #555; border-radius: 50%; animation: bounce 1.2s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,80%,100% { transform: scale(0.8); } 40% { transform: scale(1.2); } }
.input-bar {
  display: flex;
  gap: 10px;
  padding: 16px;
  border-top: 1px solid #2a2a2a;
  background: #141414;
}
textarea {
  flex: 1;
  padding: 10px 12px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #e8e8e8;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}
textarea:focus { outline: none; border-color: #7c6fff; }
button {
  padding: 10px 20px;
  background: #7c6fff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  align-self: flex-end;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
