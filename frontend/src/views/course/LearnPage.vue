<template>
  <div class="page" v-loading="loading">
    <template v-if="detail">
      <div class="page-head learn-head">
        <div class="head-main">
          <router-link :to="`/course/${courseId}`" class="back-link">
            <AppIcon name="arrow-left" :size="16" />
            <span>返回课程详情</span>
          </router-link>
          <p class="eyebrow">// {{ courseCode(course) }} · 已学 {{ doneIds.size }} / {{ flatLessons.length }} 课时</p>
          <h1 class="page-title learn-title">{{ course?.title }}</h1>
        </div>
        <div class="progress-box">
          <div class="flex-between text-sub"><span>课程进度</span><span class="mono">{{ progress }}%</span></div>
          <div class="bar"><i :style="{ width: progress + '%' }" /></div>
        </div>
      </div>

      <div class="learn-grid">
        <!-- 左侧目录 -->
        <aside class="toc">
          <div class="toc-title">课程目录</div>
          <div class="toc-body">
            <div v-for="(ch, i) in detail.chapters || []" :key="ch.id" class="toc-chapter">
              <div class="toc-ch-title"><span class="mono">{{ String(i + 1).padStart(2, '0') }}</span>{{ ch.title }}</div>
              <button
                v-for="ls in ch.lessons || []"
                :key="ls.id"
                type="button"
                class="toc-lesson"
                :class="{ active: current?.id === ls.id, done: doneIds.has(ls.id) }"
                @click="selectLesson(ls)"
              >
                <AppIcon v-if="doneIds.has(ls.id)" name="check-circle" :size="16" class="ic-done" />
                <AppIcon v-else :name="ls.kind === 'video' ? 'play' : 'doc'" :size="16" class="ic" />
                <span class="toc-ls-title">{{ ls.title }}</span>
                <span class="toc-ls-dur mono">{{ fmtMinutes(ls.duration) }}</span>
              </button>
            </div>
          </div>
        </aside>

        <!-- 右侧内容 -->
        <section v-if="current" class="content">
          <div class="content-head">
            <h2 class="content-title">{{ current.title }}</h2>
            <span class="tag">{{ LESSON_KIND[current.kind] || current.kind || '图文' }}</span>
            <span class="tag tag-line mono">{{ fmtMinutes(current.duration) }}</span>
          </div>

          <!-- 视频：有地址时播放真实视频，否则显示占位 -->
          <video
            v-if="current.kind === 'video' && current.video_url"
            :key="current.id"
            class="video-player"
            :src="current.video_url"
            controls
            preload="metadata"
            controlslist="nodownload"
          ></video>
          <div v-else-if="current.kind === 'video'" class="mock-player">
            <AppIcon name="play" :size="48" :stroke="1.4" />
            <div class="mock-tip">这节课还没有上传视频，先看下方讲义</div>
            <div class="mock-bar"><i :style="{ width: playPercent + '%' }" /></div>
          </div>

          <!-- 讲义正文 -->
          <article class="text-content">
            <h3 class="sub-title">讲义</h3>
            <template v-if="paragraphs.length">
              <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
            </template>
            <p v-else class="no-content">本课时暂无讲义</p>
          </article>

          <div class="content-foot">
            <div class="text-sub mono">本次已学 {{ elapsedText }}</div>
            <div class="foot-actions">
              <el-button v-if="nextLesson" @click="selectLesson(nextLesson)">
                下一课时
                <AppIcon name="arrow-right" :size="16" />
              </el-button>
              <el-button v-if="!doneIds.has(current.id)" type="primary" :loading="completing" @click="onComplete">
                <AppIcon name="check" :size="16" />
                <span class="btn-text">完成本课时</span>
              </el-button>
              <span v-else class="tag tag-accent done-tag"><AppIcon name="check" :size="14" />已完成</span>
            </div>
          </div>
        </section>

        <section v-else class="content">
          <el-empty description="从左侧目录选一个课时开始" />
        </section>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="无法加载课程信息">
      <el-button type="primary" @click="$router.push('/courses/theory')">返回课程中心</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCourseDetail, completeLesson } from '../../api/course'
import { fmtMinutes, LESSON_KIND, courseCode } from '../../utils'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const courseId = route.params.courseId

const loading = ref(true)
const detail = ref(null)
const current = ref(null)
const doneIds = ref(new Set())
const progress = ref(0)
const completing = ref(false)
const startAt = ref(Date.now())
const playPercent = ref(0)
const tick = ref(0)

let timer = null

const course = computed(() => detail.value?.course || detail.value)

const flatLessons = computed(() => {
  const arr = []
  for (const ch of detail.value?.chapters || []) {
    for (const ls of ch.lessons || []) arr.push(ls)
  }
  return arr
})

const nextLesson = computed(() => {
  if (!current.value) return null
  const i = flatLessons.value.findIndex((l) => l.id === current.value.id)
  return i >= 0 && i < flatLessons.value.length - 1 ? flatLessons.value[i + 1] : null
})

// 讲义：纯文本按空行/换行切成段落
const paragraphs = computed(() => {
  const raw = String(current.value?.content || '').trim()
  if (!raw) return []
  return raw
    .split(/\n\s*\n|\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
})

const elapsedText = computed(() => {
  tick.value // 依赖 tick 触发每秒刷新
  const s = Math.floor((Date.now() - startAt.value) / 1000)
  if (s < 60) return `${s} 秒`
  return `${Math.floor(s / 60)} 分钟`
})

function selectLesson(ls) {
  current.value = ls
  startAt.value = Date.now()
  playPercent.value = 0
  if (route.query.lesson !== String(ls.id)) {
    router.replace({ query: { ...route.query, lesson: ls.id } })
  }
}

async function onComplete() {
  const seconds = Math.min(7200, Math.max(1, Math.round((Date.now() - startAt.value) / 1000)))
  completing.value = true
  try {
    const res = await completeLesson(current.value.id, seconds)
    doneIds.value = new Set([...doneIds.value, current.value.id])
    if (typeof res?.progress === 'number') progress.value = res.progress
    ElMessage.success('本课时已完成')
    if (nextLesson.value) {
      setTimeout(() => selectLesson(nextLesson.value), 400)
    } else if (progress.value >= 100) {
      ElMessage.success('这门课的全部课时都学完了')
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    completing.value = false
  }
}

onMounted(async () => {
  try {
    detail.value = await getCourseDetail(courseId)
    if (!detail.value?.is_enrolled) {
      ElMessage.warning('请先报名课程')
      router.replace(`/course/${courseId}`)
      return
    }
    doneIds.value = new Set(detail.value.lesson_status || [])
    progress.value = detail.value.progress ?? 0
    // 优先选中 query 指定课时 → 第一个未完成 → 第一节
    const q = Number(route.query.lesson)
    const list = flatLessons.value
    const target = list.find((l) => l.id === q) || list.find((l) => !doneIds.value.has(l.id)) || list[0]
    if (target) selectLesson(target)
    timer = setInterval(() => {
      if (playPercent.value < 100) playPercent.value += 0.5
      tick.value++
    }, 1000)
  } catch (e) {
    detail.value = null
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.learn-head {
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

.learn-title {
  font-size: 30px;
}

.progress-box {
  width: 280px;
  flex-shrink: 0;
}

.progress-box .bar {
  margin-top: 8px;
}

.learn-grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  align-items: start;
}

.toc {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--r);
  overflow: hidden;
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 88px;
}

.toc-title {
  padding: 14px 16px;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid var(--line);
}

.toc-body {
  overflow-y: auto;
  padding: 8px;
}

.toc-ch-title {
  display: flex;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  padding: 12px 8px 6px;
}

.toc-ch-title .mono {
  color: var(--accent);
}

.toc-lesson {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 8px 10px;
  border: 0;
  border-left: 2px solid transparent;
  border-radius: var(--r);
  background: transparent;
  color: var(--ink-2);
  font-size: 13.5px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.toc-lesson:hover {
  background: var(--surface);
  color: var(--ink);
}

.toc-lesson.active {
  background: var(--tint);
  color: var(--accent);
  border-left-color: var(--accent);
}

.toc-lesson .ic {
  color: var(--faint);
}

.toc-lesson.active .ic,
.ic-done {
  color: var(--accent);
}

.toc-lesson.done:not(.active) .toc-ls-title {
  color: var(--muted);
}

.toc-ls-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toc-ls-dur {
  font-size: 11px;
  color: var(--faint);
}

.content {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 22px 24px;
  min-height: 480px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
  flex-wrap: wrap;
}

.content-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  flex: 1;
  min-width: 200px;
}

.video-player {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
  border: 1px solid var(--line);
  border-radius: var(--r);
}

.mock-player {
  margin-top: 18px;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: var(--r);
  aspect-ratio: 16 / 7;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: var(--accent);
  padding: 16px;
}

.mock-tip {
  font-size: 13px;
  color: var(--muted);
  text-align: center;
}

.mock-bar {
  width: 70%;
  height: 3px;
  background: var(--surface);
  overflow: hidden;
}

.mock-bar i {
  display: block;
  height: 100%;
  background: var(--accent);
  transition: width 1s linear;
}

.text-content {
  margin-top: 20px;
  line-height: 1.85;
  font-size: 15px;
  color: var(--ink-2);
  max-width: 72ch;
}

.sub-title {
  font: 500 12px var(--mono);
  letter-spacing: 0.08em;
  color: var(--muted);
  margin: 0 0 10px;
}

.text-content p {
  margin: 0 0 14px;
}

.no-content {
  color: var(--muted);
  padding: 24px 0;
}

.content-foot {
  margin-top: auto;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.foot-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.foot-actions .el-button .app-icon {
  margin-left: 4px;
}

.btn-text {
  margin-left: 6px;
}

.done-tag {
  gap: 4px;
  height: 32px;
  padding: 0 12px;
}

@media (max-width: 900px) {
  .learn-grid {
    grid-template-columns: 1fr;
  }

  .toc {
    position: static;
    max-height: 320px;
  }

  .progress-box {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .learn-title {
    font-size: 24px;
  }

  .content {
    padding: 18px 16px;
  }

  .toc-lesson {
    min-height: 44px;
  }

  .foot-actions {
    width: 100%;
  }

  .foot-actions > * {
    flex: 1;
    min-height: 44px;
  }

  .foot-actions .el-button + .el-button {
    margin-left: 0;
  }
}
</style>
