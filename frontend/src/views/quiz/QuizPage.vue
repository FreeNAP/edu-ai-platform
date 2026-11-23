<template>
  <div class="page page-narrow" v-loading="loading">
    <template v-if="quiz">
      <button class="back" type="button" @click="$router.push(`/course/${quiz.course_id}`)">
        <AppIcon name="arrow-left" :size="16" />返回课程
      </button>
      <div class="page-head">
        <div>
          <p class="eyebrow">{{ quiz.kind === 'exam' ? '结业考试' : '课时测验' }} · {{ quiz.question_count }} 题 · 及格 {{ quiz.pass_score }} 分</p>
          <h1 class="page-title">{{ quiz.title }}</h1>
          <p class="lead">
            <template v-if="quiz.time_limit_minutes">限时 {{ quiz.time_limit_minutes }} 分钟。</template>
            <template v-if="quiz.max_attempts">最多作答 {{ quiz.max_attempts }} 次，已用 {{ quiz.attempts.length }} 次。</template>
            <template v-if="quiz.kind === 'exam'">通过后自动发放课程证书。</template>
          </p>
        </div>
        <div v-if="remaining !== null && !result" class="timer mono" :class="{ warn: remaining < 60 }">
          <AppIcon name="clock" :size="16" />{{ fmtClock(remaining) }}
        </div>
      </div>

      <div v-if="result" class="panel result" :class="result.attempt.passed ? 'pass' : 'fail'">
        <div class="score mono">{{ result.attempt.score }}</div>
        <div>
          <b>{{ result.attempt.passed ? '通过了' : '还没通过' }}</b>
          <p class="text-sub">及格线 {{ result.pass_score }} 分。下面标出了每题的正确答案和解析。</p>
          <router-link v-if="result.certificate" :to="`/certificate/${result.certificate.cert_no}`" class="cert-link">
            <AppIcon name="star" :size="16" />查看证书 {{ result.certificate.cert_no }}
          </router-link>
        </div>
        <el-button v-if="canRetry" @click="retry">再做一次</el-button>
      </div>

      <ol class="questions">
        <li v-for="(q, i) in quiz.questions" :key="q.id" class="panel q" :class="feedbackClass(q)">
          <div class="q-head">
            <span class="mono no">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="tag">{{ KIND_LABEL[q.kind] }}</span>
            <span class="text-sub mono">{{ q.score }} 分</span>
          </div>
          <p class="stem pre-wrap">{{ q.stem }}</p>
          <div class="options" role="group" :aria-label="`第 ${i + 1} 题选项`">
            <button
              v-for="(opt, k) in q.options"
              :key="k"
              type="button"
              class="opt"
              :class="optionClass(q, k)"
              :disabled="!!result"
              :aria-pressed="isChosen(q, k)"
              @click="choose(q, k)"
            >
              <span class="letter mono">{{ letterOf(q, k) }}</span>{{ opt }}
            </button>
          </div>
          <p v-if="feedback(q)" class="explain">
            <b>{{ feedback(q).correct ? '回答正确' : `正确答案：${feedback(q).answer}` }}</b>
            <span v-if="feedback(q).explanation"> {{ feedback(q).explanation }}</span>
          </p>
        </li>
      </ol>

      <div v-if="!result" class="submit-bar">
        <span class="text-sub">已答 {{ answeredCount }} / {{ quiz.questions.length }}</span>
        <el-button type="primary" size="large" :loading="submitting" @click="onSubmit()">交卷</el-button>
      </div>
    </template>
    <el-empty v-else-if="!loading" :description="error || '测验不存在'">
      <el-button type="primary" @click="$router.back()">返回</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getQuiz, submitQuiz } from '../../api/quiz'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const KIND_LABEL = { single: '单选', multiple: '多选', judge: '判断' }
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const quiz = ref(null)
const answers = reactive({})
const result = ref(null)
const remaining = ref(null)
let timer = null

const letterOf = (q, k) => (q.kind === 'judge' ? (k === 0 ? 'T' : 'F') : String.fromCharCode(65 + k))
const isChosen = (q, k) => (answers[q.id] || '').includes(letterOf(q, k))
const answeredCount = computed(() => Object.values(answers).filter(Boolean).length)
const canRetry = computed(() => !quiz.value?.max_attempts || quiz.value.attempts.length + 1 < quiz.value.max_attempts)
const feedback = (q) => result.value?.results.find((r) => r.question_id === q.id)
const feedbackClass = (q) => (feedback(q) ? (feedback(q).correct ? 'right' : 'wrong') : '')

function optionClass(q, k) {
  const letter = letterOf(q, k)
  const fb = feedback(q)
  return {
    on: isChosen(q, k),
    correct: fb && fb.answer.includes(letter),
    missed: fb && !fb.answer.includes(letter) && isChosen(q, k)
  }
}

function choose(q, k) {
  const letter = letterOf(q, k)
  if (q.kind === 'multiple') {
    const cur = new Set((answers[q.id] || '').split('').filter(Boolean))
    cur.has(letter) ? cur.delete(letter) : cur.add(letter)
    answers[q.id] = [...cur].sort().join('')
  } else {
    answers[q.id] = letter
  }
}

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function startTimer() {
  clearInterval(timer)
  if (!quiz.value.time_limit_minutes) return
  remaining.value = quiz.value.time_limit_minutes * 60
  timer = setInterval(() => {
    remaining.value -= 1
    if (remaining.value <= 0) {
      clearInterval(timer)
      ElMessage.warning('时间到，已自动交卷')
      onSubmit(true)
    }
  }, 1000)
}

async function load() {
  loading.value = true
  try {
    quiz.value = await getQuiz(route.params.id)
    startTimer()
  } catch (e) {
    error.value = e.message
    quiz.value = null
  } finally {
    loading.value = false
  }
}

async function onSubmit(auto = false) {
  if (!auto && answeredCount.value < quiz.value.questions.length) {
    try {
      await ElMessageBox.confirm(`还有 ${quiz.value.questions.length - answeredCount.value} 题没答，确定交卷？`, '交卷', { type: 'warning', confirmButtonText: '交卷', cancelButtonText: '继续答题' })
    } catch {
      return
    }
  }
  submitting.value = true
  try {
    result.value = await submitQuiz(quiz.value.id, { ...answers })
    clearInterval(timer)
    remaining.value = null
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

function retry() {
  Object.keys(answers).forEach((k) => delete answers[k])
  result.value = null
  load()
}

onMounted(load)
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  margin-bottom: 12px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.timer {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border: 1px solid var(--line);
  border-radius: var(--r);
  font-size: 20px;
}

.timer.warn {
  color: #f28b82;
  border-color: #f28b82;
}

.result {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  border-left: 3px solid var(--line);
}

.result.pass {
  border-left-color: var(--accent);
}

.result.fail {
  border-left-color: #f28b82;
}

.result > div:nth-child(2) {
  flex: 1;
  min-width: 200px;
}

.score {
  font-size: 52px;
  line-height: 1;
}

.result.pass .score {
  color: var(--accent);
}

.cert-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--accent);
  margin-top: 6px;
}

.questions {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.questions .panel + .panel {
  margin-top: 0;
}

.q.right {
  border-color: rgba(218, 250, 156, 0.4);
}

.q.wrong {
  border-color: rgba(242, 139, 130, 0.45);
}

.q-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.no {
  color: var(--accent);
  font-size: 13px;
}

.stem {
  margin: 10px 0 12px;
  font-size: 15px;
  line-height: 1.7;
}

.options {
  display: grid;
  gap: 8px;
}

.opt {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: var(--r);
  background: var(--bg);
  color: var(--ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.opt:hover:not(:disabled) {
  border-color: var(--muted);
}

.opt:disabled {
  cursor: default;
}

.opt.on {
  border-color: var(--accent);
  background: var(--tint);
}

.opt.correct {
  border-color: var(--accent);
}

.opt.missed {
  border-color: #f28b82;
  background: rgba(242, 139, 130, 0.08);
}

.letter {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: var(--r);
  font-size: 12px;
  flex-shrink: 0;
}

.opt.on .letter {
  background: var(--accent);
  color: #0f0f0f;
  border-color: var(--accent);
}

.explain {
  margin: 12px 0 0;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
  font-size: 14px;
  color: var(--muted);
}

.explain b {
  color: var(--ink);
}

.submit-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding: 12px 0;
  background: var(--bg);
  border-top: 1px solid var(--line);
}
</style>
