<template>
  <div class="page">
    <div class="page-head profile-head">
      <div class="who">
        <UserAvatar :user="store.user" :size="72" />
        <div>
          <p class="eyebrow">{{ USER_ROLES[store.user?.role] || '学生' }}</p>
          <h1 class="page-title">{{ store.displayName }}</h1>
          <p class="lead mono">{{ store.user?.username }} · {{ store.user?.email }}<template v-if="store.user?.major"> · {{ store.user.major }}</template></p>
        </div>
      </div>
    </div>

    <el-tabs v-model="tab" class="profile-tabs" @tab-change="onTabChange">
      <!-- 基本资料 -->
      <el-tab-pane label="基本资料" name="profile">
        <el-form :model="profileForm" label-position="top" class="panel form-narrow" @submit.prevent>
          <el-form-item label="昵称">
            <el-input v-model="profileForm.nickname" maxlength="32" placeholder="别人看到的名字" />
          </el-form-item>
          <el-form-item label="专业">
            <el-input v-model="profileForm.major" maxlength="64" placeholder="比如：计算机科学与技术" />
          </el-form-item>
          <el-form-item label="头像">
            <div class="avatar-picker" role="radiogroup" aria-label="内置头像">
              <button
                v-for="a in BUILTIN_AVATARS"
                :key="a.key"
                type="button"
                role="radio"
                :aria-checked="profileForm.avatar === a.key"
                :aria-label="`图案 ${a.index}`"
                class="avatar-opt"
                :class="{ active: profileForm.avatar === a.key }"
                @click="profileForm.avatar = a.key"
              >
                <AvatarPattern :index="a.index" />
              </button>
              <button
                type="button"
                class="avatar-opt none"
                :class="{ active: !profileForm.avatar }"
                aria-label="不使用头像"
                @click="profileForm.avatar = ''"
              >
                <AppIcon name="user" :size="22" />
              </button>
            </div>
            <el-input v-model="profileForm.avatar" placeholder="也可以粘贴图片地址（https://…）" class="mt-12" />
          </el-form-item>
          <el-button type="primary" :loading="savingProfile" @click="onSaveProfile">保存</el-button>
        </el-form>
      </el-tab-pane>

      <!-- 我的学习 -->
      <el-tab-pane label="我的学习" name="learning">
        <el-empty v-if="!enrollments.length" description="还没有报名课程">
          <el-button type="primary" @click="$router.push('/courses/theory')">去选课</el-button>
        </el-empty>
        <div v-else class="rows">
          <div v-for="e in enrollments" :key="e.id || e._course.id" class="panel learn-item">
            <CourseCover :course="e._course" class="learn-cover" />
            <div class="learn-body">
              <b>{{ e._course.title }}</b>
              <span class="text-sub">{{ e._course.lecturer?.name || '讲师团队' }}</span>
              <div class="prog">
                <div class="bar"><i :style="{ width: (e.progress ?? 0) + '%' }"></i></div>
                <span class="mono text-sub">{{ e.progress ?? 0 }}%</span>
              </div>
            </div>
            <el-button type="primary" @click="$router.push(`/learn/${e._course.id}`)">
              {{ (e.progress ?? 0) > 0 ? '继续学习' : '开始学习' }}
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 学习路径 -->
      <el-tab-pane label="学习路径" name="plans">
        <el-empty v-if="!plans.length" description="还没有生成过学习路径">
          <el-button type="primary" @click="$router.push({ path: '/ai', query: { tab: 'path' } })">去生成</el-button>
        </el-empty>
        <div v-else class="rows">
          <details v-for="p in plans" :key="p.id" class="panel plan-item">
            <summary>
              <div class="plan-sum">
                <b>{{ p.plan?.title || p.goal }}</b>
                <span class="text-sub mono">
                  {{ (p.plan?.stages || []).length }} 个阶段 · 每周 {{ p.hours_per_week || '-' }} 小时 · 生成于 {{ fmtDay(p.created_at) }}
                </span>
              </div>
              <span class="tag" :class="isDue(p) ? 'tag-warn' : 'tag-accent'">
                {{ p.due_date ? (isDue(p) ? '已到期 ' : '计划完成 ') + fmtDay(p.due_date) : '未设期限' }}
              </span>
              <button class="icon-btn" type="button" aria-label="删除学习路径" @click.prevent="onDeletePlan(p)">
                <AppIcon name="trash" :size="16" />
              </button>
            </summary>
            <ol class="stages">
              <li v-for="(st, i) in p.plan?.stages || []" :key="i">
                <span class="mono no">{{ String(i + 1).padStart(2, '0') }}</span>
                <div>
                  <b>{{ st.name }}</b> <span class="text-sub mono">{{ st.duration }}</span>
                  <div class="topics"><span v-for="t in st.topics || []" :key="t" class="tag">{{ t }}</span></div>
                </div>
              </li>
            </ol>
            <p v-if="p.plan?.advice" class="text-sub pre-wrap">{{ p.plan.advice }}</p>
          </details>
        </div>
      </el-tab-pane>

      <!-- 我的收藏 -->
      <el-tab-pane label="我的收藏" name="favorites">
        <div class="seg mb-16">
          <button type="button" :class="{ on: favTab === 'courses' }" @click="favTab = 'courses'">课程 {{ favorites.courses.length }}</button>
          <button type="button" :class="{ on: favTab === 'jobs' }" @click="favTab = 'jobs'">职位 {{ favorites.jobs.length }}</button>
        </div>
        <template v-if="favTab === 'courses'">
          <el-empty v-if="!favorites.courses.length" description="还没有收藏课程" />
          <div v-else class="card-grid">
            <CourseCard v-for="c in favorites.courses" :key="c.id" :course="c" @open="(x) => $router.push(`/course/${x.id}`)" />
          </div>
        </template>
        <template v-else>
          <el-empty v-if="!favorites.jobs.length" description="还没有收藏职位" />
          <div v-else class="job-grid">
            <JobCard v-for="j in favorites.jobs" :key="j.id" :job="j" @open="(x) => $router.push(`/job/${x.id}`)" />
          </div>
        </template>
      </el-tab-pane>

      <!-- 我的订单 -->
      <el-tab-pane label="我的订单" name="orders">
        <el-empty v-if="!orders.length" description="还没有订单" />
        <div v-else class="rows">
          <div v-for="o in orders" :key="o.id" class="panel row-item">
            <div class="row-main">
              <b>{{ o.course?.title || `订单 ${o.order_no || o.id}` }}</b>
              <span class="text-sub mono">{{ o.order_no || o.id }} · {{ fmtDate(o.created_at) }}<template v-if="o.paid_at"> · 支付于 {{ fmtDate(o.paid_at) }}</template></span>
            </div>
            <span class="price">¥{{ o.amount }}</span>
            <span class="tag" :class="statusClass(o.status)">{{ ORDER_STATUS[o.status]?.label || o.status }}</span>
            <div v-if="o.status === 'pending'" class="row-ops">
              <el-button type="primary" size="small" :loading="payingId === o.id" @click="onPay(o)">支付</el-button>
              <el-button size="small" @click="onCancelOrder(o)">取消</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 我的申请 -->
      <el-tab-pane label="我的申请" name="applications">
        <el-empty v-if="!applications.length" description="还没有投递职位" />
        <div v-else class="rows">
          <div v-for="a in applications" :key="a.id" class="panel row-item hover-card clickable" @click="a.job?.id && $router.push(`/job/${a.job.id}`)">
            <div class="row-main">
              <b>{{ a.job?.title || '职位' }}</b>
              <span class="text-sub">{{ a.job?.company }} · {{ a.job?.city }}<template v-if="a.job?.salary"> · {{ a.job.salary }}</template></span>
              <span v-if="a.message" class="text-sub">附言：{{ a.message }}</span>
            </div>
            <span class="text-sub mono">{{ fmtDay(a.created_at) }}</span>
            <span class="tag" :class="statusClass(a.status)">{{ APP_STATUS[a.status]?.label || a.status }}</span>
          </div>
        </div>
      </el-tab-pane>

      <!-- AI 面试记录 -->
      <el-tab-pane label="AI 面试记录" name="interviews">
        <el-empty v-if="!interviews.length" description="还没有做过 AI 模拟面试">
          <el-button type="primary" @click="$router.push('/jobs')">去看职位</el-button>
        </el-empty>
        <div v-else class="rows">
          <div v-for="iv in interviews" :key="iv.id" class="panel row-item hover-card clickable" @click="$router.push(`/interview/${iv.id}`)">
            <div class="row-main">
              <b>{{ iv.job?.title || '模拟面试' }}</b>
              <span class="text-sub">{{ iv.job?.company }} · {{ (iv.questions || []).length }} 道题 · {{ fmtDate(iv.created_at) }}</span>
            </div>
            <span v-if="iv.status === 'done'" class="score mono">{{ iv.score }}<small> 分</small></span>
            <span class="tag" :class="iv.status === 'done' ? 'tag-accent' : 'tag-line'">{{ iv.status === 'done' ? '已完成' : '未作答' }}</span>
            <AppIcon name="chevron-right" :size="18" class="text-sub" />
          </div>
        </div>
      </el-tab-pane>

      <!-- 修改密码 -->
      <el-tab-pane label="修改密码" name="password">
        <el-form ref="pwdRef" :model="pwdForm" :rules="pwdRules" label-position="top" class="panel form-narrow" @submit.prevent>
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="pwdForm.old_password" type="password" show-password autocomplete="current-password" />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="pwdForm.new_password" type="password" show-password autocomplete="new-password" />
          </el-form-item>
          <el-form-item label="再输一次" prop="confirm">
            <el-input v-model="pwdForm.confirm" type="password" show-password autocomplete="new-password" />
          </el-form-item>
          <el-button type="primary" :loading="savingPwd" @click="onSavePwd">修改密码</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { updatePassword } from '../../api/auth'
import { getMyEnrollments, getMyFavorites } from '../../api/course'
import { getOrders, payOrder, cancelOrder } from '../../api/order'
import { getMyApplications } from '../../api/job'
import { getMyInterviews, getLearningPlans, deleteLearningPlan } from '../../api/ai'
import { BUILTIN_AVATARS, APP_STATUS, ORDER_STATUS, USER_ROLES, fmtDate, fmtDay } from '../../utils'
import UserAvatar from '../../components/UserAvatar.vue'
import CourseCard from '../../components/CourseCard.vue'
import CourseCover from '../../components/CourseCover.vue'
import JobCard from '../../components/JobCard.vue'
import AppIcon from '../../components/icons/AppIcon.vue'
import AvatarPattern from '../../components/icons/AvatarPattern.vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const TAB_NAMES = ['profile', 'learning', 'plans', 'favorites', 'orders', 'applications', 'interviews', 'password']
const tab = ref('profile')
const favTab = ref('courses')

const profileForm = reactive({ nickname: '', major: '', avatar: '' })
const savingProfile = ref(false)

const enrollments = ref([])
const plans = ref([])
const favorites = reactive({ courses: [], jobs: [] })
const orders = ref([])
const applications = ref([])
const interviews = ref([])
const payingId = ref(null)

const pwdRef = ref()
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })
const savingPwd = ref(false)

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再输一次新密码', trigger: 'blur' },
    {
      validator: (r, v, cb) => cb(v === pwdForm.new_password ? undefined : new Error('两次输入不一致')),
      trigger: 'blur'
    }
  ]
}

const POSITIVE = ['paid', 'accepted', 'done']
const NEGATIVE = ['cancelled', 'rejected']
function statusClass(s) {
  if (POSITIVE.includes(s)) return 'tag-accent'
  if (NEGATIVE.includes(s)) return 'tag-line'
  return 'tag-warn'
}

function isDue(p) {
  return p.due_date && new Date(p.due_date) < new Date()
}

function onTabChange(name) {
  router.replace({ query: { ...route.query, tab: name } })
}

function fillProfile() {
  profileForm.nickname = store.user?.nickname || ''
  profileForm.major = store.user?.major || ''
  profileForm.avatar = store.user?.avatar || ''
}

async function onSaveProfile() {
  savingProfile.value = true
  try {
    await store.updateProfile({
      nickname: profileForm.nickname.trim() || undefined,
      major: profileForm.major.trim() || undefined,
      avatar: profileForm.avatar.trim()
    })
    ElMessage.success('资料已保存')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    savingProfile.value = false
  }
}

async function onSavePwd() {
  try {
    await pwdRef.value.validate()
  } catch {
    return
  }
  savingPwd.value = true
  try {
    await updatePassword({ old_password: pwdForm.old_password, new_password: pwdForm.new_password })
    ElMessage.success('密码已修改')
    pwdForm.old_password = pwdForm.new_password = pwdForm.confirm = ''
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    savingPwd.value = false
  }
}

async function safeLoad(fn, fallback) {
  try {
    return (await fn()) || fallback
  } catch {
    return fallback
  }
}

async function loadLearning() {
  const list = await safeLoad(getMyEnrollments, [])
  enrollments.value = list.map((e) => ({ ...e, _course: e.course || e }))
}

async function loadFavorites() {
  const f = await safeLoad(getMyFavorites, {})
  favorites.courses = f.courses || []
  favorites.jobs = f.jobs || []
}

async function onPay(o) {
  payingId.value = o.id
  try {
    await payOrder(o.id)
    ElMessage.success('支付成功，课程已加入我的学习')
    orders.value = await safeLoad(getOrders, [])
    loadLearning()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    payingId.value = null
  }
}

async function onCancelOrder(o) {
  try {
    await ElMessageBox.confirm('取消后需要重新下单。', '取消订单', { type: 'warning', confirmButtonText: '取消订单', cancelButtonText: '再想想' })
  } catch {
    return
  }
  try {
    await cancelOrder(o.id)
    ElMessage.success('订单已取消')
    orders.value = await safeLoad(getOrders, [])
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDeletePlan(p) {
  try {
    await ElMessageBox.confirm(`删除「${p.plan?.title || p.goal}」？`, '删除学习路径', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  try {
    await deleteLearningPlan(p.id)
    plans.value = plans.value.filter((x) => x.id !== p.id)
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function loadByTab(name) {
  if (name === 'learning') loadLearning()
  else if (name === 'plans') plans.value = await safeLoad(getLearningPlans, [])
  else if (name === 'favorites') loadFavorites()
  else if (name === 'orders') orders.value = await safeLoad(getOrders, [])
  else if (name === 'applications') applications.value = await safeLoad(getMyApplications, [])
  else if (name === 'interviews') interviews.value = await safeLoad(getMyInterviews, [])
}

watch(tab, loadByTab)

watch(() => route.query.tab, (t) => {
  if (TAB_NAMES.includes(t)) tab.value = t
})

onMounted(async () => {
  if (TAB_NAMES.includes(route.query.tab)) tab.value = route.query.tab
  try {
    await store.fetchMe()
  } catch {
    /* token 失效时拦截器已处理跳转 */
  }
  fillProfile()
  loadByTab(tab.value)
})
</script>

<style scoped>
.who {
  display: flex;
  align-items: center;
  gap: 20px;
}

.form-narrow {
  max-width: 560px;
}

.avatar-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.avatar-opt {
  width: 52px;
  height: 52px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: var(--surface);
  color: var(--muted);
  display: grid;
  place-items: center;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.1s;
}

.avatar-opt:hover {
  border-color: var(--muted);
}

.avatar-opt:active {
  transform: scale(0.95);
}

.avatar-opt.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent);
}

.avatar-opt :deep(svg) {
  width: 100%;
  height: 100%;
}

.avatar-opt.none :deep(svg) {
  width: 22px;
  height: 22px;
}

.rows {
  display: grid;
  gap: 10px;
}

.rows .panel + .panel {
  margin-top: 0;
}

.learn-item {
  display: grid;
  grid-template-columns: 160px 1fr auto;
  gap: 18px;
  align-items: center;
  padding: 12px;
}

.learn-cover {
  height: 92px;
}

.learn-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.prog {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prog .bar {
  flex: 1;
  margin: 0;
}

.row-item {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.row-main {
  flex: 1;
  min-width: 220px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.row-ops {
  display: flex;
  gap: 6px;
}

.score {
  font-size: 22px;
  color: var(--accent);
}

.score small {
  font-size: 12px;
  color: var(--muted);
}

.tag-warn {
  background: rgba(242, 196, 109, 0.12);
  color: #f2c46d;
}

.plan-item summary {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  list-style: none;
  flex-wrap: wrap;
}

.plan-item summary::-webkit-details-marker {
  display: none;
}

.plan-sum {
  flex: 1;
  min-width: 220px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stages {
  list-style: none;
  margin: 16px 0 0;
  padding: 16px 0 0;
  border-top: 1px solid var(--line);
  display: grid;
  gap: 12px;
}

.stages li {
  display: flex;
  gap: 14px;
}

.stages .no {
  color: var(--accent);
  font-size: 13px;
  padding-top: 2px;
}

.topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

@media (max-width: 768px) {
  .who {
    gap: 14px;
  }

  .learn-item {
    grid-template-columns: 1fr;
  }

  .learn-cover {
    height: 120px;
  }

  .learn-item .el-button {
    width: 100%;
  }
}
</style>
