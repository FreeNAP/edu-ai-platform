<template>
  <div class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">{{ title }} · {{ total }} 门</p>
        <h1 class="page-title">{{ title }}</h1>
        <p class="lead">{{ subtitle }}</p>
      </div>
      <label class="search-box">
        <AppIcon name="search" />
        <input
          v-model="keyword"
          placeholder="搜课程名或讲师"
          aria-label="搜索课程"
          @keyup.enter="onSearch"
        />
        <button v-if="keyword" class="clear-btn" type="button" aria-label="清空搜索" @click="clearSearch">
          <AppIcon name="close" :size="16" />
        </button>
      </label>
    </div>

    <div class="filters-wrap">
      <div class="filters">
        <span class="lbl">方向</span>
        <button class="chip" :class="{ on: !filters.tech_domain }" type="button" @click="setFilter('tech_domain', '')">全部</button>
        <button
          v-for="d in meta.tech_domains"
          :key="d"
          type="button"
          class="chip"
          :class="{ on: filters.tech_domain === d }"
          @click="setFilter('tech_domain', d)"
        >{{ d }}</button>
      </div>
      <div class="filters">
        <span class="lbl">难度</span>
        <button class="chip" :class="{ on: !filters.difficulty }" type="button" @click="setFilter('difficulty', '')">全部</button>
        <button
          v-for="d in meta.difficulties"
          :key="d"
          type="button"
          class="chip"
          :class="{ on: filters.difficulty === d }"
          @click="setFilter('difficulty', d)"
        >{{ d }}</button>
        <span class="sep" />
        <button class="chip" :class="{ on: filters.is_free === 'true' }" type="button" @click="setFilter('is_free', filters.is_free === 'true' ? '' : 'true')">只看免费</button>
        <button class="chip" :class="{ on: filters.is_free === 'false' }" type="button" @click="setFilter('is_free', filters.is_free === 'false' ? '' : 'false')">只看付费</button>
        <div class="seg sort" role="group" aria-label="排序">
          <button v-for="s in sorts" :key="s.value" type="button" :class="{ on: sort === s.value }" @click="setSort(s.value)">{{ s.label }}</button>
        </div>
      </div>
    </div>

    <div class="body">
      <div v-loading="loading" class="list-area">
        <template v-if="items.length">
          <div class="grid">
            <CourseCard v-for="c in items" :key="c.id" :course="c" @open="openCourse" />
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
        <el-empty v-else-if="!loading" description="没有符合条件的课程，换个筛选试试" />
      </div>

      <aside class="aside">
        <section class="panel">
          <h2 class="panel-title">继续学习 <small v-if="learning.length">{{ learning.length }} 门在学</small></h2>
          <div v-if="learning.length" class="prog">
            <router-link v-for="e in learning" :key="e.course.id" :to="`/learn/${e.course.id}`" class="prog-row">
              <b>{{ e.course.title }}</b>
              <small>{{ e.progress }}% · {{ e.course.tech_domain || categoryLabel(e.course.category) }}</small>
              <div class="bar"><i :style="{ width: e.progress + '%' }" /></div>
            </router-link>
          </div>
          <p v-else class="empty-note">还没有在学的课程。报名后会显示在这里，点一下就能接着学。</p>
        </section>

        <section class="panel">
          <h2 class="panel-title">AI 学习助手 <small>多轮对话</small></h2>
          <div class="quick">
            <button v-for="q in quickQuestions" :key="q" type="button" class="quick-q" @click="askAi(q)">
              <span>{{ q }}</span>
              <AppIcon name="arrow-right" :size="14" />
            </button>
          </div>
          <form class="ask" @submit.prevent="askAi(askText)">
            <input v-model="askText" placeholder="问一个学习上的问题" aria-label="向 AI 提问" />
            <button class="btn" type="submit">提问</button>
          </form>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCourses, getCourseFilters, getMyEnrollments } from '../../api/course'
import { normalizePage, categoryLabel } from '../../utils'
import CourseCard from '../../components/CourseCard.vue'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()

const VALID = ['theory', 'practice', 'certification']
const category = computed(() => route.params.category)

const title = computed(() => categoryLabel(category.value))
const subtitle = computed(() => {
  const map = {
    theory: '机器学习、大数据、云计算、前后端和物联网的基础知识，从入门讲到进阶。',
    practice: '跟着项目一步步动手做，每门课都有可以跑起来的练习。',
    certification: '对照华为 ICT 等认证考纲安排内容，适合备考时系统过一遍。'
  }
  return map[category.value] || '按方向、难度和价格筛选课程。'
})

const sorts = [
  { value: 'newest', label: '最新' },
  { value: 'students', label: '最多人学' },
  { value: 'rating', label: '评分' }
]

const quickQuestions = ['梯度下降的学习率怎么选？', '帮我排一个四周的 Python 学习计划', 'Vue 组件之间怎么传数据？']

const meta = reactive({ tech_domains: [], difficulties: [], categories: [] })
const filters = reactive({ tech_domain: '', difficulty: '', is_free: '' })
const sort = ref('newest')
const keyword = ref('')
const page = ref(1)
const size = 12
const total = ref(0)
const items = ref([])
const loading = ref(false)
const learning = ref([])
const askText = ref('')

async function fetchList() {
  loading.value = true
  try {
    const params = {
      category: category.value,
      sort: sort.value,
      page: page.value,
      size
    }
    if (filters.tech_domain) params.tech_domain = filters.tech_domain
    if (filters.difficulty) params.difficulty = filters.difficulty
    if (filters.is_free !== '') params.is_free = filters.is_free
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const data = await getCourses(params)
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

function setFilter(key, val) {
  filters[key] = val
  page.value = 1
  fetchList()
}

function setSort(v) {
  sort.value = v
  page.value = 1
  fetchList()
}

function onSearch() {
  page.value = 1
  fetchList()
}

function clearSearch() {
  keyword.value = ''
  onSearch()
}

function openCourse(c) {
  router.push(`/course/${c.id}`)
}

function askAi(q) {
  const text = (q || '').trim()
  if (!text) return
  router.push({ path: '/ai', query: { tab: 'chat', q: text } })
}

async function loadLearning() {
  try {
    const list = (await getMyEnrollments()) || []
    learning.value = list
      .map((e) => ({ course: e.course || e, progress: Math.round(e.progress ?? 0) }))
      .filter((e) => e.course?.id && e.progress < 100)
      .sort((a, b) => b.progress - a.progress)
      .slice(0, 3)
  } catch {
    learning.value = []
  }
}

onMounted(async () => {
  loadLearning()
  try {
    const m = await getCourseFilters()
    meta.tech_domains = m?.tech_domains || []
    meta.difficulties = m?.difficulties || []
    meta.categories = m?.categories || []
  } catch {
    /* 元数据失败不阻塞列表 */
  }
})

watch(
  () => route.params.category,
  (c) => {
    if (!c) return
    if (!VALID.includes(c)) {
      router.replace('/courses/theory')
      return
    }
    page.value = 1
    fetchList()
  },
  { immediate: true }
)
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

.sort {
  margin-left: auto;
}

.body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 28px;
  align-items: start;
}

.list-area {
  min-height: 320px;
  min-width: 0;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.aside {
  position: sticky;
  top: 88px;
}

.prog {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prog-row {
  display: block;
  padding: 2px 0;
  color: var(--ink);
}

.prog-row b {
  display: block;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prog-row:hover b {
  color: var(--accent);
}

.prog-row small {
  color: var(--muted);
  font: 12px var(--mono);
}

.prog-row .bar {
  margin-top: 8px;
}

.empty-note {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.quick {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-q {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 8px 12px;
  text-align: left;
  border: 1px solid transparent;
  border-radius: var(--r);
  background: var(--surface);
  color: var(--ink-2);
  font-size: 13.5px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, transform 0.1s;
}

.quick-q:hover {
  border-color: var(--line-strong);
  color: var(--ink);
}

.quick-q:active {
  transform: scale(0.97);
}

.quick-q svg {
  color: var(--accent);
}

.ask {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.ask input {
  flex: 1;
  min-width: 0;
  height: 40px;
  border-radius: var(--r);
  border: 1px solid var(--line);
  background: var(--bg);
  padding: 0 12px;
  font: inherit;
  font-size: 14px;
  color: var(--ink);
  outline: 0;
}

.ask input:focus {
  border-color: var(--accent);
}

.btn {
  height: 40px;
  padding: 0 16px;
  border-radius: var(--r);
  border: 0;
  background: var(--accent);
  color: var(--accent-ink);
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.1s, filter 0.15s;
}

.btn:hover {
  filter: brightness(1.08);
}

.btn:active {
  transform: scale(0.97);
}

@media (max-width: 1100px) {
  .body {
    grid-template-columns: 1fr;
  }

  .grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .aside {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .aside .panel + .panel {
    margin-top: 0;
  }
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .aside {
    grid-template-columns: 1fr;
  }

  .sort {
    margin-left: 0;
    width: 100%;
  }

  .sort button {
    flex: 1;
  }

  .sep {
    display: none;
  }

  .ask input,
  .btn,
  .quick-q {
    min-height: 44px;
  }
}
</style>
