<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 操作日志</p>
        <h1 class="page-title">操作日志</h1>
        <p class="lead">管理员和教师的每一次新增、修改、删除都会记录操作人、接口、时间和来源 IP。</p>
      </div>
    </div>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索操作人、动作或接口" clearable style="max-width: 300px" @keyup.enter="onSearch" @clear="onSearch" />
      <el-button @click="onSearch">搜索</el-button>
    </div>
    <el-table v-loading="loading" class="panel-table" :data="items" empty-text="暂无记录">
      <el-table-column label="时间" width="170"><template #default="{ row }"><span class="mono">{{ fmtDate(row.created_at) }}</span></template></el-table-column>
      <el-table-column prop="actor_name" label="操作人" width="120" />
      <el-table-column label="动作" min-width="180"><template #default="{ row }"><span class="mono">{{ row.action }}</span></template></el-table-column>
      <el-table-column label="对象" width="120"><template #default="{ row }">{{ row.target_type }}<template v-if="row.target_id"> #{{ row.target_id }}</template></template></el-table-column>
      <el-table-column prop="detail" label="接口" min-width="220" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP" width="130" />
    </el-table>
    <el-pagination v-if="total > size" v-model:current-page="page" :page-size="size" :total="total" layout="total, prev, pager, next" background @current-change="load" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../../api/index'
import { fmtDate, normalizePage } from '../../utils'

const keyword = ref('')
const page = ref(1)
const size = 20
const total = ref(0)
const items = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = normalizePage(await request.get('/admin/audit-logs', { params: { keyword: keyword.value.trim() || undefined, page: page.value, size } }), size)
    items.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

onMounted(load)
</script>
