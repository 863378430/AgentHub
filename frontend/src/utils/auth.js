// 存储 Token
export const setToken = (token) => {
    localStorage.setItem('token', token)
  }
  
  // 获取 Token
  export const getToken = () => {
    return localStorage.getItem('token') || ''
  }
  
  // 存储用户信息
  export const setUserInfo = (userInfo) => {
    localStorage.setItem('userInfo', JSON.stringify(userInfo))
  }
  
  // 获取用户信息
  export const getUserInfo = () => {
    const userInfoStr = localStorage.getItem('userInfo')
    try {
      return userInfoStr ? JSON.parse(userInfoStr) : {}
    } catch {
      return {}
    }
  }
  
  // 清除认证信息
  export const clearAuth = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }