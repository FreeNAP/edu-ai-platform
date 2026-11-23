<template>
  <div>
    <div class="page-head">
      <div>
        <p class="eyebrow">后台 · 用户管理</p>
        <h1 class="page-title">用户管理</h1>
        <p class="lead">账号、角色和启用状态。禁用后该用户无法登录。</p>
      </div>
    </div>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索用户名/昵称/邮箱" clearable :prefix-icon="SearchIcon" style="max-width: 260px" @keyup.enter="onSearch" @clear="onSearch" />
      <span class="spacer"></span>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
    </div>

    <el-table class="panel-table" :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" min-width="110" />
      <el-table-column prop="nickname" label="昵称" min-width="110">
        <template #default="{ row }">{{ row.nickname || '-' }}</template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="170" show-overflow-tooltip />
      <el-table-column label="角色" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.role === 'admin' ? 'danger' : row.role === 'teacher' ? 'warning' : 'primary'" effect="light">
            {{ USER_ROLES[row.role] || row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="160">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="size"
      :total="total"
      layout="total, prev, pager, next"
      :pager-count="5"
      background
      @current-change="fetchList"
    />

    <el-dialog v-model="editVisible" title="编辑用户" width="420px">
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="editRow?.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="createVisible" title="新建用户" width="min(460px, 92vw)">
      <el-form ref="createRef" :model="createForm" :rules="createRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" maxlength="32" autocomplete="off" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" autocomplete="off" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="createForm.password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="createForm.nickname" maxlength="32" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search as SearchIcon, Plus } from '@element-plus/icons-vue'
import { adminGetUsers, adminUpdateUser, adminDeleteUser, adminCreateUser } from '../../api/admin'
import { normalizePage, fmtDate, USER_ROLES } from '../../utils'

const keyword = ref('')
const page = ref(1)
const size = 15
const total = ref(0)
const items = ref([])
const loading = ref(false)

const editVisible = ref(false)
const editRow = ref(null)
const editForm = reactive({ role: 'student', status: 'active' })
const saving = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, size }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const p = normalizePage(await adminGetUsers(params), size)
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

function openEdit(row) {
  editRow.value = row
  editForm.role = row.role
  editForm.status = row.status
  editVisible.value = true
}

async function onSave() {
  saving.value = true
  try {
    await adminUpdateUser(editRow.value.id, { role: editForm.role, status: editForm.status })
    ElMessage.success('已更新')
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
    await ElMessageBox.confirm(`确定删除用户「${row.username}」？该操作不可恢复。`, '删除用户', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await adminDeleteUser(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || e)
  }
}

onMounted(fetchList)

const createVisible = ref(false)
const creating = ref(false)
const createRef = ref()
const createForm = reactive({ username: '', email: '', password: '', nickname: '', role: 'student' })
const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, message: '至少 3 个字符', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不对', trigger: 'blur' }],
  password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }, { min: 6, message: '至少 6 位', trigger: 'blur' }]
}

function openCreate() {
  Object.assign(createForm, { username: '', email: '', password: '', nickname: '', role: 'student' })
  createVisible.value = true
}

async function onCreate() {
  try {
    await createRef.value.validate()
  } catch {
    return
  }
  creating.value = true
  try {
    await adminCreateUser({ ...createForm, nickname: createForm.nickname.trim() || undefined })
    ElMessage.success('用户已创建')
    createVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    creating.value = false
  }
}
</script>
