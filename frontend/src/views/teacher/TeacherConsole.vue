<template>
  <div class="page">
    <div class="page-head">
      <div>
        <p class="eyebrow">教师工作台</p>
        <h1 class="page-title">我负责的课程</h1>
        <p class="lead">新建的课程默认下架，补好目录和测验再上架。学员进度和测验成绩在「学员」里看。</p>
      </div>
      <el-button type="primary" @click="openCourse(null)"><AppIcon name="plus" :size="16" />新建课程</el-button>
    </div>

    <div class="stats">
      <div v-for="s in statCards" :key="s.label" class="panel stat">
        <span class="text-sub">{{ s.label }}</span>
        <b class="mono">{{ s.value }}</b>
      </div>
    </div>

    <el-table v-loading="loading" class="panel-table mt-16" :data="courses" empty-text="还没有负责的课程">
      <el-table-column label="编号" width="96"><template #default="{ row }"><span class="mono text-sub">{{ courseCode(row) }}</span></template></el-table-column>
      <el-table-column prop="title" label="课程" min-width="200" show-overflow-tooltip />
      <el-table-column label="模块" width="96"><template #default="{ row }">{{ categoryLabel(row.category) }}</template></el-table-column>
      <el-table-column label="课时" width="70" align="center"><template #default="{ row }"><span class="mono">{{ row.lesson_count }}</span></template></el-table-column>
      <el-table-column label="学员" width="70" align="center"><template #default="{ row }"><span class="mono">{{ row.enrolled }}</span></template></el-table-column>
      <el-table-column label="测验" width="70" align="center"><template #default="{ row }"><span class="mono">{{ row.quiz_count }}</span></template></el-table-column>
      <el-table-column label="上架" width="80" align="center">
        <template #default="{ row }"><el-switch :model-value="row.status === 'on'" @change="(v) => toggle(row, v)" /></template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openCourse(row)">信息</el-button>
          <el-button size="small" text type="primary" @click="openOutline(row)">目录</el-button>
          <el-button size="small" text type="primary" @click="openQuizzes(row)">测验</el-button>
          <el-button size="small" text type="primary" @click="openStudents(row)">学员</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 课程信息 -->
    <el-dialog v-model="courseVisible" :title="courseForm.id ? '编辑课程' : '新建课程'" width="min(600px, 94vw)">
      <el-form label-position="top">
        <el-form-item label="课程名" required><el-input v-model="courseForm.title" maxlength="128" /></el-form-item>
        <div class="form-grid">
          <el-form-item label="模块">
            <el-select v-model="courseForm.category"><el-option label="理论课程" value="theory" /><el-option label="实训课程" value="practice" /><el-option label="认证课程" value="certification" /></el-select>
          </el-form-item>
          <el-form-item label="技术方向"><el-input v-model="courseForm.tech_domain" placeholder="AI / 前端 / 后端 …" /></el-form-item>
          <el-form-item label="难度">
            <el-select v-model="courseForm.difficulty"><el-option v-for="d in ['入门', '初级', '中级', '高级']" :key="d" :label="d" :value="d" /></el-select>
          </el-form-item>
          <el-form-item label="价格（元，0 为免费）"><el-input-number v-model="courseForm.price" :min="0" :max="100000" /></el-form-item>
        </div>
        <el-form-item label="简介"><el-input v-model="courseForm.brief" type="textarea" :rows="4" maxlength="2000" show-word-limit /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="courseVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCourse">保存</el-button>
      </template>
    </el-dialog>

    <OutlineEditor v-model="outlineVisible" :course="current" :loader="teacherGetOutline" :saver="teacherSaveOutline" @saved="load" />

    <!-- 学员 -->
    <el-drawer v-model="studentsVisible" :title="`学员 · ${current?.title || ''}`" size="min(720px, 100vw)">
      <el-table v-loading="studentsLoading" :data="students" empty-text="还没有学员报名">
        <el-table-column label="学员" min-width="140"><template #default="{ row }">{{ row.user.nickname || row.user.username }}<div class="text-sub">{{ row.user.major }}</div></template></el-table-column>
        <el-table-column label="进度" width="160"><template #default="{ row }"><div class="prog"><div class="bar"><i :style="{ width: row.progress + '%' }"></i></div><span class="mono">{{ row.progress }}%</span></div></template></el-table-column>
        <el-table-column label="学习时长" width="100"><template #default="{ row }">{{ fmtMinutes(row.study_minutes) }}</template></el-table-column>
        <el-table-column label="最好成绩" width="90" align="center"><template #default="{ row }"><span class="mono">{{ row.best_quiz_score ?? '-' }}</span></template></el-table-column>
        <el-table-column label="报名时间" width="110"><template #default="{ row }">{{ fmtDay(row.enrolled_at) }}</template></el-table-column>
      </el-table>
    </el-drawer>

    <QuizManager v-model="quizzesVisible" :course="current" @changed="load" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  teacherOverview, teacherCourses, teacherCreateCourse, teacherUpdateCourse,
  teacherGetOutline, teacherSaveOutline, teacherStudents
} from '../../api/teacher'
import { categoryLabel, courseCode, fmtDay, fmtMinutes } from '../../utils'
import AppIcon from '../../components/icons/AppIcon.vue'
import OutlineEditor from '../../components/OutlineEditor.vue'
import QuizManager from './QuizManager.vue'

const loading = ref(false)
const saving = ref(false)
const overview = ref({})
const courses = ref([])
const current = ref(null)
const courseVisible = ref(false)
const outlineVisible = ref(false)
const studentsVisible = ref(false)
const quizzesVisible = ref(false)
const studentsLoading = ref(false)
const students = ref([])
const courseForm = reactive({ id: null, title: '', category: 'theory', tech_domain: '', difficulty: '入门', price: 0, brief: '' })

const statCards = computed(() => [
  { label: '负责课程', value: overview.value.courses ?? '-' },
  { label: '已上架', value: overview.value.on_sale ?? '-' },
  { label: '学员人次', value: overview.value.students ?? '-' },
  { label: '平均进度', value: overview.value.avg_progress != null ? `${overview.value.avg_progress}%` : '-' },
  { label: '收到评价', value: overview.value.comments ?? '-' }
])

async function load() {
  loading.value = true
  try {
    ;[overview.value, courses.value] = await Promise.all([teacherOverview(), teacherCourses()])
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openCourse(row) {
  Object.assign(courseForm, row
    ? { id: row.id, title: row.title, category: row.category, tech_domain: row.tech_domain, difficulty: row.difficulty, price: row.is_free ? 0 : row.price, brief: row.brief }
    : { id: null, title: '', category: 'theory', tech_domain: '', difficulty: '入门', price: 0, brief: '' })
  courseVisible.value = true
}

async function saveCourse() {
  if (!courseForm.title.trim()) return ElMessage.warning('课程名不能为空')
  saving.value = true
  const payload = { ...courseForm, title: courseForm.title.trim(), is_free: !courseForm.price }
  delete payload.id
  try {
    if (courseForm.id) await teacherUpdateCourse(courseForm.id, payload)
    else await teacherCreateCourse(payload)
    ElMessage.success(courseForm.id ? '已保存' : '课程已创建，当前为下架状态')
    courseVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function toggle(row, on) {
  if (on && !row.lesson_count) return ElMessage.warning('先在「目录」里添加课时再上架')
  try {
    await teacherUpdateCourse(row.id, { status: on ? 'on' : 'off' })
    row.status = on ? 'on' : 'off'
    ElMessage.success(on ? '已上架' : '已下架')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function openOutline(row) {
  current.value = row
  outlineVisible.value = true
}

function openQuizzes(row) {
  current.value = row
  quizzesVisible.value = true
}

async function openStudents(row) {
  current.value = row
  studentsVisible.value = true
  studentsLoading.value = true
  try {
    students.value = await teacherStudents(row.id)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    studentsLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-head .el-button {
  gap: 6px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.stats .panel + .panel {
  margin-top: 0;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat b {
  font-size: 26px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}

.prog {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prog .bar {
  flex: 1;
  margin: 0;
}

@media (max-width: 768px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
