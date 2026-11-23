<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 订单管理</p>
        <h1 class="page-title">订单管理</h1>
        <p class="lead">课程订单与支付状态。</p>
      </div>
    </div>
    <div class="toolbar">
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 140px" @change="fetchList">
        <el-option label="待支付" value="pending" />
        <el-option label="已支付" value="paid" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="order_no" label="订单号" min-width="160">
        <template #default="{ row }">{{ row.order_no || `ORD-${row.id}` }}</template>
      </el-table-column>
      <el-table-column label="课程" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.course?.title || row.course_title || '-' }}</template>
      </el-table-column>
      <el-table-column label="用户" width="120">
        <template #default="{ row }">{{ row.user?.nickname || row.user?.username || row.username || '-' }}</template>
      </el-table-column>
      <el-table-column label="金额" width="100">
        <template #default="{ row }"><span class="price">¥{{ row.amount }}</span></template>
      </el-table-column>
      <el-table-column label="状态" width="150">
        <template #default="{ row }">
          <el-select :model-value="row.status" size="small" style="width: 120px" @change="(v) => onStatus(row, v)">
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="支付时间" width="160">
        <template #default="{ row }">{{ row.paid_at ? fmtDate(row.paid_at) : '-' }}</template>
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
import { adminGetOrders, adminUpdateOrder } from '../../api/admin'
import { normalizePage, fmtDate } from '../../utils'

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
    const p = normalizePage(await adminGetOrders(params), size)
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

async function onStatus(row, v) {
  try {
    await adminUpdateOrder(row.id, { status: v })
    row.status = v
    ElMessage.success('状态已更新')
  } catch (e) {
    ElMessage.error(e.message)
    fetchList()
  }
}

onMounted(fetchList)
</script>
