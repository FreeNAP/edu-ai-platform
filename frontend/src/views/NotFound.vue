<template>
  <main class="nf-page">
    <div class="nf">
      <BrandMark :size="40" />
      <p class="eyebrow">404</p>
      <h1 class="page-title">这个页面不存在</h1>
      <p class="lead">链接可能写错了，或者内容已经下架。</p>
      <el-button type="primary" @click="$router.push('/')">回到课程中心</el-button>
    </div>
  </main>
</template>

<script setup>
import BrandMark from '../components/icons/BrandMark.vue'
</script>

<style scoped>
.nf-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
  background: var(--bg);
}

.nf {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  max-width: 420px;
}

.nf .eyebrow {
  margin-top: 20px;
}

.nf .el-button {
  margin-top: 20px;
}
</style>
