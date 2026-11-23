<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 讲师管理</p>
        <h1 class="page-title">讲师管理</h1>
        <p class="lead">讲师资料，课程里会显示讲师姓名和头衔。</p>
      </div>
    </div>
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openEdit(null)">新增讲师</el-button>
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="头像" width="70" align="center">
        <template #default="{ row }">
          <UserAvatar :user="{ avatar: row.avatar, nickname: row.name }" :size="34" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="姓名" min-width="120" />
      <el-table-column prop="title" label="头衔" min-width="140" show-overflow-tooltip />
      <el-table-column prop="bio" label="简介" min-width="240" show-overflow-tooltip>
        <template #default="{ row }">{{ row.bio || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editVisible" :title="editRow ? '编辑讲师' : '新增讲师'" width="480px">
      <el-form label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" maxlength="32" />
        </el-form-item>
        <el-form-item label="头衔">
          <el-input v-model="form.title" maxlength="64" placeholder="如：资深算法工程师" />
        </el-form-item>
        <el-form-item label="头像">
          <el-input v-model="form.avatar" placeholder="图片地址，可留空" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.bio" type="textarea" :rows="4" maxlength="500" />
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
import { Plus } from '@element-plus/icons-vue'
import UserAvatar from '../../components/UserAvatar.vue'
import { adminGetLecturers, adminCreateLecturer, adminUpdateLecturer, adminDeleteLecturer } from '../../api/admin'
import { normalizePage } from '../../utils'

const items = ref([])
const loading = ref(false)

const editVisible = ref(false)
const editRow = ref(null)
const saving = ref(false)
const form = reactive({ name: '', title: '', bio: '', avatar: '' })

async function fetchList() {
  loading.value = true
  try {
    const p = normalizePage(await adminGetLecturers(), 100)
    items.value = p.items
  } finally {
    loading.value = false
  }
}

function openEdit(row) {
  editRow.value = row
  Object.assign(form, row
    ? { name: row.name || '', title: row.title || '', bio: row.bio || '', avatar: row.avatar || '' }
    : { name: '', title: '', bio: '', avatar: '' })
  editVisible.value = true
}

async function onSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写姓名')
    return
  }
  saving.value = true
  try {
    if (editRow.value) await adminUpdateLecturer(editRow.value.id, { ...form })
    else await adminCreateLecturer({ ...form })
    ElMessage.success('已保存')
    editVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除讲师「${row.name}」？`, '删除讲师', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await adminDeleteLecturer(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || e)
  }
}

onMounted(fetchList)
</script>

