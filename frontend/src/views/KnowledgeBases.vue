<template>
  <div class="kb-page">
    <div class="page-header">
      <h3>知识库管理</h3>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建知识库
      </el-button>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索知识库名称"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <el-table :data="filteredKnowledgeBases" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="知识库名称" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="150" />
      <el-table-column label="可见性" width="100">
        <template #default="{ row }">
          <el-tooltip v-if="row.visibility === 'rejected' && row.reject_reason" :content="row.reject_reason" placement="top">
            <el-tag type="danger" size="small">已打回</el-tag>
          </el-tooltip>
          <el-tag v-else-if="row.visibility === 'rejected'" type="danger" size="small">已打回</el-tag>
          <el-tag v-else-if="row.visibility === 'pending'" type="warning" size="small">待审核</el-tag>
          <el-tag v-else-if="row.visibility === 'public'" type="success" size="small">公开</el-tag>
          <el-tag v-else-if="row.visibility === 'shared'" type="warning" size="small">分享</el-tag>
          <el-tag v-else type="info" size="small">私有</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="document_count" label="文档" width="70" />
      <el-table-column prop="chunk_count" label="分块" width="70" />
      <el-table-column label="来源" width="100">
        <template #default="{ row }">
          <span v-if="row.ownership === 'shared' && row.shared_by_username" style="color: #409eff; font-size: 12px">
            {{ row.shared_by_username }} 分享
          </span>
          <span v-else-if="row.ownership === 'shared'" style="color: #999; font-size: 12px">
            分享给我的
          </span>
          <span v-else-if="row.ownership === 'owner'" style="color: #67c23a; font-size: 12px">
            我创建的
          </span>
        </template>
      </el-table-column>
      <el-table-column label="评价" width="110">
        <template #default="{ row }">
          <span
            class="vote-btn"
            :class="{ active: row._userVote === 'like' }"
            @click="handleVote(row, 'like')"
          >👍 {{ row._likes || 0 }}</span>
          <span
            class="vote-btn"
            :class="{ active: row._userVote === 'dislike' }"
            @click="handleVote(row, 'dislike')"
          >👎 {{ row._dislikes || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="收藏" width="70">
        <template #default="{ row }">
          <el-button
            :type="row._favorited ? 'warning' : 'default'"
            text size="small"
            @click="handleKBFavorite(row)"
          >
            <el-icon><StarFilled v-if="row._favorited" /><Star v-else /></el-icon>
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <!-- 只有创建者或管理员才能编辑/分享/删除 -->
          <template v-if="row.ownership === 'owner' || isAdmin">
            <el-button type="primary" text size="small" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button type="primary" text size="small" @click="goToDocuments(row)">
              <el-icon><Document /></el-icon> 文档
            </el-button>
            <el-button type="primary" text size="small" @click="openShareDialog(row)">
              <el-icon><Share /></el-icon> 分享
            </el-button>
            <el-button type="danger" text size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
          <!-- 其他用户只能查看文档 -->
          <template v-else>
            <el-button type="primary" text size="small" @click="goToDocuments(row)">
              <el-icon><Document /></el-icon> 查看文档
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建知识库对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建知识库" width="400">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑知识库对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑知识库" width="400">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="editForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分享弹窗 -->
    <el-dialog v-model="showShareDialog" :title="`分享 - ${sharingKB?.name || ''}`" width="500">
      <div style="margin-bottom: 16px;">
        <el-radio-group v-model="shareMode" @change="onShareModeChange">
          <el-radio-button value="user">分享给用户</el-radio-button>
          <el-radio-button value="public">设为公开</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 分享给用户 -->
      <div v-if="shareMode === 'user'">
        <el-input
          v-model="shareSearchKeyword"
          placeholder="输入用户名搜索"
          @input="onShareSearch"
          clearable
          style="margin-bottom: 12px"
        />
        <div v-if="shareSearchResults.length > 0" class="share-search-results">
          <div
            v-for="u in shareSearchResults"
            :key="u.id"
            class="share-user-item"
            @click="handleShareToUser(u)"
          >
            <span>{{ u.username }}</span>
            <el-button type="primary" size="small" link>分享</el-button>
          </div>
        </div>
        <div v-if="sharedUsers.length > 0" style="margin-top: 16px;">
          <div style="font-size: 13px; color: #999; margin-bottom: 8px;">已分享给：</div>
          <el-tag
            v-for="u in sharedUsers"
            :key="u.shared_with_user_id"
            closable
            @close="handleUnshare(u)"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ u.username }}
            <span v-if="u.shared_by_username" style="font-size: 11px; color: #999; margin-left: 4px">
              ({{ u.shared_by_username }} 分享)
            </span>
          </el-tag>
        </div>
      </div>

      <!-- 设为公开 -->
      <div v-if="shareMode === 'public'">
        <div v-if="sharingKB?.visibility === 'rejected'" style="margin-bottom: 16px;">
          <el-alert
            title="知识库已被打回"
            :description="sharingKB?.reject_reason || '请联系管理员了解详情'"
            type="warning"
            show-icon
            :closable="false"
          />
        </div>
        <p style="color: #666;">
          提交公开申请后，管理员将审核此知识库。
          <br>审核通过后，所有用户都可以查看此知识库的内容。
        </p>
        <el-button
          v-if="sharingKB?.visibility === 'public'"
          type="danger"
          @click="handleSetPublic"
        >
          取消公开
        </el-button>
        <el-button
          v-else-if="sharingKB?.visibility === 'pending'"
          type="warning"
          disabled
        >
          等待审核中
        </el-button>
        <el-button
          v-else
          type="success"
          @click="handleSetPublic"
        >
          {{ sharingKB?.visibility === 'rejected' ? '重新提交申请' : '提交公开申请' }}
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Delete, Document, Edit, Search, Share, Star, StarFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeBaseAPI, interactAPI, authAPI } from '../api'

const router = useRouter()
const knowledgeBases = ref([])
const loading = ref(false)
const searchQuery = ref('')
const isAdmin = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = reactive({ name: '', description: '' })
const showEditDialog = ref(false)
const editing = ref(false)
const editForm = reactive({ id: null, name: '', description: '' })

// 分享相关
const showShareDialog = ref(false)
const sharingKB = ref(null)
const shareMode = ref('user')
const shareSearchKeyword = ref('')
const shareSearchResults = ref([])
const sharedUsers = ref([])
let shareSearchTimer = null

const filteredKnowledgeBases = computed(() => {
  if (!searchQuery.value.trim()) return knowledgeBases.value
  const query = searchQuery.value.trim().toLowerCase()
  return knowledgeBases.value.filter((kb) => kb.name.toLowerCase().includes(query))
})

onMounted(async () => {
  try {
    const { data } = await authAPI.getMe()
    isAdmin.value = !!data.is_admin
  } catch {}
  loadKnowledgeBases()
})

async function loadKnowledgeBases() {
  loading.value = true
  try {
    const { data } = await knowledgeBaseAPI.list()
    // 为所有知识库加载投票数据和收藏状态
    for (const kb of data) {
      try {
        const { data: votes } = await interactAPI.getVotes(kb.id)
        kb._likes = votes.likes
        kb._dislikes = votes.dislikes
        kb._userVote = votes.user_vote
      } catch { kb._likes = 0; kb._dislikes = 0; kb._userVote = null }
    }
    knowledgeBases.value = data
    // 加载收藏状态
    loadFavoritesStatus()
  } catch (e) {
    ElMessage.error('加载知识库列表失败')
  } finally {
    loading.value = false
  }
}

async function loadFavoritesStatus() {
  try {
    const { data: favorites } = await interactAPI.getFavorites()
    const favoriteKBIds = new Set(
      favorites.filter(f => f.type === 'knowledge_base').map(f => f.id)
    )
    knowledgeBases.value.forEach(kb => {
      kb._favorited = favoriteKBIds.has(kb.id)
    })
  } catch {}
}

async function handleCreate() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  creating.value = true
  try {
    await knowledgeBaseAPI.create({
      name: createForm.name.trim(),
      description: createForm.description.trim(),
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    loadKnowledgeBases()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

function openEditDialog(row) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  showEditDialog.value = true
}

async function handleEdit() {
  if (!editForm.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  editing.value = true
  try {
    await knowledgeBaseAPI.update(editForm.id, {
      name: editForm.name.trim(),
      description: editForm.description.trim(),
    })
    ElMessage.success('更新成功')
    showEditDialog.value = false
    loadKnowledgeBases()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  } finally {
    editing.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    `确定删除知识库"${row.name}"？删除后该知识库下的所有文档和向量数据将被清除。`,
    '警告',
    { type: 'warning' }
  )
  try {
    await knowledgeBaseAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadKnowledgeBases()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function goToDocuments(row) {
  router.push({ path: '/documents', query: { kb_id: row.id, kb_name: row.name } })
}

// ========== 分享功能 ==========
function openShareDialog(row) {
  sharingKB.value = row
  shareMode.value = 'user'
  shareSearchKeyword.value = ''
  shareSearchResults.value = []
  showShareDialog.value = true
  loadSharedUsers(row.id)
}

async function loadSharedUsers(kbId) {
  try {
    const { data } = await interactAPI.getShares(kbId)
    sharedUsers.value = data
  } catch { sharedUsers.value = [] }
}

function onShareSearch() {
  if (shareSearchTimer) clearTimeout(shareSearchTimer)
  shareSearchTimer = setTimeout(async () => {
    if (!shareSearchKeyword.value.trim()) { shareSearchResults.value = []; return }
    try {
      const { data } = await interactAPI.searchUsers(shareSearchKeyword.value.trim())
      shareSearchResults.value = data
    } catch { shareSearchResults.value = [] }
  }, 300)
}

async function handleShareToUser(user) {
  try {
    await interactAPI.shareKB(sharingKB.value.id, user.id)
    ElMessage.success(`已分享给 ${user.username}`)
    shareSearchKeyword.value = ''
    shareSearchResults.value = []
    loadSharedUsers(sharingKB.value.id)
    loadKnowledgeBases()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '分享失败')
  }
}

async function handleUnshare(user) {
  try {
    await interactAPI.unshareKB(sharingKB.value.id, user.shared_with_user_id)
    ElMessage.success('已取消分享')
    loadSharedUsers(sharingKB.value.id)
    loadKnowledgeBases()
  } catch (e) {
    ElMessage.error('取消分享失败')
  }
}

function onShareModeChange() {
  shareSearchKeyword.value = ''
  shareSearchResults.value = []
}

async function handleSetPublic() {
  const newVis = sharingKB.value.visibility === 'public' ? 'private' : 'public'
  try {
    await interactAPI.setVisibility(sharingKB.value.id, newVis)
    if (newVis === 'public') {
      ElMessage.success('已提交公开申请，请等待管理员审核')
    } else {
      ElMessage.success('已取消公开')
    }
    showShareDialog.value = false
    loadKnowledgeBases()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleVote(kb, voteType) {
  try {
    const { data } = await interactAPI.voteKB(kb.id, voteType)
    kb._userVote = data.vote
    // 重新加载投票数
    const { data: votes } = await interactAPI.getVotes(kb.id)
    kb._likes = votes.likes
    kb._dislikes = votes.dislikes
  } catch (e) {
    ElMessage.error('投票失败')
  }
}

async function handleKBFavorite(kb) {
  try {
    const { data } = await interactAPI.toggleKBFavorite(kb.id)
    kb._favorited = data.favorited
    ElMessage.success(data.favorited ? '已收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.kb-page {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 {
  font-size: 18px;
  color: #333;
}
.search-bar {
  margin-bottom: 16px;
}
.share-search-results {
  border: 1px solid #eee;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}
.share-user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
}
.share-user-item:hover {
  background: #f5f7fa;
}
.vote-btn {
  cursor: pointer;
  font-size: 12px;
  margin-right: 4px;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s;
  user-select: none;
  white-space: nowrap;
  display: inline-block;
}
.vote-btn:hover {
  background: #f0f0f0;
}
.vote-btn.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}
</style>
