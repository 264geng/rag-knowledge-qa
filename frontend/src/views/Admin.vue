<template>
  <div class="admin-page">
    <!-- 系统统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="8" :md="4" v-for="item in statItems" :key="item.key">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="36" :color="item.color">
              <component :is="item.icon" />
            </el-icon>
            <div class="stat-info">
              <el-statistic :value="stats[item.key]" />
              <span class="stat-label">{{ item.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户管理 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><User /></el-icon> 用户管理
          </span>
        </div>
      </template>
      <el-table :data="users" v-loading="usersLoading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
            <el-tag v-else type="info" size="small">普通用户</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="knowledge_base_count" label="知识库数" width="100" align="center" />
        <el-table-column prop="document_count" label="文档数" width="100" align="center" />
        <el-table-column prop="conversation_count" label="对话数" width="100" align="center" />
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_admin"
              type="primary"
              text
              size="small"
              :disabled="row.id === currentUserId"
              @click="handleToggleRole(row)"
            >
              <el-icon><UserFilled /></el-icon> 设为管理员
            </el-button>
            <el-button
              v-else
              type="warning"
              text
              size="small"
              :disabled="row.id === currentUserId"
              @click="handleToggleRole(row)"
            >
              <el-icon><User /></el-icon> 取消管理员
            </el-button>
            <el-button
              type="danger"
              text
              size="small"
              :disabled="row.id === currentUserId"
              @click="handleDeleteUser(row)"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 操作日志 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="section-header">
          <span class="section-title">
            <el-icon><Notebook /></el-icon> 操作日志
          </span>
          <el-select
            v-model="logFilterUserId"
            placeholder="按用户筛选"
            clearable
            size="small"
            style="width: 160px"
            @change="loadLogs(1)"
          >
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="u.username"
              :value="u.id"
            />
          </el-select>
        </div>
      </template>
      <el-table :data="logs" v-loading="logsLoading" stripe style="width: 100%">
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="action" label="操作" width="140" />
        <el-table-column prop="target" label="操作对象" width="160" />
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="logPage"
          :page-size="logPageSize"
          :total="logTotal"
          layout="total, prev, pager, next"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  User,
  UserFilled,
  Document,
  ChatDotRound,
  Files,
  Delete,
  Notebook,
  DataAnalysis,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI, authAPI } from '../api'

const stats = reactive({
  total_users: 0,
  total_knowledge_bases: 0,
  total_documents: 0,
  total_conversations: 0,
  total_messages: 0,
})

const statItems = [
  { key: 'total_users', label: '用户总数', icon: 'UserFilled', color: '#409eff' },
  { key: 'total_knowledge_bases', label: '知识库', icon: 'Files', color: '#67c23a' },
  { key: 'total_documents', label: '文档', icon: 'Document', color: '#e6a23c' },
  { key: 'total_conversations', label: '对话', icon: 'ChatDotRound', color: '#f56c6c' },
  { key: 'total_messages', label: '消息', icon: 'DataAnalysis', color: '#909399' },
]

const users = ref([])
const usersLoading = ref(false)
const currentUserId = ref(null)

const logs = ref([])
const logsLoading = ref(false)
const logPage = ref(1)
const logPageSize = 20
const logTotal = ref(0)
const logFilterUserId = ref('')

onMounted(async () => {
  await loadCurrentUser()
  loadStats()
  loadUsers()
  loadLogs(1)
})

async function loadCurrentUser() {
  try {
    const { data } = await authAPI.getMe()
    currentUserId.value = data.id
  } catch {}
}

async function loadStats() {
  try {
    const { data } = await adminAPI.getStats()
    Object.assign(stats, data)
  } catch {
    ElMessage.error('加载统计数据失败')
  }
}

async function loadUsers() {
  usersLoading.value = true
  try {
    const { data } = await adminAPI.getUsers()
    users.value = data
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

async function handleDeleteUser(row) {
  await ElMessageBox.confirm(
    `确定删除用户"${row.username}"？该操作不可恢复。`,
    '警告',
    { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
  )
  try {
    await adminAPI.deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
    loadStats()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

async function handleToggleRole(row) {
  const action = row.is_admin ? '取消管理员' : '设为管理员'
  await ElMessageBox.confirm(
    `确定将用户"${row.username}"${action}？`,
    '提示',
    { type: 'warning' }
  )
  try {
    await adminAPI.toggleRole(row.id)
    ElMessage.success(`${action}成功`)
    loadUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function loadLogs(page) {
  if (page) logPage.value = page
  logsLoading.value = true
  try {
    const params = { page: logPage.value, page_size: logPageSize }
    if (logFilterUserId.value) params.user_id = logFilterUserId.value
    const { data } = await adminAPI.getLogs(params)
    logs.value = data.items || data.logs || data
    logTotal.value = data.total || 0
  } catch {
    ElMessage.error('加载操作日志失败')
  } finally {
    logsLoading.value = false
  }
}
</script>

<style scoped>
.admin-page {
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

.stat-card :deep(.el-card__body) {
  padding: 20px;
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

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
