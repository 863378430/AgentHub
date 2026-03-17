import request from './index'

// ========== 对话(Conversation)相关接口 ==========
/**
 * 创建新对话
 * @param {Object} data - { username, title }
 */
export const createConversation = (data) => {
  return request({
    url: '/api/conversation',
    method: 'post',
    data
  })
}

/**
 * 获取单个对话详情
 * @param {string} conversationId - 16位对话ID
 */
export const getConversation = (conversationId) => {
  return request({
    url: `/api/conversation/${conversationId}`,
    method: 'get'
  })
}

/**
 * 获取用户所有对话
 * @param {string} username - 用户名
 */
export const getUserConversations = (username) => {
  return request({
    url: `/api/conversations/${username}`,
    method: 'get'
  })
}

/**
 * 更新对话标题
 * @param {string} conversationId - 16位对话ID
 * @param {Object} data - { title }
 */
export const updateConversation = (conversationId, data) => {
  return request({
    url: `/api/conversation/${conversationId}`,
    method: 'put',
    data
  })
}

/**
 * 删除对话（软删除）
 * @param {string} conversationId - 16位对话ID
 */
export const deleteConversation = (conversationId) => {
  return request({
    url: `/api/conversation/${conversationId}`,
    method: 'delete'
  })
}

// ========== 消息(Message)相关接口 ==========
/**
 * 发送消息
 * @param {Object} data - { conversation_id, username, role, content }
 */
export const sendMessage = (data) => {
  return request({
    url: '/api/message',
    method: 'post',
    data
  })
}

/**
 * 获取对话的所有消息
 * @param {string} conversationId - 16位对话ID
 */
export const getConversationMessages = (conversationId) => {
  return request({
    url: `/api/messages/${conversationId}`,
    method: 'get'
  })
}

/**
 * 删除消息（软删除）
 * @param {number} messageId - 消息ID
 */
export const deleteMessage = (messageId) => {
  return request({
    url: `/api/message/${messageId}`,
    method: 'delete'
  })
}