<template>
  <div v-loading="loading">
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 数据看板</p>
        <h1 class="page-title">平台概况</h1>
        <p class="lead">用户、课程、订单和学习时长的累计数据，下方是最近 7 天的学习活跃人数。</p>
      </div>
    </div>

    <div class="stat-grid">
      <div v-for="s in cards" :key="s.name" class="panel stat">
        <span class="stat-name"><AppIcon :name="s.icon" :size="16" />{{ s.name }}</span>
        <b class="mono">{{ s.value }}</b>
      </div>
    </div>

    <div class="panel mt-16">
      <h2 class="panel-title">近 7 日学习活跃<small>人次 / 天</small></h2>
      <div v-show="trend.length" ref="chartRef" class="trend-chart"></div>
      <el-empty v-if="!trend.length && !loading" description="最近 7 天没有学习记录" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getAdminStats } from '../../api/admin'
import { fmtMinutes } from '../../utils'
import AppIcon from '../../components/icons/AppIcon.vue'

const loading = ref(true)
const stats = ref(null)
const chartRef = ref()
let chart = null

const trend = computed(() => stats.value?.trend || [])

const cards = computed(() => {
  const s = stats.value || {}
  return [
    { name: '注册用户', value: s.users ?? '-', icon: 'users' },
    { name: '近 7 日新用户', value: s.recent_users ?? '-', icon: 'user' },
    { name: '上架课程', value: s.courses ?? '-', icon: 'book' },
    { name: '在招职位', value: s.jobs ?? '-', icon: 'briefcase' },
    { name: '订单数', value: s.orders ?? '-', icon: 'receipt' },
    { name: '已收款', value: `¥${s.paid_amount ?? 0}`, icon: 'cart' },
    { name: '累计学习时长', value: fmtMinutes(s.total_study_minutes), icon: 'clock' }
  ]
})

function cssVar(name, fallback) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function renderChart() {
  const list = trend.value
  if (!chartRef.value || !list.length) return
  const accent = cssVar('--accent', '#dafa9c')
  const muted = cssVar('--muted', '#9a9a9a')
  const line = cssVar('--line', '#2a2a2a')
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    backgroundColor: 'transparent',
    textStyle: { color: muted, fontFamily: 'Geist Mono Variable, monospace' },
    grid: { left: 8, right: 16, top: 16, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: list.map((t) => t.date), boundaryGap: false, axisLine: { lineStyle: { color: line } }, axisLabel: { color: muted } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: line } }, axisLabel: { color: muted } },
    series: [{
      name: '学习活跃',
      type: 'line',
      data: list.map((t) => t.value),
      symbol: 'rect',
      symbolSize: 6,
      lineStyle: { width: 2, color: accent },
      itemStyle: { color: accent },
      areaStyle: { color: accent, opacity: 0.08 }
    }]
  }, true)
  chart.resize()
}

onMounted(async () => {
  try {
    stats.value = await getAdminStats()
    await nextTick()
    renderChart()
    window.addEventListener('resize', renderChart)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderChart)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(200px, 100%), 1fr));
  gap: 12px;
}

@media (max-width: 560px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stat b {
    font-size: 22px;
  }
}

.stat-grid .panel + .panel {
  margin-top: 0;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
}

.stat b {
  font-size: 28px;
  font-weight: 500;
  letter-spacing: -0.03em;
}

.trend-chart {
  height: 320px;
}
</style>
