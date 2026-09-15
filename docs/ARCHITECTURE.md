# 系统架构说明

## 后端结构

### 当前状态

后端位于 `server/app/`，存在两套平行的模块组织方式：

1. **routers/** - 正式 API 入口（已在 main.py 注册）
   - 实际处理所有 HTTP 请求
   - 直接被 FastAPI 应用加载
   
2. **modules/** - 模块化草稿（未在 main.py 注册）
   - 来自 yjj 分支的模块化尝试
   - 部分与 routers/ 功能重叠
   - **未被实际使用**

### 目录职责

```
server/app/
├── main.py              # FastAPI 应用入口，注册 routers/
├── models.py            # 所有数据库模型（统一定义）
├── seed.py              # 数据库初始化种子数据
├── core/                # 核心功能
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接
│   ├── db.py            # 数据库初始化
│   ├── dependencies.py  # 依赖注入
│   └── security.py      # 认证和加密
├── routers/             # **正式 API 路由（已注册）**
│   ├── admin.py         # 管理员：部门、用户、审计日志
│   ├── assignments.py   # 派发与任务管理
│   ├── assisted_tasks.py # C/B 辅助任务
│   ├── auth.py          # 认证登录
│   ├── patient_session.py # 患者会话
│   ├── patients.py      # 患者档案
│   ├── questionnaires.py # 问卷模板治理
│   └── statistics.py    # 统计报表
├── modules/             # **未注册的模块化草稿**
│   ├── assignments/     # 与 routers/assignments.py 重叠
│   ├── auth/            # 与 routers/auth.py 重叠
│   ├── patients/        # 与 routers/patients.py 重叠
│   ├── questionnaires/  # 与 routers/questionnaires.py 重叠
│   ├── users/           # 部分功能在 routers/admin.py
│   ├── departments/     # 部分功能在 routers/admin.py
│   ├── assessments/     # 模型草稿
│   ├── audit/           # 模型草稿
│   └── scoring/         # 已被 services/scoring.py 替代
└── services/            # 业务逻辑服务层
    ├── assignment.py    # 派发逻辑
    ├── audit.py         # 审计日志
    ├── deepseek.py      # LLM 集成
    ├── llm_config.py    # LLM 配置
    ├── moca_open.py     # MoCA 开放题分析
    ├── permissions.py   # 权限检查
    ├── questionnaire.py # 问卷 schema 验证
    ├── questionnaire_governance.py # 问卷版本治理
    ├── review_rules.py  # 复核规则
    ├── scale_catalog.py # 量表目录
    └── scoring.py       # 计分逻辑
```

### 为什么存在 modules/?

从 Git 历史来看：
- `modules/` 来自 yjj 分支的模块化尝试
- dl 整合时选择了 `routers/` + `services/` 的扁平架构
- `modules/` 中的模型定义已统一到 `models.py`
- `modules/` 中的路由未被 `main.py` 注册，**实际不参与运行**

### 当前问题

1. **职责混淆**：同一功能存在两份代码
2. **维护成本**：修改时容易漏掉其中一份
3. **新人困惑**：不清楚该看哪个文件
4. **Import 混乱**：没有明确的依赖规则

## 前端结构

### 正式前端（admin-web/）

Vue 3 + Element Plus，包含医生端和患者端：

```
admin-web/src/
├── views/
│   ├── LoginView.vue         # 医生登录
│   ├── DashboardView.vue     # 仪表盘
│   ├── PatientsView.vue      # 患者列表
│   ├── PatientDetailView.vue # 患者详情
│   ├── AssignmentsView.vue   # 派发列表
│   ├── CreateAssignmentView.vue # 创建派发
│   ├── QuestionnairesView.vue # 问卷治理
│   ├── AdminCenterView.vue   # 管理中心
│   └── patient/
│       └── PatientPortal.vue # 患者填写入口
├── components/
│   ├── DynamicQuestion.vue   # 动态题型
│   ├── AssistedTask.vue      # C/B 辅助任务
│   ├── ReviewEvidence.vue    # 复核证据
│   └── ...
├── layouts/
│   └── StaffLayout.vue       # 医生端布局
├── stores/
│   └── auth.ts               # 认证状态
└── utils/
    ├── patient.ts            # 患者逻辑
    ├── mocaOpen.ts           # MoCA 分析
    └── ...
```

### 参考原型（patient-web/c2b/Frontend/）

React + TypeScript，仅作来源参考，**不在生产环境使用**：

```
patient-web/c2b/Frontend/src/
├── pages/
│   ├── HomePage.tsx          # 任务列表
│   ├── BostonNamingPage.tsx  # Boston 命名
│   ├── TrailMakingPage.tsx   # STT 连线
│   ├── ScdInterviewPage.tsx  # SCD 访谈
│   └── MocaOpenAnswerPage.tsx # MoCA 开放题
├── components/
│   ├── PageShell.tsx
│   └── ui.tsx
├── data/
│   └── demo-data.ts          # 演示数据
└── store/
    └── use-demo-store.ts     # 本地状态
```

**注意**：C/B 任务已迁移到 `admin-web`，React 版本仅用于参考原型逻辑。

## 数据库模型

所有模型定义在 `server/app/models.py`，包括：

- User, Department - 用户和部门
- Patient - 患者档案
- QuestionnaireTemplate, QuestionnaireVersion - 问卷模板和版本
- Assignment, TaskPackage, TaskItem - 派发和任务
- Response, ResponseRevision - 答卷和草稿
- AssistedTask, AssistedTaskReview - 辅助任务和复核
- AuditLog - 审计日志

## API 契约

详见 [contracts/API.md](../contracts/API.md)

主要端点：
- `/api/auth/*` - 认证
- `/api/patients/*` - 患者管理
- `/api/questionnaires/*` - 问卷治理
- `/api/assignments/*` - 派发管理
- `/api/patient-session/*` - 患者会话
- `/api/assisted-tasks/*` - 辅助任务
- `/api/statistics/*` - 统计报表
- `/api/admin/*` - 管理中心
