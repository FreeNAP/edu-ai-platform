<p align="center">
  <img src="docs/logo.svg" width="96" alt="EduAI Platform logo">
</p>

<h1 align="center">EduAI Platform · 智慧教育平台</h1>

<p align="center">选课、上课、做题、投简历，放在同一个网站里的 AI 学习平台</p>

<p align="center">
  <a href="https://github.com/FreeNAP/edu-ai-platform"><img src="https://img.shields.io/github/stars/FreeNAP/edu-ai-platform?style=flat-square&logo=github" alt="GitHub stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-dafa9c?style=flat-square" alt="License"></a>
  <a href="https://vuejs.org/"><img src="https://img.shields.io/badge/Vue-3.5-42b883?style=flat-square&logo=vuedotjs" alt="Vue"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.141-009688?style=flat-square&logo=fastapi" alt="FastAPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href=".github/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/FreeNAP/edu-ai-platform/ci.yml?style=flat-square&label=CI" alt="CI"></a>
  <a href="#测试"><img src="https://img.shields.io/badge/tests-62%20passed-dafa9c?style=flat-square" alt="Tests"></a>
  <a href="#部署"><img src="https://img.shields.io/badge/deploy-Docker%20Compose-2496ed?style=flat-square&logo=docker&logoColor=white" alt="Docker"></a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="docs/01-项目需求分析（PRD）.md">需求文档</a> ·
  <a href="docs/02-系统架构设计.md">架构设计</a> ·
  <a href="docs/API契约.md">接口文档</a> ·
  <a href="#页面展示">页面展示</a>
</p>

![EduAI Platform 课程中心](docs/screenshots/02-courses.webp)

EduAI Platform 是一个前后端分离的在线学习平台。学生在**理论课程、实训课程、认证课程、实习就业**四个模块之间切换：按方向和难度找课、逐课时学习并自动记录进度、遇到问题问 AI 助手、投递实习岗位前先做一场 AI 模拟面试。管理员在后台管理用户、课程目录、职位、订单、申请和社区内容。

后端是 FastAPI + SQLAlchemy，默认 SQLite 开箱即用，可切换 MySQL；AI 能力走 OpenAI 兼容接口，没有配置密钥时由内置引擎生成同结构的结果，所有页面都能完整演示。

## 核心功能

- **账号与安全**：学生 / 教师 / 管理员三种角色；密码强度校验（至少 8 位、字母加数字）；连续输错 5 次锁定 15 分钟；短期访问令牌 + 刷新令牌，改密码或"退出所有设备"后旧令牌立即失效；邮件验证码找回密码（验证码只存哈希、10 分钟过期、错误 5 次作废、不暴露邮箱是否注册）；登录、注册、找回密码按 IP 限流。
- **文件上传**：头像、简历、课程图片、课时视频；按文件头识别真实类型（改扩展名无效），分类型限制大小，随机文件名存储。
- **课程资源**：按技术方向（AI、大数据、云计算、前端、后端、物联网）、难度、是否免费组合筛选；按最新、学习人数、评分排序；课程名和讲师名模糊搜索。
- **课程学习**：课程详情含简介、章节目录、测验、讲师、评价；报名后逐课时学习，视频课时直接播放（支持拖动），讲义正文和视频只对已报名用户可见；完成课时自动累计时长并更新进度。
- **测验、考试与证书**：单选 / 多选 / 判断题，自动判分并给出解析；可设及格线、限时、作答次数；通过结业考试自动颁发证书，证书带编号，任何人可在线查验，支持打印或另存 PDF。
- **教师工作台**：教师只能管理自己负责的课程——编辑课程信息、章节目录（上传视频、写讲义）、出测验和结业考试、上下架；查看每位学员的进度、学习时长和最好成绩。
- **订单**：付费课程生成订单，模拟支付后自动报名，个人中心可查看订单与支付时间。
- **实习就业**：按职位分类、城市筛选，岗位名 / 公司名搜索；收藏、附简历投递、查看申请状态。
- **AI 学习助手**：
  - 智能答疑：多轮对话、逐字流式输出，可关联正在学的课程，会话自动保存；
  - 学习路径：输入目标方向和每周时长，生成分阶段计划并关联站内课程，计划会保存并在到期时提醒；
  - 作业批改：提交题目和代码，返回分数、做对的地方、问题、建议和改进后的代码；
  - 学习报告：按周 / 月统计学习时长、完成课时、各课程进度和薄弱点；
  - AI 模拟面试：按岗位出题，作答后给出总分和逐题点评，记录可随时回看。
- **消息通知**：收藏的课程或职位有更新、申请状态变化、订单支付成功、学习计划到期、自己的问题收到回答时自动通知。
- **问答社区**：提问、回答、搜索；作者和管理员可删除问题或回答。
- **AI 用量配额**：学生每天可调用次数可配置（默认 100 次），教师和管理员不限，助手页显示今日剩余次数。
- **后台管理**：操作日志（管理员和教师的每次写操作，含操作人、接口、IP）；数据看板（用户、课程、订单、收款、学习时长、近 7 日活跃趋势）；用户新建 / 改角色 / 禁用；课程上下架与章节目录编辑；讲师、职位、订单、职位申请、社区内容管理。
- **移动端**：全站响应式，手机上导航收进全屏菜单，后台菜单改为横向滚动，320px 宽度无横向溢出。

## 项目功能流程

所有流程图默认折叠，点击标题展开。

<details>
<summary><strong>01｜登录注册与角色分流</strong></summary>

```mermaid
flowchart LR
    VISIT["访问任意页面"] --> TOKEN{"已登录？"}
    TOKEN -->|否| LOGIN["登录 /login"]
    LOGIN --> REG["注册 /register"]
    LOGIN --> RESET["重置密码 /reset<br/>用户名 + 邮箱校验"]
    REG --> LOGIN
    RESET --> LOGIN
    LOGIN --> JWT["签发 JWT（7 天）"]
    TOKEN -->|是| JWT
    JWT --> STATUS{"账号状态"}
    STATUS -->|已禁用| DENY["拒绝访问"]
    STATUS -->|正常| ROLE{"角色"}
    ROLE -->|学生 / 教师| FRONT["课程中心 /courses/theory"]
    ROLE -->|管理员| FRONT
    ROLE -->|管理员| ADMIN["后台 /admin"]
```

</details>

<details>
<summary><strong>02｜选课、报名与学习进度</strong></summary>

```mermaid
flowchart TB
    LIST["课程列表 /courses/:category<br/>方向 · 难度 · 免费 · 排序 · 搜索"] --> DETAIL["课程详情 /course/:id"]
    DETAIL --> FAV["收藏"]
    DETAIL --> ENROLL{"开始学习"}
    ENROLL -->|免费课| JOIN["直接报名"]
    ENROLL -->|付费课| ORDER["生成待支付订单"]
    ORDER --> PAY["个人中心 · 模拟支付"]
    PAY --> NOTIFY_O["订单支付通知"]
    PAY --> JOIN
    JOIN --> LEARN["学习页 /learn/:id<br/>章节树 + 讲义正文"]
    LEARN --> DONE["完成课时 + 学习时长"]
    DONE --> PROGRESS["更新课程进度"]
    PROGRESS --> REPORT["周 / 月学习报告"]
    JOIN --> COMMENT["评分与评价"]
```

</details>

<details>
<summary><strong>03｜AI 学习助手</strong></summary>

```mermaid
flowchart LR
    USER["学生"] --> CHAT["智能答疑<br/>多轮会话 · 关联课程"]
    USER --> PATH["学习路径<br/>目标 + 每周时长"]
    USER --> GRADE["作业批改<br/>题目 + 代码 + 语言"]
    USER --> REPORT["学习报告<br/>本周 / 本月"]

    CHAT --> ENGINE{"AI_API_KEY 已配置？"}
    PATH --> ENGINE
    GRADE --> ENGINE
    REPORT --> ENGINE
    ENGINE -->|是| LLM["OpenAI 兼容接口"]
    ENGINE -->|否 / 调用失败| LOCAL["内置引擎<br/>同结构结果"]
    LLM --> RESULT["结构化结果"]
    LOCAL --> RESULT

    PATH --> SAVE["保存计划 + 估算到期日"]
    SAVE --> REMIND["到期后补发一次提醒"]
```

</details>

<details>
<summary><strong>04｜实习就业与 AI 模拟面试</strong></summary>

```mermaid
flowchart TB
    JOBS["职位列表 /jobs<br/>分类 · 城市 · 岗位 / 公司搜索"] --> JOB["职位详情 /job/:id"]
    JOB --> FAV["收藏职位"]
    JOB --> APPLY["投递（可附留言）"]
    JOB --> INTERVIEW["申请 AI 面试"]
    APPLY --> MYAPP["个人中心 · 我的申请"]
    ADMIN["后台修改申请状态"] --> NOTIFY["申请状态通知"]
    NOTIFY --> MYAPP
    INTERVIEW --> QUESTIONS["按岗位生成面试题"]
    QUESTIONS --> ANSWER["逐题作答"]
    ANSWER --> SCORE["总分 + 逐题点评"]
    SCORE --> RECORD["个人中心 · AI 面试记录"]
```

</details>

<details>
<summary><strong>05｜后台管理与自动通知</strong></summary>

```mermaid
flowchart TB
    ADMIN["后台 /admin"] --> DASH["数据看板"]
    ADMIN --> USERS["用户：新建 · 角色 · 禁用 · 删除"]
    ADMIN --> COURSES["课程：新增 · 编辑 · 上下架"]
    COURSES --> OUTLINE["章节目录编辑<br/>章节 · 课时 · 时长 · 类型 · 讲义"]
    ADMIN --> LECT["讲师"]
    ADMIN --> JOBS["职位：新增 · 编辑 · 上下架"]
    ADMIN --> ORDERS["订单"]
    ADMIN --> APPS["职位申请状态"]
    ADMIN --> COMM["社区内容"]

    COURSES --> N1["通知收藏该课程的用户"]
    OUTLINE --> N1
    OUTLINE --> CLEAN["清理已删除课时的学习进度"]
    JOBS --> N2["通知收藏该职位的用户"]
    APPS --> N3["通知申请人"]
```

</details>

<details>
<summary><strong>06｜前后端数据流</strong></summary>

```mermaid
flowchart LR
    PAGE["Vue 页面"] --> API["Axios 封装<br/>自动携带 Bearer Token"]
    API --> ROUTER["FastAPI Router /api/*"]
    ROUTER --> AUTH["JWT 解析 · 账号状态 · 角色校验"]
    AUTH --> LOGIC["业务逻辑<br/>参数校验 · 归属校验 · 幂等"]
    LOGIC --> ORM["SQLAlchemy ORM"]
    ORM --> DB[("SQLite / MySQL")]
    LOGIC --> NOTIFY["通知服务"]
    NOTIFY --> DB
    LOGIC --> AI["AI 服务层"]
    DB --> RESP["统一返回 code / data / detail"]
    AI --> RESP
    RESP --> PAGE
```

</details>

## 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3.5、Vite 5、Element Plus 2（暗色主题）、Pinia、Vue Router、Axios、ECharts 5、Geist 字体（本地打包） |
| 后端 | Python 3.11、FastAPI、SQLAlchemy 2.0、Pydantic 2、PyJWT、Uvicorn |
| 数据库 | SQLite（默认）、MySQL（设置 `DATABASE_URL`） |
| AI | OpenAI 兼容 Chat Completions 接口（DeepSeek、通义千问、Moonshot 等），未配置时使用内置引擎 |
| 迁移 | Alembic（CI 校验迁移与模型一致） |
| 部署 | Docker 多阶段构建、Docker Compose（PostgreSQL 16 + Nginx）、GitHub Actions |
| 质量 | pytest、Vitest、ESLint；Element Plus 按需引入、ECharts 按需注册 |

## 快速开始

环境要求：Python 3.11+、Node.js 20+。

### 一键启动（Windows）

```bat
:: 开发模式：后端 :8000 + 前端热更新 :5173
start-dev.bat

:: 生产模式：构建前端后由后端统一托管，访问 http://127.0.0.1:8000
start-prod.bat
```

### 手动启动

```bash
git clone https://github.com/FreeNAP/edu-ai-platform.git
cd edu-ai-platform

# 后端（首次启动自动建表并写入演示数据）
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端（新开一个终端）
cd frontend
npm install
npm run dev          # http://localhost:5173，/api 自动代理到 8000
```

## 部署

### Docker Compose（推荐）

```bash
git clone https://github.com/FreeNAP/edu-ai-platform.git
cd edu-ai-platform
cp .env.example .env                                    # 设置 POSTGRES_PASSWORD
cp deploy/.env.production.example deploy/.env.production # 设置 SECRET_KEY、域名、SMTP、AI
docker compose up -d --build
docker compose exec app python -m app.cli create-admin --username admin --email admin@example.com
```

启动时自动执行 `alembic upgrade head`。Nginx 负责静态资源缓存、上传文件（视频支持断点拖动）、接口限流与流式输出转发；应用以非 root 用户运行并带健康检查。生产环境默认关闭演示数据和接口文档，`SECRET_KEY` 不合格时拒绝启动。

### 手动部署

```bash
cd frontend && npm ci && npm run build
cd ../backend
cp .env.example .env        # APP_ENV=production、SECRET_KEY、DATABASE_URL……
alembic upgrade head
python -m app.cli create-admin --username admin --email admin@example.com
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers
```

### 运维命令

| 命令 | 作用 |
| --- | --- |
| `python -m app.cli check` | 检查配置、数据库连接、邮件与 AI 是否就绪 |
| `python -m app.cli create-admin --username … --email …` | 创建管理员，或把已有账号设为管理员并重置密码 |
| `python -m app.cli seed-demo` | 向空库写入演示数据 |
| `alembic upgrade head` / `alembic revision --autogenerate -m "…"` | 升级数据库 / 生成新迁移 |
| `GET /api/health` | 健康检查（含数据库连通性），供负载均衡探活 |

### 演示账号

| 账号 | 密码 | 角色 | 预置数据 |
| --- | --- | --- | --- |
| `admin` | `admin123` | 管理员 | 后台全部功能 |
| `teacher` | `teacher123` | 教师 | — |
| `student` | `student123` | 学生 | 2 门在学课程、学习记录、1 个订单、1 条申请、1 场已完成的 AI 面试、1 份学习路径、通知 |

## 配置

后端从 `backend/.env` 或同名环境变量读取配置，完整模板见 [`backend/.env.example`](backend/.env.example)，常用项如下。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` 时关闭演示数据与接口文档，并强制检查密钥 |
| `SECRET_KEY` | 开发用默认值 | JWT 签名密钥，生产环境至少 32 位随机字符串 |
| `DATABASE_URL` | SQLite | `postgresql+psycopg2://…` 或 `mysql+pymysql://…`，驱动已包含在依赖中 |
| `SMTP_HOST` 等 | 空 | 找回密码验证码邮件；未配置时开发环境直接在页面填入验证码 |
| `AI_DAILY_QUOTA` | `100` | 学生每日 AI 调用次数，0 为不限 |
| `LOG_JSON` | `false` | 输出 JSON 日志，每条请求带 `X-Request-ID` |
| `AI_API_KEY` | 空 | 留空使用内置引擎 |
| `AI_BASE_URL` | `https://api.deepseek.com` | 任意 OpenAI 兼容服务地址 |
| `AI_MODEL` | `deepseek-chat` | 模型名称 |

```bash
# Windows
set AI_API_KEY=sk-xxxx
set AI_BASE_URL=https://api.deepseek.com
set AI_MODEL=deepseek-chat

# macOS / Linux
export AI_API_KEY=sk-xxxx
```

真实接口超时或返回格式不对时会自动回退到内置引擎，页面不会报错。

## 测试

```bash
cd backend && python -m pytest tests -q          # 54 个接口测试
cd frontend && npm run lint && npm run test      # ESLint + 8 个单元测试
```

每次推送由 GitHub Actions 运行：后端迁移校验与测试、前端 lint / 单元测试 / 构建、Docker 镜像构建。后端用例覆盖账号锁定、刷新令牌与吊销、验证码找回密码、上传类型识别、教师越权、测验判分与证书发放、AI 配额与流式输出、审计日志，以及注册登录与密码、课程筛选排序、报名与课时进度、订单支付、职位投递、AI 四项功能与模拟面试、学习路径到期提醒、全部自动通知规则、社区删除权限、课程目录替换与进度清理、下架内容隐藏、禁用账号拦截、越权访问、分页上限、重复操作幂等、统一错误格式。测试使用临时数据库，不影响开发数据。

## 目录与文件用途

| 路径 | 内容 |
| --- | --- |
| `backend/app/main.py` | FastAPI 入口：中间件（请求 ID、安全响应头、审计）、统一异常处理、健康检查、托管前端与上传文件 |
| `backend/app/config.py` | 全部配置项（pydantic-settings）与生产环境检查 |
| `backend/app/security.py` / `ratelimit.py` | 密码哈希与强度、访问 / 刷新令牌、IP 限流 |
| `backend/app/cli.py` | 运维命令 |
| `backend/alembic/` | 数据库迁移 |
| `backend/app/routers/` | `auth` `users` `courses` `jobs` `orders` `ai` `quizzes` `teacher` `uploads` `notifications` `community` `admin` 十二组接口 |
| `backend/app/services/llm.py` | OpenAI 兼容接口调用、结果结构校验与失败回退 |
| `backend/app/services/mock_engine.py` | 内置 AI 引擎：答疑知识库、路径规划、代码批改、报告统计、面试题库 |
| `backend/app/services/` | 通知、邮件、审计日志、AI 配额等服务 |
| `backend/app/models.py` / `schemas.py` | 数据表模型与请求体校验 |
| `backend/app/seed.py` / `seed_content.py` | 演示账号、18 门课程、课时讲义、12 个职位与学习记录 |
| `backend/tests/` | 接口测试与公共夹具 |
| `frontend/src/views/` | 登录、课程、学习、职位、面试、AI 助手、个人中心、通知、社区、后台各页面 |
| `frontend/src/components/` | 课程卡、按方向区分的 SVG 课程封面、职位卡、头像；`icons/` 下为标志、图标与几何头像 |
| `frontend/src/api/` | 按业务拆分的接口调用 |
| `frontend/src/styles/index.css` | 设计令牌、Element Plus 暗色覆盖、通用组件与响应式规则 |
| `docs/` | 需求分析、系统架构、接口文档与截图 |
| `Dockerfile` / `docker-compose.yml` / `deploy/` | 镜像构建、生产编排、Nginx 配置与生产环境变量模板 |
| `.github/workflows/ci.yml` | 持续集成 |
| `start-dev.bat` / `start-prod.bat` | Windows 一键启动脚本 |

## 页面展示

<table>
  <tr>
    <td width="50%"><strong>登录</strong><br><img src="docs/screenshots/01-login.webp" alt="登录"></td>
    <td width="50%"><strong>课程中心</strong><br><img src="docs/screenshots/02-courses.webp" alt="课程中心"></td>
  </tr>
  <tr>
    <td><strong>课程详情</strong><br><img src="docs/screenshots/03-course-detail.webp" alt="课程详情"></td>
    <td><strong>课时学习</strong><br><img src="docs/screenshots/04-learn.webp" alt="课时学习"></td>
  </tr>
  <tr>
    <td><strong>实习就业</strong><br><img src="docs/screenshots/05-jobs.webp" alt="实习就业"></td>
    <td><strong>AI 模拟面试结果</strong><br><img src="docs/screenshots/06-interview.webp" alt="AI 模拟面试"></td>
  </tr>
  <tr>
    <td><strong>学习报告</strong><br><img src="docs/screenshots/07-ai-report.webp" alt="学习报告"></td>
    <td><strong>个人中心</strong><br><img src="docs/screenshots/08-profile.webp" alt="个人中心"></td>
  </tr>
  <tr>
    <td><strong>后台数据看板</strong><br><img src="docs/screenshots/09-admin-dashboard.webp" alt="后台数据看板"></td>
    <td><strong>课程目录编辑</strong><br><img src="docs/screenshots/10-admin-outline.webp" alt="课程目录编辑"></td>
  </tr>
</table>

## 许可证

[MIT](LICENSE)
