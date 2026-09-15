# Admin-Web 结构说明

## 项目定位

**正式 Vue 前端**，包含医生端和患者端，是生产环境唯一使用的前端代码。

## 目录结构

```
admin-web/
├── src/
│   ├── views/              # 页面视图
│   │   ├── LoginView.vue              # 医生登录
│   │   ├── DashboardView.vue          # 仪表盘（统计图表）
│   │   ├── PatientsView.vue           # 患者列表
│   │   ├── PatientDetailView.vue      # 患者详情（档案+评估历史）
│   │   ├── AssignmentsView.vue        # 派发列表
│   │   ├── CreateAssignmentView.vue   # 创建派发（选择患者和问卷）
│   │   ├── QuestionnairesView.vue     # 问卷治理（预览/导入/发布）
│   │   ├── AdminCenterView.vue        # 管理中心（部门/用户/审计）
│   │   └── patient/
│   │       └── PatientPortal.vue      # 患者入口（填写问卷+辅助任务）
│   ├── components/         # 可复用组件
│   │   ├── DynamicQuestion.vue        # 动态题型（单选/多选/文本/条件题）
│   │   ├── patient/
│   │   │   └── AssistedTask.vue       # C/B 辅助任务组件
│   │   ├── ReviewEvidence.vue         # 复核证据展示
│   │   ├── QuestionnaireDetailDialog.vue  # 问卷详情弹窗
│   │   ├── ChartPanel.vue             # 图表面板
│   │   └── StatCard.vue               # 统计卡片
│   ├── layouts/
│   │   └── StaffLayout.vue            # 医生端布局（顶栏+侧边栏）
│   ├── stores/
│   │   └── auth.ts                    # 认证状态（Pinia）
│   ├── utils/              # 工具函数
│   │   ├── patient.ts                 # 患者逻辑（草稿保存/提交）
│   │   ├── mocaOpen.ts                # MoCA 开放题分析
│   │   ├── date.ts                    # 日期格式化
│   │   └── idempotency.ts             # 幂等键生成
│   ├── api/
│   │   └── client.ts                  # Axios 客户端配置
│   ├── router.ts           # Vue Router 配置
│   └── main.ts             # 应用入口
├── public/                 # 静态资源
├── dist/                   # 构建产物
├── tests/                  # 测试
│   └── e2e/                # Playwright E2E 测试
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 路由架构

### 医生端路由（需登录）

| 路径 | 组件 | 说明 |
|---|---|---|
| `/login` | LoginView | 医生登录（用户名+密码） |
| `/` | DashboardView | 仪表盘（总览统计、图表） |
| `/patients` | PatientsView | 患者列表（搜索、筛选、创建） |
| `/patients/:id` | PatientDetailView | 患者详情（档案+评估历史+派发） |
| `/assignments` | AssignmentsView | 派发列表（进行中、已完成） |
| `/assignments/new` | CreateAssignmentView | 创建派发（选择患者+问卷） |
| `/questionnaires` | QuestionnairesView | 问卷治理（目录、版本、导入） |
| `/admin` | AdminCenterView | 管理中心（部门、用户、审计日志） |

### 患者端路由（token + 访问码）

| 路径 | 组件 | 说明 |
|---|---|---|
| `/p/fill/:token` | PatientPortal | 患者填写入口（验证访问码 → 任务列表 → 逐题作答） |

## 核心组件说明

### DynamicQuestion.vue

动态题型渲染组件，支持：
- 单选题（radio）
- 多选题（checkbox）
- 文本题（text）
- 数值题（number）
- 日期题（date）
- 条件显示（根据前置答案决定是否显示）

**使用示例**：
```vue
<DynamicQuestion
  :question="question"
  :value="answers[question.id]"
  @update:value="updateAnswer(question.id, $event)"
/>
```

### AssistedTask.vue

C/B 辅助任务组件，支持：
- Boston 图片命名（15 张图片，语音输入/文本输入）
- STT 连线测试（A 型数字、B 型数字+字母）
- SCD 访谈（对话式追问，AI 辅助生成）
- MoCA 开放问答（多轮对话，候选分析）

**数据来源**：
- STT 坐标：`patient-web/stt_sequences_with_coordinates.json`
- STT 阈值：`patient-web/stt_age_thresholds.json`

**后端集成**：
- 保存答案、点击事件、用时到后端
- DeepSeek LLM 生成候选结果（可降级）
- 医生复核确认最终结果

### ReviewEvidence.vue

复核证据展示组件，用于医生审查辅助任务：
- 显示患者答案、交互记录
- 展示 AI 候选结果和置信度
- 支持通过/退回操作

## 状态管理

### Pinia Store: auth.ts

```typescript
interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
}

// Actions
login(username, password)  // 医生登录
logout()                   // 退出登录
fetchCurrentUser()         // 获取当前用户信息
```

### 本地状态管理

患者端使用 `ref/reactive` 管理：
- 任务列表状态
- 答题进度
- 草稿数据
- 辅助任务状态

## API 集成

### 基础配置（api/client.ts）

```typescript
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：添加 token
apiClient.interceptors.request.use(config => {
  const token = authStore.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)
```

### 主要 API 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/auth/login` | POST | 医生登录 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/patients` | GET/POST | 患者列表/创建 |
| `/api/patients/:id` | GET/PUT | 患者详情/更新 |
| `/api/questionnaires` | GET/POST | 问卷列表/导入 |
| `/api/assignments` | GET/POST | 派发列表/创建 |
| `/api/patient-session/verify` | POST | 患者验证访问码 |
| `/api/patient-session/package` | GET | 获取任务包 |
| `/api/patient-session/tasks/:id/draft` | PUT | 保存草稿 |
| `/api/patient-session/tasks/:id/submit` | POST | 提交答卷 |
| `/api/assisted-tasks/:id` | GET | 获取辅助任务 |
| `/api/assisted-tasks/:id/data` | PUT | 保存辅助任务数据 |
| `/api/statistics/overview` | GET | 统计概览 |

## 技术栈

- **Vue 3.4** - Composition API, `<script setup>`
- **TypeScript 5.3** - 类型安全
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化
- **Vite 5** - 构建工具
- **Playwright** - E2E 测试

## 构建与部署

### 开发模式

```bash
npm install
npm run dev
# 访问 http://127.0.0.1:5173
```

### 生产构建

```bash
npm run build
# 产物在 dist/ 目录
```

### 测试

```bash
# 单元测试（如果有）
npm run test

# E2E 测试（需要后端运行）
npm run test:e2e
```

## 演示账号

### 医生账号
- 用户名：`doctor1`
- 密码：`Doctor123!`

### 管理员账号
- 用户名：`admin`
- 密码：`Admin123!`

### 患者演示
- 链接：http://127.0.0.1:5173/p/fill/demo-patient-token
- 访问码：`123456`

## 开发约定

### 代码风格
- 使用 `<script setup>` 语法
- 组件文件名使用 PascalCase（如 `PatientDetailView.vue`）
- 工具函数使用 camelCase（如 `formatDate`）
- 类型定义统一放在文件顶部或单独的 `types.ts`

### 命名规范
- 事件：`on` + 动作（如 `onSubmit`）
- Props：描述性名词（如 `questionData`）
- Emits：动作 + 对象（如 `update:value`）

### 目录组织
- `views/` - 页面级组件（一个路由对应一个 view）
- `components/` - 可复用组件（多处使用）
- `utils/` - 纯函数工具
- `stores/` - Pinia 状态管理

## 相关文档

- [系统架构](../docs/ARCHITECTURE.md)
- [API 契约](../contracts/API.md)
- [后端整合说明](../docs/BACKEND_INTEGRATION.md)
- [C/B 任务整合](../docs/integration/2026-09-14-cb-patient-integration.md)
