<template>
  <div class="page" v-loading="loading">
    <template v-if="course">
      <!-- 课程信息区 -->
      <div class="page-head detail-head">
        <div class="head-grid">
          <div class="head-cover-wrap">
            <CourseCover :course="course" :height="232" />
          </div>
          <div class="head-info">
            <p class="eyebrow">{{ categoryLabel(course.category) }}<template v-if="course.tech_domain"> · {{ course.tech_domain }}</template> · {{ course.difficulty || '通用' }}</p>
            <h1 class="page-title course-title">{{ course.title }}</h1>
            <p class="lead">{{ course.brief || '暂无简介' }}</p>
            <div class="stats">
              <span>评分 <b>{{ Number(course.rating ?? 0).toFixed(1) }}</b></span>
              <span><b>{{ Number(course.students_count ?? 0).toLocaleString() }}</b> 人在学</span>
              <span><b>{{ totalLessons }}</b> 课时</span>
              <span v-if="detail.lecturer">讲师 <b>{{ detail.lecturer.name }}</b></span>
            </div>
            <div v-if="detail.is_enrolled" class="progress-line">
              <div class="flex-between text-sub"><span>学习进度</span><span class="mono">{{ detail.progress ?? 0 }}%</span></div>
              <div class="bar"><i :style="{ width: (detail.progress ?? 0) + '%' }" /></div>
            </div>
            <div class="actions">
              <span v-if="course.is_free" class="tag tag-accent price-free">免费</span>
              <span v-else class="price big-price">¥{{ course.price }}</span>
              <el-button type="primary" size="large" :loading="enrolling" @click="onLearn">
                <AppIcon name="play" :size="16" />
                <span class="btn-text">{{ detail.is_enrolled ? '继续学习' : course.is_free ? '报名并开始学习' : '购买课程' }}</span>
              </el-button>
              <el-button size="large" :class="{ 'is-fav': detail.is_favorited }" @click="onFavorite">
                <AppIcon name="star" :size="16" />
                <span class="btn-text">{{ detail.is_favorited ? '已收藏' : '收藏' }}</span>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="card">
        <el-tabs v-model="tab">
          <el-tab-pane label="课程简介" name="intro">
            <div class="pre-wrap intro-text">{{ course.brief || '暂无简介' }}</div>
            <template v-if="course.description">
              <el-divider />
              <div class="pre-wrap intro-text">{{ course.description }}</div>
            </template>
          </el-tab-pane>

          <el-tab-pane :label="`章节目录（${totalLessons}）`" name="chapters">
            <el-empty v-if="!detail.chapters?.length" description="章节信息整理中" />
            <div v-else class="chapter-list">
              <div v-for="(ch, i) in detail.chapters" :key="ch.id" class="chapter">
                <div class="chapter-title">
                  <span class="chapter-no">{{ String(i + 1).padStart(2, '0') }}</span>
                  {{ ch.title }}
                </div>
                <div
                  v-for="ls in ch.lessons || []"
                  :key="ls.id"
                  class="lesson clickable"
                  @click="onLessonClick(ls)"
                >
                  <span class="lesson-left">
                    <AppIcon v-if="doneIds.has(ls.id)" name="check-circle" class="ic-done" />
                    <AppIcon v-else :name="ls.kind === 'video' ? 'play' : 'doc'" class="ic-muted" />
                    <span>{{ ls.title }}</span>
                    <span class="tag kind-tag">{{ LESSON_KIND[ls.kind] || ls.kind }}</span>
                  </span>
                  <span class="text-sub mono">{{ fmtMinutes(ls.duration) }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="讲师信息" name="lecturer">
            <div v-if="detail.lecturer" class="lecturer-box">
              <UserAvatar :user="{ avatar: detail.lecturer.avatar }" :size="64" />
              <div>
                <div class="lecturer-name">
                  {{ detail.lecturer.name }}
                  <span v-if="detail.lecturer.title" class="tag">{{ detail.lecturer.title }}</span>
                </div>
                <p class="pre-wrap text-sub lecturer-bio">{{ detail.lecturer.bio || '讲师介绍整理中' }}</p>
              </div>
            </div>
            <el-empty v-else description="暂无讲师信息" />
          </el-tab-pane>

          <el-tab-pane :label="`评价（${comments.length}）`" name="comments">
            <div v-if="detail.is_enrolled" class="comment-form">
              <div class="flex gap-12 mb-16">
                <span class="text-sub">我的评分</span>
                <el-rate v-model="commentForm.rating" />
              </div>
              <el-input
                v-model="commentForm.content"
                type="textarea"
                :rows="3"
                maxlength="500"
                show-word-limit
                placeholder="说说这门课哪里讲得好、哪里还可以改进"
              />
              <el-button type="primary" class="mt-12" :loading="commenting" @click="onComment">发表评价</el-button>
            </div>
            <el-alert v-else type="info" :closable="false" show-icon class="mb-16" title="报名课程后即可发表评价" />

            <el-empty v-if="!comments.length" description="还没有评价" />
            <div v-else class="comment-list">
              <div v-for="c in comments" :key="c.id" class="comment">
                <UserAvatar :user="c.user" :size="38" />
                <div class="comment-body">
                  <div class="flex gap-12">
                    <span class="comment-name">{{ c.user?.nickname || c.user?.username || '同学' }}</span>
                    <el-rate :model-value="c.rating" disabled size="small" />
                  </div>
                  <p class="pre-wrap comment-content">{{ c.content }}</p>
                  <span class="text-sub">{{ fmtDate(c.created_at) }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="课程不存在或已下架">
      <el-button type="primary" @click="$router.push('/courses/theory')">返回课程中心</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCourseDetail,
  toggleCourseFavorite,
  enrollCourse,
  getCourseComments,
  postCourseComment
} from '../../api/course'
import { categoryLabel, difficultyType, fmtMinutes, fmtDate, LESSON_KIND } from '../../utils'
import CourseCover from '../../components/CourseCover.vue'
import UserAvatar from '../../components/UserAvatar.vue'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const loading = ref(true)
const detail = ref(null)
const tab = ref('intro')
const enrolling = ref(false)
const commenting = ref(false)
const commentForm = reactive({ rating: 5, content: '' })

const course = computed(() => detail.value?.course || detail.value)
const comments = computed(() => detail.value?.comments || [])
const doneIds = computed(() => new Set(detail.value?.lesson_status || []))
const totalLessons = computed(() =>
  (detail.value?.chapters || []).reduce((a, ch) => a + (ch.lessons?.length || 0), 0)
)

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getCourseDetail(id)
  } catch (e) {
    detail.value = null
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function onFavorite() {
  try {
    const res = await toggleCourseFavorite(id)
    detail.value.is_favorited = res?.favorited
    ElMessage.success(res?.favorited ? '已加入收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onLearn() {
  if (detail.value.is_enrolled) {
    router.push(`/learn/${id}`)
    return
  }
  enrolling.value = true
  try {
    const res = await enrollCourse(id)
    if (res?.enrolled) {
      ElMessage.success('报名成功，开始学习吧')
      await fetchDetail()
      router.push(`/learn/${id}`)
    } else if (res?.order) {
      const amount = res.order.amount ?? course.value?.price
      await ElMessageBox.confirm(
        `该课程为付费课程（¥${amount}），已生成待支付订单，请前往「个人中心 - 我的订单」完成支付。`,
        '创建订单成功',
        { confirmButtonText: '去支付', cancelButtonText: '稍后再说', type: 'info' }
      )
      router.push('/me?tab=orders')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || e)
  } finally {
    enrolling.value = false
  }
}

function onLessonClick(ls) {
  if (!detail.value.is_enrolled) {
    ElMessage.warning('请先报名课程')
    return
  }
  router.push(`/learn/${id}?lesson=${ls.id}`)
}

async function onComment() {
  if (!commentForm.content.trim()) {
    ElMessage.warning('请填写评价内容')
    return
  }
  commenting.value = true
  try {
    await postCourseComment(id, { rating: commentForm.rating, content: commentForm.content.trim() })
    commentForm.content = ''
    ElMessage.success('评价发表成功')
    detail.value.comments = await getCourseComments(id)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    commenting.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.detail-head {
  display: block;
}

.head-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 32px;
  align-items: start;
}

.head-cover-wrap {
  border: 1px solid var(--line);
  border-radius: var(--r);
  overflow: hidden;
}

.head-cover-wrap :deep(.course-cover) {
  border-bottom: 0;
}

.course-title {
  font-size: 32px;
}

.stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin: 16px 0 0;
  color: var(--muted);
  font: 400 13px var(--mono);
}

.stats b {
  color: var(--ink);
  font-weight: 500;
}

.progress-line {
  margin-top: 16px;
  max-width: 420px;
}

.progress-line .bar {
  margin-top: 6px;
}

.actions {
  margin-top: 22px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.actions .el-button + .el-button {
  margin-left: 0;
}

.btn-text {
  margin-left: 6px;
}

.big-price {
  font-size: 22px;
  margin-right: 8px;
}

.price-free {
  font-size: 13px;
  padding: 4px 10px;
  margin-right: 8px;
}

.is-fav {
  --el-button-text-color: var(--accent);
  --el-button-border-color: var(--el-color-primary-light-7);
}

.intro-text {
  line-height: 1.85;
  color: var(--ink-2);
}

.chapter {
  border: 1px solid var(--line);
  border-radius: var(--r);
  margin-bottom: 12px;
  overflow: hidden;
}

.chapter-title {
  background: var(--surface);
  padding: 12px 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-no {
  color: var(--accent);
  font: 500 12px var(--mono);
}

.lesson {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 46px;
  padding: 10px 16px;
  border-top: 1px solid var(--line);
  transition: background 0.15s;
}

.lesson:hover {
  background: #1c1c1c;
}

.lesson-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.ic-done {
  color: var(--accent);
}

.ic-muted {
  color: var(--faint);
}

.kind-tag {
  margin-left: 4px;
}

.lecturer-box {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.lecturer-name {
  font-size: 17px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.lecturer-bio {
  margin-top: 8px;
  line-height: 1.8;
}

.comment {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}

.comment:last-child {
  border-bottom: none;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-name {
  font-weight: 600;
}

.comment-content {
  margin: 6px 0;
  line-height: 1.7;
  color: var(--ink-2);
}

@media (max-width: 960px) {
  .head-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .course-title {
    font-size: 26px;
  }

  .actions .el-button {
    flex: 1 1 100%;
    height: 44px;
  }

  .lesson-left .kind-tag {
    display: none;
  }
}
</style>
