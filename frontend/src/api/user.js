import request from './index'

// 登录接口
export const login = (data) => {
  return request({
    url: '/login',
    method: 'post',
    data
  })
}

// 获取当前用户信息
export const getUserInfo = () => {
  return request({
    url: '/api/user/info',
    method: 'get'
  })
}

// 权限测试接口
export const testPermission = (permCode) => {
  return request({
    url: `/api/test/perm/${permCode}`,
    method: 'get'
  })
}