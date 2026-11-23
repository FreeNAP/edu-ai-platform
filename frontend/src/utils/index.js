// 通用工具与常量映射

export const CATEGORY_MAP = {
  theory: '理论课程',
  practice: '实训课程',
  certification: '认证课程'
}

export function categoryLabel(key) {
  return CATEGORY_MAP[key] || key || '课程'
}

export const DIFFICULTY_TYPES = {
  入门: 'success',
  初级: 'info',
  中级: 'warning',
  高级: 'danger'
}

export function difficultyType(d) {
  return DIFFICULTY_TYPES[d] || 'info'
}

export const APP_STATUS = {
  pending: { label: '待处理', type: 'warning' },
  viewed: { label: '已查看', type: 'primary' },
  accepted: { label: '已通过', type: 'success' },
  rejected: { label: '已拒绝', type: 'danger' }
}

export const ORDER_STATUS = {
  pending: { label: '待支付', type: 'warning' },
  paid: { label: '已支付', type: 'success' },
  cancelled: { label: '已取消', type: 'info' }
}

export const USER_ROLES = {
  student: '学生',
  teacher: '教师',
  admin: '管理员'
}

export const LESSON_KIND = {
  video: '视频',
  text: '图文',
  article: '图文',
  lab: '实验',
  quiz: '测验'
}

// 技术方向 → 封面线稿类型 + 课程编号前缀
const DOMAIN_KEYS = {
  AI: 'ai', 人工智能: 'ai', 机器学习: 'ai', 深度学习: 'ai', 大模型: 'ai', LLM: 'ai',
  大数据: 'data', 数据分析: 'data', 数据挖掘: 'data', 数据库: 'data',
  云计算: 'cloud', 云原生: 'cloud', 运维: 'cloud', DevOps: 'cloud',
  前端: 'fe', 前端开发: 'fe', Web: 'fe',
  后端: 'be', 后端开发: 'be', Java: 'be', Python: 'be',
  物联网: 'iot', IoT: 'iot', 嵌入式: 'iot', 鸿蒙: 'iot'
}

const DOMAIN_PREFIX = { ai: 'AI', data: 'BD', cloud: 'CL', fe: 'FE', be: 'BE', iot: 'IOT', other: 'GEN' }

export function domainKey(domain) {
  if (!domain) return 'other'
  if (DOMAIN_KEYS[domain]) return DOMAIN_KEYS[domain]
  const s = String(domain)
  const hit = Object.keys(DOMAIN_KEYS).find((k) => s.toLowerCase().includes(k.toLowerCase()))
  return hit ? DOMAIN_KEYS[hit] : 'other'
}

// 课程编号：方向前缀 + (100 + id)，如 AI-118
export function courseCode(course) {
  const prefix = DOMAIN_PREFIX[domainKey(course?.tech_domain)]
  const id = Number(course?.id) || 0
  return `${prefix}-${100 + id}`
}

// 头像：URL 图片 / builtin:N 几何图案 / 其余一律显示人像剪影
export const BUILTIN_AVATAR_COUNT = 8

export const BUILTIN_AVATARS = Array.from({ length: BUILTIN_AVATAR_COUNT }, (_, i) => ({
  key: `builtin:${i + 1}`,
  index: i + 1
}))

export function isUrlAvatar(v) {
  return typeof v === 'string' && /^(https?:)?\/\//.test(v.trim())
}

export function builtinIndex(v) {
  const m = /^builtin:(\d+)$/.exec(String(v || '').trim())
  if (!m) return 0
  const n = Number(m[1])
  return n >= 1 && n <= BUILTIN_AVATAR_COUNT ? n : 0
}

// 通知类型
export const NOTIFY_TYPES = {
  course: '课程',
  job: '职位',
  application: '申请',
  order: '订单',
  study: '学习',
  community: '社区',
  system: '系统'
}

// 分页响应统一解包：兼容数组 / {total,page,size,items}
export function normalizePage(data, defaultSize = 12) {
  if (!data) return { items: [], total: 0, page: 1, size: defaultSize }
  if (Array.isArray(data)) {
    return { items: data, total: data.length, page: 1, size: data.length || defaultSize }
  }
  const items = Array.isArray(data.items) ? data.items : []
  return {
    items,
    total: data.total ?? items.length,
    page: data.page ?? 1,
    size: data.size ?? defaultSize
  }
}

const pad = (n) => String(n).padStart(2, '0')

export function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function fmtDay(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function fmtMinutes(min) {
  // 后端课时时长可能是 "8分钟" 这类字符串，非纯数字时原样返回
  if (typeof min === 'string' && min.trim() && !/^\d+(\.\d+)?$/.test(min.trim())) return min.trim()
  const m = Number(min) || 0
  if (m < 60) return `${m} 分钟`
  const h = Math.floor(m / 60)
  const r = m % 60
  return r ? `${h} 小时 ${r} 分` : `${h} 小时`
}

export function fmtDuration(sec) {
  const s = Number(sec) || 0
  if (s <= 0) return ''
  if (s < 60) return `${s} 秒`
  return fmtMinutes(Math.round(s / 60))
}
