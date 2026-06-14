<template>
  <div class="documents-page">
    <div class="page-header">
      <div class="header-left">
        <h3>文档管理</h3>
        <el-select
          v-model="currentKbId"
          placeholder="选择知识库"
          size="large"
          style="width: 200px; margin-left: 16px"
          @change="onKbChange"
        >
          <el-option
            v-for="kb in knowledgeBases"
            :key="kb.id"
            :label="kb.name"
            :value="kb.id"
          />
        </el-select>
      </div>
      <div class="header-right">
        <el-input
          v-if="currentKbId"
          v-model="searchKeyword"
          placeholder="搜索文件名..."
          clearable
          style="width: 220px; margin-right: 12px"
          @input="onSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-upload
          v-if="currentKbId"
          :http-request="handleUpload"
          :show-file-list="false"
          :multiple="true"
          :limit="10"
          accept=".pdf,.txt,.md,.markdown,.docx,.xlsx,.pptx,.html,.csv"
        >
          <el-button type="primary" :loading="uploading">
            <el-icon><Upload /></el-icon> 上传文档
          </el-button>
        </el-upload>
      </div>
    </div>

    <!-- 批量上传进度 -->
    <div v-if="uploading" class="upload-progress-section">
      <div class="upload-progress-header">
        <span>正在上传 {{ uploadProgress.current }} / {{ uploadProgress.total }} 个文件...</span>
      </div>
      <el-progress
        :percentage="uploadProgressPercent"
        :stroke-width="10"
        striped
        striped-flow
      />
      <div class="upload-progress-detail">
        <span class="upload-success">成功: {{ uploadProgress.success }}</span>
        <span class="upload-fail">失败: {{ uploadProgress.fail }}</span>
      </div>
    </div>

    <!-- 上传完成后结果提示 -->
    <div v-if="uploadResult" class="upload-result" :class="uploadResult.type">
      <span>{{ uploadResult.message }}</span>
      <el-button text size="small" @click="uploadResult = null">关闭</el-button>
    </div>

    <el-empty v-if="!currentKbId" description="请先选择一个知识库" />

    <el-table v-else :data="filteredDocuments" style="width: 100%" v-loading="loading">
      <el-table-column prop="filename" label="文件名" min-width="200">
        <template #default="{ row }">
          <div class="filename-cell">
            <el-icon class="file-type-icon" :style="{ color: getFileIconColor(row.filename) }">
              <Document />
            </el-icon>
            <span>{{ row.filename }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="文件大小" width="110">
        <template #default="{ row }">
          <span v-if="row.file_size">{{ formatFileSize(row.file_size) }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="chunk_count" label="分块数" width="90">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ row.chunk_count ?? 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="110">
        <template #default="{ row }">
          <el-tag
            v-if="row.status === 'completed' || row.status === 'ready'"
            type="success"
            size="small"
            effect="light"
          >
            <el-icon style="margin-right: 2px"><CircleCheckFilled /></el-icon> 就绪
          </el-tag>
          <el-tag
            v-else-if="row.status === 'processing'"
            type="warning"
            size="small"
            effect="light"
          >
            <el-icon class="rotating" style="margin-right: 2px"><Loading /></el-icon> 处理中
          </el-tag>
          <el-tag
            v-else
            type="danger"
            size="small"
            effect="light"
          >
            <el-icon style="margin-right: 2px"><CircleCloseFilled /></el-icon> {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="180" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text size="small" @click="handlePreview(row)">
            <el-icon><View /></el-icon> 预览
          </el-button>
          <!-- 收藏按钮（所有用户可用） -->
          <el-button
            :type="row._favorited ? 'warning' : 'default'"
            text size="small"
            @click="handleFavorite(row)"
          >
            <el-icon><StarFilled v-if="row._favorited" /><Star v-else /></el-icon>
            {{ row._favorited ? '已收藏' : '收藏' }}
          </el-button>
          <!-- 举报按钮（非创建者可用） -->
          <el-button
            v-if="!isOwner"
            type="danger"
            text size="small"
            @click="handleReport(row)"
          >
            <el-icon><Warning /></el-icon> 举报
          </el-button>
          <!-- 仅创建者可见：重新处理、删除 -->
          <template v-if="isOwner">
            <el-button
              v-if="row.status !== 'completed' && row.status !== 'ready' && row.status !== 'processing'"
              type="warning"
              text
              size="small"
              :loading="row._reprocessing"
              @click="handleReprocess(row)"
            >
              <el-icon><RefreshRight /></el-icon> 重处理
            </el-button>
            <el-button type="danger" text size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 文档预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewDoc?.filename ? `预览 - ${previewDoc.filename}` : '文档预览'"
      width="700px"
      destroy-on-close
    >
      <div v-loading="previewLoading">
        <template v-if="previewData">
          <div class="preview-section">
            <h4>内容预览</h4>
            <div class="preview-content">{{ previewData.preview_content || '暂无内容' }}</div>
          </div>
          <div class="preview-section">
            <div class="preview-chunks-header">
              <h4>分块列表</h4>
              <el-tag size="small" type="info">共 {{ previewData.total_chunks ?? previewData.chunks?.length ?? 0 }} 个分块</el-tag>
            </div>
            <div class="preview-chunks-list">
              <div
                v-for="chunk in previewData.chunks"
                :key="chunk.chunk_index"
                class="preview-chunk-item"
              >
                <div class="chunk-index">分块 #{{ chunk.chunk_index }}</div>
                <div class="chunk-content">{{ chunk.content }}</div>
              </div>
              <el-empty v-if="!previewData.chunks?.length" description="暂无分块" :image-size="60" />
            </div>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  Upload, Delete, Search, View, RefreshRight, Document,
  CircleCheckFilled, CircleCloseFilled, Loading,
  Star, StarFilled, Warning
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeBaseAPI, documentAPI, interactAPI } from '../api'

const route = useRoute()
const documents = ref([])
const knowledgeBases = ref([])
const currentKbId = ref('')
const loading = ref(false)
const searchKeyword = ref('')

// 上传相关
const uploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0, success: 0, fail: 0 })
const uploadResult = ref(null)

// 预览相关
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewDoc = ref(null)
const previewData = ref(null)

// 权限相关
const isOwner = ref(false)

// 客户端搜索过滤
const filteredDocuments = computed(() => {
  if (!searchKeyword.value) return documents.value
  const kw = searchKeyword.value.toLowerCase()
  return documents.value.filter(doc => doc.filename?.toLowerCase().includes(kw))
})

const uploadProgressPercent = computed(() => {
  if (uploadProgress.value.total === 0) return 0
  return Math.round((uploadProgress.value.current / uploadProgress.value.total) * 100)
})

onMounted(async () => {
  await loadKnowledgeBases()
  if (route.query.kb_id) {
    currentKbId.value = Number(route.query.kb_id)
  }
  if (currentKbId.value) {
    loadDocuments()
  }
})

async function loadKnowledgeBases() {
  try {
    const { data } = await knowledgeBaseAPI.list()
    knowledgeBases.value = data
  } catch {}
}

function onKbChange() {
  documents.value = []
  searchKeyword.value = ''
  isOwner.value = false
  if (currentKbId.value) {
    loadDocuments()
    checkOwnership()
  }
}

async function checkOwnership() {
  try {
    const { data } = await knowledgeBaseAPI.get(currentKbId.value)
    isOwner.value = data.ownership === 'owner'
  } catch { isOwner.value = false }
}

function onSearch() {
  // 客户端过滤，无需请求
}

async function loadDocuments() {
  if (!currentKbId.value) return
  loading.value = true
  try {
    const { data } = await knowledgeBaseAPI.getDocuments(currentKbId.value)
    // 加载用户的收藏列表，标记收藏状态
    try {
      const { data: favs } = await interactAPI.getFavorites()
      const favIds = new Set(favs.map(f => f.id))
      data.forEach(doc => { doc._favorited = favIds.has(doc.id) })
    } catch { data.forEach(doc => { doc._favorited = false }) }
    documents.value = data
  } catch (e) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload(options) {
  const files = options.files || [options.file]
  if (files.length > 1) {
    // 批量上传
    uploading.value = true
    uploadProgress.value = { current: 0, total: files.length, success: 0, fail: 0 }
    uploadResult.value = null

    const formData = new FormData()
    files.forEach(f => formData.append('files', f))

    try {
      uploadProgress.value.current = files.length
      const { data } = await knowledgeBaseAPI.batchUploadDocuments(currentKbId.value, formData)
      const successCount = data?.success_count ?? files.length
      const failCount = data?.fail_count ?? 0
      uploadProgress.value.success = successCount
      uploadProgress.value.fail = failCount

      if (failCount === 0) {
        uploadResult.value = { type: 'success', message: `全部 ${successCount} 个文件上传成功` }
      } else {
        uploadResult.value = { type: 'warning', message: `上传完成：成功 ${successCount} 个，失败 ${failCount} 个` }
      }
      loadDocuments()
    } catch (e) {
      uploadProgress.value.fail = files.length
      uploadResult.value = { type: 'error', message: '批量上传失败：' + (e.response?.data?.detail || e.message) }
    } finally {
      uploading.value = false
    }
  } else {
    // 单文件上传
    const formData = new FormData()
    formData.append('file', files[0])
    uploading.value = true
    uploadProgress.value = { current: 1, total: 1, success: 0, fail: 0 }
    try {
      await knowledgeBaseAPI.uploadDocument(currentKbId.value, formData)
      uploadProgress.value.success = 1
      uploadResult.value = { type: 'success', message: '文档上传成功' }
      loadDocuments()
    } catch (e) {
      uploadProgress.value.fail = 1
      uploadResult.value = { type: 'error', message: e.response?.data?.detail || '上传失败' }
    } finally {
      uploading.value = false
    }
  }
}

async function handlePreview(row) {
  previewDoc.value = row
  previewVisible.value = true
  previewLoading.value = true
  previewData.value = null
  try {
    const { data } = await documentAPI.preview(row.id)
    previewData.value = data
  } catch (e) {
    ElMessage.error('获取文档预览失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

async function handleReprocess(row) {
  await ElMessageBox.confirm(`确定要重新处理文档 "${row.filename}"？`, '提示', { type: 'warning' })
  row._reprocessing = true
  try {
    await documentAPI.reprocess(row.id)
    ElMessage.success('重新处理已提交')
    loadDocuments()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '重新处理失败')
  } finally {
    row._reprocessing = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除文档 "${row.filename}"？`, '提示', { type: 'warning' })
  try {
    await documentAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ========== 收藏 ==========
async function handleFavorite(row) {
  try {
    const { data } = await interactAPI.toggleFavorite(row.id)
    row._favorited = data.favorited
    ElMessage.success(data.message)
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// ========== 举报 ==========
async function handleReport(row) {
  const { value: reason } = await ElMessageBox.prompt('请输入举报原因', '举报文档', {
    inputPlaceholder: '例如：内容不准确、侵权等',
    inputType: 'textarea',
    confirmButtonText: '提交举报',
    cancelButtonText: '取消',
  }).catch(() => ({ value: null }))
  if (reason === null) return
  try {
    await interactAPI.reportDocument(row.id, reason || '')
    ElMessage.success('举报已提交，管理员将尽快审核')
  } catch (e) {
    ElMessage.error('举报失败')
  }
}

function getFileIconColor(filename) {
  if (!filename) return '#909399'
  const ext = filename.split('.').pop()?.toLowerCase()
  const colors = {
    pdf: '#E6A23C',
    txt: '#909399',
    md: '#409EFF',
    markdown: '#409EFF',
    docx: '#67C23A',
    doc: '#67C23A',
    xlsx: '#67C23A',
    xls: '#67C23A',
    pptx: '#E6A23C',
    ppt: '#E6A23C',
    html: '#F56C6C',
    csv: '#909399',
  }
  return colors[ext] || '#909399'
}
</script>

<style scoped>
.documents-page {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right {
  display: flex;
  align-items: center;
}
.page-header h3 {
  font-size: 18px;
  color: #333;
}

/* 上传进度 */
.upload-progress-section {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
}
.upload-progress-header {
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}
.upload-progress-detail {
  margin-top: 6px;
  display: flex;
  gap: 16px;
  font-size: 12px;
}
.upload-success { color: #67c23a; }
.upload-fail { color: #f56c6c; }

/* 上传结果 */
.upload-result {
  margin-bottom: 16px;
  padding: 10px 16px;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.upload-result.success { background: #f0f9eb; color: #67c23a; }
.upload-result.warning { background: #fdf6ec; color: #e6a23c; }
.upload-result.error { background: #fef0f0; color: #f56c6c; }

/* 文件名单元格 */
.filename-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.file-type-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.text-muted {
  color: #c0c4cc;
}

/* 预览弹窗 */
.preview-section {
  margin-bottom: 20px;
}
.preview-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #303133;
}
.preview-content {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
.preview-chunks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.preview-chunks-header h4 {
  margin: 0;
}
.preview-chunks-list {
  max-height: 300px;
  overflow-y: auto;
}
.preview-chunk-item {
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
}
.chunk-index {
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
  margin-bottom: 4px;
}
.chunk-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 旋转动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.rotating {
  animation: spin 1.5s linear infinite;
}
</style>
