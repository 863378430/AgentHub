<!-- src/views/MainLayout.vue -->
<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="logo">
        <h2>AgentHub</h2>
      </div>
      
      <div class="menu-list">
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
        
        <div class="history-divider"></div>
        <div class="history-title">历史对话</div>
        <div 
          v-for="item in historyItems" 
          :key="item.id"
          class="menu-item history-item"
          @click="$router.push('/chat')"
        >
          <span class="menu-text">{{ item.name }}</span>
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
      
      <!-- 右下角退出登录按钮 -->
      <div class="logout-btn-wrapper">
        <el-button 
          type="primary" 
          text
          @click="handleLogout"
          icon="el-icon-switch-button"
        >
          退出登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { clearAuth } from '@/utils/auth'

const router = useRouter()

// 菜单数据
const menuItems = [
  { path: '/chat', name: '新对话', icon: '💬' },
  { path: '/data', name: '数据审核', icon: '📊' },
  { path: '/permission', name: '权限管理', icon: '🔐' }
]

// 历史对话数据
const historyItems = [
  { id: 1, name: '项目讨论记录' },
  { id: 2, name: '需求分析会议' },
  { id: 3, name: '技术方案评审' }
]

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

.sidebar {
  width: 240px;
  background-color: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding-left: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.logo h2 {
  font-size: 20px;
  color: #1989fa;
  margin: 0;
}

.menu-list {
  flex: 1;
  padding: 10px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s;
  color: #333;
}

.menu-item:hover {
  background-color: #f5f5f5;
}

.menu-item.active {
  background-color: #e8e8e8;
  color: #1989fa;
  font-weight: 500;
}

.menu-icon {
  margin-right: 10px;
  font-size: 16px;
}

.menu-text {
  font-size: 14px;
}

.history-divider {
  height: 1px;
  background-color: #f0f0f0;
  margin: 10px 20px;
}

.history-title {
  padding: 10px 20px;
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.history-item {
  padding-left: 30px;
  font-size: 13px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.content-header {
  height: 60px;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 20px;
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

.logout-btn-wrapper {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
}

.logout-btn-wrapper .el-button {
  background-color: #fff;
  border: 1px solid #1989fa;
  color: #1989fa;
  padding: 8px 16px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.logout-btn-wrapper .el-button:hover {
  background-color: #f0f9ff;
}
</template>