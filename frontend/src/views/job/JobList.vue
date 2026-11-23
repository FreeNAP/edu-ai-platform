<template>
  <div class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">实习就业 · {{ total }} 个岗位</p>
        <h1 class="page-title">实习就业</h1>
        <p class="lead">合作企业发布的实习和校招岗位。投递前可以先做一次 AI 模拟面试，看看自己哪些题答得不够好。</p>
      </div>
      <label class="search-box">
        <AppIcon name="search" />
        <input v-model="keyword" placeholder="搜岗位名或公司名" aria-label="搜索职位" @keyup.enter="onSearch" />
        <button v-if="keyword" class="clear-btn" type="button" aria-label="清空搜索" @click="clearSearch">
          <AppIcon name="close" :size="16" />
        </button>
      </label>
    </div>

    <div class="filters-wrap">
      <div class="filters">
        <span class="lbl">分类</span>
        <button class="chip" :class="{ on: !category }" type="button" @click="setCategory('')">全部</button>
        <button
          v-for="c in meta.categories"
          :key="c"
          type="button"
          class="chip"
          :class="{ on: category === c }"
          @click="setCategory(c)"
        >{{ c }}</button>
      </div>
      <div class="filters">
        <span class="lbl">城市</span>
        <button class="chip" :class="{ on: !city }" type="button" @click="setCity('')">全部</button>
        <button
          v-for="c in meta.cities"
          :key="c"
          type="button"
          class="chip"
          :class="{ on: city === c }"
          @click="setCity(c)"
        >{{ c }}</button>
      </div>
    </div>

    <div v-loading="loading" class="list-area">
      <template v-if="items.length">
        <div class="job-grid">
          <JobCard v-for="j in items" :key="j.id" :job="j" @open="openJob" />
        </div>
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="prev, pager, next"
          :pager-count="5"
          background
          hide-on-single-page
          @current-change="fetchList"
        />
      </template>
      <el-empty v-else-if="!loading" description="没有符合条件的职位，换个分类或城市试试" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getJobs, getJobFilters } from '../../api/job'
import { normalizePage } from '../../utils'
import JobCard from '../../components/JobCard.vue'
import AppIcon from '../../components/icons/AppIcon.vue'

const router = useRouter()

const meta = reactive({ categories: [], cities: [] })
const category = ref('')
const city = ref('')
const keyword = ref('')
const page = ref(1)
const size = 12
const total = ref(0)
const items = ref([])
const loading = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (category.value) params.category = category.value
    if (city.value) params.city = city.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const data = await getJobs(params)
    const p = normalizePage(data, size)
    items.value = p.items
    total.value = p.total
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function setCategory(v) {
  category.value = v
  onSearch()
}

function setCity(v) {
  city.value = v
  onSearch()
}

function onSearch() {
  page.value = 1
  fetchList()
}

function clearSearch() {
  keyword.value = ''
  onSearch()
}

function openJob(j) {
  router.push(`/job/${j.id}`)
}

onMounted(async () => {
  fetchList()
  try {
    const m = await getJobFilters()
    meta.categories = m?.categories || []
    meta.cities = m?.cities || []
  } catch {
    /* 筛选元数据失败不阻塞列表 */
  }
})
</script>

<style scoped>
.clear-btn {
  border: 0;
  background: transparent;
  color: var(--muted);
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  cursor: pointer;
}

.clear-btn:hover {
  color: var(--ink);
}

.list-area {
  min-height: 300px;
}
</style>
