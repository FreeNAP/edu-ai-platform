<template>
  <svg viewBox="0 0 40 40" width="100%" height="100%" aria-hidden="true" class="avatar-pattern">
    <rect width="40" height="40" fill="#1a1a1a" />
    <!-- 1 圆环 -->
    <g v-if="n === 1" fill="none" stroke-width="2">
      <circle cx="20" cy="20" r="13" stroke="#dafa9c" />
      <circle cx="20" cy="20" r="8" stroke="#9a9a9a" />
      <circle cx="20" cy="20" r="3" fill="#dafa9c" stroke="none" />
    </g>
    <!-- 2 栅格 -->
    <g v-else-if="n === 2">
      <rect x="8" y="8" width="7" height="7" fill="#dafa9c" />
      <rect x="16.5" y="8" width="7" height="7" fill="#3a3a3a" />
      <rect x="25" y="8" width="7" height="7" fill="#9a9a9a" />
      <rect x="8" y="16.5" width="7" height="7" fill="#3a3a3a" />
      <rect x="16.5" y="16.5" width="7" height="7" fill="#dafa9c" />
      <rect x="25" y="16.5" width="7" height="7" fill="#3a3a3a" />
      <rect x="8" y="25" width="7" height="7" fill="#9a9a9a" />
      <rect x="16.5" y="25" width="7" height="7" fill="#3a3a3a" />
      <rect x="25" y="25" width="7" height="7" fill="#dafa9c" />
    </g>
    <!-- 3 三角 -->
    <g v-else-if="n === 3" stroke-linejoin="round">
      <path d="M20 7 33 30H7z" fill="none" stroke="#dafa9c" stroke-width="2" />
      <path d="M20 16 27 28H13z" fill="#9a9a9a" />
    </g>
    <!-- 4 波纹 -->
    <g v-else-if="n === 4" fill="none" stroke-width="2" stroke-linecap="round">
      <path d="M5 13c5-4 10 4 15 0s10 4 15 0" stroke="#dafa9c" />
      <path d="M5 20c5-4 10 4 15 0s10 4 15 0" stroke="#9a9a9a" />
      <path d="M5 27c5-4 10 4 15 0s10 4 15 0" stroke="#dafa9c" />
    </g>
    <!-- 5 菱形嵌套 -->
    <g v-else-if="n === 5" fill="none" stroke-width="2">
      <path d="M20 5 35 20 20 35 5 20z" stroke="#9a9a9a" />
      <path d="M20 12 28 20 20 28 12 20z" stroke="#dafa9c" />
      <path d="M20 17 23 20 20 23 17 20z" fill="#dafa9c" stroke="none" />
    </g>
    <!-- 6 半圆弧 -->
    <g v-else-if="n === 6">
      <path d="M6 30a14 14 0 0 1 28 0z" fill="#dafa9c" />
      <path d="M12 30a8 8 0 0 1 16 0" fill="none" stroke="#0f0f0f" stroke-width="2" />
      <circle cx="29" cy="11" r="3.5" fill="#9a9a9a" />
    </g>
    <!-- 7 点阵 -->
    <g v-else-if="n === 7">
      <circle v-for="d in dots" :key="d.k" :cx="d.x" :cy="d.y" :r="d.r" :fill="d.c" />
    </g>
    <!-- 8 交叉线 -->
    <g v-else fill="none" stroke-width="2" stroke-linecap="round">
      <path d="M8 8l24 24" stroke="#dafa9c" />
      <path d="M32 8 8 32" stroke="#9a9a9a" />
      <rect x="14" y="14" width="12" height="12" stroke="#dafa9c" />
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ index: { type: Number, default: 1 } })
const n = computed(() => props.index)

const dots = (() => {
  const arr = []
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      const on = (r + c) % 3 === 0
      arr.push({ k: `${r}-${c}`, x: 9 + c * 7.3, y: 9 + r * 7.3, r: on ? 2.6 : 1.6, c: on ? '#dafa9c' : '#6b6b6b' })
    }
  }
  return arr
})()
</script>

<style scoped>
.avatar-pattern {
  display: block;
}
</style>
