<template>
  <el-drawer :model-value="modelValue" :title="`测验与考试 · ${course?.title || ''}`" size="min(820px, 100vw)" @update:model-value="(v) => emit('update:modelValue', v)" @open="load">
    <div v-loading="loading">
      <template v-if="!editing">
        <div class="toolbar">
          <el-button type="primary" @click="edit(null, 'quiz')"><AppIcon name="plus" :size="16" />新建课时测验</el-button>
          <el-button :disabled="hasExam" @click="edit(null, 'exam')">新建结业考试</el-button>
        </div>
        <el-empty v-if="!quizzes.length" description="还没有测验。结业考试通过后学员会获得证书。" />
        <div v-for="q in quizzes" :key="q.id" class="panel quiz-row">
          <div class="grow">
            <b>{{ q.title }}</b>
            <span class="text-sub">{{ q.kind === 'exam' ? '结业考试' : '课时测验' }} · {{ q.question_count }} 题 · 及格 {{ q.pass_score }} 分<template v-if="q.time_limit_minutes"> · 限时 {{ q.time_limit_minutes }} 分钟</template></span>
          </div>
          <el-button size="small" @click="edit(q)">编辑</el-button>
          <el-button size="small" @click="remove(q)">删除</el-button>
        </div>
      </template>

      <el-form v-else label-position="top" class="editor">
        <div class="form-grid">
          <el-form-item label="标题" class="span2"><el-input v-model="form.title" maxlength="128" /></el-form-item>
          <el-form-item v-if="form.kind === 'quiz'" label="挂在哪个课时" class="span2">
            <el-select v-model="form.lesson_id" clearable placeholder="不选则作为课程练习">
              <el-option-group v-for="ch in outline" :key="ch.id" :label="ch.title">
                <el-option v-for="ls in ch.lessons" :key="ls.id" :label="ls.title" :value="ls.id" />
              </el-option-group>
            </el-select>
          </el-form-item>
          <el-form-item label="及格分（百分制）"><el-input-number v-model="form.pass_score" :min="1" :max="100" /></el-form-item>
          <el-form-item label="限时（分钟，0 不限）"><el-input-number v-model="form.time_limit_minutes" :min="0" :max="600" /></el-form-item>
          <el-form-item label="最多作答次数（0 不限）"><el-input-number v-model="form.max_attempts" :min="0" :max="100" /></el-form-item>
        </div>

        <div v-for="(q, i) in form.questions" :key="q._k" class="panel question">
          <div class="q-head">
            <span class="mono no">{{ String(i + 1).padStart(2, '0') }}</span>
            <el-select v-model="q.kind" class="kind" @change="onKind(q)">
              <el-option label="单选" value="single" /><el-option label="多选" value="multiple" /><el-option label="判断" value="judge" />
            </el-select>
            <el-input-number v-model="q.score" :min="1" :max="100" size="small" />
            <span class="text-sub">分</span>
            <span class="grow"></span>
            <el-button size="small" aria-label="删除题目" @click="form.questions.splice(i, 1)"><AppIcon name="trash" :size="14" /></el-button>
          </div>
          <el-input v-model="q.stem" type="textarea" :autosize="{ minRows: 2 }" placeholder="题干" />
          <template v-if="q.kind !== 'judge'">
            <div v-for="(opt, k) in q.options" :key="k" class="opt-row">
              <el-checkbox :model-value="q.answer.includes(letter(k))" @change="toggleAnswer(q, k)">{{ letter(k) }}</el-checkbox>
              <el-input v-model="q.options[k]" :placeholder="`选项 ${letter(k)}`" />
              <el-button size="small" :disabled="q.options.length <= 2" aria-label="删除选项" @click="removeOption(q, k)"><AppIcon name="close" :size="14" /></el-button>
            </div>
            <el-button text type="primary" :disabled="q.options.length >= 8" @click="q.options.push('')">加选项</el-button>
          </template>
          <el-radio-group v-else v-model="q.answer">
            <el-radio value="T">正确</el-radio><el-radio value="F">错误</el-radio>
          </el-radio-group>
          <el-input v-model="q.explanation" placeholder="解析（交卷后展示，可选）" />
        </div>
        <el-button @click="addQuestion"><AppIcon name="plus" :size="16" />加一道题</el-button>
      </el-form>
    </div>
    <template v-if="editing" #footer>
      <el-button @click="editing = false">返回列表</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { teacherQuizzes, teacherCreateQuiz, teacherUpdateQuiz, teacherDeleteQuiz, teacherGetOutline } from '../../api/teacher'
import AppIcon from '../../components/icons/AppIcon.vue'

const props = defineProps({ modelValue: Boolean, course: { type: Object, default: null } })
const emit = defineEmits(['update:modelValue', 'changed'])

const loading = ref(false)
const saving = ref(false)
const quizzes = ref([])
const outline = ref([])
const editing = ref(false)
const form = reactive({ id: null, kind: 'quiz', title: '', lesson_id: null, pass_score: 60, time_limit_minutes: 0, max_attempts: 0, questions: [] })
let seed = 0
const letter = (k) => String.fromCharCode(65 + k)
const hasExam = computed(() => quizzes.value.some((q) => q.kind === 'exam'))
const blank = () => ({ _k: ++seed, kind: 'single', stem: '', options: ['', '', '', ''], answer: '', explanation: '', score: 10 })

async function load() {
  editing.value = false
  if (!props.course) return
  loading.value = true
  try {
    ;[quizzes.value, outline.value] = await Promise.all([teacherQuizzes(props.course.id), teacherGetOutline(props.course.id)])
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function edit(q, kind) {
  Object.assign(form, q
    ? { id: q.id, kind: q.kind, title: q.title, lesson_id: q.lesson_id, pass_score: q.pass_score, time_limit_minutes: q.time_limit_minutes, max_attempts: q.max_attempts,
        questions: q.questions.map((x) => ({ _k: ++seed, kind: x.kind, stem: x.stem, options: x.kind === 'judge' ? [] : [...x.options], answer: x.answer, explanation: x.explanation || '', score: x.score })) }
    : { id: null, kind, title: kind === 'exam' ? `《${props.course.title}》结业考试` : '', lesson_id: null, pass_score: 60, time_limit_minutes: kind === 'exam' ? 30 : 0, max_attempts: kind === 'exam' ? 3 : 0, questions: [blank()] })
  editing.value = true
}

function addQuestion() {
  form.questions.push(blank())
}

function onKind(q) {
  q.answer = ''
  if (q.kind === 'judge') q.options = []
  else if (q.options.length < 2) q.options = ['', '', '', '']
}

function toggleAnswer(q, k) {
  const l = letter(k)
  if (q.kind === 'single') q.answer = l
  else q.answer = q.answer.includes(l) ? q.answer.replace(l, '') : [...q.answer, l].sort().join('')
}

function removeOption(q, k) {
  q.options.splice(k, 1)
  q.answer = ''
}

async function save() {
  if (!form.title.trim()) return ElMessage.warning('请填写标题')
  if (!form.questions.length) return ElMessage.warning('至少需要一道题')
  for (const [i, q] of form.questions.entries()) {
    if (!q.stem.trim()) return ElMessage.warning(`第 ${i + 1} 题没有题干`)
    if (!q.answer) return ElMessage.warning(`第 ${i + 1} 题没有设置答案`)
    if (q.kind !== 'judge' && q.options.some((o) => !o.trim())) return ElMessage.warning(`第 ${i + 1} 题有空选项`)
  }
  saving.value = true
  const payload = {
    title: form.title.trim(), kind: form.kind, lesson_id: form.lesson_id || null, pass_score: form.pass_score,
    time_limit_minutes: form.time_limit_minutes, max_attempts: form.max_attempts,
    questions: form.questions.map((q) => ({ kind: q.kind, stem: q.stem.trim(), options: q.options.map((o) => o.trim()), answer: q.answer, explanation: q.explanation.trim(), score: q.score }))
  }
  try {
    if (form.id) await teacherUpdateQuiz(form.id, payload)
    else await teacherCreateQuiz(props.course.id, payload)
    ElMessage.success('已保存')
    emit('changed')
    load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function remove(q) {
  try {
    await ElMessageBox.confirm(`删除「${q.title}」？学员的作答记录也会删除。`, '删除测验', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  try {
    await teacherDeleteQuiz(q.id)
    emit('changed')
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}
</script>

<style scoped>
.toolbar .el-button,
.editor > .el-button {
  gap: 6px;
}

.quiz-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.quiz-row + .quiz-row {
  margin-top: 8px;
}

.grow {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0 12px;
}

.span2 {
  grid-column: span 3;
}

.question {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}

.question + .question {
  margin-top: 0;
}

.q-head,
.opt-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.no {
  color: var(--accent);
  font-size: 13px;
}

.kind {
  width: 90px;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .span2 {
    grid-column: span 1;
  }
}
</style>
