<!-- src/views/DataPage.vue -->
<template>
  <div class="data-page">
    <h4>数据审核</h4>
    <p>数据审核功能正在开发中...</p>
    <el-table :data="tableData" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="date" label="日期" width="180" />
      <el-table-column prop="name" label="姓名" width="180" />
      <el-table-column prop="address" label="地址" />
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const tableData = ref([
  {
    date: '2026-03-01',
    name: '张三',
    address: '北京市朝阳区'
  },
  {
    date: '2026-03-02',
    name: '李四',
    address: '上海市浦东新区'
  }
])
</script>

<style scoped>
.data-page {
  padding: 20px;
}
</style>