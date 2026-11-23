<template>
  <div class="page page-narrow" v-loading="loading">
    <template v-if="interview">
      <div class="page-head">
        <div>
          <router-link :to="interview.job?.id ? `/job/${interview.job.id}` : '/jobs'" class="back-link">
            <AppIcon name="arrow-left" :size="16" />
            <span>返回职位</span>
          </router-link>
          <p class="eyebrow">// AI 模拟面试 #{{ interview.id }} · {{ isDone ? '已完成' : '作答中' }}</p>
          <h1 class="page-title">{{ interview.job?.title || '模拟面试' }}</h1>
          <p class="lead">
            <template v-if="interview.job?.company">{{ interview.job.company }} · </template>
            <template v-if="isDone">交卷时间 {{ fmtDate(interview.created_at) }}，下面是得分和逐题点评。</template>
            <template v-else>共 {{ questions.length }} 题。答完点底部的提交，AI 会给总分和每题点评。刷新页面不会丢题目，但没提交的回答不会保存。</template>
          </p>
        </div>
      </div>

      <!-- 作答 -->
      <template v-if="!isDone">
        <section v-for="(q, i) in questions" :key="i" class="card q-card">
          <div class="q-title">
            <span class="q-no mono">Q{{ String(i + 1).padStart(2, '0') }}</span>
            <span>{{ q }}</span>
          </div>
          <el-input
            v-model="answers[i]"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="写下你的回答，尽量结合做过的项目"
          />
        </section>

        <div class="submit-bar">
          <span class="text-sub mono">已作答 {{ answeredCount }} / {{ questions.length }}</span>
          <el-button type="primary" size="large" :loading="submitting" @click="onSubmit">
            <AppIcon v-if="!submitting" name="send" :size="16" />
            <span class="btn-text">提交全部作答</span>
          </el-button>
        </div>
      </template>

      <!-- 结果 -->
      <template v-else>
        <section class="card result-head">
          <div class="score-ring" :class="scoreLevel">
            <svg viewBox="0 0 120 120" aria-hidden="true">
              <circle cx="60" cy="60" r="52" class="ring-bg" />
              <circle cx="60" cy="60" r="52" class="ring-fg" :stroke-dasharray="`${ringLen} 999`" />
            </svg>
            <div class="score-text">
              <b class="mono">{{ score }}</b>
              <small>综合得分</small>
            </div>
          </div>
          <div class="result-eval">
            <h2 class="section-title">总体评价</h2>
            <p class="pre-wrap">{{ interview.evaluation || '暂无总体评价' }}</p>
          </div>
        </section>

        <section v-if="perQuestions.length" class="card mt-16">
          <h2 class="section-title">逐题点评</h2>
          <div v-for="(item, i) in perQuestions" :key="i" class="per-q">
            <div class="per-top">
              <div class="q-title">
                <span class="q-no mono">Q{{ String(i + 1).padStart(2, '0') }}</span>
                <span>{{ item.question }}</span>
              </div>
              <span v-if="item.score !== null" class="per-score mono" :class="{ low: item.score < 60 }">{{ item.score }}</span>
            </div>
            <div class="per-block">
              <small>我的回答</small>
              <p class="pre-wrap">{{ item.answer || '（未作答）' }}</p>
            </div>
            <div class="per-block comment">
              <small>点评</small>
              <p class="pre-wrap">{{ item.comment || '暂无点评' }}</p>
            </div>
          </div>
        </section>

        <div class="submit-bar">
          <el-button @click="$router.push('/me?tab=interviews')">查看全部面试记录</el-button>
          <el-button v-if="interview.job?.id" type="primary" @click="$router.push(`/job/${interview.job.id}`)">回到职位</el-button>
        </div>
      </template>
    </template>

    <el-empty v-else-if="!loading" :description="errorText">
      <el-button type="primary" @click="$router.push('/jobs')">返回职位列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getInterview, submitInterviewAnswers } from '../../api/ai'
import { fmtDate } from '../../utils'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const id = route.params.id

const loading = ref(true)
const interview = ref(null)
const answers = ref([])
const submitting = ref(false)
const errorText = ref('没有找到这场面试，可能已失效。回到职位详情页重新发起即可。')

const questions = computed(() =>
  (interview.value?.questions || []).map((q) => (typeof q === 'string' ? q : q?.question || q?.title || ''))
)
const isDone = computed(() => interview.value?.status === 'done')
const answeredCount = computed(() => answers.value.filter((a) => a?.trim()).length)
const score = computed(() => Math.max(0, Math.min(100, Math.round(Number(interview.value?.score) || 0))))
const ringLen = computed(() => (2 * Math.PI * 52 * score.value) / 100)
const scoreLevel = computed(() => (score.value >= 80 ? 'good' : score.value >= 60 ? 'mid' : 'low'))

// per_question 统一结构：{question, answer, score, comment}
const perQuestions = computed(() => {
  const list = interview.value?.per_question
  if (!Array.isArray(list)) return []
  const ans = interview.value?.answers || []
  return list.map((item, i) => {
    if (typeof item === 'string') {
      return { question: questions.value[i] || `第 ${i + 1} 题`, answer: ans[i]?.answer || '', comment: item, score: null }
    }
    return {
      question: item.question || questions.value[i] || `第 ${i + 1} 题`,
      answer: item.answer ?? ans[i]?.answer ?? '',
      comment: item.comment || item.feedback || item.evaluation || '',
      score: typeof item.score === 'number' ? Math.round(item.score) : null
    }
  })
})

async function load() {
  loading.value = true
  try {
    const data = await getInterview(id)
    interview.value = data
    answers.value = (data?.questions || []).map(() => '')
  } catch (e) {
    interview.value = null
    errorText.value = e.message && !/404/.test(e.message) ? `${e.message}。可以回到职位详情页重新发起面试。` : errorText.value
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  if (!answeredCount.value) {
    ElMessage.warning('请至少作答一道题')
    return
  }
  if (answeredCount.value < questions.value.length) {
    try {
      await ElMessageBox.confirm(`还有 ${questions.value.length - answeredCount.value} 题没写，确定现在提交吗？`, '确认提交', {
        confirmButtonText: '提交',
        cancelButtonText: '继续作答',
        type: 'warning'
      })
    } catch {
      return
    }
  }
  submitting.value = true
  try {
    const payload = questions.value.map((q, i) => ({ question: q, answer: answers.value[i] || '' }))
    const res = await submitInterviewAnswers(id, payload)
    interview.value = {
      ...interview.value,
      status: 'done',
      answers: payload,
      score: res?.score ?? 0,
      evaluation: res?.evaluation || '',
      per_question: res?.per_question || []
    }
    window.scrollTo({ top: 0 })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
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

.q-card + .q-card {
  margin-top: 16px;
}

.q-title {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  font-weight: 500;
  line-height: 1.6;
  margin-bottom: 12px;
}

.q-no {
  flex-shrink: 0;
  font-size: 12px;
  padding: 2px 6px;
  margin-top: 2px;
  background: var(--tint);
  color: var(--accent);
  border-radius: 1px;
}

.submit-bar {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-text {
  margin-left: 6px;
}

.result-head {
  display: flex;
  gap: 32px;
  align-items: center;
}

.score-ring {
  position: relative;
  width: 140px;
  height: 140px;
  flex-shrink: 0;
}

.score-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: var(--surface);
  stroke-width: 8;
}

.ring-fg {
  fill: none;
  stroke: var(--accent);
  stroke-width: 8;
  transition: stroke-dasharray 0.6s ease;
}

.score-ring.mid .ring-fg {
  stroke: var(--warn);
}

.score-ring.low .ring-fg {
  stroke: var(--danger);
}

.score-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-text b {
  font-size: 38px;
  font-weight: 600;
  line-height: 1;
}

.score-text small {
  color: var(--muted);
  font-size: 12px;
  margin-top: 6px;
}

.result-eval {
  flex: 1;
  min-width: 0;
}

.result-eval p {
  margin: 0;
  color: var(--ink-2);
  line-height: 1.8;
}

.per-q {
  padding: 18px 0;
  border-top: 1px solid var(--line);
}

.per-q:first-of-type {
  border-top: 0;
  padding-top: 4px;
}

.per-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.per-score {
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
}

.per-score.low {
  color: var(--danger);
}

.per-block {
  margin-top: 8px;
  padding: 10px 12px;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: var(--r);
}

.per-block.comment {
  background: var(--tint);
  border-color: transparent;
}

.per-block small {
  font: 500 11px var(--mono);
  color: var(--muted);
  letter-spacing: 0.06em;
}

.per-block p {
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--ink-2);
}

@media (max-width: 768px) {
  .result-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .submit-bar .el-button {
    flex: 1;
    min-height: 44px;
  }

  .submit-bar .el-button + .el-button {
    margin-left: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ring-fg {
    transition: none;
  }
}
</style>
