<template>
  <div class="user-avatar" :style="style" :title="name">
    <img v-if="isUrl && !broken" :src="avatar" class="avatar-img" alt="" @error="broken = true" />
    <AvatarPattern v-else-if="builtin" :index="builtin" />
    <svg v-else viewBox="0 0 24 24" class="avatar-silhouette" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
      <circle cx="12" cy="9.5" r="3.6" />
      <path d="M5.5 19.5c1.2-3.3 3.7-5 6.5-5s5.3 1.7 6.5 5" />
    </svg>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { isUrlAvatar, builtinIndex } from '../utils'
import AvatarPattern from './icons/AvatarPattern.vue'

const props = defineProps({
  user: { type: Object, default: () => ({}) },
  size: { type: Number, default: 36 }
})

const broken = ref(false)
const avatar = computed(() => (props.user?.avatar || '').trim())
watch(avatar, () => (broken.value = false))
const isUrl = computed(() => isUrlAvatar(avatar.value))
const builtin = computed(() => builtinIndex(avatar.value))
const name = computed(() => props.user?.nickname || props.user?.username || '')

const style = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`
}))
</script>

<style scoped>
.user-avatar {
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  user-select: none;
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--muted);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-silhouette {
  width: 72%;
  height: 72%;
}
</style>
