<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 社区管理</p>
        <h1 class="page-title">社区管理</h1>
        <p class="lead">问答社区里的全部问题。删除问题会连同下面的回答一起删除。</p>
      </div>
    </div>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索标题或内容" clearable :prefix-icon="SearchIcon" style="max-width: 280px" @keyup.enter="onSearch" @clear="onSearch" />
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="标题" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <router-link :to="`/community/${row.id}`" class="title-link">{{ row.title }}</router-link>
        </template>
      </el-table-column>
      <el-table-column label="提问者" width="130">
        <template #default="{ row }">{{ row.user?.nickname || row.user?.username || '-' }}</template>
      </el-table-column>
      <el-table-column label="回答" width="70" align="center">
        <template #default="{ row }"><span class="mono">{{ row.answers_count ?? 0 }}</span></template>
      </el-table-column>
      <el-table-column label="浏览" width="70" align="center">
        <template #default="{ row }"><span class="mono">{{ row.views ?? 0 }}</span></template>
      </el-table-column>
      <el-table-column label="发布时间" width="160">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > size"
      v-model:current-page="page"
      :page-size="size"
      :total="total"
      layout="total, prev, pager, next"
      :pager-count="5"
      background
      @current-change="fetchList"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search as SearchIcon } from '@element-plus/icons-vue'
import { adminGetQuestions, adminDeleteQuestion } from '../../api/admin'
import { normalizePage, fmtDate } from '../../utils'

const keyword = ref('')
const page = ref(1)
const size = 15
const total = ref(0)
const items = ref([])
const loading = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const res = normalizePage(await adminGetQuestions({ keyword: keyword.value.trim() || undefined, page: page.value, size }), size)
    items.value = res.items
    total.value = res.total
  } catch (e) {
    items.value = []
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  fetchList()
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`删除「${row.title}」及其全部回答？`, '删除问题', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  try {
    await adminDeleteQuestion(row.id)
    ElMessage.success('已删除')
    if (items.value.length === 1 && page.value > 1) page.value -= 1
    fetchList()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(fetchList)
</script>

<style scoped>
.title-link {
  color: var(--ink);
}

.title-link:hover {
  color: var(--accent);
}
</style>
