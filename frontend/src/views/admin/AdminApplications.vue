<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 申请管理</p>
        <h1 class="page-title">申请管理</h1>
        <p class="lead">学生投递的职位申请，改状态后申请人会收到通知。</p>
      </div>
    </div>
    <div class="toolbar">
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 140px" @change="fetchList">
        <el-option v-for="(v, k) in APP_STATUS" :key="k" :label="v.label" :value="k" />
      </el-select>
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="岗位" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.job?.title || row.job_title || '-' }}</template>
      </el-table-column>
      <el-table-column label="公司" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.job?.company || row.company || '-' }}</template>
      </el-table-column>
      <el-table-column label="申请人" width="110">
        <template #default="{ row }">{{ row.user?.nickname || row.user?.username || row.username || '-' }}</template>
      </el-table-column>
      <el-table-column prop="message" label="附言" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.message || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="150">
        <template #default="{ row }">
          <el-select :model-value="row.status" size="small" style="width: 120px" @change="(v) => onStatus(row, v)">
            <el-option v-for="(v2, k) in APP_STATUS" :key="k" :label="v2.label" :value="k" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="申请时间" width="160">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
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
import { ElMessage } from 'element-plus'
import { adminGetApplications, adminUpdateApplication } from '../../api/admin'
import { normalizePage, fmtDate, APP_STATUS } from '../../utils'

const status = ref('')
const page = ref(1)
const size = 15
const total = ref(0)
const items = ref([])
const loading = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (status.value) params.status = status.value
    const p = normalizePage(await adminGetApplications(params), size)
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

async function onStatus(row, v) {
  try {
    await adminUpdateApplication(row.id, { status: v })
    row.status = v
    ElMessage.success('状态已更新')
  } catch (e) {
    ElMessage.error(e.message)
    fetchList()
  }
}

onMounted(fetchList)
</script>
