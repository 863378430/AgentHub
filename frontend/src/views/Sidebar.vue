<!-- src/components/Sidebar.vue -->
<template>
  <div class="sidebar">
    <div class="logo">
      <h2>AgentHub</h2>
    </div>
    
    <div class="menu-list">
      <div 
        v-for="item in menuItems" 
        :key="item.path"
        class="menu-item"
        :class="{ active: currentPath === item.path }"
        @click="handleMenuClick(item.path)"
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
        :class="{ active: currentHistory === item.id }"
        @click="handleHistoryClick(item.id)"
      >
        <span class="menu-text">{{ item.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['update:path', 'update:history'])

const props = defineProps({
  currentPath: {
    type: String,
    default: '/'
  },
  currentHistory: {
    type: Number,
    default: null
  }
})

const menuItems = [
  { path: '/chat', name: '新对话', icon: '💬' },
  { path: '/data', name: '数据审核', icon: '📊' },
  { path: '/permission', name: '权限管理', icon: '🔐' }
]

const historyItems = [
  { id: 1, name: '项目讨论记录' },
  { id: 2, name: '需求分析会议' },
  { id: 3, name: '技术方案评审' }
]

const handleMenuClick = (path) => {
  emit('update:path', path)
  emit('update:history', null)
}

const handleHistoryClick = (id) => {
  emit('update:history', id)
  emit('update:path', '/chat')
}
</script>

<style scoped>
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
</style>