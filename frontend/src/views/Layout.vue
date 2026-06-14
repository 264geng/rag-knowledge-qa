<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="layout-aside">
      <div class="logo">
        <h2>🎓 智能问答</h2>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#1d1e2c"
        text-color="#a0a0b0"
        active-text-color="#409eff"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>
        <el-menu-item index="/knowledge-bases">
          <el-icon><Files /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <span>文档管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><User /></el-icon>
          <span>个人设置</span>
        </el-menu-item>
        <template v-if="isAdmin">
          <div class="menu-divider"></div>
          <el-menu-item index="/content-review">
            <el-icon><Warning /></el-icon>
            <span>内容审核</span>
          </el-menu-item>
          <el-menu-item index="/admin">
            <el-icon><Setting /></el-icon>
            <span>管理后台</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="layout-header">
        <span class="page-title">{{ $route.meta.title }}</span>
        <div class="header-right">
          <span class="username">{{ username }}</span>
          <el-button text @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Document, Files, Setting, User, Warning } from '@element-plus/icons-vue'
import { authAPI } from '../api'

const router = useRouter()
const username = ref('用户')
const isAdmin = ref(false)

onMounted(async () => {
  try {
    const { data } = await authAPI.getMe()
    username.value = data.username
    isAdmin.value = !!data.is_admin
  } catch {}
})

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.layout-aside {
  background: #1d1e2c;
  overflow: hidden;
}
.logo {
  padding: 20px 16px;
  text-align: center;
  border-bottom: 1px solid #2d2e3e;
}
.logo h2 {
  color: #fff;
  font-size: 18px;
}
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #eee;
  padding: 0 24px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  color: #666;
  font-size: 14px;
}
.layout-main {
  background: #f5f7fa;
  overflow-y: auto;
}
.menu-divider {
  height: 1px;
  background: #2d2e3e;
  margin: 12px 16px;
}
</style>
