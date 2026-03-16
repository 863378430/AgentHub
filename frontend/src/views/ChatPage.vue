<!-- src/views/ChatPage.vue -->
<template>
  <div class="chat-page">
    <h4>新对话</h4>
    <p>当前对话：{{ $route.query.id || '新建对话' }}</p>
    
    <div class="chat-container">
      <div class="chat-messages">
        <div class="message-item">
          <div class="message-author">系统</div>
          <div class="message-content">欢迎使用 AgentHub 对话功能！</div>
        </div>
      </div>
      
      <div class="chat-input">
        <el-input 
          v-model="message" 
          placeholder="请输入消息..."
          @keyup.enter="sendMessage"
        >
          <template #append>
            <el-button @click="sendMessage" type="primary">发送</el-button>
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const message = ref('')

const sendMessage = () => {
  if (!message.value) return
  console.log('发送消息：', message.value)
  message.value = ''
}
</script>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 20px;
}

.chat-messages {
  flex: 1;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 15px;
  overflow-y: auto;
}

.message-item {
  margin-bottom: 15px;
}

.message-author {
  font-size: 12px;
  color: #999;
  margin-bottom: 5px;
}

.message-content {
  background-color: #f0f9ff;
  padding: 10px 15px;
  border-radius: 6px;
  display: inline-block;
}

.chat-input {
  width: 100%;
}
</style>