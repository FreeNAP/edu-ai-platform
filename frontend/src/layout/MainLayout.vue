<template>
  <div class="layout">
    <header class="top">
      <div class="top-in">
        <router-link to="/" class="brand" aria-label="智慧教育平台首页">
          <BrandMark :size="28" />
          <span>智慧教育平台</span>
        </router-link>

        <nav class="top-nav" aria-label="主导航">
          <router-link v-for="n in navItems" :key="n.to" :to="n.to" :class="{ on: isActive(n) }">{{ n.label }}</router-link>
        </nav>

        <div class="top-r">
          <router-link to="/notifications" class="icon-btn" :aria-label="`通知${store.unreadCount ? `，${store.unreadCount} 条未读` : ''}`">
            <AppIcon name="bell" />
            <i v-if="store.unreadCount" class="badge">{{ store.unreadCount > 99 ? '99+' : store.unreadCount }}</i>
          </router-link>

          <el-dropdown trigger="click" class="wide-only" @command="onCommand">
            <button class="user-entry" type="button" aria-label="账号菜单">
              <UserAvatar :user="store.user" :size="32" />
              <span class="username">{{ store.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="me"><AppIcon name="user" :size="16" />个人中心</el-dropdown-item>
                <el-dropdown-item v-if="store.isAdmin" command="admin"><AppIcon name="settings" :size="16" />后台管理</el-dropdown-item>
                <el-dropdown-item command="logout" divided><AppIcon name="logout" :size="16" />退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <button
            class="icon-btn menu-btn narrow-only"
            type="button"
            :aria-expanded="drawer ? 'true' : 'false'"
            aria-controls="mobile-nav"
            :aria-label="drawer ? '关闭菜单' : '打开菜单'"
            @click="drawer = !drawer"
          >
            <AppIcon :name="drawer ? 'close' : 'menu'" :size="22" />
          </button>
        </div>
      </div>
    </header>

    <!-- 移动端全屏导航 -->
    <transition name="mnav">
      <div v-if="drawer" id="mobile-nav" class="m-nav" role="dialog" aria-label="导航菜单">
        <div class="m-user">
          <UserAvatar :user="store.user" :size="40" />
          <div>
            <b>{{ store.displayName }}</b>
            <small>{{ store.user?.email }}</small>
          </div>
        </div>
        <nav class="m-links">
          <router-link v-for="n in mobileItems" :key="n.to" :to="n.to" :class="{ on: isActive(n) }">
            <AppIcon :name="n.icon" />
            <span>{{ n.label }}</span>
          </router-link>
          <button type="button" class="m-logout" @click="onCommand('logout')">
            <AppIcon name="logout" />
            <span>退出登录</span>
          </button>
        </nav>
        <p class="author-line m-author">QQ 3074423966 · 抖音号 HAQI2026</p>
      </div>
    </transition>

    <main class="main">
      <router-view />
    </main>

    <footer class="foot">
      <div class="foot-in">
        <span>智慧教育平台 · 华为 ICT 学院课程项目</span>
        <span class="author-line">QQ 3074423966 · 抖音号 HAQI2026</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import UserAvatar from '../components/UserAvatar.vue'
import AppIcon from '../components/icons/AppIcon.vue'
import BrandMark from '../components/icons/BrandMark.vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const drawer = ref(false)

const navItems = [
  { to: '/courses/theory', label: '理论课程', icon: 'book' },
  { to: '/courses/practice', label: '实训课程', icon: 'grid' },
  { to: '/courses/certification', label: '认证课程', icon: 'check-circle' },
  { to: '/jobs', label: '实习就业', icon: 'briefcase', prefix: ['/job', '/interview'] },
  { to: '/ai', label: 'AI 助手', icon: 'spark' },
  { to: '/community', label: '社区', icon: 'community' }
]

const mobileItems = computed(() => [
  ...navItems,
  { to: '/notifications', label: '通知中心', icon: 'bell' },
  { to: '/me', label: '个人中心', icon: 'user' },
  ...(store.isAdmin ? [{ to: '/admin', label: '后台管理', icon: 'settings' }] : [])
])

function isActive(n) {
  const p = route.path
  if (p === n.to || p.startsWith(n.to + '/')) return true
  return (n.prefix || []).some((x) => p.startsWith(x + '/'))
}

async function onCommand(cmd) {
  drawer.value = false
  if (cmd === 'me') router.push('/me')
  else if (cmd === 'admin') router.push('/admin')
  else if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning'
      })
      store.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      /* 取消 */
    }
  }
}

function onKey(e) {
  if (e.key === 'Escape') drawer.value = false
}

watch(drawer, (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
})

onMounted(() => {
  store.refreshUnread()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
watch(
  () => route.fullPath,
  () => {
    drawer.value = false
    store.refreshUnread()
  }
)
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top {
  position: sticky;
  top: 0;
  z-index: 100;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}

.top-in {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 32px;
  display: flex;
  align-items: center;
  gap: 36px;
  height: 64px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: -0.01em;
  white-space: nowrap;
  color: var(--ink);
}

.top-nav {
  display: flex;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.top-nav a {
  padding: 8px 12px;
  border-radius: var(--r);
  color: var(--muted);
  font-weight: 500;
  white-space: nowrap;
  transition: color 0.15s, background 0.15s;
}

.top-nav a:hover,
.top-nav a.on {
  color: var(--ink);
  background: var(--surface);
}

.top-nav a.on {
  box-shadow: inset 0 -2px 0 var(--accent);
}

.top-r {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge {
  position: absolute;
  top: 3px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: var(--accent);
  color: var(--accent-ink);
  font: 500 10px/16px var(--mono);
  font-style: normal;
  text-align: center;
}

.user-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 8px 0 4px;
  border: 1px solid transparent;
  border-radius: var(--r);
  background: transparent;
  color: var(--ink);
  cursor: pointer;
  transition: background 0.15s;
}

.user-entry:hover {
  background: var(--surface);
}

.username {
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-btn {
  width: 44px;
  height: 44px;
}

.m-nav {
  position: fixed;
  inset: 64px 0 0;
  z-index: 99;
  background: var(--bg);
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.m-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 4px 16px;
  border-bottom: 1px solid var(--line);
}

.m-user b {
  display: block;
  font-size: 15px;
}

.m-user small {
  color: var(--muted);
  font-size: 12px;
}

.m-links {
  display: flex;
  flex-direction: column;
  padding: 8px 0;
}

.m-links a,
.m-logout {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 48px;
  padding: 0 12px;
  border-radius: var(--r);
  color: var(--ink-2);
  font-size: 16px;
  font-weight: 500;
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
}

.m-links a.on {
  background: var(--tint);
  color: var(--accent);
}

.m-logout {
  margin-top: 8px;
  border-top: 1px solid var(--line);
  border-radius: 0;
  color: var(--muted);
}

.m-author {
  margin-top: auto;
  padding: 16px 12px 8px;
}

.mnav-enter-active,
.mnav-leave-active {
  transition: opacity 0.15s ease;
}

.mnav-enter-from,
.mnav-leave-to {
  opacity: 0;
}

.main {
  flex: 1;
}

.foot {
  border-top: 1px solid var(--line);
  margin-top: 24px;
}

.foot-in {
  max-width: 1240px;
  margin: 0 auto;
  padding: 20px 32px;
  color: var(--muted);
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 1100px) {
  .top-in {
    gap: 20px;
  }

  .top-nav a {
    padding: 8px 8px;
  }
}

.narrow-only {
  display: none;
}

@media (max-width: 860px) {
  .top-nav,
  .wide-only {
    display: none;
  }

  .narrow-only {
    display: inline-grid;
  }
}

@media (max-width: 768px) {
  .top-in {
    padding: 0 12px 0 16px;
  }

  .foot-in {
    padding: 20px 16px;
    flex-direction: column;
  }
}
</style>
