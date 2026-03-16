// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

// 修复：统一使用 @/ 别名（避免相对路径层级错误）
import Login from '@/views/Login.vue'
import MainLayout from '@/views/MainLayout.vue'
import ChatPage from '@/views/ChatPage.vue'
import DataPage from '@/views/DataPage.vue'
import PermissionPage from '@/views/PermissionPage.vue'

// 导入权限工具函数
import { getToken } from '@/utils/auth'

// 定义路由规则
const routes = [
  // 登录页面路由
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录 - AgentHub',
      requiresAuth: false
    }
  },
  // 主布局路由（嵌套子路由）
  {
    path: '/',
    name: 'Main',
    component: MainLayout,
    meta: {
      requiresAuth: true
    },
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: ChatPage,
        meta: { title: '新对话 - AgentHub', requiresAuth: true }
      },
      {
        path: 'data',
        name: 'Data',
        component: DataPage,
        meta: { title: '数据审核 - AgentHub', requiresAuth: true }
      },
      {
        path: 'permission',
        name: 'Permission',
        component: PermissionPage,
        meta: { title: '权限管理 - AgentHub', requiresAuth: true }
      }
    ]
  },
  // 404 页面重定向
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 路由守卫：验证登录状态
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }

  const token = getToken()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && token) {
    next({ name: 'Chat' })
  } else {
    next()
  }
})

// 导出路由实例
export default router