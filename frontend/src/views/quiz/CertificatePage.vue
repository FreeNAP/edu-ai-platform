<template>
  <main class="cert-page">
    <div v-loading="loading" class="cert-wrap">
      <article v-if="cert" class="certificate">
        <header>
          <BrandMark :size="32" />
          <span class="mono">智慧教育平台 · 课程结业证书</span>
        </header>
        <p class="lead-in">兹证明</p>
        <h1 class="holder">{{ cert.holder }}</h1>
        <p class="body-text">
          完成课程<b>《{{ cert.course?.title }}》</b>的学习，并以 <b class="mono">{{ cert.score }}</b> 分通过结业考试。
        </p>
        <dl class="meta">
          <div><dt>证书编号</dt><dd class="mono">{{ cert.cert_no }}</dd></div>
          <div><dt>发证日期</dt><dd class="mono">{{ fmtDay(cert.issued_at) }}</dd></div>
          <div><dt>查验地址</dt><dd class="mono">{{ verifyUrl }}</dd></div>
        </dl>
      </article>
      <el-empty v-else-if="!loading" description="没有找到这张证书，请核对编号">
        <el-button type="primary" @click="$router.push('/')">回到首页</el-button>
      </el-empty>
      <div v-if="cert" class="actions">
        <el-button @click="copyLink">复制查验链接</el-button>
        <el-button type="primary" @click="print">打印 / 另存为 PDF</el-button>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { verifyCertificate } from '../../api/quiz'
import { fmtDay } from '../../utils'
import BrandMark from '../../components/icons/BrandMark.vue'

const route = useRoute()
const loading = ref(true)
const cert = ref(null)
const verifyUrl = computed(() => `${window.location.origin}/certificate/${cert.value?.cert_no || ''}`)

async function copyLink() {
  try {
    await navigator.clipboard.writeText(verifyUrl.value)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址栏')
  }
}

function print() {
  window.print()
}

onMounted(async () => {
  try {
    cert.value = await verifyCertificate(route.params.no)
  } catch {
    cert.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.cert-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 16px;
  background: var(--bg);
}

.cert-wrap {
  width: min(820px, 100%);
}

.certificate {
  position: relative;
  padding: 48px 56px;
  border: 1px solid var(--line);
  outline: 1px solid var(--accent);
  outline-offset: -10px;
  background: var(--card);
}

header {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--accent);
  font-size: 13px;
  letter-spacing: 0.06em;
}

.lead-in {
  margin: 40px 0 6px;
  color: var(--muted);
}

.holder {
  margin: 0;
  font-size: 44px;
  letter-spacing: -0.02em;
}

.body-text {
  margin: 18px 0 32px;
  font-size: 17px;
  line-height: 1.8;
}

.body-text b {
  color: var(--accent);
}

.meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 0;
  padding-top: 20px;
  border-top: 1px solid var(--line);
}

.meta dt {
  font-size: 12px;
  color: var(--muted);
}

.meta dd {
  margin: 4px 0 0;
  font-size: 13px;
  word-break: break-all;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

@media (max-width: 640px) {
  .certificate {
    padding: 32px 22px;
  }

  .holder {
    font-size: 32px;
  }

  .meta {
    grid-template-columns: 1fr;
  }
}

@media print {
  .actions {
    display: none;
  }

  .cert-page {
    background: #fff;
  }

  .certificate {
    background: #fff;
    color: #111;
    outline-color: #111;
  }
}
</style>
