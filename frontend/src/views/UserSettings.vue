<template>
  <div class="settings-page">
    <!-- 用户信息 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户信息</span>
        </div>
      </template>
      <div class="user-info" v-loading="userLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ userInfo.username }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ userInfo.created_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 使用统计 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>使用统计</span>
        </div>
      </template>
      <div class="stats-grid" v-loading="statsLoading">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="知识库数量" :value="stats.knowledge_base_count">
            <template #prefix>
              <el-icon style="color: #409eff"><Files /></el-icon>
            </template>
          </el-statistic>
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="文档数量" :value="stats.document_count">
            <template #prefix>
              <el-icon style="color: #67c23a"><Document /></el-icon>
            </template>
          </el-statistic>
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="对话数量" :value="stats.conversation_count">
            <template #prefix>
              <el-icon style="color: #e6a23c"><ChatDotRound /></el-icon>
            </template>
          </el-statistic>
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="消息数量" :value="stats.message_count">
            <template #prefix>
              <el-icon style="color: #f56c6c"><Comment /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </div>
    </el-card>

    <!-- 修改密码 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
        class="password-form"
      >
        <el-form-item label="原密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            show-password
            placeholder="请输入原密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码（至少6位）"
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 我的收藏 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的收藏</span>
          <el-tag size="small" type="info">{{ favorites.length }} 项</el-tag>
          <el-tag size="small" type="primary" v-if="kbFavoritesCount > 0">{{ kbFavoritesCount }} 知识库</el-tag>
          <el-tag size="small" type="warning" v-if="docFavoritesCount > 0">{{ docFavoritesCount }} 文档</el-tag>
        </div>
      </template>
      <el-table :data="favorites" style="width: 100%" v-loading="favoritesLoading" empty-text="暂无收藏">
        <el-table-column label="名称" min-width="200">
          <template #default="{ row }">
            <el-icon v-if="row.type === 'knowledge_base'" style="color: #409EFF; margin-right: 4px"><Files /></el-icon>
            <el-icon v-else style="color: #E6A23C; margin-right: 4px"><Document /></el-icon>
            {{ row.type === 'knowledge_base' ? row.name : row.filename }}
          </template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.type === 'knowledge_base'" type="primary" size="small">知识库</el-tag>
            <el-tag v-else type="warning" size="small">文档</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="kb_name" label="所属知识库" min-width="150" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="goToFavorite(row)">
              <el-icon><Link /></el-icon> 前往
            </el-button>
            <el-button type="warning" text size="small" @click="handleUnfavorite(row)">
              <el-icon><StarFilled /></el-icon> 取消收藏
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 提示词模板管理 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>提示词模板管理</span>
          <el-button type="primary" size="small" @click="showTemplateDialog = true">
            <el-icon><Plus /></el-icon> 新建模板
          </el-button>
        </div>
      </template>
      <el-table :data="templates" style="width: 100%" v-loading="templatesLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="模板名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="默认" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            <span v-else class="not-default">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="handleEditTemplate(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button type="danger" text size="small" @click="handleDeleteTemplate(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑模板对话框 -->
    <el-dialog v-model="showTemplateDialog" :title="editingTemplateId ? '编辑提示词模板' : '新建提示词模板'" width="500">
      <el-form
        ref="templateFormRef"
        :model="templateForm"
        :rules="templateRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="templateForm.description" placeholder="请输入模板描述（可选）" />
        </el-form-item>
        <el-form-item label="提示词" prop="system_prompt">
          <el-input
            v-model="templateForm.system_prompt"
            type="textarea"
            :rows="6"
            placeholder="请输入系统提示词内容"
          />
        </el-form-item>
        <el-form-item label="默认 Top K">
          <el-slider v-model="templateForm.default_top_k" :min="1" :max="10" :step="1" show-stops style="flex: 1; margin: 0 12px" />
          <span style="min-width: 24px; text-align: right; color: #409eff; font-weight: 600">{{ templateForm.default_top_k }}</span>
        </el-form-item>
        <el-form-item label="默认 Temperature">
          <el-slider v-model="templateForm.default_temperature" :min="0" :max="1" :step="0.05" style="flex: 1; margin: 0 12px" />
          <span style="min-width: 40px; text-align: right; color: #409eff; font-weight: 600">{{ templateForm.default_temperature.toFixed(2) }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeTemplateDialog">取消</el-button>
        <el-button type="primary" :loading="templateCreating" @click="handleSaveTemplate">
          {{ editingTemplateId ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Files, Document, ChatDotRound, Comment, Plus, Delete, Edit, StarFilled, Link } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authAPI, promptTemplateAPI, interactAPI } from '../api'

const router = useRouter()

// ========== 用户信息 ==========
const userLoading = ref(false)
const userInfo = reactive({
  username: '',
  created_at: '',
})

// ========== 使用统计 ==========
const statsLoading = ref(false)
const stats = reactive({
  knowledge_base_count: 0,
  document_count: 0,
  conversation_count: 0,
  message_count: 0,
})

// ========== 修改密码 ==========
const passwordFormRef = ref(null)
const passwordLoading = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

// ========== 我的收藏 ==========
const favorites = ref([])
const favoritesLoading = ref(false)
const kbFavoritesCount = computed(() => favorites.value.filter(f => f.type === 'knowledge_base').length)
const docFavoritesCount = computed(() => favorites.value.filter(f => f.type === 'document').length)

// ========== 提示词模板 ==========
const templates = ref([])
const templatesLoading = ref(false)
const showTemplateDialog = ref(false)
const templateCreating = ref(false)
const editingTemplateId = ref(null)
const templateFormRef = ref(null)
const templateForm = reactive({
  name: '',
  description: '',
  system_prompt: '',
  default_top_k: 4,
  default_temperature: 0.3,
})

const templateRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  system_prompt: [{ required: true, message: '请输入提示词内容', trigger: 'blur' }],
}

// ========== 加载数据 ==========
onMounted(() => {
  loadUserInfo()
  loadStats()
  loadFavorites()
  loadTemplates()
})

async function loadUserInfo() {
  userLoading.value = true
  try {
    const { data } = await authAPI.getMe()
    userInfo.username = data.username
    userInfo.created_at = data.created_at
  } catch {
    ElMessage.error('加载用户信息失败')
  } finally {
    userLoading.value = false
  }
}

async function loadStats() {
  statsLoading.value = true
  try {
    const { data } = await authAPI.getStats()
    stats.knowledge_base_count = data.knowledge_base_count ?? 0
    stats.document_count = data.document_count ?? 0
    stats.conversation_count = data.conversation_count ?? 0
    stats.message_count = data.message_count ?? 0
  } catch {
    ElMessage.error('加载统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

// ========== 我的收藏 ==========
async function loadFavorites() {
  favoritesLoading.value = true
  try {
    const { data } = await interactAPI.getFavorites()
    favorites.value = data
  } catch {} finally {
    favoritesLoading.value = false
  }
}

async function handleUnfavorite(row) {
  try {
    if (row.type === 'knowledge_base') {
      await interactAPI.toggleKBFavorite(row.id)
    } else {
      await interactAPI.toggleFavorite(row.id)
    }
    ElMessage.success('已取消收藏')
    loadFavorites()
  } catch { ElMessage.error('操作失败') }
}

function goToFavorite(row) {
  if (row.type === 'knowledge_base') {
    router.push({ path: '/knowledge-bases' })
  } else {
    router.push({ path: '/documents', query: { kb_id: row.kb_id, kb_name: row.kb_name } })
  }
}

async function loadTemplates() {
  templatesLoading.value = true
  try {
    const { data } = await promptTemplateAPI.list()
    templates.value = data
  } catch {
    ElMessage.error('加载模板列表失败')
  } finally {
    templatesLoading.value = false
  }
}

// ========== 修改密码 ==========
async function handleChangePassword() {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await authAPI.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

// ========== 提示词模板 ==========
function handleEditTemplate(row) {
  editingTemplateId.value = row.id
  templateForm.name = row.name
  templateForm.description = row.description || ''
  templateForm.system_prompt = row.system_prompt
  templateForm.default_top_k = row.default_top_k || 4
  templateForm.default_temperature = row.default_temperature ?? 0.3
  showTemplateDialog.value = true
}

function closeTemplateDialog() {
  showTemplateDialog.value = false
  editingTemplateId.value = null
  templateForm.name = ''
  templateForm.description = ''
  templateForm.system_prompt = ''
  templateForm.default_top_k = 4
  templateForm.default_temperature = 0.3
}

async function handleSaveTemplate() {
  const valid = await templateFormRef.value.validate().catch(() => false)
  if (!valid) return

  templateCreating.value = true
  try {
    const payload = {
      name: templateForm.name.trim(),
      description: templateForm.description.trim(),
      system_prompt: templateForm.system_prompt,
      default_top_k: templateForm.default_top_k,
      default_temperature: templateForm.default_temperature,
    }
    if (editingTemplateId.value) {
      await promptTemplateAPI.update(editingTemplateId.value, payload)
      ElMessage.success('模板更新成功')
    } else {
      await promptTemplateAPI.create(payload)
      ElMessage.success('模板创建成功')
    }
    closeTemplateDialog()
    loadTemplates()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    templateCreating.value = false
  }
}

async function handleDeleteTemplate(row) {
  await ElMessageBox.confirm(
    `确定删除模板"${row.name}"？`,
    '警告',
    { type: 'warning' }
  )
  try {
    await promptTemplateAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadTemplates()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.section-card {
  border-radius: 8px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}
.user-info {
  min-height: 40px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-card {
  text-align: center;
}
.password-form {
  max-width: 500px;
}
</style>
