<template>
  <div class="app-container">
    <div class="sidebar">
      <div class="logo">
        <h2>AgentHub</h2>
      </div>
      <div class="menu-wrapper">
        <div class="core-menu">
          <div class="menu-item create-conv-item" @click="createNewConversation">
            <span class="menu-icon">➕</span>
            <span class="menu-text">新建对话</span>
          </div>
        </div>
        <div class="history-section">
          <div class="history-divider"></div>
          <div class="history-title">历史对话</div>
          <div class="history-list" v-loading="loadingConvs">
            <div v-for="item in conversationList" :key="item.conversation_id" class="menu-item history-item" :class="{ active: currentConvId === item.conversation_id }" @click="handleConversationClick(item.conversation_id)" @contextmenu.prevent="handleConversationContextMenu($event, item)">
              <span class="menu-text">{{ item.title || `对话-${item.conversation_id.slice(-4)}` }}</span>
              <el-button type="text" icon="el-icon-delete" class="del-conv-btn" @click.stop="handleDeleteConv(item.conversation_id)"/>
            </div>
            <div v-if="!loadingConvs && !conversationList.length" class="empty-conv">暂无历史对话</div>
          </div>
        </div>
        <div class="logout-section">
          <div class="menu-item logout-item" @click="handleLogout">
            <span class="menu-icon">❎</span>
            <span class="menu-text">退出登录</span>
          </div>
        </div>
      </div>
    </div>
    <div class="main-content">
      <div class="content-header">
        <h3>{{ currentConvTitle || 'AgentHub' }}</h3>
      </div>
      <div class="content-body">
        <div class="chat-page">
          <div class="chat-messages" v-loading="loadingMessages">
            <div 
              class="message-item" 
              v-for="(msg, index) in messageList" 
              :key="index" 
              :class="{
                'user-message': msg.sender === '用户',
                'ai-message': msg.sender === 'AI'
              }"
            >
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
          
          <!-- 核心重构：输入框容器布局 -->
          <div class="chat-input-outer-box">
            <!-- 1. 文本框在上（严格限制3行） -->
            <textarea 
              v-model="message" 
              placeholder="请输入消息..." 
              @keydown.enter.prevent="handleEnterKey($event)" 
              class="chat-input-inner"
              :disabled="sendingMessage"
            ></textarea>
            
            <!-- 2. 容器包裹模式+发送按钮 -->
            <div class="mode-send-wrapper">
              <!-- 模式选择器居左 -->
              <div class="mode-selector">
                <button 
                  v-for="mode in modeList" 
                  :key="mode" 
                  class="mode-btn" 
                  :class="{ active: currentMode === mode }"
                  @click="selectMode(mode)"
                  :disabled="sendingMessage"
                >
                  {{ mode }}
                </button>
              </div>
              
              <!-- 发送按钮居右 -->
              <button class="send-button" @click="sendMessage" :disabled="sendingMessage">
                <svg v-if="!sendingMessage" width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 2L10 16M10 2L16 8M10 2L4 8" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <el-icon v-else class="loading-icon"><loading /></el-icon>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { clearAuth, getUserInfo } from '@/utils/auth'
import { 
  getUserConversations, 
  createConversation, 
  deleteConversation,
  sendMessage as apiSendMessage,
  getConversationMessages       
} from '@/api/chat'

const router = useRouter()
const route = useRoute()
const userInfo = getUserInfo()
const username = userInfo.username || ''

// 核心状态管理
const message = ref('')
const messageList = ref([])
const currentConvId = ref('')
const conversationList = ref([])
const loadingConvs = ref(false)
const loadingMessages = ref(false)
const sendingMessage = ref(false)

// 模式选择相关状态
const modeList = ref(['自动', '数据', '配置', '代码', '翻译'])
const currentMode = ref('自动') // 默认选中自动

// 计算当前对话标题
const currentConvTitle = computed(() => {
  const currentConv = conversationList.value.find(item => item.conversation_id === currentConvId.value)
  return currentConv?.title || '新对话'
})

// 切换模式方法
const selectMode = (mode) => {
  if (sendingMessage.value) return // 发送中不可切换
  currentMode.value = mode
}

// 发送消息
const sendMessage = async () => {
  const content = message.value.trim()
  if (!content || sendingMessage.value || !currentConvId.value) return

  try {
    sendingMessage.value = true
    messageList.value.push({ sender: '用户', content: content })
    message.value = ''

    // 发送消息时携带选中的模式
    const res = await apiSendMessage({
      conversation_id: currentConvId.value,
      username: username,
      role: 'user',
      content: content,
      mode: currentMode.value // 传递模式参数
    })

    if (res && res.content) {
      messageList.value.push({
        sender: 'AI',
        content: res.content
      })
    } else {
      ElMessage.warning('未收到AI回复，请稍后重试')
    }

    nextTick(() => {
      const chatMessages = document.querySelector('.chat-messages')
      if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight
      }
    })

  } catch (error) {
    messageList.value.pop()
    ElMessage.error(`消息发送失败：${error.message || '网络异常'}`)
  } finally {
    sendingMessage.value = false
  }
}

// 加载对话历史消息
const loadConversationMessages = async (convId) => {
  if (!convId) return

  try {
    loadingMessages.value = true
    const res = await getConversationMessages(convId)
    messageList.value = res.map(msg => ({
      sender: msg.role === 'user' ? '用户' : 'AI',
      content: msg.content
    }))
    nextTick(() => {
      const chatMessages = document.querySelector('.chat-messages')
      if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight
    })
  } catch (error) {
    ElMessage.error(`加载历史消息失败：${error.message || '网络异常'}`)
    messageList.value = []
  } finally {
    loadingMessages.value = false
  }
}

// 回车处理逻辑
const handleEnterKey = (e) => {
  if (e.ctrlKey || e.metaKey) {
    const cursorPos = e.target.selectionStart
    message.value = [
      message.value.substring(0, cursorPos),
      '\n',
      message.value.substring(cursorPos)
    ].join('')
    nextTick(() => {
      e.target.selectionStart = e.target.selectionEnd = cursorPos + 1
    })
  } else {
    sendMessage()
  }
}

// 加载对话列表
const loadConversationList = async () => {
  if (!username) return
  try {
    loadingConvs.value = true
    const res = await getUserConversations(username)
    conversationList.value = res
    if (res.length > 0 && !currentConvId.value) {
      currentConvId.value = res[0].conversation_id
      await loadConversationMessages(res[0].conversation_id)
    }
  } catch (e) {
    ElMessage.error(`加载对话列表失败：${e.message || '网络异常'}`)
    conversationList.value = []
  } finally {
    loadingConvs.value = false
  }
}

// 创建新对话
const createNewConversation = async () => {
  if (!username) {
    ElMessage.warning('请先登录！')
    router.push('/login')
    return
  }
  try {
    loadingConvs.value = true
    const res = await createConversation({
      username,
      title: `新对话-${new Date().getTime().toString().slice(-4)}`
    })
    currentConvId.value = res.conversation_id
    messageList.value = []
    await loadConversationList()
    ElMessage.success('新对话创建成功')
  } catch (e) {
    ElMessage.error(`创建对话失败：${e.message || '网络异常'}`)
  } finally {
    loadingConvs.value = false
  }
}

// 切换对话
const handleConversationClick = (convId) => {
  if (currentConvId.value === convId) return
  currentConvId.value = convId
  loadConversationMessages(convId)
}

// 删除对话
const handleDeleteConv = async (convId) => {
  try {
    await ElMessageBox.confirm('确定要删除该对话吗？删除后不可恢复','提示',{
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteConversation(convId)
    ElMessage.success('对话删除成功')
    await loadConversationList()
    if (convId === currentConvId.value) {
      if (conversationList.value.length > 0) {
        currentConvId.value = conversationList.value[0].conversation_id
        await loadConversationMessages(currentConvId.value)
      } else {
        createNewConversation()
      }
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(`删除对话失败：${e.message || '网络异常'}`)
    }
  }
}

// 右键菜单
const handleConversationContextMenu = (e, item) => {
  console.log('右键对话：', item.conversation_id)
}

// 退出登录
const handleLogout = () => {
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 路由监听 + 挂载初始化
watch(() => route.path, (newPath) => {
  if (newPath === '/chat' || newPath === '/') {
    loadConversationList().then(() => {
      if (currentConvId.value) {
        loadConversationMessages(currentConvId.value)
      }
    })
  }
}, { immediate: true })

onMounted(() => {
  if (username) {
    loadConversationList().then(() => {
      if (currentConvId.value) {
        loadConversationMessages(currentConvId.value)
      }
    })
  }
})
</script>

<style scoped>
/* 全局布局样式 */
.app-container {display: flex;height: 100vh;background-color: #f5f5f5;width: 100%;}
.sidebar {width: 240px;background-color: #fff;border-right: 1px solid #e8e8e8;display: flex;flex-direction: column;height: 100%;flex-shrink: 0;}
.logo {height: 60px;display: flex;align-items: center;padding-left: 20px;border-bottom: 1px solid #e8e8e8;flex-shrink: 0;}
.logo h2 {font-size: 20px;color: #1989fa;margin: 0;}
.menu-wrapper {flex: 1;display: flex;flex-direction: column;padding: 10px 0;overflow: hidden;}
.core-menu {flex-shrink: 0;}
.create-conv-item {margin-top: 8px;color: #1989fa;}
.create-conv-item:hover {background-color: #f0f9ff;}
.history-section {flex: 1;overflow-y: auto;margin: 10px 0;scrollbar-width: thin;scrollbar-color: #dcdcdc #f5f5f5;}
.history-section::-webkit-scrollbar {width: 6px;}
.history-section::-webkit-scrollbar-track {background: #f5f5f5;}
.history-section::-webkit-scrollbar-thumb {background-color: #dcdcdc;border-radius: 3px;}
.history-section::-webkit-scrollbar-thumb:hover {background-color: #bbb;}
.history-divider {height: 1px;background-color: #f0f0f0;margin: 0 20px;}
.history-title {padding: 10px 20px;font-size: 12px;color: #999;text-transform: uppercase;letter-spacing: 1px;}
.history-list {padding: 0;margin: 0;min-height: 100px;}
.empty-conv {padding: 20px;text-align: center;color: #999;font-size: 14px;}
.menu-item {display: flex;align-items: center;padding: 12px 20px;cursor: pointer;transition: all 0.3s;color: #333;margin: 0;list-style: none;justify-content: space-between;}
.menu-item:hover {background-color: #f5f5f5;color: #1989fa;}
.menu-item.active {background-color: #e8e8e8;color: #1989fa;font-weight: 500;}
.menu-icon {margin-right: 10px;font-size: 16px;width: 18px;text-align: center;}
.menu-text {font-size: 14px;flex: 1;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;}
.history-item {padding-left: 30px;}
.del-conv-btn {opacity: 0;transition: opacity 0.3s;color: #ff4d4f;padding: 0;width: 20px;height: 20px;}
.history-item:hover .del-conv-btn {opacity: 1;}
.del-conv-btn:hover {background-color: #fff2f0;}
.logout-section {flex-shrink: 0;border-top: 1px solid #f0f0f0;margin-top: 5px;}
.logout-item {width: 100%;}
.main-content {flex: 1;display: flex;flex-direction: column;overflow: hidden;height: 100%;}
.content-header {height: 60px;background-color: #fff;border-bottom: 1px solid #e8e8e8;display: flex;align-items: center;padding: 0 20px;flex-shrink: 0;}
.content-header h3 {margin: 0;font-size: 18px;color: #333;}
.content-body {flex: 1;padding: 20px;overflow-y: hidden;height: 100%;box-sizing: border-box;}
.chat-page {height: 100%;display: flex;flex-direction: column;gap: 20px;}

/* 消息样式 */
.chat-messages {flex: 1;border: 1px solid #e8e8e8;border-radius: 8px;padding: 15px;overflow-y: auto;}
.message-item {
  margin-bottom: 15px;
  display: flex;
  width: 100%;
}
.ai-message {justify-content: flex-start;}
.user-message {justify-content: flex-end;}
.message-content {
  padding: 10px 15px;
  border-radius: 6px;
  display: inline-block;
  max-width: 80%;
  white-space: pre-wrap;
  font-family: "SimSun", serif; /* 宋体 */
  font-size: 14px; /* 小四号字体标准换算值 */
  line-height: 1.5;
}
.ai-message .message-content {background-color: #f0f9ff;}
.user-message .message-content {background-color: #e6f7ff;}

/* 核心调整：输入框容器样式 */
.chat-input-outer-box {
  width: 80%;
  margin: 0 auto;
  border: 2px solid #1989fa;
  border-radius: 8px;
  padding: 12px 15px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column; /* 垂直布局：文本框在上，模式+发送按钮在下 */
  gap: 10px; /* 文本框和模式区的间距 */
  background-color: #ffffff;
}

/* 1. 文本框样式：严格限制3行高度 + 滚轮 */
.chat-input-inner {
  width: 100%; /* 占满容器宽度 */
  border: none !important;
  outline: none !important;
  background: transparent !important;
  resize: none; /* 禁止手动调整大小 */
  font-size: 14px;
  line-height: 1.5; /* 行高固定 */
  padding: 0;
  margin: 0;
  /* 核心：固定3行高度（14px*1.5行高*3行=63px） */
  height: 63px; 
  /* 超过3行显示垂直滚轮 */
  overflow-y: auto; 
}
/* 文本框滚动条优化 */
.chat-input-inner::-webkit-scrollbar {width: 6px;}
.chat-input-inner::-webkit-scrollbar-track {background: #f5f5f5;border-radius: 3px;}
.chat-input-inner::-webkit-scrollbar-thumb {background-color: #dcdcdc;border-radius: 3px;}
.chat-input-inner::placeholder {color: #999999;}

/* 2. 模式+发送按钮容器（包裹模式和发送按钮） */
.mode-send-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between; /* 模式居左，发送按钮居右 */
  width: 100%;
}

/* 模式选择器样式 */
.mode-selector {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.mode-btn {
  padding: 6px 12px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background-color: #ffffff; /* 默认白底 */
  color: #333333; /* 默认黑字 */
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.mode-btn:hover {border-color: #1989fa;}
.mode-btn.active {
  background-color: #e8e8e8; /* 选中灰底 */
  color: #1989fa; /* 选中蓝字 */
  border-color: #1989fa;
}
.mode-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f5f5f5;
}

/* 发送按钮样式 */
.send-button {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #1989fa;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  flex-shrink: 0; /* 固定大小，不压缩 */
}
.send-button:hover {background-color: #0e70d1;}
.send-button:active {background-color: #0a5cad;}
.send-button:disabled {background-color: #8cc5ff;cursor: not-allowed;}
.send-button svg {transform: translateY(1px);}
.loading-icon {color: #fff;font-size: 16px;animation: el-loading-rotate 1.5s linear infinite;}

:deep(.el-loading-mask) {background-color: rgba(255, 255, 255, 0.8);}
:deep(.el-loading-spinner) {top: 40%;}
</style>