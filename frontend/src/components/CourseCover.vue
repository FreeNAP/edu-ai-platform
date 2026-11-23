<template>
  <div class="course-cover" :class="{ compact }" :style="{ height: height + 'px' }">
    <div class="cc-inner">
      <img v-if="isUrlCover" :src="course.cover" class="cover-img" alt="" />
      <svg
        v-else
        class="cover-art"
        viewBox="0 0 320 160"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <defs>
          <pattern :id="gridId" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M20 0H0V20" stroke="#1e1e1e" stroke-width="1" />
          </pattern>
        </defs>
        <rect width="320" height="160" fill="#151515" />
        <rect width="320" height="160" :fill="`url(#${gridId})`" />

        <!-- AI：神经网络节点连线 -->
        <g v-if="kind === 'ai'">
          <path v-for="(l, i) in netLines" :key="i" :d="l" stroke="#3a3a3a" stroke-width="1" />
          <circle
            v-for="(nd, i) in netNodes"
            :key="'n' + i"
            :cx="nd.x"
            :cy="nd.y"
            r="5.5"
            :fill="nd.on ? A : '#151515'"
            :stroke="A"
            stroke-width="1.6"
          />
        </g>

        <!-- 大数据：柱状 + 散点趋势 -->
        <g v-else-if="kind === 'data'">
          <path d="M122 28V136H302" :stroke="M" stroke-width="1.4" />
          <rect v-for="(b, i) in bars" :key="i" :x="b.x" :y="136 - b.h" width="18" :height="b.h" :stroke="A" stroke-width="1.6" :fill="i === 3 ? T : 'none'" />
          <polyline points="144,88 174,64 204,78 234,40 264,56 292,30" :stroke="M" stroke-width="1.4" stroke-dasharray="4 4" />
          <circle v-for="(p, i) in scatter" :key="'s' + i" :cx="p[0]" :cy="p[1]" r="3" :fill="A" />
        </g>

        <!-- 云计算：分层堆叠 -->
        <g v-else-if="kind === 'cloud'">
          <path d="M150 112l60 22 60-22" :stroke="M" stroke-width="1.4" />
          <path d="M150 112l60-22 60 22" :stroke="M" stroke-width="1.4" stroke-dasharray="4 4" />
          <path d="M150 82l60 22 60-22" :stroke="M" stroke-width="1.4" />
          <path d="M150 82V112M270 82V112M210 104V134" :stroke="M" stroke-width="1.2" stroke-dasharray="3 4" />
          <path d="M150 52l60-22 60 22-60 22z" :stroke="A" stroke-width="1.7" :fill="T" />
          <path d="M150 52V82M270 52V82M210 74V104" :stroke="A" stroke-width="1.4" />
          <path d="M150 82l60 22 60-22" :stroke="A" stroke-width="1.7" />
        </g>

        <!-- 前端：浏览器窗口 + 组件块 -->
        <g v-else-if="kind === 'fe'">
          <rect x="128" y="24" width="174" height="114" :stroke="A" stroke-width="1.6" />
          <path d="M128 42H302" :stroke="A" stroke-width="1.4" />
          <circle cx="139" cy="33" r="2.6" :stroke="A" stroke-width="1.3" />
          <circle cx="148" cy="33" r="2.6" :stroke="M" stroke-width="1.3" />
          <circle cx="157" cy="33" r="2.6" :stroke="M" stroke-width="1.3" />
          <rect x="140" y="54" width="62" height="38" :fill="T" :stroke="A" stroke-width="1.4" />
          <rect x="212" y="54" width="78" height="14" :stroke="M" stroke-width="1.3" />
          <rect x="212" y="76" width="54" height="16" :stroke="M" stroke-width="1.3" />
          <rect x="140" y="102" width="150" height="24" :stroke="M" stroke-width="1.3" stroke-dasharray="4 3" />
          <path d="M150 114h40" :stroke="A" stroke-width="1.4" />
        </g>

        <!-- 后端：服务器机柜 + 接口连线 -->
        <g v-else-if="kind === 'be'">
          <circle cx="122" cy="80" r="5" :stroke="M" stroke-width="1.4" />
          <path d="M127 80h18M145 41v78M145 41h25M145 80h25M145 119h25" :stroke="M" stroke-width="1.3" />
          <g v-for="(y, i) in [28, 67, 106]" :key="i">
            <rect x="170" :y="y" width="116" height="26" :stroke="i === 0 ? A : M" stroke-width="1.6" :fill="i === 0 ? T : 'none'" />
            <circle cx="183" :cy="y + 13" r="3" :fill="i === 0 ? A : 'none'" :stroke="A" stroke-width="1.3" />
            <path :d="`M232 ${y + 13}H274`" :stroke="i === 0 ? A : M" stroke-width="1.4" />
            <path :d="`M196 ${y + 9}v8M204 ${y + 9}v8M212 ${y + 9}v8`" stroke="#4a4a4a" stroke-width="1.3" />
          </g>
        </g>

        <!-- 物联网：信号 + 设备节点 -->
        <g v-else-if="kind === 'iot'">
          <path v-for="(p, i) in iotNodes" :key="'l' + i" :d="`M208 80L${p[0]} ${p[1]}`" :stroke="M" stroke-width="1.2" stroke-dasharray="3 4" />
          <circle v-for="(p, i) in iotNodes" :key="'c' + i" :cx="p[0]" :cy="p[1]" r="5.5" fill="#151515" :stroke="i % 2 ? M : A" stroke-width="1.5" />
          <rect x="192" y="64" width="32" height="32" :fill="T" :stroke="A" stroke-width="1.7" />
          <circle cx="208" cy="80" r="4" :fill="A" />
          <path d="M196 54q12-10 24 0" :stroke="A" stroke-width="1.6" />
          <path d="M188 45q20-17 40 0" :stroke="A" stroke-width="1.4" />
          <path d="M180 36q28-24 56 0" :stroke="M" stroke-width="1.3" />
        </g>

        <!-- 其他：网格十字 -->
        <g v-else>
          <path v-for="(p, i) in crosses" :key="i" :d="`M${p[0] - 5} ${p[1]}h10M${p[0]} ${p[1] - 5}v10`" :stroke="p[2] ? A : M" stroke-width="1.5" />
          <rect x="190" y="50" width="60" height="60" :stroke="A" stroke-width="1.6" />
        </g>
      </svg>
    </div>
    <span class="cv-code">// {{ code }}</span>
    <span v-if="domainLabel" class="cv-dom">{{ domainLabel }}</span>
  </div>
</template>

<script setup>
import { computed, useId } from 'vue'
import { domainKey, courseCode } from '../utils'

const props = defineProps({
  course: { type: Object, required: true },
  height: { type: Number, default: 132 },
  compact: { type: Boolean, default: false }
})

const A = '#dafa9c'
const M = '#5a5a5a'
const T = '#1f2614'

const gridId = `cv-grid-${useId()}`

// 只渲染 URL 封面；emoji 等其他值一律忽略，用线稿
const isUrlCover = computed(() => {
  const c = props.course?.cover
  return typeof c === 'string' && /^(https?:)?\/\//.test(c)
})

const kind = computed(() => domainKey(props.course?.tech_domain))
const code = computed(() => courseCode(props.course))
const domainLabel = computed(() => props.course?.tech_domain || '')

const layers = [
  [140, [40, 80, 120]],
  [200, [28, 62, 98, 132]],
  [260, [58, 102]]
]
const netNodes = []
layers.forEach(([x, ys], li) => ys.forEach((y, i) => netNodes.push({ x, y, on: (li === 1 && i === 1) || (li === 2 && i === 0) })))
const netLines = []
for (let li = 0; li < layers.length - 1; li++) {
  const [x1, ys1] = layers[li]
  const [x2, ys2] = layers[li + 1]
  ys1.forEach((a) => ys2.forEach((b) => netLines.push(`M${x1} ${a}L${x2} ${b}`)))
}

const bars = [
  { x: 135, h: 42 },
  { x: 165, h: 68 },
  { x: 195, h: 54 },
  { x: 225, h: 92 },
  { x: 255, h: 76 }
]
const scatter = [[144, 88], [174, 64], [204, 78], [234, 40], [264, 56], [292, 30]]
const iotNodes = [[132, 40], [140, 128], [286, 38], [292, 120], [248, 142], [160, 84]]
const crosses = []
for (let r = 0; r < 4; r++) {
  for (let c = 0; c < 6; c++) crosses.push([130 + c * 34, 30 + r * 34, (r + c) % 4 === 0])
}
</script>

<style scoped>
.course-cover {
  position: relative;
  overflow: hidden;
  background: var(--card);
  border-bottom: 1px solid var(--line);
}

.cc-inner {
  position: absolute;
  inset: 0;
  transition: transform 0.3s ease;
}

.cover-art,
.cover-img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.cv-code {
  position: absolute;
  left: 14px;
  top: 12px;
  font: 500 12px var(--mono);
  letter-spacing: 0.04em;
  color: var(--accent);
}

.cv-dom {
  position: absolute;
  right: 12px;
  bottom: 10px;
  font: 500 11px var(--mono);
  padding: 2px 8px;
  color: var(--muted);
  background: rgba(15, 15, 15, 0.85);
  border: 1px solid var(--line);
  border-radius: 1px;
}

.compact .cv-code {
  font-size: 11px;
  left: 10px;
  top: 8px;
}

.compact .cv-dom {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .cc-inner {
    transition: none;
  }
}
</style>
