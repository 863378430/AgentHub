<!-- src/views/PermissionPage.vue -->
<template>
  <div class="permission-page">
    <h4>权限管理</h4>
    <p>权限管理功能正在开发中...</p>
    <el-card style="margin-top: 20px;">
      <el-table :data="permData" border style="width: 100%;">
        <el-table-column prop="role" label="角色" width="180" />
        <el-table-column prop="permissions" label="权限" />
        <el-table-column label="操作">
          <template #default>
            <el-button type="primary" text>编辑</el-button>
            <el-button type="danger" text>删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const permData = ref([
  {
    role: '管理员',
    permissions: 'user:view,user:edit,data:audit,perm:manage'
  },
  {
    role: '普通用户',
    permissions: 'user:view,chat:send'
  }
])
</script>

<style scoped>
.permission-page {
  padding: 20px;
}
</style>