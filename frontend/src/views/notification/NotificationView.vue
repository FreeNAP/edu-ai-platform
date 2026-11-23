<template>
  <div class="page page-narrow">
    <div class="page-head">
      <div>
        <p class="eyebrow">通知 · {{ unread }} 条未读</p>
        <h1 class="page-title">通知中心</h1>
        <p class="lead">收藏的课程和职位有更新、申请状态变化、订单支付和学习计划到期，都会发到这里。</p>
      </div>
      <el-button :disabled="!unread" @click="onReadAll">全部标为已读</el-button>
    </div>

    <div class="seg mb-16 type-seg">
      <button type="button" :class="{ on: !filter }" @click="filter = ''">全部</button>
      <button v-for="(label, key) in TYPES" :key="key" type="button" :class="{ on: filter === key }" @click="filter = key">{{ label }}</button>
    </div>

    <div v-loading="loading" class="list">
      <el-empty v-if="!shown.length && !loading" description="这里还没有通知" />
      <button
        v-for="n in shown"
        :key="n.id"
        type="button"
        class="panel item hover-card"
        :class="{ unread: !n.is_read }"
        @click="onOpen(n)"
      >
        <span class="ico"><AppIcon :name="ICONS[n.type] || 'bell'" :size="18" /></span>
        <span class="body">
          <span class="row">
            <b>{{ n.title }}</b>
            <span class="mono text-sub">{{ fmtDate(n.created_at) }}</span>
          </span>
          <span class="content pre-wrap">{{ n.content }}</span>
          <span class="meta mono">{{ NOTIFY_TYPES[n.type] || '系统' }}<template v-if="target(n)"> · 点击查看</template></span>
        </span>
        <span v-if="!n.is_read" class="dot" aria-label="未读"></span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../../api/notification'
import { useUserStore } from '../../stores/user'
import { fmtDate, NOTIFY_TYPES } from '../../utils'
import AppIcon from '../../components/icons/AppIcon.vue'

const router = useRouter()
const store = useUserStore()
const loading = ref(true)
const items = ref([])
const filter = ref('')

const TYPES = { course: '课程', job: '职位', application: '申请', order: '订单', study: '学习', community: '社区' }
const ICONS = { course: 'book', job: 'briefcase', application: 'clipboard', order: 'receipt', study: 'calendar', community: 'community', system: 'info' }
const TARGETS = {
  course: { path: '/me', query: { tab: 'favorites' } },
  job: { path: '/me', query: { tab: 'favorites' } },
  application: { path: '/me', query: { tab: 'applications' } },
  order: { path: '/me', query: { tab: 'orders' } },
  study: { path: '/me', query: { tab: 'plans' } },
  community: { path: '/community' }
}

const unread = computed(() => items.value.filter((n) => !n.is_read).length)
const shown = computed(() => (filter.value ? items.value.filter((n) => n.type === filter.value) : items.value))
const target = (n) => TARGETS[n.type]

async function fetchList() {
  loading.value = true
  try {
    const res = await getNotifications()
    items.value = res?.items || []
    store.unreadCount = res?.unread_count ?? unread.value
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function onOpen(n) {
  if (!n.is_read) {
    try {
      await markNotificationRead(n.id)
      n.is_read = true
      store.unreadCount = Math.max(0, store.unreadCount - 1)
    } catch (e) {
      ElMessage.error(e.message)
      return
    }
  }
  if (target(n)) router.push(target(n))
}

async function onReadAll() {
  try {
    await markAllNotificationsRead()
    items.value.forEach((n) => (n.is_read = true))
    store.unreadCount = 0
    ElMessage.success('已全部标为已读')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(fetchList)
</script>

<style scoped>
.type-seg {
  flex-wrap: wrap;
}

.list {
  display: grid;
  gap: 8px;
  min-height: 120px;
}

.list .panel + .panel {
  margin-top: 0;
}

.item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  width: 100%;
  text-align: left;
  font: inherit;
  color: var(--ink);
  cursor: pointer;
  padding: 16px;
  position: relative;
}

.item.unread {
  border-left: 2px solid var(--accent);
}

.ico {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: var(--r);
  color: var(--muted);
}

.item.unread .ico {
  color: var(--accent);
  border-color: var(--accent);
}

.body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.content {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}

.meta {
  font-size: 12px;
  color: var(--muted);
}

.dot {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 6px;
  height: 6px;
  background: var(--accent);
}
</style>
