import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器 - 添加 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 - 处理 401 和超时
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    // 超时或网络错误给出提示
    if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请稍后重试'
    } else if (!error.response) {
      error.message = '网络连接失败'
    }
    return Promise.reject(error)
  }
)

// ========== SSE 流式聊天工具函数 ==========
export function streamChat(data, { onSources, onToken, onDone, onError }, url = '/api/chat/stream') {
  const token = localStorage.getItem('token')
  const controller = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
    signal: controller.signal,
  })
    .then((response) => {
      if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }
      if (!response.ok) {
        // 尝试读取后端返回的错误详情
        return response.json().catch(() => null).then((errorBody) => {
          const detail = errorBody?.detail
          throw new Error(detail || `请求失败 (${response.status})`)
        })
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''

      function processChunk({ done, value }) {
        if (done) return
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) {
            currentEvent = ''
            continue
          }
          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim()
            continue
          }
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.slice(5).trim()
            if (!jsonStr) continue
            try {
              const parsed = JSON.parse(jsonStr)
              switch (currentEvent) {
                case 'sources':
                  onSources?.(parsed)
                  break
                case 'token':
                  onToken?.(parsed)
                  break
                case 'done':
                  onDone?.(parsed)
                  break
                default:
                  if (parsed.type) {
                    if (parsed.type === 'sources') onSources?.(parsed.data)
                    else if (parsed.type === 'token') onToken?.(parsed.data)
                    else if (parsed.type === 'done') onDone?.(parsed.data)
                  }
              }
            } catch {
              // 非 JSON 的 token 文本
              if (currentEvent === 'token') {
                onToken?.(jsonStr)
              }
            }
            currentEvent = ''
          }
        }
        return reader.read().then(processChunk)
      }

      return reader.read().then(processChunk)
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

  return controller
}

// ========== 认证 API ==========
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/password', data),
  getStats: () => api.get('/auth/stats'),
}

// ========== 知识库 API ==========
export const knowledgeBaseAPI = {
  list: () => api.get('/knowledge-base'),
  create: (data) => api.post('/knowledge-base', data),
  get: (id) => api.get(`/knowledge-base/${id}`),
  update: (id, data) => api.put(`/knowledge-base/${id}`, data),
  delete: (id) => api.delete(`/knowledge-base/${id}`),
  getDocuments: (id, params) => api.get(`/knowledge-base/${id}/documents`, { params }),
  uploadDocument: (id, formData) => api.post(`/knowledge-base/${id}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }),
  batchUploadDocuments: (id, formData) => api.post(`/knowledge-base/${id}/documents/batch`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }),
}

// ========== 文档 API ==========
export const documentAPI = {
  delete: (id) => api.delete(`/documents/${id}`),
  preview: (id) => api.get(`/documents/${id}/preview`),
  reprocess: (id) => api.post(`/documents/${id}/reprocess`),
}

// ========== 对话 API ==========
export const chatAPI = {
  send: (data) => api.post('/chat', data),
  regenerate: (data) => api.post('/chat/regenerate', data),
  getConversations: (params) => api.get('/chat/conversations', { params }),
  getConversation: (id) => api.get(`/chat/conversations/${id}`),
  updateConversation: (id, data) => api.put(`/chat/conversations/${id}`, data),
  deleteConversation: (id) => api.delete(`/chat/conversations/${id}`),
  updateMessageFeedback: (id, data) => api.put(`/chat/messages/${id}/feedback`, data),
}

// ========== 提示词模板 API ==========
export const promptTemplateAPI = {
  list: () => api.get('/prompt-templates'),
  create: (data) => api.post('/prompt-templates', data),
  update: (id, data) => api.put(`/prompt-templates/${id}`, data),
  delete: (id) => api.delete(`/prompt-templates/${id}`),
}

// ========== 管理员 API ==========
export const adminAPI = {
  getUsers: () => api.get('/admin/users'),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  toggleRole: (id) => api.put(`/admin/users/${id}/role`),
  getStats: () => api.get('/admin/stats'),
  getLogs: (params) => api.get('/admin/logs', { params }),
  // 审核
  getReviewKBs: () => api.get('/admin/review/knowledge-bases'),
  approveKB: (id) => api.put(`/admin/review/knowledge-bases/${id}/approve`),
  rejectKB: (id, data) => api.put(`/admin/review/knowledge-bases/${id}/reject`, data),
  takedownKB: (id) => api.put(`/admin/review/knowledge-bases/${id}/takedown`),
  getReports: (params) => api.get('/admin/review/reports', { params }),
  resolveReport: (id, data) => api.put(`/admin/review/reports/${id}/resolve`, data),
}

// ========== 互动 API ==========
export const interactAPI = {
  // 分享
  searchUsers: (keyword) => api.get('/interact/users/search', { params: { keyword } }),
  shareKB: (kbId, userId) => api.post(`/interact/knowledge-base/${kbId}/share`, { user_id: userId }),
  unshareKB: (kbId, userId) => api.delete(`/interact/knowledge-base/${kbId}/share/${userId}`),
  getShares: (kbId) => api.get(`/interact/knowledge-base/${kbId}/shares`),
  setVisibility: (kbId, visibility) => api.put(`/interact/knowledge-base/${kbId}/visibility`, { visibility }),
  // 投票
  voteKB: (kbId, voteType) => api.post(`/interact/knowledge-base/${kbId}/vote`, { vote_type: voteType }),
  getVotes: (kbId) => api.get(`/interact/knowledge-base/${kbId}/votes`),
  // 举报
  reportDocument: (docId, reason) => api.post(`/interact/document/${docId}/report`, { reason }),
  // 收藏
  toggleFavorite: (docId) => api.post(`/interact/document/${docId}/favorite`),
  toggleKBFavorite: (kbId) => api.post(`/interact/knowledge-base/${kbId}/favorite`),
  getFavorites: () => api.get('/interact/favorites'),
}

export default api
