<template>
  <a class="course-card hover-card" :href="`/course/${course.id}`" @click.prevent="$emit('open', course)">
    <CourseCover :course="course" />
    <div class="cc-body">
      <h3 class="cc-title" :title="course.title">{{ course.title }}</h3>
      <p class="cc-teacher">
        {{ course.lecturer?.name || '讲师团队' }}<template v-if="course.lecturer?.title"> · {{ course.lecturer.title }}</template>
      </p>
      <div class="cc-meta">
        <span class="tag">{{ course.difficulty || '通用' }}</span>
        <span v-if="course.is_free" class="tag tag-accent">免费</span>
        <span v-else class="price">¥{{ course.price }}</span>
      </div>
      <div class="cc-stats">
        <span>评分 {{ Number(course.rating ?? 0).toFixed(1) }}</span>
        <span>{{ Number(course.students_count ?? 0).toLocaleString() }} 人在学</span>
      </div>
    </div>
  </a>
</template>

<script setup>
import CourseCover from './CourseCover.vue'

defineProps({
  course: { type: Object, required: true }
})

defineEmits(['open'])
</script>

<style scoped>
.course-card {
  display: flex;
  flex-direction: column;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--r);
  overflow: hidden;
  color: var(--ink);
  cursor: pointer;
}

.cc-body {
  padding: 16px 18px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.cc-title {
  font-size: 16px;
  line-height: 1.35;
  margin: 0;
  font-weight: 600;
  letter-spacing: -0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 43px;
}

.cc-teacher {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cc-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cc-stats {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font: 400 12px var(--mono);
}
</style>
