<template>
  <el-config-provider :locale="zhCn">
    <div v-if="crashed" class="crash">
      <p class="eyebrow">页面出错了</p>
      <h1 class="page-title">这个页面加载失败</h1>
      <p class="lead">可能是网络中断或版本刚更新。刷新一下通常就好；如果反复出现，请把下面的信息发给管理员。</p>
      <pre class="mono">{{ crashed }}</pre>
      <el-button type="primary" @click="reload">刷新页面</el-button>
    </div>
    <router-view v-else />
  </el-config-provider>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const crashed = ref('')
const router = useRouter()

onErrorCaptured((err) => {
  console.error(err)
  crashed.value = String(err?.message || err).slice(0, 300)
  return false
})

// 发版后旧页面引用的分包已不存在：自动刷新到新版本
router.onError((err) => {
  if (/Failed to fetch dynamically imported module|Importing a module script failed/.test(String(err?.message))) {
    window.location.reload()
  }
})

router.afterEach(() => {
  crashed.value = ''
})

function reload() {
  window.location.reload()
}
</script>

<style scoped>
.crash {
  max-width: 640px;
  margin: 12vh auto;
  padding: 0 24px;
}

.crash pre {
  white-space: pre-wrap;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: var(--r);
  color: var(--muted);
  font-size: 12px;
}
</style>
