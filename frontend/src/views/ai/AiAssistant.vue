<template>
  <div class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">AI 学习助手</p>
        <h1 class="page-title">有问题，先问这里</h1>
        <p class="lead">答疑可以关联你在学的课程；学习路径会存进个人中心；作业批改支持 Python、Java、JavaScript 和 C/C++。</p>
      </div>
    </div>

    <div class="seg tabs-seg" role="tablist" aria-label="助手功能">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        role="tab"
        :aria-selected="tab === t.key"
        :class="{ on: tab === t.key }"
        @click="tab = t.key"
      >
        <AppIcon :name="t.icon" :size="16" />{{ t.label }}
      </button>
    </div>

    <!-- ============ 智能答疑 ============ -->
    <section v-show="tab === 'chat'" class="chat-wrap">
      <aside class="panel session-panel">
        <el-button type="primary" class="new-btn" @click="newSession">
          <AppIcon name="plus" :size="16" />新建会话
        </el-button>
        <div class="session-list">
          <div
            v-for="s in sessions"
            :key="s.id"
            class="session-item clickable"
            :class="{ active: s.id === currentSessionId }"
            @click="openSession(s.id)"
          >
            <div class="session-title">{{ s.title || '未命名会话' }}</div>
            <div class="session-meta">
              <span class="mono">{{ s.message_count ?? 0 }} 条 · {{ fmtDay(s.updated_at) }}</span>
              <button class="icon-btn sm" type="button" aria-label="删除会话" @click.stop="onDeleteSession(s.id)">
                <AppIcon name="trash" :size="15" />
              </button>
            </div>
          </div>
          <p v-if="!sessions.length" class="text-sub empty-line">还没有会话</p>
        </div>
      </aside>

      <div class="panel chat-panel">
        <div class="chat-toolbar">
          <el-select v-model="chatCourseId" placeholder="关联课程（可选）" clearable style="width: 240px">
            <el-option v-for="c in myCourses" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
          <span class="text-sub mono">
            <template v-if="usage && !usage.unlimited">今日剩余 {{ usage.remaining }} / {{ usage.limit }} 次 · </template>{{ currentSessionId ? `会话 #${currentSessionId}` : '新会话' }}
          </span>
        </div>

        <div ref="msgBox" class="msg-list" v-loading="sessionLoading">
          <div v-if="!messages.length" class="chat-empty">
            <AppIcon name="chat" :size="32" class="empty-icon" />
            <p class="text-sub">直接问课程里的概念、报错或者学习安排。</p>
            <div class="quick">
              <button v-for="q in quickQuestions" :key="q" type="button" class="quick-q" @click="input = q">{{ q }}</button>
            </div>
          </div>
          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="msg-bubble pre-wrap">{{ m.content }}</div>
          </div>
          <div v-if="sending" class="msg assistant">
            <div class="msg-bubble thinking"><span></span><span></span><span></span></div>
          </div>
        </div>

        <form class="chat-input" @submit.prevent="onSend">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入问题，Enter 发送，Shift+Enter 换行"
            aria-label="输入问题"
            @keydown.enter.exact.prevent="onSend"
          />
          <el-button type="primary" native-type="submit" :loading="sending">
            <AppIcon name="send" :size="16" />发送
          </el-button>
        </form>
      </div>
    </section>

    <!-- ============ 学习路径 ============ -->
    <section v-show="tab === 'path'">
      <form class="panel path-form" @submit.prevent="onGenPath">
        <el-input v-model="pathGoal" placeholder="想去的方向，比如：后端开发、数据分析、AI 工程师" class="goal-input" aria-label="学习目标" />
        <div class="hours">
          <el-input-number v-model="pathHours" :min="1" :max="60" />
          <span class="text-sub">小时 / 周</span>
        </div>
        <el-button type="primary" native-type="submit" :loading="pathLoading">
          <AppIcon name="route" :size="16" />生成学习路径
        </el-button>
      </form>

      <div v-loading="pathLoading" class="mt-16">
        <el-empty v-if="!plan && !pathLoading" description="填好方向和每周时间，按阶段排一份计划" />
        <template v-if="plan">
          <div class="plan-head">
            <div>
              <p class="eyebrow">共 {{ (plan.stages || []).length }} 个阶段</p>
              <h2 class="section-title plan-title">{{ plan.title || pathGoal + ' 学习路径' }}</h2>
            </div>
            <el-button @click="$router.push({ path: '/me', query: { tab: 'plans' } })">
              在个人中心查看<AppIcon name="arrow-right" :size="16" />
            </el-button>
          </div>
          <p v-if="plan.advice" class="pre-wrap text-sub plan-advice">{{ plan.advice }}</p>
          <ol class="stages">
            <li v-for="(st, i) in plan.stages || []" :key="i" class="panel stage">
              <div class="stage-head">
                <span class="stage-no mono">{{ String(i + 1).padStart(2, '0') }}</span>
                <b>{{ st.name }}</b>
                <span class="text-sub mono">{{ st.duration }}</span>
              </div>
              <div class="stage-topics">
                <span v-for="t in st.topics || []" :key="t" class="tag">{{ t }}</span>
              </div>
              <div v-if="(st.courses || []).length" class="stage-courses">
                <button v-for="(c, j) in st.courses" :key="j" type="button" class="stage-course" @click="goCourse(c)">
                  <AppIcon name="book" :size="16" />
                  <span>{{ courseName(c) }}</span>
                  <AppIcon name="chevron-right" :size="16" class="go" />
                </button>
              </div>
            </li>
          </ol>
        </template>
      </div>
    </section>

    <!-- ============ 作业批改 ============ -->
    <section v-show="tab === 'grade'" class="grade-grid">
      <el-form label-position="top" class="panel" @submit.prevent>
        <el-form-item label="题目">
          <el-input v-model="gradeForm.question" type="textarea" :rows="3" placeholder="比如：实现一个函数，判断字符串是不是回文" />
        </el-form-item>
        <el-form-item label="语言">
          <el-select v-model="gradeForm.language" style="width: 180px">
            <el-option label="Python" value="python" />
            <el-option label="Java" value="java" />
            <el-option label="JavaScript" value="javascript" />
            <el-option label="C/C++" value="cpp" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="代码">
          <el-input v-model="gradeForm.code" class="code-input" type="textarea" :rows="12" placeholder="把代码贴在这里" />
        </el-form-item>
        <el-button type="primary" :loading="gradeLoading" @click="onGrade">
          <AppIcon name="check-circle" :size="16" />开始批改
        </el-button>
      </el-form>

      <div class="panel grade-result" v-loading="gradeLoading">
        <el-empty v-if="!gradeResult && !gradeLoading" description="提交后这里会显示分数、问题和改进后的代码" />
        <template v-if="gradeResult">
          <div class="score-row">
            <div class="score-big mono" :class="scoreLevel(gradeResult.score)">{{ gradeResult.score ?? 0 }}</div>
            <div>
              <div class="text-sub">得分 / 100</div>
              <div class="bar score-bar"><i :style="{ width: (gradeResult.score ?? 0) + '%' }"></i></div>
            </div>
          </div>
          <div v-if="gradeResult.correct_points?.length" class="result-block">
            <div class="block-title ok"><AppIcon name="check" :size="16" />做得对的地方</div>
            <ul><li v-for="(p, i) in gradeResult.correct_points" :key="i">{{ p }}</li></ul>
          </div>
          <div v-if="gradeResult.issues?.length" class="result-block">
            <div class="block-title warn"><AppIcon name="info" :size="16" />问题</div>
            <ul><li v-for="(p, i) in gradeResult.issues" :key="i">{{ p }}</li></ul>
          </div>
          <div v-if="gradeResult.suggestions?.length" class="result-block">
            <div class="block-title"><AppIcon name="arrow-right" :size="16" />建议</div>
            <ul><li v-for="(p, i) in gradeResult.suggestions" :key="i">{{ p }}</li></ul>
          </div>
          <div v-if="gradeResult.improved_code" class="result-block">
            <div class="block-title flex-between">
              <span>改进后的代码</span>
              <el-button size="small" text type="primary" @click="copyCode">复制</el-button>
            </div>
            <div class="code-block">{{ gradeResult.improved_code }}</div>
          </div>
        </template>
      </div>
    </section>

    <!-- ============ 学习报告 ============ -->
    <section v-show="tab === 'report'">
      <div class="report-bar">
        <div class="seg">
          <button type="button" :class="{ on: reportPeriod === 'week' }" @click="setPeriod('week')">本周</button>
          <button type="button" :class="{ on: reportPeriod === 'month' }" @click="setPeriod('month')">本月</button>
        </div>
        <button class="icon-btn" type="button" aria-label="刷新报告" @click="fetchReport">
          <AppIcon name="refresh" :size="18" />
        </button>
      </div>

      <div v-loading="reportLoading">
        <template v-if="report">
          <div class="stat-cards">
            <div class="panel stat"><span class="text-sub">学习时长</span><b class="mono">{{ fmtMinutes(report.total_minutes) }}</b></div>
            <div class="panel stat"><span class="text-sub">完成课时</span><b class="mono">{{ report.completed_lessons ?? 0 }}</b></div>
            <div class="panel stat"><span class="text-sub">在学课程</span><b class="mono">{{ report.courses_progress?.length ?? 0 }}</b></div>
          </div>
          <p v-if="report.summary" class="panel pre-wrap summary">{{ report.summary }}</p>
          <div v-show="hasProgressData" class="panel">
            <h3 class="panel-title">各课程进度</h3>
            <div ref="chartRef" class="report-chart"></div>
          </div>
          <div class="report-cols">
            <div class="panel">
              <div class="block-title ok"><AppIcon name="check" :size="16" />掌握得不错</div>
              <p v-if="!report.strengths?.length" class="text-sub">暂无</p>
              <ul v-else><li v-for="(s, i) in report.strengths" :key="i">{{ s }}</li></ul>
            </div>
            <div class="panel">
              <div class="block-title warn"><AppIcon name="info" :size="16" />还需要补</div>
              <p v-if="!report.weaknesses?.length" class="text-sub">暂无</p>
              <ul v-else><li v-for="(s, i) in report.weaknesses" :key="i">{{ s }}</li></ul>
            </div>
            <div class="panel">
              <div class="block-title"><AppIcon name="arrow-right" :size="16" />下一步</div>
              <p v-if="!report.suggestions?.length" class="text-sub">暂无</p>
              <ul v-else><li v-for="(s, i) in report.suggestions" :key="i">{{ s }}</li></ul>
            </div>
          </div>
        </template>
        <el-empty v-else-if="!reportLoading" description="这段时间还没有学习记录" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import echarts from '../../lib/echarts'
import AppIcon from '../../components/icons/AppIcon.vue'
import {
  getChatSessions, getChatSession, deleteChatSession,
  getLearningPath, gradeCode, getReport, getAiUsage
} from '../../api/ai'
import { postStream } from '../../api/stream'
import { getMyEnrollments } from '../../api/course'
import { fmtMinutes, fmtDay } from '../../utils'

const route = useRoute()
const router = useRouter()
const TAB_KEYS = ['chat', 'path', 'grade', 'report']
const tabs = [
  { key: 'chat', label: '智能答疑', icon: 'chat' },
  { key: 'path', label: '学习路径', icon: 'route' },
  { key: 'grade', label: '作业批改', icon: 'code' },
  { key: 'report', label: '学习报告', icon: 'chart' }
]
const tab = ref('chat')

/* ---------------- 智能答疑 ---------------- */
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const input = ref('')
const sending = ref(false)
const sessionLoading = ref(false)
const chatCourseId = ref(null)
const myCourses = ref([])
const msgBox = ref()

const quickQuestions = ['这门课的重点是什么？', '闭包是什么，什么时候用？', '帮我排一个四周的复习计划']

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

async function loadSessions() {
  try {
    sessions.value = (await getChatSessions()) || []
  } catch {
    sessions.value = []
  }
}

function newSession() {
  currentSessionId.value = null
  messages.value = []
}

async function openSession(id) {
  sessionLoading.value = true
  try {
    const s = await getChatSession(id)
    currentSessionId.value = s.id
    messages.value = s.messages || []
    scrollBottom()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    sessionLoading.value = false
  }
}

async function onDeleteSession(id) {
  try {
    await ElMessageBox.confirm('删除后聊天记录不能恢复。', '删除会话', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  try {
    await deleteChatSession(id)
    if (currentSessionId.value === id) newSession()
    loadSessions()
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onSend(preset) {
  const text = (typeof preset === 'string' ? preset : input.value).trim()
  if (!text || sending.value) return
  messages.value.push({ role: 'user', content: text })
  if (typeof preset !== 'string') input.value = ''
  sending.value = true
  scrollBottom()
  const reply = reactive({ role: 'assistant', content: '' })
  try {
    const payload = { message: text }
    if (currentSessionId.value) payload.session_id = currentSessionId.value
    if (chatCourseId.value) payload.course_id = chatCourseId.value
    let started = false
    await postStream('/ai/chat/stream', payload, (event, data) => {
      if (event === 'meta' && data.session_id) currentSessionId.value = data.session_id
      if (event === 'delta') {
        if (!started) {
          started = true
          sending.value = false
          messages.value.push(reply)
        }
        reply.content += data.text || ''
        scrollBottom()
      }
    })
    if (!started) messages.value.push({ role: 'assistant', content: '（没有拿到回复）' })
    loadSessions()
    loadUsage()
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `出错了：${e.message}` })
  } finally {
    sending.value = false
    scrollBottom()
  }
}

const usage = ref(null)
async function loadUsage() {
  try {
    usage.value = await getAiUsage()
  } catch {
    usage.value = null
  }
}

/* ---------------- 学习路径 ---------------- */
const pathGoal = ref('')
const pathHours = ref(10)
const pathLoading = ref(false)
const plan = ref(null)

async function onGenPath() {
  if (!pathGoal.value.trim()) {
    ElMessage.warning('先写一个学习方向')
    return
  }
  pathLoading.value = true
  plan.value = null
  try {
    const res = await getLearningPath({ goal: pathGoal.value.trim(), hours_per_week: pathHours.value })
    plan.value = res?.plan || res
    ElMessage.success('已保存到个人中心的「学习路径」')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    pathLoading.value = false
  }
}

function courseName(c) {
  if (typeof c === 'string') return c
  return c?.title || c?.name || '推荐课程'
}

function goCourse(c) {
  const id = typeof c === 'object' ? c.id : null
  if (id) router.push(`/course/${id}`)
  else ElMessage.info('这门课暂时没有站内页面')
}

/* ---------------- 作业批改 ---------------- */
const gradeForm = reactive({ question: '', code: '', language: 'python' })
const gradeLoading = ref(false)
const gradeResult = ref(null)

const scoreLevel = (s) => (s >= 80 ? 'good' : s >= 60 ? 'mid' : 'low')

async function onGrade() {
  if (!gradeForm.question.trim() || !gradeForm.code.trim()) {
    ElMessage.warning('题目和代码都要填')
    return
  }
  gradeLoading.value = true
  gradeResult.value = null
  try {
    gradeResult.value = await gradeCode({
      question: gradeForm.question.trim(),
      code: gradeForm.code,
      language: gradeForm.language
    })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    gradeLoading.value = false
  }
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(gradeResult.value.improved_code)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选中复制')
  }
}

/* ---------------- 学习报告 ---------------- */
const reportPeriod = ref('week')
const reportLoading = ref(false)
const report = ref(null)
const chartRef = ref()
let chart = null

const hasProgressData = computed(() => (report.value?.courses_progress || []).length > 0)

function setPeriod(p) {
  reportPeriod.value = p
  fetchReport()
}

async function fetchReport() {
  reportLoading.value = true
  try {
    report.value = await getReport(reportPeriod.value)
    await nextTick()
    renderChart()
  } catch (e) {
    report.value = null
    ElMessage.error(e.message)
  } finally {
    reportLoading.value = false
  }
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function renderChart() {
  if (!chartRef.value) return
  const list = report.value?.courses_progress || []
  if (!list.length) return
  const names = list.map((c) => c.title || c.course_title || c.name || `课程${c.course_id || c.id || ''}`)
  const values = list.map((c) => c.progress ?? c.percent ?? 0)
  const accent = cssVar('--accent') || '#dafa9c'
  const muted = cssVar('--muted') || '#9a9a9a'
  const line = cssVar('--line') || '#2a2a2a'
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    backgroundColor: 'transparent',
    textStyle: { color: muted, fontFamily: 'Geist Variable, PingFang SC, Microsoft YaHei, sans-serif' },
    grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: line } }, axisLabel: { color: muted } },
    yAxis: { type: 'category', data: names, axisLine: { lineStyle: { color: line } }, axisLabel: { color: muted, width: 140, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      data: values,
      barWidth: 14,
      itemStyle: { color: accent, borderRadius: 0 },
      label: { show: true, position: 'right', formatter: '{c}%', color: muted }
    }]
  }, true)
  chart.resize()
}

function onResize() {
  chart?.resize()
}

watch(tab, (t) => {
  if (t === 'report') {
    if (!report.value) fetchReport()
    else nextTick(() => chart?.resize())
  }
})

function takeQuestion() {
  const q = typeof route.query.q === 'string' ? route.query.q.trim() : ''
  if (q) router.replace({ path: '/ai', query: { tab: 'chat' } })
  return q
}

function askFromQuery(q) {
  if (!q) return
  tab.value = 'chat'
  newSession()
  onSend(q)
}

watch(() => route.query.tab, (t) => {
  if (TAB_KEYS.includes(t)) tab.value = t
})

watch(() => route.query.q, (q) => {
  if (typeof q === 'string' && q.trim()) askFromQuery(takeQuestion())
})

onMounted(async () => {
  window.addEventListener('resize', onResize)
  if (TAB_KEYS.includes(route.query.tab)) tab.value = route.query.tab
  const pendingQ = takeQuestion()
  loadSessions()
  loadUsage()
  try {
    const list = (await getMyEnrollments()) || []
    myCourses.value = list.map((e) => e.course || e).filter((c) => c?.id)
    const q = Number(route.query.course_id)
    if (q && myCourses.value.some((c) => c.id === q)) chatCourseId.value = q
  } catch {
    /* 课程关联可选 */
  }
  askFromQuery(pendingQ)
  if (tab.value === 'report') fetchReport()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.tabs-seg {
  margin-bottom: 20px;
}

.tabs-seg button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* ---- 答疑 ---- */
.chat-wrap {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
  height: 600px;
}

.chat-wrap .panel + .panel {
  margin-top: 0;
}

.session-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px;
}

.new-btn {
  width: 100%;
  margin-bottom: 12px;
  gap: 6px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  margin: 0 -6px;
}

.session-item {
  padding: 10px 10px;
  border-radius: var(--r);
  border-left: 2px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}

.session-item:hover {
  background: var(--surface);
}

.session-item.active {
  background: var(--tint);
  border-left-color: var(--accent);
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--muted);
  font-size: 12px;
}

.icon-btn.sm {
  width: 28px;
  height: 28px;
}

.empty-line {
  padding: 8px 10px;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}

.chat-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-empty {
  margin: auto;
  text-align: center;
  max-width: 420px;
}

.empty-icon {
  color: var(--accent);
}

.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.quick-q {
  min-height: 36px;
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: var(--r);
  background: var(--card);
  color: var(--ink);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.1s;
}

.quick-q:hover {
  border-color: var(--accent);
}

.quick-q:active {
  transform: scale(0.97);
}

.msg {
  display: flex;
}

.msg.user {
  justify-content: flex-end;
}

.msg-bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: var(--r);
  line-height: 1.65;
  font-size: 14px;
}

.msg.user .msg-bubble {
  background: var(--ink);
  color: var(--bg);
}

.msg.assistant .msg-bubble {
  background: var(--surface);
  border: 1px solid var(--line);
}

.thinking {
  display: flex;
  gap: 5px;
  align-items: center;
  height: 40px;
}

.thinking span {
  width: 6px;
  height: 6px;
  background: var(--accent);
  animation: blink 1.2s infinite ease-in-out;
}

.thinking span:nth-child(2) { animation-delay: 0.2s; }
.thinking span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0.25; }
  40% { opacity: 1; }
}

.chat-input {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px 16px;
  border-top: 1px solid var(--line);
}

.chat-input .el-button {
  height: 54px;
  gap: 6px;
}

/* ---- 学习路径 ---- */
.path-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.goal-input {
  flex: 1;
  min-width: 260px;
}

.hours {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-form .el-button {
  gap: 6px;
}

.plan-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.plan-title {
  font-size: 22px;
  margin: 0;
}

.plan-head .el-button {
  gap: 6px;
}

.plan-advice {
  margin: 12px 0 0;
}

.stages {
  list-style: none;
  padding: 0;
  margin: 20px 0 0;
  display: grid;
  gap: 12px;
}

.stage-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.stage-no {
  color: var(--accent);
  font-size: 13px;
}

.stage-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.stage-courses {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.stage-course {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: var(--r);
  background: var(--bg);
  color: var(--ink);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.18s;
}

.stage-course:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.stage-course .go {
  color: var(--muted);
}

/* ---- 作业批改 ---- */
.grade-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.grade-grid .el-button {
  gap: 6px;
}

.grade-result {
  min-height: 420px;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
}

.score-row > div:last-child {
  flex: 1;
}

.score-big {
  font-size: 56px;
  line-height: 1;
  font-weight: 500;
  letter-spacing: -0.04em;
}

.score-big.good { color: var(--accent); }
.score-big.mid { color: #f2c46d; }
.score-big.low { color: #f28b82; }

.score-bar {
  margin-top: 10px;
}

.result-block {
  margin-top: 16px;
}

.block-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
}

.block-title.ok { color: var(--accent); }
.block-title.warn { color: #f2c46d; }

.result-block ul,
.report-cols ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
  font-size: 14px;
}

/* ---- 学习报告 ---- */
.report-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat b {
  font-size: 30px;
  font-weight: 500;
  letter-spacing: -0.03em;
}

.summary {
  margin: 0 0 16px;
  line-height: 1.8;
}

.report-chart {
  height: 260px;
}

.report-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.report-cols .panel + .panel {
  margin-top: 0;
}

@media (max-width: 960px) {
  .chat-wrap {
    grid-template-columns: 1fr;
    height: auto;
  }

  .session-panel {
    max-height: 220px;
  }

  .chat-panel {
    height: 70vh;
    min-height: 460px;
  }

  .grade-grid,
  .report-cols {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .tabs-seg {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-cards {
    grid-template-columns: 1fr;
  }

  .msg-bubble {
    max-width: 90%;
  }

  .chat-input {
    flex-direction: column;
    align-items: stretch;
  }

  .chat-input .el-button {
    height: 44px;
  }

  .path-form .el-button {
    width: 100%;
  }
}
</style>
