# API 契约（前后端并行开发依据）

- 后端：FastAPI，端口 **8000**，统一前缀 `/api`，开发模式开放 CORS。
- 前端：Vue3 + Vite，端口 **5173**，`/api` 代理到 `http://127.0.0.1:8000`。
- 鉴权：`Authorization: Bearer <token>`（JWT，HS256，7天有效）。
- 生产模式：FastAPI 挂载 `frontend/dist` 静态目录，`/api` 之外路径返回 `index.html`。

## 统一响应格式

成功：`{ "code": 0, "data": <any> }`
失败：HTTP 状态码 + `{ "code": <非0>, "detail": "错误信息" }`（FastAPI HTTPException detail 也可直接是字符串，前端需兼容 `detail` 字段）

分页响应：`{ "code": 0, "data": { "total": 100, "page": 1, "size": 12, "items": [...] } }`

---

## 1. 认证与用户 `/api/auth` `/api/users`

| 方法 | 路径 | 说明 | 请求体 / 参数 | 返回 data |
| --- | --- | --- | --- | --- |
| POST | /api/auth/register | 注册（默认 student） | `{username, email, password, nickname?}` | 用户对象+token `{user, token}` |
| POST | /api/auth/login | 登录 | `{username, password}`（username 支持用户名或邮箱） | `{user, token}` |
| POST | /api/auth/reset-password | 密码重置（校验用户名+邮箱） | `{username, email, new_password}` | `{ok: true}` |
| GET | /api/auth/me | 当前用户 | header token | 用户对象 |
| PUT | /api/users/profile | 修改个人信息 | `{nickname?, avatar?, major?}` | 用户对象 |
| PUT | /api/users/password | 修改密码 | `{old_password, new_password}` | `{ok: true}` |

用户对象：`{id, username, email, nickname, avatar, major, role("student"|"teacher"|"admin"), status("active"|"disabled"), created_at}`

## 2. 课程 `/api/courses`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/courses | 列表。参数：`category`(theory/practice/certification)、`tech_domain`、`difficulty`(入门/初级/中级/高级)、`is_free`(true/false)、`sort`(newest/students/rating)、`keyword`(匹配课程名或讲师名)、`page`、`size` |
| GET | /api/courses/meta/filters | 筛选项元数据：`{categories:[{key,label}], tech_domains:[], difficulties:[]}` |
| GET | /api/courses/{id} | 详情：`course` 字段 + `chapters:[{id,title,lessons:[{id,title,duration,kind}]}]` + `lecturer` + `comments` + `is_favorited`、`is_enrolled`、`progress`(0-100)、`lesson_status`(已学课时id列表) |
| POST | /api/courses/{id}/favorite | 收藏/取消（toggle）→ `{favorited: bool}` |
| POST | /api/courses/{id}/enroll | 报名/开始学习。免费→直接报名 `{enrolled:true, order:null}`；付费→创建待支付订单 `{enrolled:false, order:{...}}` |
| GET | /api/courses/{id}/comments | 评论列表 `[{id,user:{nickname,avatar},rating,content,created_at}]` |
| POST | /api/courses/{id}/comments | 发评论 `{rating(1-5), content}`（需已报名） |
| POST | /api/lessons/{id}/complete | 标记课时完成 `{study_seconds}` → `{progress}` |
| GET | /api/users/me/enrollments | 我的学习列表（含进度） |
| GET | /api/users/me/favorites | 我的收藏（课程与职位分开：`{courses:[], jobs:[]}`） |

课程对象（列表项）：`{id, title, cover(emoji或url), category, tech_domain, difficulty, is_free, price, students_count, rating, lecturer:{id,name,title}, brief, status, created_at}`

## 3. 实习就业 `/api/jobs`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/jobs | 参数：`category`、`keyword`(岗位名/公司名)、`city`、`page`、`size` |
| GET | /api/jobs/meta/filters | `{categories:[], cities:[]}` |
| GET | /api/jobs/{id} | 详情 + `is_favorited` + `has_applied` |
| POST | /api/jobs/{id}/favorite | toggle → `{favorited}` |
| POST | /api/jobs/{id}/apply | 申请 `{message?}` → 申请对象 |
| GET | /api/users/me/applications | 我的申请 `[{id, job:{...}, message, status(pending/viewed/accepted/rejected), created_at}]` |

职位对象：`{id, title, company, city, category, salary, tags[], description, requirements, headcount, status, created_at}`

## 4. 订单 `/api/orders`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/orders | 我的订单 `[{id, order_no, course:{id,title}, amount, status(pending/paid/cancelled), created_at, paid_at}]` |
| POST | /api/orders/{id}/pay | 模拟支付 → `{status:"paid"}`（支付成功后自动报名） |
| POST | /api/orders/{id}/cancel | 取消 |

## 5. AI 学习助手 `/api/ai`

| 方法 | 路径 | 说明 | 请求体 | 返回 data |
| --- | --- | --- | --- | --- |
| POST | /api/ai/chat | 智能答疑（多轮） | `{session_id?, message, course_id?}` | `{session_id, reply}` |
| GET | /api/ai/chat/sessions | 我的会话列表 | | `[{id, title, updated_at, message_count}]` |
| GET | /api/ai/chat/sessions/{id} | 会话详情 | | `{id,title,messages:[{role,content,created_at}]}` |
| DELETE | /api/ai/chat/sessions/{id} | 删除会话 | | `{ok:true}` |
| POST | /api/ai/learning-path | 学习路径推荐 | `{goal(目标岗位/方向), hours_per_week?}` | `{plan: {title, stages:[{name,duration,topics[],courses[]} ], advice}}`（courses 关联站内课程 id） |
| POST | /api/ai/grade | 作业自动批改 | `{question, code, language?}` | `{score(0-100), correct_points[], issues[], suggestions[], improved_code}` |
| GET | /api/ai/report | 学习报告 | `period=week|month` | `{period, total_minutes, courses_progress[], completed_lessons, strengths[], weaknesses[], suggestions[], summary}` |
| POST | /api/jobs/{id}/ai-interview | 申请AI面试 → 创建面试 | `{message?}` | `{interview_id, questions[]}` |
| POST | /api/ai/interview/{id}/answer | 提交面试作答 | `{answers:[{question,answer}]}` | `{score, evaluation, per_question[]}` |

## 6. 通知 `/api/notifications`（加分项）

- `GET /api/notifications` → `{items:[{id,type,title,content,is_read,created_at}], unread_count}`
- `POST /api/notifications/{id}/read`、`POST /api/notifications/read-all`

## 7. 社区问答 `/api/community`（加分项）

- `GET /api/community/questions?keyword=&page=` → 分页问题列表 `[{id,title,content,user,answers_count,views,created_at}]`
- `POST /api/community/questions` `{title, content}`
- `GET /api/community/questions/{id}` → 详情+`answers:[{id,user,content,created_at}]`
- `POST /api/community/questions/{id}/answers` `{content}`

## 8. 后台 `/api/admin`（仅 admin）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/admin/stats | 看板：`{users, courses, jobs, orders, paid_amount, total_study_minutes, recent_users, trend:[{date, value}]}` |
| GET | /api/admin/users?keyword=&page= | 用户列表（分页） |
| PUT | /api/admin/users/{id} | 修改 `{role?, status?}` |
| DELETE | /api/admin/users/{id} | 删除用户 |
| GET | /api/admin/courses | 全部课程（含下架） |
| POST | /api/admin/courses | 新增 |
| PUT | /api/admin/courses/{id} | 编辑（含 `status: on/off` 上下架） |
| DELETE | /api/admin/courses/{id} | 删除 |
| GET/POST/PUT/DELETE | /api/admin/lecturers[/{id}] | 讲师 CRUD `{name,title,bio,avatar}` |
| GET | /api/admin/jobs | 全部职位 |
| POST/PUT/DELETE | /api/admin/jobs[/{id}] | 职位管理（`status: on/off` 上下架） |
| GET | /api/admin/orders | 全部订单 |
| PUT | /api/admin/orders/{id} | 改状态 |
| GET | /api/admin/applications | 全部申请 |
| PUT | /api/admin/applications/{id} | 改状态 `pending/viewed/accepted/rejected` |

---

## 数据模型约定（后端实现）

表：`users, lecturers, courses, chapters, lessons, enrollments, lesson_progress, favorites, comments, jobs, job_favorites, applications, orders, chat_sessions, chat_messages, learning_plans, interviews, notifications, questions, answers`

种子数据（seed.py，首次启动自动建库填充）：
- 账号：admin/admin123、teacher/teacher123（角色teacher）、student/student123
- 讲师 ≥6；课程 ≥18（三大模块各≥6，覆盖 AI/大数据/云计算/前端/后端/物联网方向，免费与付费混合，含3-5章、每章3-6课时）
- 职位 ≥10（AI工程师/后端/前端/数据分析/运维/测试等）
- 预置：student 已报名 2 门课并有部分进度、若干评论、1 个订单、1 条申请、2 条通知

## AI 引擎约定（backend/app/services/llm.py）

- 读取环境变量：`AI_API_KEY`、`AI_BASE_URL`(默认 `https://api.deepseek.com`)、`AI_MODEL`(默认 `deepseek-chat`)
- 配置存在 → 调 `{AI_BASE_URL}/v1/chat/completions`（httpx，30s 超时，失败回退模拟）
- 未配置 → 内置模拟引擎 `mock_engine.py`：基于课程/职位内容的模板+检索式回复，保证界面完整可演示；返回内容标注「模拟模式」
- 所有 AI 接口输出结构必须与本契约一致（模拟引擎也要产出同构 JSON）

---

## 9. 二期补充接口（功能补全）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/ai/interview/{id} | 面试详情（本人）：`{id, job:{id,title,company}, questions[], answers[]|null, score|null, evaluation|null, per_question[]|null, status("pending"|"done"), created_at}`。刷新面试页时用它恢复题目 |
| GET | /api/users/me/interviews | 我的 AI 面试记录列表（同上结构，按时间倒序） |
| GET | /api/ai/learning-plans | 我生成过的学习路径列表 `[{id, goal, hours_per_week, plan, created_at, due_date}]` |
| DELETE | /api/ai/learning-plans/{id} | 删除一条学习路径 |
| DELETE | /api/community/questions/{id} | 删除问题（作者或管理员） |
| DELETE | /api/community/answers/{id} | 删除回答（作者或管理员） |
| POST | /api/admin/users | 管理员新建用户 `{username,email,password,role,nickname?}` |
| GET | /api/admin/courses/{id}/outline | 课程章节目录 `[{id,title,lessons:[{id,title,duration,kind,content}]}]` |
| PUT | /api/admin/courses/{id}/outline | 整体替换章节目录，请求体同上（无 id 视为新增） |
| GET | /api/admin/questions?keyword=&page= | 社区问题管理列表（分页） |
| DELETE | /api/admin/questions/{id} | 管理员删除问题 |

per_question 统一结构：`[{question, answer, score(0-100), comment}]`。

### 自动通知规则（后端在业务动作中写入 notifications）

| 触发 | 通知对象 | type | 示例标题 |
| --- | --- | --- | --- |
| 管理员编辑课程（标题/简介/价格/目录/上架） | 收藏该课程的用户 | course | 收藏的课程有更新 |
| 管理员修改职位或重新上架 | 收藏该职位的用户 | job | 收藏的职位有更新 |
| 管理员修改职位申请状态 | 申请人 | application | 你的职位申请状态已更新 |
| 订单支付成功 | 下单人 | order | 订单支付成功 |
| 学习路径到期（生成时按阶段总时长算 due_date；用户拉取通知时若已过期且未提醒则补发一次） | 本人 | study | 学习计划到期提醒 |
| 自己的问题收到新回答 | 提问者（回答者不是自己时） | community | 你的问题有了新回答 |
