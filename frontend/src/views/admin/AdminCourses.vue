<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 课程管理</p>
        <h1 class="page-title">课程管理</h1>
        <p class="lead">上下架、编辑信息和章节目录。修改课程会通知收藏了它的用户。</p>
      </div>
    </div>
    <div class="toolbar">
      <div class="flex gap-12">
        <el-input v-model="keyword" placeholder="搜索课程名" clearable :prefix-icon="SearchIcon" style="width: 220px" @keyup.enter="onSearch" @clear="onSearch" />
        <el-button type="primary" :icon="Plus" @click="openEdit(null)">新增课程</el-button>
      </div>
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="编号" width="90">
        <template #default="{ row }"><span class="mono text-sub">{{ courseCode(row) }}</span></template>
      </el-table-column>
      <el-table-column prop="title" label="课程名" min-width="180" show-overflow-tooltip />
      <el-table-column label="模块" width="90">
        <template #default="{ row }"><el-tag size="small" effect="plain">{{ categoryLabel(row.category) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="tech_domain" label="方向" width="90">
        <template #default="{ row }">{{ row.tech_domain || '-' }}</template>
      </el-table-column>
      <el-table-column prop="difficulty" label="难度" width="80">
        <template #default="{ row }">{{ row.difficulty || '-' }}</template>
      </el-table-column>
      <el-table-column label="价格" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.is_free" size="small" type="success">免费</el-tag>
          <span v-else class="price">¥{{ row.price }}</span>
        </template>
      </el-table-column>
      <el-table-column label="讲师" width="100">
        <template #default="{ row }">{{ row.lecturer?.name || row.lecturer_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="上架" width="80" align="center">
        <template #default="{ row }">
          <el-switch :model-value="row.status !== 'off'" @change="(v) => onToggle(row, v)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="primary" @click="openOutline(row)">目录</el-button>
          <el-button size="small" text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > size"
      v-model:current-page="page"
      :page-size="size"
      :total="total"
      layout="total, prev, pager, next"
      :pager-count="5"
      background
      @current-change="fetchList"
    />

    <el-dialog v-model="editVisible" :title="editRow ? '编辑课程' : '新增课程'" width="min(640px, 94vw)">
      <el-form label-width="90px">
        <el-form-item label="课程名" required>
          <el-input v-model="form.title" maxlength="100" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="模块" required>
              <el-select v-model="form.category" style="width: 100%">
                <el-option label="理论课程" value="theory" />
                <el-option label="实训课程" value="practice" />
                <el-option label="认证课程" value="certification" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width: 100%">
                <el-option v-for="d in ['入门','初级','中级','高级']" :key="d" :label="d" :value="d" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="技术方向">
              <el-input v-model="form.tech_domain" placeholder="如 AI/前端" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="封面图">
              <el-input v-model="form.cover" placeholder="图片地址，可留空" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否免费">
              <el-switch v-model="form.is_free" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="价格">
              <el-input-number v-model="form.price" :min="0" :disabled="form.is_free" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="讲师">
          <el-select v-model="form.lecturer_id" clearable placeholder="选择讲师" style="width: 100%">
            <el-option v-for="l in lecturers" :key="l.id" :label="`${l.name}（${l.title || '讲师'}）`" :value="l.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.brief" type="textarea" :rows="3" maxlength="500" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="on">上架</el-radio>
            <el-radio value="off">下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="outlineVisible" :title="`章节目录 · ${outlineCourse?.title || ''}`" size="min(720px, 100vw)" :close-on-click-modal="false">
      <div v-loading="outlineLoading" class="outline">
        <p class="text-sub">共 {{ outline.length }} 章 · {{ lessonCount }} 个课时。保存后会替换原目录，删掉的课时对应的学习进度会一起清除。</p>
        <div v-for="(ch, ci) in outline" :key="ch._k" class="panel ch">
          <div class="ch-head">
            <span class="mono no">{{ String(ci + 1).padStart(2, '0') }}</span>
            <el-input v-model="ch.title" placeholder="章节标题" maxlength="128" />
            <el-button-group>
              <el-button :disabled="ci === 0" aria-label="上移" @click="move(outline, ci, -1)"><AppIcon name="chevron-down" :size="14" class="up" /></el-button>
              <el-button :disabled="ci === outline.length - 1" aria-label="下移" @click="move(outline, ci, 1)"><AppIcon name="chevron-down" :size="14" /></el-button>
              <el-button aria-label="删除章节" @click="outline.splice(ci, 1)"><AppIcon name="trash" :size="14" /></el-button>
            </el-button-group>
          </div>
          <div v-for="(ls, li) in ch.lessons" :key="ls._k" class="ls">
            <div class="ls-row">
              <el-input v-model="ls.title" placeholder="课时标题" maxlength="128" class="ls-title" />
              <el-input v-model="ls.duration" placeholder="时长，如 12分钟" maxlength="16" class="ls-dur" />
              <el-select v-model="ls.kind" class="ls-kind">
                <el-option v-for="(label, k) in OUTLINE_KINDS" :key="k" :label="label" :value="k" />
              </el-select>
              <el-button-group>
                <el-button :disabled="li === 0" aria-label="上移课时" @click="move(ch.lessons, li, -1)"><AppIcon name="chevron-down" :size="14" class="up" /></el-button>
                <el-button aria-label="删除课时" @click="ch.lessons.splice(li, 1)"><AppIcon name="trash" :size="14" /></el-button>
              </el-button-group>
            </div>
            <el-input v-model="ls.content" type="textarea" :autosize="{ minRows: 2, maxRows: 8 }" placeholder="讲义正文（学员报名后可见），段落之间空一行" />
          </div>
          <el-button text type="primary" @click="addLesson(ch)"><AppIcon name="plus" :size="14" />加一个课时</el-button>
        </div>
        <el-button class="add-ch" @click="addChapter"><AppIcon name="plus" :size="16" />加一章</el-button>
      </div>
      <template #footer>
        <el-button @click="outlineVisible = false">取消</el-button>
        <el-button type="primary" :loading="outlineSaving" @click="onSaveOutline">保存目录</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppIcon from '../../components/icons/AppIcon.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search as SearchIcon, Plus } from '@element-plus/icons-vue'
import { adminGetCourses, adminCreateCourse, adminUpdateCourse, adminDeleteCourse, adminGetLecturers, adminGetOutline, adminSaveOutline } from '../../api/admin'
import { categoryLabel, courseCode, normalizePage } from '../../utils'

const keyword = ref('')
const page = ref(1)
const size = 15
const total = ref(0)
const items = ref([])
const loading = ref(false)
const lecturers = ref([])

const editVisible = ref(false)
const editRow = ref(null)
const saving = ref(false)
const form = reactive({
  title: '', category: 'theory', difficulty: '入门', tech_domain: '',
  cover: '', is_free: true, price: 0, lecturer_id: null, brief: '', status: 'on'
})

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const p = normalizePage(await adminGetCourses(params), size)
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  fetchList()
}

function openEdit(row) {
  editRow.value = row
  if (row) {
    Object.assign(form, {
      title: row.title || '',
      category: row.category || 'theory',
      difficulty: row.difficulty || '入门',
      tech_domain: row.tech_domain || '',
      cover: row.cover || '',
      is_free: !!row.is_free,
      price: row.price ?? 0,
      lecturer_id: row.lecturer?.id ?? row.lecturer_id ?? null,
      brief: row.brief || '',
      status: row.status || 'on'
    })
  } else {
    Object.assign(form, {
      title: '', category: 'theory', difficulty: '入门', tech_domain: '',
      cover: '', is_free: true, price: 0, lecturer_id: null, brief: '', status: 'on'
    })
  }
  editVisible.value = true
}

async function onSave() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写课程名')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.is_free) payload.price = 0
    if (editRow.value) await adminUpdateCourse(editRow.value.id, payload)
    else await adminCreateCourse(payload)
    ElMessage.success('已保存')
    editVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function onToggle(row, v) {
  try {
    await adminUpdateCourse(row.id, { status: v ? 'on' : 'off' })
    row.status = v ? 'on' : 'off'
    ElMessage.success(v ? '已上架' : '已下架')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除课程「${row.title}」？`, '删除课程', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await adminDeleteCourse(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || e)
  }
}

onMounted(async () => {
  fetchList()
  try {
    const p = normalizePage(await adminGetLecturers(), 50)
    lecturers.value = p.items
  } catch {
    /* 讲师下拉可选 */
  }
})

/* ---------- 章节目录 ---------- */
const OUTLINE_KINDS = { video: '视频', article: '图文', lab: '实验' }
const outlineVisible = ref(false)
const outlineLoading = ref(false)
const outlineSaving = ref(false)
const outlineCourse = ref(null)
const outline = ref([])
let keySeed = 0
const nextKey = () => ++keySeed
const lessonCount = computed(() => outline.value.reduce((n, ch) => n + ch.lessons.length, 0))

function move(list, i, d) {
  const j = i + d
  if (j < 0 || j >= list.length) return
  const [x] = list.splice(i, 1)
  list.splice(j, 0, x)
}

function addChapter() {
  outline.value.push({ _k: nextKey(), id: null, title: `第${outline.value.length + 1}章 `, lessons: [] })
}

function addLesson(ch) {
  ch.lessons.push({ _k: nextKey(), id: null, title: '', duration: '', kind: 'video', content: '' })
}

async function openOutline(row) {
  outlineCourse.value = row
  outline.value = []
  outlineVisible.value = true
  outlineLoading.value = true
  try {
    const data = (await adminGetOutline(row.id)) || []
    outline.value = data.map((ch) => ({
      _k: nextKey(),
      id: ch.id,
      title: ch.title,
      lessons: (ch.lessons || []).map((ls) => ({ _k: nextKey(), id: ls.id, title: ls.title, duration: ls.duration || '', kind: ls.kind === 'text' ? 'article' : ls.kind || 'video', content: ls.content || '', video_url: ls.video_url || '' }))
    }))
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    outlineLoading.value = false
  }
}

async function onSaveOutline() {
  for (const ch of outline.value) {
    if (!ch.title.trim()) return ElMessage.warning('有章节没写标题')
    if (ch.lessons.some((ls) => !ls.title.trim())) return ElMessage.warning(`「${ch.title}」里有课时没写标题`)
  }
  outlineSaving.value = true
  try {
    const payload = outline.value.map((ch) => ({
      id: ch.id || undefined,
      title: ch.title.trim(),
      lessons: ch.lessons.map((ls) => ({ id: ls.id || undefined, title: ls.title.trim(), duration: ls.duration || null, kind: ls.kind, content: ls.content, video_url: ls.video_url || '' }))
    }))
    await adminSaveOutline(outlineCourse.value.id, payload)
    ElMessage.success('目录已保存')
    outlineVisible.value = false
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    outlineSaving.value = false
  }
}
</script>

<style scoped>
.outline {
  display: grid;
  gap: 12px;
}

.outline .panel + .panel {
  margin-top: 0;
}

.ch {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.ch-head,
.ls-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ch-head .el-button-group,
.ls-row .el-button-group {
  display: flex;
  flex-shrink: 0;
}

.ch-head .no {
  color: var(--accent);
  font-size: 13px;
}

.ls {
  display: grid;
  gap: 6px;
  padding: 10px;
  border: 1px dashed var(--line);
  border-radius: var(--r);
}

.ls-title {
  flex: 1;
}

.ls-dur {
  width: 130px;
}

.ls-kind {
  width: 110px;
}

.up {
  transform: rotate(180deg);
}

.add-ch,
.ch .el-button.is-text {
  gap: 6px;
  justify-self: start;
}

@media (max-width: 640px) {
  .ls-row {
    flex-wrap: wrap;
  }

  .ls-title {
    flex-basis: 100%;
  }
}

</style>
