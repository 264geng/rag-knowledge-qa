<template>
  <div class="review-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="36" color="#e6a23c"><Files /></el-icon>
            <div class="stat-info">
              <el-statistic :value="pendingKBCount" />
              <span class="stat-label">待审核知识库</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="36" color="#f56c6c"><Warning /></el-icon>
            <div class="stat-info">
              <el-statistic :value="pendingReportCount" />
              <span class="stat-label">待处理举报</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="36" color="#67c23a"><CircleCheck /></el-icon>
            <div class="stat-info">
              <el-statistic :value="todayProcessedCount" />
              <span class="stat-label">今日已处理</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 知识库审核 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Files /></el-icon> 知识库审核
          </span>
          <el-radio-group v-model="kbFilter" size="small" @change="loadKBs">
            <el-radio-button value="pending">待审核</el-radio-button>
            <el-radio-button value="public">已公开</el-radio-button>
            <el-radio-button value="all">全部</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="filteredKBs" v-loading="kbLoading" stripe style="width: 100%">
        <el-table-column prop="name" label="知识库名称" min-width="150" />
        <el-table-column prop="owner_name" label="创建者" width="100" />
        <el-table-column prop="visibility" label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.visibility === 'pending'" type="warning" size="small">待审核</el-tag>
            <el-tag v-else-if="row.visibility === 'public'" type="success" size="small">已公开</el-tag>
            <el-tag v-else-if="row.visibility === 'rejected'" type="danger" size="small">已打回</el-tag>
            <el-tag v-else type="info" size="small">{{ row.visibility }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评价" width="100">
          <template #default="{ row }">
            <span style="color: #67c23a">👍 {{ row.likes }}</span>
            <span style="color: #f56c6c; margin-left: 8px">👎 {{ row.dislikes }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="document_count" label="文档数" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="handleViewKB(row)">
              <el-icon><View /></el-icon> 查看
            </el-button>
            <el-button v-if="row.visibility === 'pending'" type="success" text size="small" @click="handleApprove(row)">
              <el-icon><Check /></el-icon> 通过
            </el-button>
            <el-button v-if="row.visibility === 'pending'" type="warning" text size="small" @click="handleReject(row)">
              <el-icon><Close /></el-icon> 打回
            </el-button>
            <el-button v-if="row.visibility === 'public'" type="danger" text size="small" @click="handleTakedown(row)">
              <el-icon><CircleClose /></el-icon> 下架
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 举报列表 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Warning /></el-icon> 举报处理
          </span>
          <el-radio-group v-model="reportFilter" size="small" @change="loadReports">
            <el-radio-button value="pending">待处理</el-radio-button>
            <el-radio-button value="all">全部</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="filteredReports" v-loading="reportLoading" stripe style="width: 100%">
        <el-table-column prop="filename" label="被举报文档" min-width="150">
          <template #default="{ row }">
            <span :class="{ 'deleted-text': !row.document_id }">{{ row.filename || '文档已删除' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="kb_name" label="所属知识库" width="120" />
        <el-table-column prop="username" label="举报人" width="90" />
        <el-table-column prop="reason" label="举报原因" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="warning" size="small">待处理</el-tag>
            <el-tag v-else-if="row.status === 'resolved'" type="success" size="small">已处理</el-tag>
            <el-tag v-else-if="row.status === 'dismissed'" type="info" size="small">已驳回</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resolve_reason" label="处理说明" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="举报时间" width="170" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.document_id" type="primary" text size="small" @click="handleViewDocument(row)">
              <el-icon><View /></el-icon> 查看文档
            </el-button>
            <el-button v-if="row.status === 'pending' && row.document_id" type="danger" text size="small" @click="handleDeleteDocument(row)">
              <el-icon><Delete /></el-icon> 删除文档
            </el-button>
            <el-button v-if="row.status === 'pending'" type="warning" text size="small" @click="handleDismissReport(row)">
              <el-icon><Close /></el-icon> 驳回举报
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 查看知识库详情弹窗 -->
    <el-dialog v-model="showKBDialog" :title="`知识库详情 - ${currentKB?.name || ''}`" width="800">
      <div v-if="currentKB" class="kb-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ currentKB.name }}</el-descriptions-item>
          <el-descriptions-item label="创建者">{{ currentKB.owner_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="currentKB.visibility === 'pending'" type="warning" size="small">待审核</el-tag>
            <el-tag v-else-if="currentKB.visibility === 'public'" type="success" size="small">已公开</el-tag>
            <el-tag v-else type="info" size="small">{{ currentKB.visibility }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文档数">{{ currentKB.document_count }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentKB.description || '暂无描述' }}</el-descriptions-item>
        </el-descriptions>

        <div class="kb-documents" style="margin-top: 20px;">
          <h4>包含文档</h4>
          <el-table :data="kbDocuments" size="small" max-height="300">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="file_type" label="类型" width="80" />
            <el-table-column prop="chunk_count" label="分块数" width="80" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'ready'" type="success" size="small">就绪</el-tag>
                <el-tag v-else type="warning" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 查看文档内容弹窗 -->
    <el-dialog v-model="showDocDialog" :title="`文档预览 - ${currentDoc?.filename || ''}`" width="700">
      <div v-if="currentDoc" class="doc-preview">
        <el-descriptions :column="2" border size="small" style="margin-bottom: 16px;">
          <el-descriptions-item label="文件名">{{ currentDoc.filename }}</el-descriptions-item>
          <el-descriptions-item label="所属知识库">{{ currentDoc.kb_name }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ currentDoc.file_type }}</el-descriptions-item>
          <el-descriptions-item label="分块数">{{ currentDoc.chunk_count }}</el-descriptions-item>
        </el-descriptions>
        <div class="doc-content" v-loading="docContentLoading">
          <pre v-if="docContent" class="content-text">{{ docContent }}</pre>
          <el-empty v-else description="暂无预览内容" />
        </div>
      </div>
    </el-dialog>

    <!-- 驳回原因弹窗 -->
    <el-dialog v-model="showRejectDialog" title="驳回原因" width="500">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="驳回原因" required>
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入驳回原因，将通知给用户"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="warning" :loading="rejectLoading" @click="confirmReject">确认驳回</el-button>
      </template>
    </el-dialog>

    <!-- 打回知识库原因弹窗 -->
    <el-dialog v-model="showKBRejectDialog" title="打回知识库" width="500">
      <el-form :model="kbRejectForm" label-width="80px">
        <el-form-item label="打回原因" required>
          <el-input
            v-model="kbRejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入打回原因，将通知给创建者"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showKBRejectDialog = false">取消</el-button>
        <el-button type="warning" :loading="kbRejectLoading" @click="confirmKBReject">确认打回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Files, Warning, CircleCheck, View, Check, Close, CircleClose, Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI, knowledgeBaseAPI, documentAPI } from '../api'

// 统计数据
const pendingKBCount = ref(0)
const pendingReportCount = ref(0)
const todayProcessedCount = ref(0)

// 知识库审核
const kbFilter = ref('pending')
const allKBs = ref([])
const kbLoading = ref(false)
const showKBDialog = ref(false)
const currentKB = ref(null)
const kbDocuments = ref([])

// 举报处理
const reportFilter = ref('pending')
const allReports = ref([])
const reportLoading = ref(false)
const showDocDialog = ref(false)
const currentDoc = ref(null)
const docContent = ref('')
const docContentLoading = ref(false)

// 驳回举报
const showRejectDialog = ref(false)
const rejectForm = ref({ reportId: null, reason: '' })
const rejectLoading = ref(false)

// 打回知识库
const showKBRejectDialog = ref(false)
const kbRejectForm = ref({ kbId: null, reason: '' })
const kbRejectLoading = ref(false)

// 过滤后的数据
const filteredKBs = computed(() => {
  if (kbFilter.value === 'all') return allKBs.value
  return allKBs.value.filter(kb => kb.visibility === kbFilter.value)
})

const filteredReports = computed(() => {
  if (reportFilter.value === 'all') return allReports.value
  return allReports.value.filter(r => r.status === reportFilter.value)
})

onMounted(() => {
  loadKBs()
  loadReports()
  loadStats()
})

// 加载统计
async function loadStats() {
  try {
    const { data } = await adminAPI.getStats()
    // 这里可以添加更多统计逻辑
  } catch {}
}

// 加载知识库列表
async function loadKBs() {
  kbLoading.value = true
  try {
    const { data } = await adminAPI.getReviewKBs()
    allKBs.value = data
    pendingKBCount.value = data.filter(kb => kb.visibility === 'pending').length
    todayProcessedCount.value = data.filter(kb => kb.visibility === 'public').length // 简化统计
  } catch {
    ElMessage.error('加载知识库列表失败')
  } finally {
    kbLoading.value = false
  }
}

// 加载举报列表
async function loadReports() {
  reportLoading.value = true
  try {
    const { data } = await adminAPI.getReports()
    allReports.value = data
    pendingReportCount.value = data.filter(r => r.status === 'pending').length
  } catch {
    ElMessage.error('加载举报列表失败')
  } finally {
    reportLoading.value = false
  }
}

// 查看知识库详情
async function handleViewKB(row) {
  currentKB.value = row
  showKBDialog.value = true
  try {
    const { data } = await knowledgeBaseAPI.getDocuments(row.id)
    kbDocuments.value = data
  } catch {
    kbDocuments.value = []
  }
}

// 通过审核
async function handleApprove(row) {
  await ElMessageBox.confirm(`通过知识库"${row.name}"的公开申请？`, '提示', { type: 'success' })
  try {
    await adminAPI.approveKB(row.id)
    ElMessage.success('已通过')
    loadKBs()
    loadStats()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 打回知识库
function handleReject(row) {
  kbRejectForm.value = { kbId: row.id, reason: '' }
  showKBRejectDialog.value = true
}

async function confirmKBReject() {
  if (!kbRejectForm.value.reason.trim()) {
    ElMessage.warning('请输入打回原因')
    return
  }
  kbRejectLoading.value = true
  try {
    await adminAPI.rejectKB(kbRejectForm.value.kbId, { reason: kbRejectForm.value.reason })
    ElMessage.success('已打回')
    showKBRejectDialog.value = false
    loadKBs()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    kbRejectLoading.value = false
  }
}

// 下架知识库
async function handleTakedown(row) {
  await ElMessageBox.confirm(`确定下架知识库"${row.name}"？`, '提示', { type: 'warning' })
  try {
    await adminAPI.takedownKB(row.id)
    ElMessage.success('已下架')
    loadKBs()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 查看文档
async function handleViewDocument(row) {
  currentDoc.value = row
  showDocDialog.value = true
  docContent.value = ''
  docContentLoading.value = true
  try {
    const { data } = await documentAPI.preview(row.document_id)
    docContent.value = data.content_preview || '暂无预览内容'
  } catch {
    docContent.value = '无法加载文档内容'
  } finally {
    docContentLoading.value = false
  }
}

// 删除文档
async function handleDeleteDocument(row) {
  await ElMessageBox.confirm(
    `确定删除被举报的文档"${row.filename}"？此操作不可恢复。`,
    '警告',
    { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
  )
  try {
    await documentAPI.delete(row.document_id)
    // 同时将举报标记为已处理
    await adminAPI.resolveReport(row.id, { action: 'resolved', reason: '文档已删除' })
    ElMessage.success('文档已删除，举报已处理')
    loadReports()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

// 驳回举报
function handleDismissReport(row) {
  rejectForm.value = { reportId: row.id, reason: '' }
  showRejectDialog.value = true
}

async function confirmReject() {
  if (!rejectForm.value.reason.trim()) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  rejectLoading.value = true
  try {
    await adminAPI.resolveReport(rejectForm.value.reportId, {
      action: 'dismissed',
      reason: rejectForm.value.reason
    })
    ElMessage.success('已驳回举报')
    showRejectDialog.value = false
    loadReports()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    rejectLoading.value = false
  }
}
</script>

<style scoped>
.review-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  margin-bottom: 0;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.section-card {
  border-radius: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.kb-detail {
  max-height: 600px;
  overflow-y: auto;
}

.kb-documents h4 {
  margin-bottom: 12px;
  color: #333;
}

.doc-preview {
  max-height: 500px;
}

.doc-content {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.content-text {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  margin: 0;
}

.deleted-text {
  color: #999;
  font-style: italic;
}
</style>
