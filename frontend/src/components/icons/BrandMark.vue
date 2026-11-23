<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 32 32"
    fill="none"
    stroke="currentColor"
    stroke-width="1.9"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    class="brand-mark"
  >
    <!-- 打开的书 + 书脊上方的知识节点 -->
    <path d="M4 11.5v13c4-1.6 8-1.3 12 1.2 4-2.5 8-2.8 12-1.2v-13c-4-1.6-8-1.3-12 1.2-4-2.5-8-2.8-12-1.2z" />
    <path d="M16 12.7v13" />
    <path d="M16 12.7V7.6" />
    <circle cx="16" cy="5.2" r="2.2" />
    <path d="M8 16.5c1.6-.4 3.2-.2 4.8.5M19.2 17c1.6-.7 3.2-.9 4.8-.5" />
  </svg>
</template>

<script setup>
defineProps({ size: { type: [Number, String], default: 28 } })
</script>

<style scoped>
.brand-mark {
  color: var(--accent);
  flex-shrink: 0;
}
</style>
