<template>
  <div class="page admin-page">
    <div class="admin-wrap">
      <aside class="panel admin-aside">
        <p class="eyebrow aside-title">后台管理</p>
        <nav class="admin-nav" aria-label="后台菜单">
          <router-link v-for="m in menu" :key="m.path" :to="m.path" class="nav-item" active-class="on">
            <AppIcon :name="m.icon" :size="17" /><span>{{ m.label }}</span>
          </router-link>
        </nav>
      </aside>

      <div class="admin-main">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import AppIcon from '../../components/icons/AppIcon.vue'

const menu = [
  { path: '/admin/dashboard', label: '数据看板', icon: 'chart' },
  { path: '/admin/users', label: '用户', icon: 'users' },
  { path: '/admin/courses', label: '课程', icon: 'book' },
  { path: '/admin/lecturers', label: '讲师', icon: 'user' },
  { path: '/admin/jobs', label: '职位', icon: 'briefcase' },
  { path: '/admin/orders', label: '订单', icon: 'receipt' },
  { path: '/admin/applications', label: '职位申请', icon: 'clipboard' },
  { path: '/admin/community', label: '社区', icon: 'community' }
]
</script>

<style scoped>
.admin-wrap {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.admin-aside {
  position: sticky;
  top: 88px;
  padding: 16px 10px;
}

.aside-title {
  padding: 0 10px;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 42px;
  padding: 0 12px;
  border-radius: var(--r);
  border-left: 2px solid transparent;
  color: var(--muted);
  font-weight: 500;
  font-size: 14px;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--surface);
  color: var(--ink);
}

.nav-item.on {
  background: var(--tint);
  color: var(--accent);
  border-left-color: var(--accent);
}


.admin-main {
  min-width: 0;
}

@media (max-width: 960px) {
  .admin-wrap {
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
  }

  .admin-aside {
    min-width: 0;
  }

  .admin-aside {
    position: static;
    padding: 6px;
  }

  .aside-title,

  .admin-nav {
    flex-direction: row;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .admin-nav::-webkit-scrollbar {
    display: none;
  }

  .nav-item {
    flex-shrink: 0;
    min-height: 44px;
    border-left: 0;
    border-bottom: 2px solid transparent;
  }

  .nav-item.on {
    border-bottom-color: var(--accent);
  }
}
</style>
