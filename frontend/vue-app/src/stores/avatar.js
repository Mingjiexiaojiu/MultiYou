import { defineStore } from 'pinia'
import { listAvatars, listSessions, getLogs } from '@/api/avatar'

export const useAvatarStore = defineStore('avatar', {
  state: () => ({
    avatars: [],
    currentAvatar: null,
    sessions: [],
    currentSession: null,
    chatLogs: [],
  }),

  actions: {
    async fetchAvatars() {
      const { data } = await listAvatars()
      this.avatars = data
    },

    setCurrentAvatar(avatar) {
      this.currentAvatar = avatar
      this.sessions = []
      this.currentSession = null
      this.chatLogs = []
    },

    async fetchSessions(avatarId) {
      const { data } = await listSessions(avatarId)
      this.sessions = data
    },

    async selectSession(session) {
      this.currentSession = session
      const { data } = await getLogs(session.id)
      this.chatLogs = data
    },

    appendLog(log) {
      this.chatLogs.push(log)
    },

    prependSession(session) {
      this.sessions.unshift(session)
      this.currentSession = session
      this.chatLogs = []
    },
  },
})
