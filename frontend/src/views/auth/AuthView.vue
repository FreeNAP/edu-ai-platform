<template>
  <div class="auth-page">
    <div class="auth-box">
      <section class="brand-panel">
        <div class="brand">
          <BrandMark :size="30" />
          <span>智慧教育平台</span>
        </div>
        <div class="brand-main">
          <p class="eyebrow">// 华为 ICT 学院课程项目</p>
          <h1 class="brand-title">选课、上课、做题、投简历，<br class="desktop-only" />都在这一个网站里。</h1>
          <ul class="brand-points">
            <li>
              <span class="pt-icon"><AppIcon name="book" /></span>
              <div><b>按方向和难度找课</b><small>理论、实训、认证三类课程，学到哪一节自动记进度</small></div>
            </li>
            <li>
              <span class="pt-icon"><AppIcon name="chat" /></span>
              <div><b>卡住了直接问 AI</b><small>答疑、排学习计划、批改代码作业，结果都能回看</small></div>
            </li>
            <li>
              <span class="pt-icon"><AppIcon name="briefcase" /></span>
              <div><b>投实习前先模拟面试</b><small>按岗位出题，逐题打分和点评，再决定要不要投</small></div>
            </li>
          </ul>
        </div>
      </section>

      <section class="form-panel">
        <h2 class="form-title">{{ titles[mode] }}</h2>
        <el-tabs v-model="mode" class="auth-tabs" @tab-change="onTabChange">
          <el-tab-pane label="登录" name="login" />
          <el-tab-pane label="注册" name="register" />
          <el-tab-pane label="重置密码" name="reset" />
        </el-tabs>

        <!-- 登录 -->
        <el-form
          v-if="mode === 'login'"
          ref="loginRef"
          :model="loginForm"
          :rules="loginRules"
          size="large"
          @submit.prevent="doLogin"
        >
          <el-form-item prop="username">
            <el-input v-model="loginForm.username" placeholder="用户名或邮箱" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="doLogin"
            />
          </el-form-item>
          <el-button type="primary" class="submit-btn" size="large" :loading="loading" @click="doLogin">
            登录
          </el-button>
          <div class="form-foot">
            <el-link type="primary" :underline="false" @click="go('reset')">忘记密码？</el-link>
            <span class="text-sub">没有账号？<el-link type="primary" :underline="false" @click="go('register')">立即注册</el-link></span>
          </div>
          <div v-if="store.config.demo_mode" class="demo-tip">
            <span class="mono">DEMO</span>
            <span>学生 student / student123，管理员 admin / admin123</span>
          </div>
        </el-form>

        <!-- 注册 -->
        <el-form
          v-else-if="mode === 'register'"
          ref="regRef"
          :model="regForm"
          :rules="regRules"
          size="large"
          @submit.prevent="doRegister"
        >
          <el-form-item prop="username">
            <el-input v-model="regForm.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="regForm.email" placeholder="邮箱" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="nickname">
            <el-input v-model="regForm.nickname" placeholder="昵称（可选）" :prefix-icon="Postcard" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="regForm.password" type="password" placeholder="密码：至少 8 位，包含字母和数字" show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item prop="confirm">
            <el-input
              v-model="regForm.confirm"
              type="password"
              placeholder="确认密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="doRegister"
            />
          </el-form-item>
          <el-button type="primary" class="submit-btn" size="large" :loading="loading" @click="doRegister">
            注册
          </el-button>
          <div class="form-foot">
            <span class="text-sub">已有账号？<el-link type="primary" :underline="false" @click="go('login')">去登录</el-link></span>
          </div>
        </el-form>

        <!-- 重置密码 -->
        <el-form
          v-else
          ref="resetRef"
          :model="resetForm"
          :rules="resetRules"
          size="large"
          @submit.prevent="doReset"
        >
          <el-form-item prop="email">
            <div class="code-row">
              <el-input v-model="resetForm.email" placeholder="注册邮箱" :prefix-icon="Message" />
              <el-button :disabled="countdown > 0" :loading="sending" @click="sendCode">
                {{ countdown > 0 ? `${countdown}s 后重发` : '发送验证码' }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item prop="code">
            <el-input v-model="resetForm.code" placeholder="邮件里的 6 位验证码" maxlength="6" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="new_password">
            <el-input v-model="resetForm.new_password" type="password" placeholder="新密码：至少 8 位，包含字母和数字" show-password :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item prop="confirm">
            <el-input
              v-model="resetForm.confirm"
              type="password"
              placeholder="确认新密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="doReset"
            />
          </el-form-item>
          <el-button type="primary" class="submit-btn" size="large" :loading="loading" @click="doReset">
            重置密码
          </el-button>
          <div class="form-foot">
            <span class="text-sub">想起来了？<el-link type="primary" :underline="false" @click="go('login')">去登录</el-link></span>
          </div>
        </el-form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Postcard } from '@element-plus/icons-vue'
import { useUserStore } from '../../stores/user'
import { forgotPassword, resetPassword } from '../../api/auth'
import AppIcon from '../../components/icons/AppIcon.vue'
import BrandMark from '../../components/icons/BrandMark.vue'

const titles = { login: '登录账号', register: '注册新账号', reset: '重置密码' }

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const mode = ref(route.meta.authMode || 'login')
watch(() => route.meta.authMode, (m) => { if (m) mode.value = m })

const loading = ref(false)
const loginRef = ref()
const regRef = ref()
const resetRef = ref()

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', email: '', nickname: '', password: '', confirm: '' })
const resetForm = reactive({ email: '', code: '', new_password: '', confirm: '' })
const sending = ref(false)
const countdown = ref(0)
let timer = null

const PASSWORD_RULE = {
  validator: (r, v, cb) => {
    if (!v || v.length < 8) return cb(new Error('密码至少 8 位'))
    if (!/[A-Za-z]/.test(v) || !/\d/.test(v)) return cb(new Error('密码需要同时包含字母和数字'))
    cb()
  },
  trigger: 'blur'
}

const loginRules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const regRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度 3-32 位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, PASSWORD_RULE],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (r, v, cb) => cb(v === regForm.password ? undefined : new Error('两次密码不一致')),
      trigger: 'blur'
    }
  ]
}

const resetRules = {
  email: [
    { required: true, message: '请输入注册邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }, { len: 6, message: '验证码是 6 位数字', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, PASSWORD_RULE],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (r, v, cb) => cb(v === resetForm.new_password ? undefined : new Error('两次密码不一致')),
      trigger: 'blur'
    }
  ]
}

const MODE_ROUTE = { login: '/login', register: '/register', reset: '/reset' }

function go(m) {
  router.push(MODE_ROUTE[m])
}

function onTabChange(name) {
  router.push(MODE_ROUTE[name])
}

function redirectAfterAuth() {
  const target = route.query.redirect
  router.push(typeof target === 'string' && target.startsWith('/') ? target : '/')
}

async function doLogin() {
  try {
    await loginRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await store.login({ username: loginForm.username.trim(), password: loginForm.password })
    ElMessage.success('登录成功，欢迎回来')
    redirectAfterAuth()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  try {
    await regRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    const payload = {
      username: regForm.username.trim(),
      email: regForm.email.trim(),
      password: regForm.password
    }
    if (regForm.nickname.trim()) payload.nickname = regForm.nickname.trim()
    await store.register(payload)
    ElMessage.success('注册成功，已自动登录')
    redirectAfterAuth()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function sendCode() {
  try {
    await resetRef.value.validateField('email')
  } catch {
    return
  }
  sending.value = true
  try {
    const res = await forgotPassword(resetForm.email.trim())
    if (res?.dev_code) {
      resetForm.code = res.dev_code
      ElMessage.info('当前环境未配置邮件服务，验证码已自动填入')
    } else {
      ElMessage.success('如果该邮箱已注册，验证码已发送，请查收')
    }
    countdown.value = 60
    clearInterval(timer)
    timer = setInterval(() => {
      countdown.value -= 1
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    sending.value = false
  }
}

onBeforeUnmount(() => clearInterval(timer))

async function doReset() {
  try {
    await resetRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await resetPassword({
      email: resetForm.email.trim(),
      code: resetForm.code.trim(),
      new_password: resetForm.new_password
    })
    ElMessage.success('密码重置成功，请使用新密码登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => store.loadConfig())
</script>

<style scoped>
.code-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.code-row .el-button {
  height: 40px;
  flex-shrink: 0;
}

.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: var(--bg);
}

.auth-box {
  width: 980px;
  max-width: 100%;
  min-height: 580px;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  border: 1px solid var(--line);
  border-radius: var(--r);
  background: var(--card);
  overflow: hidden;
}

.brand-panel {
  padding: 36px 40px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  border-right: 1px solid var(--line);
  background: var(--bg);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
}

.brand-main {
  margin: auto 0;
}

.brand-title {
  font-size: 30px;
  line-height: 1.25;
  letter-spacing: -0.02em;
  font-weight: 600;
  margin: 0 0 28px;
}

.brand-points {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.brand-points li {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.pt-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: var(--r);
  color: var(--accent);
  flex-shrink: 0;
}

.brand-points b {
  display: block;
  font-weight: 500;
  font-size: 15px;
}

.brand-points small {
  color: var(--muted);
  font-size: 13px;
}

.form-panel {
  padding: 40px 44px;
}

.form-title {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0 0 12px;
}

.auth-tabs {
  margin-bottom: 8px;
}

.auth-tabs :deep(.el-tabs__item) {
  font-size: 15px;
}

.submit-btn {
  width: 100%;
  height: 44px;
  margin-top: 4px;
  font-weight: 600;
}

.form-foot {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.demo-tip {
  margin-top: 20px;
  padding: 10px 12px;
  display: flex;
  gap: 10px;
  align-items: baseline;
  border: 1px dashed var(--line);
  border-radius: var(--r);
  color: var(--muted);
  font-size: 13px;
}

.demo-tip .mono {
  color: var(--accent);
  font-size: 11px;
  letter-spacing: 0.08em;
}


@media (max-width: 860px) {
  .auth-box {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    border-right: 0;
    border-bottom: 1px solid var(--line);
    padding: 24px 20px;
    gap: 20px;
  }

  .brand-title {
    font-size: 22px;
    margin-bottom: 18px;
  }

  .brand-points small {
    display: none;
  }

  .form-panel {
    padding: 24px 20px 28px;
  }
}
</style>
