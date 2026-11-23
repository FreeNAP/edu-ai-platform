<template>
  <a class="job-card hover-card" :href="`/job/${job.id}`" @click.prevent="$emit('open', job)">
    <div class="jc-top">
      <h3 class="jc-title">{{ job.title }}</h3>
      <span class="jc-salary">{{ job.salary || '薪资面议' }}</span>
    </div>
    <div class="jc-company">
      <span>{{ job.company }}</span>
      <span class="dot" />
      <span>{{ job.city }}</span>
      <template v-if="job.headcount">
        <span class="dot" />
        <span>招 {{ job.headcount }} 人</span>
      </template>
    </div>
    <div class="jc-tags">
      <span v-if="job.category" class="tag tag-accent">{{ job.category }}</span>
      <span v-for="t in tags" :key="t" class="tag">{{ t }}</span>
    </div>
    <div class="jc-foot">
      <span>发布于 {{ fmtDay(job.created_at) }}</span>
      <span class="jc-more">查看详情 <AppIcon name="arrow-right" :size="14" /></span>
    </div>
  </a>
</template>

<script setup>
import { computed } from 'vue'
import { fmtDay } from '../utils'
import AppIcon from './icons/AppIcon.vue'

const props = defineProps({
  job: { type: Object, required: true }
})

defineEmits(['open'])

const tags = computed(() => {
  const t = props.job?.tags
  if (Array.isArray(t)) return t.slice(0, 4)
  if (typeof t === 'string') return t.split(/[,，\s]+/).filter(Boolean).slice(0, 4)
  return []
})
</script>

<style scoped>
.job-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 18px;
  color: var(--ink);
  cursor: pointer;
}

.jc-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.jc-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

.jc-salary {
  font: 600 15px var(--mono);
  color: var(--accent);
  white-space: nowrap;
}

.jc-company {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  flex-wrap: wrap;
}

.dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--line-strong);
}

.jc-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.jc-foot {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--muted);
  font: 400 12px var(--mono);
}

.jc-more {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ink);
}
</style>
