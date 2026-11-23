<template>
  <div class="page page-narrow" v-loading="loading">
    <template v-if="question">
      <button class="back" type="button" @click="$router.push('/community')">
        <AppIcon name="arrow-left" :size="16" />返回社区
      </button>

      <div class="page-head">
        <div>
          <p class="eyebrow">{{ answers.length }} 个回答 · {{ question.views ?? 0 }} 次浏览</p>
          <h1 class="page-title q-title">{{ question.title }}</h1>
          <div class="author">
            <UserAvatar :user="question.user" :size="24" />
            <span>{{ name(question.user) }}</span>
            <span class="mono text-sub">{{ fmtDate(question.created_at) }}</span>
          </div>
        </div>
        <el-button v-if="canDeleteQuestion" @click="onDeleteQuestion">
          <AppIcon name="trash" :size="16" />删除问题
        </el-button>
      </div>

      <div class="panel q-content pre-wrap">{{ question.content }}</div>

      <h2 class="section-title mt-24">回答</h2>
      <p v-if="!answers.length" class="text-sub">还没有人回答。</p>
      <div v-for="a in answers" :key="a.id" class="panel answer">
        <UserAvatar :user="a.user" :size="36" />
        <div class="answer-body">
          <div class="answer-head">
            <b>{{ name(a.user) }}</b>
            <span class="mono text-sub">{{ fmtDate(a.created_at) }}</span>
          </div>
          <div class="answer-content pre-wrap">{{ a.content }}</div>
        </div>
        <button v-if="canDelete(a.user)" class="icon-btn" type="button" aria-label="删除回答" @click="onDeleteAnswer(a)">
          <AppIcon name="trash" :size="16" />
        </button>
      </div>

      <form class="panel mt-16" @submit.prevent="onAnswer">
        <h2 class="panel-title">写回答</h2>
        <el-input v-model="answerText" type="textarea" :rows="5" maxlength="2000" show-word-limit placeholder="说说你的做法，能贴代码或步骤更好" aria-label="回答内容" />
        <el-button type="primary" native-type="submit" class="mt-12" :loading="submitting">
          <AppIcon name="send" :size="16" />提交回答
        </el-button>
      </form>
    </template>
    <el-empty v-else-if="!loading" description="问题不存在或已被删除">
      <el-button type="primary" @click="$router.push('/community')">返回社区</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getQuestionDetail, postAnswer, deleteQuestion, deleteAnswer } from '../../api/community'
import { fmtDate } from '../../utils'
import { useUserStore } from '../../stores/user'
import UserAvatar from '../../components/UserAvatar.vue'
import AppIcon from '../../components/icons/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const id = route.params.id

const loading = ref(true)
const detail = ref(null)
const answerText = ref('')
const submitting = ref(false)

const question = computed(() => detail.value?.question || detail.value)
const answers = computed(() => detail.value?.answers || [])
const name = (u) => u?.nickname || u?.username || '同学'
const canDelete = (u) => store.isAdmin || (u?.id && u.id === store.user?.id)
const canDeleteQuestion = computed(() => detail.value?.can_delete ?? canDelete(question.value?.user))

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getQuestionDetail(id)
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

async function onAnswer() {
  if (!answerText.value.trim()) {
    ElMessage.warning('回答内容不能为空')
    return
  }
  submitting.value = true
  try {
    await postAnswer(id, answerText.value.trim())
    answerText.value = ''
    ElMessage.success('已提交')
    fetchDetail()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

async function confirm(msg, title) {
  try {
    await ElMessageBox.confirm(msg, title, { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    return true
  } catch {
    return false
  }
}

async function onDeleteQuestion() {
  if (!(await confirm('问题和下面的回答会一起删除。', '删除问题'))) return
  try {
    await deleteQuestion(id)
    ElMessage.success('已删除')
    router.replace('/community')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDeleteAnswer(a) {
  if (!(await confirm('删除后不能恢复。', '删除回答'))) return
  try {
    await deleteAnswer(a.id)
    ElMessage.success('已删除')
    fetchDetail()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(fetchDetail)
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

.back:hover {
  color: var(--ink);
}

.q-title {
  font-size: 28px;
  line-height: 1.3;
}

.author {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  font-size: 14px;
}

.page-head .el-button,
form .el-button {
  gap: 6px;
}

.q-content {
  line-height: 1.8;
  font-size: 15px;
}

.answer {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.answer + .answer {
  margin-top: 8px;
}

.answer-body {
  flex: 1;
  min-width: 0;
}

.answer-head {
  display: flex;
  gap: 10px;
  align-items: baseline;
  flex-wrap: wrap;
}

.answer-content {
  margin-top: 6px;
  line-height: 1.75;
}
</style>
