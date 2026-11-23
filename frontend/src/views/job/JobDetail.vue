<template>
  <div class="page" v-loading="loading">
    <template v-if="job">
      <div class="page-head job-head">
        <div class="head-main">
          <router-link to="/jobs" class="back-link">
            <AppIcon name="arrow-left" :size="16" />
            <span>返回职位列表</span>
          </router-link>
          <p class="eyebrow">{{ job.category || '职位' }} · {{ job.city }}</p>
          <h1 class="page-title">{{ job.title }}</h1>
          <div class="company-line">
            <span><AppIcon name="building" :size="16" />{{ job.company }}</span>
            <span><AppIcon name="pin" :size="16" />{{ job.city }}</span>
            <span v-if="job.headcount"><AppIcon name="users" :size="16" />招 {{ job.headcount }} 人</span>
            <span><AppIcon name="calendar" :size="16" />{{ fmtDay(job.created_at) }} 发布</span>
          </div>
        </div>
        <div class="salary-box mono">{{ job.salary || '薪资面议' }}</div>
      </div>

      <div class="detail-grid">
        <div class="main-col">
          <div v-if="tags.length" class="tags">
            <span v-for="t in tags" :key="t" class="tag tag-line">{{ t }}</span>
          </div>

          <section class="card">
            <h2 class="section-title">职位描述</h2>
            <div class="pre-wrap jd-text">{{ job.description || '暂无描述' }}</div>
            <template v-if="job.requirements">
              <h2 class="section-title mt-24">任职要求</h2>
              <div class="pre-wrap jd-text">{{ job.requirements }}</div>
            </template>
          </section>
        </div>

        <aside class="side-col">
          <section class="panel">
            <h2 class="panel-title">投递 <small v-if="detail?.has_applied">已申请</small></h2>
            <div class="actions">
              <el-button type="primary" size="large" :disabled="!!detail?.has_applied" @click="applyVisible = true">
                <AppIcon name="send" :size="16" />
                <span class="btn-text">{{ detail?.has_applied ? '已申请' : '申请职位' }}</span>
              </el-button>
              <el-button size="large" :loading="interviewing" @click="onInterview">
                <AppIcon v-if="!interviewing" name="mic" :size="16" />
                <span class="btn-text">AI 模拟面试</span>
              </el-button>
              <el-button size="large" :class="{ 'is-fav': detail?.is_favorited }" @click="onFavorite">
                <AppIcon name="star" :size="16" />
                <span class="btn-text">{{ detail?.is_favorited ? '已收藏' : '收藏' }}</span>
              </el-button>
            </div>
            <p class="hint">模拟面试会按这个岗位出 5 道题，交卷后逐题打分。记录保存在个人中心的「AI 面试记录」。</p>
          </section>

          <section class="panel">
            <h2 class="panel-title">公司信息</h2>
            <div class="company-row">
              <span class="company-logo"><AppIcon name="building" :size="22" /></span>
              <div>
                <b class="company-name">{{ job.company }}</b>
                <small class="text-sub">{{ job.city }}</small>
              </div>
            </div>
            <p class="pre-wrap text-sub company-intro">{{ job.company_intro || job.company_introduction || '该公司暂未填写详细介绍。' }}</p>
          </section>
        </aside>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="职位不存在或已下架">
      <el-button type="primary" @click="$router.push('/jobs')">返回职位列表</el-button>
    </el-empty>

    <!-- 申请弹窗 -->
    <el-dialog v-model="applyVisible" title="申请职位" width="480px">
      <el-form label-position="top">
        <el-form-item :label="`申请岗位：${job?.title || ''}`">
          <el-input
            v-model="applyMsg"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="附言（可选）：自我介绍、做过的项目、可到岗时间"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="onApply">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getJobDetail, toggleJobFavorite, applyJob, createInterview } from '../../api/job'
import { fmtDay } from '../../utils'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const loading = ref(true)
const detail = ref(null)
const applyVisible = ref(false)
const applyMsg = ref('')
const applying = ref(false)
const interviewing = ref(false)

const job = computed(() => detail.value?.job || detail.value)
const tags = computed(() => {
  const t = job.value?.tags
  if (Array.isArray(t)) return t
  if (typeof t === 'string') return t.split(/[,，\s]+/).filter(Boolean)
  return []
})

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getJobDetail(id)
  } catch (e) {
    detail.value = null
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function onFavorite() {
  try {
    const res = await toggleJobFavorite(id)
    detail.value.is_favorited = res?.favorited
    ElMessage.success(res?.favorited ? '已收藏职位' : '已取消收藏')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onApply() {
  applying.value = true
  try {
    await applyJob(id, applyMsg.value.trim() || undefined)
    applyVisible.value = false
    detail.value.has_applied = true
    ElMessage.success('申请已提交，可在个人中心查看进度')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    applying.value = false
  }
}

async function onInterview() {
  interviewing.value = true
  try {
    const res = await createInterview(id, applyMsg.value.trim() || undefined)
    const interviewId = res?.interview_id || res?.id
    if (!interviewId) throw new Error('面试创建失败')
    // 面试页通过 GET /api/ai/interview/{id} 恢复题目
    router.push(`/interview/${interviewId}`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    interviewing.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.job-head {
  align-items: flex-end;
}

.head-main {
  min-width: 0;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
  margin-bottom: 14px;
  min-height: 32px;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--ink);
}

.company-line {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  color: var(--muted);
  font-size: 14px;
}

.company-line span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.salary-box {
  font-size: 26px;
  font-weight: 600;
  color: var(--accent);
  white-space: nowrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: start;
}

.main-col {
  min-width: 0;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.jd-text {
  line-height: 1.85;
  color: var(--ink-2);
}

.side-col {
  position: sticky;
  top: 88px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.actions .el-button {
  width: 100%;
  margin-left: 0;
}

.btn-text {
  margin-left: 6px;
}

.is-fav {
  color: var(--accent);
  border-color: var(--accent);
}

.hint {
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.6;
}

.company-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.company-logo {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: var(--r);
  background: var(--bg);
  color: var(--accent);
  flex-shrink: 0;
}

.company-name {
  display: block;
  font-size: 15px;
  font-weight: 600;
}

.company-intro {
  margin: 14px 0 0;
  line-height: 1.7;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .side-col {
    position: static;
  }
}

@media (max-width: 768px) {
  .salary-box {
    font-size: 22px;
  }

  .actions .el-button {
    min-height: 44px;
  }
}
</style>
