<!-- src/views/MainLayout.vue -->
<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="logo">
        <h2>AgentHub</h2>
      </div>
      
      <!-- 菜单列表（核心菜单固定 + 历史对话滚动） -->
      <div class="menu-wrapper">
        <!-- 核心功能菜单（固定不滚动） -->
        <div class="core-menu">
          <div 
            v-for="item in menuItems" 
            :key="item.path"
            class="menu-item"
            :class="{ active: $route.path === item.path }"
            @click="$router.push(item.path)"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span class="menu-text">{{ item.name }}</span>
          </div>
        </div>
        
        <!-- 历史对话区域（单独滚动容器） -->
        <div class="history-section">
          <div class="history-divider"></div>
          <div class="history-title">历史对话</div>
          <div class="history-list">
            <div 
              v-for="item in historyItems" 
              :key="item.id"
              class="menu-item history-item"
              @click="$router.push(`/chat?id=${item.id}`)"
            >
              <span class="menu-text">{{ item.name }}</span>
            </div>
          </div>
        </div>

        <!-- 退出登录项（固定在侧边栏底部） -->
        <div class="logout-section">
          <div class="menu-item logout-item" @click="handleLogout">
            <span class="menu-icon">🔄</span>
            <span class="menu-text">退出登录</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <div class="content-header">
        <h3>{{ $route.meta.title || 'AgentHub' }}</h3>
      </div>
      <div class="content-body">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { clearAuth } from '@/utils/auth'

const router = useRouter()

// 核心菜单数据
const menuItems = [
  { path: '/chat', name: '新对话', icon: '💬' },
  { path: '/data', name: '数据审核', icon: '📊' },
  { path: '/permission', name: '权限管理', icon: '🔐' }
]

// 生成15条历史对话数据
const historyItems = Array.from({ length: 15 }, (_, index) => ({
  id: index + 1,
  name: `对话-${index + 1}：${['项目讨论', '需求分析', '技术评审', 'bug修复', '功能规划'][Math.floor(Math.random() * 5)]}`
}))

// 退出登录
const handleLogout = () => {
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}

/* 侧边栏样式 - 固定高度，整体布局适配 */
.sidebar {
  width: 240px;
  background-color: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  height: 100vh; /* 固定高度，确保滚动生效 */
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding-left: 20px;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0; /* 固定logo高度，不被压缩 */
}

.logo h2 {
  font-size: 20px;
  color: #1989fa;
  margin: 0;
}

/* 菜单外层容器 - 填充剩余高度，核心菜单+历史对话+退出项布局 */
.menu-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px 0;
  overflow: hidden; /* 隐藏外层滚动，只保留历史对话区滚动 */
}

/* 核心功能菜单 - 固定不滚动 */
.core-menu {
  flex-shrink: 0; /* 固定高度，不被压缩 */
}

/* 历史对话区域 - 单独滚动容器 */
.history-section {
  flex: 1; /* 占据剩余高度 */
  overflow-y: auto; /* 仅历史对话区滚动 */
  margin: 10px 0; /* 与核心菜单、退出项保持间距 */
  /* 优化滚动条样式（适配Chrome/Firefox） */
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: #dcdcdc #f5f5f5; /* Firefox */
}

/* Chrome/Safari 滚动条样式优化 */
.history-section::-webkit-scrollbar {
  width: 6px; /* 窄滚动条，不占空间 */
}
.history-section::-webkit-scrollbar-track {
  background: #f5f5f5;
}
.history-section::-webkit-scrollbar-thumb {
  background-color: #dcdcdc;
  border-radius: 3px;
}
.history-section::-webkit-scrollbar-thumb:hover {
  background-color: #bbb;
}

.history-divider {
  height: 1px;
  background-color: #f0f0f0;
  margin: 0 20px;
}

.history-title {
  padding: 10px 20px;
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 1px;
  flex-shrink: 0;
}

/* 历史对话列表 - 15项时可滚动 */
.history-list {
  padding: 0;
  margin: 0;
}

/* 统一的菜单项样式 */
.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s;
  color: #333;
  margin: 0;
  list-style: none; /* 清除列表默认样式 */
}

.menu-item:hover {
  background-color: #f5f5f5;
  color: #1989fa;
}

.menu-item.active {
  background-color: #e8e8e8;
  color: #1989fa;
  font-weight: 500;
}

.menu-icon {
  margin-right: 10px;
  font-size: 16px;
  width: 18px;
  text-align: center;
}

.menu-text {
  font-size: 14px;
}

/* 历史对话子项缩进 */
.history-item {
  padding-left: 30px;
}

/* 退出登录项 - 固定在侧边栏底部 */
.logout-section {
  flex-shrink: 0; /* 固定高度，不被压缩 */
  border-top: 1px solid #f0f0f0; /* 与历史对话区分隔 */
  margin-top: 5px;
}

.logout-item {
  width: 100%;
}

/* 主内容区样式 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  height: 60px;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 20px;
  flex-shrink: 0;
}

.content-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.content-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>