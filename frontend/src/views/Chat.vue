<template>
  <div class="chat-container">
    <!-- 左侧对话历史 -->
    <div class="chat-sidebar">
      <div class="kb-selector">
        <el-select
          v-model="currentKbIds"
          placeholder="选择知识库（可多选）"
          size="large"
          style="width: 100%"
          multiple
          collapse-tags
          collapse-tags-tooltip
          @change="onKbChange"
        >
          <el-option
            v-for="kb in knowledgeBases"
            :key="kb.id"
            :label="kb.name"
            :value="kb.id"
          >
            <span>{{ kb.name }}</span>
            <span style="float: right; color: #999; font-size: 12px">{{ kb.document_count }}个文档</span>
          </el-option>
        </el-select>
      </div>
      <el-button type="primary" class="new-chat-btn" @click="newChat">
        <el-icon><Plus /></el-icon> 新建对话
      </el-button>
      <!-- 对话搜索 -->
      <el-input
        v-model="searchKeyword"
        placeholder="搜索对话..."
        clearable
        size="small"
        class="conv-search"
        @input="onSearchInput"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: currentConvId === conv.id }"
          @click="loadConversation(conv.id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <!-- 可编辑标题 -->
          <template v-if="editingConvId === conv.id">
            <el-input
              v-model="editingTitle"
              size="small"
              class="edit-title-input"
              @keydown.enter.prevent="saveConvTitle(conv.id)"
              @keydown.esc.prevent="cancelEditTitle"
              @blur="saveConvTitle(conv.id)"
              @click.stop
              ref="editTitleRef"
            />
          </template>
          <template v-else>
            <span class="conv-title" @dblclick.stop="startEditTitle(conv)">{{ conv.title || conv.knowledge_base_name + ' #' + conv.id }}</span>
          </template>
          <el-icon
            class="edit-btn"
            :class="{ hidden: editingConvId === conv.id }"
            @click.stop="startEditTitle(conv)"
          ><EditPen /></el-icon>
          <el-icon class="delete-btn" @click.stop="deleteConv(conv.id)"><Delete /></el-icon>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <div class="messages-container" ref="messagesRef">
        <div v-if="messages.length === 0" class="empty-state">
          <h2>🎓 智能知识问答</h2>
          <p v-if="currentKbIds.length > 0">选择知识库后开始提问</p>
          <p v-else>请先选择一个知识库</p>
          <div class="quick-questions" v-if="currentKbIds.length > 0">
            <el-tag
              v-for="q in quickQuestions"
              :key="q"
              class="quick-tag"
              @click="sendQuickQuestion(q)"
            >{{ q }}</el-tag>
          </div>
        </div>
        <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="36" style="background:#409eff">我</el-avatar>
            <el-avatar v-else :size="36" style="background:#67c23a">AI</el-avatar>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
            <!-- 流式输入光标 -->
            <span v-if="msg.role === 'assistant' && msg === streamingMsg && sending" class="streaming-cursor"></span>
            <!-- 来源引用 -->
            <div v-if="msg.sources && msg.sources.length > 0" class="sources-section">
              <div class="sources-title">
                <el-icon><Document /></el-icon> 参考来源
              </div>
              <div v-for="(src, si) in msg.sources" :key="si" class="source-item">
                <div class="source-header">
                  <el-tag size="small" type="info">{{ src.document_name }}</el-tag>
                  <span class="source-page">段落 {{ src.chunk_index + 1 }}</span>
                </div>
                <div class="source-content">{{ src.content }}</div>
              </div>
            </div>
            <!-- 消息反馈 + 重新生成 -->
            <div v-if="msg.role === 'assistant'" class="message-actions">
              <el-button
                :type="msg.feedback === 'like' ? 'primary' : 'default'"
                size="small"
                circle
                class="feedback-btn"
                :class="{ active: msg.feedback === 'like' }"
                @click="setFeedback(msg, 'like')"
              >
                <el-icon><Pointer /></el-icon>
              </el-button>
              <el-button
                :type="msg.feedback === 'dislike' ? 'danger' : 'default'"
                size="small"
                circle
                class="feedback-btn dislike-btn"
                :class="{ active: msg.feedback === 'dislike' }"
                @click="setFeedback(msg, 'dislike')"
              >
                <el-icon class="dislike-icon"><Pointer /></el-icon>
              </el-button>
              <!-- 重新生成按钮 - 仅最后一条 assistant 消息 -->
              <el-button
                v-if="idx === lastAssistantIndex && !sending"
                size="small"
                type="warning"
                plain
                class="regenerate-btn"
                @click="regenerate(msg, idx)"
              >
                <el-icon><Refresh /></el-icon> 重新生成
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-wrapper">
        <!-- 快捷设置面板 -->
        <div class="settings-bar">
          <el-popover
            placement="top-start"
            :width="280"
            trigger="click"
            popper-class="settings-popover"
          >
            <template #reference>
              <el-button size="small" text type="info" class="settings-trigger">
                <el-icon><Setting /></el-icon> 参数设置
              </el-button>
            </template>
            <div class="settings-panel">
              <div class="setting-item">
                <span class="setting-label">Prompt 模板</span>
                <el-select
                  v-model="selectedPromptTemplateId"
                  placeholder="默认模板"
                  size="small"
                  clearable
                  style="flex: 1; margin: 0 12px"
                  @change="onTemplateChange"
                >
                  <el-option
                    v-for="t in promptTemplates"
                    :key="t.id"
                    :label="t.name"
                    :value="t.id"
                  />
                </el-select>
              </div>
              <div class="setting-item">
                <span class="setting-label">Top K</span>
                <el-slider
                  v-model="topK"
                  :min="1"
                  :max="10"
                  :step="1"
                  show-stops
                  style="flex: 1; margin: 0 12px"
                />
                <span class="setting-value">{{ topK }}</span>
              </div>
              <div class="setting-item">
                <span class="setting-label">Temperature</span>
                <el-slider
                  v-model="temperature"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  style="flex: 1; margin: 0 12px"
                />
                <span class="setting-value">{{ temperature.toFixed(2) }}</span>
              </div>
            </div>
          </el-popover>
        </div>
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            :placeholder="currentKbIds.length > 0 ? '请输入您的问题...' : '请先选择知识库'"
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="sending || currentKbIds.length === 0"
            resize="none"
          />
          <el-button type="primary" :loading="sending" @click="sendMessage" :disabled="!inputText.trim() || currentKbIds.length === 0" class="send-btn">
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { Plus, Delete, ChatDotRound, Document, Promotion, Search, EditPen, Refresh, Pointer, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import { streamChat, chatAPI, knowledgeBaseAPI, promptTemplateAPI } from '../api'

const messages = ref([])
const conversations = ref([])
const knowledgeBases = ref([])
const currentConvId = ref('')
const currentKbIds = ref([])
const inputText = ref('')
const sending = ref(false)
const messagesRef = ref(null)
const streamController = ref(null)
const streamingMsg = ref(null)
const isStreaming = ref(false)

// 对话搜索
const searchKeyword = ref('')
let searchTimer = null

// 对话标题编辑
const editingConvId = ref('')
const editingTitle = ref('')
const editTitleRef = ref(null)

// 快捷设置
const topK = ref(4)
const temperature = ref(0.3)
const promptTemplates = ref([])
const selectedPromptTemplateId = ref(null)

const quickQuestions = [
  '这篇文档的主要内容是什么？',
  '请总结一下关键要点',
  '有哪些重要的规定？',
  '请解释一下相关条款',
]

// 最后一条 assistant 消息的索引
const lastAssistantIndex = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant') return i
  }
  return -1
})

onMounted(async () => {
  await Promise.all([loadKnowledgeBases(), loadPromptTemplates()])
  loadConversations()
})

function renderMarkdown(text) {
  return marked.parse(text || '')
}

async function loadKnowledgeBases() {
  try {
    const { data } = await knowledgeBaseAPI.list()
    knowledgeBases.value = data
    if (data.length > 0 && currentKbIds.value.length === 0) {
      currentKbIds.value = [data[0].id]
    }
  } catch {}
}

async function loadPromptTemplates() {
  try {
    const { data } = await promptTemplateAPI.list()
    promptTemplates.value = data
  } catch {}
}

function onKbChange() {
  newChat()
}

function onTemplateChange(templateId) {
  if (!templateId) return
  const t = promptTemplates.value.find(t => t.id === templateId)
  if (t) {
    if (t.default_top_k) topK.value = t.default_top_k
    if (t.default_temperature != null) temperature.value = t.default_temperature
  }
}

// ========== 对话搜索 ==========
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadConversations(searchKeyword.value.trim())
  }, 300)
}

async function loadConversations(keyword) {
  try {
    const params = {}
    if (keyword) params.keyword = keyword
    const { data } = await chatAPI.getConversations(params)
    conversations.value = data
  } catch {}
}

async function loadConversation(id) {
  if (editingConvId.value === id) return
  currentConvId.value = id
  try {
    const { data } = await chatAPI.getConversation(id)
    messages.value = (data.messages || []).map(m => {
      // sources 在数据库中是 JSON 字符串，需要解析
      let sources = m.sources
      if (typeof sources === 'string') {
        try { sources = JSON.parse(sources) } catch { sources = [] }
      }
      return {
        ...m,
        sources: Array.isArray(sources) ? sources : [],
        feedback: m.feedback || '',
      }
    })
    // 设置当前知识库为对话对应的知识库
    if (data.knowledge_base_id) {
      currentKbIds.value = [data.knowledge_base_id]
    }
    scrollToBottom()
  } catch {}
}

function newChat() {
  currentConvId.value = ''
  messages.value = []
}

async function deleteConv(id) {
  await ElMessageBox.confirm('确定删除该对话？', '提示', { type: 'warning' })
  await chatAPI.deleteConversation(id)
  if (currentConvId.value === id) newChat()
  loadConversations(searchKeyword.value.trim())
  ElMessage.success('已删除')
}

function sendQuickQuestion(q) {
  inputText.value = q
  sendMessage()
}

// ========== 对话标题编辑 ==========
function startEditTitle(conv) {
  editingConvId.value = conv.id
  editingTitle.value = conv.title || conv.knowledge_base_name + ' #' + conv.id
  nextTick(() => {
    const inputEl = editTitleRef.value
    if (inputEl) {
      const inner = inputEl.$el ? inputEl.$el.querySelector('input') : inputEl
      if (inner) inner.select()
    }
  })
}

function cancelEditTitle() {
  editingConvId.value = ''
  editingTitle.value = ''
}

async function saveConvTitle(id) {
  const title = editingTitle.value.trim()
  editingConvId.value = ''
  if (!title) return
  try {
    await chatAPI.updateConversation(id, { title })
    const conv = conversations.value.find(c => c.id === id)
    if (conv) conv.title = title
    ElMessage.success('标题已更新')
  } catch {
    ElMessage.error('更新标题失败')
  }
}

// ========== 消息反馈 ==========
async function setFeedback(msg, type) {
  if (!msg.id) {
    ElMessage.warning('消息尚未保存完成，请稍后再试')
    return
  }
  const newFeedback = msg.feedback === type ? '' : type
  msg.feedback = newFeedback
  try {
    await chatAPI.updateMessageFeedback(msg.id, { feedback: newFeedback })
  } catch {
    msg.feedback = ''
    ElMessage.error('反馈失败')
  }
}

// ========== 重新生成 ==========
async function regenerate(msg, idx) {
  if (sending.value) return
  sending.value = true
  isStreaming.value = true

  // 找到对应的用户消息
  let userMsgId = null
  for (let i = idx - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') {
      userMsgId = messages.value[i].id
      break
    }
  }
  if (!userMsgId) {
    // 如果找不到用户消息ID，用新消息方式
    sending.value = false
    ElMessage.error('无法重新生成：找不到对应的消息')
    return
  }

  // 清空该消息内容
  msg.content = ''
  msg.sources = []
  msg.feedback = ''
  streamingMsg.value = msg
  scrollToBottom()

  const requestData = {
    message_id: userMsgId,
    conversation_id: currentConvId.value,
    top_k: topK.value,
    temperature: temperature.value,
    system_prompt_id: selectedPromptTemplateId.value || undefined,
  }

  streamController.value = streamChat(requestData, {
    onSources(sourcesData) {
      const sources = Array.isArray(sourcesData) ? sourcesData : (sourcesData?.sources || sourcesData?.data || [])
      msg.sources = sources
      scrollToBottom()
    },
    onToken(token) {
      const text = typeof token === 'string' ? token : (token?.token || token?.content || token?.data || '')
      msg.content += text
      scrollToBottom()
    },
    onDone(doneData) {
      sending.value = false
      isStreaming.value = false
      streamController.value = null
      streamingMsg.value = null
      if (doneData?.message_id) {
        msg.id = doneData.message_id
      }
      // 更新 user message ID
      if (doneData?.user_message_id) {
        const userMsg = messages.value.find(m => m.role === 'user' && !m.id)
        if (userMsg) userMsg.id = doneData.user_message_id
      }
      loadConversations(searchKeyword.value.trim())
    },
    onError(err) {
      sending.value = false
      isStreaming.value = false
      streamController.value = null
      streamingMsg.value = null
      if (!msg.content) {
        msg.content = err?.message || '抱歉，系统出现了错误，请稍后再试。'
      }
      ElMessage.error(err?.message || '请求失败')
    },
  }, '/api/chat/regenerate')
}

// ========== 发送消息 (SSE 流式) ==========
function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value || currentKbIds.value.length === 0) return

  // 添加用户消息到界面
  messages.value.push({ role: 'user', content: text, sources: [], feedback: '' })
  inputText.value = ''
  sending.value = true
  isStreaming.value = true

  // 立即添加一个空的 assistant 消息
  const assistantMsg = { role: 'assistant', content: '', sources: [], feedback: '', id: null }
  messages.value.push(assistantMsg)
  streamingMsg.value = assistantMsg
  scrollToBottom()

  const requestData = {
    message: text,
    knowledge_base_ids: currentKbIds.value,
    conversation_id: currentConvId.value || undefined,
    top_k: topK.value,
    temperature: temperature.value,
    system_prompt_id: selectedPromptTemplateId.value || undefined,
  }

  streamController.value = streamChat(requestData, {
    onSources(sourcesData) {
      const sources = Array.isArray(sourcesData) ? sourcesData : (sourcesData?.sources || sourcesData?.data || [])
      assistantMsg.sources = sources
      scrollToBottom()
    },
    onToken(token) {
      const text = typeof token === 'string' ? token : (token?.token || token?.content || token?.data || '')
      assistantMsg.content += text
      scrollToBottom()
    },
    onDone(doneData) {
      sending.value = false
      isStreaming.value = false
      streamController.value = null
      streamingMsg.value = null
      if (doneData?.conversation_id) {
        currentConvId.value = doneData.conversation_id
      }
      if (doneData?.message_id) {
        assistantMsg.id = doneData.message_id
      }
      // 保存 user message ID（用于反馈和重新生成）
      if (doneData?.user_message_id) {
        const userMsg = messages.value.find(m => m.role === 'user' && !m.id)
        if (userMsg) userMsg.id = doneData.user_message_id
      }
      loadConversations(searchKeyword.value.trim())
    },
    onError(err) {
      sending.value = false
      isStreaming.value = false
      streamController.value = null
      streamingMsg.value = null
      if (!assistantMsg.content) {
        assistantMsg.content = err?.message || '抱歉，系统出现了错误，请稍后再试。'
      }
      ElMessage.error(err?.message || '请求失败')
    },
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}
.chat-sidebar {
  width: 280px;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  padding: 16px;
}
.kb-selector {
  margin-bottom: 12px;
}
.new-chat-btn {
  width: 100%;
  margin-bottom: 12px;
}
.conv-search {
  margin-bottom: 12px;
}
.conversation-list {
  flex: 1;
  overflow-y: auto;
}
.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}
.conversation-item:hover {
  background: #f5f7fa;
}
.conversation-item.active {
  background: #ecf5ff;
  color: #409eff;
}
.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.edit-title-input {
  flex: 1;
}
.edit-title-input :deep(.el-input__inner) {
  height: 24px;
  font-size: 13px;
}
.edit-btn {
  opacity: 0;
  transition: opacity 0.2s;
  color: #909399;
  font-size: 14px;
}
.conversation-item:hover .edit-btn {
  opacity: 0.6;
}
.edit-btn:hover {
  opacity: 1 !important;
  color: #409eff;
}
.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
  color: #f56c6c;
}
.conversation-item:hover .delete-btn {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.empty-state {
  text-align: center;
  padding-top: 120px;
  color: #999;
}
.empty-state h2 {
  font-size: 28px;
  color: #333;
  margin-bottom: 12px;
}
.quick-questions {
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.quick-tag {
  cursor: pointer;
  font-size: 14px;
}
.quick-tag:hover {
  color: #409eff;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.message.user {
  flex-direction: row-reverse;
}
.message.user .message-content {
  align-items: flex-end;
}
.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}
.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.message.user .message-text {
  background: #409eff;
  color: #fff;
  border-top-right-radius: 4px;
}
.message.assistant .message-text {
  background: #f4f4f5;
  color: #333;
  border-top-left-radius: 4px;
}

.sources-section {
  margin-top: 8px;
  padding: 10px 14px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #eee;
}
.sources-title {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.source-item {
  padding: 6px 0;
  border-bottom: 1px dashed #eee;
}
.source-item:last-child {
  border-bottom: none;
}
.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.source-page {
  font-size: 12px;
  color: #999;
}
.source-content {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

/* 消息反馈 & 重新生成 */
.message-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}
.feedback-btn {
  width: 28px;
  height: 28px;
  font-size: 12px;
}
.feedback-btn.active {
  transform: scale(1.15);
}
.dislike-icon {
  transform: rotate(180deg);
}
.regenerate-btn {
  margin-left: 4px;
  font-size: 12px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f4f4f5;
  border-radius: 12px;
}
.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  animation: bounce 1.4s infinite ease-in-out;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #333;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.input-wrapper {
  border-top: 1px solid #eee;
}
.settings-bar {
  padding: 6px 24px 0;
  display: flex;
  align-items: center;
}
.settings-trigger {
  font-size: 13px;
}
.input-area {
  padding: 10px 24px 16px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.input-area :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
}
.send-btn {
  height: 44px;
  width: 44px;
  border-radius: 12px;
  padding: 0;
}
</style>

<style>
.settings-popover .settings-panel {
  padding: 8px 0;
}
.settings-popover .setting-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  margin-bottom: 8px;
}
.settings-popover .setting-item:last-child {
  margin-bottom: 0;
}
.settings-popover .setting-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  min-width: 80px;
}
.settings-popover .setting-value {
  font-size: 13px;
  color: #409eff;
  font-weight: 600;
  min-width: 32px;
  text-align: right;
}
</style>
