<template>
  <div class="app-container">
    <div class="sidebar">
      <div class="logo"><h2>AgentHub</h2></div>
      <div class="menu-wrapper">
        <div class="core-menu">
          <div class="menu-item create-conv-item" @click="createNewConversation">
            <span class="menu-icon">➕</span><span class="menu-text">新建对话</span>
          </div>
        </div>
        <div class="history-section">
          <div class="history-divider"></div>
          <div class="history-title">历史对话</div>
          <div class="history-list" v-loading="loadingConvs">
            <div 
              v-for="item in conversationList" 
              :key="item.conversation_id" 
              class="menu-item history-item" 
              :class="{ active: currentConvId === item.conversation_id }"
              @click="handleConversationClick(item.conversation_id)"
            >
              <!-- 仅保留标题文本 -->
              <span class="menu-text">
                {{ item.title || `对话-${item.conversation_id.slice(-4)}` }}
              </span>
              
              <!-- 省略号按钮（正常显示） -->
              <div class="conv-actions" @click.stop>
                <span class="more-btn" @click.stop="toggleMenu(item.conversation_id)">⋯</span>
                <div 
                  class="conv-menu" 
                  v-show="showMenu && activeMenuConvId === item.conversation_id"
                  @click.stop
                >
                  <div class="menu-option" @click="startRename(item.conversation_id, item.title)">重命名</div>
                  <div class="menu-option" @click="handleDeleteConv(item.conversation_id)">删除</div>
                </div>
              </div>
            </div>
            <div v-if="!loadingConvs && !conversationList.length" class="empty-conv">暂无历史对话</div>
          </div>
        </div>
        <div class="logout-section">
          <div class="menu-item logout-item" @click="handleLogout">
            <span class="menu-icon">❎</span><span class="menu-text">退出登录</span>
          </div>
        </div>
      </div>
    </div>
    <div class="main-content">
      <div class="content-header"><h3>{{ currentConvTitle || 'AgentHub' }}</h3></div>
      <div class="content-body">
        <div class="chat-page">
          <div class="chat-messages" v-loading="loadingMessages">
            <div class="message-item" v-for="(msg, index) in messageList" :key="index" :class="{'user-message': msg.sender === '用户','ai-message': msg.sender === 'AI'}">
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </div>
          <div class="chat-input-outer-box">
            <textarea v-model="message" placeholder="请输入消息..." @keydown.enter.prevent="handleEnterKey($event)" class="chat-input-inner" :disabled="sendingMessage"></textarea>
            <div class="mode-send-wrapper">
              <div class="mode-selector">
                <button v-for="mode in modeList" :key="mode" class="mode-btn" :class="{ active: currentMode === mode }" @click="selectMode(mode)" :disabled="sendingMessage">{{ mode }}</button>
              </div>
              <button class="send-button" @click="sendMessage" :disabled="sendingMessage">
                <svg v-if="!sendingMessage" width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2L10 16M10 2L16 8M10 2L4 8" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/></svg>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { clearAuth, getUserInfo } from '@/utils/auth'
import { getUserConversations, createConversation, deleteConversation, sendMessage as apiSendMessage, getConversationMessages, updateConversation } from '@/api/chat'
const router = useRouter(), route = useRoute(), userInfo = getUserInfo(), username = userInfo.username || ''
const [message, messageList, currentConvId, conversationList] = [ref(''), ref([]), ref(''), ref([])]
const [loadingConvs, loadingMessages, sendingMessage] = [ref(false), ref(false), ref(false)]
const [modeList, currentMode] = [ref(['自动', '数据', '配置', '代码', '翻译']), ref('自动')]
const [showMenu, activeMenuConvId] = [ref(false), ref('')]

const currentConvTitle = computed(() => 
  conversationList.value.find(item => item.conversation_id === currentConvId.value)?.title || '新对话'
)

const selectMode = (mode) => { if (!sendingMessage.value) currentMode.value = mode }

const scrollToBottom = async () => {
  await nextTick() // 等待DOM更新完成
  const el = document.querySelector('.chat-messages')
  if (el) el.scrollTop = el.scrollHeight
}

const sendMessage = async () => {
  const content = message.value.trim()
  if (!content || sendingMessage.value || !currentConvId.value) return
  try {
    sendingMessage.value = true
    messageList.value.push({ sender: '用户', content })
    message.value = ''
    const res = await apiSendMessage({ conversation_id: currentConvId.value, username, content, mode: currentMode.value })
    if (res?.content) messageList.value.push({ sender: 'AI', content: res.content })
    else ElMessage.warning('未收到AI回复')
    await scrollToBottom() // 替换原有滚动代码
  } catch (e) {
    messageList.value.pop()
    ElMessage.error(`发送失败：${e.message || '网络异常'}`)
  } finally { sendingMessage.value = false }
}

const loadConversationMessages = async (convId) => {
  if (!convId) return
  try {
    loadingMessages.value = true
    const res = await getConversationMessages(convId)
    messageList.value = res.map(msg => ({ 
      sender: msg.role === 'user' ? '用户' : 'AI', content: msg.content 
    }))
    await scrollToBottom() // 替换原有滚动代码
  } catch (e) {
    ElMessage.error(`加载消息失败：${e.message}`)
    messageList.value = []
  } finally { loadingMessages.value = false }
}

const handleEnterKey = (e) => {
  if (e.ctrlKey || e.metaKey) {
    const pos = e.target.selectionStart
    message.value = `${message.value.substring(0, pos)}\n${message.value.substring(pos)}`
    e.target.selectionStart = e.target.selectionEnd = pos + 1
  } else sendMessage()
}

const loadConversationList = async () => {
  if (!username) return
  try {
    loadingConvs.value = true
    const res = await getUserConversations(username)
    conversationList.value = res
    if (res.length && !currentConvId.value) {
      currentConvId.value = res[0].conversation_id
      await loadConversationMessages(res[0].conversation_id)
    }
  } catch (e) {
    ElMessage.error(`加载对话失败：${e.message}`)
    conversationList.value = []
  } finally { loadingConvs.value = false }
}

const createNewConversation = async () => {
  if (!username) { ElMessage.warning('请先登录'); return router.push('/login') }
  try {
    loadingConvs.value = true
    const res = await createConversation({ 
      username, title: `新对话-${Date.now().toString().slice(-4)}` 
    })
    currentConvId.value = res.conversation_id
    messageList.value = []
    await loadConversationList()
    ElMessage.success('新对话创建成功')
  } catch (e) {
    ElMessage.error(`创建失败：${e.message}`)
  } finally { loadingConvs.value = false }
}

const handleConversationClick = (convId) => {
  if (currentConvId.value !== convId) {
    currentConvId.value = convId
    loadConversationMessages(convId)
  }
  showMenu.value = false
}

const handleDeleteConv = async (convId) => {
  try {
    await ElMessageBox.confirm('确定删除该对话？删除后不可恢复', '提示', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    await deleteConversation(convId)
    ElMessage.success('删除成功')
    await loadConversationList()
    if (convId === currentConvId.value) {
      currentConvId.value = conversationList.value[0]?.conversation_id || ''
      if (currentConvId.value) await loadConversationMessages(currentConvId.value)
      else createNewConversation()
    }
  } catch (e) { if (e !== 'cancel') ElMessage.error(`删除失败：${e.message}`) }
  showMenu.value = false
}

const toggleMenu = (convId) => {
  showMenu.value = !showMenu.value
  activeMenuConvId.value = showMenu.value ? convId : ''
}

// 核心修改：弹窗重命名，完全解决所有问题
const startRename = async (convId, oldTitle) => {
  showMenu.value = false
  try {
    const { value } = await ElMessageBox.prompt('', '编辑对话名称', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputValue: oldTitle || `对话-${convId.slice(-4)}`
    })
    const newTitle = value.trim()
    if (!newTitle) {
      ElMessage.warning('标题不能为空')
      return
    }
    await updateConversation(convId, { title: newTitle })
    const idx = conversationList.value.findIndex(item => item.conversation_id === convId)
    if (idx > -1) conversationList.value[idx].title = newTitle
    ElMessage.success('重命名成功')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`重命名失败：${e.message}`)
  }
}

const handleLogout = () => {
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}

watch(() => route.path, (newPath) => {
  if (newPath === '/chat' || newPath === '/') loadConversationList()
}, { immediate: true })

onMounted(() => {
  if (username) loadConversationList()
  document.addEventListener('click', () => showMenu.value = false)
})
</script>

<style scoped>
/* 其他样式保持不变，仅修改 .content-header 部分 */
.app-container {display: flex;height: 100vh;background: #f5f5f5;width: 100%;}
.sidebar {width: 240px;background: #fff;border-right: 1px solid #e8e8e8;display: flex;flex-direction: column;height: 100%;flex-shrink: 0;}
.logo {height: 60px;display: flex;align-items: center;padding-left: 20px;border-bottom: 1px solid #e8e8e8;}
.logo h2 {font-size: 20px;color: #1989fa;margin: 0;}
.menu-wrapper {flex: 1;display: flex;flex-direction: column;padding: 10px 0;overflow: hidden;}
.create-conv-item {margin-top: 8px;color: #1989fa;}
.create-conv-item:hover {background: #f0f9ff;}
.history-section {flex: 1;overflow-y: auto;margin: 10px 0;scrollbar-width: thin;}
.history-section::-webkit-scrollbar {width: 6px;}
.history-section::-webkit-scrollbar-thumb {background: #dcdcdc;border-radius: 3px;}
.history-divider {height: 1px;background: #f0f0f0;margin: 0 20px;}
.history-title {padding: 10px 20px;font-size: 12px;color: #999;}
.history-list {padding: 0;margin: 0;min-height: 100px;}
.empty-conv {padding: 20px;text-align: center;color: #999;}
.menu-item {display: flex;align-items: center;padding: 12px 20px;cursor: pointer;transition: all .3s;color: #333;justify-content: space-between;}
.menu-item:hover {background: #f5f5f5;color: #1989fa;}
.menu-item.active {background: #e8e8e8;color: #1989fa;font-weight: 500;}
.menu-icon {margin-right: 10px;}
.menu-text {font-size: 14px;flex: 1;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;}
.history-item {padding-left: 30px;position: relative;}
.logout-section {border-top: 1px solid #f0f0f0;}
.main-content {flex: 1;display: flex;flex-direction: column;overflow: hidden;}
.content-header {height: 60px; background: #fff; border-bottom: 1px solid #e8e8e8; display: flex; align-items: center; /* 垂直居中 */ justify-content: center; /* 水平居中 */ padding: 0 20px;}
.content-header h3 {margin: 0;font-size: 18px;}
.content-body {flex: 1;padding: 20px;overflow: hidden;}
.chat-page {height: 100%;display: flex;flex-direction: column;gap: 20px;}
.chat-messages {flex: 1;border: 1px solid #e8e8e8;border-radius: 8px;padding: 15px;overflow-y: auto;}
.message-item {margin-bottom: 15px;display: flex;}
.ai-message {justify-content: flex-start;}
.user-message {justify-content: flex-end;}
.message-content {padding: 10px 15px;border-radius: 6px;max-width: 80%;white-space: pre-wrap;font-size: 14px;}
.ai-message .message-content {background: #f0f9ff;}
.user-message .message-content {background: #e6f7ff;}
.chat-input-outer-box {width: 80%;margin: 0 auto;border: 2px solid #1989fa;border-radius: 8px;padding: 12px 15px;background: #fff;}
.chat-input-inner {width: 100%;border: none;outline: none;resize: none;font-size: 14px;height: 63px;}
.mode-send-wrapper {display: flex;align-items: center;justify-content: space-between;margin-top: 10px;}
.mode-selector {display: flex;gap: 6px;}
.mode-btn {padding: 6px 12px;border: 1px solid #e8e8e8;border-radius: 4px;background: #fff;font-size: 12px;cursor: pointer;}
.mode-btn:hover {border-color: #1989fa;}
.mode-btn.active {background: #e8e8e8;color: #1989fa;border-color: #1989fa;}
.send-button {width: 30px;height: 30px;border-radius: 50%;background: #1989fa;border: none;cursor: pointer;display: flex;align-items: center;justify-content: center;}
.send-button:hover {background: #0e70d1;}
.loading-icon {color: #fff;animation: el-loading-rotate 1.5s infinite linear;}
.conv-actions {position: relative;}
.more-btn {font-size: 18px;cursor: pointer;color: #666;padding: 0 4px;user-select: none;}
.history-item:hover .more-btn {color: #1989fa;}
.conv-menu {position: absolute;right: 0;top: 24px;z-index: 999;width: 100px;background: #fff;border: 1px solid #e8e8e8;border-radius: 4px;box-shadow: 0 2px 12px rgba(0,0,0,.1);}
.menu-option {padding: 8px 12px;font-size: 12px;cursor: pointer;}
.menu-option:hover {background: #f5f5f5;color: #1989fa;}
</style>