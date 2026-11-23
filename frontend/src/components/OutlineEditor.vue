<template>
  <el-drawer :model-value="modelValue" :title="`章节目录 · ${course?.title || ''}`" size="min(760px, 100vw)" :close-on-click-modal="false" @update:model-value="(v) => emit('update:modelValue', v)" @open="load">
    <div v-loading="loading" class="outline">
      <p class="text-sub">共 {{ chapters.length }} 章 · {{ lessonCount }} 个课时。保存后替换原目录，删掉的课时对应的学习进度会一起清除。</p>
      <div v-for="(ch, ci) in chapters" :key="ch._k" class="panel ch">
        <div class="row">
          <span class="mono no">{{ String(ci + 1).padStart(2, '0') }}</span>
          <el-input v-model="ch.title" placeholder="章节标题" maxlength="128" />
          <el-button aria-label="删除章节" @click="chapters.splice(ci, 1)"><AppIcon name="trash" :size="14" /></el-button>
        </div>
        <div v-for="(ls, li) in ch.lessons" :key="ls._k" class="ls">
          <div class="row wrap">
            <el-input v-model="ls.title" placeholder="课时标题" maxlength="128" class="grow" />
            <el-input v-model="ls.duration" placeholder="时长，如 12分钟" maxlength="16" class="dur" />
            <el-select v-model="ls.kind" class="kind">
              <el-option label="视频" value="video" />
              <el-option label="图文" value="article" />
              <el-option label="实验" value="lab" />
            </el-select>
            <el-button aria-label="删除课时" @click="ch.lessons.splice(li, 1)"><AppIcon name="trash" :size="14" /></el-button>
          </div>
          <div v-if="ls.kind === 'video'" class="row wrap">
            <el-input v-model="ls.video_url" placeholder="视频地址：上传或填写 https 链接" class="grow" />
            <el-upload :show-file-list="false" accept="video/mp4,video/webm" :http-request="(o) => uploadVideo(ls, o.file)">
              <el-button :loading="ls._uploading">{{ ls._progress ? `${ls._progress}%` : '上传视频' }}</el-button>
            </el-upload>
          </div>
          <el-input v-model="ls.content" type="textarea" :autosize="{ minRows: 2, maxRows: 8 }" placeholder="讲义正文（报名后可见），段落之间空一行" />
        </div>
        <el-button text type="primary" @click="ch.lessons.push(blankLesson())"><AppIcon name="plus" :size="14" />加一个课时</el-button>
      </div>
      <el-button class="add" @click="chapters.push({ _k: key(), id: null, title: `第${chapters.length + 1}章 `, lessons: [] })"><AppIcon name="plus" :size="16" />加一章</el-button>
    </div>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存目录</el-button>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadFile } from '../api/upload'
import AppIcon from './icons/AppIcon.vue'

const props = defineProps({
  modelValue: Boolean,
  course: { type: Object, default: null },
  loader: { type: Function, required: true },
  saver: { type: Function, required: true }
})
const emit = defineEmits(['update:modelValue', 'saved'])

const loading = ref(false)
const saving = ref(false)
const chapters = ref([])
let seed = 0
const key = () => ++seed
const blankLesson = () => ({ _k: key(), id: null, title: '', duration: '', kind: 'video', content: '', video_url: '' })
const lessonCount = computed(() => chapters.value.reduce((n, ch) => n + ch.lessons.length, 0))

async function load() {
  if (!props.course) return
  loading.value = true
  chapters.value = []
  try {
    const data = (await props.loader(props.course.id)) || []
    chapters.value = data.map((ch) => ({
      _k: key(),
      id: ch.id,
      title: ch.title,
      lessons: (ch.lessons || []).map((ls) => ({ ...blankLesson(), id: ls.id, title: ls.title, duration: ls.duration || '', kind: ls.kind === 'text' ? 'article' : ls.kind || 'video', content: ls.content || '', video_url: ls.video_url || '' }))
    }))
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function uploadVideo(ls, file) {
  ls._uploading = true
  try {
    const res = await uploadFile('video', file, (p) => (ls._progress = p))
    ls.video_url = res.url
    ElMessage.success('视频已上传')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    ls._uploading = false
    ls._progress = 0
  }
}

async function save() {
  for (const ch of chapters.value) {
    if (!ch.title.trim()) return ElMessage.warning('有章节没写标题')
    if (ch.lessons.some((ls) => !ls.title.trim())) return ElMessage.warning(`「${ch.title}」里有课时没写标题`)
  }
  saving.value = true
  try {
    await props.saver(props.course.id, chapters.value.map((ch) => ({
      id: ch.id || undefined,
      title: ch.title.trim(),
      lessons: ch.lessons.map((ls) => ({ id: ls.id || undefined, title: ls.title.trim(), duration: ls.duration || null, kind: ls.kind, content: ls.content, video_url: ls.kind === 'video' ? ls.video_url.trim() : '' }))
    })))
    ElMessage.success('目录已保存')
    emit('saved')
    emit('update:modelValue', false)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
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

.row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.row.wrap {
  flex-wrap: wrap;
}

.grow {
  flex: 1;
  min-width: 180px;
}

.dur {
  width: 130px;
}

.kind {
  width: 100px;
}

.no {
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

.add,
.ch .el-button.is-text {
  justify-self: start;
  gap: 6px;
}
</style>
