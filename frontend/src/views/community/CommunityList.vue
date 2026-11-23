<template>
  <div class="page page-narrow">
    <div class="page-head">
      <div>
        <p class="eyebrow">问答社区 · {{ total }} 个问题</p>
        <h1 class="page-title">卡住了就来问</h1>
        <p class="lead">报错、概念、选课和求职经验都可以问。描述清楚环境和已经试过的办法，回答会快很多。</p>
      </div>
      <el-button type="primary" @click="askVisible = true"><AppIcon name="edit" :size="16" />提问</el-button>
    </div>

    <form class="search-row" @submit.prevent="onSearch">
      <label class="search-box">
        <AppIcon name="search" />
        <input v-model="keyword" placeholder="搜问题标题或内容" aria-label="搜索问题" />
      </label>
      <el-button native-type="submit">搜索</el-button>
    </form>

    <div class="q-list" v-loading="loading">
      <el-empty v-if="!items.length && !loading" description="还没有问题，来提第一个吧" />
      <div
        v-for="q in items"
        :key="q.id"
        class="panel q-item hover-card clickable"
        @click="$router.push(`/community/${q.id}`)"
      >
        <div class="q-main">
          <div class="q-title">{{ q.title }}</div>
          <div class="q-content text-sub">{{ q.content }}</div>
          <div class="q-meta text-sub">
            <UserAvatar :user="q.user" :size="20" />
            <span>{{ q.user?.nickname || q.user?.username || '同学' }}</span>
            <span>· {{ fmtDate(q.created_at) }}</span>
          </div>
        </div>
        <div class="q-stats">
          <div class="q-stat"><span class="q-num mono">{{ q.answers_count ?? 0 }}</span><span class="text-sub">回答</span></div>
          <div class="q-stat"><span class="q-num mono">{{ q.views ?? 0 }}</span><span class="text-sub">浏览</span></div>
        </div>
      </div>
      <el-pagination
        v-model:current-page="page"
        :page-size="size"
        :total="total"
        layout="total, prev, pager, next"
        :pager-count="5"
        background
        @current-change="fetchList"
      />
    </div>

    <el-dialog v-model="askVisible" title="提一个问题" width="min(560px, 92vw)">
      <el-form label-position="top">
        <el-form-item label="问题标题" required>
          <el-input v-model="askForm.title" maxlength="120" show-word-limit placeholder="一句话描述你的问题" />
        </el-form-item>
        <el-form-item label="问题描述" required>
          <el-input v-model="askForm.content" type="textarea" :rows="5" maxlength="2000" show-word-limit placeholder="补充背景、报错信息、已尝试的方案…" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="askVisible = false">取消</el-button>
        <el-button type="primary" :loading="asking" @click="onAsk">发布问题</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppIcon from '../../components/icons/AppIcon.vue'
import { getQuestions, postQuestion } from '../../api/community'
import { normalizePage, fmtDate } from '../../utils'
import UserAvatar from '../../components/UserAvatar.vue'

const router = useRouter()

const keyword = ref('')
const page = ref(1)
const size = 10
const total = ref(0)
const items = ref([])
const loading = ref(false)

const askVisible = ref(false)
const asking = ref(false)
const askForm = reactive({ title: '', content: '' })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const p = normalizePage(await getQuestions(params), size)
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  fetchList()
}

async function onAsk() {
  if (!askForm.title.trim() || !askForm.content.trim()) {
    ElMessage.warning('请填写标题与描述')
    return
  }
  asking.value = true
  try {
    const q = await postQuestion({ title: askForm.title.trim(), content: askForm.content.trim() })
    askVisible.value = false
    askForm.title = askForm.content = ''
    ElMessage.success('发布成功')
    if (q?.id) router.push(`/community/${q.id}`)
    else fetchList()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    asking.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.search-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.search-row .search-box {
  flex: 1;
}

.page-head .el-button {
  gap: 6px;
}

.q-list {
  display: grid;
  gap: 8px;
  min-height: 120px;
}

.q-list .panel + .panel {
  margin-top: 0;
}

.q-item {
  display: flex;
  gap: 20px;
  align-items: center;
}

.q-main {
  flex: 1;
  min-width: 0;
}

.q-title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.q-content {
  margin: 6px 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.6;
}

.q-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.q-stats {
  display: flex;
  gap: 18px;
}

.q-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 44px;
}

.q-num {
  font-size: 20px;
  color: var(--ink);
}

.q-list :deep(.el-pagination) {
  justify-content: center;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .q-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .q-stats {
    gap: 24px;
  }

  .q-stat {
    flex-direction: row;
    gap: 6px;
  }
}
</style>
