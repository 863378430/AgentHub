<!-- src/App.vue -->
<template>
  <router-view />  <!-- 只保留路由视图 -->
</template>

<script setup>
// 空脚本
</script>

<style>
/* 1. 全局盒模型重置（基础） */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 2. 关键：修复高度继承链 + 覆盖 style.css 中 #app 的干扰样式 */
html, body, #app {
  height: 100%;          /* 让 MainLayout 的 100vh 能正确继承 */
  width: 100%;           /* 取消 style.css 中 #app 的固定宽度 1126px */
  border: none !important; /* 取消 style.css 中 #app 的左右边框 */
  text-align: left !important; /* 取消 style.css 中 #app 的居中对齐 */
  margin: 0 !important;  /* 取消 style.css 中 #app 的自动居中 margin */
}

/* 3. 基础字体/背景配置（和项目风格统一） */
body {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f5f5; /* 和 MainLayout 背景一致，避免割裂 */
}
</style>