<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 职位管理</p>
        <h1 class="page-title">职位管理</h1>
        <p class="lead">职位的新增、编辑和上下架。修改职位会通知收藏了它的用户。</p>
      </div>
    </div>
    <div class="toolbar">
      <div class="flex gap-12">
        <el-input v-model="keyword" placeholder="搜索岗位/公司" clearable :prefix-icon="SearchIcon" style="width: 220px" @keyup.enter="onSearch" @clear="onSearch" />
        <el-button type="primary" :icon="Plus" @click="openEdit(null)">新增职位</el-button>
      </div>
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="岗位" min-width="150" show-overflow-tooltip />
      <el-table-column prop="company" label="公司" min-width="140" show-overflow-tooltip />
      <el-table-column prop="city" label="城市" width="90" />
      <el-table-column prop="category" label="分类" width="110">
        <template #default="{ row }"><el-tag size="small" effect="plain">{{ row.category || '-' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="salary" label="薪资" width="110">
        <template #default="{ row }"><span class="price">{{ row.salary || '面议' }}</span></template>
      </el-table-column>
      <el-table-column label="上架" width="80" align="center">
        <template #default="{ row }">
          <el-switch :model-value="row.status !== 'off'" @change="(v) => onToggle(row, v)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > size"
      v-model:current-page="page"
      :page-size="size"
      :total="total"
      layout="total, prev, pager, next"
      :pager-count="5"
      background
      @current-change="fetchList"
    />

    <el-dialog v-model="editVisible" :title="editRow ? '编辑职位' : '新增职位'" width="620px">
      <el-form label-width="90px">
        <el-form-item label="岗位名" required>
          <el-input v-model="form.title" maxlength="64" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="公司" required>
              <el-input v-model="form.company" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="城市">
              <el-input v-model="form.city" maxlength="32" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="分类">
              <el-input v-model="form.category" placeholder="如 AI/后端" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="薪资">
              <el-input v-model="form.salary" placeholder="如 10k-15k" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="招聘人数">
              <el-input-number v-model="form.headcount" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="逗号分隔，如：实习,可转正,Python" />
        </el-form-item>
        <el-form-item label="职位描述">
          <el-input v-model="form.description" type="textarea" :rows="4" maxlength="2000" />
        </el-form-item>
        <el-form-item label="任职要求">
          <el-input v-model="form.requirements" type="textarea" :rows="4" maxlength="2000" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="on">上架</el-radio>
            <el-radio value="off">下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search as SearchIcon, Plus } from '@element-plus/icons-vue'
import { adminGetJobs, adminCreateJob, adminUpdateJob, adminDeleteJob } from '../../api/admin'
import { normalizePage } from '../../utils'

const keyword = ref('')
const page = ref(1)
const size = 15
const total = ref(0)
const items = ref([])
const loading = ref(false)

const editVisible = ref(false)
const editRow = ref(null)
const saving = ref(false)
const form = reactive({
  title: '', company: '', city: '', category: '', salary: '',
  tags: '', description: '', requirements: '', headcount: 1, status: 'on'
})

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const p = normalizePage(await adminGetJobs(params), size)
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  fetchList()
}

function tagsToText(tags) {
  if (Array.isArray(tags)) return tags.join(',')
  return tags || ''
}

function openEdit(row) {
  editRow.value = row
  if (row) {
    Object.assign(form, {
      title: row.title || '', company: row.company || '', city: row.city || '',
      category: row.category || '', salary: row.salary || '', tags: tagsToText(row.tags),
      description: row.description || '', requirements: row.requirements || '',
      headcount: row.headcount ?? 1, status: row.status || 'on'
    })
  } else {
    Object.assign(form, {
      title: '', company: '', city: '', category: '', salary: '',
      tags: '', description: '', requirements: '', headcount: 1, status: 'on'
    })
  }
  editVisible.value = true
}

async function onSave() {
  if (!form.title.trim() || !form.company.trim()) {
    ElMessage.warning('请填写岗位名与公司')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    payload.tags = form.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean)
    if (editRow.value) await adminUpdateJob(editRow.value.id, payload)
    else await adminCreateJob(payload)
    ElMessage.success('已保存')
    editVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function onToggle(row, v) {
  try {
    await adminUpdateJob(row.id, { status: v ? 'on' : 'off' })
    row.status = v ? 'on' : 'off'
    ElMessage.success(v ? '已上架' : '已下架')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除职位「${row.title}」？`, '删除职位', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await adminDeleteJob(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || e)
  }
}

onMounted(fetchList)
</script>
