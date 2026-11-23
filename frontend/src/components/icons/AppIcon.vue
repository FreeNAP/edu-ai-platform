<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="stroke"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
    class="app-icon"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
    <circle v-for="(c, i) in circles" :key="'c' + i" :cx="c[0]" :cy="c[1]" :r="c[2]" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

// 线性图标集：stroke 1.7、currentColor
const ICONS = {
  menu: { p: ['M4 7h16', 'M4 12h16', 'M4 17h16'] },
  close: { p: ['M6 6l12 12', 'M18 6L6 18'] },
  bell: { p: ['M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8', 'M10 20a2 2 0 0 0 4 0'] },
  search: { p: ['m20 20-3.5-3.5'], c: [[11, 11, 7]] },
  'arrow-right': { p: ['M5 12h14', 'm13 6 6 6-6 6'] },
  'arrow-left': { p: ['M19 12H5', 'm11 6-6 6 6 6'] },
  user: { p: ['M4 21c1.2-4 4.3-6 8-6s6.8 2 8 6'], c: [[12, 8, 4]] },
  book: { p: ['M3 5.5C6 4.5 9 4.8 12 7c3-2.2 6-2.5 9-1.5V19c-3-1-6-.7-9 1.5-3-2.2-6-2.5-9-1.5z', 'M12 7v13.5'] },
  briefcase: { p: ['M3 8h18v12H3z', 'M8 8V5h8v3', 'M3 13h18'] },
  chat: { p: ['M4 5h16v11H9l-5 4z', 'M8 9.5h8', 'M8 12.5h5'] },
  route: { p: ['M6 19V9a3 3 0 0 1 3-3h6', 'm13 3 3 3-3 3', 'M18 5v10a3 3 0 0 1-3 3H9'], c: [[6, 20, 1]] },
  receipt: { p: ['M6 3h12v18l-3-2-3 2-3-2-3 2z', 'M9 8h6', 'M9 12h6', 'M9 16h3'] },
  clipboard: { p: ['M8 4h8v3H8z', 'M8 5.5H5V21h14V5.5h-3', 'm9 14 2 2 4-4'] },
  clock: { p: ['M12 7v5l3 2'], c: [[12, 12, 9]] },
  community: { p: ['M3 5h13v9H8l-5 4z', 'M16 9h5v9l-3-2.5h-7V14'] },
  check: { p: ['m5 12.5 4.5 4.5L19 7.5'] },
  'check-circle': { p: ['m8 12.5 3 3 5-6'], c: [[12, 12, 9]] },
  play: { p: ['M9 7v10l8-5z'], c: [[12, 12, 9.5]] },
  doc: { p: ['M6 3h8l4 4v14H6z', 'M14 3v4h4', 'M9 12h6', 'M9 16h6'] },
  trash: { p: ['M4 7h16', 'M9 7V4h6v3', 'M6 7l1 13h10l1-13', 'M10 11v6', 'M14 11v6'] },
  edit: { p: ['M4 20h4L19 9l-4-4L4 16z', 'M13 7l4 4'] },
  plus: { p: ['M12 5v14', 'M5 12h14'] },
  logout: { p: ['M15 4h4v16h-4', 'M10 8l-4 4 4 4', 'M6 12h10'] },
  settings: { p: ['M4 7h10', 'M18 7h2', 'M4 17h2', 'M10 17h10'], c: [[16, 7, 2], [8, 17, 2]] },
  spark: { p: ['M12 3v4', 'M12 17v4', 'M3 12h4', 'M17 12h4', 'm6 6 2.5 2.5', 'm15.5 15.5 2.5 2.5', 'm18 6-2.5 2.5', 'm8.5 15.5-2.5 2.5'] },
  grid: { p: ['M4 4h7v7H4z', 'M13 4h7v7h-7z', 'M4 13h7v7H4z', 'M13 13h7v7h-7z'] },
  info: { p: ['M12 11v6', 'M12 7.5v.5'], c: [[12, 12, 9]] },
  star: { p: ['m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z'] },
  external: { p: ['M14 4h6v6', 'M20 4l-9 9', 'M18 14v6H4V6h6'] },
  building: { p: ['M4 21V5l8-2v18', 'M12 8h8v13', 'M2 21h20', 'M7 8h2', 'M7 12h2', 'M7 16h2', 'M15 12h2', 'M15 16h2'] },
  pin: { p: ['M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z'], c: [[12, 9.5, 2.5]] },
  send: { p: ['M21 3 10 14', 'M21 3l-7 18-4-7-7-4z'] },
  users: { p: ['M3 20c.8-3 3.2-5 6-5s5.2 2 6 5', 'M16 4.5a3.5 3.5 0 0 1 0 7', 'M18 15c1.6.6 2.6 2.2 3 5'], c: [[9, 8, 3.5]] },
  cart: { p: ['M3 4h2.5l2.2 11h10.6L20.5 7H7', 'M9 20h.01', 'M17 20h.01'] },
  chart: { p: ['M4 20V4', 'M4 20h16', 'M8 16v-5', 'M12 16V8', 'M16 16v-3'] },
  layers: { p: ['m12 3 9 5-9 5-9-5z', 'm3 13 9 5 9-5'] },
  code: { p: ['m8 7-5 5 5 5', 'm16 7 5 5-5 5', 'M14 4l-4 16'] },
  calendar: { p: ['M4 6h16v15H4z', 'M4 10h16', 'M8 3v4', 'M16 3v4'] },
  mic: { p: ['M9 5a3 3 0 0 1 6 0v6a3 3 0 0 1-6 0z', 'M5.5 11a6.5 6.5 0 0 0 13 0', 'M12 17.5V21'] },
  heart: { p: ['M12 20s-8-4.8-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6.2-8 11-8 11z'] },
  eye: { p: ['M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z'], c: [[12, 12, 3]] },
  'chevron-down': { p: ['m6 9 6 6 6-6'] },
  'chevron-right': { p: ['m9 6 6 6-6 6'] },
  refresh: { p: ['M20 11a8 8 0 0 0-14.6-4.5L4 8', 'M4 3v5h5', 'M4 13a8 8 0 0 0 14.6 4.5L20 16', 'M20 21v-5h-5'] },
  lock: { p: ['M5 11h14v10H5z', 'M8 11V7a4 4 0 0 1 8 0v4'] },
  mail: { p: ['M3 5h18v14H3z', 'm3 6 9 7 9-7'] },
  target: { p: [], c: [[12, 12, 9], [12, 12, 5], [12, 12, 1]] },
  flag: { p: ['M5 21V4', 'M5 4h12l-2 4 2 4H5'] },
  bolt: { p: ['M13 3 5 14h6l-1 7 8-11h-6z'] }
}

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
  stroke: { type: [Number, String], default: 1.7 }
})

const def = computed(() => ICONS[props.name] || ICONS.info)
const paths = computed(() => def.value.p || [])
const circles = computed(() => def.value.c || [])
</script>

<style scoped>
.app-icon {
  flex-shrink: 0;
  display: inline-block;
  vertical-align: middle;
}
</style>
